"""ARCH-003A close-out script tests: rebuild-bulk, quarantine exercise, VIRGIN.

Scripts are loaded from file (scripts/ is not a package) so the tool logic is a
single source of truth for both the CLI and these tests.
"""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import ingest_mt5_csv

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
WED_NOON = 1_704_283_200  # 2024-01-03 12:00 UTC (Wednesday)
TF = 3600


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _clean_csv(path: Path, n_bars: int) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["time", "open", "high", "low", "close"])
        w.writeheader()
        for i in range(n_bars):
            t = WED_NOON + i * TF
            w.writerow({"time": t, "open": 100, "high": 101, "low": 99, "close": 100.5})


# --- Deliverable 1: --rebuild-bulk -------------------------------------------
def test_rebuild_bulk_restores_and_leaves_journal_untouched(tmp_path):
    ing = _load("ingest_xauusd_s3")
    csv_path = tmp_path / "bars.csv"
    _clean_csv(csv_path, 6)
    journal = tmp_path / "journal" / "journal.jsonl"
    bulk_root = tmp_path / "bulk"

    store = RecordStore(journal)
    bulk = BulkStore(store, bulk_root)
    res = ingest_mt5_csv(csv_path, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk)
    parquet = bulk.path_for(res.clean_manifest)
    assert parquet.exists()

    journal_before = journal.read_bytes()
    parquet.unlink()  # simulate the gitignored file missing on a fresh checkout
    assert not parquet.exists()

    rebuilt = ing.rebuild_bulk(store, str(bulk_root), str(csv_path), "ds", TF, set(), None)
    assert rebuilt == [res.clean_manifest]
    # Hash-verified read now succeeds, and NOTHING was appended to the journal.
    assert bulk.read(res.clean_manifest).num_rows == res.rows_clean
    assert journal.read_bytes() == journal_before


# --- Deliverable 2: quarantine exercise --------------------------------------
def test_exercise_plants_all_classes_and_matches_source(tmp_path):
    ex = _load("exercise_quarantine_s3")
    out = ex.run_exercise(tmp_path)
    res = out["result"]

    # ingest_report v2 with the params object.
    assert res.report.schema_version == 2
    assert "params" in res.report.payload

    # Every anomaly class planted appears in the counts.
    expected_classes = {"non_monotonic", "duplicate", "gap", "high_lt_low",
                        "nonpositive_price", "spread_outlier"}
    assert set(res.anomaly_counts) == expected_classes
    assert res.rows_clean + res.rows_flagged == res.rows_total

    # Flagged rows value-match the synthetic source (stored unmodified).
    src = {}
    prices = ("open", "high", "low", "close")
    with open(out["csv"], newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            src[int(r["time_open_sec"])] = {p: float(r[p]) for p in prices}
    flagged = pq.read_table(out["flagged"]).to_pylist()
    assert len(flagged) == res.rows_flagged
    for row in flagged:
        assert row["flags"]  # non-empty
        for p in ("open", "high", "low", "close"):
            assert float(row[p]) == src[int(row["time"])][p]


# --- Deliverable 3: VIRGIN declaration ---------------------------------------
def test_is_confirmation_exact_phrase_only():
    dv = _load("declare_virgin_s3")
    assert dv.is_confirmation("DECLARE VIRGIN")
    assert dv.is_confirmation("  DECLARE VIRGIN  ")
    for bad in ("declare virgin", "DECLARE  VIRGIN", "DECLARE VIRGIN!", ""):
        assert not dv.is_confirmation(bad)


def test_split_boundary_semantics():
    dv = _load("declare_virgin_s3")
    ts = [i for i in range(10)]
    assert dv.split_boundary(ts, 0.30) == 7  # 3 trailing VIRGIN, 7 leading TRAINING
    with pytest.raises(ValueError):
        dv.split_boundary([1], 0.3)
    with pytest.raises(ValueError):
        dv.split_boundary(ts, 1.0)


def test_count_unexplained_flags_clean_vs_dirty(tmp_path):
    dv = _load("declare_virgin_s3")
    clean = tmp_path / "clean.csv"
    _clean_csv(clean, 8)
    n, counts = dv.count_unexplained_flags(str(clean), TF, set(), None)
    assert n == 0 and counts == {}

    dirty = tmp_path / "dirty.csv"
    with open(dirty, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["time", "open", "high", "low", "close"])
        w.writeheader()
        w.writerow({"time": WED_NOON, "open": 100, "high": 101, "low": 99, "close": 100.5})
        # high < low anomaly on the second bar
        w.writerow({"time": WED_NOON + TF, "open": 100, "high": 90, "low": 95, "close": 100.5})
    n2, counts2 = dv.count_unexplained_flags(str(dirty), TF, set(), None)
    assert n2 == 1 and counts2.get("high_lt_low") == 1


def test_designate_split_disjoint_and_reruns_refused(tmp_path):
    dv = _load("declare_virgin_s3")
    csv_path = tmp_path / "full.csv"
    _clean_csv(csv_path, 10)
    store = RecordStore(tmp_path / "journal" / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    res = ingest_mt5_csv(csv_path, "ds_full", timeframe_seconds=TF, store=store, bulk_store=bulk)

    assert dv.already_declared(store, "ds_full") is None
    ts_sorted = dv._sorted_ts(bulk, res.clean_manifest)
    training, virgin = dv.designate_split(store, "ds_full", ts_sorted, 0.30, res.manifest_refs)

    assert training.payload["designation"] == "TRAINING"
    assert virgin.payload["designation"] == "VIRGIN"
    # Disjoint half-open intervals that touch at the boundary (no overlap).
    assert training.payload["ts_end"] == virgin.payload["ts_start"]
    assert training.payload["ts_start"] == ts_sorted[0]
    assert virgin.payload["ts_end"] == ts_sorted[-1] + 1
    # Boundary bar (last TRAINING) is inside TRAINING, first VIRGIN starts next.
    split = dv.split_boundary(ts_sorted, 0.30)
    assert ts_sorted[split - 1] < training.payload["ts_end"]
    assert virgin.payload["ts_start"] == ts_sorted[split]
    # Re-run guard now trips.
    assert dv.already_declared(store, "ds_full") is not None
    assert store.verify().ok
