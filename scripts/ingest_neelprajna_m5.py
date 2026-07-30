"""NP-S1 deliverables 1+3 — ingest H-07's evidenced population as M5 mid bars.

NP-ADR-008 §5 ("Architecture §3.2's stated adapter path does not apply to
this population"): the H-07 324-trade export's true source is the Stage-2
**tick parquet** (60 SHA-stamped daily files, PASS), not an MT5 bar CSV — so
this is a fresh ingestion path, not ``mt5_csv.py`` (which normalizes bar
*opens* to close-time ``ts``; there is no bar here until we build one).

Builds M5 (300s) mid bars — ``mid = (bid+ask)/2``, clean ticks only
(``clean`` AND ``bid>0`` AND ``ask>0``) — from every tick in
``F:\\NeelPrajna\\Validation\\Stage2\\parquet\\*.parquet``, writes them to
BulkStore as dataset ``xauusd_m5_vantage`` (the scope named in NP-ADR-008),
then designates the Owner-confirmed TRAINING window over the *exact* ruled
span (DEVQ-01 §3, §6): UTC half-open
``[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)``. That span is used
verbatim, not derived from the bar data's own extent — the ingested bars
necessarily run a little past it (M5 bucket granularity vs. the tick-level
designated boundary), and the window record — not the dataset's full
extent — is what "burns".

**Timezone (NP-ADR-008 Observation Space).** ``time_msc`` is stored as
broker server time (Vantage MT5, UTC+3/EEST, DST-clean across this span)
misencoded as a literal Unix epoch. True UTC = the literal reading minus 3
hours: ``true_utc_ms = time_msc - 10_800_000``. Bars are bucketed on true
UTC; ``ts`` is OBS-4 close-time (``bucket_open + 300s``), int64 ns.

Idempotent: if a window for ``xauusd_m5_vantage`` already exists, reports and
writes nothing.

Run:  .venv/Scripts/python.exe scripts/ingest_neelprajna_m5.py
"""

from __future__ import annotations

import duckdb
import pyarrow as pa

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
TICK_GLOB = "F:/NeelPrajna/Validation/Stage2/parquet/*.parquet"
DATASET = "xauusd_m5_vantage"
TIMEFRAME_SECONDS = 300  # M5, single (NP-ADR-008 frozen)
BROKER_OFFSET_MS = 3 * 3600 * 1000  # Vantage MT5 server time is UTC+3 (EEST)

# NP-ADR-008 §3 / DEVQ-01 §3+§6 — the Owner-confirmed span, verbatim.
# Computed (not hand-derived) from the ISO instants via
# datetime(2026,4,20,22,0,0,tzinfo=UTC).timestamp() * 1e9 and the 2026-07-10
# equivalent, then cross-checked against the actual ingested bar boundaries:
# WINDOW_TS_START_NS lands exactly on the first M5 bucket's open, and
# WINDOW_TS_END_NS falls inside the final bucket (bucket [14:30, 14:35) UTC,
# consistent with the ADR's last-tick time of ~14:32:59 UTC).
WINDOW_TS_START_NS = 1776722400_000000000  # 2026-04-20T22:00:00Z
WINDOW_TS_END_NS = 1783693980_000000000  # 2026-07-10T14:33:00Z


def _build_m5_bars() -> pa.Table:
    con = duckdb.connect()
    query = f"""
        SELECT
            (bucket_open_sec + {TIMEFRAME_SECONDS}) * CAST(1e9 AS BIGINT) AS ts,
            bucket_open_sec AS time,
            arg_min(mid, time_msc) AS open,
            max(mid) AS high,
            min(mid) AS low,
            arg_max(mid, time_msc) AS close
        FROM (
            SELECT
                time_msc,
                (bid + ask) / 2.0 AS mid,
                CAST(FLOOR((time_msc - {BROKER_OFFSET_MS}) / {TIMEFRAME_SECONDS * 1000}.0)
                     AS BIGINT) * {TIMEFRAME_SECONDS} AS bucket_open_sec
            FROM read_parquet('{TICK_GLOB}')
            WHERE clean AND bid > 0 AND ask > 0
        ) t
        GROUP BY bucket_open_sec
        ORDER BY bucket_open_sec
    """
    return con.sql(query).to_arrow_table()


def _run_ingest(store: RecordStore) -> None:
    for w in store.query(record_type="window"):
        if w.payload["dataset"] == DATASET:
            print(
                f"already ingested: window {w.record_id} designates {DATASET} "
                f"{w.payload['designation']}; nothing written"
            )
            return

    bars = _build_m5_bars()
    print(f"built {bars.num_rows} M5 mid bars from {TICK_GLOB}")
    ts_min = int(pa.compute.min(bars.column("ts")).as_py())
    ts_max = int(pa.compute.max(bars.column("ts")).as_py())
    print(f"bar ts range: [{ts_min}, {ts_max}]")

    bulk = BulkStore(store, BULK_ROOT)
    manifest = bulk.write(DATASET, bars, producer="script:ingest_neelprajna_m5", parents=[])
    print(f"wrote manifest {manifest.record_id} ({manifest.payload['row_count']} rows, "
          f"sha256={manifest.payload['file_sha256'][:12]}...)")

    window = WindowLedger(store).designate(
        DATASET, WINDOW_TS_START_NS, WINDOW_TS_END_NS, "TRAINING",
        producer="human:girish", parents=[manifest.record_id],
    )
    print(
        f"designated TRAINING window={window.record_id} "
        f"[{WINDOW_TS_START_NS}, {WINDOW_TS_END_NS}) on {DATASET} "
        "(NP-ADR-008 / DEVQ-01 Owner-confirmed span, not the bar data's own extent)"
    )

    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    _run_ingest(store)


if __name__ == "__main__":
    main()
