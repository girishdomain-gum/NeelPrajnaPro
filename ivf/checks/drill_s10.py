#!/usr/bin/env python3
"""IVF Sprint-10 drill: unpaid attempt + sweep tampering. (rev 1)
Runs BEFORE check_s10_trials_wave2.py. Scratch journals; real parquet
passed through. Exit 0 = CAUGHT (3 frauds + clean control).
  F1 UNPAID ATTEMPT: h004's retro trial_count deleted — a hypothesis
     whose scientific cost vanished. A.unpaid + A.total must flag.
  F2 SWEEP-CHARGE SHAVED: the 500-trial charge rewritten to 499 —
     a family quietly billed less than it searched. B.charge/A.total.
  F3 LOOSENED THRESHOLDS: the sealed note's min_trades 30→2 — admitted
     flags in the parquet no longer follow the note's own rule. B.admit
     (needs the real parquet; proves the flag-vs-threshold recompute).
Usage (from /f/QRF, after rebuild):
  uv run python ivf/checks/drill_s10.py --journal datastore/journal/journal.jsonl --shortlist datastore/bulk/screener_shortlist_s10_wave2/part-00000.parquet --workdir ivf/reports/drill_s10_tmp --report ivf/reports/s10_drill.json
"""
from __future__ import annotations
import argparse, copy, json, os, subprocess, sys, time
CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s10_trials_wave2.py")

def load(p):
    return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]

def dump(p, rs):
    open(p, "w", encoding="utf-8").write(
        "".join(json.dumps(r) + "\n" for r in rs))

def run(j, a):
    p = subprocess.run([sys.executable, CHECK, "--journal", j,
                        "--shortlist", a.shortlist],
                       capture_output=True, text=True)
    return p.returncode, p.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--shortlist", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    real = load(a.journal)
    ctrl = os.path.join(a.workdir, "control.jsonl")
    dump(ctrl, real)
    rc0, _ = run(ctrl, a)
    t1 = [r for r in copy.deepcopy(real)
          if not (r.get("record_type") == "trial_count"
                  and r["payload"].get("lineage") == "h004_dow_monday_drift_v2")]
    f1 = os.path.join(a.workdir, "f1.jsonl"); dump(f1, t1)
    rc1, o1 = run(f1, a); c1 = rc1 == 1 and "A.unpaid" in o1
    t2 = copy.deepcopy(real)
    for r in t2:
        if r.get("record_type") == "trial_count" and \
                r["payload"].get("n_attempts") == 500:
            r["payload"]["n_attempts"] = 499
    f2 = os.path.join(a.workdir, "f2.jsonl"); dump(f2, t2)
    rc2, o2 = run(f2, a); c2 = rc2 == 1 and ("B.charge" in o2 or "A.total" in o2)
    t3 = copy.deepcopy(real)
    for r in reversed(t3):
        if r.get("record_type") == "note":
            try:
                nj = json.loads(r["payload"]["text"])
            except (ValueError, TypeError):
                continue
            if nj.get("kind") == "screener_shortlist":
                nj["thresholds"]["min_trades"] = 2
                r["payload"]["text"] = json.dumps(nj)
                break
    f3 = os.path.join(a.workdir, "f3.jsonl"); dump(f3, t3)
    rc3, o3 = run(f3, a); c3 = rc3 == 1 and ("B.admit" in o3 or "B.count" in o3)
    res = {"control_nonred": rc0 == 0,
           "fraud1_unpaid_attempt": "CAUGHT" if c1 else "MISSED",
           "fraud2_shaved_charge": "CAUGHT" if c2 else "MISSED",
           "fraud3_loosened_thresholds": "CAUGHT" if c3 else "MISSED",
           "check_exits": [rc0, rc1, rc2, rc3]}
    missed = rc0 != 0 or not all((c1, c2, c3))
    rep = {"drill": "s10_trials_wave2_frauds", "rev": 1,
           "run_utc": int(time.time()), "results": res,
           "verdict": "MISSED" if missed else "CAUGHT"}
    body = json.dumps(rep, indent=2)
    if a.report:
        open(a.report, "w", encoding="utf-8").write(body + "\n")
    print(body)
    return 1 if missed else 0

if __name__ == "__main__":
    sys.exit(main())
