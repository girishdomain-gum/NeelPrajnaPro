"""DST-safe local-to-UTC conversion for pinned-zone ingest pipelines.

WO-03 (S3, refs A-007 ruling (a)): every R6 timestamp is stored UTC; local
time never enters the ledger. Conversion from a broker's local wall-clock
timestamps goes through an explicit IANA zone, pinned per dataset in its
``dataset_scope`` registration record (``qrf.kernel.protocol.scope_registry``)
and DETERMINED FROM EVIDENCE — never assumed. Ambiguous (DST fall-back,
a local stamp that occurred twice) and nonexistent (DST spring-forward, a
local stamp that never occurred) wall-clock timestamps are refused loudly;
there is no silent fold resolution, ever.

This module is kernel: stdlib-only (``zoneinfo``) + the error taxonomy.
"""

from __future__ import annotations

import datetime as _dt
from zoneinfo import ZoneInfo

from qrf.kernel.errors import SchemaViolation

_EPOCH_UTC = _dt.datetime(1970, 1, 1, tzinfo=_dt.UTC)


class AmbiguousLocalTimeError(SchemaViolation):
    """A local wall-clock timestamp occurs twice (DST fall-back overlap)."""


class NonexistentLocalTimeError(SchemaViolation):
    """A local wall-clock timestamp never occurred (DST spring-forward gap)."""


def local_to_utc_ns(naive_dt: _dt.datetime, zone_name: str) -> int:
    """Convert a naive local wall-clock ``naive_dt`` in IANA zone ``zone_name``
    to nanoseconds since the Unix epoch, UTC.

    Refuses loudly — :class:`AmbiguousLocalTimeError` or
    :class:`NonexistentLocalTimeError` — rather than silently picking a fold,
    if ``naive_dt`` falls in a DST fall-back overlap or spring-forward gap.
    """
    if naive_dt.tzinfo is not None:
        raise SchemaViolation("local_to_utc_ns requires a naive (tz-less) datetime")

    zone = ZoneInfo(zone_name)
    dt_fold0 = naive_dt.replace(tzinfo=zone, fold=0)
    dt_fold1 = naive_dt.replace(tzinfo=zone, fold=1)
    off0 = dt_fold0.utcoffset()
    off1 = dt_fold1.utcoffset()

    if off0 == off1:
        return _to_ns(dt_fold0.astimezone(_dt.UTC))

    # off0 != off1: naive_dt sits in EITHER a fall-back overlap (occurs twice,
    # both real) OR a spring-forward gap (occurs never, fictitious). Roundtrip
    # fold0's UTC instant back through the zone: for a real ambiguous time this
    # reproduces naive_dt exactly (it really is a valid local wall-clock
    # instant); for a nonexistent time it lands on a DIFFERENT wall-clock
    # (shifted by the gap), because naive_dt itself was never a real instant.
    utc0 = dt_fold0.astimezone(_dt.UTC)
    roundtrip = utc0.astimezone(zone).replace(tzinfo=None)
    if roundtrip == naive_dt:
        raise AmbiguousLocalTimeError(
            f"{naive_dt.isoformat()} is ambiguous in {zone_name} "
            "(DST fall-back overlap) — refusing rather than silently picking a fold"
        )
    raise NonexistentLocalTimeError(
        f"{naive_dt.isoformat()} does not exist in {zone_name} "
        "(DST spring-forward gap) — refusing rather than silently shifting it"
    )


def _to_ns(utc_dt: _dt.datetime) -> int:
    delta = utc_dt - _EPOCH_UTC
    return (delta.days * 86_400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1_000


def find_time_of_day_at_gaps(
    sorted_local_times: list[_dt.datetime], gap_threshold: _dt.timedelta = _dt.timedelta(hours=1)
) -> list[tuple[_dt.time, _dt.time]]:
    """For a sorted sequence of (naive, local/broker-labelled) timestamps,
    return the (close_time_of_day, reopen_time_of_day) pair at every gap
    exceeding ``gap_threshold`` -- e.g. a daily maintenance break or a
    weekend closure. Pure inspection; raises nothing, decides nothing."""
    pairs: list[tuple[_dt.time, _dt.time]] = []
    for i in range(1, len(sorted_local_times)):
        if sorted_local_times[i] - sorted_local_times[i - 1] > gap_threshold:
            pairs.append((sorted_local_times[i - 1].time(), sorted_local_times[i].time()))
    return pairs


def check_maintenance_boundary_invariant(
    sorted_local_times: list[_dt.datetime],
    expected_close: _dt.time,
    expected_reopen: _dt.time,
    tolerance: _dt.timedelta = _dt.timedelta(minutes=10),
) -> tuple[bool, str]:
    """WO-10's pin self-policing invariant (A-051): a broker's daily
    maintenance-break close/reopen clock-time is a cheap, always-present
    signature of its server's CURRENT UTC offset. If that offset ever
    shifts (e.g. the broker changes its DST policy mid-collection), the
    close/reopen times observed in LOCAL (broker-labelled) terms will
    visibly drift -- this refuses loudly instead of a pin, once
    evidenced, being trusted forever without re-checking (the exact
    assumption this project keeps catching elsewhere).

    Every gap-boundary pair found via :func:`find_time_of_day_at_gaps`
    must sit within ``tolerance`` of BOTH ``expected_close`` and
    ``expected_reopen``. Returns (ok, detail); raises nothing -- the
    caller (e.g. an ingest pipeline) decides whether a violation is
    fatal for its batch.

    A batch with no gaps at all (nothing to check) is reported OK with a
    detail saying so, not silently treated as a pass with no evidence."""
    pairs = find_time_of_day_at_gaps(sorted_local_times)
    if not pairs:
        return True, "no maintenance-boundary gap observed in this batch -- nothing to check"

    def _time_delta(a: _dt.time, b: _dt.time) -> _dt.timedelta:
        da = _dt.datetime.combine(_dt.date.min, a)
        db = _dt.datetime.combine(_dt.date.min, b)
        diff = abs(da - db)
        # a boundary just either side of midnight is still "close" in
        # time-of-day terms -- take the shorter way around the 24h clock
        return min(diff, _dt.timedelta(days=1) - diff)

    violations = [
        (close_t, reopen_t)
        for close_t, reopen_t in pairs
        if _time_delta(close_t, expected_close) > tolerance
        or _time_delta(reopen_t, expected_reopen) > tolerance
    ]
    if violations:
        readable = [(c.isoformat(), r.isoformat()) for c, r in violations]
        return False, (
            f"maintenance-boundary invariant VIOLATED: {readable} do not match "
            f"expected close={expected_close.isoformat()} reopen={expected_reopen.isoformat()} "
            f"within {tolerance} -- server clock offset may have shifted"
        )
    return True, (
        f"{len(pairs)} boundary gap(s), all within {tolerance} of "
        f"expected close={expected_close} reopen={expected_reopen}"
    )
