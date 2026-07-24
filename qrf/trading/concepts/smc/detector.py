"""Detector #3 — Smart Money Concepts (SMC), wrapping ``smartmoneyconcepts``.

ARCH-004 §4, Blueprint §4.3/§7 Sprint 4. Two detectors under the ``smc`` family
turn bar tables into EventFrames:

* :class:`SMCFVGDetector` — ``smc.fvg.bull`` / ``smc.fvg.bear`` (fair value gaps).
* :class:`SMCOrderBlockDetector` — ``smc.order_block.bull`` / ``smc.order_block.bear``.

Both emit **zone** events (``zone_hi``/``zone_lo`` carry the gap/block band;
``zone_hi >= zone_lo`` always). This is the trading plug-in, so price vocabulary
is allowed.

Anti-hindsight (Blueprint §4.3, the load-bearing property here)
--------------------------------------------------------------
``smartmoneyconcepts`` is a *vectorised, whole-frame* library: it computes with
``shift(-1)`` (FVG) and with swing detection that looks ``swing_length`` bars
into the future and force-flips the frame's first/last swing (order blocks). Left
as-is that is hindsight — an event "known" at a bar that could not have been seen
yet. So every emitted event's ``ts`` is set to its **knowability moment** — the
timestamp of the *last bar the computation actually needed*:

* FVG at centre bar ``i`` uses ``low``/``high`` of bar ``i+1``; ts = ts[i+1].
* An order block is knowable only once its governing swing is confirmed and the
  structure break has printed. Rather than re-derive the library's internal
  break bar, the detector finds, by binary search over data prefixes, the
  *earliest prefix at which the library first (and stably) reports that exact
  block* — and stamps ts at that prefix's last bar. A tail margin of
  ``swing_length`` bars excludes the unconfirmed / boundary-forced blocks near
  the end of any frame, so a block, once emitted, never changes retroactively.

This makes the incremental-consistency property true by construction: detecting
on a prefix emits exactly the full-frame events whose knowability bar is within
the prefix, each with an identical ts.

The pinned library version is recorded in each detector's ``code_ref`` (and hence
in its ``instrument_registered`` payload), per the Blueprint new-dependency rule.
"""

from __future__ import annotations

import contextlib
import io
import json
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa

# Importing smartmoneyconcepts prints a banner to stdout that crashes under a
# non-UTF-8 console (Windows cp1252). Swallow it so the import is side-effect free.
with contextlib.redirect_stdout(io.StringIO()):
    from smartmoneyconcepts import smc

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import CalibrationCase, build_event_frame

SMC_VERSION: str = smc.__version__
FAMILY = "smc"
_ZONE_TOL = 1e-6


def _ohlc(data: pa.Table) -> tuple[np.ndarray, pd.DataFrame]:
    """Extract (ts int64 array, OHLCV DataFrame) from an input bar table.

    Requires ``ts, open, high, low, close``. ``volume`` (or ``tick_volume``) is
    used if present, else a constant is injected — volume never gates SMC event
    *detection* (only the library's descriptive OBVolume/Percentage), so a
    constant does not change which events fire.
    """
    if not isinstance(data, pa.Table):
        raise SchemaViolation(f"SMC detector expects a pyarrow.Table, got {type(data).__name__}")
    for col in ("ts", "open", "high", "low", "close"):
        if col not in data.column_names:
            raise SchemaViolation(f"SMC detector requires a {col!r} column")
    ts = np.asarray([int(t) for t in data.column("ts").to_pylist()], dtype=np.int64)
    df = pd.DataFrame(
        {
            c: [float(x) for x in data.column(c).to_pylist()]
            for c in ("open", "high", "low", "close")
        }
    )
    if "volume" in data.column_names:
        df["volume"] = [float(x) for x in data.column("volume").to_pylist()]
    elif "tick_volume" in data.column_names:
        df["volume"] = [float(x) for x in data.column("tick_volume").to_pylist()]
    else:
        df["volume"] = 1.0
    return ts, df


def _zone(top: float, bottom: float) -> tuple[float, float]:
    """Return (zone_hi, zone_lo) with zone_hi >= zone_lo."""
    return (top, bottom) if top >= bottom else (bottom, top)


# ===========================================================================
# Fair Value Gaps
# ===========================================================================
class SMCFVGDetector:
    """Fair-value-gap detector (``smc.fvg.bull`` / ``smc.fvg.bear``)."""

    instrument_id = "smc.fvg"
    family = FAMILY
    kind = "detector"
    code_ref = (
        f"qrf.trading.concepts.smc.detector:SMCFVGDetector (smartmoneyconcepts=={SMC_VERSION})"
    )
    params_schema = {
        "join_consecutive": "bool  # merge back-to-back gaps into one (default False)",
    }

    def __init__(self, *, version: str = "0.1.0", params: dict[str, Any] | None = None) -> None:
        self.version = version
        p = dict(params or {})
        self.join_consecutive = bool(p.get("join_consecutive", False))
        self.params = {"join_consecutive": self.join_consecutive}

    def detect(self, data: pa.Table) -> pa.Table:
        ts, df = _ohlc(data)
        n = len(df)
        if n < 3:  # a 3-bar pattern is the minimum; fewer bars -> silence.
            return build_event_frame([])
        fvg = smc.fvg(df, join_consecutive=self.join_consecutive)
        rows: list[dict[str, Any]] = []
        for i in range(n):
            v = fvg["FVG"].iloc[i]
            if pd.isna(v):
                continue
            k = i + 1  # knowability: the gap needs the bar after the centre.
            if k >= n:  # last-row centres never fire (shift(-1) is NaN there).
                continue
            direction = int(v)
            side = "bull" if direction == 1 else "bear"
            zone_hi, zone_lo = _zone(float(fvg["Top"].iloc[i]), float(fvg["Bottom"].iloc[i]))
            # Strength: the gap size relative to the total range spanned by the
            # three bars that form it (i-1, i, i+1) — a bounded (0, 1] measure,
            # computed only from bars up to the knowability bar i+1 (causal).
            span = max(df["high"].iloc[i - 1 : i + 2]) - min(df["low"].iloc[i - 1 : i + 2])
            gap = zone_hi - zone_lo
            strength = float(min(1.0, gap / span)) if span > 0 else 1.0
            rows.append(
                {
                    "ts": int(ts[k]),
                    "event_type": f"smc.fvg.{side}",
                    "direction": direction,
                    "level": (zone_hi + zone_lo) / 2.0,
                    "zone_hi": zone_hi,
                    "zone_lo": zone_lo,
                    "strength": strength,
                    "meta": json.dumps({"confirm_lag_bars": 1}, sort_keys=True),
                }
            )
        rows.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))
        return build_event_frame(rows)

    def planted_cases(self) -> list[CalibrationCase]:
        from qrf.trading.concepts.smc.fixtures import fvg_cases

        return fvg_cases()


# ===========================================================================
# Order Blocks
# ===========================================================================
class SMCOrderBlockDetector:
    """Order-block detector (``smc.order_block.bull`` / ``smc.order_block.bear``)."""

    instrument_id = "smc.order_block"
    family = FAMILY
    kind = "detector"
    code_ref = (
        f"qrf.trading.concepts.smc.detector:SMCOrderBlockDetector "
        f"(smartmoneyconcepts=={SMC_VERSION})"
    )
    params_schema = {
        "swing_length": "int >= 2  # bars each side for swing detection (default 3)",
        "close_mitigation": "bool  # mitigate on close vs high/low (default False)",
    }

    def __init__(self, *, version: str = "0.1.0", params: dict[str, Any] | None = None) -> None:
        self.version = version
        p = dict(params or {})
        self.swing_length = int(p.get("swing_length", 3))
        if self.swing_length < 2:
            raise ValueError("SMC order-block swing_length must be >= 2")
        self.close_mitigation = bool(p.get("close_mitigation", False))
        self.params = {"swing_length": self.swing_length, "close_mitigation": self.close_mitigation}

    # -- raw (whole-frame) blocks, tail-trimmed for stability -----------------
    def _raw(self, df: pd.DataFrame) -> dict[int, tuple[int, float, float]]:
        """Blocks the library reports on ``df``, keyed by block-bar index.

        Blocks whose bar sits within ``swing_length`` of the frame end are
        dropped: their governing swing is not yet confirmed (or is the
        force-flipped boundary swing), so they are unstable and non-causal.
        """
        n = len(df)
        if n < 2 * self.swing_length + 2:
            return {}
        shl = smc.swing_highs_lows(df, swing_length=self.swing_length)
        ob = smc.ob(df, shl, close_mitigation=self.close_mitigation)
        limit = n - self.swing_length
        out: dict[int, tuple[int, float, float]] = {}
        col = ob["OB"]
        top_col, bot_col = ob["Top"], ob["Bottom"]
        for i in range(n):
            v = col.iloc[i]
            if pd.isna(v) or v == 0:
                continue
            if i >= limit:
                continue
            zone_hi, zone_lo = _zone(float(top_col.iloc[i]), float(bot_col.iloc[i]))
            out[i] = (int(v), zone_hi, zone_lo)
        return out

    def _knowability(
        self,
        df: pd.DataFrame,
        ob_index: int,
        direction: int,
        zone_hi: float,
        zone_lo: float,
        n: int,
    ) -> int | None:
        """Index of the last bar of the smallest prefix that stably reports the block."""

        def has(length: int) -> bool:
            e = self._raw(df.iloc[:length]).get(ob_index)
            return (
                e is not None
                and e[0] == direction
                and abs(e[1] - zone_hi) < _ZONE_TOL
                and abs(e[2] - zone_lo) < _ZONE_TOL
            )

        if not has(n):  # not present in the full frame -> nothing to stamp.
            return None
        lo, hi = ob_index + 1, n
        while lo < hi:
            mid = (lo + hi) // 2
            if has(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo - 1  # prefix length `lo` -> last bar index lo-1

    def detect(self, data: pa.Table) -> pa.Table:
        ts, df = _ohlc(data)
        n = len(df)
        raw = self._raw(df)
        rows: list[dict[str, Any]] = []
        for ob_index, (direction, zone_hi, zone_lo) in raw.items():
            k = self._knowability(df, ob_index, direction, zone_hi, zone_lo, n)
            if k is None:
                continue
            side = "bull" if direction == 1 else "bear"
            rows.append(
                {
                    "ts": int(ts[k]),
                    "event_type": f"smc.order_block.{side}",
                    "direction": direction,
                    "level": (zone_hi + zone_lo) / 2.0,
                    "zone_hi": zone_hi,
                    "zone_lo": zone_lo,
                    "strength": 1.0,
                    "meta": json.dumps({"swing_length": self.swing_length}, sort_keys=True),
                }
            )
        rows.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))
        return build_event_frame(rows)

    def planted_cases(self) -> list[CalibrationCase]:
        from qrf.trading.concepts.smc.fixtures import order_block_cases

        return order_block_cases(swing_length=self.swing_length)


__all__ = ["SMCFVGDetector", "SMCOrderBlockDetector", "SMC_VERSION"]
