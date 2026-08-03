"""Order Block detector drills (docs/detectors/order_block.md, origin-candle
method, A-019 R1/R3/R4).
"""

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.trading.concepts.order_block.detector import BEARISH, BULLISH, OrderBlockDetector

_CONFIG = DetectorConfig(source_sha256="0" * 64, span_start_utc=0, span_end_utc=1)


def _bars(n, high=None, low=None, open_=None, close=None, base=100.0):
    """Baseline: a flat, doji-like series (open==close==100, high=100.2,
    low=99.8) so nothing is a swing and nothing breaks unless overridden.
    """
    opens = [base] * n
    closes = [base] * n
    highs = [base + 0.2] * n
    lows = [base - 0.2] * n
    for d, arr in ((high, highs), (low, lows), (open_, opens), (close, closes)):
        if d:
            for idx, val in d.items():
                arr[idx] = val
    return tuple(
        Bar(time=i * 300, open=opens[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n)
    )


def _detect(bars):
    return OrderBlockDetector().detect(bars, _CONFIG)


def test_planted_truth_bullish_order_block():
    # Swing low at bar 10 (confirmed at 13): low[10]=99.0, neighbors baseline 99.8.
    # A bearish (down) candle at bar 12 (the nearest opposite candle before
    # the break), then a break above at bar 20: close[20] > swing high...
    # simpler: use a swing HIGH to break bullish. Swing high at 10
    # (confirmed 13): high[10]=101.0. Bearish origin candle at bar 15
    # (open>close). Break at bar 20: close[20] > 101.0.
    bars = _bars(
        30,
        high={10: 101.0},
        open_={15: 100.5},
        close={15: 100.1, 20: 101.5},
    )
    obs_set = _detect(bars)
    ob = next(o for o in obs_set.observations if o.break_bar == 20)
    assert ob.side == BULLISH
    assert ob.broken_swing_bar == 10
    assert ob.origin_bar == 15
    assert ob.zone_low == bars[15].low
    assert ob.zone_high == bars[15].high


def test_planted_truth_bearish_order_block_mirror():
    bars = _bars(
        30,
        low={10: 99.0},
        open_={15: 100.1},
        close={15: 100.5, 20: 98.5},
    )
    obs_set = _detect(bars)
    ob = next(o for o in obs_set.observations if o.break_bar == 20)
    assert ob.side == BEARISH
    assert ob.broken_swing_bar == 10
    assert ob.origin_bar == 15
    assert ob.zone_low == bars[15].low
    assert ob.zone_high == bars[15].high


# --- clean control / near-miss --------------------------------------------


def test_clean_control_swing_never_broken_no_block():
    bars = _bars(30, high={10: 101.0})  # swing forms but nothing ever breaks it
    obs_set = _detect(bars)
    assert obs_set.observations == ()


def test_clean_control_no_opposite_candle_in_bound_no_block():
    """Every candle from the swing to the break is the SAME color (all
    bullish) -- no origin candle exists inside [s, b-1], so no block, per
    the definition doc's explicit "real, expected outcome" case.
    """
    bars = _bars(
        30,
        high={10: 101.0},
        open_={i: 100.0 for i in range(11, 20)},
        close={**{i: 100.1 for i in range(11, 20)}, 20: 101.5},
    )
    obs_set = _detect(bars)
    assert not any(o.break_bar == 20 for o in obs_set.observations)


# --- the nearest-vs-furthest origin candle trap (Sec6) --------------------


def test_origin_candle_is_nearest_not_furthest():
    # Swing high at 10 (confirmed 13). TWO bearish candles exist before
    # the break: bar 12 (further) and bar 17 (nearer), with bullish
    # candles in between and after. The origin must be 17, not 12.
    bars = _bars(
        30,
        high={10: 101.0},
        open_={12: 100.5, 17: 100.5},
        close={12: 100.1, 17: 100.1, 20: 101.5},
    )
    obs_set = _detect(bars)
    ob = next(o for o in obs_set.observations if o.break_bar == 20)
    assert ob.origin_bar == 17, "must pick the NEAREST opposite candle, not the furthest"


# --- A-019 R1: search bounded by the broken swing, not further -------------


def test_search_bound_ignores_opposite_candle_before_the_swing():
    # A bearish candle exists BEFORE the swing itself (bar 5) -- outside
    # [s=10, b-1=19] -- and every candle from 10 to 19 is bullish. Must
    # find NO origin candle (never reach back past the swing to bar 5).
    bars = _bars(
        30,
        high={10: 101.0},
        open_={5: 100.5, **{i: 100.0 for i in range(11, 20)}},
        close={5: 100.1, **{i: 100.1 for i in range(11, 20)}, 20: 101.5},
    )
    obs_set = _detect(bars)
    assert not any(o.break_bar == 20 for o in obs_set.observations)


# --- C1/C2/C3 ---------------------------------------------------------------


def test_determinism_c2():
    bars = _bars(30, high={10: 101.0}, open_={15: 100.5}, close={15: 100.1, 20: 101.5})
    a = OrderBlockDetector().detect(bars, _CONFIG)
    b = OrderBlockDetector().detect(bars, _CONFIG)
    assert a == b


def test_no_self_vouching_field_exists_c3():
    bars = _bars(30, high={10: 101.0}, open_={15: 100.5}, close={15: 100.1, 20: 101.5})
    obs_set = _detect(bars)
    forbidden = {"significance", "edge", "hit_rate", "win_rate", "profitability", "profit"}
    for obs in obs_set.observations:
        assert not (set(obs.__dataclass_fields__) & forbidden)
