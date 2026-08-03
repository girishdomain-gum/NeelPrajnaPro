"""E5: server clock shift between batches is refused, naming both values."""

from qrf.errors import ClockDrift
from qrf.kernel.observation.clock import check_clock_pin, measure_offset
from tests.drills.harness import DrillLog, run_drill


def test_measure_offset_is_a_plain_subtraction():
    assert measure_offset(server_epoch_seconds=1000, wall_clock_utc_epoch_seconds=1000) == 0
    assert measure_offset(server_epoch_seconds=8200, wall_clock_utc_epoch_seconds=1000) == 7200


def test_e5_clock_drift_refused_drill():
    log = DrillLog()
    pinned = 7200.0  # e.g. a GMT+2 server pin from an earlier batch

    def checker(measured: float):
        check_clock_pin(pinned, measured, tolerance_seconds=300)

    result = run_drill(
        name="E5-clock-drift-refused",
        checker=checker,
        clean_input=7205.0,  # 5s of measurement jitter -- within tolerance
        tampered_input=10800.0,  # a full 1-hour DST-sized shift
        expected_exception=ClockDrift,
        log=log,
    )
    assert result.tampered_exception is ClockDrift


def test_e5_drift_exception_names_both_values():
    try:
        check_clock_pin(7200.0, 10800.0, tolerance_seconds=300)
    except ClockDrift as exc:
        assert exc.pinned_offset_seconds == 7200.0
        assert exc.measured_offset_seconds == 10800.0
    else:
        raise AssertionError("expected ClockDrift")
