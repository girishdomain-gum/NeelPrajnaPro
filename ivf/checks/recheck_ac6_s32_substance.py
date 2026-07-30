#!/usr/bin/env python3
"""IVF NP-S1 AC-6, ARCH-NP-003 SS1: SS3.2 re-checked as a SUBSTANCE test.

NP-ADR-008 APPENDIX B SS B.7 rules the registration wording accepted
as-is (substance present, bytes not; re-registration refused -- it would
orphan the verdict from its hypothesis and spend two further family
trials). This script re-checks accordingly: SUBSTANCE test (does each of
the three propositions appear IN MEANING) reported separately from the
BYTE test (restated as a recorded deviation per B.7, not a failure).

No qrf import; reads the journal directly (stdlib json).

Usage:
  python ivf/checks/recheck_ac6_s32_substance.py --journal <path>
    --verdict-id 01KYSGQR3D8SYSVJFSF9M77CMY --report ivf/reports/ac6_s32_recheck.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

# NP-ADR-008 SS2.1, exact byte text (for the byte test, restated per B.7):
ADR_STATEMENTS_BYTE = [
    "E2-v1.1 is not equivalent to the original v1.0 hypothesis.",
    "It is a new hypothesis bound to the documented v1.1 detector lineage.",
    "Any future judgment of the original T3/MSS detector requires a separate "
    "implementation and fresh out-of-sample evidence.",
]

# Substance markers for each proposition -- what the sentence must MEAN,
# not how it must be spelled. Each is a list of regexes; a statement's
# substance is present if ALL regexes in its list find a match (order-
# independent, case-insensitive) somewhere in the registration's
# outcome_interpretations + thesis text.
SUBSTANCE_MARKERS = [
    # (1) v1.1 is NOT equivalent to the original v1.0 hypothesis
    [r"v1\.1", r"not\s+equivalent", r"v1\.0\s+hypothesis"],
    # (2) it IS a new hypothesis bound to the documented v1.1 detector lineage
    [r"new\s+hypothesis", r"v1\.1\s+detector\s+lineage"],
    # (3) any future judgment of the original T3/MSS detector requires a
    #     separate implementation and fresh out-of-sample evidence
    [r"T3/MSS\s+detector", r"separate\s+implementation", r"fresh\s+out-of-sample\s+evidence"],
]

PROPOSITION_LABELS = [
    "(1) v1.1 not equivalent to the original v1.0 hypothesis",
    "(2) it is a new hypothesis bound to the documented v1.1 detector lineage",
    "(3) future judgment of the original T3/MSS detector requires separate "
    "implementation + fresh out-of-sample evidence",
]


def load_journal(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def substance_present(markers, hay):
    return all(re.search(m, hay, re.IGNORECASE) for m in markers)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--verdict-id", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    journal = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in journal}
    verdict = by_id[a.verdict_id]
    hyp = by_id[verdict["payload"]["hypothesis_ref"]]
    lineage = hyp["payload"]["lineage"]

    lineage_hyps = [
        r for r in journal
        if r.get("record_type") == "hypothesis" and r["payload"].get("lineage") == lineage
    ]

    substance_results = []
    byte_results = []
    any_substance_fail = False

    for hrec in lineage_hyps:
        hrp = hrec["payload"]
        claim_form = hrp.get("setup_dsl", {}).get("claim_form", "?")
        hay = json.dumps(hrp.get("outcome_interpretations", {})) + " " + hrp.get("thesis", "")

        for i, (markers, label, byte_stmt) in enumerate(
            zip(SUBSTANCE_MARKERS, PROPOSITION_LABELS, ADR_STATEMENTS_BYTE), start=1
        ):
            sub_ok = substance_present(markers, hay)
            substance_results.append(
                {
                    "registration": hrec["record_id"],
                    "claim_form": claim_form,
                    "statement": i,
                    "proposition": label,
                    "result": "PASS" if sub_ok else "FAIL",
                }
            )
            if not sub_ok:
                any_substance_fail = True

            byte_ok = byte_stmt in hay
            byte_results.append(
                {
                    "registration": hrec["record_id"],
                    "claim_form": claim_form,
                    "statement": i,
                    "byte_exact": byte_ok,
                    "disposition": (
                        "byte-exact"
                        if byte_ok
                        else "recorded deviation per NP-ADR-008 Appendix B SS B.7 "
                        "(wording joined/paraphrased; substance judged separately above)"
                    ),
                }
            )

    report = {
        "check": "ac6_s32_substance_recheck",
        "rev": 1,
        "run_utc": int(time.time()),
        "arch": "ARCH-NP-003 SS1",
        "substance_test": substance_results,
        "substance_overall": "FAIL" if any_substance_fail else "PASS",
        "byte_test": byte_results,
        "byte_overall": "0/{} byte-exact (unchanged from AC-6's original finding); accepted per Appendix B SS B.7, not a failure".format(
            len(byte_results)
        ),
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if any_substance_fail else 0


if __name__ == "__main__":
    sys.exit(main())
