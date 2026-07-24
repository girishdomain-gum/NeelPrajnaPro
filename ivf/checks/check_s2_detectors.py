#!/usr/bin/env python3
"""IVF Sprint-2 check: detectors vs MT5-derived independent references.

INDEPENDENCE: stdlib only; imports nothing from qrf. Consumes two CSV files:
  --mt5     IVF_S2_Export.mq5 output (time_open_sec,time_close_sec,o,h,l,c,
            rsiN,dow)
  --events  qrf-side event export: header ts,event_type,direction
            (ts in int nanoseconds, close-time basis; see checklist_s2.md
            for the sanctioned qrf-side export snippet)
  --sessions  session spec like "london=28800-57600" (UTC seconds-of-day,
            [start,end)), repeatable. Must match the detector's registered
            params (read them from the journal's instrument_registered
            record — by eye, not by import).
  --rsi-overbought / --rsi-oversold  thresholds (default 70/30)

What it does, independently of qrf code:
  A) Recomputes RSI crossings from MT5's OWN rsi column (prev<=OB<cur up;
     prev>=OS>cur down), warm-up = rows with empty rsi skipped, and compares
     to the qrf classical.rsi events: EXACT on (ts_close, direction).
     Divergences where MT5 RSI is within --amber-band (default 0.5) of the
     threshold are AMBER (near-threshold implementation sensitivity,
     REV-S2 OBS-5); all other divergences are RED.
  B) Recomputes session open/close and day-start DOW markers from bar
     times and compares to qrf seasonality events: EXACT.

Report: IVF §5.2 JSON to --report; human summary to stdout.
Exit 0 GREEN, 2 AMBER (all ambers explained-able), 1 RED.
"""

from __future__ import annotations

import argparse, csv, json, sys, time

NS = 1_000_000_000


def load_mt5(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append({
                "open_s": int(r["time_open_sec"]),
                "close_s": int(r["time_close_sec"]),
                "close": float(r["close"]),
                "rsi": (float(r[[k for k in r if k.startswith("rsi")][0]])
                        if r[[k for k in r if k.startswith("rsi")][0]] else None),
                "dow": int(r["dow"]),
            })
    rows.sort(key=lambda x: x["open_s"])
    return rows


def load_events(path):
    ev = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            ev.append({"ts": int(r["ts"]), "event_type": r["event_type"].strip(),
                       "direction": int(r["direction"])})
    return ev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mt5", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--sessions", action="append", default=[])
    ap.add_argument("--rsi-overbought", type=float, default=70.0)
    ap.add_argument("--rsi-oversold", type=float, default=30.0)
    ap.add_argument("--amber-band", type=float, default=0.5)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    bars = load_mt5(a.mt5)
    events = load_events(a.events)
    diffs = []

    def add(status, key, expected, got, why):
        diffs.append({"key": key, "expected": str(expected)[:120],
                      "got": str(got)[:120], "delta": why,
                      "band": "EXACT" if status == "RED" else f"rsi±{a.amber_band}",
                      "status": status, "explanation": None})

    # ---- A) RSI crossings from MT5's own RSI column -------------------------
    exp_cross = {}
    prev = None
    for b in bars:
        cur = b["rsi"]
        if prev is not None and cur is not None:
            if prev <= a.rsi_overbought < cur:
                exp_cross[b["close_s"] * NS] = (-1, cur)
            elif prev >= a.rsi_oversold > cur:
                exp_cross[b["close_s"] * NS] = (+1, cur)
        prev = cur

    got_cross = {e["ts"]: e["direction"] for e in events
                 if e["event_type"].startswith("classical.rsi.")}

    for ts, (d, rsi_v) in sorted(exp_cross.items()):
        near = min(abs(rsi_v - a.rsi_overbought), abs(rsi_v - a.rsi_oversold)) <= a.amber_band
        if ts not in got_cross:
            add("AMBER" if near else "RED", f"A.rsi.{ts}.missing",
                f"crossing dir {d} (mt5 rsi {rsi_v:.3f})", "no qrf event",
                "reference crossing absent in qrf events")
        elif got_cross[ts] != d:
            add("RED", f"A.rsi.{ts}.direction", d, got_cross[ts], "direction mismatch")
    for ts, d in sorted(got_cross.items()):
        if ts not in exp_cross:
            # near-threshold? find the bar
            bar = next((b for b in bars if b["close_s"] * NS == ts), None)
            near = bool(bar and bar["rsi"] is not None and
                        min(abs(bar["rsi"] - a.rsi_overbought),
                            abs(bar["rsi"] - a.rsi_oversold)) <= a.amber_band)
            add("AMBER" if near else "RED", f"A.rsi.{ts}.extra",
                "no reference crossing", f"qrf event dir {d}",
                "qrf crossing absent in MT5-derived reference")

    # ---- B) Sessions + DOW from bar times -----------------------------------
    sess = {}
    for spec in a.sessions:
        name, rng = spec.split("=")
        lo, hi = (int(x) for x in rng.split("-"))
        sess[name] = (lo, hi)

    exp_seas = set()
    day_seen = set()
    dow_name = {1: "mon", 2: "tue", 3: "wed", 4: "thu", 5: "fri"}
    open_times = {b["open_s"] for b in bars}
    for b in bars:
        day = b["open_s"] - (b["open_s"] % 86400)
        sec = b["open_s"] % 86400
        if day not in day_seen and b["dow"] in dow_name:
            day_seen.add(day)
            if b["open_s"] == day:  # marker only when the day-start bar exists
                exp_seas.add((day * NS, f"seasonality.dow.{dow_name[b['dow']]}"))
        for nm, (lo, hi) in sess.items():
            if sec == lo:
                exp_seas.add((b["open_s"] * NS, "seasonality.session.open"))
            if sec == hi and b["open_s"] in open_times:
                exp_seas.add((b["open_s"] * NS, "seasonality.session.close"))

    got_seas = {(e["ts"], e["event_type"]) for e in events
                if e["event_type"].startswith("seasonality.")}
    for k in sorted(exp_seas - got_seas):
        add("RED", f"B.seas.{k[0]}.{k[1]}.missing", k[1], "absent", "expected marker missing")
    for k in sorted(got_seas - exp_seas):
        add("RED", f"B.seas.{k[0]}.{k[1]}.extra", "no marker", k[1], "unexpected marker")

    reds = sum(1 for d in diffs if d["status"] == "RED")
    ambers = sum(1 for d in diffs if d["status"] == "AMBER")
    verdict = "RED" if reds else ("AMBER" if ambers else "GREEN")
    report = {"check_id": "s2.detectors_vs_mt5", "sprint": 2,
              "class": "EXACT(+declared amber band, REV-S2 OBS-5)",
              "inputs": {"mt5": a.mt5, "events": a.events},
              "rows_compared": len(bars),
              "green": len(bars) - len(diffs), "amber": ambers, "red": reds,
              "diffs": diffs, "verdict": verdict, "generated_ts": time.time_ns()}
    if a.report:
        json.dump(report, open(a.report, "w", encoding="utf-8"), indent=2)
    print(f"[IVF s2] bars={len(bars)} qrf_events={len(events)} verdict={verdict} "
          f"(red={reds} amber={ambers})")
    for d in diffs[:25]:
        print(f"  {d['status']} {d['key']}: {d['delta']}")
    return 1 if verdict == "RED" else (2 if verdict == "AMBER" else 0)


if __name__ == "__main__":
    sys.exit(main())
