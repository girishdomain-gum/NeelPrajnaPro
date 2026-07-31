"""ARCH-009 §1 — rebuild EVERY verdict_trades.* dataset from journal + bars alone.

The carried debt from Sprint 8, now due: a verdict record anchors its pooled
fold trades in a ``verdict_trades.<lineage>`` Parquet file (a ``bulk_manifest``),
but those files are gitignored — the journal is the root of trust. This script
proves that the anchored bytes are REBUILDABLE: for every verdict in the journal
it deterministically re-runs the recorded experiment (bars -> events -> splits ->
fills) via the SAME pipeline the verdict used (``EvidenceBattery.evaluate`` ->
``EvidenceBattery.trades_table``, never a parallel implementation), writes the
Parquet to the manifest's path, and asserts the rebuilt file's sha256 EQUALS the
manifest's ``file_sha256``. A rebuild that "mostly matches" is a fabrication —
any mismatch is a loud, fatal failure, not a warning.

    .venv/Scripts/python.exe scripts/rebuild_bulk.py            # rebuild + assert
    .venv/Scripts/python.exe scripts/rebuild_bulk.py --check    # same; explicit

This repository's own venv is required: the archived origin's interpreter
resolves ``qrf`` to the retired Kernel, silently, for any lineage that predates
the split (NOTE-NP-005).

Appends NOTHING (asserted). The bars parquets are rebuilt first from their source
(reusing each ingest's own rebuild path so there is one bars-rebuild code path per
dataset); then every registered lineage (h001 / h002 / h003 / h004 / h007) is
regenerated. An unknown lineage (a future verdict with no registered event
builder) is a LOUD failure, never a silent skip — "every" means every.

Independent-lens note (ARCH-009 architecture note of record): the per-lineage
event reconstruction below is a dispatch, so a new hypothesis lineage joins by
adding one builder, not by forking this script.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import BulkIntegrityError
from qrf.kernel.records.bulk import BulkStore, _sha256_file
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.concepts.seasonality.detector import SeasonalityDetector
from qrf.trading.concepts.smc.detector import SMCFVGDetector
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"
DATASET_FULL = "xauusd_h1_full"
DATASET_PRIMARY = "xauusd_h1_primary_full"  # spans 2024+2025 (H-004's multi-window union)

# scripts/ is not a package (see tests/scripts/test_arch003a.py). Load the sibling
# judges by file path so the ONE bars-rebuild path and the ONE set of setup-event
# builders are reused verbatim — the CLI resolves them without a PYTHONPATH.
_SCRIPTS = Path(__file__).resolve().parent


def _load_sibling(name: str):
    spec = importlib.util.spec_from_file_location(name, _SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_judge_h001 = _load_sibling("judge_h001")
_wave1 = _load_sibling("judge_family_wave1_s8")
_lens = _load_sibling("ingest_lens_feeds_s9")
_h007_ingest = _load_sibling("ingest_h07_m5_vantage")
rebuild_bars = _judge_h001.rebuild_bulk
rebuild_lens_bars = _lens.rebuild  # rebuilds xauusd_h1_primary_full (+ secondfeed) parquet
rebuild_h007_bars = _h007_ingest.rebuild_bulk  # rebuilds xauusd_m5_vantage from raw ticks
_intra_week_events = _wave1._intra_week_events
_monday_long_events = _wave1._monday_long_events

DATASET_H007_M5 = _h007_ingest.DATASET  # "xauusd_m5_vantage" (NP-ADR-008 §5 v1.1)
_H007_SWEEP_EVENT_TYPE = f"{LiquiditySweepDetector.instrument_id}.sweep"

# Which ingested dataset carries each lineage's window bars. Single-window 2024
# lineages ride xauusd_h1_full; H-004's multi-window union (2024+2025) rides
# xauusd_h1_primary_full (whose 2024 slice is byte-identical to xauusd_h1_full);
# H-007 (NP-ADR-008 §5 v1.1 liquidity sweep) rides its own M5 vantage bars.
_LINEAGE_DATASET = {
    "h001_fvg_follow_through": DATASET_FULL,
    "h002_fvg_intraweek_follow_through": DATASET_FULL,
    "h003_dow_monday_drift": DATASET_FULL,
    "h004_dow_monday_drift_v2": DATASET_PRIMARY,
    "h007_np_liquidity_sweep_v1_1": DATASET_H007_M5,
}


def _manifest_for(store: RecordStore, dataset: str) -> Record:
    for m in store.query(record_type="bulk_manifest"):
        if m.payload["dataset"] == dataset:
            return m
    raise SystemExit(f"no bulk_manifest for {dataset}; the bars were never ingested")


def _events_for_lineage(
    lineage: str, bars_table, bars_full: pd.DataFrame
) -> pd.DataFrame:
    """Reconstruct the EXACT setup events each recorded verdict was judged on.

    Dispatch by lineage; every branch calls the same detector/filter the original
    judge used (imported, not copied). ``bars_table``/``bars_full`` are that
    lineage's own dataset (see :data:`_LINEAGE_DATASET`). A lineage with no
    registered builder is a loud failure so a new verdict can never be silently
    left un-rebuilt.
    """
    if lineage == "h001_fvg_follow_through":
        return SMCFVGDetector().detect(bars_table).to_pandas()
    if lineage == "h002_fvg_intraweek_follow_through":
        fvg = SMCFVGDetector().detect(bars_table).to_pandas()
        return _intra_week_events(bars_full, fvg)
    if lineage in ("h003_dow_monday_drift", "h004_dow_monday_drift_v2"):
        # H-004 shares H-003's Monday-long builder; the difference is the MULTI-WINDOW
        # union (sealed in the hypothesis, applied by the battery), not the events.
        seasonality = SeasonalityDetector().detect(bars_table).to_pandas()
        return _monday_long_events(seasonality)
    if lineage == "h007_np_liquidity_sweep_v1_1":
        all_events = LiquiditySweepDetector().detect(bars_table).to_pandas()
        return all_events[all_events["event_type"] == _H007_SWEEP_EVENT_TYPE].reset_index(
            drop=True
        )
    raise SystemExit(
        f"no event builder registered for lineage {lineage!r} — refusing to "
        "leave its verdict_trades un-rebuilt (register a builder in "
        "scripts/rebuild_bulk.py:_events_for_lineage)"
    )


def rebuild_all(*, verbose: bool = True) -> list[str]:
    """Rebuild every verdict_trades.* file and assert each sha == its manifest.

    Returns the list of manifest_refs rebuilt. Raises on any mismatch, any missing
    builder, or any accidental record append.
    """
    # 1. Bars parquets first (root of trust for events) — reuse the ingest paths.
    #    xauusd_h1_full (2024) via judge_h001; xauusd_h1_primary_full (2024+2025, for
    #    H-004's union) via the lens ingest; xauusd_m5_vantage (H-007) via its own
    #    tick-source ingest. All three are hash-verified on read below.
    rebuild_bars()
    rebuild_lens_bars()
    rebuild_h007_bars()

    store = RecordStore(JOURNAL)  # verifies the chain on open
    bulk = BulkStore(store, BULK_ROOT)
    n_before = len(store)

    # Load each dataset once, hash-verified, and cache by name.
    bars_cache: dict[str, tuple] = {}

    def _bars(dataset: str) -> tuple:
        if dataset not in bars_cache:
            table = bulk.read(_manifest_for(store, dataset).record_id)  # hash gate
            bars_cache[dataset] = (table, table.to_pandas())
        return bars_cache[dataset]

    hyps = {h.record_id: h for h in store.query(record_type="hypothesis")}

    rebuilt: list[str] = []
    for verdict in store.query(record_type="verdict"):
        manifest_ref = verdict.payload.get("trades_manifest")
        if not manifest_ref:
            continue  # a 0-trade verdict anchors no dataset (correct, not a gap)

        hyp = hyps[verdict.payload["hypothesis_ref"]]
        lineage = hyp.payload["lineage"]
        dataset = _LINEAGE_DATASET.get(lineage)
        if dataset is None:
            raise SystemExit(
                f"no dataset registered for lineage {lineage!r} — add it to "
                "scripts/rebuild_bulk.py:_LINEAGE_DATASET"
            )
        bars_table, bars_full = _bars(dataset)
        events = _events_for_lineage(lineage, bars_table, bars_full)

        cost_model = cost_models.load_cost_model(hyp.payload["cost_model_ref"])
        # Same pipeline the verdict ran (default engine_seed == seeds.for_run),
        # WITHOUT burning — evaluate() is the placebo/replay entry point. For a
        # multi-window lineage evaluate slices each window from these bars itself.
        result = EvidenceBattery(store, bulk).evaluate(
            hyp.record_id,
            simulator=EventEngine(),
            cost_model=cost_model,
            bars=bars_full,
            events=events,
        )
        table = EvidenceBattery.trades_table(result.outcomes)
        if table is None:
            raise SystemExit(
                f"{lineage}: rebuild produced 0 trades but manifest {manifest_ref} "
                "anchors a non-empty dataset — the experiment did not reproduce"
            )

        manifest = store.get(manifest_ref)
        recorded_sha = manifest.payload["file_sha256"]
        path = bulk.path_for(manifest_ref)
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, path)

        # BINDING (ARCH-009 §1): byte-exact or loud failure. Two independent
        # checks — the direct sha assert AND bulk.read()'s own hash gate.
        actual_sha = _sha256_file(path)
        if actual_sha != recorded_sha:
            raise SystemExit(
                f"REBUILD MISMATCH for {lineage} (manifest {manifest_ref}):\n"
                f"  rebuilt sha256  = {actual_sha}\n"
                f"  recorded sha256 = {recorded_sha}\n"
                "A rebuild that does not match byte-for-byte is a fabrication."
            )
        try:
            bulk.read(manifest_ref)  # re-hashes the file; raises on any drift
        except BulkIntegrityError as e:  # pragma: no cover - covered by the assert above
            raise SystemExit(f"bulk.read hash gate failed after rebuild: {e}") from e

        rebuilt.append(manifest_ref)
        if verbose:
            print(
                f"rebuilt + sha-verified {lineage}: {manifest_ref} "
                f"({table.num_rows} rows, sha {actual_sha[:16]}… == recorded)"
            )

    assert len(store) == n_before, "rebuild must not append records"
    if verbose:
        print(f"\nrebuilt {len(rebuilt)} verdict_trades dataset(s); all sha256 assert-equal.")
    return rebuilt


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check", action="store_true",
        help="rebuild every verdict_trades.* and assert sha == manifest (the default)",
    )
    ap.parse_args()
    rebuild_all()


if __name__ == "__main__":
    main()
