"""Inspect the SYNTHETIC calibration suite for the Sprint-2 detectors.

**What this is (and is not).** This script prints each *planted calibration
case* — hand-constructed synthetic fixtures — beside the detector's output, so a
human can eyeball that the fixtures encode what they claim. It inspects the
CALIBRATION SUITE, not real market events. It was renamed from
``hand_audit_s2.py`` in ARCH-003 to remove the Sprint-2 confusion where a
"hand audit" was read as sampling *real* events: the Owner's human-check (HC)
over REAL evidence is ``ivf/human/sample_s2_events.py`` (deterministic sampling
of real detector events against the MT5 chart), a separate and independent tool.

The seasonality suite includes the ARCH-003 gapped-feed case (first bar of each
day at 01:00, no midnight bar) that locks the ratified DEVQ-005 dow contract.

Run:  uv run python scripts/calibration_audit_s2.py
"""

from __future__ import annotations

from qrf.kernel.instruments.calibration import descriptors
from qrf.trading.concepts.classical import RSIDetector
from qrf.trading.concepts.seasonality import SeasonalityDetector
from qrf.trading.concepts.seasonality import fixtures as SF


def _audit(det, label: str) -> None:
    print(f"=== {label}: synthetic calibration suite ===")
    for case in det.planted_cases():
        got = descriptors(det.detect(case.data))
        want = case.expected if case.kind == "planted_truth" else []
        verdict = "PASS" if got == want else "FAIL"
        print(f"  case {case.case_id!r} [{case.kind}] -> {verdict}")
        print(f"    expected {len(case.expected)} event(s), got {len(got)}")
        for d in got[:12]:
            print(f"      got: ts={d['ts']} {d['event_type']} dir={d['direction']}")
    print()


def main() -> None:
    seas = SeasonalityDetector(params=SF.CANONICAL_PARAMS)
    rsi = RSIDetector()
    _audit(seas, "seasonality.calendar (SYNTHETIC)")
    _audit(rsi, "classical.rsi (SYNTHETIC)")
    print("NOTE: real-evidence human check is ivf/human/sample_s2_events.py, not this script.")


if __name__ == "__main__":
    main()
