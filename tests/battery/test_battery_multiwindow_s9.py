"""EvidenceBattery — multi-window (schema v3) judging (ARCH-009 §4, DEVQ-022 A).

A v3 hypothesis is judged over the UNION of disjoint windows: folds are computed
per window (the seam a hard boundary), trades pooled across the union, and EACH
window burned once. These tests cover the union PASS, the N-burns, the verdict v3
payload, re-run refusal on either window, a VIRGIN member refusal, and the
inter-window hole drop count.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import ContaminationError, WindowBurnedError
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility.cost_models import CostModel

ZERO_COST = CostModel(name="zero", spread=0.0, slippage_per_side=0.0, commission_per_side=0.0)


def _scratch(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    return store, bulk


def _planted(ts_base, *, n_events, drift, hold=1):
    """Episodic planted bars over a contiguous ts block starting at ``ts_base``."""
    L = hold + 2
    n_bars = n_events * L
    ts = ts_base + np.arange(n_bars, dtype=np.int64)
    opens = np.full(n_bars, 100.0, dtype=np.float64)
    ev_ts = []
    for k in range(n_events):
        e0 = k * L
        opens[e0 + 1 + hold] = 100.0 + drift
        ev_ts.append(int(ts[e0]))
    bars = pd.DataFrame({"ts": ts, "open": opens, "high": opens, "low": opens, "close": opens})
    events = pd.DataFrame(
        {
            "ts": np.array(ev_ts, dtype=np.int64),
            "direction": np.ones(n_events, dtype=np.int64),
            "strength": np.ones(n_events, dtype=np.float64),
        }
    )
    return bars, events


def _designate(store, bars, designation="TRAINING", dataset="synthetic"):
    ts = bars["ts"].tolist()
    return WindowLedger(store).designate(
        dataset, int(ts[0]), int(ts[-1]) + 1, designation
    ).record_id


def _multi_hyp(store, window_refs, *, lineage="multi", min_n=100, hold=1, embargo=2):
    payload = {
        "lineage": lineage,
        "scope": "synthetic",
        "instrument_refs": ["placeholder-ref"],
        "setup_dsl": {"event": "planted"},
        "execution": {
            "hold_bars": hold, "size": 1.0, "strength_min": 0.0,
            "stop_offset": None, "target_offset": None, "exit_rule": "time_stop",
        },
        "cost_model_ref": "zero",
        "split_spec": {"n_folds": 4, "embargo_bars": embargo},
        "thresholds": {"min_n": min_n, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
        "thesis": "A planted edge across two windows.",
        "outcome_interpretations": {"PASS": "edge", "FAIL": "no edge", "INSUFFICIENT": "few"},
        "family": "synthetic/planted",
        "window_refs": list(window_refs),
    }
    return store.append(
        "hypothesis", payload, producer="human:composer", event_ts=now_ns(),
        parents=list(window_refs), schema_version=3,
    ).record_id


def _two_windows(store, *, gap=10**12, n_a=140, n_b=140, hold=1):
    """Two disjoint planted windows separated by a hole; returns (bars, wa, wb)."""
    bars_a, ev_a = _planted(1_700_000_000_000_000_000, n_events=n_a, drift=10.0, hold=hold)
    b_base = int(bars_a["ts"].iloc[-1]) + gap
    bars_b, ev_b = _planted(b_base, n_events=n_b, drift=10.0, hold=hold)
    bars = pd.concat([bars_a, bars_b], ignore_index=True)
    events = pd.concat([ev_a, ev_b], ignore_index=True)
    wa = _designate(store, bars_a)
    wb = _designate(store, bars_b)
    return bars, events, wa, wb


def test_union_passes_and_burns_each_window(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events, wa, wb = _two_windows(store)
    hyp = _multi_hyp(store, [wa, wb], min_n=100)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    p = verdict.payload
    assert p["verdict"] == "PASS"
    assert verdict.schema_version == 3
    assert p["window_refs"] == [wa, wb]
    assert p["window_ref"] == wa  # primary retained for v1/v2 readers
    assert "n_dropped_hole" in p
    # ONE burn per window, both consuming this verdict.
    burns = [b for b in store.query(record_type="window_burn")
             if b.payload["consumed_by"] == verdict.record_id]
    assert {b.payload["window_ref"] for b in burns} == {wa, wb}
    assert len(burns) == 2
    # trades pooled across BOTH windows.
    assert p["n_trades"] >= 200


def test_rerun_refused_when_either_window_burned(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events, wa, wb = _two_windows(store)
    hyp = _multi_hyp(store, [wa, wb])
    battery = EvidenceBattery(store, bulk)
    battery.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events)
    with pytest.raises(WindowBurnedError):
        battery.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events)


def test_virgin_member_refused(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars_a, ev_a = _planted(1_700_000_000_000_000_000, n_events=140, drift=10.0)
    b_base = int(bars_a["ts"].iloc[-1]) + 10**12
    bars_b, ev_b = _planted(b_base, n_events=140, drift=10.0)
    bars = pd.concat([bars_a, bars_b], ignore_index=True)
    events = pd.concat([ev_a, ev_b], ignore_index=True)
    wa = _designate(store, bars_a, "TRAINING")
    wb = _designate(store, bars_b, "VIRGIN")  # a reserve in the union — must refuse
    hyp = _multi_hyp(store, [wa, wb])
    with pytest.raises(ContaminationError):
        EvidenceBattery(store, bulk).run(
            hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
        )
    # nothing burned when the run is refused.
    assert not list(store.query(record_type="window_burn"))


def test_hole_drop_counted(tmp_path):
    """A trade in the first (non-last) window whose time-stop exit lands past that
    window's end is dropped as a HOLE crossing and counted in n_dropped_hole."""
    store, bulk = _scratch(tmp_path)
    # Window A: 10 bars; an event near the end whose entry+hold exit is beyond A.
    ts_a = 1_700_000_000_000_000_000 + np.arange(10, dtype=np.int64)
    opens_a = np.full(10, 100.0)
    bars_a = pd.DataFrame({"ts": ts_a, "open": opens_a, "high": opens_a, "low": opens_a,
                           "close": opens_a})
    # Window B: a healthy planted block so the union is judgeable.
    b_base = int(ts_a[-1]) + 10**12
    bars_b, ev_b = _planted(b_base, n_events=140, drift=10.0, hold=4)
    bars = pd.concat([bars_a, bars_b], ignore_index=True)
    # event in A at bar index 8 (ts) -> entry bar 9 -> exit at 9+4=13 > 10 bars: hole drop.
    ev_a = pd.DataFrame({"ts": [int(ts_a[8])], "direction": [1], "strength": [1.0]})
    events = pd.concat([ev_a, ev_b], ignore_index=True)
    wa = _designate(store, bars_a)
    wb = _designate(store, bars_b)
    hyp = _multi_hyp(store, [wa, wb], hold=4, embargo=5, min_n=1)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert verdict.payload["n_dropped_hole"] >= 1
