"""Promoter — the four-gate graduation of a claim (ARCH-008 §2, G-1).

Acceptance: a promotion appends iff ALL four legs hold, and each missing/failing
leg is individually refused — so no promotion can exist in the journal without a
PASS verdict, a clean placebo, a second lens, and a non-contested belief. Built on
a REAL PASS verdict + real placebo in a scratch datastore.
"""

from __future__ import annotations

import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.battery.placebo import DIRECTION_PERMUTATION, PlaceboBattery
from qrf.kernel.belief.belief import BeliefLayer
from qrf.kernel.errors import GraduationRefused
from qrf.kernel.graduation import Promoter
from qrf.kernel.records.record import now_ns
from qrf.trading.simulator.engine import EventEngine
from tests.battery.test_battery import ZERO_COST, _designate, _hypothesis, _scratch
from tests.battery.test_placebo import _planted_directional

FAMILY = "synthetic/planted"
CLAIM = "the planted edge is real"


def _second_lens(store, overlap_manifest, *, source="second-broker-xauusd-h1"):
    return store.append(
        "second_lens",
        {
            "source_name": source,
            "overlap_manifest": overlap_manifest,
            "agreement_summary": {
                "n_overlap": 100, "n_agree": 98, "agreement_rate": 0.98, "notes": "synthetic",
            },
        },
        producer="human:owner", event_ts=now_ns(),
    ).record_id


def _pass_chain(tmp_path, *, drift=10.0, noise=0.0):
    """A real PASS verdict + clean placebo + SUPPORTED belief + second_lens.

    Returns (store, bulk, refs) where refs has hyp/verdict/placebo/lens/belief ids.
    """
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=240, drift=drift)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family=FAMILY)

    placebo = PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=DIRECTION_PERMUTATION, base_seed=20260725, n_runs=20,
    )
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
    )
    assert verdict.payload["verdict"] == "PASS"
    belief = BeliefLayer(store).update(verdict.record_id, claim=CLAIM, family=FAMILY)
    lens = _second_lens(store, verdict.payload["trades_manifest"])
    refs = {
        "hyp": hyp, "verdict": verdict.record_id, "placebo": placebo.record_id,
        "lens": lens, "belief": belief.record_id,
    }
    return store, bulk, refs


def _promote(store, refs, **overrides):
    kw = dict(
        family=FAMILY, claim=CLAIM, hypothesis_ref=refs["hyp"],
        verdict_ref=refs["verdict"], placebo_ref=refs["placebo"],
        second_lens_ref=refs["lens"], belief_ref=refs["belief"],
    )
    kw.update(overrides)
    return Promoter(store).promote(**kw)


def test_all_four_gates_hold_promotes(tmp_path):
    store, bulk, refs = _pass_chain(tmp_path)
    promo = _promote(store, refs)
    assert promo.record_type == "promotion"
    assert promo.payload["family"] == FAMILY and promo.payload["claim"] == CLAIM
    assert promo.payload["verdict_ref"] == refs["verdict"]
    assert set(promo.parents) == {refs["verdict"], refs["placebo"], refs["lens"], refs["belief"]}
    # A promotion does NOT add a belief stance — beliefs stay verdict-only.
    assert not [b for b in store.query(record_type="belief")
                if b.payload.get("stance") == "PROMOTED"]


def test_refused_without_pass_verdict(tmp_path):
    """Leg (a): a FAIL verdict cannot promote."""
    store, bulk = _scratch(tmp_path)
    # A noisy zero-drift setup so the verdict is a decisive FAIL, not INSUFFICIENT.
    from tests.battery.test_battery import _planted_bars_events
    bars, events = _planted_bars_events(n_events=240, drift=0.0, noise_sd=1.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family=FAMILY)
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
    )
    assert verdict.payload["verdict"] == "FAIL"
    placebo = PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=DIRECTION_PERMUTATION, base_seed=1, n_runs=20,
    )
    belief = BeliefLayer(store).update(verdict.record_id, claim=CLAIM, family=FAMILY)
    lens = _second_lens(store, verdict.payload["trades_manifest"] or _designate(store, bars))
    with pytest.raises(GraduationRefused, match="not PASS"):
        Promoter(store).promote(
            family=FAMILY, claim=CLAIM, hypothesis_ref=hyp, verdict_ref=verdict.record_id,
            placebo_ref=placebo.record_id, second_lens_ref=lens, belief_ref=belief.record_id,
        )


def test_refused_with_excess_placebo_passes(tmp_path):
    """Leg (b): a placebo showing excess null passes cannot promote."""
    store, bulk, refs = _pass_chain(tmp_path)
    # Hand-append a placebo_run OF THE SAME hypothesis with obviously-excess passes.
    bad_placebo = store.append(
        "placebo_run",
        {
            "hypothesis_ref": refs["hyp"], "method": DIRECTION_PERMUTATION, "seed": 0,
            "n_runs": 20, "outcomes": ["PASS"] * 15 + ["FAIL"] * 5, "n_pass": 15,
        },
        producer="placebo", event_ts=now_ns(), parents=[refs["hyp"]],
    ).record_id
    with pytest.raises(GraduationRefused, match="over-eager"):
        _promote(store, refs, placebo_ref=bad_placebo)


def test_refused_without_second_lens(tmp_path):
    """Leg (c): no second lens (a wrong-type ref) cannot promote."""
    store, bulk, refs = _pass_chain(tmp_path)
    with pytest.raises(GraduationRefused, match="second_lens"):
        _promote(store, refs, second_lens_ref=refs["verdict"])  # a verdict, not a lens


def test_refused_with_contested_belief(tmp_path):
    """Leg (d): a CONTESTED belief cannot promote."""
    store, bulk, refs = _pass_chain(tmp_path)
    contested = store.append(
        "belief",
        {
            "family": FAMILY, "claim": CLAIM, "stance": "CONTESTED", "strength": 0.5,
            "verdict_refs": [refs["verdict"]],
        },
        producer="belief", event_ts=now_ns(), parents=[refs["verdict"]],
    ).record_id
    with pytest.raises(GraduationRefused, match="CONTESTED"):
        _promote(store, refs, belief_ref=contested)


def test_refused_when_belief_does_not_cite_verdict(tmp_path):
    """Leg (d): the belief must cite the promotion's verdict."""
    store, bulk, refs = _pass_chain(tmp_path)
    stray = store.append(
        "belief",
        {
            "family": FAMILY, "claim": CLAIM, "stance": "SUPPORTED", "strength": 0.9,
            "verdict_refs": [refs["hyp"]],  # cites something that is not this verdict
        },
        producer="belief", event_ts=now_ns(), parents=[refs["hyp"]],
    ).record_id
    with pytest.raises(GraduationRefused, match="does not cite"):
        _promote(store, refs, belief_ref=stray)


def test_refused_when_placebo_is_of_another_hypothesis(tmp_path):
    """Leg (b): the placebo must be of the SAME hypothesis being promoted."""
    store, bulk, refs = _pass_chain(tmp_path)
    other_placebo = store.append(
        "placebo_run",
        {
            "hypothesis_ref": "some-other-hypothesis", "method": DIRECTION_PERMUTATION,
            "seed": 0, "n_runs": 20, "outcomes": ["FAIL"] * 20, "n_pass": 0,
        },
        producer="placebo", event_ts=now_ns(), parents=[refs["hyp"]],
    ).record_id
    with pytest.raises(GraduationRefused, match="of hypothesis"):
        _promote(store, refs, placebo_ref=other_placebo)
