# DEVQ-010 · QUESTION · Sprint 4 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-004 §4 + Key contracts, Blueprint §4.3 (EventFrame, anti-hindsight),
ADR-009

## Question
ARCH-004 §4 anticipated "SMC library version choice and any disagreement between
its zone definitions and the architecture's." Two things to ratify:

1. **Version pin.** `smartmoneyconcepts==0.0.27` (latest on PyPI; installs and
   imports cleanly on this Python 3.13 / Windows toolchain — vectorbt 0.28.2 too).
   Recorded in each detector's `code_ref` and hence its `instrument_registered`
   payload (per the Blueprint new-dependency rule). uv.lock updated.

2. **Causality disagreement (the substantive one).** The library is a *vectorised
   whole-frame* calculator and is **non-causal as written**:
   - `fvg()` uses `shift(-1)` — an FVG "at" bar *i* needs bar *i+1*.
   - `swing_highs_lows()` looks `swing_length` bars into the FUTURE and
     force-flips the frame's first/last swing; `ob()` reports a block at a PAST
     bar that is only knowable once a later structure-break prints.
   Emitting events at the library's reported index would violate the Blueprint
   §4.3 anti-hindsight invariant (`ts >= last input bar needed`).

## What I built (reconciliation)
A **knowability wrapper** in `qrf/trading/concepts/smc/detector.py`, split into two
family-`smc` detectors so each has clean fixtures:
- **`smc.fvg`** — event `ts` = the confirmation bar `i+1` (exact, cheap).
- **`smc.order_block`** — `ts` = the last bar of the *smallest data prefix at
  which the library first, and stably, reports that exact block* (found by binary
  search), with a `swing_length` tail margin that drops unconfirmed /
  boundary-forced blocks. This makes incremental-consistency true by construction.
Zones map directly: `zone_hi/zone_lo` = the library's `Top/Bottom`
(`zone_hi >= zone_lo` always). Planted fixtures (bull/bear FVG + OB, truth 1.0),
structured-noise silence (1.0), insufficient silence; anti-hindsight property
test green for all four truth cases; both detectors registered + calibrated
through the real journal.

## Options considered
A) Wrap + relocate `ts` to the knowability bar (as built) — keeps the library's
   zone math, satisfies §4.3.
B) Re-implement FVG/OB causally from scratch, ignore the library — more code, no
   dependency, but re-derives what the library already computes and loses the
   "wrap a named library" intent of ARCH-004 §4.
C) Emit at the library's index and relax §4.3 — **rejected** (weakens a frozen
   invariant; would be an `architecture-conflict` BLOCKER, not this QUESTION).

Recommendation: **A** (built). Pin `smartmoneyconcepts==0.0.27`. Proceeding on A;
calibration + anti-hindsight are green.

## How this blocks (or not)
Non-blocking. Flagged as a QUESTION (not `architecture-conflict`) because the
wrapper *upholds* §4.3 rather than fighting it. If you would rather OB knowability
be defined by an explicit break-bar rule than by first-stable-appearance, that is
a localized change to `_knowability`.

---
## REPLY · architect (fable) · 2026-07-25
Decision: **A RATIFIED**; pin **smartmoneyconcepts==0.0.27**. Your
non-causality finding is the most valuable sentence of the sprint — a
named, popular library emits SMC events at times when they were NOT yet
knowable, and QRF's §4.3 invariant caught it at the wrapper boundary.
Record kept here for the mechanism registry later: this is exactly the
kind of structural hindsight that manufactures fake edges downstream.

Ratified specifics: fvg ts = confirmation bar i+1 (exact, correct);
order_block ts = first-stable-appearance with swing_length tail margin,
ACCEPTED FOR SPRINT 4 with a caveat — it is an operational definition
(what the library first reports) rather than a structural one (the
break bar that makes the block meaningful). Before any OB-based
hypothesis reaches the battery (Sprint 6 gate), knowability must be
restated as an explicit break-bar rule and shown equivalent (or the
delta characterized) on the planted fixtures. Queued in GO-S4 retro as
a carried item; NOT required for GO-S4 itself. The anti-hindsight
property test plus stable-appearance construction satisfies §4.3 today.
Status: CLOSED

---
## ADDENDUM · architect (fable) · 2026-07-25 · FVG definition completed
The IVF S4 independent recomputation went RED on real data: 107 vs 105
events. Diagnosis (bars inspected by the Owner, evidence in
ivf/reports/s4_verify.json rev-2 run): the two disputed patterns have
BEARISH middle candles inside "bullish" gaps. The library's rule — now
RATIFIED as the QRF FVG contract — is:

  bull FVG at pattern bar i:  low[i+1] > high[i-1]  AND  close[i] > open[i]
  bear FVG at pattern bar i:  high[i+1] < low[i-1] AND  close[i] < open[i]
  zone = [high[i-1], low[i+1]] (bull; mirrored bear) · ts = bar i+1.

The displacement-candle condition was UNDERSPECIFIED in our contracts
until now; two independent implementations disagreeing by 2/107 on first
real contact is exactly what the IVF exists to catch. Check rev 3
encodes the completed rule.

Recorded observation (not a defect): both implementations treat row
adjacency as bar adjacency across the 50-hour weekend hole — both
disputed patterns spanned Fri→Sun. Whether weekend-spanning FVGs are
the same tradable object is a RESEARCH question; queue a `question`
record when the observatory opens (Sprint 7).
Status: CLOSED (addendum recorded)
