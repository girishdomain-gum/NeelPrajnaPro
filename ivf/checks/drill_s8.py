#!/usr/bin/env python3
"""IVF Sprint-8 drill: hidden placebo pass + promotion missing legs. (rev 1)

STANDING RULE: runs BEFORE check_s8_graduation_placebo.py judges the
real ledger. Scratch copies of the real journal, three planted frauds
(ARCH-008 §Sprint close: "planted fake-placebo-pass + planted
promotion-without-gates"; clean control mandatory):

  FRAUD 1 — HIDDEN PASS (consistency): one outcome of the H-003
  placebo flipped FAIL→PASS while ``n_pass`` is left at its recorded
  value — a placebo quietly claiming fewer null passes than its own
  outcome list shows. Section D's count consistency must flag (the
  recomputation will also disagree).
  FRAUD 2 — SEED SWAP (the deep one): the H-003 placebo's recorded
  ``seed`` changed by +1. Its outcome list is now a fabrication with
  respect to its own recorded provenance; ONLY a check that actually
  re-runs the nulls from the recorded seed can notice — internal
  consistency still holds. Section D's recomputation must flag.
  (Planted on H-003, not H-002: at H-002's ~1e-4 deflation every null
  run FAILs under any seed, so its outcome sequence is seed-insensitive
  and a seed swap there is undetectable in principle — noted, not
  hidden.)
  FRAUD 3 — PROMOTION WITHOUT ITS LEGS: a fabricated ``promotion``
  appended, citing H-002's FAIL verdict (gate a violated), its real
  placebo, a nonexistent second_lens id (gate c violated), and the
  H-002 belief. Section E must flag BOTH failing legs by name.

  CONTROL — the untampered copy must be NON-RED.

Tampered copies live only in the gitignored workdir; content hashes are
deliberately left stale (this check audits meaning, not the chain —
verify_journal.py owns the chain).

Exit 0 = CAUGHT (all three + clean control), 1 = MISSED.

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/checks/drill_s8.py --journal datastore/journal/journal.jsonl --bars datastore/bulk/xauusd_h1_full/part-00000.parquet --trades-h002 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h002_fvg_intraweek_follow_through/part-00000.parquet --trades-h003 .claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/verdict_trades.h003_dow_monday_drift/part-00000.parquet --venues configs/venues.yaml --workdir ivf/reports/drill_s8_tmp --report ivf/reports/s8_drill.json
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
                     "check_s8_graduation_placebo.py")
H003_LINEAGE = "h003_dow_monday_drift"
H002_LINEAGE = "h002_fvg_intraweek_follow_through"


def load(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def dump(path: str, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def placebo_of(records: list[dict], lineage: str) -> dict:
    hyp_ids = {r["record_id"] for r in records
               if r.get("record_type") == "hypothesis"
               and r["payload"].get("lineage") == lineage}
    return next(r for r in records if r.get("record_type") == "placebo_run"
                and r["payload"].get("hypothesis_ref") in hyp_ids)


def run_check(journal: str, a) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, CHECK, "--journal", journal, "--bars", a.bars,
         "--trades-h002", a.trades_h002, "--trades-h003", a.trades_h003,
         "--venues", a.venues],
        capture_output=True, text=True, cwd=os.getcwd())
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--trades-h002", required=True)
    ap.add_argument("--trades-h003", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    real = load(a.journal)

    ctrl = os.path.join(a.workdir, "control_journal.jsonl")
    dump(ctrl, real)
    rc_ctrl, out_ctrl = run_check(ctrl, a)

    # FRAUD 1: hidden pass — outcome flipped, n_pass left as recorded.
    t1 = copy.deepcopy(real)
    p1 = placebo_of(t1, H003_LINEAGE)
    flip = p1["payload"]["outcomes"].index("FAIL")
    p1["payload"]["outcomes"][flip] = "PASS"
    f1 = os.path.join(a.workdir, "tampered_hidden_pass.jsonl")
    dump(f1, t1)
    rc1, out1 = run_check(f1, a)
    caught1 = rc1 == 1 and "D.count" in out1

    # FRAUD 2: seed swap — provenance broken, internals still consistent.
    t2 = copy.deepcopy(real)
    p2 = placebo_of(t2, H003_LINEAGE)
    p2["payload"]["seed"] = int(p2["payload"]["seed"]) + 1
    f2 = os.path.join(a.workdir, "tampered_seed_swap.jsonl")
    dump(f2, t2)
    rc2, out2 = run_check(f2, a)
    caught2 = rc2 == 1 and "D.recompute" in out2

    # FRAUD 3: promotion citing a FAIL verdict and a nonexistent lens.
    t3 = copy.deepcopy(real)
    hyp2 = next(r for r in t3 if r.get("record_type") == "hypothesis"
                and r["payload"].get("lineage") == H002_LINEAGE)
    v2 = next(r for r in t3 if r.get("record_type") == "verdict"
              and r["payload"].get("hypothesis_ref") == hyp2["record_id"])
    pb2 = placebo_of(t3, H002_LINEAGE)
    bl2 = next(r for r in t3 if r.get("record_type") == "belief"
               and r["payload"].get("family") == hyp2["payload"]["family"]
               and r["payload"].get("claim") == hyp2["payload"]["thesis"])
    t3.append({
        "record_id": "00DRILLS8FAKEPROMOTION0000",
        "record_type": "promotion",
        "producer": "graduation",
        "schema_version": 1,
        "event_ts": 0, "recorded_ts": 0,
        "parents": [v2["record_id"]],
        "prev_hash": "drill", "content_hash": "drill",
        "payload": {
            "family": hyp2["payload"]["family"],
            "claim": hyp2["payload"]["thesis"],
            "hypothesis_ref": hyp2["record_id"],
            "verdict_ref": v2["record_id"],
            "placebo_ref": pb2["record_id"],
            "second_lens_ref": "00DRILLS8NOSUCHLENS0000000",
            "belief_ref": bl2["record_id"],
        },
    })
    f3 = os.path.join(a.workdir, "tampered_promotion.jsonl")
    dump(f3, t3)
    rc3, out3 = run_check(f3, a)
    caught3 = rc3 == 1 and "E.gate-a" in out3 and "second_lens_ref" in out3

    results = {
        "control_nonred": rc_ctrl == 0,
        "fraud1_hidden_pass": "CAUGHT" if caught1 else "MISSED",
        "fraud2_seed_swap": "CAUGHT" if caught2 else "MISSED",
        "fraud3_promotion_missing_legs": "CAUGHT" if caught3 else "MISSED",
        "check_exit_control": rc_ctrl, "check_exit_f1": rc1,
        "check_exit_f2": rc2, "check_exit_f3": rc3,
    }
    missed = (rc_ctrl != 0) or not (caught1 and caught2 and caught3)
    report = {"drill": "s8_placebo_promotion_frauds", "rev": 1,
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
