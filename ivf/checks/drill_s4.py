#!/usr/bin/env python3
"""IVF Sprint-4 drill: planted verdict-writer + trial under-count. (rev 1)

Two planted frauds, both in SCRATCH space (nothing real is touched); the
S4 check must catch BOTH or the CHECK fails the drill:

  Drill 1 — VERDICT-WRITING SCREENER. Builds a scratch source tree
  containing a screener-like module that calls
  store.append(record_type="verdict", ...). Section A of the check must
  go RED naming the file and line.

  Drill 2 — TRIAL UNDER-COUNT. Builds a scratch journal whose shortlist
  note declares grid_size=500 but whose trial_count record says
  n_attempts=180 (the classic "only count the ones we liked"). Section B
  must go RED naming both records. The scratch journal also carries a
  correct pair as a control — the check must NOT flag it.

Runs the real check as a subprocess, exactly as the Owner runs it.
Exit 0 = CAUGHT (both), 1 = MISSED.

Usage (bash-ready, from F:/QRF):
  uv run python ivf/checks/drill_s4.py --workdir ivf/reports/drill_s4_tmp --report ivf/reports/s4_drill.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s4_screener.py")

BAD_SCREENER = '''\
"""Scratch planted module — a screener that (fraudulently) judges."""
def run(store, grid):
    shortlist = sorted(grid)[:3]
    store.append(record_type="verdict", payload={"verdict": "PASS"})
    return shortlist
'''

GOOD_NOTE = {"record_id": "SCRATCHNOTEGOOD00000000000", "record_type": "note",
             "payload": {"grid_size": 500, "trial_count_ref":
                         "SCRATCHTRIALGOOD0000000000",
                         "ranking_metric": "net_sharpe",
                         "thresholds": {"min_trades": 30, "min_sharpe": 0.10},
                         "cost_model": "xauusd_retail_median"}}
GOOD_TRIAL = {"record_id": "SCRATCHTRIALGOOD0000000000",
              "record_type": "trial_count",
              "payload": {"n_attempts": 500, "source": "screener",
                          "lineage": "scratch", "data_scope": "scratch"}}
BAD_NOTE = {"record_id": "SCRATCHNOTEBAD000000000000", "record_type": "note",
            "payload": {"grid_size": 500, "trial_count_ref":
                        "SCRATCHTRIALBAD00000000000",
                        "ranking_metric": "net_sharpe",
                        "thresholds": {"min_trades": 30, "min_sharpe": 0.10},
                        "cost_model": "xauusd_retail_median"}}
BAD_TRIAL = {"record_id": "SCRATCHTRIALBAD00000000000",
             "record_type": "trial_count",
             "payload": {"n_attempts": 180, "source": "screener",
                         "lineage": "scratch", "data_scope": "scratch"}}
VENUES = "xauusd_retail_median:\n  spread: 0.30\n  commission: 0.0\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    src = os.path.join(a.workdir, "src")
    fixtures = os.path.join(a.workdir, "fixtures")  # intentionally empty
    os.makedirs(src, exist_ok=True)
    os.makedirs(fixtures, exist_ok=True)

    with open(os.path.join(src, "planted_screener.py"), "w",
              encoding="utf-8") as f:
        f.write(BAD_SCREENER)
    journal = os.path.join(a.workdir, "scratch_journal.jsonl")
    with open(journal, "w", encoding="utf-8") as f:
        for rec in (GOOD_TRIAL, GOOD_NOTE, BAD_TRIAL, BAD_NOTE):
            f.write(json.dumps(rec) + "\n")
    venues = os.path.join(a.workdir, "venues.yaml")
    with open(venues, "w", encoding="utf-8") as f:
        f.write(VENUES)

    p = subprocess.run(
        [sys.executable, CHECK, "--src", src, "--journal", journal,
         "--venues", venues, "--fixtures", fixtures],
        capture_output=True, text=True)
    out = p.stdout

    caught1 = "A.forbidden" in out and "planted_screener.py" in out
    caught2 = ("B.count" in out and "SCRATCHNOTEBAD" in out
               and "n_attempts=180" in out)
    control_clean = "SCRATCHNOTEGOOD" not in "".join(
        line for line in out.splitlines() if '"B.' in line or '"C.' in line)
    results = {
        "drill1_verdict_writer": "CAUGHT" if caught1 else "MISSED",
        "drill2_trial_undercount": "CAUGHT" if caught2 else "MISSED",
        "control_pair_unflagged": bool(control_clean),
        "check_exit": p.returncode,
    }
    missed = (not caught1) or (not caught2) or (not control_clean)
    report = {"drill": "s4_screener_frauds", "rev": 1,
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
