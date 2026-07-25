"""Schemas for the Sprint-7 observatory + belief record types (ARCH-007).

anomaly_scan / question / belief are validated by shape here; the closed key set
is the type-audit that a question cannot carry a threshold/verdict/burn and a
belief cannot carry non-verdict fields. Divergence from Blueprint §2 is DEVQ-016.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records import schemas


def _valid_anomaly_scan() -> dict:
    return {
        "family": "xauusd_h1/smc.fvg",
        "window_ref": "01WIN",
        "manifest_refs": ["01MAN"],
        "method": "fvg.weekend_partition@h4",
        "seed": 20260725,
        "findings": {"n_events": 105, "partitions": {}},
        "n_searched": 1,
    }


def _valid_question() -> dict:
    return {
        "observation": "weekend-spanning FVGs behave differently",
        "data_slice_refs": ["01SLICE"],
        "candidate_hypothesis": "restrict FVG to intra-week",
        "evidence_refs": ["01VERDICT", "01TRADES"],
        "origin": "observatory",
    }


def _valid_belief() -> dict:
    return {
        "family": "xauusd_h1/smc.fvg",
        "claim": "naive FVG follow-through is profitable",
        "stance": "REJECTED",
        "strength": 0.94,
        "verdict_refs": ["01VERDICT"],
    }


# --- anomaly_scan ------------------------------------------------------------
def test_anomaly_scan_accepts_valid():
    schemas.validate("anomaly_scan", _valid_anomaly_scan())


def test_anomaly_scan_requires_positive_n_searched():
    p = _valid_anomaly_scan() | {"n_searched": 0}
    with pytest.raises(SchemaViolation):
        schemas.validate("anomaly_scan", p)


def test_anomaly_scan_rejects_empty_manifest_refs():
    p = _valid_anomaly_scan() | {"manifest_refs": []}
    with pytest.raises(SchemaViolation):
        schemas.validate("anomaly_scan", p)


def test_anomaly_scan_rejects_negative_seed():
    p = _valid_anomaly_scan() | {"seed": -1}
    with pytest.raises(SchemaViolation):
        schemas.validate("anomaly_scan", p)


def test_anomaly_scan_rejects_unknown_key():
    p = _valid_anomaly_scan() | {"verdict": "PASS"}
    with pytest.raises(SchemaViolation):
        schemas.validate("anomaly_scan", p)


# --- question (type-audit: no thresholds/verdict/burn) -----------------------
def test_question_accepts_valid():
    schemas.validate("question", _valid_question())


def test_question_optional_priority_score():
    schemas.validate("question", _valid_question() | {"priority_score": 0.5})


def test_question_rejects_bad_origin():
    with pytest.raises(SchemaViolation):
        schemas.validate("question", _valid_question() | {"origin": "battery"})


@pytest.mark.parametrize("forbidden", ["thresholds", "verdict", "window_burn", "base_alpha"])
def test_question_cannot_carry_judgement_fields(forbidden):
    # The closed key set is the type-audit: a question pre-registers nothing.
    p = _valid_question() | {forbidden: "anything"}
    with pytest.raises(SchemaViolation):
        schemas.validate("question", p)


def test_question_requires_nonempty_observation():
    with pytest.raises(SchemaViolation):
        schemas.validate("question", _valid_question() | {"observation": "  "})


# --- belief ------------------------------------------------------------------
def test_belief_accepts_valid():
    schemas.validate("belief", _valid_belief())


def test_belief_accepts_contested_stance():
    # DEVQ-016: CONTESTED is a valid stance (decisive verdicts disagree).
    schemas.validate("belief", _valid_belief() | {"stance": "CONTESTED"})


def test_belief_contested_needs_a_verdict():
    with pytest.raises(SchemaViolation):
        schemas.validate("belief", _valid_belief() | {"stance": "CONTESTED", "verdict_refs": []})


def test_belief_accepts_untested_without_verdicts():
    schemas.validate(
        "belief",
        {"family": "f", "claim": "c", "stance": "UNTESTED", "strength": 0.0, "verdict_refs": []},
    )


def test_belief_decided_stance_needs_a_verdict():
    p = _valid_belief() | {"verdict_refs": []}
    with pytest.raises(SchemaViolation):
        schemas.validate("belief", p)


@pytest.mark.parametrize("bad", [-0.01, 1.01])
def test_belief_strength_bounds(bad):
    with pytest.raises(SchemaViolation):
        schemas.validate("belief", _valid_belief() | {"strength": bad})


def test_belief_rejects_bad_stance():
    with pytest.raises(SchemaViolation):
        schemas.validate("belief", _valid_belief() | {"stance": "MAYBE"})


def test_belief_optional_prev_state():
    schemas.validate("belief", _valid_belief() | {"prev_state": "01PRIOR"})
