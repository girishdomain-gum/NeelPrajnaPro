# DEVQ-003 · QUESTION · Sprint 2 · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-002 §Trading plug-in (classical RSI), Blueprint §4.3, "How to ask"
(RSI warm-up period exclusion rules)

## Question
Detector #2 wraps pandas-ta RSI and emits threshold **crossing** events. RSI
is undefined / unsettled during warm-up. What is the warm-up exclusion rule
for emitting crossings?

Empirical note: the working pandas-ta (0.4.71b0; see NOTE-006) computes RSI
via Wilder RMA and emits a *non-NaN* value from bar index 1 onward — i.e. it
does NOT leave the first `period` bars NaN the way a textbook first-valid-at-
`period` implementation would. So "both endpoints non-NaN" alone would let
crossings fire on unsettled early values.

## Options considered
A) **Exclude the first `period` bars from crossing emission** (treat RSI as
   untrustworthy until `period` full observations exist), AND require both
   RSI[t-1] and RSI[t] present. Inputs shorter than `period+1` bars are an
   `insufficient` calibration case: emit nothing, do not crash.
B) "Both endpoints non-NaN" only (trust pandas-ta's early values). Simpler
   but fires on unsettled RSI; fragile fixtures.
C) Extra settling window beyond `period` (e.g. 2·period) before trusting
   crossings. Safest against early noise; more arbitrary.

Recommendation: **A**. I am proceeding on A: warm-up = first `period` bars
excluded, `period+1` minimum, sub-minimum inputs → insufficient/silent. The
exact rule is documented in the detector docstring and encoded in the
planted fixtures. C can be layered later if calibration shows spurious early
crossings.

Level: QUESTION (not a blocker) — work continues on default A; a reversal
only changes the RSI detector + its fixtures, nothing kernel-side.

---
## REPLY · architect (fable, via Owner relay) · 2026-07-24
Decision: **A RATIFIED.** Period-bar exclusion — no events until the indicator
is fully warmed. Architecture impact: none.
Status: CLOSED
