#!/usr/bin/env python3
"""IVF Sprint-3 drill: plant a silent repair; the check MUST catch it. (rev 1)

Drill 1 (required, per handover §7): copy the CLEAN dataset parquet and
"correct" exactly one price — the close of the middle row is nudged by one
pip (+0.01) — simulating a silent repair during ingest. Run
check_s3_dataplane.py against the tampered copy: it MUST exit RED and name
the row. GREEN on tampered data means the CHECK failed the drill.

Drill 2 (runs only when a flagged dataset exists): copy the QUARANTINE
parquet and alter one quarantined price, simulating a repair hidden inside
quarantine. The check's price comparison MUST catch it too. If there is no
flagged dataset (the real S3 sample ingests with 0 flags), this part
reports SKIPPED — visibly, never silently.

INDEPENDENCE: no qrf imports; tampering is done by rewriting the parquet
with pyarrow; the check is invoked as a subprocess exactly as the Owner
runs it.

Usage:
  uv run python ivf/checks/drill_s3.py \
      --mt5 ivf/mt5/IVF_S3_FRESH_XAUUSD_H1.csv --timeframe 3600 \
      --clean datastore/bulk/xauusd_h1_sample/part-00000.parquet \
      [--flagged datastore/bulk/xauusd_h1_sample__flagged/part-00000.parquet] \
      --workdir ivf/reports/drill_s3_tmp --report ivf/reports/s3_drill.json

Exit 0 = CAUGHT (drill passed), 1 = MISSED (check failed the drill).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

PIP = 0.01
CHECK = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "check_s3_dataplane.py")


def tamper(src: str, dst: str, price_col: str) -> int:
    """Rewrite parquet with one value nudged; return the row's open time."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pq.read_table(src)
    rows = table.to_pylist()
    i = len(rows) // 2
    rows[i][price_col] = float(rows[i][price_col]) + PIP
    out = pa.Table.from_pylist(rows, schema=table.schema)
    pq.write_table(out, dst)
    return int(rows[i]["time"])


def run_check(mt5: str, tf: int, clean: str, flagged: str | None) -> tuple[int, str]:
    cmd = [sys.executable, CHECK, "--mt5", mt5, "--timeframe", str(tf),
           "--clean", clean]
    if flagged:
        cmd += ["--flagged", flagged]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mt5", required=True)
    ap.add_argument("--timeframe", required=True, type=int)
    ap.add_argument("--clean", required=True)
    ap.add_argument("--flagged", default=None)
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    results = {}

    # Drill 1: silent repair in the clean partition.
    t_clean = os.path.join(a.workdir, "tampered_clean.parquet")
    victim1 = tamper(a.clean, t_clean, "close")
    rc1, out1 = run_check(a.mt5, a.timeframe, t_clean, a.flagged)
    caught1 = rc1 == 1 and str(victim1) in out1
    results["drill1_clean_repair"] = {
        "victim_time": victim1, "check_exit": rc1,
        "named_victim": str(victim1) in out1,
        "result": "CAUGHT" if caught1 else "MISSED",
    }

    # Drill 2: repair hidden inside quarantine (only if quarantine exists).
    if a.flagged:
        t_flag = os.path.join(a.workdir, "tampered_flagged.parquet")
        victim2 = tamper(a.flagged, t_flag, "close")
        rc2, out2 = run_check(a.mt5, a.timeframe, a.clean, t_flag)
        caught2 = rc2 == 1 and str(victim2) in out2
        results["drill2_quarantine_repair"] = {
            "victim_time": victim2, "check_exit": rc2,
            "named_victim": str(victim2) in out2,
            "result": "CAUGHT" if caught2 else "MISSED",
        }
    else:
        results["drill2_quarantine_repair"] = {"result": "SKIPPED (no flagged dataset)"}

    missed = any(v.get("result") == "MISSED" for v in results.values())
    report = {"drill": "s3_silent_repair", "rev": 1, "run_utc": int(time.time()),
              "results": results, "verdict": "MISSED" if missed else "CAUGHT"}
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
