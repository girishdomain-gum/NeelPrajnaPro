"""neelprajna liquidity_sweep detector tests (NP-S1, NP-ADR-008 §5 v1.1, AC-1/AC-2).

Covers: planted truth found (single-bar sweep both sides, boundary-inclusive
2-bar reclose, invalidation-emits-no-sweep), structured-noise and insufficient
silence, zone validity (both events are point events -- zone_hi/zone_lo NaN),
the incremental-consistency (anti-hindsight) property, and calibration through
the registry/harness with the uncalibrated-call refusal.
"""

from __future__ import annotations

import math

import pyarrow as pa
import pytest

from qrf.kernel.errors import SchemaViolation, UncalibratedInstrumentError
from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.instruments.calibration import CalibrationHarness, descriptors
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.concepts.neelprajna.fixtures import STEP, TS0, liquidity_sweep_cases

DETECTORS = [(LiquiditySweepDetector(), liquidity_sweep_cases())]


# --- planted cases (direct detect) -------------------------------------------
@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["liquidity_sweep"])
def test_planted_cases_match_hand_truth(detector, cases):
    for case in cases:
        got = descriptors(detector.detect(case.data))
        assert got == case.expected, f"{case.case_id}: {got} != {case.expected}"


@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["liquidity_sweep"])
def test_noise_and_insufficient_are_silent(detector, cases):
    for case in cases:
        if case.kind in ("planted_noise", "insufficient"):
            assert descriptors(detector.detect(case.data)) == []


def test_invalidation_emits_pool_formed_but_no_sweep():
    case = next(c for c in liquidity_sweep_cases() if c.case_id == "high_pool_invalidation_truth")
    got = descriptors(LiquiditySweepDetector().detect(case.data))
    assert len(got) == 1
    assert got[0]["event_type"] == "neelprajna.liquidity_sweep.pool_formed"


def test_boundary_reclose_at_exactly_two_bars_is_a_sweep_not_invalidation():
    case = next(
        c for c in liquidity_sweep_cases() if c.case_id == "high_pool_two_bar_reclose_truth"
    )
    got = descriptors(LiquiditySweepDetector().detect(case.data))
    sweeps = [e for e in got if e["event_type"] == "neelprajna.liquidity_sweep.sweep"]
    assert len(sweeps) == 1
    assert sweeps[0]["ts"] == int(TS0 + 16 * STEP)


# --- zone validity (both events are point events) -----------------------------
@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["liquidity_sweep"])
def test_zone_is_nan_point_event_on_truth(detector, cases):
    for case in cases:
        ef = detector.detect(case.data)
        validate_event_frame(ef)  # NaN zones bypass zone_hi >= zone_lo trivially
        if case.kind != "planted_truth":
            continue
        hi = ef.column("zone_hi").to_pylist()
        lo = ef.column("zone_lo").to_pylist()
        for h, low in zip(hi, lo, strict=True):
            assert h is None or math.isnan(h)
            assert low is None or math.isnan(low)


def test_level_matches_pool_price_on_truth():
    case = next(
        c for c in liquidity_sweep_cases() if c.case_id == "high_pool_single_bar_sweep_truth"
    )
    ef = LiquiditySweepDetector().detect(case.data)
    rows = ef.to_pylist()
    for row in rows:
        assert row["level"] == pytest.approx(100.35)


# --- incremental consistency (anti-hindsight) --------------------------------
def _emit_set(detector, table):
    return {
        (d["ts"], d["event_type"], d["direction"]) for d in descriptors(detector.detect(table))
    }


@pytest.mark.parametrize(
    "case_id",
    [
        "high_pool_single_bar_sweep_truth",
        "low_pool_single_bar_sweep_truth",
        "high_pool_two_bar_reclose_truth",
        "high_pool_invalidation_truth",
    ],
)
def test_incremental_consistency(case_id):
    detector = LiquiditySweepDetector()
    case = next(c for c in liquidity_sweep_cases() if c.case_id == case_id)
    table = case.data
    n = table.num_rows
    full = _emit_set(detector, table)
    assert full, "expected at least one event in the truth case"

    know = {e: (e[0] - TS0) // STEP for e in full}

    prev: set = set()
    for p in range(1, n + 1):
        emitted = _emit_set(detector, table.slice(0, p))
        assert prev <= emitted, f"{case_id}: event vanished at prefix {p}"
        expected = {e for e, k in know.items() if k <= p - 1}
        assert emitted == expected, f"{case_id}: prefix {p}: {emitted} != {expected}"
        prev = emitted

    for e, k in know.items():
        assert e not in _emit_set(detector, table.slice(0, k))
        assert e in _emit_set(detector, table.slice(0, k + 1))


# --- calibration through the registry + harness ------------------------------
def test_calibration_passes_and_gates(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    registry = InstrumentRegistry(store)
    harness = CalibrationHarness(store, registry)
    detector = LiquiditySweepDetector()

    reg = registry.register(detector)
    with pytest.raises(UncalibratedInstrumentError):
        registry.require_calibrated(reg.record_id)

    cal = harness.run(detector, detector.planted_cases(), suite_id="neelprajna.np_s1")
    assert cal.payload["overall_pass"] is True
    assert cal.payload["pass_rate_truth"] == 1.0
    assert cal.payload["silence_rate_noise"] == 1.0
    registry.require_calibrated(reg.record_id)  # now passes, no raise


def test_provenance_hashes_in_code_ref():
    code_ref = LiquiditySweepDetector().code_ref
    assert "1a0b5d9f" in code_ref  # np_feature_service.py sha256 prefix
    assert "a9b75aeb" in code_ref  # np_probability_engine.py sha256 prefix


def test_detect_requires_columns():
    with pytest.raises(SchemaViolation):
        LiquiditySweepDetector().detect(pa.table({"ts": [1, 2, 3]}))  # missing high/low/close


def test_params_are_frozen_not_constructor_configurable():
    # No `params=` kwarg exists on this detector's constructor -- the frozen
    # values are hard-coded, not CLI defaults (NP-ADR-008 SS3 identity).
    with pytest.raises(TypeError):
        LiquiditySweepDetector(params={"pool_tol_ticks": 99.0})  # type: ignore[call-arg]
