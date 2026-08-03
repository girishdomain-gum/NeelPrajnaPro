# DETECTOR DEFINITION — Order Block (M6)

**Status:** PROPOSED, awaiting Architect approval (A-018 §3 step 2). No
code exists against this definition yet.

**Origin:** The Owner's material names two methods (A-018 §2.2). The
Owner's own one-line gloss (`SMC_Concept_Glossary.md`) states:
*"Last opposing candle before impulsive structure-breaking move"* — this
is the **origin-candle** method. A second method, "the range" (a
consolidation cluster around the origin candle), is named but not chosen
here. This document is written from that one-line gloss and from general,
non-proprietary SMC terminology; it does not consult or derive from any
previous-era code (AM-02).

## 0. Method choice: ORIGIN CANDLE, not "the range" — proposed, with reasoning

I propose implementing the **origin-candle** method as `order_block` v1,
and naming "the range" explicitly as a DIFFERENT detector, never a
configuration of this one, per A-018 §2.2's own instruction. Reasoning:

1. It is the method the Owner's own glossary line states directly and
   completely — "the range" is named only as an alternative, without a
   comparably precise one-line description to build from.
2. It resolves to a SINGLE, uniquely identifiable candle. "The range"
   requires additional undecided rules (how many candles form the
   cluster, what counts as "consolidation") that nothing available to me
   specifies — building it now would mean inventing those rules while
   coding, exactly the risk A-018 §3 exists to prevent.
3. It is mechanically simpler to drill precisely (one candle, one zone)
   than a cluster boundary would be.

If approved, "the range" method remains available as `order_block_range`
or similarly named, a full sibling detector, built only if a future
sprint needs it and can source its own precise definition.

## 1. The rule (origin-candle method)

Given a bar series, first identify **swings** (this detector's own,
self-contained primitive — it does not depend on any other detector's
output):

- Bar `i` is a **swing high** iff `high[i]` is the strict maximum of
  `[i-SWING_K, i+SWING_K]`; a **swing low** iff `low[i]` is the strict
  minimum of the same window. `SWING_K = 3` (frozen; see §3). A swing is
  visible only at its confirmation bar `i+SWING_K`, exactly as the sweep
  detector's pivots work (A-012 §2.4(a)) — same reasoning, independently
  re-derived: a swing extremum cannot be known until bars exist on both
  sides of it.

A **structure break**, at bar `b`, is:
- **BULLISH** iff `close[b]` is strictly greater than the most recently
  CONFIRMED swing high at the time bar `b` closes.
- **BEARISH** iff `close[b]` is strictly less than the most recently
  confirmed swing low.

(If no swing high/low has yet been confirmed, no break can be evaluated
— see §2, "cold start".)

Given a structure break at bar `b` (direction `D`), the **origin candle**
is the NEAREST bar `j < b` whose candle color is opposite `D`:
- for a BULLISH break, the nearest prior BEARISH candle (`close[j] <
  open[j]`);
- for a BEARISH break, the nearest prior BULLISH candle (`close[j] >
  open[j]`).

A candle with `close[j] == open[j]` (a doji) is neither color and is
SKIPPED over while searching backward — it is not a match, but it does
not stop the search either.

The **order block zone** is `[low[j], high[j]]` — the origin candle's
own full price range, frozen at the moment the structure break confirms
it (bar `b`). The order block becomes visible at bar `b`.

If no opposite-colored candle is found within `MAX_LOOKBACK` bars
strictly before `b` (frozen constant, see §3), no order block is emitted
for that break — this is a real, expected outcome (a long uniform run
before a break), not an error.

## 2. Cold start and one-break-one-block

- **Cold start.** Before `SWING_K` swings of each type exist, no
  structure break can be evaluated (there is nothing confirmed yet to
  break). This is a plain, silent "not yet" — no event, no error.
- **Each structure break produces AT MOST one order block** (the single
  nearest origin candle, or none if `MAX_LOOKBACK` is exceeded) — never a
  set of candidate blocks to choose from later.

## 3. Frozen constants (module-level, per A-012's own precedent)

- `SWING_K = 3` — chosen for consistency with this project's other
  swing-based reasoning (the sweep detector's `PIVOT_K`), and because it
  is the smallest window that still requires confirmation on both sides.
  This is an independently-chosen constant for THIS detector, not a
  borrowed dependency on the sweep detector's value.
- `MAX_LOOKBACK = 50` bars — proposed as generous enough that a real
  origin candle is essentially always found in a genuine impulsive move
  (which by definition is a short run of same-direction candles), while
  still bounding the search so a pathological same-direction run cannot
  make the detector scan indefinitely. I am not confident this is the
  only defensible value — if you disagree, please say so; I have no
  strong basis to prefer 50 over, say, 30 or 100, and would rather you
  rule on it than have it hide as an arbitrary choice.

## 4. What this detector does NOT do (deliberately)

- No "impulse strength" or displacement-magnitude requirement on the
  break — any strictly-beyond close counts, mirroring the sweep
  detector's own strict-comparison style.
- No re-confirmation, extension, or invalidation of an order block once
  formed (no "block already tested" or "block broken" tracking). This
  detector reports formation only, like the FVG detector.
- No "the range" (cluster) method — see §0.
- No higher-timeframe context of any kind.

## 5. The mechanic a careless reader would get wrong

Searching backward for the origin candle must stop at the FIRST (nearest)
opposite-colored candle, not the LAST (furthest) one within the impulsive
run. A careless implementation might instead walk backward through the
ENTIRE same-colored run and return the opposite candle furthest back
(effectively the start of a longer consolidation) — that is a different,
undocumented rule, not this one. The planted-truth drill specifically
constructs a run long enough that "nearest" and "furthest" opposite
candles differ, to catch this.
