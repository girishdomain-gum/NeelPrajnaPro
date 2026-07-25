#!/usr/bin/env python3
"""IVF Sprint-5 HUMAN CHECK sampler: real engine trades for chart overlay. (rev 1)

Runs the REAL audited engine (in a subprocess, black-box) over real bars +
real SMC FVG events, samples N closed trades, and emits the two-line input
for ivf/mt5/IVF_S5_HC_Trades.mq5 — provenance line + trade entries. The MT5
script then re-verifies, from ITS OWN series, that each entry filled at the
next bar's open (the no-look-ahead rule, checked by an independent lens).

Usage (bash-ready, from F:/QRF):
  uv run python ivf/human/sample_s5_trades.py --bars datastore/bulk/xauusd_h1_sample/part-00000.parquet --events datastore/bulk/xauusd_h1_sample_smc_fvg_events/part-00000.parquet --dataset xauusd_h1_sample --manifest 01KYB7WQFND907DMH550GPKMW0 --hold 4 --n 5 --seed 5
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
from datetime import UTC, datetime

NS = 1_000_000_000

RUN_ENGINE = r"""
import json, sys
import pandas as pd
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.utility.cost_models import load_cost_model
bars_path, events_path, hold, seed = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
bars = pd.read_parquet(bars_path)[["ts", "open", "high", "low", "close"]]
ev = pd.read_parquet(events_path)
ev = ev[ev["event_type"].astype(str).str.startswith("smc.fvg.")][["ts", "direction", "strength"]]
t = EventEngine().simulate(bars, ev, load_cost_model("xauusd_retail_median"),
                           seed=seed, execution=ExecutionSpec(hold_bars=hold))
print(json.dumps(t.canonical_payload()))
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--hold", type=int, default=4)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=5)
    a = ap.parse_args()

    p = subprocess.run(
        [sys.executable, "-c", RUN_ENGINE, a.bars, a.events, str(a.hold),
         str(a.seed)],
        capture_output=True, text=True)
    if p.returncode != 0:
        print("engine run failed:\n" + p.stderr[-2000:])
        return 1
    payload = json.loads(p.stdout.strip().splitlines()[-1])
    trades = payload["trades"]
    if not trades:
        print("engine produced no closed trades — nothing to sample.")
        return 1

    rng = random.Random(a.seed)
    picks = sorted(rng.sample(range(len(trades)), min(a.n, len(trades))))
    print(f"HC-S5 sample: {len(picks)} of {len(trades)} closed trades "
          f"(hold={a.hold}, seed={a.seed}, "
          f"n_dropped_tail={payload['n_dropped_tail']})\n")
    entries = []
    for i in picks:
        t = trades[i]
        e_utc = datetime.fromtimestamp(int(t["entry_ts"]) // NS, UTC)
        x_utc = datetime.fromtimestamp(int(t["exit_ts"]) // NS, UTC)
        print(f"trade {i:4d}  dir {int(t['direction']):+d}  "
              f"entry {e_utc:%Y-%m-%d %H:%M} @ {t['entry_price']:.2f}  "
              f"exit {x_utc:%Y-%m-%d %H:%M} @ {t['exit_price']:.2f}  "
              f"gross {t['gross_pnl']:+.2f}  net {t['net_pnl']:+.2f}")
        entries.append(
            f"{e_utc:%Y.%m.%d %H:%M}|{x_utc:%Y.%m.%d %H:%M}"
            f"|{int(t['direction'])}|{t['entry_price']:.2f}"
            f"|{t['exit_price']:.2f}|{t['gross_pnl']:+.2f}|{t['net_pnl']:+.2f}"
        )
    prov = (f"PROV|dataset={a.dataset}|manifest={a.manifest}"
            f"|hold={a.hold}|seed={a.seed}|engine_seed={payload['seed']}"
            f"|sampler=sample_s5_trades rev1")
    print("\nContents for HC_S5_input.txt (copy BOTH lines exactly):")
    print(prov)
    print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
