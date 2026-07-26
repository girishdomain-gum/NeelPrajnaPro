"""ARCH-010 §3 — Exploration Wave 2: the S4 screener on NEW ground.

Sprint 9 opened the second eye; Sprint 10 points the SAME instrument at data it
has never seen. The estate is exhausted on 2024: smc.fvg is deprioritized (two
decisive FAILs, 502 trials) and seasonality.calendar found no edge in two
attempts. Rather than a third variant on the burned year, this wave runs the
UNCHANGED S4 detector suite (smc.fvg) and the UNCHANGED 500-variant grid over the
**2025-TRAINING** window — a new year, same market, same telescope.

Discipline (all binding, all from the record):

* **Reserve untouched.** The 2025 primary feed parquet spans BOTH training and
  the 2025-VIRGIN reserve. The screener does NOT slice bars to a window (S4's
  sample manifest simply WAS the training data), so this script slices the bars
  to the 2025-TRAINING interval FIRST — canonical ``ts_start <= ts < ts_end``,
  the battery's own rule — and detects events on that slice ALONE. Nothing beyond
  ``ts_end`` is ever read into the sweep, so a near-boundary exit can never reach
  a reserve bar. An explicit assert proves the slice ends before the VIRGIN start.
* **Trial-counted from birth (§1).** The screener's single code path appends one
  ``trial_count`` of the EXACT grid size (500) keyed to family
  ``xauusd_h1/smc.fvg`` — every configuration counted, so a future smc.fvg claim
  is deflated by this search too (multiplicity accrues to the CLAIM's family, not
  the window it searched — DEVQ-015).
* **CANDIDATES, not claims.** This wave produces a shortlist only. NO hypothesis
  is registered — registration is a Sprint-11 decision with the Owner. The
  shortlist is recorded exactly as S4 did (manifest + declaring note).

Idempotent: if the Wave-2 shortlist for this lineage already exists it is reported
and not re-run. ``--rebuild-bulk`` re-creates the gitignored slice/events/shortlist
parquet from (journal + primary feed) and hash-verifies each, appending nothing.

    F:/QRF/.venv/Scripts/python.exe scripts/wave2_screen_s10.py
    F:/QRF/.venv/Scripts/python.exe scripts/wave2_screen_s10.py --rebuild-bulk
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.simulator.screener_vbt import Screener, ScreenThresholds

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"

# The 2025 primary feed (2024+2025) and the 2025-TRAINING / 2025-VIRGIN windows.
PRIMARY_MANIFEST = "01KYDC8XG934XDP8G5MDAT7JR4"
TRAIN_WINDOW = "01KYDE784029NZNXPPN5PA8P8G"   # xauusd_h1_primary_full, TRAINING
VIRGIN_WINDOW = "01KYDE784NHYD1ZX4X9BQJ54V2"  # xauusd_h1_primary_full, VIRGIN (reserve)

# The gitignored datasets this wave creates (all rebuildable, hash-verified).
BARS_DATASET = "xauusd_h1_primary_2025train"
EVENTS_DATASET = "xauusd_h1_primary_2025train_smc_fvg_events"
SHORTLIST_DATASET = "screener_shortlist_s10_wave2"

# The S4 detector suite + grid, UNCHANGED (500 variants).
LINEAGE = "smc.fvg.screen.s10.wave2"
# DEVQ-015: multiplicity accrues to the {market}/{instrument_family} — the SAME
# family the 2024 sweep + h001/h002 already burdened. A 2025 search on this market
# is still an smc.fvg search.
FAMILY = "xauusd_h1/smc.fvg"
COST_MODEL = "xauusd_retail_median"

GRID = {
    "hold_bars": list(range(1, 26)),                         # 25
    "strength_min": [round(0.1 * k, 1) for k in range(10)],  # 10
    "side": ["long", "short"],                               # 2  -> 500 variants
}
THRESHOLDS = ScreenThresholds(min_trades=30, min_sharpe=0.10)


def _calibrated_fvg_ref(store: RecordStore) -> str:
    """The instrument_ref of a passing-calibrated smc.fvg, or raise (S4 suite)."""
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


def _training_slice(
    store: RecordStore,
    bulk: BulkStore,
    *,
    primary_manifest: str = PRIMARY_MANIFEST,
    train_window: str = TRAIN_WINDOW,
    virgin_window: str = VIRGIN_WINDOW,
) -> pa.Table:
    """The 2025-TRAINING bars, sliced from the primary feed — reserve-safe.

    Canonical window slice (battery ``_window_bars``): ``ts_start <= ts < ts_end``.
    An explicit assert proves nothing at or beyond the 2025-VIRGIN start leaks in.
    The refs are parameters (defaulting to this wave's ids) so the reserve-safety
    property is unit-testable on a synthetic feed.
    """
    w = store.get(train_window).payload
    ts_start, ts_end = int(w["ts_start"]), int(w["ts_end"])
    virgin_start = int(store.get(virgin_window).payload["ts_start"])

    df = bulk.read(primary_manifest).to_pandas()  # hash-verified on read
    sl = df[(df["ts"] >= ts_start) & (df["ts"] < ts_end)]
    sl = sl.sort_values("ts", kind="mergesort").reset_index(drop=True)
    if len(sl) == 0:
        raise SystemExit("2025-TRAINING slice is empty — window/feed mismatch")
    # RESERVE GUARD: the training slice must end strictly before the reserve begins.
    assert int(sl["ts"].max()) < virgin_start, "training slice reached the VIRGIN reserve"
    assert ts_end <= virgin_start, "TRAINING ts_end overlaps the VIRGIN window"
    return pa.Table.from_pandas(sl, preserve_index=False)


def _manifest_by_dataset(store: RecordStore, dataset: str):
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m
    return None


def _bars_slice_manifest(store: RecordStore, bulk: BulkStore) -> str:
    """Reuse or write the 2025-TRAINING bars-slice dataset (parented on the feed)."""
    existing = _manifest_by_dataset(store, BARS_DATASET)
    if existing is not None:
        return existing.record_id
    table = _training_slice(store, bulk)
    m = bulk.write(BARS_DATASET, table, producer="human:girish",
                   parents=[PRIMARY_MANIFEST, TRAIN_WINDOW])
    print(f"wrote {table.num_rows} training bars -> slice manifest {m.record_id}")
    return m.record_id


def _events_manifest(store: RecordStore, bulk: BulkStore, bars_slice_ref: str) -> str:
    """Reuse or write the smc.fvg EventFrame over the training slice."""
    existing = _manifest_by_dataset(store, EVENTS_DATASET)
    if existing is not None:
        return existing.record_id
    bars = bulk.read(bars_slice_ref)
    ef = SMCFVGDetector().detect(bars)
    if ef.num_rows == 0:
        raise SystemExit("smc.fvg produced no events on the 2025-TRAINING slice")
    m = bulk.write(EVENTS_DATASET, ef, producer="smc.fvg", parents=[bars_slice_ref])
    print(f"wrote {ef.num_rows} FVG events -> events manifest {m.record_id}")
    return m.record_id


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
    print(f"smc.fvg calibrated ref = {fvg_ref} (S4 detector suite, unchanged)")

    existing = _existing_shortlist(store)
    if existing is not None:
        print(f"Wave-2 shortlist for {LINEAGE!r} exists: note {existing}; not re-running")
        return

    bars_ref = _bars_slice_manifest(store, bulk)
    events_ref = _events_manifest(store, bulk, bars_ref)
    designation = WindowLedger(store).check_screenable(TRAIN_WINDOW)

    t0 = time.perf_counter()
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[bars_ref],
        eventframe_manifest_ref=events_ref,
        grid=GRID,
        cost_model_name=COST_MODEL,
        window_ref=TRAIN_WINDOW,
        lineage=LINEAGE,
        family=FAMILY,
        thresholds=THRESHOLDS,
        shortlist_dataset=SHORTLIST_DATASET,
        producer="human:girish",
    )
    elapsed = time.perf_counter() - t0
    decl = json.loads(note.payload["text"])
    print(
        f"[Wave-2] window={designation} grid_size={decl['grid_size']} "
        f"trial_count_n={decl['trial_count_n']} n_admitted={decl['n_admitted']} "
        f"in {elapsed:.2f}s  (shortlist note {note.record_id})"
    )
    print(f"      shortlist manifest = {decl['shortlist_manifest_ref']}  "
          f"trial_count = {decl['trial_count_ref']}")
    ranking = bulk.read(decl["shortlist_manifest_ref"]).to_pandas()
    traded = ranking[ranking["n_trades"] > 0].head(5)
    print("      top traded variants (gross vs net):")
    for _, r in traded.iterrows():
        print(
            f"        hold={int(r['hold_bars'])} smin={r['strength_min']} side={r['side']} "
            f"n={int(r['n_trades'])} gross_total={r['gross_total']:.2f} "
            f"net_total={r['net_total']:.2f} net_sharpe={r['net_sharpe']:.3f} "
            f"admitted={bool(r['admitted'])}"
        )
    rep = store.verify()
    print(f"      journal verify ok={rep.ok} n_records={len(store)} head={rep.head_hash[:12]}")


def _rebuild_bulk() -> None:
    """Re-create the slice/events/shortlist parquet + hash-verify; no journal writes."""
    store = RecordStore(JOURNAL)
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)

    bars_m = _manifest_by_dataset(store, BARS_DATASET)
    ev_m = _manifest_by_dataset(store, EVENTS_DATASET)
    sl_m = _manifest_by_dataset(store, SHORTLIST_DATASET)
    if bars_m is None and ev_m is None and sl_m is None:
        print("nothing to rebuild: no Wave-2 manifests yet (run scripts/wave2_screen_s10.py)")
        return

    try:
        # 1. Training-slice bars: re-derive from the primary feed by the same slice.
        if bars_m is not None:
            table = _training_slice(store, bulk)
            path = Path(BULK_ROOT) / bars_m.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(table, path)
            bulk.read(bars_m.record_id)  # hash-verify vs manifest, or raise
            print(f"rebuilt + hash-verified {bars_m.record_id} "
                  f"({BARS_DATASET}, {table.num_rows} bars)")

        # 2. Events: re-run smc.fvg over the just-rebuilt slice.
        if ev_m is not None:
            if bars_m is None:
                raise SystemExit("cannot rebuild events without the bars-slice manifest")
            ef = SMCFVGDetector().detect(bulk.read(bars_m.record_id))
            path = Path(BULK_ROOT) / ev_m.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(ef, path)
            bulk.read(ev_m.record_id)  # hash-verify
            print(f"rebuilt + hash-verified {ev_m.record_id} "
                  f"({EVENTS_DATASET}, {ef.num_rows} events)")

        # 3. Shortlist ranking: the pure sweep (writes nothing) re-derives the parquet.
        if sl_m is not None:
            if ev_m is None:
                raise SystemExit("cannot rebuild the shortlist without its events manifest")
            result = Screener(store, bulk).compute_ranking(
                dataset_manifest_refs=[bars_m.record_id],
                eventframe_manifest_ref=ev_m.record_id,
                grid=GRID,
                cost_model_name=COST_MODEL,
                window_ref=TRAIN_WINDOW,
                thresholds=THRESHOLDS,
            )
            path = Path(BULK_ROOT) / sl_m.payload["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            pq.write_table(result.table, path)
            bulk.read(sl_m.record_id)  # hash-verify
            print(f"rebuilt + hash-verified {sl_m.record_id} "
                  f"({SHORTLIST_DATASET}, {result.table.num_rows} rows)")
    except BulkIntegrityError as e:
        raise SystemExit(f"rebuild hash mismatch or missing input: {e}") from e

    assert len(store) == n_before, "rebuild must not append records"
    print(f"journal unchanged: n_records={len(store)} (rebuild writes no records)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--rebuild-bulk", action="store_true",
        help="rebuild gitignored slice/events/shortlist parquet + hash-verify; no journal writes",
    )
    a = ap.parse_args()
    if a.rebuild_bulk:
        _rebuild_bulk()
        return
    _real_screen()


if __name__ == "__main__":
    main()
