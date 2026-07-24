"""EventFrame validator matrix (Blueprint §4.3, ARCH-002 AC).

Each contract violation must raise SchemaViolation: unknown column, missing
column, wrong dtype, a non-int64 (timestamp) ts, and zone_hi < zone_lo. Valid
frames — including empty and point-event (NaN zone) frames — must pass.
"""

from __future__ import annotations

import math

import pyarrow as pa
import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.instruments.base import (
    EVENTFRAME_COLUMNS,
    build_event_frame,
    empty_event_frame,
    validate_event_frame,
)


def _row(**over):
    base = {
        "ts": 1,
        "event_type": "fam.det.evt",
        "direction": 0,
        "level": math.nan,
        "zone_hi": math.nan,
        "zone_lo": math.nan,
        "strength": 1.0,
        "meta": "{}",
    }
    base.update(over)
    return base


def test_valid_frame_passes():
    tbl = build_event_frame([_row(ts=1, direction=1), _row(ts=2, direction=-1)])
    validate_event_frame(tbl)  # no raise
    assert tbl.num_rows == 2
    assert list(tbl.column_names) == list(EVENTFRAME_COLUMNS)


def test_empty_frame_passes():
    validate_event_frame(empty_event_frame())


def test_point_event_nan_zone_passes():
    validate_event_frame(build_event_frame([_row(zone_hi=math.nan, zone_lo=math.nan)]))


def test_concrete_zone_ok_when_hi_ge_lo():
    validate_event_frame(build_event_frame([_row(zone_hi=2.0, zone_lo=1.0)]))
    validate_event_frame(build_event_frame([_row(zone_hi=1.0, zone_lo=1.0)]))  # equal ok


def test_zone_hi_below_lo_rejected():
    with pytest.raises(SchemaViolation):
        build_event_frame([_row(zone_hi=1.0, zone_lo=2.0)])


def test_non_table_rejected():
    with pytest.raises(SchemaViolation):
        validate_event_frame({"ts": [1]})


def test_missing_column_rejected():
    tbl = build_event_frame([_row()])
    dropped = tbl.drop(["strength"])
    with pytest.raises(SchemaViolation):
        validate_event_frame(dropped)


def test_unknown_column_rejected():
    tbl = build_event_frame([_row()])
    extra = tbl.append_column("surprise", pa.array([1], type=pa.int64()))
    with pytest.raises(SchemaViolation):
        validate_event_frame(extra)


def test_wrong_dtype_direction_rejected():
    tbl = build_event_frame([_row(direction=1)])
    # direction must be int8, not int64.
    bad = tbl.set_column(
        tbl.schema.get_field_index("direction"),
        "direction",
        pa.array([1], type=pa.int64()),
    )
    with pytest.raises(SchemaViolation):
        validate_event_frame(bad)


def test_non_ns_ts_timestamp_type_rejected():
    tbl = build_event_frame([_row(ts=1)])
    bad = tbl.set_column(
        tbl.schema.get_field_index("ts"),
        "ts",
        pa.array([1], type=pa.timestamp("ns")),
    )
    with pytest.raises(SchemaViolation):
        validate_event_frame(bad)


def test_int32_ts_rejected():
    tbl = build_event_frame([_row(ts=1)])
    bad = tbl.set_column(
        tbl.schema.get_field_index("ts"), "ts", pa.array([1], type=pa.int32())
    )
    with pytest.raises(SchemaViolation):
        validate_event_frame(bad)
