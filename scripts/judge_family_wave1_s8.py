"""ARCH-008 §3 — register + judge Family Wave 1 (H-002, H-003) on the real journal.

Two pre-registered hypotheses, each judged on the TRAINING window (a FRESH lineage,
so the window H-001 burned for ITS lineage is available), each accompanied by its
placebo run (G-3, ARCH-008 §1):

* H-002 h002_fvg_intraweek_follow_through — H-001's setup MINUS weekend-born FVGs
  (the scan's OWN spans_weekend rule, inlined as the setup filter). family
  xauusd_h1/smc.fvg (502 trials -> effective alpha ~1e-4). Placebo null:
  direction_permutation (DEVQ-018 — a directional event claim).
* H-003 h003_dow_monday_drift — enter LONG at next-open after each Monday's
  `seasonality.dow.mon` marker, hold 22 bars (DEVQ-019). FRESH family
  xauusd_h1/seasonality.calendar (N_trials ~0 -> the zero-deflation boundary).
  Placebo null: entry_time_shuffle (DEVQ-018 — a fixed-direction timing claim).

Outcomes are WHATEVER THE DATA SAYS — all three tri-states are acceptance-valid
(ARCH-008 §Acceptance). Idempotent + burn-safe: a hypothesis already judged is
reported, never re-run (out-of-sample data is spent once).

    F:/QRF/.venv/Scripts/python.exe scripts/judge_family_wave1_s8.py
    F:/QRF/.venv/Scripts/python.exe scripts/judge_family_wave1_s8.py --preview   # read-only

Rebuild the gitignored full parquet first if needed (see scripts/judge_h001.py
--rebuild-bulk); this script reuses the same xauusd_h1_full manifest.
"""

from __future__ import annotations

import argparse

import pandas as pd

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.battery.placebo import DIRECTION_PERMUTATION, ENTRY_TIME_SHUFFLE, PlaceboBattery
from qrf.kernel.belief.belief import BeliefLayer
from qrf.kernel.errors import BulkIntegrityError, WindowBurnedError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.seasonality.detector import SeasonalityDetector
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.observatory.scans import _infer_timeframe_seconds, _spans_weekend
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET_FULL = "xauusd_h1_full"
PLACEBO_SEED = 20260725
PLACEBO_N_RUNS = 20

H002_CONFIG = "configs/hypotheses/h002_fvg_intraweek_follow_through.yaml"
H003_CONFIG = "configs/hypotheses/h003_dow_monday_drift.yaml"


def _full_manifest(store: RecordStore) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == DATASET_FULL:
            return m
    raise SystemExit(f"no bulk_manifest for {DATASET_FULL}; run judge_h001.py --rebuild-bulk")


def _window_ref_of(store: RecordStore, config_path: str) -> str:
    return HypothesisRegistry.load_config(config_path)["window"]


def _window_bars(bars: pd.DataFrame, window: Record) -> pd.DataFrame:
    lo, hi = window.payload["ts_start"], window.payload["ts_end"]
    return bars[(bars["ts"] >= lo) & (bars["ts"] < hi)].sort_values("ts").reset_index(drop=True)


def _intra_week_events(bars: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    """H-002 setup filter: drop weekend-born FVGs using the SCAN'S OWN spans_weekend.

    An FVG's 3 forming bars are (k-2, k-1, k) where k is its knowability bar (its ts).
    It is weekend-born iff either forming gap crosses a weekend — the exact rule
    qrf.trading.observatory.scans applies (single source of truth for the IVF).
    """
    b = bars.sort_values("ts").reset_index(drop=True)
    ts_list = b["ts"].astype("int64").tolist()
    index_of = {int(t): i for i, t in enumerate(ts_list)}
    tf = _infer_timeframe_seconds(ts_list)
    keep = []
    for ev in events.itertuples(index=False):
        k = index_of.get(int(ev.ts))
        weekend = bool(
            k is not None
            and k >= 2
            and (
                _spans_weekend(ts_list[k - 2], ts_list[k - 1], tf)
                or _spans_weekend(ts_list[k - 1], ts_list[k], tf)
            )
        )
        keep.append(not weekend)
    return events[pd.Series(keep, index=events.index)].reset_index(drop=True)


def _monday_long_events(events: pd.DataFrame) -> pd.DataFrame:
    """H-003 setup: the `seasonality.dow.mon` markers lifted to LONG entries."""
    mon = events[events["event_type"] == "seasonality.dow.mon"].copy()
    mon["direction"] = 1
    mon["strength"] = 1.0
    return mon.reset_index(drop=True)


def _existing_verdict(store: RecordStore, hypothesis_ref: str) -> Record | None:
    for v in store.query(record_type="verdict"):
        if v.payload.get("hypothesis_ref") == hypothesis_ref:
            return v
    return None


def _print_verdict(store: RecordStore, verdict: Record) -> None:
    p = verdict.payload
    c = p["corrections"]
    print("-" * 70)
    print(f"  hypothesis   : {p['hypothesis_ref']}")
    print(f"  VERDICT      : {p['verdict']}   (n_trades={p['n_trades']}, "
          f"n_dropped_tail={p['n_dropped_tail']})")
    print(f"  net mean/tr  : {p['net']['mean']}   net total: {p['net']['total']}")
    stat = p["statistics"]["t_one_sided"]
    print(f"  one-sided t  : stat={stat['stat']} p={stat['p']}")
    # DEVQ-015: every judge prints family / N_trials / effective_alpha.
    print(f"  family       : {c.get('family', '(none)')}")
    print(f"  correction   : {c['method']} N_trials={c['family_m']} "
          f"base_alpha={c['base_alpha']} -> effective_alpha={c['effective_alpha']}")
    print(f"  verdict rec  : {verdict.record_id}")
    print("-" * 70)


def judge_one(
    store: RecordStore,
    bulk: BulkStore,
    *,
    config_path: str,
    events: pd.DataFrame,
    bars_window: pd.DataFrame,
    placebo_method: str,
    preview: bool,
) -> None:
    available = cost_models.available()
    registry = HypothesisRegistry(store)

    if preview:
        # Read-only: prove the config resolves + the window/tri-state are sane,
        # WITHOUT sealing a hypothesis id or writing a verdict.
        payload, ver, _window_refs = registry._resolved_payload(
            HypothesisRegistry.load_config(config_path), available
        )
        print(f"[preview] {config_path}: resolves to schema v{ver}, "
              f"lineage={payload['lineage']}, family={payload['family']}, "
              f"setup events={len(events)}")
        return

    hyp = registry.register(config_path, cost_model_refs=available, producer="human:girish")
    print(f"\n=== {hyp.payload['lineage']} — hypothesis {hyp.record_id} ===")
    print(f"  family={hyp.payload['family']} setup events (post-filter)={len(events)} "
          f"ancestry={hyp.payload.get('observatory_ancestry', [])}")

    existing = _existing_verdict(store, hyp.record_id)
    if existing is not None:
        print("  already judged — refusing re-run; reporting existing verdict.")
        _print_verdict(store, existing)
        return

    cost_model = cost_models.load_cost_model(hyp.payload["cost_model_ref"])

    # Placebo FIRST (it burns nothing); accompanies the verdict (ARCH-008 §1).
    placebo = PlaceboBattery(store, bulk).run(
        hyp.record_id, simulator=EventEngine(), cost_model=cost_model,
        bars=bars_window, events=events, method=placebo_method,
        base_seed=PLACEBO_SEED, n_runs=PLACEBO_N_RUNS,
    )
    print(f"  placebo_run  : {placebo.record_id} method={placebo.payload['method']} "
          f"n_runs={placebo.payload['n_runs']} n_pass={placebo.payload['n_pass']}")

    try:
        verdict = EvidenceBattery(store, bulk).run(
            hyp.record_id, simulator=EventEngine(), cost_model=cost_model,
            bars=bars_window, events=events,
        )
    except WindowBurnedError as e:
        print(f"  window already burned for this lineage — refusing: {e}")
        return
    _print_verdict(store, verdict)

    # Fold the verdict into the belief chain (arrow-8: verdict-only evidence).
    belief = BeliefLayer(store).update(
        verdict.record_id, claim=hyp.payload["thesis"], family=hyp.payload["family"]
    )
    print(f"  belief       : {belief.record_id} stance={belief.payload['stance']} "
          f"strength={belief.payload['strength']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preview", action="store_true",
                    help="resolve configs + count events only; no verdict/burn writes")
    args = ap.parse_args()

    store = RecordStore(JOURNAL)  # verifies chain on open
    bulk = BulkStore(store, BULK_ROOT)

    try:
        bars_table = bulk.read(_full_manifest(store).record_id)
    except BulkIntegrityError as e:
        raise SystemExit(
            f"{e}\nThe full-dataset parquet is missing/corrupt. Rebuild:\n"
            "  F:/QRF/.venv/Scripts/python.exe scripts/judge_h001.py --rebuild-bulk"
        ) from e
    bars_full = bars_table.to_pandas()

    # Detect on the FULL bars (same as H-001), then window-slice for judging so the
    # placebo's timing shuffle samples within TRAINING and VIRGIN is never touched.
    window = store.get(_window_ref_of(store, H002_CONFIG))
    bars_window = _window_bars(bars_full, window)

    fvg_events = SMCFVGDetector().detect(bars_table).to_pandas()
    seasonality_events = SeasonalityDetector().detect(bars_table).to_pandas()
    h002_events = _intra_week_events(bars_full, fvg_events)
    h003_events = _monday_long_events(seasonality_events)
    print(f"detected: FVG={len(fvg_events)} (intra-week {len(h002_events)}), "
          f"Monday markers={len(h003_events)}; window bars={len(bars_window)}")

    judge_one(store, bulk, config_path=H002_CONFIG, events=h002_events,
              bars_window=bars_window, placebo_method=DIRECTION_PERMUTATION, preview=args.preview)
    judge_one(store, bulk, config_path=H003_CONFIG, events=h003_events,
              bars_window=bars_window, placebo_method=ENTRY_TIME_SHUFFLE, preview=args.preview)

    report = store.verify()
    print(f"\njournal verify ok={report.ok} n_records={report.n_records} "
          f"head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()
