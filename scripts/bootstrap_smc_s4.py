"""Bootstrap the Sprint-4 SMC detectors into the real journal (ARCH-004 §4).

Registers and calibrates both SMC detectors through the real journal, so the
ledger holds their ``instrument_registered`` (with the pinned
``smartmoneyconcepts`` version in ``code_ref``) and passing ``calibration``
records. Idempotent: if both are already registered it reports the ids and
writes nothing.

Run:  uv run python scripts/bootstrap_smc_s4.py
"""

from __future__ import annotations

from qrf.kernel.instruments.calibration import CalibrationHarness
from qrf.kernel.instruments.registry import InstrumentRegistry
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.smc.detector import SMCFVGDetector, SMCOrderBlockDetector

JOURNAL = "datastore/journal/journal.jsonl"
SWING_LENGTH = 3


def _existing_registration(store: RecordStore, iid: str, ver: str) -> Record | None:
    for r in store.query(record_type="instrument_registered"):
        if r.payload["instrument_id"] == iid and r.payload["version"] == ver:
            return r
    return None


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    detectors = [
        SMCFVGDetector(),
        SMCOrderBlockDetector(params={"swing_length": SWING_LENGTH}),
    ]

    if all(_existing_registration(store, d.instrument_id, d.version) for d in detectors):
        print("already bootstrapped; existing registrations:")
        for d in detectors:
            reg = _existing_registration(store, d.instrument_id, d.version)
            print(f"  {d.instrument_id}@{d.version} instrument_registered={reg.record_id}")
        return

    registry = InstrumentRegistry(store)
    harness = CalibrationHarness(store, registry)
    for d in detectors:
        reg = registry.register(d, producer="human:girish")
        cal = harness.run(d, d.planted_cases(), suite_id=f"{d.instrument_id}.s4")
        if not cal.payload["overall_pass"]:
            raise SystemExit(f"calibration FAILED for {d.instrument_id}@{d.version}")
        assert registry.is_calibrated(reg.record_id)
        print(
            f"{d.instrument_id}@{d.version}: instrument_registered={reg.record_id} "
            f"calibration={cal.record_id} "
            f"(truth={cal.payload['pass_rate_truth']} silence={cal.payload['silence_rate_noise']}) "
            f"code_ref={reg.payload['code_ref']}"
        )

    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()
