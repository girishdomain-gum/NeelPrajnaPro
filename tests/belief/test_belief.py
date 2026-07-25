"""BeliefLayer — updated ONLY by verdicts; stance/strength derived (ARCH-007 §3).

The arrow-8 audit: a belief refuses any non-verdict evidence. Stance/strength are
a pure function of the cited verdicts (so the IVF can recompute independently), and
the chain is append-only — a new verdict adds a state, never overwrites one.
"""

from __future__ import annotations

import pytest

from qrf.kernel.belief import CONTESTED, REJECTED, SUPPORTED, UNTESTED, BeliefLayer
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


# --- stance + strength = DECISIVENESS 2·|p−0.5| (DEVQ-016 ruling) ------------
def test_fail_verdict_yields_rejected_belief_at_h001_decisiveness(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.9435489368933117)  # H-001's own p
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == REJECTED
    # 2·|0.9435−0.5| = 0.887 — the anchor the ruling names for H-001.
    assert rec.payload["strength"] == pytest.approx(0.8870978737866234)
    assert rec.payload["verdict_refs"] == [v]
    assert rec.parents == (v,)
    assert "prev_state" not in rec.payload


def test_decisiveness_formula_values():
    from qrf.kernel.belief.belief import _decisiveness

    assert _decisiveness(0.5) == pytest.approx(0.0)          # coin-flip -> ~0
    assert _decisiveness(0.9435) == pytest.approx(0.887)     # H-001 -> 0.887
    assert _decisiveness(0.0001) == pytest.approx(0.9998)    # deflated PASS -> ~1
    assert _decisiveness(None) == 1.0                         # degenerate p -> max


def test_marginal_pass_uses_the_formula_not_p_as_strength(tmp_path):
    # DEVQ-016 rejected p-as-strength (a p=0.049 PASS would have claimed 0.951).
    # The ruled formula 2·|p−0.5| gives 0.902 here (the data sit far from a
    # coin-flip). NOTE: the ruling's worked example says 0.098 — an arithmetic
    # slip (2·|0.049−0.5| = 0.902); flagged in DEVQ-017. H-001 = 0.887 forces
    # this formula, so 0.902 is the correct value. Under real deflation a PASS
    # needs p <= effective_alpha (~1e-4), so genuine PASSes are near-maximally
    # decisive regardless.
    store = _store(tmp_path)
    v = _verdict(store, outcome="PASS", p=0.049)
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == SUPPORTED
    assert rec.payload["strength"] == pytest.approx(0.902)


def test_thin_evidence_pass_has_near_zero_strength(tmp_path):
    # A PASS whose p sits near 0.5 is decided but on thin evidence -> strength ~0.
    store = _store(tmp_path)
    v = _verdict(store, outcome="PASS", p=0.5)
    rec = BeliefLayer(store).update(v, claim=CLAIM, family=FAMILY)
    assert rec.payload["stance"] == SUPPORTED
    assert rec.payload["strength"] == pytest.approx(0.0)


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
    # Two AGREEING decisive verdicts (both FAIL): newest-decisive stance, appended.
    store = _store(tmp_path)
    v1 = _verdict(store, outcome="FAIL", p=0.8)
    beliefs = BeliefLayer(store)
    s1 = beliefs.update(v1, claim=CLAIM, family=FAMILY)
    v2 = _verdict(store, outcome="FAIL", p=0.95)  # a later, more decisive FAIL
    s2 = beliefs.update(v2, claim=CLAIM, family=FAMILY)
    assert s2.record_id != s1.record_id
    assert s2.payload["stance"] == REJECTED  # they agree -> still rejected
    assert s2.payload["strength"] == pytest.approx(0.9)  # 2·|0.95−0.5|, newest
    assert s2.payload["verdict_refs"] == [v1, v2]
    assert s2.payload["prev_state"] == s1.record_id
    assert BeliefLayer(store).latest(FAMILY, CLAIM).record_id == s2.record_id
    assert store.get(s1.record_id).payload["strength"] == pytest.approx(0.6)  # untouched


# --- CONTESTED: decisive verdicts disagree (DEVQ-016 conflict rule) ----------
def test_pass_after_fail_is_contested(tmp_path):
    store = _store(tmp_path)
    v_fail = _verdict(store, outcome="FAIL", p=0.9)
    beliefs = BeliefLayer(store)
    s1 = beliefs.update(v_fail, claim=CLAIM, family=FAMILY)
    assert s1.payload["stance"] == REJECTED
    v_pass = _verdict(store, outcome="PASS", p=0.02)  # a later, decisive PASS
    s2 = beliefs.update(v_pass, claim=CLAIM, family=FAMILY)
    # recency does NOT win: the conflict is preserved as CONTESTED.
    assert s2.payload["stance"] == CONTESTED
    # strength = decisiveness of the NEWEST decisive verdict (the PASS).
    assert s2.payload["strength"] == pytest.approx(0.96)  # 2·|0.02−0.5|
    assert s2.payload["verdict_refs"] == [v_fail, v_pass]
    assert s2.payload["prev_state"] == s1.record_id


def test_fail_after_pass_is_also_contested(tmp_path):
    store = _store(tmp_path)
    beliefs = BeliefLayer(store)
    beliefs.update(_verdict(store, outcome="PASS", p=0.01), claim=CLAIM, family=FAMILY)
    s2 = beliefs.update(_verdict(store, outcome="FAIL", p=0.85), claim=CLAIM, family=FAMILY)
    assert s2.payload["stance"] == CONTESTED


# --- re-derivation under a changed formula (append-only) ---------------------
def test_rederive_appends_a_new_state_when_numbers_move(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.9435489368933117)
    beliefs = BeliefLayer(store)
    head = beliefs.update(v, claim=CLAIM, family=FAMILY)
    # Simulate a state sealed under the retired rule by hand-forcing its strength,
    # then re-derive: the current formula gives 0.887, which differs -> new state.
    # (We reach the retired value by appending a belief with the old p-as-strength.)
    old = store.append(
        "belief",
        {"family": FAMILY, "claim": CLAIM, "stance": REJECTED, "strength": 0.9435489368933117,
         "verdict_refs": [v], "prev_state": head.record_id},
        producer="belief", event_ts=1, parents=[v, head.record_id],
    )
    n = len(store)
    rederived = beliefs.rederive(FAMILY, CLAIM)
    assert rederived.record_id != old.record_id
    assert rederived.payload["strength"] == pytest.approx(0.8870978737866234)
    assert rederived.payload["prev_state"] == old.record_id
    assert rederived.payload["verdict_refs"] == [v]
    assert len(store) == n + 1
    # the retired state stays in the chain (append-only memory).
    assert store.get(old.record_id).payload["strength"] == pytest.approx(0.9435489368933117)


def test_rederive_is_idempotent(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.9)
    beliefs = BeliefLayer(store)
    beliefs.update(v, claim=CLAIM, family=FAMILY)  # already at current formula
    n = len(store)
    same = beliefs.rederive(FAMILY, CLAIM)
    assert len(store) == n  # nothing appended
    assert same.record_id == beliefs.latest(FAMILY, CLAIM).record_id


def test_rederive_missing_belief_returns_none(tmp_path):
    assert BeliefLayer(_store(tmp_path)).rederive(FAMILY, CLAIM) is None


def test_beliefs_isolate_by_family_and_claim(tmp_path):
    store = _store(tmp_path)
    v = _verdict(store, outcome="FAIL", p=0.8)
    beliefs = BeliefLayer(store)
    beliefs.update(v, claim=CLAIM, family=FAMILY)
    assert beliefs.latest("other/family", CLAIM) is None
    assert beliefs.latest(FAMILY, "other claim") is None
