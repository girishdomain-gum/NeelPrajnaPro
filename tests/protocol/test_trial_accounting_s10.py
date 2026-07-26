"""ARCH-010 §1 — trial accounting at registration (ADR-011).

Registration SPENDS one family attempt: :meth:`HypothesisRegistry.register`
appends exactly one ``trial_count`` ``{family, lineage, n_attempts: 1}`` in the
same flow, parented on the new hypothesis and sharing its instant. The three
binding checks the instruction names are exercised here:

1. registration appends exactly one such trial (and idempotent re-registration
   appends none);
2. the deflation SEES it — a family's trial burden rises by one per registration,
   so siblings deflate one another;
3. an existing verdict's recorded ``family_m`` is UNTOUCHED by a later (retro or
   sibling) trial_count append — history is immutable; the ledger only learns.
"""

from __future__ import annotations

import pytest

from qrf.kernel.corrections.deflation import deflate_family, family_trials
from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

COST_MODELS = ["xauusd_retail_median"]


def _register_instrument(store, iid, version="0.1.0"):
    reg = store.append(
        "instrument_registered",
        {
            "instrument_id": iid,
            "kind": "detector",
            "version": version,
            "params_schema": {},
            "code_ref": f"{iid}:{version}",
        },
        producer="human:bootstrap",
        event_ts=now_ns(),
    )
    store.append(
        "calibration",
        {
            "instrument_ref": reg.record_id,
            "suite_id": f"{iid}.suite",
            "cases": [
                {"case_id": "c1", "kind": "planted_truth", "expected": 1, "got": 1, "pass": True}
            ],
            "pass_rate_truth": 1.0,
            "silence_rate_noise": 1.0,
            "overall_pass": True,
        },
        producer="calibration",
        event_ts=now_ns(),
        parents=[reg.record_id],
    )
    return reg.record_id


def _window(store, *, ts_start=1000, ts_end=2000):
    return store.append(
        "window",
        {
            "dataset": "xauusd_h1_full",
            "ts_start": ts_start,
            "ts_end": ts_end,
            "designation": "TRAINING",
        },
        producer="human:protocol",
        event_ts=now_ns(),
    ).record_id


def _config(window_ref, *, lineage="h001_fvg_follow_through", family="xauusd_h1/smc.fvg", **ov):
    cfg = {
        "lineage": lineage,
        "scope": "xauusd_h1",
        "window": window_ref,
        "instruments": ["smc.fvg@0.1.0"],
        "setup_dsl": {"event": "smc.fvg", "direction": "follow_through"},
        "execution": {
            "hold_bars": 4, "size": 1.0, "strength_min": 0.0,
            "stop_offset": None, "target_offset": None,
        },
        "cost_model_ref": "xauusd_retail_median",
        "split_spec": {"n_folds": 4, "embargo_bars": 8},
        "thresholds": {"min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
        "thesis": "After an FVG forms, price follows through in its direction.",
        "outcome_interpretations": {
            "PASS": "The follow-through edge survives real costs.",
            "FAIL": "No net edge after costs.",
            "INSUFFICIENT": "Too few trades to decide.",
        },
        "family": family,
    }
    cfg.update(ov)
    return cfg


@pytest.fixture
def store(tmp_path):
    s = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(s, "smc.fvg")
    return s


def _trials(store):
    return list(store.query(record_type="trial_count"))


# 1 — registration appends exactly one trial_count -----------------------------

def test_registration_appends_exactly_one_trial(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    assert _trials(store) == []
    h = reg.register(_config(w), cost_model_refs=COST_MODELS)

    trials = _trials(store)
    assert len(trials) == 1
    tc = trials[0]
    # {family, lineage, n_attempts: 1} — exactly the ADR-011 shape.
    assert tc.payload["family"] == "xauusd_h1/smc.fvg"
    assert tc.payload["lineage"] == "h001_fvg_follow_through"
    assert tc.payload["n_attempts"] == 1
    assert tc.payload["source"] == "human"
    # parented on the hypothesis, sharing its instant — auditable back to the claim.
    assert tc.parents == (h.record_id,)
    assert tc.event_ts == h.event_ts


def test_idempotent_reregistration_appends_no_second_trial(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert len(_trials(store)) == 1
    # Same config -> idempotent return -> the attempt is NOT counted twice.
    reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert len(_trials(store)) == 1


def test_explicit_event_ts_is_shared_by_hypothesis_and_trial(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    ts = 1_700_000_000_000_000_000
    h = reg.register(_config(w), cost_model_refs=COST_MODELS, event_ts=ts)
    assert h.event_ts == ts
    assert _trials(store)[0].event_ts == ts


# 2 — the deflation sees it ----------------------------------------------------

def test_deflation_sees_the_registration_attempt(store):
    reg = HypothesisRegistry(store)
    fam = "xauusd_h1/smc.fvg"
    # Before any registration, the family carries no burden.
    assert family_trials(fam, store) == 0

    reg.register(_config(_window(store)), cost_model_refs=COST_MODELS)
    assert family_trials(fam, store) == 1
    # base_alpha deflated by the one recorded attempt.
    d1 = deflate_family(0.05, fam, store)
    assert d1.n_trials == 1
    assert d1.effective_alpha == pytest.approx(0.05)

    # A sibling in the same family — a SECOND attempt — deflates them both.
    reg.register(
        _config(_window(store, ts_start=3000, ts_end=4000), lineage="h002_fvg_intraweek"),
        cost_model_refs=COST_MODELS,
    )
    assert family_trials(fam, store) == 2
    d2 = deflate_family(0.05, fam, store)
    assert d2.n_trials == 2
    assert d2.effective_alpha == pytest.approx(0.025)


def test_distinct_families_do_not_cross_deflate(store):
    _register_instrument(store, "seasonality.calendar")
    reg = HypothesisRegistry(store)
    reg.register(_config(_window(store)), cost_model_refs=COST_MODELS)  # smc.fvg
    reg.register(
        _config(
            _window(store, ts_start=3000, ts_end=4000),
            lineage="h003_dow_monday_drift",
            family="xauusd_h1/seasonality.calendar",
            instruments=["seasonality.calendar@0.1.0"],
            setup_dsl={"event": "seasonality.calendar", "direction": "long"},
        ),
        cost_model_refs=COST_MODELS,
    )
    assert family_trials("xauusd_h1/smc.fvg", store) == 1
    assert family_trials("xauusd_h1/seasonality.calendar", store) == 1


# 3 — an existing verdict's recorded family_m is untouched ----------------------

def test_existing_verdict_family_m_untouched_by_later_trial(store):
    """A verdict sealed under the rule as it stood stays history; a later
    trial_count append (retro-count or a sibling registration) never mutates it.
    """
    fam = "xauusd_h1/seasonality.calendar"
    _register_instrument(store, "seasonality.calendar")
    reg = HypothesisRegistry(store)
    # A first attempt whose verdict recorded family_m at the value it then saw.
    h = reg.register(
        _config(
            _window(store),
            lineage="h003_dow_monday_drift",
            family=fam,
            instruments=["seasonality.calendar@0.1.0"],
            setup_dsl={"event": "seasonality.calendar", "direction": "long"},
        ),
        cost_model_refs=COST_MODELS,
    )
    # family_m as of judging time: 1 (its own registration attempt).
    m_at_judging = family_trials(fam, store)
    verdict = store.append(
        "verdict",
        {
            "hypothesis_ref": h.record_id,
            "window_ref": "01WIN",
            "verdict": "FAIL",
            "n_trades": 654,
            "n_dropped_tail": 0,
            "gross": {"total": -56.2, "mean": -0.08},
            "net": {"total": -363.58, "mean": -0.55},
            "statistics": {
                "t_one_sided": {"stat": -1.59, "p": 0.9, "ci_low": -1.29, "ci_high": 0.14}
            },
            "folds": [],
            "corrections": {
                "family_m": m_at_judging, "method": "bonferroni",
                "base_alpha": 0.05, "effective_alpha": 0.05,
            },
            "thresholds": {
                "min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}
            },
            "seed": 1,
            "selftest_seed": 2,
            "engine_version": "engine.s5.1",
            "trades_manifest": "01TRADES",
        },
        producer="battery",
        event_ts=now_ns(),
        parents=[h.record_id],
    )
    assert verdict.payload["corrections"]["family_m"] == 1

    # A back-dated retro-count / sibling attempt appends LATER...
    TrialCountLedger(store).bump(
        scope="xauusd_h1", lineage="h004_dow_monday_drift_v2", n=1, source="human",
        family=fam, parents=[h.record_id], producer="developer:claude-code",
        event_ts=h.event_ts,
    )
    # ...the family total rises, but the sealed verdict's family_m is UNCHANGED.
    assert family_trials(fam, store) == 2
    assert store.get(verdict.record_id).payload["corrections"]["family_m"] == 1
