"""Fair Value Gap detector drills (docs/detectors/fair_value_gap.md)."""

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.trading.concepts.fair_value_gap.detector import (
    BEARISH,
    BULLISH,
    FairValueGapDetector,
)

_CONFIG = DetectorConfig(source_sha256="0" * 64, span_start_utc=0, span_end_utc=1)


def _bars(n, high=None, low=None, base_high=100.0, base_low=99.0, base_close=99.5):
    highs = [base_high] * n
    lows = [base_low] * n
    for d, arr in ((high, highs), (low, lows)):
        if d:
            for idx, val in d.items():
                arr[idx] = val
    return tuple(
        Bar(time=i * 300, open=base_close, high=highs[i], low=lows[i], close=base_close)
        for i in range(n)
    )


def _detect(bars):
    return FairValueGapDetector().detect(bars, _CONFIG)


def test_planted_truth_bullish_gap():
    bars = _bars(10, low={4: 101.0})  # high[2]=100 (baseline) < low[4]=101
    obs_set = _detect(bars)
    gap = next(o for o in obs_set.observations if o.first_bar == 2)
    assert gap.side == BULLISH
    assert gap.third_bar == 4
    assert gap.gap_low == 100.0
    assert gap.gap_high == 101.0
    assert gap.gap_size == 1.0
    assert obs_set.source_sha256 == "0" * 64


def test_planted_truth_bearish_gap_mirror():
    bars = _bars(10, high={7: 98.0})  # low[5]=99 (baseline) > high[7]=98
    obs_set = _detect(bars)
    gap = next(o for o in obs_set.observations if o.first_bar == 5)
    assert gap.side == BEARISH
    assert gap.third_bar == 7
    assert gap.gap_low == 98.0
    assert gap.gap_high == 99.0
    assert gap.gap_size == 1.0


# --- clean control: plausible near-miss, not empty data -------------------


def test_clean_control_touching_bars_are_not_a_gap():
    """Ambiguity resolved in the definition doc Sec1: strict inequality.
    high[i] == low[i+2] touches with zero width -- not a gap.
    """
    bars = _bars(10, low={4: 100.0})  # high[2]=100 == low[4]=100 exactly
    obs_set = _detect(bars)
    assert not any(o.first_bar == 2 for o in obs_set.observations)


def test_clean_control_no_gap_when_overlapping():
    bars = _bars(10)  # flat baseline everywhere -- no gaps possible
    obs_set = _detect(bars)
    assert obs_set.observations == ()


# --- the mirror-comparison trap (Sec4 / Sec5) ------------------------------


def test_bearish_rule_is_not_a_naive_sign_flip_of_bullish():
    """A common transcription bug writes the bearish case as
    high[i] > low[i+2] (reusing the bullish comparison's operands with the
    inequality flipped) instead of the correct low[i] > high[i+2]. This
    bar triple satisfies the WRONG formula (high[i]=100 > low[i+2]=99,
    trivially true almost everywhere) but must NOT be reported as a
    bearish gap, since low[i]=99 is not > high[i+2]=100.
    """
    bars = _bars(10)  # baseline: high=100, low=99 everywhere
    obs_set = _detect(bars)
    assert not any(o.side == BEARISH for o in obs_set.observations)


# --- C1/C2/C3 ---------------------------------------------------------------


def test_determinism_c2():
    bars = _bars(10, low={4: 101.0})
    a = FairValueGapDetector().detect(bars, _CONFIG)
    b = FairValueGapDetector().detect(bars, _CONFIG)
    assert a == b


def test_no_self_vouching_field_exists_c3():
    bars = _bars(10, low={4: 101.0})
    obs_set = _detect(bars)
    forbidden = {"significance", "edge", "hit_rate", "win_rate", "profitability", "profit"}
    for obs in obs_set.observations:
        assert not (set(obs.__dataclass_fields__) & forbidden)
