#!/usr/bin/env python3
"""IVF Sprint-3 HUMAN CHECK sampler: bars for eyeball comparison vs MT5. (rev 1)

Owner procedure (HC-S3):
  1. Run:  uv run python ivf/human/sample_s3_bars.py \
               --clean datastore/bulk/xauusd_h1_sample/part-00000.parquet \
               [--n 5] [--seed 3]
  2. For each printed bar, open the XAUUSD H1 chart in MT5, find the bar
     whose OPEN time (shown in UTC) matches, and compare O/H/L/C by eye.
     Remember OBS-4: MT5's bar label is the OPEN time; the stored `ts`
     shown alongside is the CLOSE time (open + 1h).
  3. All sampled bars match -> HC PASS; any mismatch -> STOP, file it.

INDEPENDENCE: no qrf imports; pyarrow reader only; deterministic sample
(seeded) so the same rows can be re-checked.
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", required=True)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--mql", action="store_true",
                    help="also print the InpBars string for "
                         "ivf/mt5/IVF_S3_HC_Screenshot.mq5")
    a = ap.parse_args()

    import pyarrow.parquet as pq

    rows = pq.read_table(a.clean).to_pylist()
    rng = random.Random(a.seed)
    picks = sorted(rng.sample(range(len(rows)), min(a.n, len(rows))))
    print(f"HC-S3 sample: {len(picks)} of {len(rows)} bars (seed={a.seed})\n")
    for i in picks:
        r = rows[i]
        open_utc = datetime.fromtimestamp(int(r["time"]), UTC)
        close_utc = datetime.fromtimestamp(int(r["ts"]) // 1_000_000_000, UTC)
        print(
            f"row {i:4d}  OPEN {open_utc:%Y-%m-%d %H:%M} UTC  "
            f"(close ts {close_utc:%H:%M})\n"
            f"          O={r['open']:.2f}  H={r['high']:.2f}  "
            f"L={r['low']:.2f}  C={r['close']:.2f}"
        )
    print("\nCompare each bar against the MT5 chart (bar label = OPEN time).")
    if a.mql:
        entries = []
        for i in picks:
            r = rows[i]
            t = datetime.fromtimestamp(int(r["time"]), UTC)
            entries.append(
                f"{t:%Y.%m.%d %H:%M}|{r['open']:.2f}|{r['high']:.2f}"
                f"|{r['low']:.2f}|{r['close']:.2f}"
            )
        print("\nInpBars for IVF_S3_HC_Screenshot.mq5 (copy the next line):")
        print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
