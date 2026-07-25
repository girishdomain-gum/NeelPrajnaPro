#!/usr/bin/env python3
"""IVF Sprint-6 drill: threshold-swap verdict + double burn. (rev 1)

STANDING RULE: runs BEFORE check_s6_verdict.py judges the real ledger.
Builds scratch journals from the REAL one (read-only source, scratch
copies) and plants the two frauds a verdict system must fear most:

  FRAUD 1 — THRESHOLD SWAP: the verdict's thresholds are loosened
  (min_n 100→10, and an easier effective_alpha) while the registration
  stays strict. Section B must flag the byte-inequality AND the
  tri-state re-derivation.
  FRAUD 2 — DOUBLE BURN: a second window_burn for the same
  (window, lineage) is appended. Section C must flag it.

  CONTROL — the untampered copy must be NON-RED.

The check is invoked exactly as the Owner runs it, pointed at the
scratch journals + the real trades parquet.

Exit 0 = CAUGHT (both frauds + clean control), 1 = MISSED.

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/drill_s6.py --journal datastore/journal/journal.jsonl --trades datastore/bulk/verdict_trades.h001_fvg_follow_through/part-00000.parquet --workdir ivf/reports/drill_s6_tmp --report ivf/reports/s6_drill.json
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
                     "check_s6_verdict.py")
FAMILY = "xauusd_h1/smc.fvg"


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def dump(path: str, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def run_check(journal: str, trades: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, CHECK, "--journal", journal, "--trades", trades,
         "--family", FAMILY],
        capture_output=True, text=True, cwd=os.getcwd())
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--trades", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)

    real = load(a.journal)

    # control: byte-faithful copy
    ctrl = os.path.join(a.workdir, "control_journal.jsonl")
    dump(ctrl, real)
    rc_ctrl, _out_ctrl = run_check(ctrl, a.trades)

    # fraud 1: threshold swap on the verdict only
    t1 = copy.deepcopy(real)
    for r in t1:
        if r.get("record_type") == "verdict":
            r["payload"]["thresholds"] = {"min_n": 10, "base_alpha": 0.5,
                                          "correction": {"method": "bonferroni"}}
            r["payload"]["corrections"]["effective_alpha"] = 0.5
    p1 = os.path.join(a.workdir, "tampered_thresholds.jsonl")
    dump(p1, t1)
    rc1, out1 = run_check(p1, a.trades)
    caught1 = rc1 == 1 and "B.thresholds" in out1

    # fraud 2: double burn
    t2 = copy.deepcopy(real)
    dup = copy.deepcopy(next(r for r in t2
                             if r.get("record_type") == "window_burn"))
    dup["record_id"] = "SCRATCHDOUBLEBURN000000000"
    t2.append(dup)
    p2 = os.path.join(a.workdir, "tampered_doubleburn.jsonl")
    dump(p2, t2)
    rc2, out2 = run_check(p2, a.trades)
    caught2 = rc2 == 1 and "C.burn" in out2 and "exactly 1 required" in out2

    results = {
        "control_nonred": rc_ctrl == 0,
        "fraud1_threshold_swap": "CAUGHT" if caught1 else "MISSED",
        "fraud2_double_burn": "CAUGHT" if caught2 else "MISSED",
        "check_exit_control": rc_ctrl,
        "check_exit_f1": rc1, "check_exit_f2": rc2,
    }
    missed = (rc_ctrl != 0) or not (caught1 and caught2)
    report = {"drill": "s6_verdict_frauds", "rev": 1,
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
