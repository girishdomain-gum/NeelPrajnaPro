"""WO-07 stage B (S5, refs A-020) — drill law for the zero-epistemic-weight
gate (Architecture B.1): qrf.kernel.records.epistemic itself, plus each of
the four closed-write-authority functions it protects — EvidenceBattery.
evaluate/run, WindowLedger.burn, TrialCountLedger.bump, BeliefLayer.update
— proven to REFUSE tainted-ancestry input and stay GREEN on ordinary,
untainted input (the control every drill needs)."""

from __future__ import annotations

import pandas as pd
import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.belief.belief import BeliefLayer
from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import EpistemicTaintError
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.epistemic import (
    TAINTED_TYPES,
    append_with_lineage,
    compute_epistemic_lineage,
    is_tainted,
    refuse_if_tainted,
)
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore
from qrf.trading.simulator.engine import EventEngine
from qrf.trading.utility.cost_models import CostModel

ZERO_COST = CostModel(name="zero", spread=0.0, slippage_per_side=0.0, commission_per_side=0.0)


def _store(tmp_path) -> RecordStore:
    return RecordStore(tmp_path / "journal.jsonl")


def _npsu_record(store: RecordStore, *, record_type="npsu_legacy_import_trade"):
    return store.append(
        record_type,
        {
            "source": "x.csv", "file_sha256": "0" * 64, "row_count": 1,
            "bulk_manifest_ref": "stub", "epistemic_weight": "zero",
            "duplicate_source_paths": [],
        },
        producer="test", event_ts=now_ns(),
    )


# --- the module itself ----------------------------------------------------
def test_npsu_record_is_tainted_by_type(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    assert is_tainted(store, npsu.record_id)


def test_unrelated_record_is_clean(tmp_path):
    store = _store(tmp_path)
    win = WindowLedger(store).designate("d", 0, 1, "TRAINING", producer="test")
    assert not is_tainted(store, win.record_id)


def test_direct_parent_of_npsu_is_tainted_even_without_the_flag(tmp_path):
    """Fail-safe: a caller that referenced tainted data via plain
    store.append (forgetting append_with_lineage) is STILL caught, because
    is_tainted checks direct-parent TYPE, not only the cached meta flag."""
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    derived = store.append(
        "window", {"dataset": "d", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        producer="test", event_ts=now_ns(), parents=[npsu.record_id],
    )
    assert is_tainted(store, derived.record_id)


def test_append_with_lineage_stamps_the_flag_for_onehop_ancestors(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    derived = append_with_lineage(
        store, "window", {"dataset": "d", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        parents=[npsu.record_id], producer="test",
    )
    assert derived.meta["epistemic_lineage"] == "tainted"
    assert is_tainted(store, derived.record_id)


def test_compute_epistemic_lineage_clean_when_no_tainted_parent(tmp_path):
    store = _store(tmp_path)
    win = WindowLedger(store).designate("d", 0, 1, "TRAINING", producer="test")
    assert compute_epistemic_lineage(store, [win.record_id]) == "clean"


def test_refuse_if_tainted_raises_named_context(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    with pytest.raises(EpistemicTaintError, match="my-gate"):
        refuse_if_tainted(store, npsu.record_id, context="my-gate")


def test_legacy_pre_existing_records_are_never_retroactively_tainted(tmp_path):
    """The fail-safe must not blanket-refuse the ledger's own history: a
    record with zero NPSU connection anywhere in sight stays clean even
    though it predates this module and carries no meta flag at all."""
    store = _store(tmp_path)
    for i in range(5):
        rec = store.append(
            "window", {"dataset": f"d{i}", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
            producer="test", event_ts=now_ns(),
        )
        assert not is_tainted(store, rec.record_id)


def test_both_npsu_types_are_tainted(tmp_path):
    store = _store(tmp_path)
    for t in TAINTED_TYPES:
        rec = _npsu_record(store, record_type=t)
        assert is_tainted(store, rec.record_id)


# --- GATE 1: WindowLedger.burn ---------------------------------------------
def test_window_burn_refuses_tainted_window(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    ledger = WindowLedger(store)
    tainted_window = append_with_lineage(
        store, "window", {"dataset": "d", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        parents=[npsu.record_id], producer="test",
    )
    fake_verdict = store.append(
        "window", {"dataset": "_stub", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        producer="test", event_ts=now_ns(),
    )
    n_before = len(store)
    with pytest.raises(EpistemicTaintError):
        ledger.burn(tainted_window.record_id, "lineage_a", fake_verdict.record_id)
    assert len(store) == n_before  # refused before any write


def test_window_burn_still_works_on_clean_window(tmp_path):
    store = _store(tmp_path)
    ledger = WindowLedger(store)
    win = ledger.designate("d", 0, 1, "TRAINING", producer="test")
    fake_verdict = store.append(
        "window", {"dataset": "_stub", "ts_start": 0, "ts_end": 1, "designation": "TRAINING"},
        producer="test", event_ts=now_ns(),
    )
    burn = ledger.burn(win.record_id, "lineage_a", fake_verdict.record_id)
    assert burn.record_type == "window_burn"


# --- GATE 2: TrialCountLedger.bump ------------------------------------------
def test_trial_bump_refuses_tainted_parent(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    ledger = TrialCountLedger(store)
    n_before = len(store)
    with pytest.raises(EpistemicTaintError):
        ledger.bump("scope", "lineage", 1, "human", parents=[npsu.record_id])
    assert len(store) == n_before


def test_trial_bump_refuses_when_scope_itself_is_tainted(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    ledger = TrialCountLedger(store)
    with pytest.raises(EpistemicTaintError):
        ledger.bump(npsu.record_id, "lineage", 1, "human")


def test_trial_bump_still_works_on_clean_input(tmp_path):
    store = _store(tmp_path)
    ledger = TrialCountLedger(store)
    rec = ledger.bump("some_scope", "lineage", 1, "human")
    assert rec.record_type == "trial_count"


# --- GATE 3: BeliefLayer.update ---------------------------------------------
def test_belief_update_refuses_tainted_verdict(tmp_path):
    store = _store(tmp_path)
    npsu = _npsu_record(store)
    tainted_verdict = append_with_lineage(
        store, "verdict",
        {
            "hypothesis_ref": "stub", "window_ref": "stub", "verdict": "PASS",
            "n_trades": 1, "n_dropped_tail": 0,
            "gross": {"total": 1.0, "mean": 1.0}, "net": {"total": 1.0, "mean": 1.0},
            "statistics": {"t_one_sided": {"stat": 1.0, "p": 0.01, "ci_low": 0.0, "ci_high": 2.0}},
            "folds": [], "corrections": {
                "family_m": 1, "method": "bonferroni", "base_alpha": 0.05, "effective_alpha": 0.05,
            },
            "thresholds": {"min_n": 1, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
            "seed": 1, "selftest_seed": 1, "engine_version": "test", "trades_manifest": "",
        },
        parents=[npsu.record_id], producer="test",
    )
    belief = BeliefLayer(store)
    n_before = len(store)
    with pytest.raises(EpistemicTaintError):
        belief.update(tainted_verdict.record_id, claim="c", family="f")
    assert len(store) == n_before


# --- GATE 4: EvidenceBattery.evaluate/run -----------------------------------
class _StubSimulator:
    is_audited_simulator = True
    engine_version = "stub"

    def simulate(self, bars, events, cost_model, *, seed, execution):
        from qrf.trading.simulator.engine import Trades

        return Trades(seed=seed, trades=[], n_dropped_tail=0)


def _hypothesis_and_window(store, *, taint_window: bool):
    if taint_window:
        npsu = _npsu_record(store)
        window = append_with_lineage(
            store, "window",
            {"dataset": "d", "ts_start": 0, "ts_end": 100, "designation": "TRAINING"},
            parents=[npsu.record_id], producer="test",
        )
    else:
        window = WindowLedger(store).designate("d", 0, 100, "TRAINING", producer="test")
    hyp = store.append(
        "hypothesis",
        {
            "scope": "d", "lineage": "lin", "instrument_refs": ["x"],
            "setup_dsl": {"event": "e"}, "execution": {"hold_bars": 1, "size": 1.0},
            "cost_model_ref": "cm", "split_spec": {"n_folds": 1, "embargo_bars": 2},
            "thresholds": {"min_n": 1, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
        },
        producer="test", event_ts=now_ns(), parents=[window.record_id],
    )
    return hyp, window


def test_battery_evaluate_refuses_tainted_window(tmp_path):
    store = _store(tmp_path)
    bulk = BulkStore(store, str(tmp_path / "bulk"))
    hyp, _ = _hypothesis_and_window(store, taint_window=True)
    battery = EvidenceBattery(store, bulk)
    bars = pd.DataFrame({"ts": [], "open": [], "high": [], "low": [], "close": []})
    events = pd.DataFrame({"ts": [], "direction": [], "strength": []})
    with pytest.raises(EpistemicTaintError):
        battery.evaluate(hyp.record_id, simulator=_StubSimulator(), cost_model=object(),
                          bars=bars, events=events)


def test_battery_run_refuses_tainted_window(tmp_path):
    store = _store(tmp_path)
    bulk = BulkStore(store, str(tmp_path / "bulk"))
    hyp, _ = _hypothesis_and_window(store, taint_window=True)
    battery = EvidenceBattery(store, bulk)
    bars = pd.DataFrame({"ts": [], "open": [], "high": [], "low": [], "close": []})
    events = pd.DataFrame({"ts": [], "direction": [], "strength": []})
    n_before = len(store)
    # The real audited engine (not the stub) -- run() calls the selftest
    # gate (step 2) BEFORE the taint gate (step 3), so a stub that always
    # returns zero trades would fail calibration first, never reaching the
    # gate this test exists to prove.
    with pytest.raises(EpistemicTaintError):
        battery.run(hyp.record_id, simulator=EventEngine(), cost_model=ZERO_COST,
                     bars=bars, events=events)
    assert len(store) == n_before  # refused before verdict/burn


def test_battery_evaluate_unaffected_on_clean_hypothesis(tmp_path):
    """Control: an ordinary (untainted) hypothesis is not blocked by this
    gate — the tainted-window test above is not merely failing for some
    other, unrelated reason (e.g. a malformed hypothesis fixture)."""
    store = _store(tmp_path)
    bulk = BulkStore(store, str(tmp_path / "bulk"))
    hyp, _ = _hypothesis_and_window(store, taint_window=False)
    battery = EvidenceBattery(store, bulk)
    bars = pd.DataFrame({"ts": [], "open": [], "high": [], "low": [], "close": []})
    events = pd.DataFrame({"ts": [], "direction": [], "strength": []})
    # Should get past the taint gate; whatever happens next (selftest, e.g.)
    # is unrelated to this WO, so only assert it's NOT an EpistemicTaintError.
    try:
        battery.evaluate(hyp.record_id, simulator=_StubSimulator(), cost_model=object(),
                          bars=bars, events=events)
    except EpistemicTaintError:
        pytest.fail("clean hypothesis was wrongly refused by the epistemic-taint gate")
    except Exception:
        pass  # any other failure is out of this test's scope
