"""Instrument base contracts — Detector protocol, CalibrationCase, EventFrame.

Implementation Blueprint v1.0 §4.3. This module is kernel: it is domain-blind.
The EventFrame column spec speaks only in the §4.3 names — ``ts``, ``event_type``,
``direction``, ``level``, ``zone_hi``, ``zone_lo``, ``strength``, ``meta`` — and
carries no trading vocabulary. A detector's *meaning* (that ``level`` holds a
market price, say) lives entirely in the trading plug-in; the kernel only knows
the shape.

EventFrame column spec (normative, §4.3):

===========  =========  ===============================================
column       dtype      rule
===========  =========  ===============================================
ts           int64      knowability moment, nanoseconds UTC
event_type   string     namespaced ``{family}.{detector}.{event}``
direction    int8       +1 / -1 / 0
level        float64    primary level; NaN allowed (set a meta flag)
zone_hi      float64    NaN for point events; must be >= zone_lo
zone_lo      float64    NaN for point events
strength     float32    detector-defined 0..1
meta         string     JSON of family extras; never load-bearing
===========  =========  ===============================================
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import pyarrow as pa

from qrf.kernel.errors import SchemaViolation

# Canonical column order for an EventFrame (§4.3). Detectors build frames in this
# order; the validator checks by name, so order is a convenience, not a contract.
EVENTFRAME_COLUMNS: tuple[str, ...] = (
    "ts",
    "event_type",
    "direction",
    "level",
    "zone_hi",
    "zone_lo",
    "strength",
    "meta",
)

# The required arrow type per column. Enforced exactly (int64 ts rejects a
# timestamp[*] column — "non-ns ts" — and rejects int32).
_EVENTFRAME_TYPES: dict[str, pa.DataType] = {
    "ts": pa.int64(),
    "event_type": pa.string(),
    "direction": pa.int8(),
    "level": pa.float64(),
    "zone_hi": pa.float64(),
    "zone_lo": pa.float64(),
    "strength": pa.float32(),
    "meta": pa.string(),
}

EVENTFRAME_SCHEMA: pa.Schema = pa.schema(
    [(name, _EVENTFRAME_TYPES[name]) for name in EVENTFRAME_COLUMNS]
)

_REQUIRED_COLUMNS = frozenset(EVENTFRAME_COLUMNS)

# Calibration case kinds (§2 calibration.cases[].kind).
CALIBRATION_CASE_KINDS = frozenset({"planted_truth", "planted_noise", "insufficient"})


def _is_absent(x: object) -> bool:
    """True if a float cell is 'absent' — null or NaN (a point-event zone)."""
    return x is None or (isinstance(x, float) and math.isnan(x))


def validate_event_frame(table: object) -> None:
    """Validate an EventFrame against the §4.3 column spec.

    Raises :class:`SchemaViolation` on: a non-table input, a missing or unknown
    column, a wrong column dtype (including a non-int64 ``ts`` — e.g. a
    ``timestamp`` column), or any row where ``zone_hi < zone_lo`` (both present).
    An empty table with the correct schema is valid (detectors emit one when
    they have nothing to say).
    """
    if not isinstance(table, pa.Table):
        raise SchemaViolation(
            f"EventFrame must be a pyarrow.Table, got {type(table).__name__}"
        )

    names = set(table.column_names)
    missing = _REQUIRED_COLUMNS - names
    if missing:
        raise SchemaViolation(f"EventFrame missing column(s) {sorted(missing)}")
    unknown = names - _REQUIRED_COLUMNS
    if unknown:
        raise SchemaViolation(f"EventFrame has unknown column(s) {sorted(unknown)}")

    for name in EVENTFRAME_COLUMNS:
        want = _EVENTFRAME_TYPES[name]
        got = table.schema.field(name).type
        if not got.equals(want):
            raise SchemaViolation(
                f"EventFrame column {name!r} has dtype {got}, expected {want}"
                + (" (ts must be int64 nanoseconds UTC, not a timestamp type)"
                   if name == "ts" else "")
            )

    # zone_hi >= zone_lo wherever both are concrete (NaN/null = point event).
    hi = table.column("zone_hi").to_pylist()
    lo = table.column("zone_lo").to_pylist()
    for i, (h, low) in enumerate(zip(hi, lo, strict=True)):
        if _is_absent(h) or _is_absent(low):
            continue
        if h < low:
            raise SchemaViolation(
                f"EventFrame row {i}: zone_hi ({h}) < zone_lo ({low})"
            )


def empty_event_frame() -> pa.Table:
    """A valid, zero-row EventFrame — what a silent detector returns."""
    return EVENTFRAME_SCHEMA.empty_table()


def build_event_frame(rows: list[dict[str, Any]]) -> pa.Table:
    """Build a schema-correct EventFrame from a list of per-row dicts.

    Each row must supply every EventFrame column. Floats may be ``float('nan')``
    for absent levels/zones. The result is validated before return, so a
    detector that builds through here cannot emit a malformed frame.
    """
    if not rows:
        return empty_event_frame()
    columns = {name: [row[name] for row in rows] for name in EVENTFRAME_COLUMNS}
    arrays = [
        pa.array(columns[name], type=_EVENTFRAME_TYPES[name])
        for name in EVENTFRAME_COLUMNS
    ]
    table = pa.Table.from_arrays(arrays, names=list(EVENTFRAME_COLUMNS))
    validate_event_frame(table)
    return table


@dataclass(frozen=True)
class CalibrationCase:
    """One planted case fed to the :class:`CalibrationHarness`.

    ``data`` is the input the detector runs on (an EventFrame-shaped bar table or
    any table the detector accepts). ``expected`` is the JSON-serializable list of
    event descriptors the case asserts — ``{"ts", "event_type", "direction"}`` per
    event, sorted; ``[]`` for ``planted_noise`` / ``insufficient`` (silence). The
    heavy ``data`` never enters the ledger; only ``expected`` and the harness-
    computed ``got`` do.
    """

    case_id: str
    kind: str
    data: Any
    expected: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.kind not in CALIBRATION_CASE_KINDS:
            raise SchemaViolation(
                f"CalibrationCase.kind {self.kind!r} not in {sorted(CALIBRATION_CASE_KINDS)}"
            )


@runtime_checkable
class Detector(Protocol):
    """The detector contract (§4.3).

    A detector turns a table of observations into an EventFrame and knows its own
    calibration suite. ``params`` is validated against the detector's
    ``params_schema`` (used by the registry to build the ``instrument_registered``
    record). ``detect`` must be pure and causal: an emitted row's ``ts`` is never
    earlier than the last input row needed to compute it (anti-hindsight).
    """

    instrument_id: str
    version: str
    family: str
    params: dict[str, Any]

    def detect(self, data: pa.Table) -> pa.Table: ...

    def planted_cases(self) -> list[CalibrationCase]: ...
