"""BeliefLayer — updated ONLY by verdicts; stance/strength derived (ARCH-007 §3).

The arrow-8 audit: a belief refuses any non-verdict evidence. Stance/strength are
a pure function of the cited verdicts (so the IVF can recompute independently), and
the chain is append-only — a new verdict adds a state, never overwrites one.
"""

from __future__ import annotations

import pytest

from qrf.kernel.belief import REJECTED, SUPPORTED, UNTESTED, BeliefLayer
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.store import RecordStore

FAMILY = "xauusd_h1/smc.fvg"
CLAIM = "naive FVG follow-through is profitable"


def _store(tmp_path) -> RecordStore:
    return RecordStore(tmp_path / "journal.jsonl")


def _verdict(store: RecordStore, *, outcome: str, p: float | None) -> str:
    payload = {
        "hypothesis_ref": "01HYP",
        "window_ref": "01WIN",
        "verdict": outcome,
        "n_trades": 654,
        "n_dropped_tail": 0,
        "gross": {"total": -56.2, "mean": -0.08},
        "net": {"total": -363.58, "mean": -0.55},
        "statistics": {"t_one_sided": {"stat": -1.59, "p": p, "ci_low": -1.29, "ci_high": 0.14}},
        "folds": [],
        "corrections": {"family_m": 0, "method": "bonferroni", "base_alpha": 0.05,
                        "effective_alpha": 0.05},
        "thresholds": {"min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
        "seed": 1,
        "selftest_seed": 2,
        "engine_version": "engine.s5.1",
        "trades_manifest": "01TRADES",
    }
    return store.append("verdict", payload, producer="battery", event_ts=1).record_id


def _other_record(store: RecordStore) -> str:
    return store.append("note", {"text": "not a verdict"}, producer="t", event_ts=1).record_id


# --- the arrow-8 type audit --------------------------------------------------
def test_update_refuses_non_verdict_evidence(tmp_path):
    store = _store(tmp_path)
    note = _other_record(store)
    beliefs = BeliefLayer(store)
    with pytest.raises(SchemaViolation):
        beliefs.update(note, claim=CLAIM, family=FAMILY)
    assert not list(store.query(record_type="belief"))


def test_update_refuses_missing_evidence(tmp_path):
    beliefs = BeliefLayer(_store(tmp_path))
    with pytest.raises(SchemaViolation):
        beliefs.update("01DOESNOTEXIST", claim=CLAIM, family=FAMILY)


# --- stance + strength derivation -------------------------------------------
def test_fail_verdict_yields_rejected_belief(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.9435489368933117)
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == REJECTED
    assert rec.payload["strength"] == pytest.approx(0.9435489368933117)
    assert rec.payload["verdict_refs"] == [v]
    assert rec.parents == (v,)
    assert "prev_state" not in rec.payload


def test_pass_verdict_yields_supported_belief(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="PASS", p=0.01)
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == SUPPORTED
    assert rec.payload["strength"] == pytest.approx(0.99)


def test_insufficient_verdict_is_untested(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="INSUFFICIENT", p=None)
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == UNTESTED
    assert rec.payload["strength"] == 0.0


# --- append-only chain + idempotency ----------------------------------------
def test_idempotent_on_same_verdict(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.9)
    beliefs = BeliefLayer(store)
    r1 = beliefs.update(v, claim=CLAIM, family=FAMILY)
    r2 = beliefs.update(v, claim=CLAIM, family=FAMILY)
    assert r1.record_id == r2.record_id
    assert len(list(store.query(record_type="belief"))) == 1


def test_new_verdict_appends_state_never_overwrites(tmp_path):
    store = _store(tmp_path)
    v1 = _verdict(store, outcome="FAIL", p=0.9)
    beliefs = BeliefLayer(store)
    s1 = beliefs.update(v1, claim=CLAIM, family=FAMILY)
    v2 = _verdict(store, outcome="PASS", p=0.02)  # a later, decisive PASS
    s2 = beliefs.update(v2, claim=CLAIM, family=FAMILY)
    assert s2.record_id != s1.record_id
    # newest decisive verdict drives the stance; both verdicts are cited.
    assert s2.payload["stance"] == SUPPORTED
    assert s2.payload["verdict_refs"] == [v1, v2]
    assert s2.payload["prev_state"] == s1.record_id
    assert BeliefLayer(store).latest(FAMILY, CLAIM).record_id == s2.record_id
    # the first state is untouched (append-only).
    assert store.get(s1.record_id).payload["stance"] == REJECTED


def test_beliefs_isolate_by_family_and_claim(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.8)
    beliefs = BeliefLayer(store)
    beliefs.update(v, claim=CLAIM, family=FAMILY)
    assert beliefs.latest("other/family", CLAIM) is None
    assert beliefs.latest(FAMILY, "other claim") is None
