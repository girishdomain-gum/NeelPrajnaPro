"""CalibrationHarness tests (Blueprint §4.4/§2, ARCH-002 AC).

Calibration record field shape and rates; block-on-fail semantics; that the
record is parented to the registration and validates against the §2 schema.
"""

from __future__ import annotations

import pytest

from qrf.kernel.instruments.calibration import CalibrationHarness
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records import schemas
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.classical import RSIDetector
from qrf.trading.concepts.seasonality import SeasonalityDetector
from qrf.trading.concepts.seasonality import fixtures as SF


@pytest.fixture
def env(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    registry = InstrumentRegistry(store)
    return store, registry, CalibrationHarness(store, registry)


def test_calibration_record_fields(env):
    store, registry, harness = env
    det = RSIDetector()
    reg_rec = registry.register(det)
    rec = harness.run(det, det.planted_cases(), suite_id="rsi_v1")

    assert rec.record_type == "calibration"
    assert rec.schema_version == 1
    # Parented to the registration; instrument_ref is that record id.
    assert reg_rec.record_id in rec.parents
    p = rec.payload
    assert p["instrument_ref"] == reg_rec.record_id
    assert p["suite_id"] == "rsi_v1"
    assert p["overall_pass"] is True
    assert p["pass_rate_truth"] == 1.0
    assert p["silence_rate_noise"] == 1.0
    # One case per planted case, each with the §2 fields.
    assert len(p["cases"]) == 3
    kinds = {c["kind"] for c in p["cases"]}
    assert kinds == {"planted_truth", "planted_noise", "insufficient"}
    for c in p["cases"]:
        assert set(c) == {"case_id", "kind", "expected", "got", "pass"}
        assert isinstance(c["pass"], bool)

    # The payload validates against the registered calibration schema (I-4).
    schemas.validate("calibration", p, 1)
    # And it is durably on the chain.
    assert store.verify().ok


def test_producer_defaults_to_instrument_identity(env):
    _, registry, harness = env
    det = RSIDetector(version="0.3.1")
    registry.register(det)
    rec = harness.run(det, det.planted_cases())
    assert rec.producer == "classical.rsi@0.3.1"


def test_rates_reflect_partial_failure(env):
    """pass_rate_truth and silence_rate_noise are real fractions, not booleans."""
    _, registry, harness = env
    det = SeasonalityDetector(params=SF.CANONICAL_PARAMS)
    registry.register(det)
    cases = det.planted_cases()
    truth = next(c for c in cases if c.kind == "planted_truth")
    noise = next(c for c in cases if c.kind == "planted_noise")
    # Two truth cases: one correct, one with a broken expectation -> 0.5 rate.
    broken = type(truth)(
        case_id="broken", kind="planted_truth", data=truth.data,
        expected=[{"ts": 0, "event_type": "nope", "direction": 0}],
    )
    rec = harness.run(det, [truth, broken, noise])
    assert rec.payload["pass_rate_truth"] == 0.5
    assert rec.payload["silence_rate_noise"] == 1.0
    assert rec.payload["overall_pass"] is False


def test_calibration_requires_registration_first(env):
    _, registry, harness = env
    det = RSIDetector()
    # Not registered -> harness.run must fail looking up the ref.
    from qrf.kernel.errors import UnknownInstrumentError

    with pytest.raises(UnknownInstrumentError):
        harness.run(det, det.planted_cases())
