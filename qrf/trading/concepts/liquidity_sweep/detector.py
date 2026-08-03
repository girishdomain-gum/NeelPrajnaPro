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

No significance/edge/outcome field exists anywhere in this module's
observations (AM-01 C3) -- this detector reports what it saw, never
whether it mattered.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

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
class SweepObservation(Observation):
    side: str = HIGH
    direction: int = 0
    level: float = 0.0
    pool_formation_bar: int = 0
    penetration_bar: int = 0
    sweep_bar: int = 0
    reclose_bars: int = 0
    max_penetration: float = 0.0


@dataclass
class _PivotRecord:
    formation_index: int
    price: float


@dataclass
class _Pool:
    side: str
    level: float
    formation_bar: int
    penetration_bar: int | None = None
    max_penetration: float = 0.0


@dataclass(frozen=True)
class DetectionCounts:
    """Diagnostic counts for parity-checking against Appendix B §B.6.
    NOT part of the SDK's ObservationSet (that stays minimal, C3-clean);
    this is a separate, explicitly non-authoritative side channel used
    only to compare against the pinned reproduction numbers.
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


def _run(bars: Sequence[Bar]) -> tuple[list[SweepObservation], DetectionCounts]:
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
    sweeps: list[SweepObservation] = []
    pool_count = 0

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
                    sweeps.append(
                        SweepObservation(
                            kind="SWEEP",
                            side=pool.side,
                            direction=-1 if is_high else 1,
                            level=pool.level,
                            pool_formation_bar=pool.formation_bar,
                            penetration_bar=pool.penetration_bar,
                            sweep_bar=i,
                            reclose_bars=0,
                            max_penetration=pool.max_penetration,
                        )
                    )
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
                    sweeps.append(
                        SweepObservation(
                            kind="SWEEP",
                            side=pool.side,
                            direction=-1 if is_high else 1,
                            level=pool.level,
                            pool_formation_bar=pool.formation_bar,
                            penetration_bar=p,
                            sweep_bar=i,
                            reclose_bars=i - p,
                            max_penetration=pool.max_penetration,
                        )
                    )
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
                member_prices = [e.price for e in mates] + [r_price]
                level = max(member_prices) if side == HIGH else min(member_prices)
                suppressed = any(
                    p.side == side and abs(p.level - level) <= POOL_TOL for p in active
                )
                if not suppressed:
                    active.append(_Pool(side=side, level=level, formation_bar=i))
                    pool_count += 1
            hist.append(_PivotRecord(formation_index=formation_index, price=r_price))

    return sweeps, DetectionCounts(pivots=pivot_count, pools=pool_count, sweeps=len(sweeps))


class LiquiditySweepDetector(Detector):
    def detect(self, data: Sequence[Bar], config: DetectorConfig) -> ObservationSet:
        sweeps, _counts = _run(data)
        return ObservationSet(
            detector_name=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            source_sha256=config.source_sha256,
            span_start_utc=config.span_start_utc,
            span_end_utc=config.span_end_utc,
            observations=tuple(sweeps),
        )

    def detect_with_counts(
        self, data: Sequence[Bar], config: DetectorConfig
    ) -> tuple[ObservationSet, DetectionCounts]:
        """Same as `detect()`, plus the diagnostic pivot/pool/sweep counts
        for parity-checking against Appendix B §B.6. Not part of the SDK
        interface -- a detector-specific extra, used only by tests/tools.
        """
        sweeps, counts = _run(data)
        obs_set = ObservationSet(
            detector_name=DETECTOR_NAME,
            detector_version=DETECTOR_VERSION,
            source_sha256=config.source_sha256,
            span_start_utc=config.span_start_utc,
            span_end_utc=config.span_end_utc,
            observations=tuple(sweeps),
        )
        return obs_set, counts
