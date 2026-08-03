"""Liquidity sweep detector (H-07 track), implementing the Detector SDK
(AM-01) against NP-ADR-008 §5 v1.1 AS PINNED BY APPENDIX B
(reference/NeelPrajnaPro_v1/docs/legacy/ops/
NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md), re-implemented from
that pinned text -- never from §5 v1.0 (a different, frozen-forever
definition; AM-02 forbids consulting it as a specification) and never
from the previous era's code.

FROZEN CONSTANTS (A-012 §2.3): changing ANY of these mints a NEW detector
version, never a configuration of this one -- they are module constants,
not constructor parameters, on purpose.
  TICK_SIZE = 0.01           (agrees with S03's corrected digits=2 pin)
  POOL_TOL_TICKS = 30        -> pool_tol = 0.30
  MIN_PEN_TICKS = 5          -> min_pen = 0.05
  PIVOT_K = 3
  MEMBER_WINDOW = 200 bars
  RECLOSE_WINDOW = 2 bars
  TIMEFRAME_SECONDS = 300    (M5)

MECHANICS, per Appendix B (each letter below is that section):
  B.1 a pivot is visible only at its confirmation bar (formation + k);
  B.2 pool membership is a STAR centred on the newest pivot (never a
      transitive chain), against a same-side history pruned to formation
      indices within MEMBER_WINDOW of the confirming bar; the confirming
      pivot joins history only AFTER the mate search;
  B.3 level is frozen at formation; an active same-side pool within
      pool_tol of a candidate's level suppresses that candidate entirely
      (resolved pools do not suppress);
  B.4 per bar: sweep/invalidation checks run BEFORE new pools form, so a
      pool can never form and be swept on the same bar;
  B.5 reclose is tested before expiry at every bar from the first
      penetration on; invalidation fires the first bar the reclose
      window (2 bars) is exceeded without a reclose.

EVENTS (A-013 R1): the definition is the two-event chain POOL_FORMED ->
SWEEP (invalidation is silent -- resolved, no event, per B.5). Both are
first-class `Observation`s in the SDK's `ObservationSet`, provenance-bound
like everything else (C1) -- a pool count reachable only through a
side channel outside the SDK would be exactly the C1 violation the SDK
exists to forbid. `detect_with_counts()` remains as a convenience for
parity-checking, but every count it reports is now also derivable from
`detect()`'s own output.

No significance/edge/outcome field exists anywhere in this module's
observations (AM-01 C3) -- this detector reports what it saw, never
whether it mattered. The audit fields added per A-013 R2 (pool_members,
penetration_ticks, close_back_ticks, pool_age_bars) are NEVER
load-bearing for a verdict -- they exist only so a human can reconstruct
why an event fired.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from qrf.kernel.detection.interface import Detector
from qrf.kernel.detection.types import Bar, DetectorConfig, Observation, ObservationSet

DETECTOR_NAME = "liquidity_sweep"
DETECTOR_VERSION = "H-07-v1.1-appendixB"

TICK_SIZE = 0.01
POOL_TOL_TICKS = 30
MIN_PEN_TICKS = 5
PIVOT_K = 3
MEMBER_WINDOW = 200
RECLOSE_WINDOW = 2
TIMEFRAME_SECONDS = 300

POOL_TOL = POOL_TOL_TICKS * TICK_SIZE
MIN_PEN = MIN_PEN_TICKS * TICK_SIZE

HIGH = "HIGH"
LOW = "LOW"


@dataclass(frozen=True)
class PoolFormedObservation(Observation):
    side: str = HIGH
    direction: int = 0
    level: float = 0.0
    formation_bar: int = 0
    pool_members: tuple[float, ...] = ()


@dataclass(frozen=True)
class SweepObservation(Observation):
    side: str = HIGH
    direction: int = 0
    level: float = 0.0
    pool_formation_bar: int = 0
    pool_members: tuple[float, ...] = ()
    penetration_bar: int = 0
    sweep_bar: int = 0
    reclose_bars: int = 0
    pool_age_bars: int = 0
    max_penetration: float = 0.0
    penetration_ticks: float = 0.0
    close_back_ticks: float = 0.0


@dataclass
class _PivotRecord:
    formation_index: int
    price: float


@dataclass
class _Pool:
    side: str
    level: float
    formation_bar: int
    members: tuple[float, ...] = field(default_factory=tuple)
    penetration_bar: int | None = None
    max_penetration: float = 0.0


@dataclass(frozen=True)
class DetectionCounts:
    """Convenience counts for parity-checking against Appendix B §B.6.
    Every number here is derivable from `detect()`'s own ObservationSet
    (pivots aside, which are not events at all under v1.1 and so are not
    observations) -- this is not a second source of truth, just a
    shortcut for tooling.
    """

    pivots: int
    pools: int
    sweeps: int


def _is_pivot_high(highs: Sequence[float], i: int, k: int) -> bool:
    v = highs[i]
    return all(v > highs[j] for j in range(i - k, i)) and all(
        v > highs[j] for j in range(i + 1, i + k + 1)
    )


def _is_pivot_low(lows: Sequence[float], i: int, k: int) -> bool:
    v = lows[i]
    return all(v < lows[j] for j in range(i - k, i)) and all(
        v < lows[j] for j in range(i + 1, i + k + 1)
    )


def _run(bars: Sequence[Bar]) -> tuple[list[Observation], DetectionCounts]:
    n = len(bars)
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    closes = [b.close for b in bars]

    confirmations: dict[int, list[tuple[str, int]]] = {}
    for i in range(PIVOT_K, n - PIVOT_K):
        c = i + PIVOT_K
        if _is_pivot_high(highs, i, PIVOT_K):
            confirmations.setdefault(c, []).append((HIGH, i))
        if _is_pivot_low(lows, i, PIVOT_K):
            confirmations.setdefault(c, []).append((LOW, i))
    pivot_count = sum(len(v) for v in confirmations.values())

    history: dict[str, list[_PivotRecord]] = {HIGH: [], LOW: []}
    active: list[_Pool] = []
    observations: list[Observation] = []
    pool_count = 0
    sweep_count = 0

    for i in range(n):
        # B.4: sweep/invalidation checks run FIRST, against every pool
        # already active -- a pool formed later this same bar (step
        # below) is never checked here.
        still_active: list[_Pool] = []
        for pool in active:
            is_high = pool.side == HIGH
            if pool.penetration_bar is None:
                penetrating = (
                    (highs[i] >= pool.level + MIN_PEN)
                    if is_high
                    else (lows[i] <= pool.level - MIN_PEN)
                )
                if not penetrating:
                    still_active.append(pool)
                    continue
                pool.penetration_bar = i
                pool.max_penetration = max(
                    0.0, (highs[i] - pool.level) if is_high else (pool.level - lows[i])
                )
                recloses = (closes[i] < pool.level) if is_high else (closes[i] > pool.level)
                if recloses:
                    close_back = (pool.level - closes[i]) if is_high else (closes[i] - pool.level)
                    observations.append(
                        SweepObservation(
                            kind="SWEEP",
                            side=pool.side,
                            direction=-1 if is_high else 1,
                            level=pool.level,
                            pool_formation_bar=pool.formation_bar,
                            pool_members=pool.members,
                            penetration_bar=pool.penetration_bar,
                            sweep_bar=i,
                            reclose_bars=0,
                            pool_age_bars=i - pool.formation_bar,
                            max_penetration=pool.max_penetration,
                            penetration_ticks=pool.max_penetration / TICK_SIZE,
                            close_back_ticks=max(0.0, close_back) / TICK_SIZE,
                        )
                    )
                    sweep_count += 1
                    # resolved: swept, dropped from active
                else:
                    still_active.append(pool)
            else:
                p = pool.penetration_bar
                depth_i = max(
                    0.0, (highs[i] - pool.level) if is_high else (pool.level - lows[i])
                )
                if depth_i > pool.max_penetration:
                    pool.max_penetration = depth_i
                recloses = (closes[i] < pool.level) if is_high else (closes[i] > pool.level)
                if recloses:
                    close_back = (pool.level - closes[i]) if is_high else (closes[i] - pool.level)
                    observations.append(
                        SweepObservation(
                            kind="SWEEP",
                            side=pool.side,
                            direction=-1 if is_high else 1,
                            level=pool.level,
                            pool_formation_bar=pool.formation_bar,
                            pool_members=pool.members,
                            penetration_bar=p,
                            sweep_bar=i,
                            reclose_bars=i - p,
                            pool_age_bars=i - pool.formation_bar,
                            max_penetration=pool.max_penetration,
                            penetration_ticks=pool.max_penetration / TICK_SIZE,
                            close_back_ticks=max(0.0, close_back) / TICK_SIZE,
                        )
                    )
                    sweep_count += 1
                    # resolved: swept, dropped from active
                elif i - p >= RECLOSE_WINDOW:
                    pass  # resolved: invalidated, no event, dropped from active
                else:
                    still_active.append(pool)
        active = still_active

        # then: pivots confirming at this bar become new pools
        for side, formation_index in confirmations.get(i, []):
            r_price = highs[formation_index] if side == HIGH else lows[formation_index]
            hist = history[side]
            hist[:] = [e for e in hist if (i - e.formation_index) <= MEMBER_WINDOW]
            mates = [e for e in hist if abs(e.price - r_price) <= POOL_TOL]
            if mates:
                member_prices = tuple([e.price for e in mates] + [r_price])
                level = max(member_prices) if side == HIGH else min(member_prices)
                suppressed = any(
                    p.side == side and abs(p.level - level) <= POOL_TOL for p in active
                )
                if not suppressed:
                    active.append(
                        _Pool(side=side, level=level, formation_bar=i, members=member_prices)
                    )
                    pool_count += 1
                    observations.append(
                        PoolFormedObservation(
                            kind="POOL_FORMED",
                            side=side,
                            direction=-1 if side == HIGH else 1,
                            level=level,
                            formation_bar=i,
                            pool_members=member_prices,
                        )
                    )
            hist.append(_PivotRecord(formation_index=formation_index, price=r_price))

    return observations, DetectionCounts(pivots=pivot_count, pools=pool_count, sweeps=sweep_count)


class LiquiditySweepDetector(Detector):
    def detect(self, data: Sequence[Bar], config: DetectorConfig) -> ObservationSet:
        observations, _counts = _run(data)
        return ObservationSet(
            detector_name=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            source_sha256=config.source_sha256,
            span_start_utc=config.span_start_utc,
            span_end_utc=config.span_end_utc,
            observations=tuple(observations),
        )

    def detect_with_counts(
        self, data: Sequence[Bar], config: DetectorConfig
    ) -> tuple[ObservationSet, DetectionCounts]:
        """Same as `detect()`, plus pivot/pool/sweep counts as a
        convenience for parity-checking against Appendix B §B.6 -- pools
        and sweeps are also directly countable from `detect()`'s own
        ObservationSet by `kind`; this just saves the caller from doing
        that arithmetic itself.
        """
        observations, counts = _run(data)
        obs_set = ObservationSet(
            detector_name=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            source_sha256=config.source_sha256,
            span_start_utc=config.span_start_utc,
            span_end_utc=config.span_end_utc,
            observations=tuple(observations),
        )
        return obs_set, counts
