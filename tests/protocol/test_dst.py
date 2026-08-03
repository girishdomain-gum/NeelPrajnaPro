"""WO-03 AT-2 (S3, refs A-007 ruling (a)): the DST conversion rule exercised
across a real DST transition — correct conversion proven on unambiguous
stamps either side of the boundary, loud refusal proven on the ambiguous
(fall-back) and nonexistent (spring-forward) stamps inside it.

Europe/Berlin is used as the exercising zone (real IANA tzdata, standard EU
rule: last Sunday of March / October) — a fixture choice to prove the
MECHANISM works against a real, known transition; it is NOT a claim about
which zone R6's own dataset_scope will pin (that is decided from real Vantage
tick evidence, per A-007, once the Owner's first export lands).
"""

from __future__ import annotations

import datetime as dt

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.dst import (
    AmbiguousLocalTimeError,
    NonexistentLocalTimeError,
    check_maintenance_boundary_invariant,
    find_time_of_day_at_gaps,
    local_to_utc_ns,
)

ZONE = "Europe/Berlin"

# 2026 EU DST transitions (last Sunday of March / October): spring-forward
# 2026-03-29 02:00 CET (+01:00) -> 03:00 CEST (+02:00); fall-back
# 2026-10-25 03:00 CEST (+02:00) -> 02:00 CET (+01:00).


def _ns(y, mo, d, h, mi, s=0):
    epoch = dt.datetime(1970, 1, 1, tzinfo=dt.UTC)
    delta = dt.datetime(y, mo, d, h, mi, s, tzinfo=dt.UTC) - epoch
    return (delta.days * 86_400 + delta.seconds) * 1_000_000_000


# --- correct conversion on unambiguous stamps ---------------------------------
def test_converts_ordinary_time_correctly():
    # 2026-06-15 12:00 CEST (+02:00, well inside summer, no transition nearby)
    result = local_to_utc_ns(dt.datetime(2026, 6, 15, 12, 0), ZONE)
    assert result == _ns(2026, 6, 15, 10, 0)  # 12:00 - 2h = 10:00 UTC


def test_converts_correctly_just_before_spring_forward():
    # 2026-03-29 01:59 CET (+01:00), one minute before the gap
    result = local_to_utc_ns(dt.datetime(2026, 3, 29, 1, 59), ZONE)
    assert result == _ns(2026, 3, 29, 0, 59)  # 01:59 - 1h = 00:59 UTC


def test_converts_correctly_just_after_spring_forward():
    # 2026-03-29 03:01 CEST (+02:00), one minute after the gap
    result = local_to_utc_ns(dt.datetime(2026, 3, 29, 3, 1), ZONE)
    assert result == _ns(2026, 3, 29, 1, 1)  # 03:01 - 2h = 01:01 UTC


def test_converts_correctly_just_before_fall_back():
    # 2026-10-25 02:59, but BEFORE the repeat starts: 2026-10-25 01:59 CEST
    # (+02:00), a full hour before the ambiguous window even opens.
    result = local_to_utc_ns(dt.datetime(2026, 10, 25, 1, 59), ZONE)
    assert result == _ns(2026, 10, 24, 23, 59)  # 01:59 - 2h = 23:59 UTC (Oct 24)


def test_converts_correctly_just_after_fall_back():
    # 2026-10-25 03:01 CET (+01:00), one minute after the repeated hour ends.
    result = local_to_utc_ns(dt.datetime(2026, 10, 25, 3, 1), ZONE)
    assert result == _ns(2026, 10, 25, 2, 1)  # 03:01 - 1h = 02:01 UTC


# --- loud refusal on the spring-forward gap (nonexistent local stamps) -------
def test_refuses_nonexistent_time_in_spring_forward_gap():
    # 2026-03-29 02:30 never happened — clocks jumped 02:00 -> 03:00.
    with pytest.raises(NonexistentLocalTimeError):
        local_to_utc_ns(dt.datetime(2026, 3, 29, 2, 30), ZONE)


def test_refuses_nonexistent_time_at_gap_start():
    with pytest.raises(NonexistentLocalTimeError):
        local_to_utc_ns(dt.datetime(2026, 3, 29, 2, 0), ZONE)


# --- loud refusal on the fall-back overlap (ambiguous local stamps) ----------
def test_refuses_ambiguous_time_in_fall_back_overlap():
    # 2026-10-25 02:30 happened twice — once at +02:00, once at +01:00.
    with pytest.raises(AmbiguousLocalTimeError):
        local_to_utc_ns(dt.datetime(2026, 10, 25, 2, 30), ZONE)


def test_refuses_ambiguous_time_at_overlap_start():
    with pytest.raises(AmbiguousLocalTimeError):
        local_to_utc_ns(dt.datetime(2026, 10, 25, 2, 0), ZONE)


# --- guard: requires a naive datetime -----------------------------------------
def test_refuses_aware_datetime_input():
    aware = dt.datetime(2026, 6, 15, 12, 0, tzinfo=dt.UTC)
    with pytest.raises(SchemaViolation):
        local_to_utc_ns(aware, ZONE)


# --- A-051's pin self-policing invariant --------------------------------------
# Real evidence from WO-10's actual export: Vantage's XAUUSD M5 feed shows a
# daily maintenance close at 23:55 and reopen at 01:00, server-labelled time,
# unchanged across both the 2025-10-26/2025-11-02 and 2026-03-08/2026-03-29
# transitions. These fixtures use that real close/reopen pair.
CLOSE = dt.time(23, 55)
REOPEN = dt.time(1, 0)


def _times(*hm_pairs):
    """hm_pairs like [(day, hour, minute), ...] -> naive datetimes, 2026-01-(day)."""
    return [dt.datetime(2026, 1, day, h, m) for day, h, m in hm_pairs]


def _trading_day(day, close=CLOSE, reopen=REOPEN, step_minutes=30):
    """One day's worth of densely-spaced intraday points from `reopen` to
    `close` (so no >1h gap appears WITHIN the day, only at the real
    close/reopen boundary), for a fixture day starting 2026-01-(day)."""
    start = dt.datetime.combine(dt.date(2026, 1, day), reopen)
    end = dt.datetime.combine(dt.date(2026, 1, day), close)
    points = []
    t = start
    while t <= end:
        points.append(t)
        t += dt.timedelta(minutes=step_minutes)
    if points[-1] != end:
        points.append(end)
    return points


def test_find_time_of_day_at_gaps_returns_pair_per_gap():
    # two full trading days back-to-back -- only the close/reopen boundary
    # between them should register as a gap, nothing intraday
    times = _trading_day(1) + _trading_day(2)
    pairs = find_time_of_day_at_gaps(times, gap_threshold=dt.timedelta(hours=1))
    assert pairs == [(CLOSE, REOPEN)]


def test_find_time_of_day_at_gaps_ignores_small_gaps():
    # 5-minute bar spacing -- not a gap at all under a 1h threshold
    times = _times((1, 12, 0), (1, 12, 5), (1, 12, 10))
    assert find_time_of_day_at_gaps(times, gap_threshold=dt.timedelta(hours=1)) == []


def test_maintenance_boundary_invariant_holds_on_matching_data():
    times = _trading_day(1) + _trading_day(2) + _trading_day(3)
    ok, detail = check_maintenance_boundary_invariant(times, CLOSE, REOPEN)
    assert ok is True
    assert "2 boundary gap" in detail


def test_maintenance_boundary_invariant_reports_ok_with_no_gaps_present():
    """A batch with nothing to check must say so explicitly, not silently
    pass as though it had verified something."""
    times = _times((1, 12, 0), (1, 12, 5))
    ok, detail = check_maintenance_boundary_invariant(times, CLOSE, REOPEN)
    assert ok is True
    assert "nothing to check" in detail


def test_maintenance_boundary_invariant_refuses_a_one_hour_shift():
    """This is the drill: a server clock that shifted by exactly one hour
    (the DST-policy-change scenario A-051 is guarding against) must be
    caught, not silently absorbed."""
    # 1h earlier than the pinned close=23:55 / reopen=01:00
    times = [dt.datetime(2026, 1, 1, 22, 55), dt.datetime(2026, 1, 2, 0, 0)]
    ok, detail = check_maintenance_boundary_invariant(times, CLOSE, REOPEN)
    assert ok is False
    assert "VIOLATED" in detail
    assert "22:55" in detail


def test_maintenance_boundary_invariant_tolerates_small_jitter():
    # 3 minutes off the pinned close/reopen -- inside the default 10-min tolerance
    times = [
        dt.datetime(2026, 1, 1, 23, 58), dt.datetime(2026, 1, 2, 1, 3),
    ]
    ok, _ = check_maintenance_boundary_invariant(times, CLOSE, REOPEN)
    assert ok is True


def test_maintenance_boundary_invariant_respects_custom_tolerance():
    times = [
        dt.datetime(2026, 1, 1, 23, 58), dt.datetime(2026, 1, 2, 1, 3),
    ]
    ok, _ = check_maintenance_boundary_invariant(
        times, CLOSE, REOPEN, tolerance=dt.timedelta(minutes=1)
    )
    assert ok is False


def test_maintenance_boundary_invariant_handles_midnight_wraparound():
    """A boundary just either side of midnight must be measured the SHORT
    way around the 24h clock, not naively subtracted (23:59 vs 00:01 is a
    2-minute difference, not 23h58m)."""
    close_near_midnight = dt.time(23, 59)
    reopen_near_midnight = dt.time(0, 1)
    times = [
        dt.datetime(2026, 1, 1, 23, 59), dt.datetime(2026, 1, 2, 0, 1),
    ]
    ok, _ = check_maintenance_boundary_invariant(
        times, close_near_midnight, reopen_near_midnight, tolerance=dt.timedelta(minutes=5)
    )
    assert ok is True
