"""Schema tests for the Sprint-3 data-plane record types (Blueprint §2).

bulk_manifest / ingest_report / window / window_burn: accept a valid payload,
reject missing/unknown fields, bad enums and wrong types. These validate through
``RecordStore.append`` (I-4), the same path production uses.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records import schemas


def _ok(rt, payload):
    schemas.validate(rt, payload, 1)


def test_bulk_manifest_valid_and_rejections():
    good = {
        "path": "ds/part-00000.parquet",
        "dataset": "ds",
        "row_count": 3,
        "byte_size": 1234,
        "file_sha256": "ab" * 32,
        "columns": [{"name": "ts", "dtype": "int64"}, {"name": "open", "dtype": "double"}],
        "ts_min": 10,
        "ts_max": 30,
    }
    _ok("bulk_manifest", good)

    with pytest.raises(SchemaViolation):  # ts_max < ts_min
        _ok("bulk_manifest", {**good, "ts_min": 40})
    with pytest.raises(SchemaViolation):  # negative row_count
        _ok("bulk_manifest", {**good, "row_count": -1})
    with pytest.raises(SchemaViolation):  # column missing dtype
        _ok("bulk_manifest", {**good, "columns": [{"name": "ts"}]})
    with pytest.raises(SchemaViolation):  # unknown field
        _ok("bulk_manifest", {**good, "extra": 1})
    with pytest.raises(SchemaViolation):  # bool is not int
        _ok("bulk_manifest", {**good, "byte_size": True})


def test_ingest_report_valid_and_rejections():
    good = {
        "manifest_refs": ["01A", "01B"],
        "rows_clean": 500,
        "rows_flagged": 4,
        "anomaly_counts": {"gap": 3, "duplicate": 1},
        "verdict": "PASS",
    }
    _ok("ingest_report", good)

    with pytest.raises(SchemaViolation):  # bad verdict enum
        _ok("ingest_report", {**good, "verdict": "MAYBE"})
    with pytest.raises(SchemaViolation):  # anomaly count not int
        _ok("ingest_report", {**good, "anomaly_counts": {"gap": "lots"}})
    with pytest.raises(SchemaViolation):  # manifest_refs not all strings
        _ok("ingest_report", {**good, "manifest_refs": ["01A", 2]})


def test_ingest_report_v2_params_valid_and_rejections():
    params = {
        "timeframe_seconds": 3600,
        "gap_k": 1.0,
        "weekend_allowance": True,
        "holidays": ["2024-01-01", "2024-01-15"],
        "spread_mad_k": 5.0,
        "flagged_threshold": 0.05,
        "dataset": "xauusd_h1_sample",
    }
    good = {
        "manifest_refs": ["01A"],
        "rows_clean": 500,
        "rows_flagged": 4,
        "anomaly_counts": {"gap": 4},
        "verdict": "PASS",
        "params": params,
    }
    schemas.validate("ingest_report", good, 2)

    # v1 must reject the params key (unknown field under v1).
    with pytest.raises(SchemaViolation):
        schemas.validate("ingest_report", good, 1)
    # v2 requires params.
    with pytest.raises(SchemaViolation):
        schemas.validate("ingest_report", {k: v for k, v in good.items() if k != "params"}, 2)
    # holidays must be sorted.
    with pytest.raises(SchemaViolation):
        bad = {**good, "params": {**params, "holidays": ["2024-01-15", "2024-01-01"]}}
        schemas.validate("ingest_report", bad, 2)
    # weekend_allowance must be a bool.
    with pytest.raises(SchemaViolation):
        bad_wa = {**good, "params": {**params, "weekend_allowance": "yes"}}
        schemas.validate("ingest_report", bad_wa, 2)
    # timeframe_seconds must be a positive int.
    with pytest.raises(SchemaViolation):
        schemas.validate("ingest_report", {**good, "params": {**params, "timeframe_seconds": 0}}, 2)
    # unknown param key rejected.
    with pytest.raises(SchemaViolation):
        schemas.validate("ingest_report", {**good, "params": {**params, "tz": "UTC"}}, 2)


def test_window_valid_and_rejections():
    good = {"dataset": "ds", "ts_start": 10, "ts_end": 40, "designation": "TRAINING"}
    _ok("window", good)
    for des in ("EXPLORATION", "VIRGIN"):
        _ok("window", {**good, "designation": des})

    with pytest.raises(SchemaViolation):  # bad designation
        _ok("window", {**good, "designation": "HOLDOUT"})
    with pytest.raises(SchemaViolation):  # ts_end <= ts_start
        _ok("window", {**good, "ts_end": 10})


def test_window_burn_valid_and_rejections():
    good = {"window_ref": "01W", "lineage": "famA", "consumed_by": "01V"}
    _ok("window_burn", good)
    with pytest.raises(SchemaViolation):  # missing consumed_by
        _ok("window_burn", {"window_ref": "01W", "lineage": "famA"})
    with pytest.raises(SchemaViolation):  # wrong type
        _ok("window_burn", {**good, "lineage": 5})
