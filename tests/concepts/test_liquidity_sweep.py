"""LiquiditySweepDetector tests (NP-ADR-008 §3, v1.1: POOL_FORMED -> SWEEP only).

Planted-truth exact events/ts on both sides (immediate + delayed reclose);
clean-control and insufficient-data silence; the anti-hindsight incremental-
consistency property; EventFrame schema conformance; no third event ever
(REVERSAL_CONFIRMED does not exist in this lineage).
"""

from __future__ import annotations

import json

import pytest

from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.instruments.calibration import descriptors
from qrf.trading.concepts.neelprajna import LiquiditySweepDetector
from qrf.trading.concepts.neelprajna import fixtures as LF


def _det():
    return LiquiditySweepDetector()


def test_pool_and_immediate_sweep_exact_events():
    det = _det()
    case = LF.liquidity_sweep_cases()[0]
    assert case.case_id == "pool_and_immediate_sweep"
    got = descriptors(det.detect(case.data))
    assert got == case.expected
    assert len(got) == 2


def test_low_pool_delayed_reclose_exact_events():
    det = _det()
    case = LF.liquidity_sweep_cases()[1]
    assert case.case_id == "low_pool_delayed_reclose"
    got = descriptors(det.detect(case.data))
    assert got == case.expected
    assert len(got) == 2


def test_sweep_meta_reports_reclose_bars_and_penetration():
    det = _det()
    frame = det.detect(LF.CASE_1_POOL_AND_IMMEDIATE_SWEEP)
    metas = [json.loads(m) for m in frame.column("meta").to_pylist()]
    sweep_meta = [m for m in metas if "reclose_bars" in m][0]
    assert sweep_meta["reclose_bars"] == 0
    assert sweep_meta["penetration_ticks"] == pytest.approx(15.0)

    frame2 = det.detect(LF.CASE_2_LOW_POOL_DELAYED_RECLOSE)
    metas2 = [json.loads(m) for m in frame2.column("meta").to_pylist()]
    sweep_meta2 = [m for m in metas2 if "reclose_bars" in m][0]
    assert sweep_meta2["reclose_bars"] == 2
    assert sweep_meta2["penetration_ticks"] == pytest.approx(15.0)


def test_flat_and_short_are_silent():
    det = _det()
    for case in LF.liquidity_sweep_cases():
        if case.kind == "planted_truth":
            continue
        assert det.detect(case.data).num_rows == 0


def test_output_is_valid_eventframe():
    det = _det()
    frame = det.detect(LF.CASE_1_POOL_AND_IMMEDIATE_SWEEP)
    validate_event_frame(frame)
    types = set(frame.column("event_type").to_pylist())
    assert types <= {
        "neelprajna.liquidity_sweep.pool_formed",
        "neelprajna.liquidity_sweep.sweep",
    }
    # No third event exists in this lineage (ADR §3) — never emitted, ever.
    assert "neelprajna.liquidity_sweep.reversal_confirmed" not in types


def test_incremental_consistency_property_both_cases():
    """Feeding prefixes never changes previously emitted events (anti-hindsight)."""
    det = _det()
    for data in (LF.CASE_1_POOL_AND_IMMEDIATE_SWEEP, LF.CASE_2_LOW_POOL_DELAYED_RECLOSE):
        ts_all = data.column("ts").to_pylist()
        full = descriptors(det.detect(data))
        for k in range(1, data.num_rows + 1):
            prefix = descriptors(det.detect(data.slice(0, k)))
            expected_prefix = [d for d in full if d["ts"] <= ts_all[k - 1]]
            assert prefix == expected_prefix, f"prefix k={k} diverged"


def test_params_are_frozen_defaults():
    det = _det()
    assert det.params == {
        "pivot_k": 3,
        "member_window_bars": 200,
        "pool_tol_ticks": 30.0,
        "min_pen_ticks": 5.0,
        "reclose_window_bars": 2,
        "tick_size": 0.01,
    }
    assert det.instrument_id == "neelprajna.liquidity_sweep"
    assert det.version == "1.1.0"
    assert det.family == "neelprajna"
