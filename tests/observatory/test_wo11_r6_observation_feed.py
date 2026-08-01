"""WO-11 (S4, spec A-013, refs A-019) — R6-shaped events through the EXISTING
Observation Engine. ZERO new semantics per A-013's own gate: qrf/kernel/
observatory/scan.py and qrf/trading/observatory/scans.py are UNCHANGED — this
file only proves the mechanism WO-01/prior lineages already exercised also
accepts a real liquidity-sweep (neelprajna, the R6 concept family) event
batch, with level/zone_hi/zone_lo populated exactly as the kernel §4.3
EventFrame contract requires, and that no ledger write happens beyond the
Observatory's own two-record contract (anomaly_scan + trial_count bump).

The bars fixture reuses WO-03's own single-pool pattern (tests/simulator/
test_wo02_liquidity_sweep_event_stop.py's segment A) — a REAL
LiquiditySweepDetector run, not hand-built events, so "R6-shaped" means what
it says: what the real detector actually emits.
"""

from __future__ import annotations

import pyarrow as pa

from qrf.kernel.observatory import Observatory
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.observatory.scans import weekend_partition_scan

FAMILY = "xauusd/neelprajna.liquidity_sweep"


def _store(tmp_path) -> RecordStore:
    return RecordStore(tmp_path / "journal.jsonl")


def _manifest(store: RecordStore, dataset: str) -> str:
    return store.append(
        "bulk_manifest",
        {
            "path": f"{dataset}/part-00000.parquet", "dataset": dataset, "row_count": 15,
            "byte_size": 100, "file_sha256": "0" * 64,
            "columns": [{"name": "ts", "dtype": "int64"}], "ts_min": 0, "ts_max": 14,
        },
        producer="test", event_ts=100,
    ).record_id


def _real_liquidity_sweep_events():
    """One real detector run (fixtures case A pattern: HIGH pool + sweep), with
    extra trailing bars so the sweep event (ts=14) has follow_through room."""
    n = 20  # 15 for the detection pattern + 5 trailing bars for descriptive room
    h = [100.00] * n
    low = [99.50] * n
    c = [100.00] * n
    h[3], h[10], h[14] = 100.20, 100.35, 100.45
    c[14] = 100.30
    bars_pa = pa.table(
        {
            "ts": pa.array(list(range(15)), type=pa.int64()),
            "high": h[:15], "low": low[:15], "close": c[:15],
        }
    )
    events = LiquiditySweepDetector().detect(bars_pa).to_pandas()

    import pandas as pd

    bars_pd = pd.DataFrame(
        {"ts": list(range(n)), "open": [100.0] * n, "high": h, "low": low, "close": c}
    )
    return bars_pd, events


def test_r6_shaped_events_have_level_and_zone_columns_populated():
    """EventFrame fidelity (WO-03's own AT-3 property), re-confirmed for the
    exact batch this WO-11 test feeds the observatory."""
    _, events = _real_liquidity_sweep_events()
    assert len(events) == 2  # pool_formed + sweep
    assert (events["level"].notna()).all()  # point-event level always populated
    assert (events["zone_hi"].isna()).all()  # point events: zone_hi/zone_lo NaN
    assert (events["zone_lo"].isna()).all()


def test_r6_shaped_batch_flows_through_the_unmodified_observatory(tmp_path):
    bars, events = _real_liquidity_sweep_events()
    store = _store(tmp_path)
    dataset = "xauusd_ticks_vantage_r6_test"
    man = _manifest(store, dataset)
    win = WindowLedger(store).designate(dataset, 0, 15, "TRAINING", producer="test")

    n_before = len(store)

    # The EXISTING trading-side descriptive scan (qrf/trading/observatory/scans.py,
    # UNCHANGED) computes findings from the real event batch — zero new semantics.
    findings, annotated = weekend_partition_scan(bars, events, seed=1, horizon=2)
    assert findings["n_events"] >= 0  # descriptive only; may be 0 if no room ahead

    # The EXISTING kernel Observatory (qrf/kernel/observatory/scan.py, UNCHANGED)
    # accepts the R6-family findings exactly as it accepts any other family's.
    obs = Observatory(store)
    scan = obs.scan(
        family=FAMILY, window_ref=win.record_id, manifest_refs=[man],
        method="neelprajna.liquidity_sweep.weekend_partition@h2", seed=1,
        findings=findings, n_searched=len(events),
    )

    assert scan.record_type == "anomaly_scan"
    assert scan.payload["findings"] == findings
    # No writes outside the engine's own contract: exactly 2 new records
    # (the anomaly_scan + its trial_count bump) — asserted, not narrated.
    assert len(store) == n_before + 2
    assert len(list(store.query(record_type="anomaly_scan"))) == 1
    assert len(list(store.query(record_type="trial_count"))) == 1
    assert not list(store.query(record_type="question"))  # no question raised, none forced
    assert not list(store.query(record_type="verdict"))  # observatory never judges
    assert not list(store.query(record_type="window_burn"))  # observatory never burns
