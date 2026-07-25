"""Calendar-day exit rule (ARCH-009 §4, DEVQ-019 successor) — engine + fills.

The exit is the OPEN of the LAST bar sharing the entry bar's UTC calendar day
(epoch-day, the SAME index the SeasonalityDetector uses for its dow markers),
capped at hold_bars. A day truncated by the data tail (the inter-window hole /
fold boundary) is DROPPED, never exited early — so a same-Monday exit is never
fabricated from bars that are not there.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.simulator.fills import _NS_PER_DAY, resolve_exit
from qrf.trading.utility.cost_models import load_cost_model

COST = load_cost_model("xauusd_retail_median")
HR = 3_600_000_000_000  # one hour in ns


def _ts(day, hour):
    return day * _NS_PER_DAY + hour * HR


def _bars(rows):
    """rows: list of (day, hour, open)."""
    ts = [_ts(d, h) for d, h, _o in rows]
    o = np.asarray([r[2] for r in rows], dtype=float)
    return pd.DataFrame({"ts": ts, "open": o, "high": o, "low": o, "close": o})


# --- resolve_exit unit ------------------------------------------------------
def test_calendar_exit_lands_on_last_bar_of_day():
    # day 0: hours 0..5 ; day 1: hours 0..3 (so day 0 is confirmed-ended).
    rows = [(0, h, 100 + h) for h in range(6)] + [(1, h, 200 + h) for h in range(4)]
    ts_sorted = [_ts(d, h) for d, h, _ in rows]
    opens = [r[2] for r in rows]
    # entry at index 1 (day 0 hour 1); last bar of day 0 is index 5.
    fill = resolve_exit(
        entry_index=1, direction=1, entry_price=opens[1], hold_bars=24,
        opens=opens, highs=opens, lows=opens, stop_offset=None, target_offset=None,
        ts_sorted=ts_sorted, exit_rule="calendar_day",
    )
    assert fill is not None
    assert fill.exit_index == 5
    assert fill.reason == "calendar_day"


def test_calendar_exit_dropped_when_day_truncated_at_tail():
    # Only day 2 present and it is the LAST day: its end can't be confirmed -> drop.
    rows = [(2, h, 300 + h) for h in range(3)]
    ts_sorted = [_ts(d, h) for d, h, _ in rows]
    opens = [r[2] for r in rows]
    fill = resolve_exit(
        entry_index=0, direction=1, entry_price=opens[0], hold_bars=24,
        opens=opens, highs=opens, lows=opens, stop_offset=None, target_offset=None,
        ts_sorted=ts_sorted, exit_rule="calendar_day",
    )
    assert fill is None  # truncated day -> dropped, never exited early


def test_calendar_exit_capped_by_hold_bars():
    # A day with 48 half-hour bars (all epoch-day 0) exceeds a hold cap of 24 ->
    # the calendar exit would breach the embargo bound, so the trade is dropped.
    half = HR // 2
    ts_sorted = [0 * _NS_PER_DAY + i * half for i in range(48)] + [_NS_PER_DAY]  # +day1 bar
    opens = [100.0 + i for i in range(len(ts_sorted))]
    # sanity: the first 48 bars are all day 0, bar 48 is day 1.
    assert all(t // _NS_PER_DAY == 0 for t in ts_sorted[:48])
    assert ts_sorted[48] // _NS_PER_DAY == 1
    fill = resolve_exit(
        entry_index=0, direction=1, entry_price=opens[0], hold_bars=24,
        opens=opens, highs=opens, lows=opens, stop_offset=None, target_offset=None,
        ts_sorted=ts_sorted, exit_rule="calendar_day",
    )
    assert fill is None  # day longer than the hold bound -> dropped (no leak)


# --- engine integration -----------------------------------------------------
def test_engine_calendar_exit_trade_and_drop():
    rows = (
        [(0, h, 100 + h) for h in range(6)]
        + [(1, h, 200 + h) for h in range(4)]
        + [(2, h, 300 + h) for h in range(3)]
    )
    bars = _bars(rows)
    # markers at the first bar of each day (day0 h0, day1 h0, day2 h0).
    events = pd.DataFrame(
        {
            "ts": [_ts(0, 0), _ts(1, 0), _ts(2, 0)],
            "direction": [1, 1, 1],
            "strength": [1.0, 1.0, 1.0],
        }
    )
    ex = ExecutionSpec(hold_bars=24, size=1.0, exit_rule="calendar_day")
    trades = EventEngine().simulate(bars, events, COST, seed=1, execution=ex)
    # day 0 and day 1 close within data; day 2 is the tail -> dropped.
    assert len(trades.trades) == 2
    assert trades.n_dropped_tail == 1
    # day 0 entry at h1 (open 101), exit at last bar of day 0 = h5 (open 105).
    t0 = trades.trades[0]
    assert t0.entry_price == 101.0 and t0.exit_price == 105.0
    assert t0.exit_reason == "calendar_day"


def test_calendar_exit_is_additive_default_time_stop_unchanged():
    # Same bars, default exit_rule -> time stop at entry+hold_bars.
    rows = [(0, h, 100 + h) for h in range(10)]
    bars = _bars(rows)
    events = pd.DataFrame({"ts": [_ts(0, 0)], "direction": [1], "strength": [1.0]})
    ex = ExecutionSpec(hold_bars=3, size=1.0)  # default time_stop
    trades = EventEngine().simulate(bars, events, COST, seed=1, execution=ex)
    t = trades.trades[0]
    assert t.exit_reason == "time_stop"
    # entry index 1, exit index 1+3=4 -> open 104.
    assert t.exit_price == 104.0
