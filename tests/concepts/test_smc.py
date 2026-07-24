"""SMC detector tests (ARCH-004 §4, Blueprint §4.3).

Covers, for both smc.fvg and smc.order_block: planted truth found, structured-
noise silence, insufficient silence; zone validity (zone_hi >= zone_lo); the
incremental-consistency (anti-hindsight) property; calibration through the
registry/harness with the uncalibrated-call refusal; and the pinned library
version recorded in the instrument_registered payload.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from qrf.kernel.errors import SchemaViolation, UncalibratedInstrumentError
from qrf.kernel.instruments.base import validate_event_frame
from qrf.kernel.instruments.calibration import CalibrationHarness, descriptors
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import (
    SMC_VERSION,
    SMCFVGDetector,
    SMCOrderBlockDetector,
)
from qrf.trading.concepts.smc.fixtures import (
    STEP,
    TS0,
    fvg_cases,
    order_block_cases,
)

DETECTORS = [
    (SMCFVGDetector(), fvg_cases()),
    (SMCOrderBlockDetector(params={"swing_length": 3}), order_block_cases(swing_length=3)),
]


# --- planted cases (direct detect) -------------------------------------------
@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["fvg", "order_block"])
def test_planted_cases_match_hand_truth(detector, cases):
    for case in cases:
        got = descriptors(detector.detect(case.data))
        assert got == case.expected, f"{case.case_id}: {got} != {case.expected}"


@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["fvg", "order_block"])
def test_noise_and_insufficient_are_silent(detector, cases):
    for case in cases:
        if case.kind in ("planted_noise", "insufficient"):
            assert descriptors(detector.detect(case.data)) == []


# --- zone validity -----------------------------------------------------------
@pytest.mark.parametrize("detector,cases", DETECTORS, ids=["fvg", "order_block"])
def test_zone_hi_ge_zone_lo_on_truth(detector, cases):
    for case in cases:
        ef = detector.detect(case.data)
        validate_event_frame(ef)  # enforces zone_hi >= zone_lo already
        hi = ef.column("zone_hi").to_pylist()
        lo = ef.column("zone_lo").to_pylist()
        for h, low in zip(hi, lo, strict=True):
            assert h is not None and low is not None and h >= low


def test_fvg_bull_zone_matches_hand_values():
    ef = SMCFVGDetector().detect(fvg_cases()[0].data)
    row = ef.to_pylist()[0]
    # Bullish gap: Bottom = high[0] = 10, Top = low[2] = 12.0.
    assert row["zone_lo"] == pytest.approx(10.0)
    assert row["zone_hi"] == pytest.approx(12.0)
    assert row["level"] == pytest.approx(11.0)


# --- incremental consistency (anti-hindsight) --------------------------------
def _emit_set(detector, table):
    return {(d["ts"], d["event_type"], d["direction"]) for d in descriptors(detector.detect(table))}


@pytest.mark.parametrize(
    "detector,case_index",
    [
        (SMCFVGDetector(), 0),
        (SMCFVGDetector(), 1),
        (SMCOrderBlockDetector(params={"swing_length": 3}), 0),
        (SMCOrderBlockDetector(params={"swing_length": 3}), 1),
    ],
    ids=["fvg_bull", "fvg_bear", "ob_bull", "ob_bear"],
)
def test_incremental_consistency(detector, case_index):
    cases = detector.planted_cases()
    table = cases[case_index].data
    n = table.num_rows
    full = _emit_set(detector, table)
    assert full, "expected at least one event in the truth case"

    # Every full-frame event's knowability index (derived from its ts).
    know = {e: (e[0] - TS0) // STEP for e in full}

    prev: set = set()
    for p in range(1, n + 1):
        emitted = _emit_set(detector, table.slice(0, p))
        # Monotone: nothing an earlier prefix emitted ever disappears.
        assert prev <= emitted, f"event vanished at prefix {p}"
        # Exactly the events whose knowability bar is inside this prefix.
        expected = {e for e, k in know.items() if k <= p - 1}
        assert emitted == expected, f"prefix {p}: {emitted} != {expected}"
        prev = emitted

    # Each event first appears exactly at its knowability bar, not before.
    for e, k in know.items():
        assert e not in _emit_set(detector, table.slice(0, k))       # absent at k bars
        assert e in _emit_set(detector, table.slice(0, k + 1))       # present at k+1 bars


# --- calibration through the registry + harness ------------------------------
@pytest.mark.parametrize(
    "detector",
    [SMCFVGDetector(), SMCOrderBlockDetector(params={"swing_length": 3})],
    ids=["fvg", "order_block"],
)
def test_calibration_passes_and_gates(tmp_path, detector):
    store = RecordStore(tmp_path / "journal.jsonl")
    registry = InstrumentRegistry(store)
    harness = CalibrationHarness(store, registry)

    reg = registry.register(detector)
    # Uncalibrated: the gate refuses use before a passing calibration exists.
    with pytest.raises(UncalibratedInstrumentError):
        registry.require_calibrated(reg.record_id)

    cal = harness.run(detector, detector.planted_cases(), suite_id="smc.s4")
    assert cal.payload["overall_pass"] is True
    assert cal.payload["pass_rate_truth"] == 1.0
    assert cal.payload["silence_rate_noise"] == 1.0
    registry.require_calibrated(reg.record_id)  # now passes, no raise


# --- version pin recorded ----------------------------------------------------
@pytest.mark.parametrize(
    "detector",
    [SMCFVGDetector(), SMCOrderBlockDetector(params={"swing_length": 3})],
    ids=["fvg", "order_block"],
)
def test_library_version_pin_in_registration(tmp_path, detector):
    store = RecordStore(tmp_path / "journal.jsonl")
    reg = InstrumentRegistry(store).register(detector)
    code_ref = reg.payload["code_ref"]
    assert f"smartmoneyconcepts=={SMC_VERSION}" in code_ref
    assert SMC_VERSION == "0.0.27"


def test_detect_requires_columns():
    with pytest.raises(SchemaViolation):
        SMCFVGDetector().detect(pa.table({"ts": [1, 2, 3]}))  # missing OHLC
