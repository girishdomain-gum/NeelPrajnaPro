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
