#!/usr/bin/env python3
"""IVF Sprint-2 check: detectors vs MT5-derived independent references. (rev 3)

rev 3 (DEVQ-005): §B DOW expectations rebuilt to the RATIFIED contract —
`seasonality.dow.<mon..fri>` fires at the ts of the FIRST bar whose UTC
epoch-day differs from the previous bar's (close-time basis), weekday from
that ts, weekends silent. The previous midnight-open-bar assumption made the
comparison vacuous on gapped feeds (0/504 midnight bars on real XAUUSD) and
was the artifact; the detector's contract stands. Weekday is computed here
from epoch arithmetic (1970-01-01 = Thursday), NOT from the CSV's open-time
`dow` column, which disagrees on 23:00->00:00 bars. The --skip-bars boundary
day is excluded symmetrically on both sides.
rev 2: --skip-bars warm-up exclusion (MT5 RSI is history-seeded).

INDEPENDENCE: stdlib only; imports nothing from qrf. Inputs:
  --mt5     IVF_S2_Export.mq5 CSV (time_open_sec,time_close_sec,o,h,l,c,rsiN,dow)
  --events  qrf event CSV (ts,event_type,direction; ts int ns, CLOSE-time basis)
  --sessions  e.g. "london=28800-57600" (UTC seconds-of-day, [start,end)),
              repeatable — must match the registered detector params.
Checks: A) RSI crossings from MT5's OWN rsi column vs qrf events (EXACT;
near-threshold divergence within --amber-band -> AMBER, REV-S2 OBS-5).
B) session open/close + DOW markers per the ratified contract vs qrf events
(EXACT). Report: IVF §5.2 JSON. Exit 0 GREEN, 2 AMBER, 1 RED.
"""

from __future__ import annotations

import argparse, csv, json, sys, time

NS = 1_000_000_000
DAY = 86_400
# 1970-01-01 was a Thursday; index into names with (epoch_day + 3) % 7, Mon=0.
_WD = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def weekday_of_sec(sec: int) -> str:
    return _WD[((sec // DAY) + 3) % 7]


def load_mt5(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rsi_key = [k for k in r if k.startswith("rsi")][0]
            rows.append({
                "open_s": int(r["time_open_sec"]),
                "close_s": int(r["time_close_sec"]),
                "close": float(r["close"]),
                "rsi": (float(r[rsi_key]) if r[rsi_key] else None),
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
    ap.add_argument("--skip-bars", type=int, default=50,
                    help="exclude first N bars from BOTH sides (RSI seeding)")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    bars = load_mt5(a.mt5)
    events = load_events(a.events)

    # Symmetric warm-up exclusion (rev 2) + boundary-day exclusion (rev 3).
    skip_day: int | None = None
    if a.skip_bars > 0 and len(bars) > a.skip_bars:
        cutoff_ns = bars[a.skip_bars]["open_s"] * NS
        bars = bars[a.skip_bars:]
        events = [e for e in events if e["ts"] >= cutoff_ns]
        skip_day = bars[0]["close_s"] // DAY  # partial first day: both sides skip

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
            bar = next((b for b in bars if b["close_s"] * NS == ts), None)
            near = bool(bar and bar["rsi"] is not None and
                        min(abs(bar["rsi"] - a.rsi_overbought),
                            abs(bar["rsi"] - a.rsi_oversold)) <= a.amber_band)
            add("AMBER" if near else "RED", f"A.rsi.{ts}.extra",
                "no reference crossing", f"qrf event dir {d}",
                "qrf crossing absent in MT5-derived reference")

    # ---- B) Sessions + DOW (ratified contract, rev 3) -----------------------
    sess = {}
    for spec in a.sessions:
        name, rng = spec.split("=")
        lo, hi = (int(x) for x in rng.split("-"))
        sess[name] = (lo, hi)

    exp_seas = set()

    # B1: DOW — first bar (close-time basis) of each new UTC epoch-day.
    prev_day = None
    for b in bars:
        d0 = b["close_s"] // DAY
        if prev_day is None:
            prev_day = d0  # boundary day of --skip-bars: no expectation
            continue
        if d0 != prev_day:
            wd = weekday_of_sec(b["close_s"])
            if wd in ("mon", "tue", "wed", "thu", "fri"):
                exp_seas.add((b["close_s"] * NS, f"seasonality.dow.{wd}"))
            prev_day = d0

    # B2: session open/close — membership transitions on close-time sod.
    prev_member = {name: False for name in sess}
    first = True
    for b in bars:
        sod = b["close_s"] % DAY
        for nm, (lo, hi) in sess.items():
            member = lo <= sod < hi
            if not first:
                if member and not prev_member[nm]:
                    exp_seas.add((b["close_s"] * NS, "seasonality.session.open"))
                elif not member and prev_member[nm]:
                    exp_seas.add((b["close_s"] * NS, "seasonality.session.close"))
            prev_member[nm] = member
        first = False

    got_seas = set()
    for e in events:
        if not e["event_type"].startswith("seasonality."):
            continue
        if skip_day is not None and e["ts"] // NS // DAY == skip_day \
                and e["event_type"].startswith("seasonality.dow."):
            continue  # boundary-day dow markers excluded on both sides
        got_seas.add((e["ts"], e["event_type"]))
    # First filtered bar can't show a transition on the qrf side either:
    # drop got session markers at the very first bar's ts to stay symmetric.
    first_ts = bars[0]["close_s"] * NS if bars else None
    got_seas = {k for k in got_seas
                if not (k[0] == first_ts and k[1].startswith("seasonality.session."))}

    for k in sorted(exp_seas - got_seas):
        add("RED", f"B.seas.{k[0]}.{k[1]}.missing", k[1], "absent", "expected marker missing")
    for k in sorted(got_seas - exp_seas):
        add("RED", f"B.seas.{k[0]}.{k[1]}.extra", "no marker", k[1], "unexpected marker")

    reds = sum(1 for d in diffs if d["status"] == "RED")
    ambers = sum(1 for d in diffs if d["status"] == "AMBER")
    verdict = "RED" if reds else ("AMBER" if ambers else "GREEN")
    report = {"check_id": "s2.detectors_vs_mt5", "sprint": 2,
              "class": "EXACT(+declared amber band, REV-S2 OBS-5)",
              "inputs": {"mt5": a.mt5, "events": a.events,
                         "skip_bars": a.skip_bars, "check_rev": 3},
              "rows_compared": len(bars),
              "green": len(bars) - len(diffs), "amber": ambers, "red": reds,
              "diffs": diffs, "verdict": verdict, "generated_ts": time.time_ns()}
    if a.report:
        json.dump(report, open(a.report, "w", encoding="utf-8"), indent=2)
    print(f"[IVF s2 rev3] bars={len(bars)} qrf_events={len(events)} verdict={verdict} "
          f"(red={reds} amber={ambers})")
    for d in diffs[:25]:
        print(f"  {d['status']} {d['key']}: {d['delta']}")
    return 1 if verdict == "RED" else (2 if verdict == "AMBER" else 0)


if __name__ == "__main__":
    sys.exit(main())
