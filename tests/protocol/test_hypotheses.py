"""HypothesisRegistry — pre-registration + its refusals (ARCH-006 §1, Blueprint §4.5).

Every registration validation is exercised, including the two named refusals the
instruction singles out: the order-block restatement gate (DEVQ-010) and the
embargo >= hold_bars + 1 boundary rule (DEVQ-011).
"""

from __future__ import annotations

import copy

import pytest

from qrf.kernel.errors import (
    SchemaViolation,
    TamperedHypothesisError,
    UncalibratedInstrumentError,
    UnknownInstrumentError,
    UnknownRecordError,
)
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

COST_MODELS = ["xauusd_retail_median"]


def _register_instrument(store, iid, version="0.1.0", *, calibrated=True):
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
    if calibrated:
        store.append(
            "calibration",
            {
                "instrument_ref": reg.record_id,
                "suite_id": f"{iid}.suite",
                "cases": [
                    {
                        "case_id": "c1", "kind": "planted_truth",
                        "expected": 1, "got": 1, "pass": True,
                    }
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


def _window(store):
    return store.append(
        "window",
        {"dataset": "xauusd_h1_full", "ts_start": 1000, "ts_end": 2000, "designation": "TRAINING"},
        producer="human:protocol",
        event_ts=now_ns(),
    ).record_id


def _config(window_ref, *, v2=True, **overrides):
    cfg = {
        "lineage": "h001_fvg_follow_through",
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
    }
    if v2:
        cfg.update(
            thesis="After an FVG forms, price follows through in its direction.",
            outcome_interpretations={
                "PASS": "The follow-through edge survives real costs.",
                "FAIL": "No net edge after costs — the pattern does not pay.",
                "INSUFFICIENT": "Too few trades to decide.",
            },
            family="xauusd_h1/smc.fvg",
        )
    cfg.update(overrides)
    return cfg


@pytest.fixture
def store(tmp_path):
    s = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(s, "smc.fvg")
    return s


def test_register_happy_path_and_idempotent(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert rec.record_type == "hypothesis"
    assert rec.schema_version == 2
    assert rec.parents == (w,)
    # instrument spec resolved to the registration record id.
    fvg_ref = next(r.record_id for r in store.query(record_type="instrument_registered"))
    assert rec.payload["instrument_refs"] == [fvg_ref]
    # v2 pre-commitments are on the record.
    assert rec.payload["family"] == "xauusd_h1/smc.fvg"
    assert set(rec.payload["outcome_interpretations"]) == {"PASS", "FAIL", "INSUFFICIENT"}
    assert rec.payload["thesis"].strip()
    # Idempotent: same config -> same record, no second append.
    n = len(store)
    again = reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert again.record_id == rec.record_id
    assert len(store) == n


def test_new_hypothesis_without_v2_fields_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation, match="thesis"):
        reg.register(_config(w, v2=False), cost_model_refs=COST_MODELS)


def test_partial_v2_fields_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    # Only thesis, no outcome_interpretations/family -> refused (all or none).
    cfg = _config(w, v2=False, thesis="a claim")
    with pytest.raises(SchemaViolation):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_order_block_refused_devq010(store):
    _register_instrument(store, "smc.order_block")
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation, match="DEVQ-010"):
        reg.register(_config(w, instruments=["smc.order_block@0.1.0"]), cost_model_refs=COST_MODELS)


def test_embargo_below_hold_plus_one_refused_devq011(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    # hold_bars=4 needs embargo >= 5; 4 is refused.
    cfg = _config(w, split_spec={"n_folds": 4, "embargo_bars": 4})
    with pytest.raises(SchemaViolation, match="DEVQ-011"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_unknown_cost_model_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation, match="DEVQ-008"):
        reg.register(_config(w, cost_model_ref="nonexistent_venue"), cost_model_refs=COST_MODELS)


def test_uncalibrated_instrument_refused(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(store, "smc.fvg", calibrated=False)
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(UncalibratedInstrumentError):
        reg.register(_config(w), cost_model_refs=COST_MODELS)


def test_unknown_instrument_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(UnknownInstrumentError):
        reg.register(_config(w, instruments=["smc.nonexistent@0.1.0"]), cost_model_refs=COST_MODELS)


def test_missing_or_wrong_window_refused(store):
    reg = HypothesisRegistry(store)
    # No window key.
    cfg = _config("x")
    del cfg["window"]
    with pytest.raises(SchemaViolation):
        reg.register(cfg, cost_model_refs=COST_MODELS)
    # Window ref that does not exist.
    with pytest.raises(UnknownRecordError):
        reg.register(_config("01KYNONEXISTENT00000000000"), cost_model_refs=COST_MODELS)


# --- ARCH-NP-004 §4.5 — per-trade stop / R-multiple target registration refusals ---
def test_target_r_multiple_without_stop_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "target_r_multiple": 1.5,
    })
    with pytest.raises(SchemaViolation, match="target_r_multiple requires a stop"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_event_stop_column_unsupported_by_eventframe_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "event_stop_column": "strength",
    })
    with pytest.raises(SchemaViolation, match="EventFrame cannot supply it"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_non_positive_stop_offset_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "stop_offset": 0.0,
    })
    with pytest.raises(SchemaViolation, match="stop_offset"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_non_finite_stop_offset_refused(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "stop_offset": float("inf"),
    })
    with pytest.raises(SchemaViolation, match="stop_offset"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_event_stop_column_and_stop_offset_mutually_exclusive(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "stop_offset": 2.0, "event_stop_column": "level",
    })
    with pytest.raises(SchemaViolation, match="mutually exclusive"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_target_offset_and_target_r_multiple_mutually_exclusive(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "stop_offset": 2.0,
        "target_offset": 3.0, "target_r_multiple": 1.5,
    })
    with pytest.raises(SchemaViolation, match="mutually exclusive"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_valid_per_trade_stop_and_r_multiple_target_registers(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    cfg = _config(w, execution={
        "hold_bars": 4, "size": 1.0, "event_stop_column": "level", "target_r_multiple": 1.5,
    })
    rec = reg.register(cfg, cost_model_refs=COST_MODELS)
    assert rec.payload["execution"]["event_stop_column"] == "level"
    assert rec.payload["execution"]["target_r_multiple"] == 1.5


def test_verify_frozen_detects_tamper(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(_config(w), cost_model_refs=COST_MODELS)
    # Unchanged config verifies.
    reg.verify_frozen(rec.record_id, _config(w), cost_model_refs=COST_MODELS)
    # A changed field (different hold_bars, matched embargo) no longer matches.
    tampered = copy.deepcopy(_config(w))
    tampered["execution"]["hold_bars"] = 2
    with pytest.raises(TamperedHypothesisError):
        reg.verify_frozen(rec.record_id, tampered, cost_model_refs=COST_MODELS)
    # A changed v2 pre-commitment (the thesis) is also a re-registration, not a mutation.
    tampered2 = copy.deepcopy(_config(w))
    tampered2["thesis"] = "a different claim entirely"
    with pytest.raises(TamperedHypothesisError):
        reg.verify_frozen(rec.record_id, tampered2, cost_model_refs=COST_MODELS)


def test_changed_v2_field_registers_new_id(store):
    """Editing a v2 pre-commitment yields a NEW hypothesis id (not a mutation)."""
    reg = HypothesisRegistry(store)
    w = _window(store)
    a = reg.register(_config(w), cost_model_refs=COST_MODELS)
    b = reg.register(
        _config(w, thesis="A sharper, different one-sentence claim."),
        cost_model_refs=COST_MODELS,
    )
    assert a.record_id != b.record_id
