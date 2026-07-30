#!/usr/bin/env python3
"""IVF NP-S1 AC-6, SS3 item 3: independent SWEEP recount.

Re-derives the SWEEP event count from the M5 bars using NP-ADR-008 SS5
v1.1's TEXT ALONE (no qrf import, no reading of np_feature_service.py /
np_probability_engine.py). Compared against the Developer's reported 325
(against the bespoke stack's historical 325, NP-ADR-008 SS5).

MECHANICAL DEFINITION (verbatim parameters from NP-ADR-008 SS3, frozen
parameters): bar timeframe 300s (M5) single; pivot_k 3; member window
200 bars; pool_tol 30.0 ticks fixed (TICK_SIZE 0.01 => 0.30 price units);
min_pen 5.0 ticks (0.05 price units); reclose_window 2 bars.

POOL_FORMED -- ADR text: "on each newly confirmed pivot: same-side pivots
within the last 200 bars priced within pool_tol of the new pivot; >=2
members; level = max of member prices (HIGH) / min (LOW), frozen at
formation; no new pool within pool_tol of an active same-side pool;
active until swept or invalidated."

SWEEP -- ADR text: "wick penetrates the level by >= min_pen ticks;
same-bar close back on the defended side -> sweep (reclose_bars 0);
else a 2-bar reclose window -- closing back inside -> sweep (max
penetration retained); failing -> invalidation, pool resolved, no event."

ASSUMPTIONS MADE WHERE THE ADR TEXT UNDERSPECIFIES THE MECHANICS (named
here, not hidden -- the call site `build_pools_and_sweeps(bars, swings,
30.0, 5.0, 3, 2)` takes a `swings` input the ADR text never defines the
computation of):
  (i) PIVOT/SWING DEFINITION: the ADR states only "a pivot at bar i is
      confirmed only at i+k" (anti-repaint contract), never the pivot
      TEST itself. This script uses the standard fractal definition
      consistent with pivot_k=3: bar i is a swing HIGH iff high[i] is
      the strict max of high[i-3..i+3]; swing LOW iff low[i] is the
      strict min of low[i-3..i+3] (ties broken toward the earliest bar,
      i.e. a later equal value is not itself a new pivot). This is a
      genuine, disclosed assumption -- a different pivot test would
      change the count.
  (ii) POOL-MEMBER CLUSTERING: when a new pivot confirms, this script
      collects every same-side pivot within the last 200 bars whose
      price is within pool_tol of the NEW pivot's price (a star/anchor
      clustering on the newest member, not full pairwise transitive
      clustering). If that set has >=2 members (including the new
      pivot) and no already-active same-side pool has a level within
      pool_tol of the new pivot, a pool forms.
  (iii) "no new pool within pool_tol" is read as: the new pivot forms no
      pool and is simply not added to any pool (it is not merged into
      the nearby active pool's membership either) -- ADR text does not
      say which.

Usage:
  python ivf/checks/sweep_recount_np_s1_ac6.py --bars <path-to-m5-bars-parquet>
    --report ivf/reports/ac6_sweep_recount.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time

TICK = 0.01
POOL_TOL = 30.0 * TICK  # 0.30
MIN_PEN = 5.0 * TICK  # 0.05
PIVOT_K = 3
MEMBER_WINDOW = 200
RECLOSE_WINDOW = 2
REPORTED_HISTORICAL = 325


def find_pivots(highs, lows, k):
    """(i) fractal pivot, confirmed at i+k. Returns list of (i, 'H'|'L', price)."""
    n = len(highs)
    pivots = []
    for i in range(k, n - k):
        window_h = highs[i - k : i + k + 1]
        if highs[i] == max(window_h) and window_h.count(highs[i]) == 1:
            pivots.append((i, "H", highs[i]))
        window_l = lows[i - k : i + k + 1]
        if lows[i] == min(window_l) and window_l.count(lows[i]) == 1:
            pivots.append((i, "L", lows[i]))
    pivots.sort(key=lambda p: p[0])
    return pivots


class Pool:
    __slots__ = ("side", "level", "members", "formed_at", "active")

    def __init__(self, side, level, members, formed_at):
        self.side = side
        self.level = level
        self.members = members
        self.formed_at = formed_at
        self.active = True


def build_pools_and_sweeps(opens, highs, lows, closes, pivots):
    """POOL_FORMED / SWEEP per NP-ADR-008 SS3 text + disclosed assumptions."""
    n = len(highs)
    pivots_by_confirm = {}
    for i, side, price in pivots:
        confirm_at = i + PIVOT_K
        pivots_by_confirm.setdefault(confirm_at, []).append((i, side, price))

    active_pools = {"H": [], "L": []}
    all_pools = []
    pool_formed_events = []
    sweep_events = []

    seen_pivots = {"H": [], "L": []}  # (orig_idx, price), confirmed and visible so far

    for bar_i in range(n):
        # 1) confirm any pivots that resolve at this bar (ADR anti-repaint: ts >= confirm bar)
        for orig_idx, side, price in pivots_by_confirm.get(bar_i, []):
            seen_pivots[side].append((orig_idx, price))
            # candidate members: same-side pivots within last 200 bars (of confirm bar)
            candidates = [
                (oi, p) for (oi, p) in seen_pivots[side] if bar_i - oi <= MEMBER_WINDOW
            ]
            cluster = [p for (oi, p) in candidates if abs(p - price) <= POOL_TOL]
            near_active = [
                pl for pl in active_pools[side] if pl.active and abs(pl.level - price) <= POOL_TOL
            ]
            if len(cluster) >= 2 and not near_active:
                level = max(cluster) if side == "H" else min(cluster)
                pool = Pool(side, level, cluster, bar_i)
                active_pools[side].append(pool)
                all_pools.append(pool)
                pool_formed_events.append({"bar": bar_i, "side": side, "level": level})

        # 2) check active pools for sweep/invalidation against this bar's wick
        for side in ("H", "L"):
            still_active = []
            for pool in active_pools[side]:
                if not pool.active:
                    continue
                if pool.formed_at >= bar_i:
                    still_active.append(pool)
                    continue
                if side == "H":
                    penetration = highs[bar_i] - pool.level
                else:
                    penetration = pool.level - lows[bar_i]
                if penetration >= MIN_PEN:
                    # penetrated -- check reclose on THIS bar first
                    reclosed = closes[bar_i] < pool.level if side == "H" else closes[bar_i] > pool.level
                    if reclosed:
                        sweep_events.append(
                            {
                                "pool_bar": pool.formed_at,
                                "side": side,
                                "level": pool.level,
                                "sweep_bar": bar_i,
                                "reclose_bars": 0,
                                "penetration": penetration,
                            }
                        )
                        pool.active = False
                        continue
                    # else: 2-bar reclose window from bar_i+1..bar_i+RECLOSE_WINDOW
                    max_pen = penetration
                    resolved = False
                    for j in range(1, RECLOSE_WINDOW + 1):
                        bj = bar_i + j
                        if bj >= n:
                            break
                        pen_j = (highs[bj] - pool.level) if side == "H" else (pool.level - lows[bj])
                        max_pen = max(max_pen, pen_j)
                        reclosed_j = closes[bj] < pool.level if side == "H" else closes[bj] > pool.level
                        if reclosed_j:
                            sweep_events.append(
                                {
                                    "pool_bar": pool.formed_at,
                                    "side": side,
                                    "level": pool.level,
                                    "sweep_bar": bj,
                                    "reclose_bars": j,
                                    "penetration": max_pen,
                                }
                            )
                            pool.active = False
                            resolved = True
                            break
                    if not resolved:
                        pool.active = False  # invalidation, no event
                    continue
                still_active.append(pool)
            active_pools[side] = still_active

    return pool_formed_events, sweep_events


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    df = pq.read_table(a.bars).to_pydict()
    opens, highs, lows, closes = df["open"], df["high"], df["low"], df["close"]
    n = len(highs)

    pivots = find_pivots(highs, lows, PIVOT_K)
    pool_events, sweep_events = build_pools_and_sweeps(opens, highs, lows, closes, pivots)

    report = {
        "check": "ac6_sweep_recount",
        "rev": 1,
        "run_utc": int(time.time()),
        "n_bars": n,
        "n_pivots": len(pivots),
        "n_pools_formed": len(pool_events),
        "n_sweeps": len(sweep_events),
        "reported_historical": REPORTED_HISTORICAL,
        "agrees_with_325": len(sweep_events) == REPORTED_HISTORICAL,
        "assumptions": [
            "pivot test: strict-max/min fractal over [i-3, i+3], unique extremum",
            "pool clustering: star/anchor on the newest confirmed pivot, not full pairwise",
            "near-active same-side pool suppresses new pool formation entirely (no merge)",
        ],
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
