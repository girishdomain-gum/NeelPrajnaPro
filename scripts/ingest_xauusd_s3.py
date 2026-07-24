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
close-out (``scripts/declare_virgin_s3.py``). This designates TRAINING only.

Idempotent: if a ``window`` for ``xauusd_h1_sample`` already exists, the default
run reports and writes nothing.

``--rebuild-bulk`` (REV-S3 F-1): gitignored parquet does not travel via git, so
on a fresh checkout the journal holds the ingest but the bulk file is absent.
This mode re-creates the missing parquet partition(s) from the source CSV using
the SAME deterministic write and verifies each rebuilt file's sha256 against the
EXISTING manifest. It appends NOTHING to the journal and mints no new manifest —
a mismatch raises BulkIntegrityError.

Run:  uv run python scripts/ingest_xauusd_s3.py
      uv run python scripts/ingest_xauusd_s3.py --rebuild-bulk
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import (
    QUARANTINE_SUFFIX,
    _to_store_table,
    build_bar_frame,
    flag_anomalies,
    ingest_mt5_csv,
)
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP, to_canonical

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
CSV = "IVF_S2_XAUUSD_PERIOD_H1.csv"
DATASET = "xauusd_h1_sample"
TIMEFRAME_SECONDS = 3600  # H1 — explicit (OBS-4: never inferred)
HOLIDAYS = {"2024-01-15"}  # MLK Day US market holiday (mid-week early close)


def rebuild_bulk(
    store: RecordStore,
    bulk_root: str,
    csv: str,
    dataset: str,
    timeframe_seconds: int,
    holidays: set[str] | frozenset[str],
    column_map: dict[str, str] | None,
) -> list[str]:
    """Re-create the parquet partition(s) for ``dataset`` and hash-verify them.

    Reproduces the adapter's deterministic transform + write, then verifies each
    rebuilt file against its EXISTING manifest via :meth:`BulkStore.read` (which
    raises :class:`BulkIntegrityError` on any sha256 mismatch). Appends nothing to
    the journal and mints no manifest. Returns the verified manifest ids.
    """
    bulk = BulkStore(store, bulk_root)
    raw = pd.read_csv(csv)
    frame = build_bar_frame(to_canonical(raw, column_map), timeframe_seconds)
    flagged_frame, _ = flag_anomalies(
        frame, timeframe_seconds=timeframe_seconds, holidays=holidays
    )
    is_clean = flagged_frame["flags"].map(len) == 0
    partitions = {
        dataset: (flagged_frame[is_clean], False),
        f"{dataset}{QUARANTINE_SUFFIX}": (flagged_frame[~is_clean], True),
    }

    rebuilt: list[str] = []
    for m in store.query(record_type="bulk_manifest"):
        ds = m.payload["dataset"]
        if ds not in partitions:
            continue
        df, with_flags = partitions[ds]
        table = _to_store_table(df, with_flags=with_flags)
        path = Path(bulk_root) / m.payload["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, path)
        bulk.read(m.record_id)  # hash-verify vs the existing manifest, or raise
        rebuilt.append(m.record_id)
    return rebuilt


def _run_ingest(store: RecordStore) -> None:
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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild-bulk", action="store_true",
        help="rebuild gitignored parquet from source + hash-verify vs manifests; no journal writes",
    )
    a = ap.parse_args()

    store = RecordStore(JOURNAL)  # verifies chain on open

    if a.rebuild_bulk:
        n_before = len(store)
        rebuilt = rebuild_bulk(
            store, BULK_ROOT, CSV, DATASET, TIMEFRAME_SECONDS, HOLIDAYS, IVF_S2_COLUMN_MAP
        )
        if not rebuilt:
            print(f"nothing to rebuild: no manifest for {DATASET} (run the ingest first)")
        for mid in rebuilt:
            print(f"rebuilt + hash-verified {mid}")
        assert len(store) == n_before, "rebuild must not append records"
        print(f"journal unchanged: n_records={len(store)} (rebuild writes no records)")
        return

    _run_ingest(store)


if __name__ == "__main__":
    main()
