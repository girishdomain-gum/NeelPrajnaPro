"""E5: server clock shift between batches is refused, naming both values.

Also: A-009/F-04 -- the probe is noisy BY CONSTRUCTION, proven directly
from S03's own three real measurements, so stability is never mistaken
for exactness (see clock.py's module docstring for the full constraint).
"""

from qrf.errors import ClockDrift
from qrf.kernel.observation.clock import check_clock_pin, measure_drift_probe
from tests.drills.harness import DrillLog, run_drill

# The three REAL measurements from S03's actual runs against the live
# Vantage terminal (see data/provenance/*.provenance.json and the sprint
# report) -- not synthetic. A real server-side UTC offset does not wobble
# by ~49s; this spread is exactly the round-trip latency this probe was
# always documented to carry.
REAL_S03_MEASUREMENTS_SECONDS = [7284.975182533264, 7252.936553001404, 7236.056415081024]


def test_measure_drift_probe_is_a_plain_subtraction():
    assert measure_drift_probe(server_epoch_seconds=1000, wall_clock_utc_epoch_seconds=1000) == 0
    assert (
        measure_drift_probe(server_epoch_seconds=8200, wall_clock_utc_epoch_seconds=1000) == 7200
    )


def test_probe_is_noisy_by_construction():
    """The real measurements disagree with each other by tens of seconds.
    That spread is the proof: this value is a latency-inflated probe, not
    a stable constant, and nobody should ever be tempted to treat it as
    one just because it happened to look stable in some other run.
    """
    spread = max(REAL_S03_MEASUREMENTS_SECONDS) - min(REAL_S03_MEASUREMENTS_SECONDS)
    assert spread > 0, "the probe must never be mistaken for an exact, stable constant"
    # a real DST shift is 3600s; this spread must stay a small fraction of
    # that, or E5's tolerance stops making sense
    assert spread < 60, "unexpectedly large spread -- re-check the tolerance reasoning in clock.py"


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
