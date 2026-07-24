"""ARCH-003A — VIRGIN reserve declaration tool (the Owner runs this, not the AI).

Ingests the Owner's BIGGER XAUUSD H1 export as dataset ``xauusd_h1_full``
(timeframe 3600, ingest_report v2), then — only after the report is PASS with
**0 unexplained flags** and the Owner types the exact phrase ``DECLARE VIRGIN`` —
designates a TRAILING portion of the span VIRGIN and the leading portion
TRAINING, over DISJOINT half-open intervals so contamination is impossible by
construction (the boundary bar belongs to TRAINING; VIRGIN starts at the next
bar).

Refusals:
- verdict not PASS / any flagged rows  -> abort, nothing designated;
- already declared (a window for ``xauusd_h1_full`` exists) -> abort;
- phrase not typed exactly              -> abort, no window.

The Developer implements this; the **Owner** runs it. The Owner's console phrase
and the printed record ids go into GO-S3.md.

Run:  uv run python scripts/declare_virgin_s3.py --csv <export.csv> \
        --holidays 2024-01-01,2024-01-15 [--virgin-fraction 0.30]
"""

from __future__ import annotations

import argparse

import pandas as pd

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import build_bar_frame, flag_anomalies, ingest_mt5_csv
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP, to_canonical

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET_FULL = "xauusd_h1_full"
TIMEFRAME_SECONDS = 3600
DEFAULT_VIRGIN_FRACTION = 0.30
CONFIRM_PHRASE = "DECLARE VIRGIN"


def is_confirmation(text: str) -> bool:
    """True only for the exact confirmation phrase (surrounding whitespace ok)."""
    return text.strip() == CONFIRM_PHRASE


def already_declared(store: RecordStore, dataset: str) -> Record | None:
    """The existing ``window`` for ``dataset`` if any (the re-run guard)."""
    for w in store.query(record_type="window"):
        if w.payload["dataset"] == dataset:
            return w
    return None


def count_unexplained_flags(
    csv: str, timeframe_seconds: int, holidays: set[str], column_map: dict[str, str] | None
) -> tuple[int, dict[str, int]]:
    """Dry pass (no writes): how many rows would be flagged, by class.

    A flag here is by definition *unexplained* — weekend/holiday gaps do not
    flag. Used to abort before any journal write if the export is not clean.
    """
    raw = pd.read_csv(csv)
    frame = build_bar_frame(to_canonical(raw, column_map), timeframe_seconds)
    flagged_frame, counts = flag_anomalies(
        frame, timeframe_seconds=timeframe_seconds, holidays=holidays
    )
    n = int((flagged_frame["flags"].map(len) > 0).sum())
    return n, counts


def split_boundary(ts_sorted: list[int], virgin_fraction: float) -> int:
    """First VIRGIN index: the trailing ``virgin_fraction`` of rows are VIRGIN.

    The boundary bar (index ``split-1``) is the last TRAINING bar; VIRGIN starts
    at ``ts_sorted[split]``. At least one bar on each side.
    """
    n = len(ts_sorted)
    if n < 2:
        raise ValueError("need at least 2 bars to split TRAINING/VIRGIN")
    if not 0.0 < virgin_fraction < 1.0:
        raise ValueError("virgin_fraction must be in (0, 1)")
    n_virgin = max(1, round(n * virgin_fraction))
    return max(1, min(n - n_virgin, n - 1))


def _sorted_ts(bulk: BulkStore, clean_manifest: str) -> list[int]:
    table = bulk.read(clean_manifest)
    return sorted(int(x) for x in table.column("ts").to_pylist())


def designate_split(
    store: RecordStore,
    dataset: str,
    ts_sorted: list[int],
    virgin_fraction: float,
    manifest_refs: list[str],
) -> tuple[Record, Record]:
    """Designate disjoint TRAINING (leading) and VIRGIN (trailing) windows.

    Half-open intervals: TRAINING ``[first, boundary)`` (excludes the first
    VIRGIN bar), VIRGIN ``[boundary, last+1)`` (includes the last bar). They
    touch at the boundary but never overlap — contamination is impossible by
    construction.
    """
    split = split_boundary(ts_sorted, virgin_fraction)
    train_start, boundary, last = ts_sorted[0], ts_sorted[split], ts_sorted[-1]
    # Disjointness invariant (half-open [a,b) vs [b,c) never intersect).
    assert train_start < boundary <= last, "degenerate split"

    wl = WindowLedger(store)
    training = wl.designate(
        dataset, train_start, boundary, "TRAINING",
        producer="human:girish", parents=manifest_refs,
    )
    virgin = wl.designate(
        dataset, boundary, last + 1, "VIRGIN",
        producer="human:girish", parents=manifest_refs,
    )
    return training, virgin


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", required=True, help="the bigger XAUUSD H1 export CSV")
    ap.add_argument("--holidays", default="", help="comma-separated UTC dates (YYYY-MM-DD)")
    ap.add_argument("--virgin-fraction", type=float, default=DEFAULT_VIRGIN_FRACTION)
    a = ap.parse_args()
    holidays = {h.strip() for h in a.holidays.split(",") if h.strip()}

    store = RecordStore(JOURNAL)  # verifies chain on open

    prior = already_declared(store, DATASET_FULL)
    if prior is not None:
        raise SystemExit(
            f"already declared: window {prior.record_id} ({prior.payload['designation']}) "
            f"on {DATASET_FULL}; refusing to run twice"
        )

    # Dry pass: abort with nothing written if the export is not clean.
    n_flagged, counts = count_unexplained_flags(
        a.csv, TIMEFRAME_SECONDS, holidays, IVF_S2_COLUMN_MAP
    )
    if n_flagged:
        raise SystemExit(
            f"ABORT: {n_flagged} unexplained flag(s) {counts} — the export must ingest "
            f"with 0 flags before a VIRGIN declaration (check --holidays). Nothing written."
        )

    bulk = BulkStore(store, BULK_ROOT)
    res = ingest_mt5_csv(
        a.csv, DATASET_FULL, timeframe_seconds=TIMEFRAME_SECONDS,
        store=store, bulk_store=bulk, column_map=IVF_S2_COLUMN_MAP, holidays=holidays,
    )
    if res.verdict != "PASS" or res.rows_flagged != 0:
        raise SystemExit(f"ABORT: verdict={res.verdict} flagged={res.rows_flagged} — not clean")

    print(f"ingested {res.rows_total} rows as {DATASET_FULL}: clean={res.rows_clean} "
          f"flagged=0 verdict=PASS")
    print(f"ingest_report={res.report.record_id} (schema v{res.report.schema_version}) "
          f"manifests={res.manifest_refs}")

    ts_sorted = _sorted_ts(bulk, res.clean_manifest)
    split = split_boundary(ts_sorted, a.virgin_fraction)
    print(f"span [{ts_sorted[0]}, {ts_sorted[-1]}], {len(ts_sorted)} bars; "
          f"virgin_fraction={a.virgin_fraction} -> {len(ts_sorted) - split} trailing VIRGIN, "
          f"{split} leading TRAINING")
    print(f"boundary: last TRAINING ts={ts_sorted[split - 1]}, first VIRGIN ts={ts_sorted[split]}")

    entered = input(f"Type exactly '{CONFIRM_PHRASE}' to designate the VIRGIN reserve: ")
    if not is_confirmation(entered):
        raise SystemExit("not confirmed (phrase mismatch); no window designated")

    training, virgin = designate_split(
        store, DATASET_FULL, ts_sorted, a.virgin_fraction, res.manifest_refs
    )
    print(f"TRAINING window={training.record_id} "
          f"[{training.payload['ts_start']}, {training.payload['ts_end']})")
    print(f"VIRGIN   window={virgin.record_id} "
          f"[{virgin.payload['ts_start']}, {virgin.payload['ts_end']})")
    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()
