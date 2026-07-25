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

``--rebuild-bulk`` (REV-S4 F-5): re-create the gitignored Sprint-4 detector and
screener parquet — the ``xauusd_h1_sample_smc_fvg_events`` (SMC FVG detect) and
``screener_shortlist`` (screener ranking) datasets — from the journal manifests
via the SAME deterministic computation, hash-verified against each existing
manifest, appending NOTHING to the journal. This is the F-1 remedy extended to
detector/screener datasets, so the Owner never hand-copies parquet between
worktrees again. The sample BARS parquet must exist first (rebuild it with
scripts/ingest_xauusd_s3.py --rebuild-bulk).

Run:  uv run python scripts/screen_s4.py
      uv run python scripts/screen_s4.py --rebuild-bulk
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.instruments.base import build_event_frame
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.simulator.screener_vbt import Screener, ScreenThresholds

SHORTLIST_DATASET = "screener_shortlist"

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


def _manifest_by_dataset(store: RecordStore, dataset: str):
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m
    return None


def _rebuild_bulk() -> None:
    """Re-create the events + shortlist parquet and hash-verify; no journal writes."""
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)

    ev_manifest = _manifest_by_dataset(store, EVENTS_DATASET)
    sl_manifest = _manifest_by_dataset(store, SHORTLIST_DATASET)
    if ev_manifest is None and sl_manifest is None:
        print(f"nothing to rebuild: no manifest for {EVENTS_DATASET!r} or "
              f"{SHORTLIST_DATASET!r} (run scripts/screen_s4.py first)")
        return

    try:
        # 1. Detector dataset: re-run smc.fvg over the sample bars.
        if ev_manifest is not None:
            bars = bulk.read(SAMPLE_MANIFEST)  # verifies the bars parquet too
            ef = SMCFVGDetector().detect(bars)
            path = Path(BULK_ROOT) / ev_manifest.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(ef, path)
            bulk.read(ev_manifest.record_id)  # hash-verify vs the manifest, or raise
            print(f"rebuilt + hash-verified {ev_manifest.record_id} "
                  f"({EVENTS_DATASET}, {ef.num_rows} events)")

        # 2. Screener dataset: re-run the ranking sweep (reads the events parquet
        #    just rebuilt). compute_ranking writes NOTHING to the journal.
        if sl_manifest is not None:
            if ev_manifest is None:
                raise SystemExit("cannot rebuild the shortlist without its events manifest")
            result = Screener(store, bulk).compute_ranking(
                dataset_manifest_refs=[SAMPLE_MANIFEST],
                eventframe_manifest_ref=ev_manifest.record_id,
                grid=GRID,
                cost_model_name=COST_MODEL,
                window_ref=SAMPLE_WINDOW,
                thresholds=ScreenThresholds(min_trades=30, min_sharpe=0.10),
            )
            path = Path(BULK_ROOT) / sl_manifest.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(result.table, path)
            bulk.read(sl_manifest.record_id)  # hash-verify vs the manifest, or raise
            print(f"rebuilt + hash-verified {sl_manifest.record_id} "
                  f"({SHORTLIST_DATASET}, {result.table.num_rows} rows)")
    except BulkIntegrityError as e:
        raise SystemExit(
            f"rebuild hash mismatch or missing input: {e}\n"
            "If the sample BARS parquet is missing, rebuild it first with:\n"
            "  uv run python scripts/ingest_xauusd_s3.py --rebuild-bulk"
        ) from e

    assert len(store) == n_before, "rebuild must not append records"
    print(f"journal unchanged: n_records={len(store)} (rebuild writes no records)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild-bulk", action="store_true",
        help="rebuild gitignored detector/screener parquet + hash-verify; no journal writes",
    )
    a = ap.parse_args()
    if a.rebuild_bulk:
        _rebuild_bulk()
        return
    _real_screen()
    _random_screen_scratch()


if __name__ == "__main__":
    main()
