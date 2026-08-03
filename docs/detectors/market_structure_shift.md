# DETECTOR DEFINITION — Market Structure Shift (M5)

**Status:** PROPOSED, awaiting Architect approval (A-018 §3 step 2). No
code exists against this definition yet.

**Origin:** The Owner's material refers to structure turning,
higher-timeframe bias, and "who is currently in control" (A-018 §2.3).
The Owner's own one-line gloss (`SMC_Concept_Glossary.md`) states:
*"Confirmed flip: CHoCH + displacement."* A-018 is explicit that this is
"the hardest and least specified" of the three and instructs me NOT to
invent a rich structural model, but to propose the SIMPLEST definition
that can still serve M5 and §1.6's choppy/directionless boundary. This
document does exactly that, and says plainly what it excludes. It does
not consult or derive from any previous-era code (AM-02).

## 1. The rule

Uses the SAME swing primitive as `order_block.md` §1 (`SWING_K = 3`,
confirmed at `i + SWING_K`) — reused as a shared, well-specified
mechanical building block, not as a dependency on the Order Block
detector's OUTPUT. Each detector computes its own swings independently
from the same simple, restated rule.

**Prevailing structure**, evaluated at each bar as swings confirm:
- **BULLISH** iff the two most recently confirmed swing highs are
  strictly ascending (each newer high > the previous one) AND the two
  most recently confirmed swing lows are strictly ascending (higher
  lows).
- **BEARISH** iff both are strictly descending (lower highs, lower
  lows).
- **UNDEFINED** otherwise — including every case where highs and lows
  disagree (e.g. higher highs but lower lows), or fewer than two
  confirmed swings of either type exist yet.

UNDEFINED is not a third kind of trend; it is the absence of one, and it
is the mechanical proxy for §1.6's "choppy or directionless" boundary —
no shift can be observed from a structure that is not itself coherent.

**A Market Structure Shift fires at bar `b`** iff, immediately before
`b`, prevailing structure was BULLISH or BEARISH (not UNDEFINED), AND
`close[b]` breaks strictly beyond the swing point that defines that
structure in the OPPOSING direction:
- from BULLISH structure: `close[b] < ` the most recently confirmed swing
  LOW (the last higher-low is broken) → a BEARISH shift.
- from BEARISH structure: `close[b] > ` the most recently confirmed swing
  HIGH (the last lower-high is broken) → a BULLISH shift.

No event fires from UNDEFINED structure — there is nothing to shift
from.

After a shift fires, the prevailing structure for subsequent bars is
reset to UNDEFINED (not immediately assumed to be the opposite trend):
a single break is evidence structure CHANGED, not proof of a new,
established trend, which would need its own two ascending/descending
swings to confirm again under this same rule.

## 2. What this deliberately does NOT capture

Stated plainly, per A-018 §2.3's own instruction:

- **No higher-timeframe bias.** This is a single-timeframe, single-series
  rule. The Owner's material discusses aligning structure across
  timeframes; this detector does not attempt that at all.
- **No "who is currently in control" as a richer judgment** beyond the
  mechanical ascending/descending swing test above. That phrase describes
  a trader's holistic read of a chart; this detector implements only the
  narrowest mechanical proxy for it that could still produce a testable
  signal.
- **No CHoCH-vs-BOS distinction.** SMC terminology often separates a
  "change of character" (first break against an established trend) from
  a subsequent "break of structure" (continuation of the new trend). This
  detector emits a single event kind (`STRUCTURE_SHIFT`) for the first
  break only — the reset-to-UNDEFINED in §1 means it does not attempt to
  track or name what happens after.
- **No displacement/momentum confirmation.** The Owner's gloss pairs
  "CHoCH" with "+ displacement" (implying the breaking move should also
  be forceful, not just a marginal close-through). This definition tests
  ONLY the close-price break, deliberately, because "displacement" has no
  precise, sourced threshold available to me and adding one would be
  inventing a parameter while coding — exactly what A-018 warns against.
  A future, stricter detector that also requires displacement is a
  DIFFERENT detector, not a configuration of this one.

## 3. Frozen constants

- `SWING_K = 3` — same value as `order_block.md`, same reasoning,
  independently declared as this detector's own frozen constant (not an
  import of the other detector's constant, so the two can diverge in
  future without either silently affecting the other).

## 4. The mechanic a careless reader would get wrong

"Ascending" for structure must be checked using the two MOST RECENT
confirmed swings of each type, compared to EACH OTHER — not compared
against some older reference point, and not requiring highs and lows to
agree with a third, independent trend indicator. A careless
implementation might track "the last swing high" and "the last swing
low" as a running pair and call structure bullish whenever `price` is
above some moving reference; that is a different (and much richer, less
simple) model than this one. This definition is purely about the
RELATIVE ORDERING of the last two confirmed swings on each side — nothing
else feeds into it.

Also easy to miss: the reset-to-UNDEFINED after a shift (§1, last
paragraph) — an implementation that immediately treats a shift as
establishing the opposite trend (without waiting for two new confirming
swings) would over-report shifts, since a single break can occur inside
what is still choppy, undefined structure.
