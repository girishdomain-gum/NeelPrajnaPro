"""EvidenceBattery — the full §4.7 verdict pipeline end-to-end (ARCH-006 §3).

Covers the acceptance criteria: a planted-edge synthetic run reaches PASS with a
window_burn; the same window judged twice raises WindowBurnedError; the screener
is rejected by type; a broken engine trips the selftest gate; a VIRGIN window is
refused; and the verdict payload carries every required field. All runs happen in
a scratch datastore — no synthetic record touches the real journal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.errors import (
    ContaminationError,
    JudgeNotCalibratedError,
    WindowBurnedError,
)
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore
from qrf.trading.simulator.engine import EventEngine, Trades
from qrf.trading.utility.cost_models import CostModel

ZERO_COST = CostModel(name="zero", spread=0.0, slippage_per_side=0.0, commission_per_side=0.0)
_BASE_TS = 1_700_000_000_000_000_000


def _planted_bars_events(
    *, n_events: int, drift: float, hold: int = 1, noise_sd: float = 0.0, seed: int = 7
):
    """Episodic bars: each event enters next-open at 100, exits ``hold`` bars later.

    A long trade realises gross ``drift + N(0, noise_sd)``; with zero cost the net
    mean is ``drift``. Episodes are independent (one non-overlapping trade each).
    """
    rng = np.random.default_rng(seed)
    L = hold + 2
    n_bars = n_events * L
    ts = _BASE_TS + np.arange(n_bars, dtype=np.int64)
    opens = np.full(n_bars, 100.0, dtype=np.float64)
    moves = drift + rng.normal(0.0, noise_sd, size=n_events)
    ev_ts = []
    for k in range(n_events):
        e0 = k * L
        opens[e0 + 1 + hold] = 100.0 + moves[k]
        ev_ts.append(int(ts[e0]))
    bars = pd.DataFrame(
        {"ts": ts, "open": opens, "high": opens, "low": opens, "close": opens}
    )
    events = pd.DataFrame(
        {
            "ts": np.array(ev_ts, dtype=np.int64),
            "direction": np.ones(n_events, dtype=np.int64),
            "strength": np.ones(n_events, dtype=np.float64),
        }
    )
    return bars, events


def _scratch(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    return store, bulk


def _designate(store, bars, designation="TRAINING"):
    ts = bars["ts"].tolist()
    return WindowLedger(store).designate(
        "synthetic", int(ts[0]), int(ts[-1]) + 1, designation
    ).record_id


def _hypothesis(
    store, window_ref, *, lineage="planted", min_n=100, hold=1, embargo=2, base_alpha=0.05,
    family=None,
):
    payload = {
        "lineage": lineage,
        "scope": "synthetic",
        "instrument_refs": ["placeholder-instrument-ref"],
        "setup_dsl": {"event": "planted"},
        "execution": {
            "hold_bars": hold, "size": 1.0, "strength_min": 0.0,
            "stop_offset": None, "target_offset": None,
        },
        "cost_model_ref": "zero",
        "split_spec": {"n_folds": 4, "embargo_bars": embargo},
        "thresholds": {
            "min_n": min_n, "base_alpha": base_alpha, "correction": {"method": "bonferroni"},
        },
    }
    schema_version = 1
    if family is not None:
        payload["thesis"] = "A planted synthetic edge."
        payload["outcome_interpretations"] = {
            "PASS": "edge present", "FAIL": "no edge", "INSUFFICIENT": "too few",
        }
        payload["family"] = family
        schema_version = 2
    return store.append(
        "hypothesis", payload, producer="human:composer", event_ts=now_ns(),
        parents=[window_ref], schema_version=schema_version,
    ).record_id


def test_planted_edge_passes_and_burns(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100)

    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    p = verdict.payload
    assert p["verdict"] == "PASS"
    assert p["n_trades"] >= 100
    assert p["net"]["mean"] == pytest.approx(10.0, abs=0.5)
    # The window_burn was appended in the same flow, consuming this verdict.
    burns = [b for b in store.query(record_type="window_burn")
             if b.payload["consumed_by"] == verdict.record_id]
    assert len(burns) == 1
    assert burns[0].payload["window_ref"] == window
    # The pooled trades were persisted and are hash-verifiable.
    assert p["trades_manifest"]
    assert bulk.read(p["trades_manifest"]).num_rows == p["n_trades"]


def test_double_judge_refused_window_burned(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window)
    battery = EvidenceBattery(store, bulk)
    battery.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events)
    with pytest.raises(WindowBurnedError):
        battery.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events)


def test_noise_fails(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=0.0, noise_sd=1.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert verdict.payload["verdict"] == "FAIL"


def test_small_n_insufficient(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=20, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert verdict.payload["verdict"] == "INSUFFICIENT"
    assert verdict.payload["n_trades"] < 100


def test_screener_rejected_by_type(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=20, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window)

    class _FakeScreener:
        def run(self, *a, **k):  # note: 'run', not 'simulate'; no marker
            return None

    with pytest.raises(TypeError):
        EvidenceBattery(store, bulk).run(
            hyp, simulator=_FakeScreener(), cost_model=ZERO_COST, bars=bars, events=events
        )


def test_selftest_gate_blocks_broken_engine(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window)

    class _FlatEngine:
        is_audited_simulator = True
        engine_version = "flat"

        def simulate(self, bars, events, cost_model, *, seed, execution):
            # Always zero net -> planted-edge suite classifies FAIL, gate must fail.
            return Trades(seed=seed, trades=[], n_dropped_tail=0)

    with pytest.raises(JudgeNotCalibratedError):
        EvidenceBattery(store, bulk).run(
            hyp, simulator=_FlatEngine(), cost_model=ZERO_COST, bars=bars, events=events
        )


def test_virgin_window_refused(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=10.0)
    window = _designate(store, bars, designation="VIRGIN")
    hyp = _hypothesis(store, window)
    with pytest.raises(ContaminationError):
        EvidenceBattery(store, bulk).run(
            hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
        )
    # Nothing was burned (the refusal preceded any verdict).
    assert not list(store.query(record_type="verdict"))
    assert not list(store.query(record_type="window_burn"))


def test_verdict_payload_completeness_and_thresholds_byte_equal(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp_ref = _hypothesis(store, window)
    hyp = store.get(hyp_ref)
    verdict = EvidenceBattery(store, bulk).run(
        hyp_ref, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    p = verdict.payload
    for key in (
        "hypothesis_ref", "window_ref", "verdict", "n_trades", "n_dropped_tail",
        "gross", "net", "statistics", "folds", "corrections", "thresholds",
        "seed", "selftest_seed", "engine_version", "trades_manifest",
    ):
        assert key in p, f"verdict missing {key}"
    # Thresholds recorded AS REGISTERED (byte-equal to the hypothesis).
    assert p["thresholds"] == hyp.payload["thresholds"]
    assert verdict.parents == (hyp_ref, window)
    assert len(p["folds"]) == 4
    assert p["engine_version"] == "engine.s5.1"
    # Correction fields reconstruct the deflation.
    c = p["corrections"]
    assert c["base_alpha"] == 0.05 and c["method"] == "bonferroni"
    assert c["effective_alpha"] == pytest.approx(0.05 / max(1, c["family_m"]))


def test_deflated_alpha_can_flip_pass_to_fail(tmp_path):
    """A large trial ledger deflates alpha enough to reject an otherwise-significant edge."""
    store, bulk = _scratch(tmp_path)
    # A weak but positive edge: significant at 0.05, not at 0.05/huge.
    bars, events = _planted_bars_events(n_events=240, drift=0.15, noise_sd=1.0)
    window = _designate(store, bars)
    from qrf.kernel.corrections.trials import TrialCountLedger
    TrialCountLedger(store).bump("synthetic", "deflated", 100000, "screener")
    hyp = _hypothesis(store, window, lineage="deflated", min_n=100, base_alpha=0.05)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert verdict.payload["corrections"]["family_m"] == 100000
    assert verdict.payload["verdict"] == "FAIL"


def test_v2_hypothesis_deflates_by_family(tmp_path):
    """A v2 hypothesis deflates by its CLAIM family (DEVQ-015), capturing legacy
    lineage-keyed trials by prefix; the verdict records the family (schema v2)."""
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=0.15, noise_sd=1.0)
    window = _designate(store, bars)
    from qrf.kernel.corrections.trials import TrialCountLedger
    # A LEGACY lineage-keyed record (no family field) on the same instrument family.
    TrialCountLedger(store).bump("some_window", "smc.fvg.screen.s4", 100000, "screener")
    hyp_ref = _hypothesis(
        store, window, lineage="h_fvg", min_n=100, base_alpha=0.05, family="synthetic/smc.fvg"
    )
    verdict = EvidenceBattery(store, bulk).run(
        hyp_ref, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    c = verdict.payload["corrections"]
    # The legacy record was captured by instrument-family prefix WITHOUT re-keying.
    assert c["family_m"] == 100000
    assert c["family"] == "synthetic/smc.fvg"
    assert c["effective_alpha"] == pytest.approx(0.05 / 100000)
    assert verdict.schema_version == 2
    assert verdict.payload["verdict"] == "FAIL"  # deflation bites


def test_verdict_recomputes_from_persisted_trades(tmp_path):
    """IVF-style: the verdict's fold stats + net total recompute from its own trades."""
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_bars_events(n_events=240, drift=3.0, noise_sd=1.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window)
    v = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    p = v.payload
    trades = bulk.read(p["trades_manifest"]).to_pandas()
    assert len(trades) == p["n_trades"]
    assert trades["net_pnl"].sum() == pytest.approx(p["net"]["total"])
    assert trades["gross_pnl"].sum() == pytest.approx(p["gross"]["total"])
    for f in p["folds"]:
        sub = trades[trades["fold"] == f["index"]]
        assert len(sub) == f["n_trades"]
        if f["n_trades"]:
            assert sub["net_pnl"].mean() == pytest.approx(f["mean_net"])


def test_pooled_statistics_seed_reproducible(tmp_path):
    """The seeded bootstrap CI is byte-reproducible for the same (data, seed)."""
    store, bulk = _scratch(tmp_path)
    battery = EvidenceBattery(store, bulk)
    net = list(np.random.default_rng(0).normal(0.5, 1.0, size=200))
    s1 = battery._pooled_statistics(net, seed=4242)
    s2 = battery._pooled_statistics(net, seed=4242)
    assert s1 == s2
    # Mean / t / p are seed-independent; only the bootstrap CI moves with the seed.
    s3 = battery._pooled_statistics(net, seed=4243)
    assert s3["mean"] == s1["mean"] and s3["p"] == s1["p"]
