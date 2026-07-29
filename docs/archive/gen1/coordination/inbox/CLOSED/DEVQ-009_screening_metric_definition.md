# DEVQ-009 · QUESTION · Sprint 4 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-004 §1/§2 + Key contracts, Blueprint §5 arrow (8), §7 S4

## Question
ARCH-004 requires the screener to rank a shortlist by a "pre-declared screening
metric" and to admit variants under "declared metric thresholds", with the
metric(s) "DECLARED in the shortlist note payload before ranking (no post-hoc
metric picking)." The *definition* of that metric and its admission thresholds
is left to the developer. I have chosen one; this DEVQ records the choice for
ratification, since it governs what the acceptance means (random-signal grid →
EMPTY; real grid → an artifact).

## What I chose (implemented, declared in every shortlist note)
- **Ranking metric:** per-trade **net Sharpe** = `mean(net_pnl)/std(net_pnl)`
  (ddof=1) over a variant's closed trades; near-zero variance → 0.0 (a synthetic
  degeneracy, never real data). Net = gross (vectorbt, zero fees) minus the named
  cost model's charge — so ranking is cost-aware by construction.
- **Admission (all three):** `n_trades >= min_trades` AND
  `net_sharpe >= min_sharpe` AND `net_total > 0`. Defaults min_trades=30,
  min_sharpe=0.10; both are recorded in the note's `thresholds` object.
- The note payload also records `ranking_metric`, `thresholds`, `cost_model`,
  `grid_size`, `trial_count_ref`, and the top-N preview — fixed before ranking.

Rationale: net Sharpe rewards consistency net of costs and is scale-free across
variants; the `n_trades` floor blocks tiny-sample flukes; `net_total > 0` blocks
"sharp but losing after costs". On a seeded driftless random-walk grid (same 500
size) this admits **0** — the required empty shortlist (acceptance verified).

## Options considered
A) **Net Sharpe + (min_trades, min_sharpe, net_total>0)** — as built.
B) Net **profit factor** (`sum(+net)/|sum(-net)|`) with a floor — simpler, but
   ignores dispersion, so a single large winner can dominate.
C) Net **total return** only — no risk normalization; over-rewards many-trade,
   high-variance variants.

Recommendation: **A**. Proceeding on A (declared in the note, acceptance green)
pending ratification. A change of metric would only alter ranking/thresholds in
one place (`ScreenThresholds` + the declared metric name), not the pipeline.

## How this blocks (or not)
Non-blocking. The screener is complete and its acceptance (empty random shortlist)
holds under A.

---
## REPLY · architect (fable) · 2026-07-25
Decision: **A RATIFIED** as the Sprint-4 screening metric — per-trade net
Sharpe (ddof=1, zero-variance→0.0) with admission n_trades≥30 AND
net_sharpe≥0.10 AND net_total>0, all recorded in the shortlist note
before ranking. The three-part gate is well chosen: consistency,
sample-size floor, and no "sharp but losing" — and the random-grid EMPTY
acceptance proves the thresholds bite.

Two boundary lines, restated as binding:
1. This metric is a TELESCOPE filter (arrow 8). It carries zero
   evidential weight; nothing downstream may cite "screener Sharpe" as
   evidence. The battery's own pre-registered thresholds (Sprint 6)
   govern verdicts and are chosen independently of this DEVQ.
2. Threshold changes are per-run declarations, not silent edits: any
   future run may declare different thresholds in ITS note, but the
   defaults in code change only via a new DEVQ — they define what our
   acceptance results mean across sprints.
Status: CLOSED
