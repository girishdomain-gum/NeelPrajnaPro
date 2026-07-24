"""ARCH-003 — ingest the real Sprint-2 XAUUSD export into the data plane.

Ingests ``IVF_S2_XAUUSD_PERIOD_H1.csv`` (MT5-format plus extra columns) as
dataset ``xauusd_h1_sample`` via the mt5_csv adapter, then designates the whole
span TRAINING. Manifests, the ingest_report, and the window record land in the
real journal; the parquet files land under ``datastore/bulk/`` (gitignored,
rebuildable — the manifest is the root of trust).

Gap allowance (DEVQ-006): weekend closes are excused automatically; the one
mid-week hole in this month is the 2024-01-15 US market holiday (MLK Day), passed
explicitly as a declared holiday so it does not flag. Result: 0 unexplained flags.

**Not** a VIRGIN declaration — that is the Owner's act over a larger export at
close-out (ARCH-003A). This designates TRAINING only.

Idempotent: if a ``window`` for ``xauusd_h1_sample`` already exists, it reports
and writes nothing.

Run:  uv run python scripts/ingest_xauusd_s3.py
"""

from __future__ import annotations

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import ingest_mt5_csv
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
CSV = "IVF_S2_XAUUSD_PERIOD_H1.csv"
DATASET = "xauusd_h1_sample"
TIMEFRAME_SECONDS = 3600  # H1 — explicit (OBS-4: never inferred)
HOLIDAYS = {"2024-01-15"}  # MLK Day US market holiday (mid-week early close)


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open

    for w in store.query(record_type="window"):
        if w.payload["dataset"] == DATASET:
            print(f"already ingested: window {w.record_id} designates {DATASET} "
                  f"{w.payload['designation']}; nothing written")
            return

    bulk = BulkStore(store, BULK_ROOT)
    res = ingest_mt5_csv(
        CSV, DATASET,
        timeframe_seconds=TIMEFRAME_SECONDS,
        store=store, bulk_store=bulk,
        column_map=IVF_S2_COLUMN_MAP,
        holidays=HOLIDAYS,
    )
    print(f"ingested {res.rows_total} rows: clean={res.rows_clean} flagged={res.rows_flagged}")
    print(f"anomaly_counts={res.anomaly_counts} verdict={res.verdict}")
    print(f"ingest_report={res.report.record_id} manifests={res.manifest_refs}")

    window = WindowLedger(store).designate(
        DATASET, res.ts_min, res.ts_max, "TRAINING",
        producer="human:girish", parents=res.manifest_refs,
    )
    print(f"designated TRAINING window={window.record_id} "
          f"[{res.ts_min}, {res.ts_max}] on {DATASET}")

    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()
