#!/usr/bin/env python3
"""IVF Sprint-6 HUMAN CHECK sampler: the verdict's own trades. (rev 1)

Samples N trades directly from the VERDICT's trades-manifest parquet —
the exact trades the FAIL was computed from — and emits the two-line
input for the EXISTING ivf/mt5/IVF_S5_HC_Trades.mq5 tool (same format:
the chart re-verifies each entry/exit price against its bar's open in
MT5's own series). The Owner sees, on the chart, the year that said no.

Usage (paste in git bash, from /f/QRF):
  uv run python ivf/human/sample_s6_verdict_trades.py --trades datastore/bulk/verdict_trades.h001_fvg_follow_through/part-00000.parquet --verdict 01KYC7Y2KWYGXH73V1R9P57MYA --hypothesis 01KYC7Y1S2534DVYHWHNCZGTGZ --n 5 --seed 6
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime

NS = 1_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True)
    ap.add_argument("--verdict", required=True)
    ap.add_argument("--hypothesis", required=True)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=6)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    rows = pq.read_table(a.trades).to_pylist()
    if not rows:
        print("no trades in the manifest parquet — nothing to sample")
        return 1
    rng = random.Random(a.seed)
    picks = sorted(rng.sample(range(len(rows)), min(a.n, len(rows))))
    print(f"HC-S6 sample: {len(picks)} of {len(rows)} verdict trades "
          f"(seed={a.seed})\n")
    entries = []
    for i in picks:
        t = rows[i]
        e = datetime.fromtimestamp(int(t["entry_ts"]) // NS, UTC)
        x = datetime.fromtimestamp(int(t["exit_ts"]) // NS, UTC)
        print(f"trade {i:4d}  dir {int(t['direction']):+d}  "
              f"entry {e:%Y-%m-%d %H:%M} @ {float(t['entry_price']):.2f}  "
              f"exit {x:%Y-%m-%d %H:%M} @ {float(t['exit_price']):.2f}  "
              f"gross {float(t['gross_pnl']):+.2f}  "
              f"net {float(t['net_pnl']):+.2f}"
              + (f"  fold {int(t['fold'])}" if "fold" in t else ""))
        entries.append(
            f"{e:%Y.%m.%d %H:%M}|{x:%Y.%m.%d %H:%M}|{int(t['direction'])}"
            f"|{float(t['entry_price']):.2f}|{float(t['exit_price']):.2f}"
            f"|{float(t['gross_pnl']):+.2f}|{float(t['net_pnl']):+.2f}")
    prov = (f"PROV|verdict={a.verdict}|hypothesis={a.hypothesis}"
            f"|trades={a.trades.replace('|', '/')}|seed={a.seed}"
            f"|sampler=sample_s6_verdict_trades rev1")
    print("\nContents for HC_S5_input.txt (the S5 chart tool is reused — "
          "copy BOTH lines exactly):")
    print(prov)
    print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
