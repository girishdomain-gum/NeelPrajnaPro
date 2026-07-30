"""neelprajna.liquidity_sweep — H-07 detector, §5 v1.1 (NP-ADR-008 sealed).

Implements exactly NP-ADR-008 §3's two-event chain: **POOL_FORMED → SWEEP**.
There is no third event — REVERSAL_CONFIRMED / MSS does not exist in this
lineage (that is the entire content of the v1.0 → v1.1 divergence; see the ADR
§2). ``qrf/trading/concepts/neelprajna/reference_configs/`` (the MQL5
``T3_SweepFVGGate.mqh`` v2.1 pool engine) and the retired
``np_feature_service.py`` are reference only — §5 v1.1 below is normative.

**Frozen parameters** (identity-defining; changing any of them mints a NEW
lineage per NP-ADR-008 M1, never an edit to this one): bar timeframe 300s (M5,
single) · pivot_k 3 · member window 200 bars · pool_tol 30.0 ticks fixed ·
min_pen 5.0 ticks · reclose_window 2 bars · tick_size 0.01 (XAUUSD). The
constructor still accepts ``params`` (matching the Detector contract every
other concept plug-in uses) so the instrument registry can record what ran,
but a sealed H-07 registration must never override these defaults — an
override away from them is definitionally a different, unsealed detector.

**Clauses v1.1 does NOT inherit from v1.0** (ADR §3, "does NOT inherit"):
v1.0 required the exec bar to open inside the defended side and excluded
gap-through opens. The evidenced Python lineage never reads the bar ``open``,
so this detector reads only ``high``, ``low``, ``close`` — never ``open``.

Algorithm (single forward pass, streaming — the anti-hindsight contract):

* **Pivot confirmation.** Bar ``i`` is a pivot HIGH iff ``high[i]`` is
  strictly greater than ``high[i-pivot_k .. i-1]`` and ``high[i+1 ..
  i+pivot_k]``; pivot LOW is the mirror on ``low``. A pivot at bar ``i`` is
  only *knowable* once bar ``i+pivot_k`` has arrived — that is its
  confirmation bar, and it is also the earliest an emission may reference it.
* **POOL_FORMED.** On each newly confirmed pivot, cluster it with same-side
  pivots confirmed so far whose own bar index falls in the trailing
  ``member_window_bars`` (inclusive of the new pivot's bar) and whose price is
  within ``pool_tol`` of the new pivot's price. A cluster of ≥2 members forms
  a pool, level = max (HIGH side) / min (LOW side) of member prices, frozen at
  formation. Refused if within ``pool_tol`` of an already-active same-side
  pool (no duplicate/overlapping pools). Emitted at the confirmation bar's
  ``ts`` (close time).
* **SWEEP.** For each active pool, on every subsequent bar: a HIGH pool is
  *penetrated* when ``high[bar] >= level + min_pen``; a LOW pool when
  ``low[bar] <= level - min_pen``. If the penetration bar's own ``close``
  is already back on the defended side (below ``level`` for HIGH, above for
  LOW), SWEEP fires on that bar (``reclose_bars = 0``). Otherwise the
  following ``reclose_window_bars`` (2) bars are watched for a close back on
  the defended side; the deepest wick reached across the window is retained
  as the emitted penetration. A reclose within the window fires SWEEP on the
  bar it happens; no reclose by the window's end resolves the pool as an
  **invalidation** — pool removed from active state, no event emitted.
* **No REVERSAL_CONFIRMED.** A pool that sweeps is simply resolved; nothing
  else is emitted for it.
* A pool becomes breach-eligible starting the bar *after* its formation bar
  (it cannot be swept on the very bar it forms) — a deterministic, documented
  choice where the ADR is silent on same-bar formation-and-breach ordering.

``strength``/``direction``/``zone_hi``/``zone_lo`` encodings below are
detector-level presentation choices (the ADR is silent on them — its
normative content is event *existence and timing*, which is what the E2
arrangement claim and the Battery consume): ``direction`` is +1 for the
HIGH/upper side, -1 for the LOW/lower side (which side of the market the
event concerns; SWEEP's implied *trade* bias per the prediction-layer
playbook is the opposite of this — a HIGH-pool sweep is a SELL signal). POOL
``strength`` is member-count confidence, clamped; SWEEP ``strength`` is
penetration depth relative to ``min_pen``, clamped. Neither is Battery-facing
for the E2 existence claim (event ts/type only); the prediction claim reads
them as auxiliary, non-normative colour.
"""

from __future__ import annotations

import json
import math
from typing import Any

import pyarrow as pa

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import CalibrationCase, build_event_frame

# Frozen identity (NP-ADR-008 §3). Do not change; a change is a new lineage.
PIVOT_K = 3
MEMBER_WINDOW_BARS = 200
POOL_TOL_TICKS = 30.0
MIN_PEN_TICKS = 5.0
RECLOSE_WINDOW_BARS = 2
TICK_SIZE = 0.01

_SIDE_HIGH = "high"
_SIDE_LOW = "low"


class _Pivot:
    __slots__ = ("side", "bar_index", "price", "confirmed_at")

    def __init__(self, side: str, bar_index: int, price: float, confirmed_at: int) -> None:
        self.side = side
        self.bar_index = bar_index
        self.price = price
        self.confirmed_at = confirmed_at


class _Pool:
    __slots__ = ("side", "level", "n_members", "formed_at_index", "pending")

    def __init__(self, side: str, level: float, n_members: int, formed_at_index: int) -> None:
        self.side = side
        self.level = level
        self.n_members = n_members
        self.formed_at_index = formed_at_index
        # Pending-sweep tracking, set once penetrated; None while merely active.
        self.pending: dict[str, Any] | None = None


def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


class LiquiditySweepDetector:
    """H-07 §5 v1.1 detector: POOL_FORMED -> SWEEP over M5 mid bars."""

    instrument_id = "neelprajna.liquidity_sweep"
    family = "neelprajna"
    kind = "detector"
    code_ref = (
        "qrf.trading.concepts.neelprajna.liquidity_sweep:LiquiditySweepDetector"
    )

    params_schema = {
        "pivot_k": "int  # bars each side required to confirm a swing pivot",
        "member_window_bars": "int  # trailing lookback for same-side pool clustering",
        "pool_tol_ticks": "float  # clustering tolerance, in ticks",
        "min_pen_ticks": "float  # minimum wick penetration to count as a sweep, in ticks",
        "reclose_window_bars": "int  # bars after penetration allowed to reclose",
        "tick_size": "float  # price per tick for this instrument",
    }

    def __init__(self, *, version: str = "1.1.0", params: dict[str, Any] | None = None) -> None:
        self.version = version
        p = dict(params or {})
        self.pivot_k = int(p.get("pivot_k", PIVOT_K))
        self.member_window_bars = int(p.get("member_window_bars", MEMBER_WINDOW_BARS))
        self.pool_tol_ticks = float(p.get("pool_tol_ticks", POOL_TOL_TICKS))
        self.min_pen_ticks = float(p.get("min_pen_ticks", MIN_PEN_TICKS))
        self.reclose_window_bars = int(p.get("reclose_window_bars", RECLOSE_WINDOW_BARS))
        self.tick_size = float(p.get("tick_size", TICK_SIZE))
        if self.pivot_k < 1:
            raise ValueError("pivot_k must be >= 1")
        if self.member_window_bars < 1:
            raise ValueError("member_window_bars must be >= 1")
        if self.pool_tol_ticks <= 0 or self.min_pen_ticks <= 0:
            raise ValueError("pool_tol_ticks and min_pen_ticks must be > 0")
        if self.reclose_window_bars < 0:
            raise ValueError("reclose_window_bars must be >= 0")
        if self.tick_size <= 0:
            raise ValueError("tick_size must be > 0")
        self.params = {
            "pivot_k": self.pivot_k,
            "member_window_bars": self.member_window_bars,
            "pool_tol_ticks": self.pool_tol_ticks,
            "min_pen_ticks": self.min_pen_ticks,
            "reclose_window_bars": self.reclose_window_bars,
            "tick_size": self.tick_size,
        }
        self._pool_tol = self.pool_tol_ticks * self.tick_size
        self._min_pen = self.min_pen_ticks * self.tick_size

    # -- detection --------------------------------------------------------
    def detect(self, data: pa.Table) -> pa.Table:
        for col in ("ts", "high", "low", "close"):
            if col not in data.column_names:
                raise SchemaViolation(
                    f"liquidity_sweep detector requires a {col!r} column"
                )
        ts = data.column("ts").to_pylist()
        high = data.column("high").to_pylist()
        low = data.column("low").to_pylist()
        close = data.column("close").to_pylist()
        n = len(ts)

        rows: list[dict[str, Any]] = []
        pivots: dict[str, list[_Pivot]] = {_SIDE_HIGH: [], _SIDE_LOW: []}
        active_pools: list[_Pool] = []
        k = self.pivot_k

        for i in range(n):
            # 1. Advance every active pool at this bar: for a pool not yet
            #    breached, this checks for a fresh breach (and, if one starts
            #    right here, evaluates the same-bar reclose immediately); for
            #    a pool already pending, this advances its reclose window.
            #    A pool formed at bar i (step 3 below) is not checked until
            #    i+1 — it cannot be swept on the very bar it forms.
            still_active: list[_Pool] = []
            for pool in active_pools:
                resolved = self._advance_pool(pool, i, high, low, close, ts, rows)
                if not resolved:
                    still_active.append(pool)
            active_pools = still_active

            # 2. Confirm a pivot centered at i-k (needs k bars on each side).
            center = i - k
            if center >= k:
                if self._is_pivot_high(center, k, high):
                    piv = _Pivot(_SIDE_HIGH, center, high[center], i)
                    self._form_pool_if_clustered(
                        piv, pivots[_SIDE_HIGH], active_pools, i, ts, rows
                    )
                    pivots[_SIDE_HIGH].append(piv)
                if self._is_pivot_low(center, k, low):
                    piv = _Pivot(_SIDE_LOW, center, low[center], i)
                    self._form_pool_if_clustered(
                        piv, pivots[_SIDE_LOW], active_pools, i, ts, rows
                    )
                    pivots[_SIDE_LOW].append(piv)

        return build_event_frame(rows)

    @staticmethod
    def _is_pivot_high(center: int, k: int, high: list[float]) -> bool:
        v = high[center]
        for j in range(1, k + 1):
            if high[center - j] >= v or high[center + j] >= v:
                return False
        return True

    @staticmethod
    def _is_pivot_low(center: int, k: int, low: list[float]) -> bool:
        v = low[center]
        for j in range(1, k + 1):
            if low[center - j] <= v or low[center + j] <= v:
                return False
        return True

    def _form_pool_if_clustered(
        self,
        new_pivot: _Pivot,
        history: list[_Pivot],
        active_pools: list[_Pool],
        confirm_bar_index: int,
        ts: list[int],
        rows: list[dict[str, Any]],
    ) -> None:
        lo_bar = new_pivot.bar_index - self.member_window_bars + 1
        members = [
            p
            for p in history
            if p.bar_index >= lo_bar
            and abs(p.price - new_pivot.price) <= self._pool_tol
        ]
        members.append(new_pivot)
        if len(members) < 2:
            return
        level = (
            max(p.price for p in members)
            if new_pivot.side == _SIDE_HIGH
            else min(p.price for p in members)
        )
        for pool in active_pools:
            if pool.side == new_pivot.side and abs(pool.level - level) <= self._pool_tol:
                return  # too close to an already-active same-side pool
        pool = _Pool(new_pivot.side, level, len(members), confirm_bar_index)
        active_pools.append(pool)
        strength = _clamp01(len(members) / 4.0)
        direction = 1 if new_pivot.side == _SIDE_HIGH else -1
        rows.append(
            {
                "ts": ts[confirm_bar_index],
                "event_type": "neelprajna.liquidity_sweep.pool_formed",
                "direction": direction,
                "level": level,
                "zone_hi": level,
                "zone_lo": level,
                "strength": strength,
                "meta": json.dumps(
                    {"side": new_pivot.side, "n_members": len(members)}, sort_keys=True
                ),
            }
        )

    def _maybe_breach(
        self, pool: _Pool, i: int, high: list[float], low: list[float]
    ) -> None:
        if pool.side == _SIDE_HIGH:
            if high[i] >= pool.level + self._min_pen:
                pool.pending = {"breach_index": i, "extreme": high[i]}
        else:
            if low[i] <= pool.level - self._min_pen:
                pool.pending = {"breach_index": i, "extreme": low[i]}

    def _advance_pool(
        self,
        pool: _Pool,
        i: int,
        high: list[float],
        low: list[float],
        close: list[float],
        ts: list[int],
        rows: list[dict[str, Any]],
    ) -> bool:
        """Advance ``pool``'s pending sweep window at bar ``i``. Returns True if resolved."""
        if pool.pending is None:
            # Not yet breached; also check for a same-bar breach so a fresh
            # active pool can be swept on its very first eligible bar.
            self._maybe_breach(pool, i, high, low)
            if pool.pending is None:
                return False
            # Fall through: freshly breached this bar, evaluate same-bar reclose below.

        pend = pool.pending
        breach_index = pend["breach_index"]
        if i < breach_index:
            return False
        # Track the deepest wick reached so far (including this bar, if later).
        if i > breach_index:
            if pool.side == _SIDE_HIGH:
                if high[i] > pend["extreme"]:
                    pend["extreme"] = high[i]
            else:
                if low[i] < pend["extreme"]:
                    pend["extreme"] = low[i]

        reclosed = (
            close[i] < pool.level if pool.side == _SIDE_HIGH else close[i] > pool.level
        )
        bars_since_breach = i - breach_index
        if reclosed:
            penetration_ticks = (
                (pend["extreme"] - pool.level) / self.tick_size
                if pool.side == _SIDE_HIGH
                else (pool.level - pend["extreme"]) / self.tick_size
            )
            strength = _clamp01(penetration_ticks / (self.min_pen_ticks * 3.0))
            direction = 1 if pool.side == _SIDE_HIGH else -1
            zone_hi = pend["extreme"] if pool.side == _SIDE_HIGH else pool.level
            zone_lo = pool.level if pool.side == _SIDE_HIGH else pend["extreme"]
            rows.append(
                {
                    "ts": ts[i],
                    "event_type": "neelprajna.liquidity_sweep.sweep",
                    "direction": direction,
                    "level": pool.level,
                    "zone_hi": zone_hi,
                    "zone_lo": zone_lo,
                    "strength": strength,
                    "meta": json.dumps(
                        {
                            "side": pool.side,
                            "reclose_bars": bars_since_breach,
                            "penetration_ticks": penetration_ticks,
                        },
                        sort_keys=True,
                    ),
                }
            )
            return True
        if bars_since_breach >= self.reclose_window_bars:
            return True  # invalidation: resolved, silent
        return False

    # -- calibration --------------------------------------------------------
    def planted_cases(self) -> list[CalibrationCase]:
        from qrf.trading.concepts.neelprajna.fixtures import liquidity_sweep_cases

        return liquidity_sweep_cases()
