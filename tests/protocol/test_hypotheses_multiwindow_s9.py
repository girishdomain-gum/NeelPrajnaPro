"""HypothesisRegistry — multi-window (schema v3) registration (ARCH-009 §4, DEVQ-022 A).

A v3 hypothesis binds to a ``window_refs`` LIST instead of a single ``window``: the
battery judges the union of disjoint windows (the non-contiguous 2024+2025 training
span H-004 needs). These tests exercise the registry's v3 path and its refusals —
the multi-window binding is sealed both in the payload and in the record parents.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation, TamperedHypothesisError
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

# Reuse the single-window fixtures verbatim (same instrument + config shape).
from tests.protocol.test_hypotheses import _config, _register_instrument  # noqa: F401

COST_MODELS = ["xauusd_retail_median"]


@pytest.fixture
def store(tmp_path):
    s = RecordStore(tmp_path / "journal.jsonl")
    _register_instrument(s, "smc.fvg")
    return s


def _window(store, ts_start, ts_end, designation="TRAINING", dataset="xauusd_h1_full"):
    return store.append(
        "window",
        {"dataset": dataset, "ts_start": ts_start, "ts_end": ts_end, "designation": designation},
        producer="human:protocol",
        event_ts=now_ns(),
    ).record_id


def _multi_config(refs, **overrides):
    """A v2 config re-pointed at a window_refs LIST (drop the single 'window')."""
    cfg = _config("PLACEHOLDER", v2=True)
    cfg.pop("window")
    cfg["window_refs"] = list(refs)
    cfg.update(overrides)
    return cfg


def test_multiwindow_registers_as_v3(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 3000, 4000)  # disjoint, later
    rec = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    assert rec.schema_version == 3
    # window binding sealed BOTH in the parents (ordered) and the payload list.
    assert rec.parents == (w1, w2)
    assert rec.payload["window_refs"] == [w1, w2]
    # v2 pre-commitments still present.
    assert rec.payload["family"] == "xauusd_h1/smc.fvg"


def test_multiwindow_idempotent(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 3000, 4000)
    rec = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    n = len(store)
    again = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    assert again.record_id == rec.record_id
    assert len(store) == n


def test_both_window_and_window_refs_refused(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    cfg = _multi_config([w1])
    cfg["window"] = w1  # both set
    with pytest.raises(SchemaViolation, match="both 'window' and 'window_refs'"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_overlapping_windows_refused(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2500)
    w2 = _window(store, 2000, 4000)  # overlaps w1 on [2000, 2500)
    with pytest.raises(SchemaViolation, match="overlap"):
        reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)


def test_touching_windows_allowed(store):
    """Half-open [a,b) and [b,c) touch at b but do not overlap — a valid union."""
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 2000, 3000)
    rec = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    assert rec.schema_version == 3


def test_window_refs_entry_not_a_window_refused(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    not_a_window = store.append(
        "note", {"text": "x"}, producer="t", event_ts=now_ns()
    ).record_id
    with pytest.raises(SchemaViolation, match="not a window"):
        reg.register(_multi_config([w1, not_a_window]), cost_model_refs=COST_MODELS)


def test_empty_window_refs_refused(store):
    reg = HypothesisRegistry(store)
    with pytest.raises(SchemaViolation, match="non-empty list"):
        reg.register(_multi_config([]), cost_model_refs=COST_MODELS)


def test_multiwindow_requires_v2_precommitments(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 3000, 4000)
    cfg = _multi_config([w1, w2])
    for k in ("thesis", "outcome_interpretations", "family"):
        cfg.pop(k)
    with pytest.raises(SchemaViolation, match="must declare the v2"):
        reg.register(cfg, cost_model_refs=COST_MODELS)


def test_verify_frozen_catches_window_list_edit(store):
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 3000, 4000)
    w3 = _window(store, 5000, 6000)
    rec = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    # unchanged config verifies clean
    reg.verify_frozen(rec.record_id, _multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    # a swapped window is a tamper (different parents => different id)
    with pytest.raises(TamperedHypothesisError):
        reg.verify_frozen(rec.record_id, _multi_config([w1, w3]), cost_model_refs=COST_MODELS)


def test_window_order_is_significant(store):
    """[w1, w2] and [w2, w1] are different hypotheses (parents order = seam order)."""
    reg = HypothesisRegistry(store)
    w1 = _window(store, 1000, 2000)
    w2 = _window(store, 3000, 4000)
    rec_a = reg.register(_multi_config([w1, w2]), cost_model_refs=COST_MODELS)
    rec_b = reg.register(_multi_config([w2, w1]), cost_model_refs=COST_MODELS)
    assert rec_a.record_id != rec_b.record_id
