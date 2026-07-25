"""Trading-side FVG scans — descriptive weekend flag + follow-through (ARCH-007 §2).

The scans compute a DESCRIPTIVE summary; these tests pin the weekend-spanning
detection, the follow-through arithmetic, and determinism-per-seed.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd
import pytest

from qrf.trading.observatory.scans import (
    _spans_weekend,
    follow_through,
    net_drift_scan,
    weekend_partition_scan,
)

HOUR_NS = 3600 * 10**9


def _ts(y, m, d, h) -> int:
    return int(datetime(y, m, d, h, tzinfo=UTC).timestamp()) * 10**9


def _bars(ts_list, closes) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "ts": ts_list,
            "open": closes,
            "high": [c + 1 for c in closes],
            "low": [c - 1 for c in closes],
            "close": closes,
        }
    )


def _events(rows) -> pd.DataFrame:
    return pd.DataFrame(
        rows, columns=["ts", "event_type", "direction", "zone_hi", "zone_lo"]
    )


# --- weekend-spanning detection ---------------------------------------------
def test_spans_weekend_friday_to_sunday_true():
    # 2024-01-05 is a Friday; 2024-01-07 is a Sunday.
    fri = _ts(2024, 1, 5, 21)
    sun = _ts(2024, 1, 7, 22)
    assert _spans_weekend(fri, sun, 3600) is True


def test_contiguous_hours_do_not_span():
    a = _ts(2024, 1, 3, 10)
    b = _ts(2024, 1, 3, 11)
    assert _spans_weekend(a, b, 3600) is False


def test_midweek_holiday_gap_not_weekend():
    # Wed 09:00 -> Thu 12:00 (a 27h gap) crosses no Sat/Sun.
    a = _ts(2024, 1, 3, 9)
    b = _ts(2024, 1, 4, 12)
    assert _spans_weekend(a, b, 3600) is False


# --- follow-through arithmetic ----------------------------------------------
def test_follow_through_direction_and_horizon():
    ts_list = [_ts(2024, 1, 3, h) for h in range(10)]  # contiguous Wednesday hours
    closes = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109]
    bars = _bars(ts_list, closes)
    # bull FVG knowable at k=4 (needs k-2..k); horizon 4 -> close[8]-close[4] = 4.
    ev = _events([[ts_list[4], "smc.fvg.bull", 1, 104.5, 103.5]])
    out = follow_through(bars, ev, horizon=4)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["follow_through"] == pytest.approx(108 - 104)
    assert bool(row["weekend_spanning"]) is False


def test_bear_direction_flips_sign():
    ts_list = [_ts(2024, 1, 3, h) for h in range(10)]
    closes = [100, 99, 98, 97, 96, 95, 94, 93, 92, 91]  # falling
    bars = _bars(ts_list, closes)
    ev = _events([[ts_list[4], "smc.fvg.bear", -1, 96.5, 95.5]])
    out = follow_through(bars, ev, horizon=4)
    # bear, price fell: direction(-1) * (close[8]-close[4]) = -1 * (92-96) = 4.
    assert out.iloc[0]["follow_through"] == pytest.approx(4.0)


def test_events_without_future_room_are_dropped():
    ts_list = [_ts(2024, 1, 3, h) for h in range(6)]
    bars = _bars(ts_list, [100, 101, 102, 103, 104, 105])
    ev = _events([[ts_list[5], "smc.fvg.bull", 1, 105.5, 104.5]])  # no 4 bars ahead
    assert len(follow_through(bars, ev, horizon=4)) == 0


# --- scan summaries + determinism -------------------------------------------
def _weekend_dataset():
    # Wed..Fri contiguous, weekend hole, then Mon..Tue — so an event whose forming
    # bars straddle Fri->Mon is weekend-spanning and one purely mid-week is not.
    ts_list = (
        [_ts(2024, 1, 3, h) for h in range(20, 24)]     # Wed 20-23
        + [_ts(2024, 1, 4, h) for h in range(0, 4)]     # Thu 0-3
        + [_ts(2024, 1, 5, h) for h in (21, 22, 23)]    # Fri 21-23 (pre-close)
        + [_ts(2024, 1, 8, h) for h in range(0, 8)]     # Mon 0-7 (after weekend)
    )
    closes = [100 + i for i in range(len(ts_list))]
    return _bars(ts_list, closes), ts_list


def test_weekend_partition_scan_partitions_and_is_deterministic():
    bars, ts_list = _weekend_dataset()
    # intra-week event fully inside Wed/Thu; weekend event whose k-2..k cross Fri->Mon.
    fri_last = ts_list[10]  # Fri 23
    mon_first = ts_list[11]  # Mon 0 (k here -> forming bars Fri22,Fri23,Mon0)
    ev = _events(
        [
            [ts_list[3], "smc.fvg.bull", 1, 103.5, 102.5],   # Wed 23 knowability — intra-week
            [mon_first, "smc.fvg.bull", 1, 111.5, 110.5],    # Mon 0 — weekend-spanning
        ]
    )
    f1, ann = weekend_partition_scan(bars, ev, seed=123)
    f2, _ = weekend_partition_scan(bars, ev, seed=123)
    assert f1 == f2  # deterministic per seed
    assert f1["partitions"]["weekend_spanning"]["n"] == 1
    assert f1["partitions"]["intra_week"]["n"] == 1
    assert bool(ann[ann["ts"] == mon_first]["weekend_spanning"].iloc[0]) is True
    assert fri_last  # (referenced for clarity)


def test_net_drift_scan_buckets_by_quarter_deterministic():
    ts_list = [_ts(2024, 1, 3, h) for h in range(10)]
    bars = _bars(ts_list, [100 + i for i in range(10)])
    ev = _events([[ts_list[4], "smc.fvg.bull", 1, 104.5, 103.5]])
    f1, _ = net_drift_scan(bars, ev, seed=9)
    f2, _ = net_drift_scan(bars, ev, seed=9)
    assert f1 == f2
    assert "2024Q1" in f1["buckets_by_quarter"]
