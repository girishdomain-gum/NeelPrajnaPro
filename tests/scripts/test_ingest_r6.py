"""WO-03 (S3, refs A-007 ruling (b)) — drill law for scripts/ingest_r6.py:
idempotent batch-forward ingest, refuses overlap/duplicate/backwards batches
and ambiguous/nonexistent local timestamps loudly, before writing anything.
Every test builds its own disposable scratch journal — never the real one."""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol import scope_registry
from qrf.kernel.records.store import RecordStore
from scripts.ingest_r6 import ingest_batch

DATASET = "xauusd_ticks_vantage_r6_test"
ZONE = "Europe/Berlin"


def _store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


def _register_scope(store):
    return scope_registry.register(
        store,
        dataset=DATASET,
        iana_zone=ZONE,
        zone_evidence="test fixture — not a real evidence-based pin",
        ingest_path="datastore/r6_exports_test",
        batch_forward_protocol="test protocol paragraph",
        oos_designation="EXPLORATION",
        anchor_ts=1_000_000_000,
    )


def _write_csv(tmp_path, name, rows):
    """``rows`` is a list of (local_time_str, bid, ask) tuples."""
    path = tmp_path / name
    lines = ["local_time,bid,ask"] + [f"{t},{b},{a}" for t, b, a in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --- guard: no registered scope -----------------------------------------------
def test_refuses_without_registered_scope(tmp_path):
    store = _store(tmp_path)
    csv_path = _write_csv(tmp_path, "batch1.csv", [("2026-06-15 12:00:00", 100.0, 100.1)])
    with pytest.raises(SchemaViolation, match="no dataset_scope"):
        ingest_batch(store, DATASET, csv_path)


# --- happy path: first batch ---------------------------------------------------
def test_ingests_first_batch_successfully(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    csv_path = _write_csv(
        tmp_path, "batch1.csv",
        [("2026-06-15 12:00:00", 100.0, 100.1), ("2026-06-15 12:00:05", 100.1, 100.2)],
    )
    rec = ingest_batch(store, DATASET, csv_path)
    assert rec.record_type == "r6_ingest_batch"
    assert rec.payload["row_count"] == 2
    assert rec.payload["ts_end"] > rec.payload["ts_start"]


# --- malformed CSV refusals ----------------------------------------------------
def test_refuses_missing_columns(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    path = tmp_path / "bad.csv"
    path.write_text("local_time,bid\n2026-06-15 12:00:00,100.0\n", encoding="utf-8")
    with pytest.raises(SchemaViolation, match="missing required column"):
        ingest_batch(store, DATASET, path)


def test_refuses_empty_csv(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    path = tmp_path / "empty.csv"
    path.write_text("local_time,bid,ask\n", encoding="utf-8")
    with pytest.raises(SchemaViolation, match="no rows"):
        ingest_batch(store, DATASET, path)


# --- DST refusals ride end-to-end through the real ingest path ---------------
def test_refuses_batch_with_nonexistent_local_time(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    csv_path = _write_csv(
        tmp_path, "gap.csv",
        [("2026-06-15 12:00:00", 100.0, 100.1), ("2026-03-29 02:30:00", 99.0, 99.1)],
    )
    with pytest.raises(SchemaViolation, match="does not exist"):
        ingest_batch(store, DATASET, csv_path)
    assert len(list(store.query(record_type="r6_ingest_batch"))) == 0  # untouched


def test_refuses_batch_with_ambiguous_local_time(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    csv_path = _write_csv(
        tmp_path, "overlap.csv",
        [("2026-06-15 12:00:00", 100.0, 100.1), ("2026-10-25 02:30:00", 99.0, 99.1)],
    )
    with pytest.raises(SchemaViolation, match="ambiguous"):
        ingest_batch(store, DATASET, csv_path)
    assert len(list(store.query(record_type="r6_ingest_batch"))) == 0  # untouched


# --- idempotency: duplicate source file -----------------------------------------
def test_refuses_duplicate_source_file(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    csv_path = _write_csv(tmp_path, "batch1.csv", [("2026-06-15 12:00:00", 100.0, 100.1)])
    ingest_batch(store, DATASET, csv_path)
    with pytest.raises(SchemaViolation, match="already ingested"):
        ingest_batch(store, DATASET, csv_path)


# --- idempotency: overlap/duplicate/backwards batches ---------------------------
def test_refuses_overlapping_batch(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    first = _write_csv(tmp_path, "batch1.csv", [("2026-06-15 12:00:00", 100.0, 100.1)])
    ingest_batch(store, DATASET, first)
    # Second batch starts BEFORE the first one's ts_end — overlap/backwards.
    second = _write_csv(tmp_path, "batch2.csv", [("2026-06-15 11:59:59", 99.0, 99.1)])
    with pytest.raises(SchemaViolation, match="overlap/duplicate/backwards"):
        ingest_batch(store, DATASET, second)
    assert len(list(store.query(record_type="r6_ingest_batch"))) == 1  # only the first


def test_second_strictly_newer_batch_succeeds(tmp_path):
    store = _store(tmp_path)
    _register_scope(store)
    first = _write_csv(tmp_path, "batch1.csv", [("2026-06-15 12:00:00", 100.0, 100.1)])
    ingest_batch(store, DATASET, first)
    second = _write_csv(tmp_path, "batch2.csv", [("2026-06-16 12:00:00", 100.0, 100.1)])
    rec = ingest_batch(store, DATASET, second)
    assert rec.payload["row_count"] == 1
    assert len(list(store.query(record_type="r6_ingest_batch"))) == 2
