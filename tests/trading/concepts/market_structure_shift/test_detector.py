"""Market Structure Shift detector drills
(docs/detectors/market_structure_shift.md, A-019 R2/R3/R4).
"""

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.trading.concepts.market_structure_shift.detector import (
    BEARISH,
    BULLISH,
    MarketStructureShiftDetector,
)

_CONFIG = DetectorConfig(source_sha256="0" * 64, span_start_utc=0, span_end_utc=1)


def _bars(n, high=None, low=None, close=None, base=100.0):
    highs = [base + 0.2] * n
    lows = [base - 0.2] * n
    closes = [base] * n
    for d, arr in ((high, highs), (low, lows), (close, closes)):
        if d:
            for idx, val in d.items():
                arr[idx] = val
    return tuple(
        Bar(time=i * 300, open=closes[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n)
    )


def _detect(bars):
    return MarketStructureShiftDetector().detect(bars, _CONFIG)


def test_planted_truth_bullish_structure_then_bearish_shift():
    # Ascending swing highs at 10 (101), 30 (102), both above the 100.2
    # baseline; ascending swing lows at 20 (99.0), 40 (99.4), both below
    # the 99.8 baseline -> prevailing becomes BULLISH once both pairs are
    # confirmed (bar 43). A close below the last swing low (99.4) at bar
    # 50 must fire a BEARISH shift.
    bars = _bars(
        60,
        high={10: 101.0, 30: 102.0},
        low={20: 99.0, 40: 99.4},
        close={50: 99.0},
    )
    obs_set = _detect(bars)
    shift = next(o for o in obs_set.observations if o.shift_bar == 50)
    assert shift.shift_direction == BEARISH
    assert shift.prevailing_before == BULLISH
    assert shift.broken_swing_bar == 40
    assert shift.broken_swing_price == 99.4


def test_planted_truth_bearish_structure_then_bullish_shift_mirror():
    bars = _bars(
        60,
        low={10: 99.0, 30: 98.0},
        high={20: 101.0, 40: 100.5},
        close={50: 101.0},
    )
    obs_set = _detect(bars)
    shift = next(o for o in obs_set.observations if o.shift_bar == 50)
    assert shift.shift_direction == BULLISH
    assert shift.prevailing_before == BEARISH
    assert shift.broken_swing_bar == 40
    assert shift.broken_swing_price == 100.5


# --- clean control: choppy/UNDEFINED structure never shifts ----------------


def test_clean_control_choppy_structure_never_shifts():
    # Highs ascending (10->101, 30->102) but lows DESCENDING (20->99,
    # 40->98) -- disagreement means UNDEFINED, never BULLISH/BEARISH, so
    # no shift can ever fire even though later closes cross these levels.
    bars = _bars(
        60,
        high={10: 101.0, 30: 102.0},
        low={20: 99.0, 40: 98.0},
        close={50: 90.0, 55: 110.0},  # extreme closes, still no shift possible
    )
    obs_set = _detect(bars)
    assert obs_set.observations == ()


# --- A-019 R2 (mandatory drill): two breaks from incoherent structure -----


def test_r2_two_breaks_in_a_row_from_incoherent_structure_yield_one_event():
    # Establish BULLISH (as in the planted-truth case), shift once at bar
    # 50, then IMMEDIATELY another close below the same broken level at
    # bar 51 -- prevailing is now UNDEFINED (reset), so this second break
    # must NOT fire a second event.
    bars = _bars(
        60,
        high={10: 101.0, 30: 102.0},
        low={20: 99.0, 40: 99.4},
        close={50: 99.0, 51: 98.5},
    )
    obs_set = _detect(bars)
    assert len(obs_set.observations) == 1
    assert obs_set.observations[0].shift_bar == 50


# --- C1/C2/C3 ---------------------------------------------------------------


def test_determinism_c2():
    bars = _bars(
        60, high={10: 101.0, 30: 102.0}, low={20: 99.0, 40: 100.0}, close={50: 99.5}
    )
    a = MarketStructureShiftDetector().detect(bars, _CONFIG)
    b = MarketStructureShiftDetector().detect(bars, _CONFIG)
    assert a == b


def test_no_self_vouching_field_exists_c3():
    bars = _bars(
        60, high={10: 101.0, 30: 102.0}, low={20: 99.0, 40: 100.0}, close={50: 99.5}
    )
    obs_set = _detect(bars)
    forbidden = {"significance", "edge", "hit_rate", "win_rate", "profitability", "profit"}
    for obs in obs_set.observations:
        assert not (set(obs.__dataclass_fields__) & forbidden)
