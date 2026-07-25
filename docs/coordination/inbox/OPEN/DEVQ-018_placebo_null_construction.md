# DEVQ-018 · QUESTION · Sprint 8 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-008 §1 (placebo battery G-3), A1.7 (placebo before any trusted PASS),
Blueprint §4.7 (verdict pipeline)

## Question
ARCH-008 §1 requires the placebo battery to run the SAME pipeline on "a
null-preserving synthetic twin of the window (seeded circular block-shuffle of
returns, OR label-permutation of event directions — choose via DEVQ, document
the null it preserves)". Which null(s), and what does each preserve? The three
Wave-1 setups do not share one honest null:

- H-001 / H-002 (FVG follow-through) CLAIM: *the event's own direction predicts
  the subsequent net move.* The matching null is "event direction is
  uninformative."
- H-003 (Monday long-at-open) CLAIM: *entry on this specific calendar day is
  profitable.* Direction is FIXED long — there is no signal sign to permute, so
  direction-permutation is a no-op-shaped null for it. The matching null is
  "the chosen entry TIMING carries no edge beyond the base drift" (otherwise a
  generic 2024 gold uptrend would let ANY always-long strategy PASS, and a
  direction-null placebo would not catch it).

A circular block-shuffle of *returns* is rejected for a third reason: the engine
fills on OHLC bars (stops, pessimistic gap-through — A1.5/DEVQ-012), and a
returns-only shuffle cannot reconstruct a valid OHLC path, so it would conflate
the null with path-reconstruction artifacts and would NOT be "the SAME pipeline."

## Options considered
A) `direction_permutation` only — seeded permutation of the events' `direction`
   column; bars/OHLC untouched. Right null for FVG; wrong null for H-003.
B) `entry_time_shuffle` only — seeded reassignment of each entry to a uniformly
   random distinct window bar, direction/strength/hold preserved; bars untouched.
   Right null for a fixed-direction timing claim; for FVG it tests a weaker null
   (timing, not direction).
C) BOTH, assigned by claim type: `direction_permutation` for directional event
   claims (H-001/H-002), `entry_time_shuffle` for fixed-direction timing claims
   (H-003). `placebo_run.method` records which was used per run.

Recommendation: **C.** Each hypothesis declares its `placebo_method`; the placebo
engine dispatches on it. Both methods hold the bar/OHLC path and the cost model
fixed and perturb ONLY the setup's claimed signal, so the engine, splits, pooled
stats and tri-state-at-deflated-alpha run byte-for-byte as in the real verdict —
genuinely the SAME pipeline, differing only in the seeded null draw.

Nulls preserved, explicitly:
- `direction_permutation`: event count, timing, strength, bar path, cost, and the
  MARGINAL direction mix; DESTROYS the direction↔outcome alignment.
- `entry_time_shuffle`: entry count, direction, hold, bar path, cost; DESTROYS the
  entry-timing↔outcome alignment (so a base-drift-only "edge" shows up as excess
  null passes — the honest placebo for H-003).

A healthy judge yields ~alpha·n_runs passes AT MOST under either (ARCH-008 §1 AC).

## Proceeding
QUESTION-level; I am building §1 against recommendation C and will note it for
REV-S8 ratification. If the Architect prefers a single method, the `method` field
and per-hypothesis `placebo_method` make a swap a config change, not a rewrite.
