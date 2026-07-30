#!/usr/bin/env python3
"""IVF NP-S1 AC-6 drill: six planted frauds + one clean control. (rev 1)

STANDING RULE (ARCH-NP-002 SS1): runs BEFORE check_np_s1_ac6.py judges the
real ledger. Builds scratch journals/trades from the REAL ones (read-only
sources; scratch copies only, under a *_tmp/ workdir the .gitignore
already reserves for "IVF drill scratch (tampered copies; must never be
tracked)"). A miss on any plant, or a false alarm on the control, is RED
and the real re-derivation must not proceed.

  P1 alter one trade's net in the trades parquet
  P2 change verdict corrections.family_m from 19 -> 18
  P3 delete one trial_count record from the family
  P4 swap the cost model to $0.26 (bakes into the trades parquet's own
     cost/net_pnl columns, as an actual $0.26-costed run would have)
  P5 move the window's ts_end by one bar (300s)
  P6 edit the registration's thresholds after the fact (verdict's copy
     left untouched -- byte-inequality is the catch)
  C0 untampered control -- must raise nothing

Each plant is judged against check_np_s1_ac6.py's CHAIN-CHECK verdict
(sections A-K, its exit code) ONLY -- section3 (L/M) findings are
substantive, honestly-may-fail items on the real ledger, not fraud
signatures the drill is targeting, so they never gate catch/miss here.

Usage:
  python ivf/checks/drill_np_s1_ac6.py --journal <real_journal.jsonl>
    --trades <real_trades.parquet> --venues <real_venues.yaml>
    --verdict-id 01KYSGQR3D8SYSVJFSF9M77CMY
    --workdir ivf/reports/drill_ac6_tmp --report ivf/reports/ac6_drill.json
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import time

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_np_s1_ac6.py")
VERDICT_ID = "01KYSGQR3D8SYSVJFSF9M77CMY"


def load_journal(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def dump_journal(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def run_check(python_exe, journal, trades, venues, verdict_id):
    p = subprocess.run(
        [python_exe, CHECK, "--journal", journal, "--trades", trades,
         "--venues", venues, "--verdict-id", verdict_id],
        capture_output=True, text=True, cwd=os.getcwd())
    try:
        report = json.loads(p.stdout)
    except json.JSONDecodeError:
        report = {"red": ["UNPARSEABLE OUTPUT: " + p.stdout[-2000:] + p.stderr[-2000:]], "verdict": "RED"}
    return p.returncode, report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal", required=True)
    ap.add_argument("--trades", required=True)
    ap.add_argument("--venues", required=True)
    ap.add_argument("--verdict-id", default=VERDICT_ID)
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)

    real = load_journal(a.journal)
    by_id = {r["record_id"]: r for r in real}
    verdict = by_id[a.verdict_id]
    hyp_id = verdict["payload"]["hypothesis_ref"]
    win_id = verdict["payload"]["window_ref"]

    import pyarrow.parquet as pq
    import pyarrow as pa

    base_table = pq.read_table(a.trades)
    base_df = base_table.to_pandas()

    results = {}

    def check(label, journal_path, trades_path, venues_path, expect_catch, catch_substr=None):
        rc, report = run_check(a.python, journal_path, trades_path, venues_path, a.verdict_id)
        red_lines = report.get("red", [])
        is_red = rc == 1
        if expect_catch:
            caught = is_red and (catch_substr is None or any(catch_substr in ln for ln in red_lines))
            results[label] = {
                "expect": "CATCH", "outcome": "CAUGHT" if caught else "MISSED",
                "exit_code": rc, "red": red_lines,
            }
        else:
            clean = not is_red
            results[label] = {
                "expect": "CLEAN", "outcome": "CLEAN" if clean else "FALSE_ALARM",
                "exit_code": rc, "red": red_lines,
            }

    # --- C0: untampered control ------------------------------------------------
    c0_journal = os.path.join(a.workdir, "c0_journal.jsonl")
    c0_trades = os.path.join(a.workdir, "c0_trades.parquet")
    dump_journal(c0_journal, real)
    pq.write_table(base_table, c0_trades)
    check("C0_control", c0_journal, c0_trades, a.venues, expect_catch=False)

    # --- P1: alter one trade's net_pnl -----------------------------------------
    p1_df = base_df.copy()
    p1_df.loc[0, "net_pnl"] = p1_df.loc[0, "net_pnl"] + 100.0
    p1_trades = os.path.join(a.workdir, "p1_trades.parquet")
    pq.write_table(pa.Table.from_pandas(p1_df, schema=base_table.schema, preserve_index=False), p1_trades)
    p1_journal = os.path.join(a.workdir, "p1_journal.jsonl")
    dump_journal(p1_journal, real)
    check("P1_altered_trade_net", p1_journal, p1_trades, a.venues, expect_catch=True, catch_substr="D.net_mean")

    # --- P2: verdict corrections.family_m 19 -> 18 -------------------------------
    p2 = copy.deepcopy(real)
    for r in p2:
        if r["record_id"] == a.verdict_id:
            r["payload"]["corrections"]["family_m"] = 18
            r["payload"]["corrections"]["effective_alpha"] = 0.05 / 18
    p2_journal = os.path.join(a.workdir, "p2_journal.jsonl")
    dump_journal(p2_journal, p2)
    check("P2_family_m_19_to_18", p2_journal, a.trades, a.venues, expect_catch=True, catch_substr="A.family_m")

    # --- P3: delete one trial_count record from the family -----------------------
    p3 = copy.deepcopy(real)
    removed = False
    kept = []
    for r in p3:
        if (not removed and r.get("record_type") == "trial_count"
                and r["payload"].get("family") == "xauusd/neelprajna"):
            removed = True
            continue
        kept.append(r)
    assert removed, "drill setup error: no xauusd/neelprajna trial_count record found to delete"
    p3_journal = os.path.join(a.workdir, "p3_journal.jsonl")
    dump_journal(p3_journal, kept)
    check("P3_deleted_trial_count", p3_journal, a.trades, a.venues, expect_catch=True, catch_substr="A.family_m")

    # --- P4: swap cost model to $0.26 (bake into trades parquet) ------------------
    p4_df = base_df.copy()
    p4_df["cost"] = 0.26
    p4_df["net_pnl"] = p4_df["gross_pnl"] - 0.26
    p4_trades = os.path.join(a.workdir, "p4_trades.parquet")
    pq.write_table(pa.Table.from_pandas(p4_df, schema=base_table.schema, preserve_index=False), p4_trades)
    p4_journal = os.path.join(a.workdir, "p4_journal.jsonl")
    dump_journal(p4_journal, real)
    check("P4_cost_model_swap_026", p4_journal, p4_trades, a.venues, expect_catch=True, catch_substr="F.per_trade_cost")

    # --- P5: move window ts_end by one bar (300s) ---------------------------------
    p5 = copy.deepcopy(real)
    for r in p5:
        if r["record_id"] == win_id:
            r["payload"]["ts_end"] = int(r["payload"]["ts_end"]) - 300_000_000_000
    p5_journal = os.path.join(a.workdir, "p5_journal.jsonl")
    dump_journal(p5_journal, p5)
    check("P5_window_ts_end_shift", p5_journal, a.trades, a.venues, expect_catch=True, catch_substr="G.bounds")

    # --- P6: edit registration's thresholds after the fact -------------------------
    p6 = copy.deepcopy(real)
    for r in p6:
        if r["record_id"] == hyp_id:
            r["payload"]["thresholds"] = dict(r["payload"]["thresholds"])
            r["payload"]["thresholds"]["min_n"] = 50
    p6_journal = os.path.join(a.workdir, "p6_journal.jsonl")
    dump_journal(p6_journal, p6)
    check("P6_thresholds_edited_after_fact", p6_journal, a.trades, a.venues, expect_catch=True, catch_substr="B.thresholds")

    missed = any(
        (v["expect"] == "CATCH" and v["outcome"] != "CAUGHT")
        or (v["expect"] == "CLEAN" and v["outcome"] != "CLEAN")
        for v in results.values()
    )
    report = {
        "drill": "np_s1_ac6",
        "rev": 1,
        "run_utc": int(time.time()),
        "results": results,
        "verdict": "MISSED" if missed else "CAUGHT",
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
