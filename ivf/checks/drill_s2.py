#!/usr/bin/env python3
"""Drill S2 — plant a one-bar timestamp shift in the qrf events CSV.

The classic hindsight bug: every event stamped one bar early. The tampered
copy MUST turn check_s2_detectors.py RED (timestamp mismatches on both the
RSI and seasonality comparisons). Stdlib only; never touches the original.

Usage:
  python ivf/checks/drill_s2.py --events events.csv --bar-seconds 3600 \
         --out tampered_events.csv
Then run check_s2_detectors.py with --events tampered_events.csv → expect RED.
"""

from __future__ import annotations

import argparse, csv

NS = 1_000_000_000

ap = argparse.ArgumentParser()
ap.add_argument("--events", required=True)
ap.add_argument("--bar-seconds", type=int, required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

with open(a.events, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
    fields = f.seek(0) or csv.DictReader(open(a.events, newline="", encoding="utf-8")).fieldnames

for r in rows:
    r["ts"] = str(int(r["ts"]) - a.bar_seconds * NS)  # one bar EARLY = hindsight

with open(a.out, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)
print(f"[drill S2] planted -{a.bar_seconds}s shift on {len(rows)} events -> {a.out}")
