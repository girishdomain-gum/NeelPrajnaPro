"""Classical RSI detector (detector #2) — pandas-ta RSI threshold crossings.

ARCH-002 §Trading plug-in. Wraps pandas-ta's RSI and emits events only on
threshold **crossings** (never while RSI merely stays beyond a band):

* ``classical.rsi.overbought_cross`` — RSI crosses up through ``overbought``;
  ``direction = -1`` (stretched high -> bearish lean).
* ``classical.rsi.oversold_cross`` — RSI crosses down through ``oversold``;
  ``direction = +1`` (stretched low -> bullish lean).

EventFrame mapping (ARCH-002): ``level`` = the bar close (a price level; this is
the trading plug-in, so price vocabulary is allowed here), and the RSI value goes
in ``meta`` as ``{"rsi": ..., "period": ...}``. ``strength = 1.0`` per crossing.

**Knowability / anti-hindsight.** An event's ``ts`` is the ``ts`` of the bar that
*completed* the crossing — the bar-close time carried in the input ``ts`` column,
never a bar's open time. RSI (Wilder RMA) is causal, so a crossing at bar *i*
depends only on bars ``0..i`` and never changes as later bars arrive.

**Warm-up (DEVQ-002/003, proceeding on option A).** RSI is untrustworthy until
``period`` full observations exist, so the first ``period`` bars are excluded from
crossing emission (even though pandas-ta yields a numeric RSI earlier). A series
shorter than ``period + 1`` bars is *insufficient*: the detector emits nothing and
does not raise.
"""

from __future__ import annotations

import json
import math
from typing import Any

import pandas as pd
import pandas_ta as ta
import pyarrow as pa

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import CalibrationCase, build_event_frame


class RSIDetector:
    """RSI overbought/oversold crossing detector (pandas-ta wrap)."""

    instrument_id = "classical.rsi"
    family = "classical"
    kind = "detector"
    code_ref = "qrf.trading.concepts.classical.detector_rsi:RSIDetector"

    params_schema = {
        "period": "int > 0  # RSI lookback (default 14)",
        "overbought": "float  # upper threshold (default 70)",
        "oversold": "float  # lower threshold (default 30)",
    }

    def __init__(self, *, version: str = "0.1.0", params: dict[str, Any] | None = None) -> None:
        self.version = version
        params = dict(params or {})
        period = int(params.get("period", 14))
        overbought = float(params.get("overbought", 70.0))
        oversold = float(params.get("oversold", 30.0))
        if period <= 0:
            raise ValueError("RSI period must be a positive integer")
        if not (0.0 <= oversold < overbought <= 100.0):
            raise ValueError("require 0 <= oversold < overbought <= 100")
        self._period = period
        self._overbought = overbought
        self._oversold = oversold
        self.params = {"period": period, "overbought": overbought, "oversold": oversold}

    # -- detection ------------------------------------------------------------
    def detect(self, data: pa.Table) -> pa.Table:
        """Emit RSI threshold crossings over the ``close`` series in ``data``."""
        for col in ("ts", "close"):
            if col not in data.column_names:
                raise SchemaViolation(f"RSI detector requires a {col!r} column")
        ts = [int(t) for t in data.column("ts").to_pylist()]
        close = [float(c) for c in data.column("close").to_pylist()]
        n = len(close)

        # Insufficient data: cannot warm up -> silent (no crash).
        if n < self._period + 1:
            return build_event_frame([])

        rsi = ta.rsi(pd.Series(close), length=self._period)
        rsi_vals = [float(v) for v in rsi.tolist()]

        rows: list[dict[str, Any]] = []
        # Warm-up exclusion: only consider crossings at bar i >= period.
        for i in range(self._period, n):
            prev, cur = rsi_vals[i - 1], rsi_vals[i]
            if math.isnan(prev) or math.isnan(cur):
                continue
            if prev <= self._overbought < cur:
                rows.append(self._crossing(ts[i], close[i], cur, "overbought_cross", -1))
            elif prev >= self._oversold > cur:
                rows.append(self._crossing(ts[i], close[i], cur, "oversold_cross", +1))
        return build_event_frame(rows)

    def _crossing(
        self, ts: int, close: float, rsi_value: float, event: str, direction: int
    ) -> dict[str, Any]:
        meta = {"rsi": round(rsi_value, 6), "period": self._period}
        return {
            "ts": ts,
            "event_type": f"classical.rsi.{event}",
            "direction": direction,
            "level": float(close),  # price level of the completing bar
            "zone_hi": math.nan,
            "zone_lo": math.nan,
            "strength": 1.0,
            "meta": json.dumps(meta, sort_keys=True),
        }

    # -- calibration ----------------------------------------------------------
    def planted_cases(self) -> list[CalibrationCase]:
        from qrf.trading.concepts.classical.fixtures import rsi_cases

        return rsi_cases(period=self._period)
