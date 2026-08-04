"""AM-07 Stage A P2 gate (A-042): the window-membership check, drilled
RED first. Entirely synthetic bars -- this module has no opinion about
market data, only about time arithmetic.
"""

import pytest

from qrf.errors import WindowConflict
from qrf.kernel.detection.types import Bar
from qrf.kernel.windows.membership import BAR_SECONDS, assert_bars_within_window
from tests.drills.harness import DrillLog, run_drill


def _bar(time: int) -> Bar:
    return Bar(time=time, open=1.0, high=1.0, low=1.0, close=1.0)


def test_control_all_bars_inside_window_passes():
    bars = [_bar(0), _bar(300), _bar(600), _bar(900)]
    assert_bars_within_window(bars, start=0, end=1200)  # must not raise


def test_empty_bar_sequence_is_vacuously_inside():
    assert_bars_within_window([], start=0, end=300)  # must not raise


# --- the two cases A-042 named as the ones that actually matter ----------


def test_bar_opening_exactly_at_start_passes():
    """`start` IS a valid open-time inside the window -- the first bar."""
    bars = [_bar(1000)]
    assert_bars_within_window(bars, start=1000, end=1300)  # must not raise


def test_bar_opening_exactly_at_end_fails_drill():
    """The off-by-one this whole module exists to name: a bar opening
    AT `end` belongs to the NEXT window, not this one, and must FAIL.
    """
    log = DrillLog()

    def checker(bar_time: int):
        assert_bars_within_window([_bar(bar_time)], start=1000, end=1300)

    result = run_drill(
        name="P2-window-membership-end-edge",
        checker=checker,
        clean_input=1000,  # last valid open-time for [1000,1300): 1000+300=1300<=1300
        tampered_input=1300,  # exactly at end -- must be refused
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict


def test_bar_opening_one_bar_length_before_end_is_the_last_valid_one():
    """A bar's own COVERAGE must fit inside the window too, not just its
    open time -- the last valid open-time is `end - BAR_SECONDS`, whose
    coverage `[end - BAR_SECONDS, end)` exactly reaches `end`.
    """
    end = 1300
    bars = [_bar(end - BAR_SECONDS)]
    assert_bars_within_window(bars, start=1000, end=end)  # must not raise


def test_bar_opening_before_start_fails_drill():
    log = DrillLog()

    def checker(bar_time: int):
        assert_bars_within_window([_bar(bar_time)], start=1000, end=1300)

    result = run_drill(
        name="P2-window-membership-start-edge",
        checker=checker,
        clean_input=1000,
        tampered_input=999,
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict


def test_failure_names_the_bar_index_and_time():
    bars = [_bar(1000), _bar(1300), _bar(1600)]  # third bar covers [1600,1900), past end=1900? no
    with pytest.raises(WindowConflict) as exc_info:
        assert_bars_within_window(bars, start=1000, end=1600)  # third bar (index 2) violates
    assert "bar 2" in str(exc_info.value)
    assert "1600" in str(exc_info.value)


def test_invalid_span_itself_is_refused():
    with pytest.raises(WindowConflict):
        assert_bars_within_window([_bar(0)], start=500, end=500)


# --- real-scale gate: dataset (1) against its own reserved span ----------


def test_p2_gate_real_dataset_inside_its_reserved_span():
    from pathlib import Path

    from qrf.kernel.observation.bars import load_bars_csv

    real_csv = Path(r"F:\NeelPrajnaProData\datastore\s07_bulk\xauusd_m5_s07_fresh_window.csv")
    if not real_csv.exists():
        pytest.skip("real Stage A dataset not present")
    bars = load_bars_csv(real_csv)
    # the exact reserved span from A-038 Ruling 2 / D-039 / A-040
    assert_bars_within_window(bars, start=1_767_766_200, end=1_776_722_700)  # must not raise
