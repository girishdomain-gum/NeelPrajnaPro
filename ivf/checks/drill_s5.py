#!/usr/bin/env python3
"""IVF Sprint-5 drill: look-ahead fill + embargo violation + broken determinism. (rev 1)

STANDING RULE (GO-S4 retro): this drill runs BEFORE check_s5_battery.py is
allowed to judge the real system. It fabricates two artifact sets in scratch:

  CONTROL — fully consistent artifacts (the real micro-scenario numbers,
  spec-correct splits, a coherent selftest). The check must be NON-RED here;
  a check that flags clean data fails the drill too.

  TAMPERED — three planted frauds:
    1. LOOK-AHEAD FILL: trade A's entry moved to the SIGNAL bar at a better
       price (the classic hindsight fill). Section B must flag entry_ts and
       entry_price for signal 0.
    2. EMBARGO VIOLATION: one fold's train extended to the test start,
       swallowing the embargo gap. Section C must flag geometry/embargo.
    3. BROKEN DETERMINISM: the two cross-process hashes differ. Section A
       must flag it.

Exit 0 = CAUGHT (all three flagged AND control clean), 1 = MISSED.

Usage (bash-ready, from F:/QRF):
  uv run python ivf/checks/drill_s5.py --workdir ivf/reports/drill_s5_tmp --report ivf/reports/s5_drill.json
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import subprocess
import sys
import time

CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s5_battery.py")
COST = 0.47  # xauusd_retail_median round trip: 0.30 + 2*(0.05+0.035)


def micro_control() -> dict:
    opens = [100.0] * 15
    opens[3] = 105.0
    opens[6] = 200.0
    opens[8] = 197.0
    opens[11] = 50.0
    opens[13] = 48.0
    trades = [
        {"signal_ts": 0, "entry_ts": 1, "exit_ts": 3, "direction": 1,
         "size": 1.0, "entry_price": 100.0, "exit_price": 105.0,
         "gross_pnl": 5.0, "cost": COST, "net_pnl": 5.0 - COST,
         "exit_reason": "time_stop"},
        {"signal_ts": 5, "entry_ts": 6, "exit_ts": 8, "direction": 1,
         "size": 1.0, "entry_price": 200.0, "exit_price": 197.0,
         "gross_pnl": -3.0, "cost": COST, "net_pnl": -3.0 - COST,
         "exit_reason": "time_stop"},
        {"signal_ts": 10, "entry_ts": 11, "exit_ts": 13, "direction": -1,
         "size": 1.0, "entry_price": 50.0, "exit_price": 48.0,
         "gross_pnl": 2.0, "cost": COST, "net_pnl": 2.0 - COST,
         "exit_reason": "time_stop"},
    ]
    return {"bars": {"ts": list(range(15)), "open": opens},
            "events": {"ts": [0, 5, 10], "direction": [1, 1, -1],
                       "strength": [1.0, 1.0, 1.0]},
            "hold_bars": 2, "size": 1.0, "cost_model": "xauusd_retail_median",
            "engine": {"seed": 12345, "n_dropped_tail": 0, "trades": trades}}


def splits_control() -> dict:
    cases = [{"n_bars": 100, "n_folds": 4, "embargo": 5},
             {"n_bars": 103, "n_folds": 4, "embargo": 5}]
    out = []
    for c in cases:
        nb = c["n_folds"] + 1
        base, rem = divmod(c["n_bars"], nb)
        bounds = [0]
        for b in range(nb):
            bounds.append(bounds[-1] + base + (1 if b < rem else 0))
        folds = [{"train": [0, max(0, bounds[i] - c["embargo"])],
                  "test": [bounds[i], bounds[i + 1]]}
                 for i in range(1, c["n_folds"] + 1)]
        out.append({**c, "folds": folds})
    return {"cases": out}


def selftest_control() -> dict:
    def stats_of(vals):
        n = len(vals)
        mean = sum(vals) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in vals) / (n - 1))
        t = mean / (sd / math.sqrt(n)) if sd > 1e-9 else float("inf")
        return n, mean, t
    edge = [1.0, 2.0] * 30
    noise = [0.5, -0.5] * 30
    small = [1.0] * 8
    ne, me, te = stats_of(edge)
    nn_, mn, tn = stats_of(noise)
    return {"seed": 777, "passed": True,
            "results": [
                {"name": "planted_edge", "expected": "PASS",
                 "classification": "PASS", "n_trades": ne, "mean": me,
                 "t_stat": te, "p_value": 1e-12},
                {"name": "pure_noise", "expected": "FAIL",
                 "classification": "FAIL", "n_trades": nn_, "mean": mn,
                 "t_stat": tn, "p_value": 0.5},
                {"name": "small_n", "expected": "INSUFFICIENT",
                 "classification": "INSUFFICIENT", "n_trades": 8,
                 "mean": 1.0, "t_stat": float("nan"), "p_value": float("nan")},
            ],
            "outcomes": {"planted_edge": edge, "pure_noise": noise,
                         "small_n": small}}


def write_artifacts(d: str, det: dict, micro: dict, splits: dict, st: dict) -> None:
    os.makedirs(d, exist_ok=True)
    for name, obj in (("determinism", det), ("micro", micro),
                      ("splits", splits), ("selftest", st)):
        with open(os.path.join(d, f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1)


def run_check(artifacts: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, CHECK, "--artifacts", artifacts],
                       capture_output=True, text=True, cwd=os.getcwd())
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    det_ok = {"hash1": "f" * 64, "hash2": "f" * 64}
    ctrl = os.path.join(a.workdir, "control")
    write_artifacts(ctrl, det_ok, micro_control(), splits_control(),
                    selftest_control())
    rc_ctrl, out_ctrl = run_check(ctrl)

    # tampered set
    m = copy.deepcopy(micro_control())
    m["engine"]["trades"][0].update(
        {"entry_ts": 0, "entry_price": 99.5, "gross_pnl": 5.5,
         "net_pnl": 5.5 - COST})  # look-ahead: filled on the signal bar, better price
    s = splits_control()
    s["cases"][0]["folds"][0]["train"] = [0, s["cases"][0]["folds"][0]["test"][0]]
    det_bad = {"hash1": "f" * 64, "hash2": "0" * 64}
    tamp = os.path.join(a.workdir, "tampered")
    write_artifacts(tamp, det_bad, m, s, selftest_control())
    rc_tamp, out_tamp = run_check(tamp)

    caught_lookahead = ("B.entry_ts" in out_tamp and "signal 0" in out_tamp
                        and "B.entry_price" in out_tamp)
    caught_embargo = "C." in out_tamp and "fold 1" in out_tamp
    caught_determinism = "A.determinism" in out_tamp
    control_clean = rc_ctrl == 0

    results = {
        "control_nonred": control_clean,
        "fraud1_lookahead_fill": "CAUGHT" if caught_lookahead else "MISSED",
        "fraud2_embargo_violation": "CAUGHT" if caught_embargo else "MISSED",
        "fraud3_broken_determinism": "CAUGHT" if caught_determinism else "MISSED",
        "check_exit_control": rc_ctrl, "check_exit_tampered": rc_tamp,
    }
    missed = (not control_clean) or rc_tamp != 1 or not (
        caught_lookahead and caught_embargo and caught_determinism)
    report = {"drill": "s5_battery_frauds", "rev": 1,
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
