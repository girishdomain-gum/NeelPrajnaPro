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
from scripts.migrate_npsu import _group_by_sha256, dry_run, migrate_group, migrate_one

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


def test_migrate_one_always_carries_empty_duplicate_list(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    csv_path = _write_csv(tmp_path, "trade.csv", TRADE_COLUMNS)
    rec = migrate_one(store, bulk, csv_path)
    assert rec.payload["duplicate_source_paths"] == []


# --- F-MIG-1 (A-030): content duplicates under DIFFERENT basenames ------------
def _write_identical_content_csv(tmp_path, name, columns, n_rows=3):
    """A second file with the SAME bytes as one built by _write_csv with the
    same (columns, n_rows) — simulates the real estate's byte-identical
    cross-basename pairs (F-MIG-1), not the already-handled bridge/results
    vs runs/*/csv MIRROR (same basename, collapsed earlier by
    _discover_estate_files)."""
    return _write_csv(tmp_path, name, columns, n_rows=n_rows)


def test_group_by_sha256_finds_cross_basename_content_duplicates(tmp_path):
    a = _write_csv(tmp_path, "0006_backtest.NP_Trades_x.csv", TRADE_COLUMNS)
    b = _write_identical_content_csv(tmp_path, "0007_backtest.NP_Trades_y.csv", TRADE_COLUMNS)
    c = _write_csv(tmp_path, "trade_different.csv", TRADE_COLUMNS, n_rows=9)

    groups = _group_by_sha256([a, b, c])
    assert len(groups) == 2  # a+b share content; c is its own group
    ab_group = next(g for g in groups if len(g.paths) == 2)
    assert {ab_group.primary, *ab_group.duplicates} == {a, b}
    assert ab_group.primary == min(a, b, key=str)  # deterministic: path-sorted


def test_dry_run_reports_duplicate_as_would_skip_not_would_migrate(tmp_path):
    store, _ = _store_and_bulk(tmp_path)
    a = _write_csv(tmp_path, "0006_backtest.NP_Trades_x.csv", TRADE_COLUMNS)
    b = _write_identical_content_csv(tmp_path, "0007_backtest.NP_Trades_y.csv", TRADE_COLUMNS)

    plans = dry_run(store, [a, b])

    assert len(plans) == 1  # one group, not two independent "would migrate" plans
    assert plans[0].already_migrated is False
    assert set(plans[0].duplicate_paths) == {a, b} - {plans[0].primary_path}


def test_dry_run_predicted_equals_real_run_actual(tmp_path):
    """A-030's own required test: two identical-content, different-named
    fixture files -- what the dry-run predicts must equal what the real run
    then does, exactly (F-MIG-1's gap, closed)."""
    store, bulk = _store_and_bulk(tmp_path)
    a = _write_csv(tmp_path, "0006_backtest.NP_Trades_x.csv", TRADE_COLUMNS, n_rows=4)
    b = _write_identical_content_csv(
        tmp_path, "0007_backtest.NP_Trades_y.csv", TRADE_COLUMNS, n_rows=4
    )

    predicted = dry_run(store, [a, b])
    n_before = len(store)
    predicted_would_migrate = sum(1 for p in predicted if not p.already_migrated)
    predicted_rows = sum(p.row_count for p in predicted if not p.already_migrated)

    groups = _group_by_sha256([a, b])
    actual_migrated = [g for g in groups if migrate_group(store, bulk, g) is not None]

    assert len(actual_migrated) == predicted_would_migrate == 1
    assert len(store) == n_before + 2  # exactly one group's worth: manifest + record
    rec = next(iter(store.query(record_type="npsu_legacy_import_trade")))
    assert rec.payload["row_count"] == predicted_rows == 4
    # The provenance decision (A-030 option (b)): the skipped path survives
    # in the migrated record, never silently dropped.
    assert set(rec.payload["duplicate_source_paths"]) | {rec.payload["source"]} == {
        str(a), str(b),
    }


def test_dry_run_predicted_equals_real_run_actual_when_already_migrated(tmp_path):
    store, bulk = _store_and_bulk(tmp_path)
    a = _write_csv(tmp_path, "0006_backtest.NP_Trades_x.csv", TRADE_COLUMNS)
    b = _write_identical_content_csv(tmp_path, "0007_backtest.NP_Trades_y.csv", TRADE_COLUMNS)
    migrate_group(store, bulk, _group_by_sha256([a, b])[0])  # migrate once, for real
    n_after_first = len(store)

    plans = dry_run(store, [a, b])
    assert plans[0].already_migrated is True

    groups = _group_by_sha256([a, b])
    result = migrate_group(store, bulk, groups[0])
    assert result is None  # nothing newly written, matching the dry-run's prediction
    assert len(store) == n_after_first


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
