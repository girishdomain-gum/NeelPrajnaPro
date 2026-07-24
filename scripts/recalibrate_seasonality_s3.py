"""ARCH-003 — recalibrate the seasonality detector with the gapped-feed case.

The seasonality suite gained a gapped-feed planted-truth case (first bar of each
day at 01:00, no midnight bar; DEVQ-005 ratified contract). This appends a fresh
``calibration`` record over the FULL expanded suite, parented to the detector's
EXISTING Sprint-2 registration (record 01KYAKYY1298M1N3JWAA8HBQ5P) — same
instrument, same version, strengthened suite. No new registration is minted.

The harness resolves the instrument_ref via its registry; here we feed it a
minimal ref-stub that returns the existing registration id (rebuilding the whole
in-memory registry is unnecessary and re-``register()`` would wrongly mint a
second registration record). The harness itself does the comparison and append,
so the calibration record is produced through the sanctioned code path.

Idempotent: if a calibration over this suite already exists for the ref, report
and write nothing.

Run:  uv run python scripts/recalibrate_seasonality_s3.py
"""

from __future__ import annotations

from types import SimpleNamespace

from qrf.kernel.instruments.calibration import CalibrationHarness
from qrf.kernel.records.store import RecordStore
from qrf.trading.concepts.seasonality import SeasonalityDetector
from qrf.trading.concepts.seasonality import fixtures as SF

JOURNAL = "datastore/journal/journal.jsonl"
SUITE_ID = "seasonality.calendar.s3"  # expanded suite incl. gapped-feed case


class _RefStub:
    """Minimal registry surface: hand the harness the existing instrument_ref."""

    def __init__(self, ref: str) -> None:
        self._ref = ref

    def get(self, instrument_id: str, version: str | None = None):  # noqa: ARG002
        return SimpleNamespace(record_id=self._ref)


def _existing_registration(store: RecordStore, iid: str, ver: str) -> str | None:
    for r in store.query(record_type="instrument_registered"):
        if r.payload["instrument_id"] == iid and r.payload["version"] == ver:
            return r.record_id
    return None


def main() -> None:
    store = RecordStore(JOURNAL)  # verifies chain on open
    det = SeasonalityDetector(params=SF.CANONICAL_PARAMS)

    ref = _existing_registration(store, det.instrument_id, det.version)
    if ref is None:
        raise SystemExit(
            f"no registration for {det.instrument_id}@{det.version}; "
            "run scripts/bootstrap_s2_instruments.py first"
        )

    for r in store.query(record_type="calibration"):
        if r.payload.get("instrument_ref") == ref and r.payload.get("suite_id") == SUITE_ID:
            print(f"already recalibrated: calibration {r.record_id} (suite {SUITE_ID})")
            return

    harness = CalibrationHarness(store, _RefStub(ref))
    cases = det.planted_cases()
    cal = harness.run(det, cases, suite_id=SUITE_ID, producer="human:girish")
    if not cal.payload["overall_pass"]:
        raise SystemExit(f"recalibration FAILED: {cal.record_id}")

    n_truth = sum(c["kind"] == "planted_truth" for c in cal.payload["cases"])
    print(f"recalibrated seasonality: calibration={cal.record_id} parents={list(cal.parents)}")
    print(f"  cases={len(cal.payload['cases'])} (truth={n_truth}) "
          f"truth_rate={cal.payload['pass_rate_truth']} "
          f"silence_rate={cal.payload['silence_rate_noise']} pass={cal.payload['overall_pass']}")

    report = store.verify()
    print(f"journal verify ok={report.ok} n_records={len(store)} head={report.head_hash[:12]}")


if __name__ == "__main__":
    main()
