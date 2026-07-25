"""ARCH-006 §4 — register + judge H-001 on the real TRAINING window.

The Owner-facing end-to-end run: register the pre-registered hypothesis H-001
(configs/hypotheses/h001_fvg_follow_through.yaml) idempotently, then run the full
EvidenceBattery over the xauusd_h1_full TRAINING window and print every record id
and the tri-state outcome, plainly. The verdict is WHATEVER THE DATA SAYS — the
machinery, not the outcome, is under test (ARCH-006 pre-registered expectation:
FAIL or INSUFFICIENT is the likely, healthy result of a naive FVG follow-through
with real costs).

Idempotent + burn-safe: once H-001's window is burned for its lineage, this
refuses to re-run and reports the existing verdict instead (out-of-sample data is
spent exactly once).

The full-dataset parquet is gitignored (the journal manifest is the root of
trust), so on a fresh checkout rebuild it first:

    uv run python scripts/judge_h001.py --rebuild-bulk

That reconstructs datastore/bulk/xauusd_h1_full/ from the source CSV using the
adapter's deterministic transform and hash-verifies it against the existing
manifest (appends nothing). Then run the judge:

    uv run python scripts/judge_h001.py

If the source CSV is missing, place the Owner's XAUUSD H1 2024 export at
ivf/mt5/XAUUSD_H1_2024_FULL.csv and re-run --rebuild-bulk.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import BulkIntegrityError, WindowBurnedError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import (
    QUARANTINE_SUFFIX,
    _to_store_table,
    build_bar_frame,
    flag_anomalies,
)
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP, to_canonical
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
CONFIG = "configs/hypotheses/h001_fvg_follow_through.yaml"
DATASET_FULL = "xauusd_h1_full"
FULL_CSV = "ivf/mt5/XAUUSD_H1_2024_FULL.csv"
TIMEFRAME_SECONDS = 3600
# The 2024 US market holidays whose mid-week closes appear as gaps in this export
# (declared so the ingest is clean; the same set the VIRGIN declaration used).
FULL_HOLIDAYS = frozenset(
    {
        "2024-01-15", "2024-02-19", "2024-05-27", "2024-06-19",
        "2024-07-04", "2024-09-02", "2024-11-28", "2024-12-25",
    }
)


def _full_manifest(store: RecordStore) -> Record:
    """The clean-partition bulk_manifest for xauusd_h1_full (root of trust)."""
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == DATASET_FULL:
            return m
    raise SystemExit(
        f"no bulk_manifest for {DATASET_FULL} — the full dataset was never ingested; "
        "run scripts/declare_virgin_s3.py (Owner) first"
    )


def rebuild_bulk() -> None:
    """Re-create the gitignored full-dataset parquet from the CSV; hash-verify."""
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)
    csv_path = Path(FULL_CSV)
    if not csv_path.exists():
        raise SystemExit(
            f"source CSV {FULL_CSV} not found — place the Owner's XAUUSD H1 2024 export "
            f"there and re-run:\n  uv run python scripts/judge_h001.py --rebuild-bulk"
        )
    raw = pd.read_csv(FULL_CSV)
    frame = build_bar_frame(to_canonical(raw, IVF_S2_COLUMN_MAP), TIMEFRAME_SECONDS)
    flagged, _ = flag_anomalies(frame, timeframe_seconds=TIMEFRAME_SECONDS, holidays=FULL_HOLIDAYS)
    is_clean = flagged["flags"].map(len) == 0
    partitions = {
        DATASET_FULL: (flagged[is_clean], False),
        f"{DATASET_FULL}{QUARANTINE_SUFFIX}": (flagged[~is_clean], True),
    }
    rebuilt = 0
    try:
        for m in store.query(record_type="bulk_manifest"):
            ds = m.payload["dataset"]
            if ds not in partitions:
                continue
            df, with_flags = partitions[ds]
            if df.empty:
                continue
            table = _to_store_table(df, with_flags=with_flags)
            path = Path(BULK_ROOT) / m.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(table, path)
            bulk.read(m.record_id)  # hash-verify vs the existing manifest, or raise
            print(f"rebuilt + hash-verified {m.record_id} ({ds}, {table.num_rows} rows)")
            rebuilt += 1
    except BulkIntegrityError as e:
        raise SystemExit(
            f"rebuild hash mismatch: {e}\nThe source CSV or holiday set does not match "
            "the ingest that produced the manifest."
        ) from e
    assert len(store) == n_before, "rebuild must not append records"
    if not rebuilt:
        print(f"nothing to rebuild for {DATASET_FULL}")


def _existing_verdict(store: RecordStore, hypothesis_ref: str) -> Record | None:
    for v in store.query(record_type="verdict"):
        if v.payload.get("hypothesis_ref") == hypothesis_ref:
            return v
    return None


def _print_verdict(store: RecordStore, verdict: Record) -> None:
    p = verdict.payload
    burn = next(
        (b for b in store.query(record_type="window_burn")
         if b.payload["consumed_by"] == verdict.record_id),
        None,
    )
    print("-" * 68)
    print(f"  hypothesis   : {p['hypothesis_ref']}")
    print(f"  window       : {p['window_ref']}")
    print(f"  VERDICT      : {p['verdict']}   (n_trades={p['n_trades']}, "
          f"n_dropped_tail={p['n_dropped_tail']})")
    print(f"  net total    : {p['net']['total']}   net mean/trade: {p['net']['mean']}")
    print(f"  gross total  : {p['gross']['total']}")
    stat = p["statistics"]["t_one_sided"]
    print(f"  one-sided t  : stat={stat['stat']} p={stat['p']} "
          f"ci=[{stat['ci_low']}, {stat['ci_high']}]")
    c = p["corrections"]
    print(f"  correction   : {c['method']} base_alpha={c['base_alpha']} "
          f"N_trials={c['family_m']} -> effective_alpha={c['effective_alpha']}")
    print(f"  thresholds   : min_n={p['thresholds']['min_n']} "
          f"base_alpha={p['thresholds']['base_alpha']}")
    print("  per-fold     : "
          + "; ".join(f"f{f['index']}(n={f['n_trades']}, mean_net={f['mean_net']})"
                      for f in p["folds"]))
    print(f"  seed         : {p['seed']}   selftest_seed: {p['selftest_seed']}")
    print(f"  engine       : {p['engine_version']}")
    print(f"  trades_manifest: {p['trades_manifest'] or '(none — 0 trades)'}")
    print(f"  verdict record : {verdict.record_id}")
    if burn is not None:
        print(f"  window_burn    : {burn.record_id} (lineage {burn.payload['lineage']})")
    print("-" * 68)


def judge() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    bulk = BulkStore(store, BULK_ROOT)

    # 1. Register H-001 idempotently.
    registry = HypothesisRegistry(store)
    available = cost_models.available()
    hyp = registry.register(CONFIG, cost_model_refs=available, producer="human:girish")
    print(f"H-001 hypothesis record = {hyp.record_id}")
    print(f"  lineage={hyp.payload['lineage']} scope={hyp.payload['scope']} "
          f"instruments={hyp.payload['instrument_refs']}")

    # 2. If already judged/burned, refuse re-run and report the existing verdict.
    existing = _existing_verdict(store, hyp.record_id)
    if existing is not None:
        print("already judged — out-of-sample data is spent once; refusing to re-run.")
        _print_verdict(store, existing)
        return

    # 3. Load the real full-dataset bars (hash-verified) + detect FVG events.
    try:
        bars_table = bulk.read(_full_manifest(store).record_id)
    except BulkIntegrityError as e:
        raise SystemExit(
            f"{e}\nThe full-dataset parquet is missing or corrupt. Rebuild it:\n"
            "  uv run python scripts/judge_h001.py --rebuild-bulk"
        ) from e
    bars = bars_table.to_pandas()
    events = SMCFVGDetector().detect(bars_table).to_pandas()
    print(f"loaded {len(bars)} full-dataset bars; smc.fvg detected {len(events)} events")

    # 4. Run the battery (engine + cost model injected; battery windows + folds).
    cost_model = cost_models.load_cost_model("xauusd_retail_median")
    try:
        verdict = EvidenceBattery(store, bulk).run(
            hyp.record_id,
            simulator=EventEngine(),
            cost_model=cost_model,
            bars=bars,
            events=events,
        )
    except WindowBurnedError as e:
        print(f"window already burned for this lineage — refusing re-run: {e}")
        prior = _existing_verdict(store, hyp.record_id)
        if prior is not None:
            _print_verdict(store, prior)
        return

    print("\nJUDGED — verdict + window_burn appended to the REAL journal:")
    _print_verdict(store, verdict)
    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild-bulk", action="store_true",
        help="rebuild the gitignored full-dataset parquet from the CSV + hash-verify (no writes)",
    )
    a = ap.parse_args()
    if a.rebuild_bulk:
        rebuild_bulk()
        return
    judge()


if __name__ == "__main__":
    main()
