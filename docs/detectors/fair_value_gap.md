# DETECTOR DEFINITION — Fair Value Gap (M7)

**Status:** PROPOSED, awaiting Architect approval (A-018 §3 step 2). No code
exists against this definition yet.

**Origin:** The Owner's own one-line gloss (`F:\QRF\docs\reference\
SMC_Concept_Glossary.md`, "Contributed by: Owner (Girish)"): *"3-candle
pattern; wick of candle 1 and candle 3 do not overlap."* Also stated
directly in A-018 §2.1: "the isolated space between the first candle's
high and the third candle's low (and its mirror)." This document expands
that one line into a precise, reproducible mechanical rule — it does not
consult, and is not derived from, any previous-era code (AM-02).

## 1. The rule

Consider three CONSECUTIVE bars at indices `i`, `i+1`, `i+2`.

- A **BULLISH FVG** exists at `(i, i+1, i+2)` iff `high[i] < low[i+2]`
  (bar `i`'s high sits strictly below bar `i+2`'s low). The gap is the
  price interval `(high[i], low[i+2])`.
- A **BEARISH FVG** (the mirror) exists iff `low[i] > high[i+2]`. The gap
  is the price interval `(high[i+2], low[i])`.

The middle bar (`i+1`) has **no shape requirement** — its own high/low do
not enter the condition at all. This is the "least ambiguous" of the
three detectors precisely because the rule is a pure comparison between
bars 1 and 3; nothing about bar 2's body, direction, or size is part of
the mechanical definition.

**Strict inequality, not `<=`.** If `high[i] == low[i+2]` (or the
mirror), the bars touch with zero width — that is not "isolated space",
so no gap is recorded. A careless reader who uses `<=` would count
touching-but-not-gapped triples as gaps; this is the ambiguity Appendix
B's own §B.5 taught to state explicitly for exactly this project.

## 2. Confirmation lag

An FVG at `(i, i+1, i+2)` is not knowable until bar `i+2`'s own high/low
are final — i.e. it becomes visible at bar `i+2`, the same bar whose
value the rule tests. There is no additional lag beyond that (unlike the
sweep detector's pivot, which needs `k` bars on EACH side): a 3-candle
pattern is complete the instant its third candle closes.

## 3. What this detector does NOT do (deliberately)

- **No fill/mitigation tracking.** This detector reports FORMATION only
  (one event per gap, at the bar it becomes visible). Whether price later
  re-enters, partially fills, or fully fills the gap is a different
  question this detector does not answer — LS-01's M7 only asks whether
  an FVG is *created*, not what happens to it afterward. A fill-tracking
  detector, if ever needed, is a DIFFERENT detector.
- **No minimum gap size.** The Owner's material states no size threshold,
  and this document invents none — adding one would be a parameter
  choice, and per AM-04 a parameter choice is a measurement decision, not
  part of the concept's detector. Every gap meeting the strict inequality
  is reported, however small.
- **No merging of overlapping/adjacent gaps.** Each `(i, i+1, i+2)` triple
  is evaluated independently; two triples that share bars can both
  produce gaps (e.g. a bullish gap at `(i, i+1, i+2)` and another at
  `(i+1, i+2, i+3)`). This detector does not attempt to decide whether
  they are "the same" gap — that judgment, if ever wanted, belongs to a
  consumer of the observations, not the detector (C3: it reports what it
  saw, not an interpretation).

## 4. The mechanic a careless reader would get wrong

Testing `high[i] < low[i+2]` for bullish and `low[i] > high[i+2]` for
bearish are NOT symmetric copies of the same comparison with signs
flipped naively — a common transcription error is to write the bearish
case as `high[i] > low[i+2]` (comparing the wrong pair of prices). The
correct mirror compares **low-to-high**, not high-to-low, in both
directions: bullish compares bar 1's high against bar 3's low (the gap is
"above" bar 1 and "below" bar 3); bearish compares bar 1's low against
bar 3's high (the gap is "below" bar 1 and "above" bar 3). Both drills
(planted truth for each direction) exist specifically to catch this
transcription error.
