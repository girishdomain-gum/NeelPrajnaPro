"""ARCH-009 §4.3 — register + judge H-004 (Monday drift v2), placebo-first.

H-004 h004_dow_monday_drift_v2 is the DEVQ-019 successor to H-003, judged on the
MULTI-WINDOW union of the 2024 AND 2025 training spans (schema v3, DEVQ-022 Option A)
with a CALENDAR exit (exit at the open of the last bar sharing the entry's
server-Monday). Placebo FIRST (entry_time_shuffle, sealed in the YAML per ARCH-009
§2), then the verdict — all three tri-states acceptance-valid; a PASS claims only
"Monday beats RANDOM TIMING" (OBS-1), and even a clean PASS promotes NOTHING (no
second lens yet — that gate is DEVQ-023-blocked).

Bars: the union is fed from ``xauusd_h1_primary_full`` (which spans both training
years); its 2024-training slice is ASSERTED byte-identical to the 2024-training
window's own manifest (``xauusd_h1_full``), satisfying the reserve-by-market-time
doctrine (bars per window == that window's manifest). The two VIRGIN reserves are
never in the union — nothing computes on them.

    F:/QRF/.venv/Scripts/python.exe scripts/judge_h004_s9.py
    F:/QRF/.venv/Scripts/python.exe scripts/judge_h004_s9.py --preview   # read-only

Idempotent + burn-safe: an H-004 already judged is reported, never re-run (each
training span is spent once for this lineage). Rebuild the parquets first if absent:
    F:/QRF/.venv/Scripts/python.exe scripts/ingest_lens_feeds_s9.py --rebuild-bulk
    F:/QRF/.venv/Scripts/python.exe scripts/judge_h001.py --rebuild-bulk
"""

from __future__ import annotations

import argparse

import pandas as pd

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.battery.placebo import ENTRY_TIME_SHUFFLE, PlaceboBattery
from qrf.kernel.belief.belief import BeliefLayer
from qrf.kernel.errors import BulkIntegrityError, WindowBurnedError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.seasonality.detector import SeasonalityDetector
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET_PRIMARY = "xauusd_h1_primary_full"
DATASET_2024 = "xauusd_h1_full"
H004_CONFIG = "configs/hypotheses/h004_dow_monday_drift_v2.yaml"
PLACEBO_SEED = 20260726
PLACEBO_N_RUNS = 20

_OHLC = ("open", "high", "low", "close")


def _manifest(store: RecordStore, dataset: str) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m
    raise SystemExit(
        f"no bulk_manifest for {dataset!r}; rebuild the parquets (see this script's docstring)"
    )


def _window_slice(bars: pd.DataFrame, window: Record) -> pd.DataFrame:
    lo, hi = window.payload["ts_start"], window.payload["ts_end"]
    return bars[(bars["ts"] >= lo) & (bars["ts"] < hi)].sort_values("ts").reset_index(drop=True)


def _monday_long_events(events: pd.DataFrame) -> pd.DataFrame:
    """The ``seasonality.dow.mon`` markers lifted to LONG entries (H-003/H-004 setup)."""
    mon = events[events["event_type"] == "seasonality.dow.mon"].copy()
    mon["direction"] = 1
    mon["strength"] = 1.0
    return mon.reset_index(drop=True)


def _assert_byte_identical(a: pd.DataFrame, b: pd.DataFrame, msg: str) -> None:
    """The reserve-by-market-time doctrine: window bars == the window's own manifest."""
    if len(a) != len(b):
        raise SystemExit(f"{msg}: row count differs ({len(a)} vs {len(b)})")
    ax = a.sort_values("ts").reset_index(drop=True)
    bx = b.sort_values("ts").reset_index(drop=True)
    if not (ax["ts"].to_numpy() == bx["ts"].to_numpy()).all():
        raise SystemExit(f"{msg}: timestamps differ")
    for c in _OHLC:
        if (ax[c].to_numpy() != bx[c].to_numpy()).any():
            raise SystemExit(f"{msg}: {c} differs — NOT byte-identical to the window manifest")


def _existing_verdict(store: RecordStore, hypothesis_ref: str) -> Record | None:
    for v in store.query(record_type="verdict"):
        if v.payload.get("hypothesis_ref") == hypothesis_ref:
            return v
    return None


def _print_verdict(verdict: Record) -> None:
    p = verdict.payload
    c = p["corrections"]
    print("-" * 72)
    print(f"  hypothesis   : {p['hypothesis_ref']}")
    print(f"  windows      : {p.get('window_refs', [p['window_ref']])}")
    print(f"  VERDICT      : {p['verdict']}   (n_trades={p['n_trades']}, "
          f"n_dropped_tail={p['n_dropped_tail']}, n_dropped_hole={p.get('n_dropped_hole', 0)})")
    print(f"  net mean/tr  : {p['net']['mean']}   net total: {p['net']['total']}")
    stat = p["statistics"]["t_one_sided"]
    print(f"  one-sided t  : stat={stat['stat']} p={stat['p']}")
    print(f"  family       : {c.get('family', '(none)')}")
    print(f"  correction   : {c['method']} N_trials={c['family_m']} "
          f"base_alpha={c['base_alpha']} -> effective_alpha={c['effective_alpha']}")
    print(f"  verdict rec  : {verdict.record_id}")
    print("-" * 72)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preview", action="store_true",
                    help="resolve config + count events only; no verdict/burn writes")
    args = ap.parse_args()

    store = RecordStore(JOURNAL)  # verifies chain on open
    bulk = BulkStore(store, BULK_ROOT)
    available = cost_models.available()
    registry = HypothesisRegistry(store)

    # Load bars: primary_full (spans both training years) + the 2024 window manifest.
    try:
        primary_tbl = bulk.read(_manifest(store, DATASET_PRIMARY).record_id)
        bars_2024_mani = bulk.read(_manifest(store, DATASET_2024).record_id).to_pandas()
    except BulkIntegrityError as e:
        raise SystemExit(f"{e}\nRebuild the parquets (see this script's docstring).") from e
    primary = primary_tbl.to_pandas()

    cfg = HypothesisRegistry.load_config(H004_CONFIG)
    w2024 = store.get(cfg["window_refs"][0])
    w2025 = store.get(cfg["window_refs"][1])

    # Union bars = each window's slice of primary_full (reserves excluded by the
    # window boundaries); assert the 2024 slice is byte-identical to its own manifest.
    bars_a = _window_slice(primary, w2024)
    bars_b = _window_slice(primary, w2025)
    ref_a = _window_slice(bars_2024_mani, w2024)
    _assert_byte_identical(
        bars_a, ref_a, "2024-training slice of primary_full vs xauusd_h1_full manifest"
    )
    bars_union = pd.concat([bars_a, bars_b], ignore_index=True)

    # Detect Monday markers on the CONTINUOUS primary feed, then keep only those in
    # the union (a marker's day-change is computed on the real series, not the gap).
    seasonality = SeasonalityDetector().detect(primary_tbl).to_pandas()
    mondays = _monday_long_events(seasonality)
    in_union = (
        ((mondays["ts"] >= w2024.payload["ts_start"]) & (mondays["ts"] < w2024.payload["ts_end"]))
        | ((mondays["ts"] >= w2025.payload["ts_start"]) & (mondays["ts"] < w2025.payload["ts_end"]))
    )
    events = mondays[in_union].reset_index(drop=True)
    print(f"union bars={len(bars_union)} (2024={len(bars_a)} + 2025={len(bars_b)}); "
          f"Monday markers in union={len(events)}")

    if args.preview:
        payload, ver, wrefs = registry._resolved_payload(cfg, available)
        print(f"[preview] {H004_CONFIG}: resolves to schema v{ver}, lineage={payload['lineage']}, "
              f"family={payload['family']}, window_refs={wrefs}, "
              f"placebo_method={payload.get('placebo_method')}")
        return

    hyp = registry.register(H004_CONFIG, cost_model_refs=available, producer="human:girish")
    print(f"\n=== {hyp.payload['lineage']} — hypothesis {hyp.record_id} "
          f"(schema v{hyp.schema_version}) ===")

    existing = _existing_verdict(store, hyp.record_id)
    if existing is not None:
        print("  already judged — refusing re-run; reporting existing verdict.")
        _print_verdict(existing)
        return

    cost_model = cost_models.load_cost_model(hyp.payload["cost_model_ref"])

    # Placebo FIRST (burns nothing); the sealed method must be entry_time_shuffle.
    placebo = PlaceboBattery(store, bulk).run(
        hyp.record_id, simulator=EventEngine(), cost_model=cost_model,
        bars=bars_union, events=events, method=ENTRY_TIME_SHUFFLE,
        base_seed=PLACEBO_SEED, n_runs=PLACEBO_N_RUNS,
    )
    print(f"  placebo_run  : {placebo.record_id} method={placebo.payload['method']} "
          f"n_runs={placebo.payload['n_runs']} n_pass={placebo.payload['n_pass']}")

    try:
        verdict = EvidenceBattery(store, bulk).run(
            hyp.record_id, simulator=EventEngine(), cost_model=cost_model,
            bars=bars_union, events=events,
        )
    except WindowBurnedError as e:
        print(f"  a window is already burned for this lineage — refusing: {e}")
        return
    _print_verdict(verdict)

    belief = BeliefLayer(store).update(
        verdict.record_id, claim=hyp.payload["thesis"], family=hyp.payload["family"]
    )
    print(f"  belief       : {belief.record_id} stance={belief.payload['stance']} "
          f"strength={belief.payload['strength']}")

    rep = store.verify()
    print(f"\njournal verify ok={rep.ok} n_records={rep.n_records} head={rep.head_hash[:12]}")


if __name__ == "__main__":
    main()
