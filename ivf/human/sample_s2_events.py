#!/usr/bin/env python3
"""IVF S2 HC sampler — draw random REAL events for the Owner's chart check.

Replaces scripts/hand_audit_s2.py for HC purposes: that script samples the
synthetic calibration fixtures (correct for its Sprint-2 birth, wrong for a
chart comparison — caught at HC, 2026-07-24). This tool samples the committed
real evidence instead. Stdlib only; file inputs only (IND-1/IND-2).

Usage:
  python ivf/human/sample_s2_events.py --events s2_events.csv \
      --mt5 IVF_S2_XAUUSD_PERIOD_H1.csv [--per-group 10] [--seed 42]

The seed is fixed by default so the drawn sample is reproducible — the tool
chooses the events, not the person (anti-cherry-picking).
"""

from __future__ import annotations

import argparse, csv, random
from datetime import datetime, timezone

NS = 1_000_000_000

ap = argparse.ArgumentParser()
ap.add_argument("--events", required=True)
ap.add_argument("--mt5", required=True)
ap.add_argument("--per-group", type=int, default=10)
ap.add_argument("--seed", type=int, default=42)
a = ap.parse_args()

events = list(csv.DictReader(open(a.events, newline="", encoding="utf-8")))
bars = {int(r["time_close_sec"]): r
        for r in csv.DictReader(open(a.mt5, newline="", encoding="utf-8"))}

groups = {"seasonality": [e for e in events if e["event_type"].startswith("seasonality.")],
          "classical.rsi": [e for e in events if e["event_type"].startswith("classical.rsi.")]}

rng = random.Random(a.seed)
for name, evs in groups.items():
    pick = sorted(rng.sample(evs, min(a.per_group, len(evs))),
                  key=lambda e: int(e["ts"]))
    print(f"\n# HC sample — {name} ({len(pick)} of {len(evs)} real events, seed={a.seed})")
    for e in pick:
        ts = int(e["ts"])
        sec = ts // NS
        utc = datetime.fromtimestamp(sec, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        b = bars.get(sec)
        bar_txt = (f"bar open={b['open']} high={b['high']} low={b['low']} "
                   f"close={b['close']} rsi={b.get('rsi14','')}"
                   if b else "NO MATCHING BAR (check!)")
        print(f"  {utc}  {e['event_type']:34s} dir={e['direction']:>2s}  {bar_txt}")
print("\nChart check: for each RSI crossing, the RSI(14) line must cross the "
      "threshold ON that bar (close basis), not the next bar. For each "
      "seasonality marker, the session/day boundary must be where stated "
      "(post-weekend Mondays legitimately mark at the day's first bar — DEVQ-005).")
