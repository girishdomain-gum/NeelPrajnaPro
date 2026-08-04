# RETROSPECTIVE — S08 PHASE 1: THE DRESS REHEARSAL
**Closed:** 2026-08-04 · **Owner sign-off:** given in chat
**Messages of record:** A-032 (briefing) · D-023 (rehearsal) · A-033 (power
check required) · D-024 (**F-09**) · A-034 (ruling: the null is wrong) ·
D-025 (proposal) · A-035 (approved + 2 refinements) · D-026 (fix + acceptance)
· A-036 (approved, §5 amended)
**Commits on dev:** 0bf844b (rehearsal) → cb47b60 (power check) → 82dacb3
(circular-shift null)

## Why this phase existed
The real judgment gets exactly ONE attempt: the moment it runs, a registration
slot and a window of market time are spent — including if it fails halfway on
a mechanical defect. Every component was tested in isolation; the SEQUENCE had
never been run. S07's F-08 was the precedent: a green suite, a clean compile
and a static scan all agreed the EA was correct, and all three were wrong.

## What it found — F-09, and it is the most valuable finding of the project
**The specified null could not detect its own effect.**

At the real settings, a planted effect returned p ≈ 0.561. Scaling that effect
**ten-fold made p worse (0.762)**. A merely underpowered test improves as the
effect grows; this got worse. That is the signature of blindness, not weakness.

**The cause:** the null block-resampled the raw bar series and re-ran
detection inside each resample — so every block carried its events AND the
returns that followed them, welded together. Each resample still contained the
full association. We were comparing the effect against itself.

**THE RULE: a null must DESTROY the thing being tested. This one preserved
it.** Block-resampling a price series is the right null for a question about
the SERIES; it is the wrong null for a question about an EVENT-OUTCOME LINK.
S05's null model is not at fault — the defect was the PAIRING of that null
with this statistic, a measurement-level choice.

**The fix (circular shift):** detection runs exactly once, on the real data,
and is never re-run for the null. One offset per resample, applied rigidly to
all events, slides the events against the price series. It preserves the real
events, the real series structure, and the events' mutual clustering; it
destroys only the correspondence between an event and the specific return that
followed it.

Two Architect refinements: the offset must clear MEMBER_WINDOW (200) on both
sides of the wrap — derived from an already-frozen constant, no new
discretion; and the qualifying event set is defined ONCE and shared by the
observed statistic and every resample, removing an asymmetry rather than
documenting it.

**Acceptance, first attempt, untuned:** convict p = 0.002 · acquit p = 0.830 ·
and the monotonicity check that exposed F-09 now positively confirms the fix
(0.05× → 0.094, 0.2× → 0.002, saturating at the estimator's floor above that).

## What went well
1. **The Developer refused to tune past the failure.** It reported p ≈ 0.56,
   ruled out the two explanations it could think of (effect size, spacing
   regularity), and stopped — rather than quietly reaching for a parameter.
2. **The 10× diagnostic.** Scaling the effect and watching the DIRECTION of p
   is what converted "weak result" into "broken instrument". A test whose
   result must move the right way is worth more than one that merely passes.
3. **It re-ran that same diagnostic on the fix**, unprompted — proving the new
   null passes the test the old one failed, not merely that two numbers landed
   on convenient sides of a threshold.
4. **Causality by signature:** `qualifying_events()` takes no `bars` parameter,
   so no future close can influence qualification because none can be read.
5. **Duck-typing to honour the inner wall** rather than asking for it to be
   relaxed.
6. **The empty-population choice** — returning 0.0, the value that asserts
   nothing, because a positive default would bias every starved resample
   toward significance.
7. **It ruled between the two null options** rather than handing back a coin
   flip, showing that the second collapses into the first once made precise.

## What went wrong
- The original rehearsal reached significance only by shrinking the block
  length to 10 — moving past the obstacle rather than through it. Caught by
  A-033 requiring a power check at the REAL value. Without that, F-09 would
  have surfaced in the real judgment.

## Rules this phase forged
1. **A null must destroy what is being tested.**
2. **A test whose result must move in a known direction is worth more than one
   that merely passes** — monotonicity is now an acceptance criterion for any
   null this measurement is judged under, not a diagnostic.
3. **An instrument may be corrected BEFORE registration and never after.** The
   entire value of the rehearsal was landing on the right side of that line.
4. **Remove an asymmetry rather than document it**, where removal is possible.
5. **Report a resolved number, not a saturated one:** N = 5,000 for the real
   run, so the verdict's p-value is a fact about the market rather than about
   the resample count.

## Carried forward
- **Friction #1:** no canonical CSV-to-Bar loader exists; every real run so far
  loaded bars by hand outside the tracked pipeline. Ruled: build it when the
  real judgment needs it, against the real export format — not now, against a
  format we would be guessing at.
- **The collection thread is the only remaining work.** 60 / 20,000 VIRGIN M5
  bars, weekly, looked at by nobody. The tenth batch is as untouchable as the
  first.
- **The two ceremony words remain the Owner's**, unchosen, with months and no
  deadline. Noted here because the Owner offered to defer to the Architect's
  verdicts: acceptable for a sprint review, never for the registration phrase
  or the burn word. Those two acts are the human key on the one lock the
  machine cannot turn alone; delegating them would remove the only thing
  preventing the system from grading its own work.
- **The open alpha-schedule question** (family capacity 100 nominal, ~6–8
  practical) is still deferred and still safe to defer — AM-03's migration
  requirement means any future scheme applies forward only.
