"""S08 Phase 1, the ACCEPTANCE TEST for the circular-shift null (A-035),
run on the exact same fixture as tests/kernel/test_s08_power_check.py
(the one that exposed F-09: the old block-resampling null was BLIND to
a real, population-wide effect at the real block_length).

SKIPPED BY DEFAULT for the same reason as the v1 power check: several
minutes of real compute (though the circular-shift null itself is now
much cheaper than block-resampling, since detection never re-runs
inside the null -- most of the time here is the ONE real detect() call
plus fixture construction, not N resample computations).

THE RESULT (recorded here because it is the actual finding -- full
transcript at
F:\\NeelPrajnaProData\\reports\\S08\\rehearsal\\power_check_v2_output.txt):

  CONVICT (jittered effect, 170 events, realistic magnitude): p = 0.002 -- SIGNIFICANT
  ACQUIT  (no effect, pure random walk):                       p = 0.830 -- not significant
  MONOTONIC IMPROVEMENT (the specific acceptance criterion, A-035):
    0.05x magnitude: p = 0.094 (not significant)
    0.2x  magnitude: p = 0.002 (significant)
    1x    magnitude: p = 0.002 (significant, floor-saturated at N=500 --
                                min achievable p = 1/(1+500) = 0.001996;
                                both 0.2x and 1x hit every one of the 500
                                null resamples below the observed value)

Contrast with the OLD null (F-09, D-024): a 10x LARGER effect made p
WORSE (0.561 -> 0.762). Here, increasing effect size from 0.05x to 0.2x
makes p dramatically BETTER (0.094 -> 0.002), and effect strengths at or
above the realistic 1x magnitude all saturate the estimator's floor
rather than degrading -- the opposite failure mode, and the correct one.

BOTH HALVES OF A-035'S ACCEPTANCE TEST PASS. Per A-035 R2, `excluded`
was 0 in every run -- no qualifying event's horizon ran past the end of
a 51,000-bar series (expected; horizon=10 bars is negligible against
that scale).
"""

import random
import time

import pytest

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.kernel.measurement.circular_shift_null import run_circular_shift_null_test
from qrf.kernel.measurement.ls01_r001 import (
    HORIZON,
    ls01_r001_statistic,
    qualifying_events_with_valid_horizon,
)
from qrf.kernel.null.resampling import block_length_from_detector
from qrf.trading.concepts.liquidity_sweep.detector import MEMBER_WINDOW, LiquiditySweepDetector
from qrf.trading.concepts.market_structure_shift.detector import MarketStructureShiftDetector

SPACING = 300
FOOTPRINT = 70


def _plant_jittered_magnitude(highs, lows, closes, offset, base, slope):
    highs[offset + 10] = base + 0.8
    highs[offset + 30] = base + 1.8
    lows[offset + 20] = base - 1.0
    lows[offset + 40] = base - 0.6
    closes[offset + 50] = base - 1.0
    highs[offset + 25] = base + 0.8
    highs[offset + 45] = base + 1.0
    highs[offset + 55] = base + 1.06
    closes[offset + 55] = base + 0.8
    for i in range(offset + 56, offset + 66):
        closes[i] = (base + 0.8) - (i - (offset + 55)) * slope
        highs[i] = max(highs[i], closes[i] + 0.1)
        lows[i] = min(lows[i], closes[i] - 0.1)


def build_effect_bars(n_bars, seed=101, mag_lo=0.15, mag_hi=0.75):
    highs = [0.0] * n_bars
    lows = [0.0] * n_bars
    closes = [0.0] * n_bars
    rng = random.Random(seed)
    base_price = 100.0
    offsets = list(range(0, n_bars - FOOTPRINT, SPACING))
    planted = set()
    for off in offsets:
        for i in range(off, min(off + FOOTPRINT, n_bars)):
            highs[i] = base_price + 0.2
            lows[i] = base_price - 0.2
            closes[i] = base_price
        planted.update(range(off, min(off + FOOTPRINT, n_bars)))
        slope = rng.uniform(mag_lo, mag_hi)
        _plant_jittered_magnitude(highs, lows, closes, off, base_price, slope)
        base_price += rng.uniform(0.3, 1.0)

    close = 100.0
    for i in range(n_bars):
        if i not in planted:
            close += rng.uniform(-0.02, 0.02)
            closes[i] = close
            highs[i] = close + 0.05
            lows[i] = close - 0.05
        else:
            close = closes[i]

    bars = tuple(
        Bar(time=i * 300, open=closes[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n_bars)
    )
    return bars, len(offsets)


def build_no_effect_bars(n_bars, seed=202):
    rng = random.Random(seed)
    close = 100.0
    closes = []
    for _ in range(n_bars):
        close += rng.uniform(-0.15, 0.15)
        closes.append(close)
    return tuple(
        Bar(
            time=i * 300, open=closes[i], high=closes[i] + 0.15, low=closes[i] - 0.15,
            close=closes[i],
        )
        for i in range(n_bars)
    )


def run_power_check_v2(bars, label, n_resamples=500, seed=1):
    cfg = DetectorConfig(
        source_sha256="0" * 64, span_start_utc=bars[0].time, span_end_utc=bars[-1].time
    )
    t0 = time.time()
    sweep_set = LiquiditySweepDetector().detect(bars, cfg)
    shift_set = MarketStructureShiftDetector().detect(bars, cfg)
    t1 = time.time()

    valid, excluded = qualifying_events_with_valid_horizon(
        sweep_set.observations, shift_set.observations, bars
    )
    observed_statistic = ls01_r001_statistic(sweep_set.observations, shift_set.observations, bars)
    min_offset = block_length_from_detector(MEMBER_WINDOW)

    print(
        f"[{label}] n_bars={len(bars)} detect_time={t1 - t0:.2f}s "
        f"qualifying_valid={len(valid)} excluded={excluded} "
        f"observed_statistic={observed_statistic}"
    )

    t2 = time.time()
    result = run_circular_shift_null_test(
        valid, bars, observed_statistic, min_offset, n_resamples, seed, 0.025, excluded, HORIZON
    )
    t3 = time.time()
    print(
        f"[{label}] min_offset={min_offset} n_resamples={n_resamples} "
        f"p_value={result.p_value} significant={result.p_value < 0.025} "
        f"null_time={t3 - t2:.2f}s"
    )
    return result


@pytest.mark.skip(reason="real power check (minutes); run by hand, see D-026/A-035")
def test_v2_convict():
    bars, _n = build_effect_bars(51000)
    result = run_power_check_v2(bars, "convict")
    print(result.p_value)


@pytest.mark.skip(reason="real power check (minutes); run by hand, see D-026/A-035")
def test_v2_acquit():
    bars = build_no_effect_bars(51000)
    result = run_power_check_v2(bars, "acquit")
    print(result.p_value)


@pytest.mark.skip(reason="real power check (minutes); run by hand, see D-026/A-035")
def test_v2_monotonic_improvement():
    for label, lo, hi in [("0.05x", 0.0075, 0.0375), ("0.2x", 0.03, 0.15), ("1x", 0.15, 0.75)]:
        bars, _n = build_effect_bars(51000, mag_lo=lo, mag_hi=hi)
        run_power_check_v2(bars, label)


if __name__ == "__main__":
    print("=== CONVICT (jittered effect) ===")
    effect_bars, n_planted = build_effect_bars(51000)
    print(f"planted {n_planted} independent events")
    run_power_check_v2(effect_bars, "convict")

    print("\n=== ACQUIT (no effect) ===")
    no_effect_bars = build_no_effect_bars(51000)
    run_power_check_v2(no_effect_bars, "acquit")

    print("\n=== MONOTONIC IMPROVEMENT ===")
    for label, lo, hi in [("0.05x", 0.0075, 0.0375), ("0.2x", 0.03, 0.15), ("1x", 0.15, 0.75)]:
        bars, _n = build_effect_bars(51000, mag_lo=lo, mag_hi=hi)
        run_power_check_v2(bars, label)
