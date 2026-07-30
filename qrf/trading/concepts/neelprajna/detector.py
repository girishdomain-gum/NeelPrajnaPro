"""Detector #4 — neelprajna liquidity sweep (NP-ADR-008 §5 v1.1).

:class:`LiquiditySweepDetector` emits ``neelprajna.liquidity_sweep.pool_formed``
and ``neelprajna.liquidity_sweep.sweep`` — the two-event chain (POOL_FORMED ->
SWEEP, terminal; no REVERSAL_CONFIRMED here) that actually produced the H-07
324-trade evidence population. §5 v1.0 (the T3 MQL5 gate's faithful abstraction
— H1/M1, adaptive ATR tolerance, average-pivot level, mandatory MSS stage) is a
*different, frozen-forever* definition; this detector implements v1.1 only, per
NP-ADR-008 §2.1's three non-equivalence statements. No verdict produced here
speaks for the historical T3 gate.

Provenance (NP-ADR-008 §3 identity table): this is a from-scratch Kernel port of
the literal control flow of ``np_feature_service.py::detect_swings`` and
``build_pools_and_sweeps`` (sha256 ``1a0b5d9f…a6c0``), called at the evidenced
site ``build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2)`` on 300s bars —
values hard-coded at the call site, never CLI defaults, and therefore hard-coded
here as module constants rather than constructor parameters: changing any of
them would mint a new detector version, not a configuration of this one.

Five non-obvious behaviors of the evidenced source are preserved here verbatim
(control flow, not paraphrase — see ``ops/H07_evidenced_definition_annex_NP-S1.md``
recon and NP-ADR-008 §3):

1. A reclose landing exactly on the boundary bar (``i - pen_start == reclose_window``,
   i.e. bar 2 of the window) still counts as a SWEEP, not an invalidation — the
   ``reclosed_now`` check runs before the ``>= reclose_window`` check in the same
   ``elif`` chain.
2. The member-window test (last 200 bars) compares the *confirming* bar's index
   to each candidate mate's own (unconfirmed) formation-bar index, not the
   mate's confirmation index.
3. Sweep/invalidation checks against *already-active* pools run before that same
   bar's newly-confirmed pivots are turned into new pools — a pool cannot be
   swept or invalidated on its own formation bar.
4. Max penetration is monotone non-decreasing: a non-penetrating bar contributes
   exactly 0.0 as a candidate, never a negative value.
5. A pivot that duplicate-suppresses against an already-active pool is still
   recorded in the side's ``recent`` list (available as a future mate for a
   *different* pool) but never joins or updates the suppressing pool's members
   or level.

Anti-hindsight (Blueprint §4.3, machine-checked by the incremental-consistency
test): unlike the SMC detectors, no binary-search knowability derivation is
needed here — the ported algorithm is already a strictly causal, single forward
pass. A pivot at bar ``i`` is used only once the loop reaches ``i + pivot_k``
(the confirmation bar); a pool's POOL_FORMED ``ts`` is that confirmation bar's
``ts`` and never changes once a data prefix includes it; a SWEEP's ``ts`` is the
bar whose close resolves it, and every bar up to and including that bar produces
an identical resolution regardless of what data (if any) follows. Detecting on a
truncated prefix therefore reproduces exactly the full-frame events whose
knowability bar lies inside that prefix — nothing more, nothing less.

Direction convention (detector-defined, §4.3): a HIGH-side pool defends a level
whose eventual sweep predicts SELL (NP-ADR-008 §3 prediction layer); a LOW-side
pool predicts BUY. ``direction`` is therefore -1 for every HIGH-side event
(POOL_FORMED and SWEEP alike) and +1 for every LOW-side event — a stable sign
across a pool's whole lifecycle, not just at the sweep.

Zone convention: both event types describe a single defended price level, not a
band, so ``zone_hi``/``zone_lo`` are NaN (point events, per the classical/RSI
detector convention) and ``level`` carries the frozen pool price. ``meta`` (JSON,
never load-bearing) carries the annex §2's per-event descriptive fields
(pool_members, penetration_ticks, close_back_ticks, reclose_bars, pool_age_bars)
for audit, exactly as the evidenced pipeline recorded them.
"""

from __future__ import annotations

import json
import math
from typing import Any

import numpy as np
import pyarrow as pa

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import CalibrationCase, build_event_frame

FAMILY = "neelprajna"

# Frozen parameters (NP-ADR-008 §3 "Frozen parameters" — hard-coded at the
# evidenced call site, never CLI defaults). Changing any of these values mints a
# new detector version (a new NP-ADR), never an in-place edit of this module.
TICK_SIZE: float = 0.01
POOL_TOL_TICKS: float = 30.0
MIN_PEN_TICKS: float = 5.0
PIVOT_K: int = 3
MEMBER_WINDOW_BARS: int = 200
RECLOSE_WINDOW_BARS: int = 2
TIMEFRAME_SECONDS: int = 300  # M5, single timeframe — no anchor/exec pair.


def _ohlc(data: pa.Table) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract (ts, high, low, close) arrays from an input bar table.

    Requires only ``ts, high, low, close`` — the evidenced source never reads
    the bar ``open`` (§5 v1.1 "clauses not inherited": v1.0's open-inside
    condition and gap-through exclusion are unenforceable in this lineage and
    v1.1 states neither), so an ``open`` column, if present, is ignored.
    """
    if not isinstance(data, pa.Table):
        raise SchemaViolation(
            f"liquidity_sweep detector expects a pyarrow.Table, got {type(data).__name__}"
        )
    for col in ("ts", "high", "low", "close"):
        if col not in data.column_names:
            raise SchemaViolation(f"liquidity_sweep detector requires a {col!r} column")
    ts = np.asarray([int(t) for t in data.column("ts").to_pylist()], dtype=np.int64)
    high = np.asarray([float(x) for x in data.column("high").to_pylist()], dtype=np.float64)
    low = np.asarray([float(x) for x in data.column("low").to_pylist()], dtype=np.float64)
    close = np.asarray([float(x) for x in data.column("close").to_pylist()], dtype=np.float64)
    return ts, high, low, close


def _detect_swings(
    high: np.ndarray, low: np.ndarray, k: int
) -> list[tuple[int, str, float]]:
    """k-bar pivot highs/lows (F-SWING). Ported verbatim from
    ``np_feature_service.py::detect_swings``. Returns ``(bar_idx, side, price)``;
    a pivot at ``bar_idx`` is usable only once the caller reaches ``bar_idx + k``
    (confirmation lag) — enforced by the caller, not here.
    """
    n = len(high)
    rows: list[tuple[int, str, float]] = []
    for i in range(k, n - k):
        if (
            high[i] == high[i - k : i + k + 1].max()
            and bool((high[i - k : i] < high[i]).all())
            and bool((high[i + 1 : i + k + 1] < high[i]).all())
        ):
            rows.append((i, "HIGH", float(high[i])))
        if (
            low[i] == low[i - k : i + k + 1].min()
            and bool((low[i - k : i] > low[i]).all())
            and bool((low[i + 1 : i + k + 1] > low[i]).all())
        ):
            rows.append((i, "LOW", float(low[i])))
    return rows


def _build_pools_and_sweeps(
    ts: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    swings: list[tuple[int, str, float]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """F-POOL + F-SWEEP. Ported verbatim (control flow, boundary conditions,
    ordering) from ``np_feature_service.py::build_pools_and_sweeps`` at its
    evidenced call site — ``pool_tol_ticks=30.0, min_pen_ticks=5.0, pivot_k=3,
    reclose_window=2``. Returns ``(pools, sweeps)``: every pool that ever formed
    (whether later swept, invalidated, or still active at the end of ``data``),
    and every SWEEP outcome (invalidations produce no sweep entry — no event).
    """
    tol = POOL_TOL_TICKS * TICK_SIZE
    pen = MIN_PEN_TICKS * TICK_SIZE
    pools: list[dict[str, Any]] = []
    sweeps: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []

    sw_by_idx: dict[int, list[tuple[int, str, float]]] = {}
    for bar_idx, side, price in swings:
        sw_by_idx.setdefault(bar_idx + PIVOT_K, []).append((bar_idx, side, price))

    recent: dict[str, list[tuple[int, float]]] = {"HIGH": [], "LOW": []}

    def resolve(p: dict[str, Any], swept: bool, event: dict[str, Any] | None) -> None:
        if event is not None:
            sweeps.append(event)
        pools.append(p)
        active.remove(p)

    n = len(high)
    for i in range(n):
        # 1) sweep / invalidation check against active pools (runs BEFORE any
        #    pool newly formed at this same bar i is added to `active` below —
        #    a pool cannot be swept/invalidated on its own formation bar).
        for p in list(active):
            hi_side = p["side"] == "HIGH"
            penetrated_now = (
                (high[i] >= p["price"] + pen) if hi_side else (low[i] <= p["price"] - pen)
            )
            reclosed_now = (close[i] < p["price"]) if hi_side else (close[i] > p["price"])
            depth = ((high[i] - p["price"]) if hi_side else (p["price"] - low[i])) / TICK_SIZE

            if p["pen_start"] is None:
                if penetrated_now:
                    p["pen_start"], p["max_pen"] = i, depth
                    if reclosed_now:  # single-bar sweep-and-reclose
                        resolve(
                            p,
                            True,
                            {
                                "ts": int(ts[i]),
                                "bar_idx": i,
                                "side": "SELL" if hi_side else "BUY",
                                "pool_price": p["price"],
                                "pool_members": p["members"],
                                "penetration_ticks": round(depth, 1),
                                "close_back_ticks": round(
                                    abs(close[i] - p["price"]) / TICK_SIZE, 1
                                ),
                                "reclose_bars": 0,
                                "pool_age_bars": i - p["formed_idx"],
                            },
                        )
            else:
                # Monotone non-decreasing: a non-penetrating bar contributes 0.0,
                # never a negative candidate.
                p["max_pen"] = max(p["max_pen"], depth if penetrated_now else 0.0)
                if reclosed_now:  # reclose within (and including) the window -> sweep
                    resolve(
                        p,
                        True,
                        {
                            "ts": int(ts[i]),
                            "bar_idx": i,
                            "side": "SELL" if hi_side else "BUY",
                            "pool_price": p["price"],
                            "pool_members": p["members"],
                            "penetration_ticks": round(p["max_pen"], 1),
                            "close_back_ticks": round(
                                abs(close[i] - p["price"]) / TICK_SIZE, 1
                            ),
                            "reclose_bars": i - p["pen_start"],
                            "pool_age_bars": i - p["formed_idx"],
                        },
                    )
                elif i - p["pen_start"] >= RECLOSE_WINDOW_BARS:
                    resolve(p, False, None)  # broke through: invalidation, no event

        # 2) newly CONFIRMED pivots at this bar (bar_idx + pivot_k == i).
        for bar_idx, side, price in sw_by_idx.get(i, []):
            recent[side] = [x for x in recent[side] if i - x[0] <= MEMBER_WINDOW_BARS]
            mates = [x for x in recent[side] if abs(x[1] - price) <= tol]
            if mates:
                prices = [x[1] for x in mates] + [price]
                level = float(max(prices) if side == "HIGH" else min(prices))
                if not any(
                    p["side"] == side and abs(p["price"] - level) <= tol for p in active
                ):
                    active.append(
                        {
                            "side": side,
                            "price": level,
                            "members": len(prices),
                            "formed_ts": int(ts[i]),
                            "formed_idx": i,
                            "pen_start": None,
                            "max_pen": 0.0,
                        }
                    )
            recent[side].append((bar_idx, price))

    for p in active:  # never resolved within the data given
        pools.append(p)

    return pools, sweeps


def _pool_strength(members: int) -> float:
    """Detector-defined [0,1]: more corroborating pivots -> higher confidence.
    Not load-bearing for any NP-S1 threshold (registered ``strength_min`` is 0.0)."""
    return float(min(1.0, max(0.0, (members - 1) / 4.0)))


def _sweep_strength(penetration_ticks: float) -> float:
    """Detector-defined [0,1]: deeper penetration relative to the minimum
    qualifying depth -> higher confidence. Not load-bearing for any NP-S1
    threshold (registered ``strength_min`` is 0.0)."""
    return float(min(1.0, max(0.0, penetration_ticks / (MIN_PEN_TICKS * 4.0))))


class LiquiditySweepDetector:
    """POOL_FORMED -> SWEEP liquidity-sweep detector (NP-ADR-008 §5 v1.1)."""

    instrument_id = "neelprajna.liquidity_sweep"
    family = FAMILY
    kind = "detector"
    code_ref = (
        "qrf.trading.concepts.neelprajna.detector:LiquiditySweepDetector "
        "(NP-ADR-008 SS5 v1.1 port of np_feature_service.py sha256 "
        "1a0b5d9f...a6c0 / np_probability_engine.py sha256 a9b75aeb...d2ff, "
        "call site build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2))"
    )
    params_schema = {
        "tick_size": "float  # price units per tick (frozen 0.01, XAUUSD)",
        "pool_tol_ticks": "float  # fixed pool-mate tolerance, ticks (frozen 30.0)",
        "min_pen_ticks": "float  # minimum sweep penetration, ticks (frozen 5.0)",
        "pivot_k": "int  # pivot confirmation half-window, bars (frozen 3)",
        "member_window_bars": "int  # pool-mate lookback, bars (frozen 200)",
        "reclose_window_bars": "int  # max bars to reclose after penetration (frozen 2)",
        "timeframe_seconds": "int  # single bar timeframe, M5 (frozen 300)",
    }

    def __init__(self, *, version: str = "1.1.0") -> None:
        self.version = version
        # Frozen, not configurable — see module docstring. Exposed as a plain
        # dict (not constructor kwargs) so the instrument_registered payload
        # documents the sealed values without offering any way to vary them.
        self.params = {
            "tick_size": TICK_SIZE,
            "pool_tol_ticks": POOL_TOL_TICKS,
            "min_pen_ticks": MIN_PEN_TICKS,
            "pivot_k": PIVOT_K,
            "member_window_bars": MEMBER_WINDOW_BARS,
            "reclose_window_bars": RECLOSE_WINDOW_BARS,
            "timeframe_seconds": TIMEFRAME_SECONDS,
        }

    def detect(self, data: pa.Table) -> pa.Table:
        ts, high, low, close = _ohlc(data)
        n = len(high)
        if n < 2 * PIVOT_K + 1:  # detect_swings' range(k, n-k) would be empty.
            return build_event_frame([])

        swings = _detect_swings(high, low, PIVOT_K)
        pools, sweeps = _build_pools_and_sweeps(ts, high, low, close, swings)

        rows: list[dict[str, Any]] = []
        for p in pools:
            direction = -1 if p["side"] == "HIGH" else 1
            rows.append(
                {
                    "ts": int(p["formed_ts"]),
                    "event_type": f"{self.instrument_id}.pool_formed",
                    "direction": direction,
                    "level": p["price"],
                    "zone_hi": math.nan,
                    "zone_lo": math.nan,
                    "strength": _pool_strength(p["members"]),
                    "meta": json.dumps(
                        {
                            "side": p["side"],
                            "pool_members": p["members"],
                            "formed_idx": p["formed_idx"],
                        },
                        sort_keys=True,
                    ),
                }
            )
        for ev in sweeps:
            direction = -1 if ev["side"] == "SELL" else 1
            rows.append(
                {
                    "ts": int(ev["ts"]),
                    "event_type": f"{self.instrument_id}.sweep",
                    "direction": direction,
                    "level": ev["pool_price"],
                    "zone_hi": math.nan,
                    "zone_lo": math.nan,
                    "strength": _sweep_strength(ev["penetration_ticks"]),
                    "meta": json.dumps(
                        {
                            "side": ev["side"],
                            "pool_members": ev["pool_members"],
                            "penetration_ticks": ev["penetration_ticks"],
                            "close_back_ticks": ev["close_back_ticks"],
                            "reclose_bars": ev["reclose_bars"],
                            "pool_age_bars": ev["pool_age_bars"],
                        },
                        sort_keys=True,
                    ),
                }
            )
        rows.sort(key=lambda r: (r["ts"], r["event_type"], r["direction"]))
        return build_event_frame(rows)

    def planted_cases(self) -> list[CalibrationCase]:
        from qrf.trading.concepts.neelprajna.fixtures import liquidity_sweep_cases

        return liquidity_sweep_cases()


__all__ = ["LiquiditySweepDetector", "FAMILY"]
