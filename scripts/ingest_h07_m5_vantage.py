"""NP-S1 deliverable-2 prerequisite — ingest XAUUSD M5 mid bars for scope
``xauusd_m5_vantage`` (NP-ADR-008 §5 v1.1 data path, §5 "M7 — corrected").

Architecture §3.2's ``NP_Trades_*``/``NPSU_Trades_*`` CSV path through
``mt5_csv.py`` does NOT apply to this population — the evidenced source is the
Stage-2 tick parquet (60 SHA-stamped daily files), never the retired bespoke
stack's own Stage-3 ``bars_300s.parquet`` output (using that would be an
evidentiary use of the retired stack — a standing tripwire, Execution Plan §3).
This script builds M5 mid bars from raw ticks itself:

1. Read every ``F:\\NeelPrajna\\Validation\\Stage2\\parquet\\NP_TICKS_XAUUSD_*.parquet``
   file (``time_msc, bid, ask, clean`` columns only).
2. Keep clean ticks only: ``clean & bid > 0 & ask > 0`` (NP-ADR-008 §3
   Observation Space).
3. **Broker-time correction.** ``time_msc`` is stored in Vantage broker server
   time (EEST = UTC+3 across this whole span, DST-clean — independently
   verified by the Architect/Owner on the record, DEVQ-NP-002 reply Q2), NOT
   true UTC, exactly like the H-07 trades export it feeds. Confirmed directly
   against the first tick file: its earliest ``time_msc``, read as literal UTC,
   is 2026-04-21T01:00:01.425Z — matching DEVQ-NP-002's own record of the
   *stored* tick-capture start (Vantage server time 2026-04-21 01:00:00), not
   the *true UTC* start it maps to (2026-04-20 22:00:00Z). Every timestamp is
   therefore corrected by **-3h (10800s, an exact multiple of the 300s bucket
   width, so bucket boundaries are unaffected by correction order)** before
   bucketing.
4. mid = (bid + ask) / 2; bucket the corrected-UTC second into 300s (M5)
   buckets by floor division on the bucket START (open) second.
5. OHLC of the mid per bucket: open=first, high=max, low=min, close=last,
   ticks=count.
6. ``ts`` per bar = OBS-4 close-time convention, consistent with the rest of
   this Kernel's data plane (``mt5_csv.build_bar_frame``/``compute_close_ts``,
   and BulkStore's own docstring: "ts is kernel vocabulary — the EventFrame
   knowability moment"): ``ts_ns = (bucket_open_epoch_sec + 300) * 1e9``. This
   is a uniform +300s relabelling versus the evidenced pipeline's own
   bucket-open ``bar_ts`` — it changes no detector decision (which is entirely
   bar-INDEX driven, never ts-value driven; see the detector module docstring),
   only the epoch label attached to each bar/event, and it is *more*
   conservative for knowability (a bar's close time is when its H/L/C are
   actually fully known).

The TRAINING window is designated over NP-ADR-008 §3's *sealed, Owner-confirmed*
UTC half-open interval — [2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z) — not
whatever ts_min/ts_max this ingestion happens to produce; the actual observed
bar range is printed for audit against that sealed value.

Idempotent: if a ``window`` for dataset ``xauusd_m5_vantage`` already exists,
the run reports and writes nothing.

Run:  .venv/Scripts/python.exe scripts/ingest_h07_m5_vantage.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET = "xauusd_m5_vantage"  # == scope (NP-ADR-008 §3); no separate dataset name given
TICK_DIR = Path(r"F:\NeelPrajna\Validation\Stage2\parquet")
TIMEFRAME_SECONDS = 300  # M5, single (NP-ADR-008 §3 frozen parameters)
NS_PER_SEC = 1_000_000_000
BROKER_TO_UTC_OFFSET_SECONDS = 3 * 3600  # Vantage EEST = UTC+3, DST-clean (DEVQ-NP-002 Q2)

# NP-ADR-008 §3 "Designated coverage" / Execution Plan §0 — sealed, Owner-
# confirmed 2026-07-30. Hard-coded, not derived from the ingest, per P8/window
# designation discipline: a scope-designated window is not sealed until the
# Owner has seen and confirmed the concrete span, which has already happened.
SEALED_TS_START_NS = 1776722400000000000  # 2026-04-20T22:00:00Z
SEALED_TS_END_NS = 1783693980000000000  # 2026-07-10T14:33:00Z (half-open)


def build_m5_bars(tick_dir: Path) -> pd.DataFrame:
    """Ticks -> M5 mid-bar OHLC, OBS-4 close-time ``ts`` (int64 ns UTC)."""
    files = sorted(tick_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"no tick parquet files in {tick_dir}")
    parts: list[pd.DataFrame] = []
    total_ticks = 0
    clean_ticks = 0
    for f in files:
        df = pd.read_parquet(f, columns=["time_msc", "bid", "ask", "clean"])
        total_ticks += len(df)
        df = df[df["clean"] & (df["bid"] > 0) & (df["ask"] > 0)]
        clean_ticks += len(df)
        if df.empty:
            continue
        mid = (df["bid"] + df["ask"]) / 2.0
        # time_msc is broker (Vantage EEST/UTC+3) epoch millis; correct to true
        # UTC before bucketing (see module docstring point 3).
        epoch_sec_utc = df["time_msc"] // 1000 - BROKER_TO_UTC_OFFSET_SECONDS
        bucket_open_sec = (epoch_sec_utc // TIMEFRAME_SECONDS) * TIMEFRAME_SECONDS
        g = mid.groupby(bucket_open_sec.values)
        parts.append(
            pd.DataFrame(
                {
                    "bucket_open_sec": g.size().index.astype("int64"),
                    "open": g.first().values,
                    "high": g.max().values,
                    "low": g.min().values,
                    "close": g.last().values,
                    "ticks": g.size().values,
                }
            )
        )
    print(f"ticks: total={total_ticks} clean={clean_ticks} ({clean_ticks / total_ticks:.4%})")

    bars = (
        pd.concat(parts)
        .groupby("bucket_open_sec", as_index=False)
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            ticks=("ticks", "sum"),
        )
        .sort_values("bucket_open_sec")
        .reset_index(drop=True)
    )
    # OBS-4: ts = close time = bucket open + timeframe, int64 ns UTC.
    bars["ts"] = (bars["bucket_open_sec"] + TIMEFRAME_SECONDS).astype("int64") * NS_PER_SEC
    return bars[["ts", "open", "high", "low", "close", "ticks"]]


def _bars_to_table(bars: pd.DataFrame) -> pa.Table:
    """The exact BulkStore table shape written at ingest (reused by rebuild)."""
    return pa.table(
        {
            "ts": pa.array(bars["ts"].tolist(), type=pa.int64()),
            "open": pa.array(bars["open"].tolist(), type=pa.float64()),
            "high": pa.array(bars["high"].tolist(), type=pa.float64()),
            "low": pa.array(bars["low"].tolist(), type=pa.float64()),
            "close": pa.array(bars["close"].tolist(), type=pa.float64()),
            "ticks": pa.array(bars["ticks"].tolist(), type=pa.int64()),
        }
    )


def rebuild_bulk() -> None:
    """Re-create the gitignored M5 bars parquet from raw ticks; hash-verify.

    Mirrors ``judge_h001.rebuild_bulk``'s pattern: the manifest (and its path,
    dataset name, recorded sha256) is already in the journal from the original
    ingest; only the file bytes are gitignored and need reconstructing.
    """
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)
    manifest = next(
        (m for m in store.query(record_type="bulk_manifest") if m.payload["dataset"] == DATASET),
        None,
    )
    if manifest is None:
        raise SystemExit(
            f"no bulk_manifest for {DATASET} — run scripts/ingest_h07_m5_vantage.py first"
        )
    table = _bars_to_table(build_m5_bars(TICK_DIR))
    path = Path(BULK_ROOT) / manifest.payload["path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    try:
        bulk.read(manifest.record_id)  # hash-verify vs the existing manifest, or raise
    except BulkIntegrityError as e:
        raise SystemExit(
            f"rebuild hash mismatch: {e}\nThe raw tick source at {TICK_DIR} does not "
            "match the ingest that produced the manifest."
        ) from e
    assert len(store) == n_before, "rebuild must not append records"
    print(f"rebuilt + hash-verified {manifest.record_id} ({DATASET}, {table.num_rows} rows)")


def _run_ingest(store: RecordStore) -> None:
    for w in store.query(record_type="window"):
        if w.payload["dataset"] == DATASET:
            print(
                f"already ingested: window {w.record_id} designates {DATASET} "
                f"{w.payload['designation']}; nothing written"
            )
            return

    bulk = BulkStore(store, BULK_ROOT)
    bars = build_m5_bars(TICK_DIR)
    print(f"built {len(bars)} M5 bars from {TICK_DIR}")
    print(
        f"observed ts range: [{int(bars['ts'].min())}, {int(bars['ts'].max())}] "
        f"vs sealed window [{SEALED_TS_START_NS}, {SEALED_TS_END_NS})"
    )

    table = _bars_to_table(bars)
    manifest = bulk.write(DATASET, table, producer="human:girish", parents=[])
    print(f"wrote bulk_manifest={manifest.record_id} rows={manifest.payload['row_count']}")

    window = WindowLedger(store).designate(
        DATASET,
        SEALED_TS_START_NS,
        SEALED_TS_END_NS,
        "TRAINING",
        producer="human:girish",
        parents=[manifest.record_id],
    )
    print(
        f"designated TRAINING window={window.record_id} "
        f"[{SEALED_TS_START_NS}, {SEALED_TS_END_NS}) on {DATASET}"
    )

    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    _run_ingest(store)


if __name__ == "__main__":
    main()
