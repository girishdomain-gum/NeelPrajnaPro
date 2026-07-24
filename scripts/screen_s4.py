"""Sprint-4 screener acceptance (ARCH-004 AC, Blueprint §7 S4).

Demonstrates, against the REAL journal, the two Sprint-4 screener acceptance
criteria:

  (1) A 500-variant grid over ``xauusd_h1_sample`` TRAINING data screens in
      minutes; a shortlist artifact + a ``trial_count`` (n = 500) are recorded in
      one run (the single screener code path).
  (2) A random-signal grid of the same size (seeded synthetic no-edge events)
      yields an EMPTY shortlist under the declared metric thresholds — shown in a
      scratch store so no synthetic records touch the real ledger.

Prerequisites (real data + instruments): the sample bulk parquet rebuilt
(scripts/ingest_xauusd_s3.py --rebuild-bulk) and the SMC detectors bootstrapped
(scripts/bootstrap_smc_s4.py). Idempotent: if the real shortlist for this lineage
already exists it is reported and not re-run.

Run:  uv run python scripts/screen_s4.py
"""

from __future__ import annotations

import json
import time

import numpy as np
import pyarrow as pa

from qrf.kernel.instruments.base import build_event_frame
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.simulator.screener_vbt import Screener, ScreenThresholds

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
SAMPLE_MANIFEST = "01KYAWHZ6A9X3YZQ2W0BDRFDS1"
SAMPLE_WINDOW = "01KYAWHZ86ZNDGY4NZNCF4XFY0"
EVENTS_DATASET = "xauusd_h1_sample_smc_fvg_events"
LINEAGE = "smc.fvg.screen.s4"
COST_MODEL = "xauusd_retail_median"

GRID = {
    "hold_bars": list(range(1, 26)),                        # 25
    "strength_min": [round(0.1 * k, 1) for k in range(10)],  # 10
    "side": ["long", "short"],                              # 2  -> 500 variants
}


def _calibrated_fvg_ref(store: RecordStore) -> str:
    """The instrument_ref of a passing-calibrated smc.fvg, or raise."""
    regs = [
        r for r in store.query(record_type="instrument_registered")
        if r.payload["instrument_id"] == "smc.fvg"
    ]
    if not regs:
        raise SystemExit("smc.fvg not registered — run scripts/bootstrap_smc_s4.py first")
    ref = regs[-1].record_id
    passing = any(
        c.payload.get("instrument_ref") == ref and c.payload.get("overall_pass")
        for c in store.query(record_type="calibration")
    )
    if not passing:
        raise SystemExit("smc.fvg has no passing calibration — run scripts/bootstrap_smc_s4.py")
    return ref


def _events_manifest(store: RecordStore, bulk: BulkStore, fvg: SMCFVGDetector) -> str:
    """Reuse or build the smc.fvg EventFrame manifest for the sample (real journal)."""
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == EVENTS_DATASET:
            return m.record_id
    bars = bulk.read(SAMPLE_MANIFEST)
    ef = fvg.detect(bars)
    if ef.num_rows == 0:
        raise SystemExit("smc.fvg produced no events on the sample — cannot screen")
    manifest = bulk.write(EVENTS_DATASET, ef, producer="smc.fvg", parents=[SAMPLE_MANIFEST])
    print(f"wrote {ef.num_rows} FVG events -> events manifest {manifest.record_id}")
    return manifest.record_id


def _existing_shortlist(store: RecordStore) -> str | None:
    for n in store.query(record_type="note"):
        try:
            d = json.loads(n.payload["text"])
        except (ValueError, TypeError):
            continue
        if d.get("kind") == "screener_shortlist" and d.get("lineage") == LINEAGE:
            return n.record_id
    return None


def _real_screen() -> None:
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    fvg_ref = _calibrated_fvg_ref(store)
    print(f"smc.fvg calibrated ref = {fvg_ref}")

    existing = _existing_shortlist(store)
    if existing is not None:
        print(f"real shortlist for lineage {LINEAGE!r} exists: note {existing}; not re-running")
        return

    events_ref = _events_manifest(store, bulk, SMCFVGDetector())
    # Guard the window is screenable (TRAINING) before the expensive sweep.
    designation = WindowLedger(store).check_screenable(SAMPLE_WINDOW)

    t0 = time.perf_counter()
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[SAMPLE_MANIFEST],
        eventframe_manifest_ref=events_ref,
        grid=GRID,
        cost_model_name=COST_MODEL,
        window_ref=SAMPLE_WINDOW,
        lineage=LINEAGE,
        thresholds=ScreenThresholds(min_trades=30, min_sharpe=0.10),
        producer="human:girish",
    )
    elapsed = time.perf_counter() - t0
    decl = json.loads(note.payload["text"])
    print(
        f"[AC1] window={designation} grid_size={decl['grid_size']} "
        f"trial_count_n={decl['trial_count_n']} n_admitted={decl['n_admitted']} "
        f"in {elapsed:.2f}s  (shortlist note {note.record_id})"
    )
    print(f"      shortlist manifest = {decl['shortlist_manifest_ref']}  "
          f"trial_count = {decl['trial_count_ref']}")
    ranking = bulk.read(decl["shortlist_manifest_ref"]).to_pandas()
    traded = ranking[ranking["n_trades"] > 0].head(3)
    print("      gross vs net (top traded variants):")
    for _, r in traded.iterrows():
        print(
            f"        hold={int(r['hold_bars'])} smin={r['strength_min']} side={r['side']} "
            f"n={int(r['n_trades'])} gross_total={r['gross_total']:.2f} "
            f"net_total={r['net_total']:.2f} net_sharpe={r['net_sharpe']:.3f}"
        )
    rep = store.verify()
    print(f"      journal verify ok={rep.ok} n_records={len(store)} head={rep.head_hash[:12]}")


def _random_screen_scratch() -> None:
    """AC2: random no-edge grid -> empty shortlist, in a throwaway store."""
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp())
    store = RecordStore(tmp / "journal.jsonl")
    bulk = BulkStore(store, tmp / "bulk")
    rng = np.random.default_rng(20260725)
    n = 600  # synthetic series length
    step = 3600 * 10**9
    ts = np.array([1704160800000000000 + i * step for i in range(n)], dtype=np.int64)
    close = 2000.0 + np.cumsum(rng.normal(0.0, 1.0, n))  # driftless random walk
    bars = pa.table(
        {"ts": ts, "open": close, "high": close + 1.0, "low": close - 1.0, "close": close}
    )
    bm = bulk.write("rand_bars", bars, producer="synthetic", parents=[])
    idx = np.flatnonzero(rng.random(n) < 0.15)
    rows = [
        {
            "ts": int(ts[i]), "event_type": "rand.sig", "direction": 1, "level": float(close[i]),
            "zone_hi": float("nan"), "zone_lo": float("nan"), "strength": 1.0, "meta": "{}",
        }
        for i in idx
    ]
    em = bulk.write("rand_events", build_event_frame(rows), producer="synthetic", parents=[])
    w = WindowLedger(store).designate(
        "rand_bars", int(ts[0]), int(ts[-1]) + 1, "TRAINING", parents=[bm.record_id]
    )
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=GRID,
        cost_model_name=COST_MODEL,
        window_ref=w.record_id,
        lineage="random.noedge.s4",
        thresholds=ScreenThresholds(min_trades=30, min_sharpe=0.10),
    )
    decl = json.loads(note.payload["text"])
    verdict = "EMPTY" if decl["n_admitted"] == 0 else f"NON-EMPTY ({decl['n_admitted']})"
    print(
        f"[AC2] random-signal grid_size={decl['grid_size']} -> shortlist {verdict} "
        f"(n_admitted={decl['n_admitted']}) [scratch store; not in the real journal]"
    )


def main() -> None:
    _real_screen()
    _random_screen_scratch()


if __name__ == "__main__":
    main()
