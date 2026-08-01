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
