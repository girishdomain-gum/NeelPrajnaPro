"""Server-clock drift probing and self-policing (A-007 §3.5).

A broker's server clock is not UTC and its offset can shift (DST). This
module never asserts a clock offset it cannot measure: `measure_drift_probe`
takes the two raw numbers (a server-time epoch and a wall-clock UTC epoch,
both supplied by the caller so this stays terminal-independent and
testable) and returns their difference, honestly, with no correction
applied.

WHAT THIS VALUE IS NOT (A-005/A-009 F-04): the result is `true_server_
offset + round_trip_latency` (the launch-run-close cycle's own duration),
never the server's real UTC offset alone -- three real S03 runs measured
7284.98s, 7252.94s and 7236.06s, a ~49s spread no real timezone produces.
It is a NOISY, LATENCY-INFLATED UPPER BOUND, valid only for detecting
DRIFT between batches (a real DST shift is 3600s and swamps ~90s of
noise). IT MUST NEVER BE USED TO CONVERT A TIMESTAMP -- converting server
bar times with this value would silently misassign any event within its
own noise band of a bar boundary. A true absolute offset would need a
time reference outside MT5 entirely, which A-007 §3.5 already forbids
inventing; nothing in this project attempts one.

`check_clock_pin` is the self-policing half: it compares a newly measured
probe against the PINNED one from an earlier batch and refuses, naming
both values, if they disagree beyond `tolerance_seconds` -- wide enough to
absorb the measurement noise described above, never so wide that a real
DST shift could slip through.
"""

from __future__ import annotations

from qrf.errors import ClockDrift

DEFAULT_TOLERANCE_SECONDS = 300  # 5 minutes: generous for measurement noise,
# a full order of magnitude below a real DST shift (3600s), so a genuine
# shift is never mistaken for jitter.


def measure_drift_probe(server_epoch_seconds: float, wall_clock_utc_epoch_seconds: float) -> float:
    """Return server_time - wall_clock_utc, in seconds -- a noisy,
    latency-inflated PROBE for batch-to-batch drift detection, never the
    server's true UTC offset (see the module docstring). Positive means
    the server clock read ahead of the wall clock at measurement time.
    Only as precise as the two epochs given to it, and always carries
    whatever round-trip latency existed between reading them.
    """
    return server_epoch_seconds - wall_clock_utc_epoch_seconds


def check_clock_pin(
    pinned_probe_seconds: float,
    measured_probe_seconds: float,
    tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS,
) -> None:
    """Refuse, naming both values, if `measured_probe_seconds` disagrees
    with `pinned_probe_seconds` by more than `tolerance_seconds`. Mixing
    two time bases in one dataset silently destroys every timing-based
    measurement later, so this is a hard refusal, never a warning.
    """
    if abs(measured_probe_seconds - pinned_probe_seconds) > tolerance_seconds:
        raise ClockDrift(pinned_probe_seconds, measured_probe_seconds)
