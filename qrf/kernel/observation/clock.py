"""Server-clock pinning and self-policing (A-007 §3.5).

A broker's server clock is not UTC and its offset can shift (DST). This
module never asserts a clock offset it cannot measure: `measure_offset`
takes the two raw numbers (a server-time epoch and a wall-clock UTC
epoch, both supplied by the caller so this stays terminal-independent and
testable) and returns their difference, honestly, with no correction
applied. `check_clock_pin` is the self-policing half: it compares a newly
measured offset against the PINNED one from an earlier batch and refuses,
naming both values, if they disagree beyond `tolerance_seconds` -- wide
enough to absorb measurement noise (network latency, tick timing), never
so wide that a real DST shift (typically +-3600s) could slip through.
"""

from __future__ import annotations

from qrf.errors import ClockDrift

DEFAULT_TOLERANCE_SECONDS = 300  # 5 minutes: generous for measurement noise,
# a full order of magnitude below a real DST shift (3600s), so a genuine
# shift is never mistaken for jitter.


def measure_offset(server_epoch_seconds: float, wall_clock_utc_epoch_seconds: float) -> float:
    """Return server_time - wall_clock_utc, in seconds. Positive means the
    server clock reads ahead of UTC. This is a measurement, not a claim
    about the server's timezone: it is only as precise as the two epochs
    given to it, and carries whatever network/IPC latency existed between
    reading them.
    """
    return server_epoch_seconds - wall_clock_utc_epoch_seconds


def check_clock_pin(
    pinned_offset_seconds: float,
    measured_offset_seconds: float,
    tolerance_seconds: float = DEFAULT_TOLERANCE_SECONDS,
) -> None:
    """Refuse, naming both values, if `measured_offset_seconds` disagrees
    with `pinned_offset_seconds` by more than `tolerance_seconds`. Mixing
    two time bases in one dataset silently destroys every timing-based
    measurement later, so this is a hard refusal, never a warning.
    """
    if abs(measured_offset_seconds - pinned_offset_seconds) > tolerance_seconds:
        raise ClockDrift(pinned_offset_seconds, measured_offset_seconds)
