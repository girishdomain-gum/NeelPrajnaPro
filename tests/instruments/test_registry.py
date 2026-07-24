"""InstrumentRegistry tests (Blueprint §4.4, ARCH-002 AC).

Registry round-trip; the calibration gate (uncalibrated use refused, no
soft-pass); and version-bump forcing recalibration.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import UncalibratedInstrumentError, UnknownInstrumentError
from qrf.kernel.instruments.calibration import CalibrationHarness
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.classical import RSIDetector


@pytest.fixture
def store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


@pytest.fixture
def registry(store):
    return InstrumentRegistry(store)


def test_register_roundtrip(store, registry):
    det = RSIDetector()
    rec = registry.register(det)
    assert rec.record_type == "instrument_registered"
    assert rec.payload["instrument_id"] == "classical.rsi"
    assert rec.payload["version"] == det.version
    assert rec.payload["kind"] == "detector"
    assert rec.payload["params_schema"] == det.params_schema
    # get() returns the same info; ref is the registration record id.
    info = registry.get("classical.rsi")
    assert info.record_id == rec.record_id
    assert info.version == det.version
    assert registry.info_for_ref(rec.record_id).instrument_id == "classical.rsi"


def test_get_unknown_instrument_raises(registry):
    with pytest.raises(UnknownInstrumentError):
        registry.get("nope.detector")


def test_is_calibrated_false_before_calibration(store, registry):
    ref = registry.register(RSIDetector()).record_id
    assert registry.is_calibrated(ref) is False


def test_require_calibrated_refuses_uncalibrated(store, registry):
    det = RSIDetector()
    ref = registry.register(det).record_id
    with pytest.raises(UncalibratedInstrumentError):
        registry.require_calibrated(ref)
    with pytest.raises(UncalibratedInstrumentError):
        registry.run_detector(ref, det.planted_cases()[0].data)


def test_gate_opens_after_passing_calibration(store, registry):
    det = RSIDetector()
    ref = registry.register(det).record_id
    CalibrationHarness(store, registry).run(det, det.planted_cases())
    assert registry.is_calibrated(ref) is True
    events = registry.run_detector(ref, det.planted_cases()[0].data)
    assert events.num_rows == 2  # the two planted crossings


def test_failed_calibration_does_not_open_gate(store, registry):
    """No soft-pass: a calibration whose truth case fails must NOT calibrate."""
    det = RSIDetector()
    ref = registry.register(det).record_id
    # Feed the truth case a WRONG expectation so it fails.
    cases = det.planted_cases()
    good_truth = cases[0]
    bad = type(good_truth)(
        case_id=good_truth.case_id,
        kind="planted_truth",
        data=good_truth.data,
        expected=[{"ts": 1, "event_type": "wrong", "direction": 0}],
    )
    rec = CalibrationHarness(store, registry).run(det, [bad, cases[1], cases[2]])
    assert rec.payload["overall_pass"] is False
    assert rec.payload["pass_rate_truth"] == 0.0
    assert registry.is_calibrated(ref) is False
    with pytest.raises(UncalibratedInstrumentError):
        registry.require_calibrated(ref)


def test_version_bump_forces_recalibration(store, registry):
    det_v1 = RSIDetector(version="0.1.0")
    ref_v1 = registry.register(det_v1).record_id
    CalibrationHarness(store, registry).run(det_v1, det_v1.planted_cases())
    assert registry.is_calibrated(ref_v1) is True

    # A new version is a new registration record -> a new ref -> uncalibrated.
    det_v2 = RSIDetector(version="0.2.0")
    ref_v2 = registry.register(det_v2).record_id
    assert ref_v2 != ref_v1
    assert registry.get("classical.rsi").version == "0.2.0"  # latest
    assert registry.is_calibrated(ref_v2) is False
    with pytest.raises(UncalibratedInstrumentError):
        registry.require_calibrated(ref_v2)

    # Calibrating v2 opens only v2's gate; v1 remains calibrated independently.
    CalibrationHarness(store, registry).run(det_v2, det_v2.planted_cases())
    assert registry.is_calibrated(ref_v2) is True
    assert registry.is_calibrated(ref_v1) is True


def test_max_age_days_staleness(store, registry):
    """A calibration older than max_age_days no longer counts."""
    det = RSIDetector()
    ref = registry.register(det).record_id
    # event_ts 10 days in the past (deterministic, not wall-clock dependent here).
    from qrf.kernel.records.record import now_ns

    old_ts = now_ns() - 10 * 86_400 * 1_000_000_000
    CalibrationHarness(store, registry).run(det, det.planted_cases(), event_ts=old_ts)
    assert registry.is_calibrated(ref) is True  # no age bound
    assert registry.is_calibrated(ref, max_age_days=30) is True
    assert registry.is_calibrated(ref, max_age_days=5) is False


def test_is_calibrated_unknown_ref_raises(registry):
    with pytest.raises(UnknownInstrumentError):
        registry.is_calibrated("01NOSUCHREF")
