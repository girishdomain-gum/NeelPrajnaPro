"""ARCH-009 §2 — placebo_method under the content-hash seal (registry side).

DEVQ-018 ADDENDUM, forward-binding: a NEW hypothesis whose claim will be judged
with a placebo carries ``placebo_method`` inside its YAML, so the seal covers it;
registration REFUSES an unknown method. The grandfather path (Wave-1 records that
never carried the field) is exercised in the judge-side test and by the fact that
every existing v2 config here still validates without the field.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation, TamperedHypothesisError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.store import RecordStore
from tests.protocol.test_hypotheses import (
    COST_MODELS,
    _config,
    _register_instrument,
    _window,
)


@pytest.fixture
def store(tmp_path):
    s = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(s, "smc.fvg")
    return s


def test_register_seals_valid_placebo_method(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(
        _config(w, placebo_method="entry_time_shuffle"), cost_model_refs=COST_MODELS
    )
    assert rec.payload["placebo_method"] == "entry_time_shuffle"


def test_placebo_method_is_under_the_seal(store):
    """A changed placebo_method yields a different hypothesis id (the seal covers it)."""
    reg = HypothesisRegistry(store)
    w = _window(store)
    a = reg.register(_config(w, placebo_method="entry_time_shuffle"),
                     cost_model_refs=COST_MODELS)
    b = reg.register(_config(w, placebo_method="direction_permutation"),
                     cost_model_refs=COST_MODELS)
    assert a.record_id != b.record_id, "placebo_method must change the content-hash seal"


def test_register_refuses_unknown_placebo_method(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation, match="not a DEVQ-018 ruled null"):
        reg.register(_config(w, placebo_method="block_shuffle"), cost_model_refs=COST_MODELS)


def test_placebo_method_requires_v2(store):
    reg = HypothesisRegistry(store)
    w = _window(store)
    with pytest.raises(SchemaViolation, match="requires a v2 hypothesis"):
        reg.register(_config(w, v2=False, placebo_method="entry_time_shuffle"),
                     cost_model_refs=COST_MODELS)


def test_verify_frozen_detects_placebo_method_edit(store):
    """The seal binds the method: verifying against a different method is tamper."""
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(_config(w, placebo_method="entry_time_shuffle"), cost_model_refs=COST_MODELS)
    reg.verify_frozen(rec.record_id, _config(w, placebo_method="entry_time_shuffle"),
                      cost_model_refs=COST_MODELS)  # unchanged → OK
    with pytest.raises(TamperedHypothesisError):
        reg.verify_frozen(rec.record_id, _config(w, placebo_method="direction_permutation"),
                          cost_model_refs=COST_MODELS)


def test_wave1_style_config_without_field_still_registers(store):
    """Grandfather shape: a v2 config that omits placebo_method registers unchanged."""
    reg = HypothesisRegistry(store)
    w = _window(store)
    rec = reg.register(_config(w), cost_model_refs=COST_MODELS)
    assert "placebo_method" not in rec.payload
