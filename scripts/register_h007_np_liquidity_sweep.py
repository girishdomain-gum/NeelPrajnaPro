"""NP-S1 deliverable 3 — register the neelprajna liquidity_sweep instrument and
its two sealed H-007 hypotheses (NP-ADR-008 §5 v1.1): the prediction claim and
the E2 existence claim. Registration only — does NOT run the EvidenceBattery.

**Ordering trap (ops/DEVELOPER_BOOT_NP-S1_RESUME.md):** the Battery run
(deliverable 4) must NOT happen until all 19 family trials are registered
(deliverable 6, the 17 counted-only entries, currently held behind DEVQ-NP-003
— see docs/coordination/inbox/OPEN/). This script only performs the two H-007
registrations; it deliberately does not run the Battery.

Idempotent: re-running after the instrument/hypotheses already exist reports
and writes nothing new (InstrumentRegistry/HypothesisRegistry's own idempotency).

Run:  .venv/Scripts/python.exe scripts/register_h007_np_liquidity_sweep.py
"""

from __future__ import annotations

from qrf.kernel.instruments.calibration import CalibrationHarness
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.protocol.hypotheses import HypothesisRegistry
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector
from qrf.trading.utility import cost_models

JOURNAL = "datastore/journal/journal.jsonl"
PREDICTION_YAML = "configs/hypotheses/h007_np_liquidity_sweep_v1_1_prediction.yaml"
E2_YAML = "configs/hypotheses/h007_np_liquidity_sweep_v1_1_e2_existence.yaml"


def _existing_registration(store: RecordStore, iid: str, ver: str) -> Record | None:
    # InstrumentRegistry.register() is NOT idempotent by itself (it always
    # appends) and a fresh registry's in-memory index has no knowledge of
    # instruments registered by a prior process run — the idempotency check
    # must query the store directly, matching scripts/bootstrap_smc_s4.py's
    # own convention.
    for r in store.query(record_type="instrument_registered"):
        if r.payload["instrument_id"] == iid and r.payload["version"] == ver:
            return r
    return None


def _register_and_calibrate_instrument(store: RecordStore) -> None:
    registry = InstrumentRegistry(store)
    harness = CalibrationHarness(store, registry)
    detector = LiquiditySweepDetector()

    existing = _existing_registration(store, detector.instrument_id, detector.version)
    if existing is not None:
        print(f"instrument already registered: {existing.record_id}")
        return  # a prior run's calibration (if any) also already exists; nothing to do

    reg = registry.register(detector, producer="human:girish")
    print(f"registered instrument {detector.instrument_id}@{detector.version} = {reg.record_id}")

    cal = harness.run(detector, detector.planted_cases(), suite_id="neelprajna.np_s1")
    print(
        f"calibration {cal.record_id}: overall_pass={cal.payload['overall_pass']} "
        f"pass_rate_truth={cal.payload['pass_rate_truth']} "
        f"silence_rate_noise={cal.payload['silence_rate_noise']}"
    )
    if not cal.payload["overall_pass"]:
        raise SystemExit(f"calibration FAILED for {detector.instrument_id}@{detector.version}")
    registry.require_calibrated(reg.record_id)  # raises if the calibration didn't pass


def _register_hypothesis(store: RecordStore, config_path: str) -> None:
    registry = HypothesisRegistry(store)
    config = registry.load_config(config_path)
    available = cost_models.available()
    hyp = registry.register(config, cost_model_refs=available, producer="human:girish")
    print(f"hypothesis {config['lineage']} ({config_path}) = {hyp.record_id}")


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    n_before = len(store)

    _register_and_calibrate_instrument(store)
    _register_hypothesis(store, PREDICTION_YAML)
    _register_hypothesis(store, E2_YAML)

    report = store.verify()
    print(
        f"journal verify ok={report.ok} n_records={len(store)} "
        f"(+{len(store) - n_before}) head={report.head_hash[:12]}"
    )


if __name__ == "__main__":
    main()
