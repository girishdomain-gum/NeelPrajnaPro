"""ARCH-009 §2 — placebo_method under the seal (judge side).

PlaceboBattery.run REFUSES a method that disagrees with the hypothesis's sealed
``placebo_method`` (SchemaViolation naming both), runs when they agree, and — the
grandfather path — runs a Wave-1-style hypothesis that never sealed the field
with whatever method the caller supplies (exactly as H-002/H-003 were judged).
"""

from __future__ import annotations

import pytest

from qrf.kernel.battery.placebo import (
    DIRECTION_PERMUTATION,
    ENTRY_TIME_SHUFFLE,
    PlaceboBattery,
)
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.record import now_ns
from qrf.trading.simulator.engine import EventEngine
from tests.battery.test_battery import ZERO_COST, _designate, _scratch
from tests.battery.test_placebo import _planted_directional


def _sealed_hypothesis(store, window_ref, placebo_method: str | None):
    """Append a v2 hypothesis, optionally sealing a ``placebo_method``."""
    payload = {
        "lineage": "planted", "scope": "synthetic",
        "instrument_refs": ["placeholder-instrument-ref"],
        "setup_dsl": {"event": "planted"},
        "execution": {"hold_bars": 1, "size": 1.0, "strength_min": 0.0,
                      "stop_offset": None, "target_offset": None},
        "cost_model_ref": "zero",
        "split_spec": {"n_folds": 4, "embargo_bars": 2},
        "thresholds": {"min_n": 100, "base_alpha": 0.05,
                       "correction": {"method": "bonferroni"}},
        "thesis": "A planted synthetic edge.",
        "outcome_interpretations": {"PASS": "edge present", "FAIL": "no edge",
                                    "INSUFFICIENT": "too few"},
        "family": "synthetic/planted",
    }
    if placebo_method is not None:
        payload["placebo_method"] = placebo_method
    return store.append(
        "hypothesis", payload, producer="human:composer", event_ts=now_ns(),
        parents=[window_ref], schema_version=2,
    ).record_id


def _run(store, bulk, hyp, bars, events, method):
    return PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=method, base_seed=20260726, n_runs=2,
    )


def test_judge_refuses_method_disagreeing_with_seal(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=50, drift=5.0)
    window = _designate(store, bars)
    hyp = _sealed_hypothesis(store, window, DIRECTION_PERMUTATION)
    with pytest.raises(SchemaViolation, match="placebo method mismatch"):
        _run(store, bulk, hyp, bars, events, ENTRY_TIME_SHUFFLE)


def test_judge_runs_when_method_agrees_with_seal(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=50, drift=5.0)
    window = _designate(store, bars)
    hyp = _sealed_hypothesis(store, window, DIRECTION_PERMUTATION)
    rec = _run(store, bulk, hyp, bars, events, DIRECTION_PERMUTATION)
    assert rec.payload["method"] == DIRECTION_PERMUTATION
    assert rec.parents == (hyp,)


def test_grandfathered_hypothesis_without_seal_runs_any_method(tmp_path):
    """A Wave-1-style record (no sealed placebo_method) is judged with the caller's
    method, unbroken by the new rule."""
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=50, drift=5.0)
    window = _designate(store, bars)
    hyp = _sealed_hypothesis(store, window, None)
    rec = _run(store, bulk, hyp, bars, events, ENTRY_TIME_SHUFFLE)
    assert rec.payload["method"] == ENTRY_TIME_SHUFFLE
