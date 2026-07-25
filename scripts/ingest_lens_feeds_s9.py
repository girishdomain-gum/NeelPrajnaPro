"""ARCH-009 §4 — ingest the two independent-lens feeds (raw storage only).

The Owner's ARCH-009 data drop delivered a matched export pair from the QRF_Data_Export
tool: the PRIMARY feed (Winprofx, server time, 2-digit) and the SECOND feed (Exness,
UTC, 3-digit), both XAUUSD H1 spanning 2024-01..2025-12. This script ingests BOTH as
new datasets with hash-anchored manifests and an ingest_report v2 (params recorded).

It writes NO window records and designates NO reserve — storage is not computation
(ARCH-009 §4 ADDENDUM: "The raw second-feed CSV/parquet may of course CONTAIN [VIRGIN]
rows — storage is not computation"). The TRAINING/VIRGIN split of the primary extension
is the Owner's typed-phrase act (scripts/declare_virgin_2025_s9.py); the cross-feed
overlap/agreement is a later, pre-registered computation.

Both feeds use the ARCH-009 export schema (``time_open_sec,time_close_sec,open,high,
low,close,rsi14,dow``); the mt5_csv adapter reads it via IVF_S2_COLUMN_MAP (ts = close
basis, OBS-4). The clocks DIFFER by design (server vs UTC) — the raw ts are stored
as-exported; clock alignment happens at overlap time (ARCH-009 ADDENDUM 2).

    F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py
    F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk

Idempotent: a feed whose dataset already has a bulk_manifest is skipped.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import ingest_mt5_csv
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP

# scripts/ is not a package: load the sibling rebuild path by file (reuse, not copy).
_spec = importlib.util.spec_from_file_location(
    "ingest_xauusd_s3", Path(__file__).resolve().parent / "ingest_xauusd_s3.py"
)
_ingest_s3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ingest_s3)
rebuild_bulk = _ingest_s3.rebuild_bulk

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
TIMEFRAME_SECONDS = 3600  # H1 — explicit (OBS-4: never inferred)

# US market / COMEX gold mid-week closes across the 2024-2025 span that appear as
# gaps in these exports (weekends are auto-excused). A holiday that is not actually
# a gap is harmless (it only excuses); declaring too few would flag. Recorded in the
# ingest_report params either way, so the anomaly verdict is reconstructable.
HOLIDAYS_2024_2025 = frozenset({
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29", "2024-05-27",
    "2024-06-19", "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18", "2025-05-26",
    "2025-06-19", "2025-07-04", "2025-09-01", "2025-11-27", "2025-12-25",
})

# (csv, dataset) — the primary feed keeps the "primary" name; the second lens is
# named for its role, not "exactly two" (ARCH-009 Independent Observation Lenses note).
FEEDS = [
    ("ivf/mt5/QRF_XAUUSD_PERIOD_H1_20240101_20260101_primary_full.csv",
     "xauusd_h1_primary_full"),
    ("ivf/mt5/QRF_XAUUSDm_PERIOD_H1_20240101_20260101_secondfeed.csv",
     "xauusd_h1_secondfeed"),
]


def _already_ingested(store: RecordStore, dataset: str) -> bool:
    return any(
        m.payload["dataset"] == dataset for m in store.query(record_type="bulk_manifest")
    )


def rebuild() -> None:
    store = RecordStore(JOURNAL)
    for csv, dataset in FEEDS:
        refs = rebuild_bulk(store, BULK_ROOT, csv, dataset, TIMEFRAME_SECONDS,
                            HOLIDAYS_2024_2025, IVF_S2_COLUMN_MAP)
        print(f"{dataset}: rebuilt + hash-verified {len(refs)} partition(s)")


def ingest() -> None:
    store = RecordStore(JOURNAL)  # verifies the chain on open
    bulk = BulkStore(store, BULK_ROOT)
    for csv, dataset in FEEDS:
        if _already_ingested(store, dataset):
            print(f"{dataset}: already ingested (bulk_manifest present); skipping.")
            continue
        res = ingest_mt5_csv(
            csv, dataset, timeframe_seconds=TIMEFRAME_SECONDS,
            store=store, bulk_store=bulk, column_map=IVF_S2_COLUMN_MAP,
            holidays=HOLIDAYS_2024_2025,
        )
        p = res.report.payload
        print(
            f"{dataset}: ingest_report {res.report.record_id} verdict={p['verdict']} "
            f"rows_clean={p['rows_clean']} rows_flagged={p['rows_flagged']} "
            f"manifests={p['manifest_refs']}"
        )
    rep = store.verify()
    print(f"journal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rebuild-bulk", action="store_true",
                    help="rebuild the gitignored parquet(s) from CSV + hash-verify (no writes)")
    a = ap.parse_args()
    if a.rebuild_bulk:
        rebuild()
        return
    ingest()


if __name__ == "__main__":
    main()
