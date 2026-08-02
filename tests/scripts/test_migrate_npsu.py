"""WO-07 stage B (S5, refs A-020) — drill law for scripts/migrate_npsu.py:
idempotent per-file-batch migration, auto-detected record type, refusal on
an unrecognized column shape. Every test builds its own disposable scratch
journal — never the real one."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.epistemic import is_tainted
from qrf.kernel.records.store import RecordStore
from scripts.migrate_npsu import dry_run, migrate_one

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "migrate_npsu.py"

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


# --- addendum (A-028): --dry-run must be provably a no-op --------------------
def _bulk_file_count(bulk_root: Path) -> int:
    if not bulk_root.exists():
        return 0
    return sum(1 for p in bulk_root.rglob("*") if p.is_file())


def test_dry_run_writes_nothing_single_file(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    n_before = len(store)
    files_before = _bulk_file_count(tmp_path / "bulk")

    plans = dry_run(store, [csv_path])

    assert len(store) == n_before  # no journal append
    assert _bulk_file_count(tmp_path / "bulk") == files_before  # no Parquet/manifest
    assert len(plans) == 1
    assert plans[0].record_type == "npsu_legacy_import_trade"
    assert plans[0].row_count == 3
    assert plans[0].already_migrated is False


def test_dry_run_correctly_reports_already_migrated(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    migrate_one(store, bulk, csv_path)  # real migration first
    n_after_real = len(store)
    files_after_real = _bulk_file_count(tmp_path / "bulk")

    plans = dry_run(store, [csv_path])

    assert plans[0].already_migrated is True
    assert len(store) == n_after_real  # dry-run still wrote nothing
    assert _bulk_file_count(tmp_path / "bulk") == files_after_real


def test_dry_run_plan_matches_what_a_real_migration_would_do(tmp_path):
    """The dry-run and the real path share _plan_one — this proves the
    promise ("what the dry-run reports is what the real run will do") holds,
    not just that dry-run writes nothing."""
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS, n_rows=7)
    plan = dry_run(store, [csv_path])[0]

    rec = migrate_one(store, bulk, csv_path)
    assert rec.record_type == plan.record_type
    assert rec.payload["row_count"] == plan.row_count
    assert rec.payload["file_sha256"] == plan.file_sha256


# --- addendum (A-028): --help / -h must not be treated as a path -------------
def _run_cli(*args, cwd):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], cwd=str(cwd),
        capture_output=True, text=True,
    )


def test_help_flag_prints_usage_and_does_not_touch_the_real_journal(tmp_path):
    # Run from a directory with NO datastore\journal\ at all -- if --help were
    # ever misread as a path and fell through to RecordStore(JOURNAL), it
    # would raise (missing file) rather than print usage; a clean exit with
    # "Usage" in stdout is the proof it never got that far.
    result = _run_cli("--help", cwd=tmp_path)
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_short_help_flag_also_prints_usage(tmp_path):
    result = _run_cli("-h", cwd=tmp_path)
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_no_args_prints_usage_not_an_error(tmp_path):
    result = _run_cli(cwd=tmp_path)
    assert result.returncode == 0
    assert "Usage" in result.stdout
