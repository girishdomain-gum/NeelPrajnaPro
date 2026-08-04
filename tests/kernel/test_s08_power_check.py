"""S08 Phase 1, R1 (A-033): a power check at the REAL block_length=200
(MEMBER_WINDOW, zero discretion) and REAL alpha=0.025, against a
population shaped like the real one (~20,000-50,000 bars, ~170
qualifying events per D-016's 8.4/1,000 rate), with JITTERED events
(varying decline magnitude, drifting price level) rather than the
byte-identical copies that caused Friction #2 in the first rehearsal
pass.

SKIPPED BY DEFAULT: each run detects over 51,000 bars ~500 times (once
per resample) and takes several minutes -- run by hand, not in CI, same
precedent as `qrf/kernel/observation/launcher.py`'s `run_export()` (no
MT5 terminal in CI) and the S07 EA live-run (A-030 R2). Run directly
with `uv run pytest tests/kernel/test_s08_power_check.py -m slow -s`
or invoke the module as a script.

THE RESULT (recorded here because it is the actual finding, not just
the mechanism to reproduce it -- full transcript at
F:\\NeelPrajnaProData\\reports\\S08\\rehearsal\\power_check_output.txt):

  jittered effect (170 events, realistic magnitude): p = 0.561 -- NOT significant
  10x magnitude, same population:  p = 0.762 -- NOT significant (worse, not better)
  clustered/irregular spacing, realistic magnitude:  p = 0.572 -- NOT significant

All three constructions -- uniform spacing, 10x the magnitude, and a
deliberately IRREGULAR clustered spacing (to rule out "your spacing was
artificially regular") -- land in the same 0.55-0.76 range, nowhere
near 0.025, and scaling magnitude 10x made it WORSE rather than better.
This is not resampling noise (N=100-500 resamples cannot move a p-value
by 0.5) and it did not respond to the one lever a real power problem
should respond to (effect size). The mechanism: a block-bootstrap null
resamples WITH REPLACEMENT from the SAME ~255 blocks of the SAME
51,000-bar array. When the planted effect has roughly CONSTANT density
across the whole series (as every construction here does, by design --
even the "clustered" one still has ~28 events per cluster densely
spaced within each cluster), every resample's own ~255 drawn blocks
also carry that same density almost by construction, so the null
distribution's typical statistic tracks the observed one regardless of
magnitude. The null, AS SPECIFIED, is well-suited to detect a LOCALIZED
temporal dependency; it appears poorly suited to detect a MARGINAL,
population-wide bias with even density -- which is exactly the shape
LS-01-R001's own statistic (a plain mean over all qualifying events) is
built to summarize.

STOPPED HERE, per A-033's explicit instruction: "DO NOT tune anything
to make it pass. If it fails, report the failure and stop." No further
parameter search was attempted after the second and third confirming
runs.
"""

import random
import time

import pytest

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.kernel.measurement.ls01_r001 import ls01_r001_statistic, qualifying_events
from qrf.kernel.null.resampling import block_length_from_detector, run_null_test
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


def build_effect_bars(n_bars, seed=101):
    """~n_bars/SPACING independent events, JITTERED decline magnitude
    (Uniform(0.15, 0.75) slope) and a drifting price level -- deliberately
    NOT byte-identical, per A-033 R1(a).
    """
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
        slope = rng.uniform(0.15, 0.75)
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


def run_power_check(bars, label, n_resamples=500, seed=1):
    """Runs the REAL null machinery (`run_null_test`, the same function
    `Battery.judge()` calls) at the REAL block_length_from_detector
    output and REAL alpha, and reports the honest p-value.
    """
    cfg = DetectorConfig(
        source_sha256="0" * 64, span_start_utc=bars[0].time, span_end_utc=bars[-1].time
    )
    t0 = time.time()
    sweep_set = LiquiditySweepDetector().detect(bars, cfg)
    shift_set = MarketStructureShiftDetector().detect(bars, cfg)
    t1 = time.time()
    q = qualifying_events(sweep_set.observations, shift_set.observations)
    stat = ls01_r001_statistic(sweep_set.observations, shift_set.observations, bars)
    print(
        f"[{label}] n_bars={len(bars)} detect_time={t1 - t0:.2f}s "
        f"sweeps={sum(1 for o in sweep_set.observations if o.kind == 'SWEEP')} "
        f"shifts={sum(1 for o in shift_set.observations if o.kind == 'STRUCTURE_SHIFT')} "
        f"qualifying={len(q)} observed_statistic={stat}"
    )

    block_length = block_length_from_detector(MEMBER_WINDOW)

    def statistic_fn(resampled_bars):
        rsw = LiquiditySweepDetector().detect(resampled_bars, cfg)
        rsh = MarketStructureShiftDetector().detect(resampled_bars, cfg)
        return ls01_r001_statistic(rsw.observations, rsh.observations, resampled_bars)

    t2 = time.time()
    result = run_null_test(
        list(bars), statistic_fn, stat, block_length, n_resamples, seed, alpha=0.025
    )
    t3 = time.time()
    print(
        f"[{label}] block_length={block_length} n_resamples={n_resamples} "
        f"p_value={result.p_value} significant={result.p_value < 0.025} "
        f"null_time={t3 - t2:.1f}s"
    )
    return result


@pytest.mark.skip(reason="expensive real power check (minutes); run by hand, see D-024/A-033 R1")
def test_power_check_jittered_effect_at_real_block_length():
    bars, _n_planted = build_effect_bars(51000)
    result = run_power_check(bars, "effect")
    print(result.p_value)  # NOT asserted significant -- report honestly, see module docstring


@pytest.mark.skip(reason="expensive real power check (minutes); run by hand, see D-024/A-033 R1")
def test_power_check_no_effect_at_real_block_length():
    bars = build_no_effect_bars(51000)
    result = run_power_check(bars, "no-effect")
    print(result.p_value)


if __name__ == "__main__":
    N = 51000
    print("=== WITH JITTERED EFFECT ===")
    effect_bars, n_planted = build_effect_bars(N)
    print(f"planted {n_planted} independent events across {N} bars")
    run_power_check(effect_bars, "effect")

    print("\n=== NO EFFECT (pure random walk) ===")
    no_effect_bars = build_no_effect_bars(N)
    run_power_check(no_effect_bars, "no-effect")
