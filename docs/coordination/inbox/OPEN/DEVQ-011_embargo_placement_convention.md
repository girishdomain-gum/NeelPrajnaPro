# DEVQ-011 · QUESTION · Sprint 5 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-005 §3 + DoD ("embargo placement convention (after-test vs symmetric)"),
Blueprint §4.7 step 5, qrf/kernel/protocol/splits.py

## Question
ARCH-005 §3 specifies anchored walk-forward with "embargo bars excluded AFTER
each test range boundary" but leaves the exact geometry to me; the DoD names this
a likely DEVQ. This records the convention I implemented, for ratification, since
it defines what the split-based acceptance means.

## What I chose (implemented, tested — splits.py)
Window = index range `[0, n_bars)`, partitioned into `n_folds + 1` contiguous
near-equal blocks `B0…B_{n_folds}` (remainder to the earliest blocks). `B0` is the
anchored training seed; `B1…B_{n_folds}` are the test blocks. For fold `i`:
- `test_i  = B_i = [t0_i, t1_i)`
- `train_i = [0, max(0, t0_i − embargo_bars))` — anchored at the window start,
  expanding each fold, with `embargo_bars` withheld immediately before the test
  block (a contiguous leakage gap at the train→test boundary).

Guaranteed + property-tested: test blocks disjoint and ordered; `train.end ≤
test.start` (no train/test overlap); every range strictly inside `[0, n_bars)`;
train anchored at 0; pure/deterministic in `(n_bars, spec)`. A large embargo
collapses a fold's train to an explicit empty `[0,0)` range, never a silent error.

## Options considered
A) **Contiguous boundary-gap embargo** (as built): the `embargo_bars` adjacent to
   each test block's start are removed from that fold's training set. Train stays a
   single contiguous anchored range — simple, hand-verifiable, one range per fold.
B) **López-de-Prado "purge-after-test"**: embargo the `embargo_bars` immediately
   FOLLOWING each test block from all LATER (expanding) training sets. Under an
   anchored/expanding scheme this punches holes into later trains, so `train`
   becomes a UNION of intervals (list of ranges), not one contiguous range.
C) **Symmetric embargo**: a gap on both sides of each test block.

Recommendation: **A**. For anchored+expanding folds the only train adjacent to a
test block is that fold's own train, so a single boundary gap already absorbs the
cross-boundary serial-correlation leakage the embargo targets, while keeping each
`train` one contiguous range (much simpler to reason about, serialize, and audit).
If you prefer the strict LdP semantics (B), it is additive: `walk_forward` would
return `train` as a list of `IndexRange` and I'd add the hole-punching + tests. No
pipeline rework either way — only the split geometry changes.

## How this blocks (or not)
Non-blocking. splits.py is complete and green under A; the battery (S6) is the
first production consumer, so a switch to B before then costs no rework.

## How to ask
Ratify A, or rule B/C. If B, I'll change `train` to a list of ranges in one place.
