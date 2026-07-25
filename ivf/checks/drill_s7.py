#!/usr/bin/env python3
"""IVF Sprint-7 drill: VIRGIN-referencing question + FAIL-ignoring belief. (rev 1)

STANDING RULE: runs BEFORE check_s7_observatory.py judges the real
ledger. Scratch copies of the real journal, two planted frauds:

  FRAUD 1 — a question whose data_slice_refs quietly include the VIRGIN
  window id (curiosity contaminating the reserve). Section B must flag.
  FRAUD 2 — a belief flipped to SUPPORTED while citing H-001's FAIL
  verdict (memory ignoring the judge). Section A must flag stance.

  CONTROL — untampered copy must be NON-RED.

Exit 0 = CAUGHT (both + clean control), 1 = MISSED.

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/drill_s7.py --journal datastore/journal/journal.jsonl --bars datastore/bulk/xauusd_h1_full/part-00000.parquet --events "datastore/bulk/xauusd_h1_training_smc_fvg_scan/part-00000.parquet" --virgin 01KYB4SSD9VVKB577KRGB1W1P0 --workdir ivf/reports/drill_s7_tmp --report ivf/reports/s7_drill.json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import time

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s7_observatory.py")


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def dump(path: str, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def run_check(journal: str, a) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, CHECK, "--journal", journal, "--bars", a.bars,
         "--events", a.events, "--virgin", a.virgin],
        capture_output=True, text=True, cwd=os.getcwd())
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--virgin", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    real = load(a.journal)

    ctrl = os.path.join(a.workdir, "control_journal.jsonl")
    dump(ctrl, real)
    rc_ctrl, out_ctrl = run_check(ctrl, a)

    # fraud 1: VIRGIN-referencing question
    t1 = copy.deepcopy(real)
    q1 = next(r for r in t1 if r.get("record_type") == "question")
    q1["payload"].setdefault("data_slice_refs", []).append(a.virgin)
    p1 = os.path.join(a.workdir, "tampered_virgin_question.jsonl")
    dump(p1, t1)
    rc1, out1 = run_check(p1, a)
    caught1 = rc1 == 1 and "B.virgin" in out1 and "question" in out1

    # fraud 2: belief flipped to SUPPORTED against a FAIL verdict
    t2 = copy.deepcopy(real)
    terminals = [r for r in t2 if r.get("record_type") == "belief"]
    prevs = {b["payload"].get("prev_state") for b in terminals}
    b2 = next(b for b in terminals if b["record_id"] not in prevs)
    b2["payload"]["stance"] = "SUPPORTED"
    p2 = os.path.join(a.workdir, "tampered_belief.jsonl")
    dump(p2, t2)
    rc2, out2 = run_check(p2, a)
    caught2 = rc2 == 1 and "A.stance" in out2 and "SUPPORTED" in out2

    results = {
        "control_nonred": rc_ctrl == 0,
        "fraud1_virgin_question": "CAUGHT" if caught1 else "MISSED",
        "fraud2_fail_ignoring_belief": "CAUGHT" if caught2 else "MISSED",
        "check_exit_control": rc_ctrl,
        "check_exit_f1": rc1, "check_exit_f2": rc2,
    }
    missed = (rc_ctrl != 0) or not (caught1 and caught2)
    report = {"drill": "s7_observatory_frauds", "rev": 1,
              "run_utc": int(time.time()), "results": results,
              "verdict": "MISSED" if missed else "CAUGHT"}
    body = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(body + "\n")
    print(body)
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
