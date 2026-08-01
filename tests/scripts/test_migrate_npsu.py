"""WO-07 stage B (S5, refs A-020) — drill law for scripts/migrate_npsu.py:
idempotent per-file-batch migration, auto-detected record type, refusal on
an unrecognized column shape. Every test builds its own disposable scratch
journal — never the real one."""

from __future__ import annotations

import pandas as pd
import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.epistemic import is_tainted
from qrf.kernel.records.store import RecordStore
from scripts.migrate_npsu import migrate_one

TRADE_COLUMNS = ["schema_version", "run_id", "position_id", "gate", "direction", "profit"]
SHADOW_COLUMNS = ["schema_version", "run_id", "universe_id", "universe_name", "profit_R"]


def _store_and_bulk(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, str(tmp_path / "bulk"))
    return store, bulk


def _write_csv(tmp_path, name, columns, n_rows=3):
    path = tmp_path / name
    df = pd.DataFrame({c: list(range(n_rows)) for c in columns})
    df.to_csv(path, index=False)
    return path


def test_migrates_trade_shape_as_trade_type(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    rec = migrate_one(store, bulk, csv_path)
    assert rec.record_type == "npsu_legacy_import_trade"
    assert rec.payload["row_count"] == 3
    assert rec.payload["epistemic_weight"] == "zero"
    assert is_tainted(store, rec.record_id)


def test_migrates_shadow_shape_as_shadow_type(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "shadow.csv", SHADOW_COLUMNS)
    rec = migrate_one(store, bulk, csv_path)
    assert rec.record_type == "npsu_legacy_import_shadow"
    assert is_tainted(store, rec.record_id)


def test_refuses_unrecognized_column_shape(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "mystery.csv", ["a", "b", "c"])
    n_before = len(store)
    with pytest.raises(SchemaViolation, match="cannot classify"):
        migrate_one(store, bulk, csv_path)
    assert len(store) == n_before


def test_idempotent_same_file_migrated_once(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    first = migrate_one(store, bulk, csv_path)
    assert first is not None
    n_after_first = len(store)

    second = migrate_one(store, bulk, csv_path)
    assert second is None  # already migrated, nothing written
    assert len(store) == n_after_first


def test_appends_exactly_two_records_per_migration(tmp_path):
    """One bulk_manifest (the rows) + one npsu_legacy_import_* (the event) —
    asserted, not narrated, per this project's own sharpened AT-5 standard."""
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    n_before = len(store)
    migrate_one(store, bulk, csv_path)
    assert len(store) == n_before + 2
    assert len(list(store.query(record_type="bulk_manifest"))) == 1
    assert len(list(store.query(record_type="npsu_legacy_import_trade"))) == 1


def test_two_different_files_both_migrate(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    a = _write_csv(tmp_path, "trade_a.csv", TRADE_COLUMNS)
    b = _write_csv(tmp_path, "trade_b.csv", TRADE_COLUMNS, n_rows=5)
    rec_a = migrate_one(store, bulk, a)
    rec_b = migrate_one(store, bulk, b)
    assert rec_a is not None and rec_b is not None
    assert rec_a.record_id != rec_b.record_id
    assert rec_a.payload["file_sha256"] != rec_b.payload["file_sha256"]
