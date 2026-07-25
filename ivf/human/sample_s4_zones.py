#!/usr/bin/env python3
"""IVF Sprint-4 HUMAN CHECK sampler: SMC zone events for chart overlay. (rev 1)

Samples N events from an SMC EventFrame parquet and emits the input line
for ivf/mt5/IVF_S4_HC_Zones.mq5, including an ADR-009 provenance line so
every screenshot is self-contained evidence.

EventFrame columns used (Blueprint §4.3): ts (int64 ns, CLOSE basis),
event_type, direction, zone_hi, zone_lo.

Usage (bash-ready, from F:/QRF — replace the --events path with the real
events parquet for the dataset under review):
  uv run python ivf/human/sample_s4_zones.py --events datastore/bulk/xauusd_h1_sample_events_smc/part-00000.parquet --dataset xauusd_h1_sample --manifest 01KYAWHZ6A9X3YZQ2W0BDRFDS1 --n 5 --seed 4

INDEPENDENCE: pyarrow only; no qrf imports; deterministic (seeded).
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime

NS = 1_000_000_000


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--seed", type=int, default=4)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    rows = [r for r in pq.read_table(a.events).to_pylist()
            if str(r.get("event_type", "")).startswith("smc.")]
    if not rows:
        print("No smc.* events in this parquet — nothing to sample.")
        return 1
    rng = random.Random(a.seed)
    picks = sorted(rng.sample(range(len(rows)), min(a.n, len(rows))))

    print(f"HC-S4 sample: {len(picks)} of {len(rows)} smc events "
          f"(seed={a.seed})\n")
    entries = []
    for i in picks:
        r = rows[i]
        close_utc = datetime.fromtimestamp(int(r["ts"]) // NS, UTC)
        print(f"row {i:5d}  {r['event_type']:<22} close-ts "
              f"{close_utc:%Y-%m-%d %H:%M} UTC  "
              f"zone [{float(r['zone_lo']):.2f}, {float(r['zone_hi']):.2f}] "
              f"dir {int(r['direction']):+d}")
        entries.append(
            f"{close_utc:%Y.%m.%d %H:%M}|{r['event_type']}"
            f"|{float(r['zone_hi']):.2f}|{float(r['zone_lo']):.2f}"
            f"|{int(r['direction'])}"
        )
    prov = (f"PROV|dataset={a.dataset}|manifest={a.manifest}"
            f"|events={a.events.replace('|', '/')}|seed={a.seed}"
            f"|sampler=sample_s4_zones rev1")
    print("\nContents for HC_S4_input.txt (copy BOTH lines exactly):")
    print(prov)
    print(";".join(entries))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
