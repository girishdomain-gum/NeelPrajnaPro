#!/usr/bin/env python3
"""IVF NP-S1 AC-6, SS3 item 3: independent SWEEP recount. (rev 2)

rev 2 re-derives from NP-ADR-008 APPENDIX B SS B.1-B.5 (the pinned
mechanics, ARCH-NP-003) instead of rev 1's own disclosed assumptions from
SS3's under-specified text. Still no qrf import, still no reading of
np_feature_service.py / np_probability_engine.py -- Appendix B is the
sole source of the mechanics below.

MECHANICAL DEFINITION, PINNED (Appendix B.1-B.5; frozen parameters from
NP-ADR-008 SS3: pivot_k 3, member window 200 bars, pool_tol 30 ticks /
0.30, min_pen 5 ticks / 0.05, reclose_window 2 bars):

  B.1 PIVOT: bar i is a pivot HIGH iff high[i] is the STRICT max of
      [i-k, i+k]; symmetrically LOW on low[i]. Both may be emitted at the
      same bar. Confirmed (visible) only at bar i+k.
  B.2 POOL MEMBERSHIP is ANCHORED on the newest pivot r, never pairwise/
      transitive: same-side history first pruned to formation_index with
      (current_confirmation_index - formation_index) <= 200 (permanent);
      mates are surviving pivots within pool_tol of r's price ALONE; pool
      forms iff >=1 mate exists (>=2 members including r); r is appended
      to history only AFTER the mate search (cannot mate with itself).
  B.3 LEVEL = max/min of members (including r), frozen at formation. The
      candidate is SUPPRESSED ENTIRELY if any CURRENTLY ACTIVE same-side
      pool lies within pool_tol of the CANDIDATE'S COMPUTED LEVEL (not of
      r's raw price) -- no merge, no update. Resolved (swept/invalidated)
      pools never suppress.
  B.4 PER-BAR ORDER: at each bar, sweep/invalidation checks against every
      active pool run FIRST; pivot-to-pool processing runs SECOND. A pool
      cannot form and be swept on the same bar.
  B.5 PENETRATION/RECLOSE: penetration HIGH: high[i] >= level+min_pen;
      LOW: low[i] <= level-min_pen. Reclose HIGH: close[i] < level; LOW:
      close[i] > level (strict). First penetrating bar p recloses same
      bar -> SWEEP (reclose_bars=0). Else reclose is TESTABLE AT BARS
      p+1 AND p+2 -- recloses at either -> SWEEP; invalidation fires at
      the first bar with (i-p) >= 2 without a reclose. Max penetration
      retained and reported on the SWEEP.

WHAT CHANGED FROM REV 1's THREE DISCLOSED ASSUMPTIONS (per ARCH-NP-003 SS2):
  (i) pivot test -- UNCHANGED. Rev 1's strict-extremum fractal over
      [i-k,i+k] with both-sides-emittable-at-one-bar already matches B.1
      exactly.
  (ii) pool clustering (star/anchor on newest pivot) -- UNCHANGED in its
      distance rule (distance to r alone), but rev 1 folded r into the
      candidate history array before filtering by pool_tol, which is
      mathematically identical to B.2's "mates found first, r appended
      after" for the purposes of membership and level (r trivially
      satisfies distance-0-to-itself either way) -- no behavioural change.
  (iii) suppression -- CHANGED, and this is the fix that mattered. Rev 1
      checked candidate active-pool proximity against r's OWN raw price;
      B.3 requires the check against the CANDIDATE POOL'S COMPUTED LEVEL
      (max/min of the whole cluster, which can differ from r's own price
      when r is not the cluster's own extremum). This under-suppressed
      rev 1 relative to the pinned rule whenever r's price was not the
      pool's eventual level.
  ALSO CHANGED, beyond rev 1's three named assumptions: rev 1's per-bar
  loop processed pivot-to-pool formation BEFORE the sweep/invalidation
  pass; B.4 pins the OPPOSITE order. This mattered whenever an active pool
  P was resolved (swept/invalidated) on the SAME bar a new pivot's
  candidate level would have been suppressed by P: under rev 1's order P
  was still "active" (not yet resolved this bar) at candidate-check time,
  over-suppressing; under B.4's pinned order P is already resolved by
  then and does not suppress. Rev 1's `formed_at >= bar_i` guard already
  prevented a pool from being swept the same bar it formed, so that one
  consequence of B.4 was already satisfied by accident -- but the
  suppression-ordering consequence above was not, and is fixed here by
  literally reordering the per-bar loop to match B.4.
  B.5 (reclose testable at p, p+1 AND p+2) -- UNCHANGED. Rev 1's
  `range(1, RECLOSE_WINDOW+1)` already checked exactly p+1 and p+2 in
  addition to p itself, matching B.5 exactly; re-verified, not modified.

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
REPORTED_HISTORICAL_SWEEPS = 325
EXPECTED_PIVOTS = 3099
EXPECTED_POOLS = 465
EXPECTED_SWEEPS = 325


def find_pivots(highs, lows, k):
    """B.1: strict-extremum pivot, both sides emittable at one bar, confirmed at i+k."""
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


def build_pools_and_sweeps(highs, lows, closes, pivots):
    """POOL_FORMED / SWEEP per Appendix B.1-B.5, pinned."""
    n = len(highs)
    pivots_by_confirm = {}
    for i, side, price in pivots:
        confirm_at = i + PIVOT_K
        pivots_by_confirm.setdefault(confirm_at, []).append((i, side, price))

    active_pools = {"H": [], "L": []}
    pool_formed_events = []
    sweep_events = []
    first_divergence_bar = None  # reserved for diagnostic use if counts miss target

    # B.2: same-side history of CONFIRMED, VISIBLE pivots (formation_index, price).
    seen_pivots = {"H": [], "L": []}

    for bar_i in range(n):
        # --- B.4 step 1: sweep / invalidation checks FIRST, against every active pool ---
        for side in ("H", "L"):
            still_active = []
            for pool in active_pools[side]:
                if pool.formed_at >= bar_i:
                    # cannot be checked before/at its own formation bar (B.4 consequence)
                    still_active.append(pool)
                    continue
                if side == "H":
                    penetration = highs[bar_i] - pool.level
                else:
                    penetration = pool.level - lows[bar_i]
                if penetration < MIN_PEN:
                    still_active.append(pool)
                    continue
                # penetrated -- B.5: reclose testable at p (this bar), else p+1, p+2
                p = bar_i
                reclosed = closes[bar_i] < pool.level if side == "H" else closes[bar_i] > pool.level
                if reclosed:
                    sweep_events.append(
                        {"pool_bar": pool.formed_at, "side": side, "level": pool.level,
                         "sweep_bar": bar_i, "reclose_bars": 0, "penetration": penetration}
                    )
                    continue  # resolved, drop from active (not appended to still_active)
                max_pen = penetration
                resolved = False
                for j in (1, 2):
                    bj = p + j
                    if bj >= n:
                        break
                    pen_j = (highs[bj] - pool.level) if side == "H" else (pool.level - lows[bj])
                    max_pen = max(max_pen, pen_j)
                    reclosed_j = closes[bj] < pool.level if side == "H" else closes[bj] > pool.level
                    if reclosed_j:
                        sweep_events.append(
                            {"pool_bar": pool.formed_at, "side": side, "level": pool.level,
                             "sweep_bar": bj, "reclose_bars": j, "penetration": max_pen}
                        )
                        resolved = True
                        break
                # if not resolved: invalidation at first bar with (bj - p) >= 2, no event
                # (either way the pool is resolved and dropped from active)
                if not resolved:
                    pass
            active_pools[side] = still_active

        # --- B.4 step 2: pivot-to-pool processing SECOND ---
        for orig_idx, side, price in pivots_by_confirm.get(bar_i, []):
            # B.2.1: prune history to formation_index within 200 of THIS confirmation bar
            candidates = [
                (oi, p) for (oi, p) in seen_pivots[side] if bar_i - oi <= MEMBER_WINDOW
            ]
            # B.2.2: mates = candidates within pool_tol of r's price ALONE
            mates = [p for (oi, p) in candidates if abs(p - price) <= POOL_TOL]
            # B.2.3/4: pool forms iff >=1 mate; r joins the cluster (and the history) after the search
            if mates:
                cluster = mates + [price]
                level = max(cluster) if side == "H" else min(cluster)
                # B.3: suppression is against the CANDIDATE'S COMPUTED LEVEL, not r's raw price
                near_active = any(
                    abs(pl.level - level) <= POOL_TOL for pl in active_pools[side]
                )
                if not near_active:
                    pool = Pool(side, level, cluster, bar_i)
                    active_pools[side].append(pool)
                    pool_formed_events.append({"bar": bar_i, "side": side, "level": level})
            seen_pivots[side].append((orig_idx, price))

    return pool_formed_events, sweep_events


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bars", required=True)
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    import pyarrow.parquet as pq

    df = pq.read_table(a.bars).to_pydict()
    highs, lows, closes = df["high"], df["low"], df["close"]
    n = len(highs)

    pivots = find_pivots(highs, lows, PIVOT_K)
    pool_events, sweep_events = build_pools_and_sweeps(highs, lows, closes, pivots)

    n_pivots, n_pools, n_sweeps = len(pivots), len(pool_events), len(sweep_events)
    report = {
        "check": "ac6_sweep_recount",
        "rev": 2,
        "run_utc": int(time.time()),
        "n_bars": n,
        "n_pivots": n_pivots,
        "n_pools_formed": n_pools,
        "n_sweeps": n_sweeps,
        "expected": {"pivots": EXPECTED_PIVOTS, "pools": EXPECTED_POOLS, "sweeps": EXPECTED_SWEEPS},
        "matches": {
            "pivots": n_pivots == EXPECTED_PIVOTS,
            "pools": n_pools == EXPECTED_POOLS,
            "sweeps": n_sweeps == EXPECTED_SWEEPS,
        },
        "reported_historical_sweeps": REPORTED_HISTORICAL_SWEEPS,
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
