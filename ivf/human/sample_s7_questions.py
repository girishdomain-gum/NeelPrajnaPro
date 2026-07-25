#!/usr/bin/env python3
"""IVF Sprint-7 HUMAN CHECK sampler: the observatory's questions on the chart. (rev 1)

Stratified per PROGRAM_RETRO HC-1: from the full-dataset FVG scan events,
pick 3 WEEKEND-SPANNING zones (the question's 18) and 2 intra-week zones
for contrast, and emit the two-line input for the EXISTING
ivf/mt5/IVF_S4_HC_Zones.mq5 (which re-verifies FVG zone edges from MT5's
own bars). The Owner looks at what the machine is WONDERING about.

Weekend flag (the scan's declared rule): for either adjacent forming-bar
pair, the gap exceeds one timeframe AND the endpoint dates (inclusive)
contain a Sat/Sun (UTC).

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/human/sample_s7_questions.py --events "datastore/bulk/xauusd_h1_training_smc_fvg_scan/part-00000.parquet" --bars datastore/bulk/xauusd_h1_full/part-00000.parquet --question-weekend <QUESTION_ID_A> --question-drift <QUESTION_ID_B> --seed 7
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime

NS = 1_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--bars", required=True)
    ap.add_argument("--question-weekend", required=True)
    ap.add_argument("--question-drift", required=True)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    bars = sorted(pq.read_table(a.bars).to_pylist(), key=lambda r: int(r["ts"]))
    idx = {int(r["ts"]): i for i, r in enumerate(bars)}
    events = [e for e in pq.read_table(a.events).to_pylist()
              if str(e.get("event_type", "")).startswith("smc.fvg.")]

    from datetime import UTC, datetime, timedelta

    def spans_weekend(a_ns: int, b_ns: int) -> bool:
        if b_ns - a_ns <= 3600 * NS:
            return False
        day = datetime.fromtimestamp(a_ns // NS, UTC).date()
        end = datetime.fromtimestamp(b_ns // NS, UTC).date()
        while day <= end:
            if day.weekday() >= 5:
                return True
            day += timedelta(days=1)
        return False

    weekend, intra = [], []
    for e in events:
        k = idx.get(int(e["ts"]))
        if k is None or k < 2 or k + 4 >= len(bars):
            continue
        w = (spans_weekend(int(bars[k - 2]["ts"]), int(bars[k - 1]["ts"]))
             or spans_weekend(int(bars[k - 1]["ts"]), int(bars[k]["ts"])))
        (weekend if w else intra).append(e)

    rng = random.Random(a.seed)
    picks = (rng.sample(weekend, min(3, len(weekend)))
             + rng.sample(intra, min(2, len(intra))))
    picks.sort(key=lambda e: int(e["ts"]))
    print(f"HC-S7 sample: {len(weekend)} weekend-spanning / {len(intra)} "
          f"intra-week FVGs; showing {len(picks)} (3 weekend + 2 intra, "
          f"seed={a.seed})\n")
    entries = []
    for e in picks:
        close_utc = datetime.fromtimestamp(int(e["ts"]) // NS, UTC)
        k = idx[int(e["ts"])]
        w = (spans_weekend(int(bars[k - 2]["ts"]), int(bars[k - 1]["ts"]))
             or spans_weekend(int(bars[k - 1]["ts"]), int(bars[k]["ts"])))
        tag = "WEEKEND" if w else "intra"
        span_h = (int(bars[k]["ts"]) - int(bars[k - 2]["ts"])) // (3600 * NS)
        print(f"{tag:8s} {e['event_type']:<14} close-ts "
              f"{close_utc:%Y-%m-%d %H:%M} UTC  zone "
              f"[{float(e['zone_lo']):.2f}, {float(e['zone_hi']):.2f}]  "
              f"pattern span {span_h}h")
        entries.append(
            f"{close_utc:%Y.%m.%d %H:%M}|{e['event_type']}"
            f"|{float(e['zone_hi']):.2f}|{float(e['zone_lo']):.2f}"
            f"|{int(e['direction'])}")
    prov = (f"PROV|question_weekend={a.question_weekend}"
            f"|question_drift={a.question_drift}"
            f"|events={a.events.replace('|', '/')}|seed={a.seed}"
            f"|sampler=sample_s7_questions rev1")
    print("\nContents for HC_S4_input.txt (the S4 zones tool is reused — "
          "copy BOTH lines exactly):")
    print(prov)
    print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
