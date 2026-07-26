#!/usr/bin/env python3
"""IVF Sprint-9 drill: five frauds against the multi-window + lens check. (rev 1)

STANDING RULE: runs BEFORE check_s9_lens_multiwindow.py judges the real
ledger. Scratch copies of the real journal in a gitignored workdir; the
real (hash-verified) parquets are passed through untouched. Clean control
mandatory. Exit 0 = CAUGHT (all five + control NON-RED), 1 = MISSED.

  FRAUD 1 — SEAM-STRADDLING FOLD: H-004's fold-5 test_start pulled back
  across the inter-window seam (4986 → 4000), a fold quietly spanning the
  2024 reserve hole. Section B's fold re-derivation must flag.
  FRAUD 2 — HOLE MISCOUNT: the verdict's n_dropped_hole rewritten to 3
  (holes claimed that the seam geometry does not produce — the mirror of
  an uncounted hole; the detection surface is the same structural
  recomputation). Section B.hole must flag.
  FRAUD 3 — SINGLE-SHIFT LENS: the recorded second_lens doctored to claim
  one constant −2h alignment across the DST boundary (all four CHOSEN
  entries rewritten to −2h) with a flattered pooled n_agree/rate. Section
  D's independent recomputation must flag BOTH the shifts and the pooled
  figures.
  FRAUD 4 — ORDERING FRAUD (the sprint's soul): the sealed correction
  note physically moved to AFTER the second_lens in the journal sequence
  — an overlap whose pre-registration postdates it. Section E's
  chain-position audit must flag. (Content hashes are left stale — the
  drill audits meaning; verify_journal.py owns the chain.)
  FRAUD 5 — BROKEN SEAL: H-004's sealed placebo_method rewritten to
  direction_permutation while its placebo_run ran entry_time_shuffle.
  Sections C/F must flag the seal mismatch.

Usage (paste in git bash, from /f/QRF, after rebuilding parquets):
  uv run python ivf/checks/drill_s9.py --journal datastore/journal/journal.jsonl --bars-primary datastore/bulk/xauusd_h1_primary_full/part-00000.parquet --bars-second datastore/bulk/xauusd_h1_secondfeed/part-00000.parquet --trades-h004 datastore/bulk/verdict_trades.h004_dow_monday_drift_v2/part-00000.parquet --overlap datastore/bulk/xauusd_h1_overlap_lens/part-00000.parquet --venues configs/venues.yaml --workdir ivf/reports/drill_s9_tmp --report ivf/reports/s9_drill.json
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import time

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s9_lens_multiwindow.py")
H004 = "h004_dow_monday_drift_v2"


def load(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def dump(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def h004_records(records):
    hyp = next(r for r in records if r.get("record_type") == "hypothesis"
               and r["payload"].get("lineage") == H004)
    ver = next(r for r in records if r.get("record_type") == "verdict"
               and r["payload"].get("hypothesis_ref") == hyp["record_id"])
    return hyp, ver


def run_check(journal, a):
    p = subprocess.run(
        [sys.executable, CHECK, "--journal", journal,
         "--bars-primary", a.bars_primary, "--bars-second", a.bars_second,
         "--trades-h004", a.trades_h004, "--overlap", a.overlap,
         "--venues", a.venues],
        capture_output=True, text=True, cwd=os.getcwd())
    return p.returncode, p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--bars-primary", required=True)
    ap.add_argument("--bars-second", required=True)
    ap.add_argument("--trades-h004", required=True)
    ap.add_argument("--overlap", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    real = load(a.journal)

    ctrl = os.path.join(a.workdir, "control.jsonl")
    dump(ctrl, real)
    rc0, out0 = run_check(ctrl, a)

    # FRAUD 1: seam-straddling fold
    t1 = copy.deepcopy(real)
    _, v1 = h004_records(t1)
    v1["payload"]["folds"][4]["test_start"] = 4000  # crosses the 4157 seam
    f1 = os.path.join(a.workdir, "f1_seam_fold.jsonl")
    dump(f1, t1)
    rc1, out1 = run_check(f1, a)
    c1 = rc1 == 1 and "B.fold5" in out1

    # FRAUD 2: hole miscount
    t2 = copy.deepcopy(real)
    _, v2 = h004_records(t2)
    v2["payload"]["n_dropped_hole"] = 3
    f2 = os.path.join(a.workdir, "f2_hole_miscount.jsonl")
    dump(f2, t2)
    rc2, out2 = run_check(f2, a)
    c2 = rc2 == 1 and "B.hole" in out2

    # FRAUD 3: single-shift lens across the DST boundary
    t3 = copy.deepcopy(real)
    lens = next(r for r in t3 if r.get("record_type") == "second_lens")
    ag = lens["payload"]["agreement_summary"]
    ag["notes"] = re.sub(r"CHOSEN -\dh", "CHOSEN -2h", ag["notes"])
    ag["n_agree"] = int(ag["n_agree"]) + 180  # flattered constant-shift total
    ag["agreement_rate"] = ag["n_agree"] / ag["n_overlap"]
    f3 = os.path.join(a.workdir, "f3_single_shift_lens.jsonl")
    dump(f3, t3)
    rc3, out3 = run_check(f3, a)
    c3 = rc3 == 1 and "D.shifts" in out3 and "D.n_agree" in out3

    # FRAUD 4: ordering fraud — the sealed note moved after the lens
    t4 = copy.deepcopy(real)
    lens4 = next(r for r in t4 if r.get("record_type") == "second_lens")
    note_id = next(p for p in lens4["parents"]
                   if next(r for r in t4 if r["record_id"] == p)
                   ["record_type"] == "note")
    note_rec = next(r for r in t4 if r["record_id"] == note_id)
    t4.remove(note_rec)
    t4.append(note_rec)  # note now AFTER the lens in journal sequence
    f4 = os.path.join(a.workdir, "f4_ordering.jsonl")
    dump(f4, t4)
    rc4, out4 = run_check(f4, a)
    c4 = rc4 == 1 and "E.order" in out4

    # FRAUD 5: broken placebo_method seal
    t5 = copy.deepcopy(real)
    h5, _ = h004_records(t5)
    h5["payload"]["placebo_method"] = "direction_permutation"
    f5 = os.path.join(a.workdir, "f5_broken_seal.jsonl")
    dump(f5, t5)
    rc5, out5 = run_check(f5, a)
    c5 = rc5 == 1 and ("C.seal" in out5 or "F.seal" in out5)

    results = {
        "control_nonred": rc0 == 0,
        "fraud1_seam_fold": "CAUGHT" if c1 else "MISSED",
        "fraud2_hole_miscount": "CAUGHT" if c2 else "MISSED",
        "fraud3_single_shift_lens": "CAUGHT" if c3 else "MISSED",
        "fraud4_ordering": "CAUGHT" if c4 else "MISSED",
        "fraud5_broken_seal": "CAUGHT" if c5 else "MISSED",
        "check_exits": [rc0, rc1, rc2, rc3, rc4, rc5],
    }
    missed = (rc0 != 0) or not all((c1, c2, c3, c4, c5))
    report = {"drill": "s9_lens_multiwindow_frauds", "rev": 1,
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
