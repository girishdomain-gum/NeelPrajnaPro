"""ARCH-007 §2 — run the observatory for real; register the two pre-declared questions.

The first REAL observatory output. Over the xauusd_h1_full TRAINING window (never
VIRGIN), detect FVG events and run the two pre-declared descriptive scans, each
recording an ``anomaly_scan`` (which bumps the FVG family's trial ledger — looking
is a burden, DEVQ-015) and one ``question`` parented to it:

(a) weekend-spanning FVGs (DEVQ-010 addendum) — do FVGs whose 3 forming bars span
    the weekend hole behave differently from intra-week ones?
(b) fold-4 deterioration — does the FVG family's descriptive follow-through drift
    across 2024, the shape H-001's fold means (-0.03, -0.87, -0.08, -1.25) showed?

Both questions cite H-001's verdict + trades manifest as evidence (they describe
the same data the first verdict judged; they do not re-litigate it). Descriptive
only: no thresholds, no PASS/FAIL, no verdict language.

Idempotent + append-only-safe: a scan/question/slice already in the journal is
reused, never duplicated, so this is safe to re-run.

The full-dataset parquet is gitignored (the journal manifest is the root of
trust). On a fresh checkout rebuild it first:

    uv run python scripts/judge_h001.py --rebuild-bulk

then run:

    uv run python scripts/observe_s7.py
"""

from __future__ import annotations

import pyarrow as pa
import pyarrow.compute as pc

from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.observatory import Observatory
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.observatory import net_drift_scan, weekend_partition_scan

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"

DATASET_FULL = "xauusd_h1_full"
FAMILY = "xauusd_h1/smc.fvg"
TRAINING_WINDOW = "01KYB4SSC96SSS8RA7D1NMTPEX"

# The first verdict set (GO-S6) the two questions cite as evidence.
H001_VERDICT = "01KYC7Y2KWYGXH73V1R9P57MYA"
H001_TRADES_MANIFEST = "01KYC7Y2JQY15BVJP146FX1QGF"

# Fixed scan seeds (determinism: same seed -> identical findings summary).
SEED_WEEKEND = 20260725
SEED_DRIFT = 20260726

SLICE_DATASET = "xauusd_h1_training_smc_fvg_scan"
METHOD_WEEKEND = "fvg.weekend_partition.followthrough@h4"
METHOD_DRIFT = "fvg.net_followthrough_drift.byquarter@h4"


def _full_manifest(store: RecordStore) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == DATASET_FULL:
            return m
    raise SystemExit(f"no bulk_manifest for {DATASET_FULL}; run declare_virgin_s3.py first")


def _window(store: RecordStore, window_ref: str) -> Record:
    return store.get(window_ref)


def _slice_to_window(table: pa.Table, ts_start: int, ts_end: int) -> pa.Table:
    ts = table.column("ts")
    mask = pc.and_(pc.greater_equal(ts, pa.scalar(ts_start)), pc.less(ts, pa.scalar(ts_end)))
    return table.filter(mask)


def _existing_slice(store: RecordStore, dataset: str) -> str | None:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m.record_id
    return None


def _existing_scan(store: RecordStore, method: str, seed: int, window_ref: str) -> Record | None:
    for s in store.query(record_type="anomaly_scan"):
        p = s.payload
        if p["method"] == method and p["seed"] == seed and p["window_ref"] == window_ref:
            return s
    return None


def _existing_question(store: RecordStore, scan_ref: str) -> Record | None:
    return next(iter(store.query(record_type="question", parent=scan_ref)), None)


def _annotated_table(annotated) -> pa.Table:
    """The per-event scan slice as an int64-``ts`` pyarrow table (for BulkStore)."""
    table = pa.Table.from_pandas(annotated, preserve_index=False)
    ts_i64 = table.column("ts").cast(pa.int64())
    return table.set_column(table.schema.get_field_index("ts"), "ts", ts_i64)


def main() -> None:
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    obs = Observatory(store)

    full = _full_manifest(store)
    win = _window(store, TRAINING_WINDOW)
    ts_start, ts_end = win.payload["ts_start"], win.payload["ts_end"]

    try:
        full_bars = bulk.read(full.record_id)
    except BulkIntegrityError as e:
        raise SystemExit(
            f"{e}\nThe full-dataset parquet is missing or corrupt. Rebuild it:\n"
            "  uv run python scripts/judge_h001.py --rebuild-bulk"
        ) from e

    train_bars_tbl = _slice_to_window(full_bars, ts_start, ts_end)
    events_tbl = SMCFVGDetector().detect(train_bars_tbl)
    bars = train_bars_tbl.to_pandas()
    events = events_tbl.to_pandas()
    print(f"TRAINING window {TRAINING_WINDOW}: {len(bars)} bars; "
          f"smc.fvg detected {len(events)} events")

    # Descriptive scans (no costs, no verdict language).
    fnd_weekend, annotated = weekend_partition_scan(bars, events, seed=SEED_WEEKEND)
    fnd_drift, _ = net_drift_scan(bars, events, seed=SEED_DRIFT)

    # One data slice (the annotated FVG events with the weekend flag + follow-through)
    # anchors both questions and gives the visual HC concrete slices to chart.
    slice_ref = _existing_slice(store, SLICE_DATASET)
    if slice_ref is None:
        slice_ref = bulk.write(
            SLICE_DATASET, _annotated_table(annotated), producer="observatory",
            parents=[TRAINING_WINDOW, full.record_id],
        ).record_id
        print(f"wrote FVG scan slice manifest = {slice_ref} ({len(annotated)} events)")
    else:
        print(f"FVG scan slice manifest exists = {slice_ref}")

    # ---- scan (a): weekend-spanning FVGs ----
    pw = fnd_weekend["partitions"]
    w, iw = pw["weekend_spanning"], pw["intra_week"]
    obs_a = (
        f"Of {fnd_weekend['n_events']} FVG events on the xauusd_h1 TRAINING window, "
        f"{w['n']} span the weekend hole (their 3 forming bars straddle a Sat/Sun) and "
        f"{iw['n']} are intra-week. Descriptive H+{fnd_weekend['horizon_bars']} "
        f"follow-through mean (direction x price move, NO costs): weekend-spanning="
        f"{w['mean']}, intra-week={iw['mean']}. DEVQ-010's addendum flagged that both "
        "FVG implementations treat row adjacency as bar adjacency across the 50-hour "
        "weekend hole; the two disputed patterns both spanned Fri->Sun."
    )
    cand_a = (
        "Sketch (NOT a pre-registration): weekend-spanning FVGs may be a different "
        "tradable object from intra-week ones. A future hypothesis could restrict the "
        "FVG setup to intra-week patterns, or test weekend-spanning ones as a separate "
        "family, rather than pooling them as H-001 did."
    )
    scan_a, q_a = _ensure_scan_question(
        store, obs, method=METHOD_WEEKEND, seed=SEED_WEEKEND, findings=fnd_weekend,
        manifest_refs=[full.record_id], observation=obs_a, candidate=cand_a, slice_ref=slice_ref,
    )

    # ---- scan (b): fold-4 deterioration / net drift ----
    means = {lbl: b["mean"] for lbl, b in fnd_drift["buckets_by_quarter"].items()}
    obs_b = (
        "H-001's four walk-forward fold means worsened roughly monotonically "
        "(-0.03, -0.87, -0.08, -1.25) — an ENGINE net outcome, with costs. Scanning "
        f"the FVG family's descriptive H+{fnd_drift['horizon_bars']} follow-through "
        "(direction x price move, NO costs) by calendar quarter across the 2024 "
        f"TRAINING window gives means {means} (last-minus-first drift "
        f"{fnd_drift['drift_last_minus_first_mean']}). The descriptive picture is "
        "NOT monotone the way the cost-laden engine net was — so H-001's fold "
        "deterioration may be driven as much by costs / trade-mix as by a decay in "
        "the raw follow-through itself."
    )
    cand_b = (
        "Sketch (NOT a pre-registration): the FVG follow-through may be "
        "non-stationary across 2024, and the deterioration H-001 showed may be a "
        "cost/regime effect rather than a raw-signal decay. A future hypothesis "
        "could condition on time/regime, or test earlier vs later sub-windows "
        "separately, rather than assume a stationary edge over the whole window."
    )
    scan_b, q_b = _ensure_scan_question(
        store, obs, method=METHOD_DRIFT, seed=SEED_DRIFT, findings=fnd_drift,
        manifest_refs=[full.record_id], observation=obs_b, candidate=cand_b, slice_ref=slice_ref,
    )

    report = store.verify()
    print("\nObservatory S7 — records on the REAL journal:")
    print(f"  scan (a) weekend  = {scan_a.record_id}  ->  question = {q_a.record_id}")
    print(f"  scan (b) drift    = {scan_b.record_id}  ->  question = {q_b.record_id}")
    print(f"  FVG scan slice    = {slice_ref}")
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


def _ensure_scan_question(
    store: RecordStore, obs: Observatory, *, method: str, seed: int, findings: dict,
    manifest_refs: list[str], observation: str, candidate: str, slice_ref: str,
) -> tuple[Record, Record]:
    """Append (or reuse) one scan + its question idempotently."""
    scan = _existing_scan(store, method, seed, TRAINING_WINDOW)
    if scan is None:
        scan = obs.scan(
            family=FAMILY, window_ref=TRAINING_WINDOW, manifest_refs=manifest_refs,
            method=method, seed=seed, findings=findings, n_searched=1,
        )
        print(f"appended anomaly_scan ({method}) = {scan.record_id} (+ family trial bump)")
    else:
        print(f"anomaly_scan ({method}) exists = {scan.record_id}")
    q = _existing_question(store, scan.record_id)
    if q is None:
        q = obs.pose_question(
            scan_ref=scan.record_id, observation=observation, data_slice_refs=[slice_ref],
            candidate_hypothesis=candidate, evidence_refs=[H001_VERDICT, H001_TRADES_MANIFEST],
            origin="observatory",
        )
        print(f"appended question = {q.record_id}")
    else:
        print(f"question exists = {q.record_id}")
    return scan, q


if __name__ == "__main__":
    main()
