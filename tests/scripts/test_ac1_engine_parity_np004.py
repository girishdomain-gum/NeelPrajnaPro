"""ARCH-NP-004 §3 AC-1 — every existing sealed verdict reproduces byte-identically
under the bumped engine (``engine.s5.2``), with the new per-trade/R-multiple
capability unused.

h001-h004 rebuild via the SAME pipeline pieces ``scripts/rebuild_bulk.py`` uses
(bars -> events -> ``EvidenceBattery.evaluate`` -> ``EvidenceBattery.trades_table``,
never a parallel re-implementation) — but this test drives that loop itself
rather than calling ``rebuild_bulk.rebuild_all()``, because that orchestrator
unconditionally iterates EVERY verdict in the journal and has no dispatch entry
for the h007 lineage; it now raises ``SystemExit`` on any invocation, a
PRE-EXISTING break discovered while building this test (see
``ops/coordination/notes/NOTE-NP-003_rebuild_bulk_missing_h007_lineage.md``) and
unrelated to this work order — ``scripts/`` is outside WO-P's write scope
(``qrf/**`` + ``tests/**``, ARCH-NP-004 §9 addendum), so it is intentionally left
unfixed here and worked around instead of silently papered over.

h007 (the one JUDGED registration — the second registration was never judged,
so there is no verdict to byte-compare; see the third test below) is verified
the same way, using the same ``evaluate`` -> ``trades_table`` pipeline
``scripts/judge_h007_prediction_s1.py`` used to write the original verdict.

Both paths write only a DERIVED, gitignored ``datastore/bulk/*.parquet`` file
(never a journal record — asserted below) exactly like ``rebuild_bulk.py``
itself does; WO-P's "no ledger writes" rule (ARCH-NP-004 §9 addendum) is about
``datastore/journal/**``, the hash-chained ledger, not the rebuildable bulk
cache these scripts already treat as disposable.

Read-only integration tests: they use the real journal and the real
(gitignored) tick/bar sources, exactly like ``test_rebuild_bulk_s9.py``. The
h007 tests skip (not fail) when the raw tick source isn't present on the
machine running them.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.records.bulk import BulkStore, _sha256_file
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.utility import cost_models

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = ROOT / "datastore" / "bulk"
H007_LINEAGE = "h007_np_liquidity_sweep_v1_1"
SWEEP_EVENT_TYPE = "neelprajna.liquidity_sweep.sweep"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ac1_h001_through_h004_reproduce_byte_identically():
    """engine.s5.2 changes nothing for any sealed h001-h004 verdict (AC-1).

    Drives rebuild_bulk's own pieces (bars ingest, per-lineage event builders,
    EvidenceBattery.evaluate/trades_table) directly rather than calling
    rebuild_bulk.rebuild_all(), which raises on the journal's h007 verdict (see
    module docstring) — a pre-existing gap unrelated to this work order.
    """
    rebuild_bulk = _load("rebuild_bulk")
    store = RecordStore(rebuild_bulk.JOURNAL)
    n_before = len(store)
    bulk = BulkStore(store, rebuild_bulk.BULK_ROOT)

    rebuild_bulk.rebuild_bars()
    rebuild_bulk.rebuild_lens_bars()

    bars_cache: dict[str, tuple] = {}

    def _bars(dataset: str) -> tuple:
        if dataset not in bars_cache:
            manifest = next(
                m for m in store.query(record_type="bulk_manifest")
                if m.payload["dataset"] == dataset
            )
            table = bulk.read(manifest.record_id)  # hash gate
            bars_cache[dataset] = (table, table.to_pandas())
        return bars_cache[dataset]

    hyps = {h.record_id: h for h in store.query(record_type="hypothesis")}
    checked = 0
    for verdict in store.query(record_type="verdict"):
        manifest_ref = verdict.payload.get("trades_manifest")
        if not manifest_ref:
            continue
        hyp = hyps[verdict.payload["hypothesis_ref"]]
        lineage = hyp.payload["lineage"]
        if lineage == H007_LINEAGE:
            continue  # verified separately below (test_ac1_h007_reproduces_byte_identically)
        dataset = rebuild_bulk._LINEAGE_DATASET.get(lineage)
        if dataset is None:
            continue  # no dispatch entry for this lineage

        bars_table, bars_full = _bars(dataset)
        events = rebuild_bulk._events_for_lineage(lineage, bars_table, bars_full)
        cost_model = cost_models.load_cost_model(hyp.payload["cost_model_ref"])
        result = EvidenceBattery(store, bulk).evaluate(
            hyp.record_id, simulator=EventEngine(), cost_model=cost_model,
            bars=bars_full, events=events,
        )
        table = EvidenceBattery.trades_table(result.outcomes)
        assert table is not None, f"{lineage}: rebuild produced 0 trades but a manifest anchors one"

        recorded_sha = store.get(manifest_ref).payload["file_sha256"]
        path = BULK_ROOT / f"_ac1_{lineage}_rebuild_check.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, path)
        try:
            actual_sha = _sha256_file(path)
            assert actual_sha == recorded_sha, (
                f"AC-1 FAILED for {lineage}: rebuilt sha256 {actual_sha} != recorded {recorded_sha}"
            )
        finally:
            path.unlink(missing_ok=True)
        checked += 1

    assert checked == 4, "expected h001, h002, h003, h004 — every anchored trades dataset"
    assert len(RecordStore(rebuild_bulk.JOURNAL)) == n_before, "AC-1 check must not write the ledger"


def _h007_hypotheses(store: RecordStore) -> list:
    return [
        h for h in store.query(record_type="hypothesis")
        if h.payload["lineage"] == H007_LINEAGE
    ]


def test_ac1_h007_reproduces_byte_identically():
    """engine.s5.2 changes nothing for the judged h007 registration's 259 trades."""
    ingest = _load("ingest_h07_m5_vantage")
    if not ingest.TICK_DIR.exists():
        pytest.skip(f"H-007 raw tick source not present on this machine: {ingest.TICK_DIR}")

    store = RecordStore(JOURNAL)
    n_before = len(store)

    hyps = {h.record_id: h for h in _h007_hypotheses(store)}
    assert len(hyps) == 2, "expected both h007 registrations in the journal"
    verdicts = [v for v in store.query(record_type="verdict") if v.payload["hypothesis_ref"] in hyps]
    assert len(verdicts) == 1, "expected exactly one JUDGED h007 registration"
    verdict = verdicts[0]
    manifest_ref = verdict.payload["trades_manifest"]
    recorded_sha = store.get(manifest_ref).payload["file_sha256"]
    hyp = hyps[verdict.payload["hypothesis_ref"]]

    # Bars rebuilt straight from the raw ticks — a pure function, no bulk-store
    # read required (the ingested bulk_manifest/parquet may not even exist yet
    # in a fresh worktree; datastore/bulk/ is gitignored).
    bars_df = ingest.build_m5_bars(ingest.TICK_DIR)
    bars_table = pa.table(
        {
            "ts": pa.array(bars_df["ts"].tolist(), type=pa.int64()),
            "open": pa.array(bars_df["open"].tolist(), type=pa.float64()),
            "high": pa.array(bars_df["high"].tolist(), type=pa.float64()),
            "low": pa.array(bars_df["low"].tolist(), type=pa.float64()),
            "close": pa.array(bars_df["close"].tolist(), type=pa.float64()),
        }
    )
    bars = bars_table.to_pandas()

    all_events = LiquiditySweepDetector().detect(bars_table).to_pandas()
    events = all_events[all_events["event_type"] == SWEEP_EVENT_TYPE].reset_index(drop=True)

    cost_model = cost_models.load_cost_model(hyp.payload["cost_model_ref"])
    bulk = BulkStore(store, str(BULK_ROOT))
    result = EvidenceBattery(store, bulk).evaluate(
        hyp.record_id, simulator=EventEngine(), cost_model=cost_model, bars=bars, events=events,
    )
    table = EvidenceBattery.trades_table(result.outcomes)
    assert table is not None, "h007 rebuild produced 0 trades but the manifest anchors a non-empty dataset"

    path = BULK_ROOT / "_ac1_h007_rebuild_check.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    try:
        actual_sha = _sha256_file(path)
        assert actual_sha == recorded_sha, (
            f"AC-1 FAILED for h007: rebuilt sha256 {actual_sha} != recorded {recorded_sha}"
        )
    finally:
        path.unlink(missing_ok=True)  # scratch file — not the anchored dataset

    assert len(RecordStore(JOURNAL)) == n_before, "AC-1 check must not write the ledger"


def test_ac1_h007_second_registration_execution_unaffected():
    """The unjudged 2nd h007 registration has no verdict to byte-compare (it was
    never run) — the applicable proof is that its execution dict still parses to
    the identical ExecutionSpec, with neither new field silently active."""
    store = RecordStore(JOURNAL)
    hyps = _h007_hypotheses(store)
    assert len(hyps) == 2
    verdict_hyp_refs = {v.payload["hypothesis_ref"] for v in store.query(record_type="verdict")}
    unjudged = [h for h in hyps if h.record_id not in verdict_hyp_refs]
    assert len(unjudged) == 1, "expected exactly one UNJUDGED h007 registration"

    exe = ExecutionSpec.from_dict(unjudged[0].payload["execution"])
    assert exe.event_stop_column is None
    assert exe.target_r_multiple is None
    assert exe.stop_offset is None and exe.target_offset is None
