"""NP-S1 deliverable 4 — register (idempotent) + judge the H-007 PREDICTION
claim on the real xauusd_m5_vantage TRAINING window (NP-ADR-008 §5 v1.1).

The verdict is WHATEVER THE DATA SAYS. Only `neelprajna.liquidity_sweep.sweep`
events are trade signals — `setup_dsl.event` in the YAML documents this, but
`EventEngine.simulate` reads every row of whatever `events` frame it's given
(it does not filter by event_type itself), so this script filters explicitly
to sweep events, excluding POOL_FORMED events (which are not signals).

Idempotent + burn-safe: once the window is burned for this lineage, refuses to
re-run and reports the existing verdict instead — out-of-sample data spent once.

Run:  .venv/Scripts/python.exe scripts/judge_h007_prediction_s1.py
"""

from __future__ import annotations

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import BulkIntegrityError, WindowBurnedError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
CONFIG = "configs/hypotheses/h007_np_liquidity_sweep_v1_1_prediction.yaml"
DATASET = "xauusd_m5_vantage"
SWEEP_EVENT_TYPE = "neelprajna.liquidity_sweep.sweep"


def _manifest(store: RecordStore, dataset: str) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m
    raise SystemExit(f"no bulk_manifest for {dataset} — run scripts/ingest_h07_m5_vantage.py first")


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
    print(f"  family       : {c.get('family')}")
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

    # 1. Register the prediction hypothesis idempotently (already registered in
    #    SNP-S1-03; this call is a no-op that returns the same record).
    registry = HypothesisRegistry(store)
    available = cost_models.available()
    hyp = registry.register(CONFIG, cost_model_refs=available, producer="human:girish")
    print(f"H-007 prediction hypothesis record = {hyp.record_id}")
    print(f"  lineage={hyp.payload['lineage']} scope={hyp.payload['scope']} "
          f"family={hyp.payload.get('family')} instruments={hyp.payload['instrument_refs']}")

    # 2. If already judged/burned, refuse re-run and report the existing verdict.
    existing = _existing_verdict(store, hyp.record_id)
    if existing is not None:
        print("already judged — out-of-sample data is spent once; refusing to re-run.")
        _print_verdict(store, existing)
        return

    # 3. Load the real M5 bars (hash-verified) + detect events, filtered to SWEEP only.
    try:
        bars_table = bulk.read(_manifest(store, DATASET).record_id)
    except BulkIntegrityError as e:
        raise SystemExit(
            f"{e}\nThe M5 parquet is missing or corrupt. Rebuild it:\n"
            "  .venv/Scripts/python.exe scripts/ingest_h07_m5_vantage.py"
        ) from e
    bars = bars_table.to_pandas()

    detector = LiquiditySweepDetector()
    all_events = detector.detect(bars_table).to_pandas()
    events = all_events[all_events["event_type"] == SWEEP_EVENT_TYPE].reset_index(drop=True)
    n_pool_formed = int((all_events["event_type"] != SWEEP_EVENT_TYPE).sum())
    print(
        f"loaded {len(bars)} M5 bars; detector emitted {len(all_events)} events total "
        f"({n_pool_formed} POOL_FORMED excluded, {len(events)} SWEEP trade signals)"
    )

    # 4. Run the battery (engine + cost model injected; battery windows + folds).
    cost_model = cost_models.load_cost_model("xauusd_retail_h07")
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


if __name__ == "__main__":
    judge()
