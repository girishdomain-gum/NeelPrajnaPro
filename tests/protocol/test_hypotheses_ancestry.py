"""observatory_ancestry wiring on the hypothesis registry (ARCH-007 §4, DEVQ-014).

hypothesis v2.1 adds an optional ``observatory_ancestry`` = list of question ids;
the registry validates each id EXISTS and is a ``question`` record, and it is
refused on a non-v2 hypothesis.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

COST_MODELS = ["xauusd_retail_median"]


def _register_instrument(store, iid="smc.fvg"):
    reg = store.append(
        "instrument_registered",
        {"instrument_id": iid, "kind": "detector", "version": "0.1.0",
         "params_schema": {}, "code_ref": f"{iid}:0.1.0"},
        producer="human:bootstrap", event_ts=now_ns(),
    )
    store.append(
        "calibration",
        {"instrument_ref": reg.record_id, "suite_id": "s", "cases": [
            {"case_id": "c1", "kind": "planted_truth", "expected": 1, "got": 1, "pass": True}],
         "pass_rate_truth": 1.0, "silence_rate_noise": 1.0, "overall_pass": True},
        producer="calibration", event_ts=now_ns(), parents=[reg.record_id],
    )
    return reg.record_id


def _window(store):
    return store.append(
        "window",
        {"dataset": "xauusd_h1_full", "ts_start": 1000, "ts_end": 2000, "designation": "TRAINING"},
        producer="human:protocol", event_ts=now_ns(),
    ).record_id


def _question(store, scan_parent=None):
    # A question needs an anomaly_scan parent in production; for this unit the
    # parent is irrelevant to ancestry validation, so append parentless.
    return store.append(
        "question",
        {"observation": "weekend FVGs differ", "data_slice_refs": ["01S"],
         "candidate_hypothesis": "restrict intra-week", "evidence_refs": ["01V"],
         "origin": "observatory"},
        producer="observatory", event_ts=now_ns(),
    ).record_id


def _config(window_ref, **overrides):
    cfg = {
        "lineage": "h002_fvg_intraweek", "scope": "xauusd_h1", "window": window_ref,
        "instruments": ["smc.fvg@0.1.0"],
        "setup_dsl": {"event": "smc.fvg", "direction": "follow_through"},
        "execution": {"hold_bars": 4, "size": 1.0, "strength_min": 0.0,
                      "stop_offset": None, "target_offset": None},
        "cost_model_ref": "xauusd_retail_median",
        "split_spec": {"n_folds": 4, "embargo_bars": 8},
        "thresholds": {"min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
        "thesis": "Intra-week FVGs follow through.",
        "outcome_interpretations": {"PASS": "edge", "FAIL": "no edge", "INSUFFICIENT": "too few"},
        "family": "xauusd_h1/smc.fvg",
    }
    cfg.update(overrides)
    return cfg


@pytest.fixture
def store(tmp_path):
    s = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(s)
    return s


def test_ancestry_recorded_when_valid(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    q = _question(store)
    rec = reg.register(_config(w, observatory_ancestry=[q]), cost_model_refs=COST_MODELS)
    assert rec.payload["observatory_ancestry"] == [q]
    assert rec.schema_version == 2


def test_ancestry_absent_is_fine(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert "observatory_ancestry" not in rec.payload


def test_ancestry_id_must_exist(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation):
        reg.register(
            _config(w, observatory_ancestry=["01DOESNOTEXIST"]), cost_model_refs=COST_MODELS
        )


def test_ancestry_id_must_be_a_question(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    # point at the window record — a real id, wrong type.
    with pytest.raises(SchemaViolation):
        reg.register(_config(w, observatory_ancestry=[w]), cost_model_refs=COST_MODELS)


def test_ancestry_requires_v2(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    q = _question(store)
    # strip the v2 pre-commitments but keep ancestry -> refused.
    cfg = _config(w, observatory_ancestry=[q])
    for k in ("thesis", "outcome_interpretations", "family"):
        cfg.pop(k)
    with pytest.raises(SchemaViolation):
        reg.register(cfg, cost_model_refs=COST_MODELS)
