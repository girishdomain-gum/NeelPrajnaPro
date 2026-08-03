"""WO-03 (S3, refs A-007 ruling (b)) — R6's batch-forward ingest.

R6 (dataset ``xauusd_ticks_vantage_r6``) has no live feed under this repo's
adopted D-5 model (no automation bridge): the Owner periodically exports
fresh Vantage ticks into the dataset's pinned ``ingest_path`` (see its
``dataset_scope`` registration, ``qrf.kernel.protocol.scope_registry``); this
script appends STRICTLY-NEWER data only, one CSV batch at a time, and
journals every batch (an ``r6_ingest_batch`` record) — the journal IS the
collection record, not a side file.

Expected CSV shape (pending real evidence — see the dataset_scope's own
``zone_evidence`` field once a real export exists): columns ``local_time``
(``YYYY-MM-DD HH:MM:SS``, broker server wall-clock, NO timezone suffix),
``bid``, ``ask``. Local timestamps are converted to UTC via the dataset's
PINNED IANA zone (``qrf.kernel.protocol.dst.local_to_utc_ns``) — ambiguous
(DST fall-back) or nonexistent (DST spring-forward) local stamps make the
WHOLE batch refuse loudly, naming the offending row; no silent fold
resolution, ever.

Idempotency (no daemon, no live socket, safe to run many times, boring to
operate — the Owner's whole role is one export + one run per batch):
refuses a batch whose ts_start is before the dataset's last-ingested ts_end
(overlap, duplicate, or a batch arriving out of order), and refuses a batch
whose ``source`` filename was already ingested for this dataset — both
loudly, before writing anything.

PIN SELF-POLICING (WO-10, A-051): the pinned zone was determined from
evidence (D-037/A-051) that Vantage's XAUUSD feed shows a daily
maintenance close at 23:55 / reopen at 01:00, server-labelled time,
confirmed unchanged across FOUR real DST transitions spanning two
calendar years (2025-10-26, 2025-11-02, 2026-03-08, 2026-03-29). A pin
verified once and trusted forever is exactly the assumption this
project keeps catching elsewhere — so every batch's local timestamps
are checked against that same invariant before ingest. If Vantage ever
changes its server clock policy mid-collection, THIS is what catches
it: the batch is refused loudly, naming the drifted boundary, instead
of a silent one-hour shift being absorbed into the dataset.

Run:  .venv/Scripts/python.exe scripts/ingest_r6.py <dataset> <csv_path>
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pandas as pd

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.dst import check_maintenance_boundary_invariant, local_to_utc_ns
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
REQUIRED_COLUMNS = ("local_time", "bid", "ask")

# Vantage XAUUSD's real, evidenced daily maintenance boundary (D-037/A-051) —
# dataset-specific, not a general R6 property. If a future dataset needs a
# different invariant, this is the place to make it per-dataset.
VANTAGE_R6_EXPECTED_CLOSE = datetime.time(23, 55)
VANTAGE_R6_EXPECTED_REOPEN = datetime.time(1, 0)
VANTAGE_R6_BOUNDARY_TOLERANCE = datetime.timedelta(minutes=10)


def _load_scope(store: RecordStore, dataset: str) -> dict:
    scopes = [
        r for r in store.query(record_type="dataset_scope")
        if r.payload["dataset"] == dataset
    ]
    if not scopes:
        raise SchemaViolation(
            f"no dataset_scope registered for {dataset!r} — run "
            "qrf.kernel.protocol.scope_registry.register first"
        )
    return scopes[-1].payload  # most recent registration is authoritative


def _read_batch_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise SchemaViolation(f"{path}: missing required column(s) {sorted(missing)}")
    if df.empty:
        raise SchemaViolation(f"{path}: no rows")
    return df


def _convert_batch_to_utc(df: pd.DataFrame, zone_name: str, source: str) -> pd.DataFrame:
    ts_ns: list[int] = []
    local_dts: list[datetime.datetime] = []
    for i, local_str in enumerate(df["local_time"]):
        try:
            naive = datetime.datetime.strptime(local_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise SchemaViolation(f"{source} row {i}: unparseable local_time {local_str!r}") from e
        local_dts.append(naive)
        ts_ns.append(local_to_utc_ns(naive, zone_name))  # raises loudly on ambiguous/nonexistent
    out = df.copy()
    out["ts"] = ts_ns
    out["_local_dt"] = local_dts
    return out.sort_values("ts").reset_index(drop=True)


def _check_boundary_invariant(sorted_local_dts: list, source: str) -> None:
    """A-051's pin self-policing: refuses loudly if this batch's own
    local timestamps show the maintenance boundary somewhere other than
    where the pin's evidence says it should be. See module docstring."""
    ok, detail = check_maintenance_boundary_invariant(
        sorted_local_dts, VANTAGE_R6_EXPECTED_CLOSE, VANTAGE_R6_EXPECTED_REOPEN,
        tolerance=VANTAGE_R6_BOUNDARY_TOLERANCE,
    )
    if not ok:
        raise SchemaViolation(f"{source}: pin self-policing check failed — {detail}")


def _last_ingested_ts_end(store: RecordStore, dataset: str) -> int | None:
    ends = [
        r.payload["ts_end"]
        for r in store.query(record_type="r6_ingest_batch")
        if r.payload["dataset"] == dataset
    ]
    return max(ends) if ends else None


def _already_ingested_source(store: RecordStore, dataset: str, source: str) -> bool:
    return any(
        r.payload["dataset"] == dataset and r.payload["source"] == source
        for r in store.query(record_type="r6_ingest_batch")
    )


def ingest_batch(store: RecordStore, dataset: str, csv_path: Path):
    """Ingest one CSV batch for ``dataset``. Refuses loudly (writes nothing)
    on: an unregistered dataset scope, a malformed/empty CSV, an ambiguous or
    nonexistent local timestamp anywhere in the batch, a duplicate source
    filename, a batch that overlaps/duplicates/precedes the last-ingested
    span, or (A-051) a batch whose own local timestamps show the pinned
    maintenance boundary has drifted from where the pin's evidence says it
    should be. Returns the appended ``r6_ingest_batch`` record on success.
    """
    source = str(csv_path)
    scope = _load_scope(store, dataset)

    if _already_ingested_source(store, dataset, source):
        raise SchemaViolation(f"{source}: already ingested for {dataset!r} — refusing duplicate")

    df = _read_batch_csv(csv_path)
    df = _convert_batch_to_utc(df, scope["iana_zone"], source)
    _check_boundary_invariant(list(df["_local_dt"]), source)

    ts_start = int(df["ts"].min())
    ts_end = int(df["ts"].max()) + 1  # half-open convention: [ts_start, ts_end)

    last_end = _last_ingested_ts_end(store, dataset)
    if last_end is not None and ts_start < last_end:
        raise SchemaViolation(
            f"{source}: batch starts at {ts_start}, before the last-ingested ts_end "
            f"{last_end} for {dataset!r} — overlap/duplicate/backwards batch refused"
        )

    return store.append(
        "r6_ingest_batch",
        {
            "dataset": dataset,
            "ts_start": ts_start,
            "ts_end": ts_end,
            "row_count": len(df),
            "source": source,
        },
        producer="script:ingest_r6",
        event_ts=now_ns(),
    )


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: ingest_r6.py <dataset> <csv_path>")
    dataset, csv_path = sys.argv[1], Path(sys.argv[2])
    store = RecordStore(JOURNAL)  # verifies chain on open
    rec = ingest_batch(store, dataset, csv_path)
    print(
        f"ingested batch={rec.record_id} dataset={dataset} "
        f"[{rec.payload['ts_start']}, {rec.payload['ts_end']}) rows={rec.payload['row_count']}"
    )


if __name__ == "__main__":
    main()
