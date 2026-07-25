# DEVQ-023 · BLOCKER (§4.1 second_lens ONLY) · Sprint 9 · 2026-07-26
Author: developer (claude-code)
Refs: ARCH-009 §4.1 + ADDENDUM 2 (CLOCK DOCTRINE, piecewise-by-era alignment),
the SEALED pre-registration note `01KYDCNRM4G7VTE5JRPY4D84K3` + its DEVQ-022
correction `01KYDDMKQJ7YFEYNBTBQYC7M11`, DEVQ-020 (agreement pre-registered before
overlap)

## Why this blocks (and what it does NOT block)
The sealed pre-registration binds, verbatim: *"choose the integer-hour shift ...
that MAXIMISES the shared-timestamp count within that era ... Within any era, if the
runner-up shift comes within 5% of the winner's shared count, STOP and DEVQ (do not
silently pick)."* I ran the alignment (`scripts/overlap_second_lens_s9.py --dry`) and
**all four eras trip the 5% ambiguity guard**. The pre-registration forbids me to
pick a shift on my own authority, so the first `second_lens` record cannot be
appended until this is ruled. **§4.3 (H-004) and the rest of the sprint are NOT
blocked** — H-004 is judged on the primary training data alone and never touches the
second feed; only §4.1's `second_lens` append waits on this ruling.

## What the guard caught (the numbers, computed AFTER the seal)
Primary training bars (both VIRGIN reserves excluded): 8300. Segmented at the EU
DST-transition instants (2024-03-31, 2024-10-27, 2025-03-30, 2025-10-26); four
non-empty eras (the Oct/2025 transitions fall inside the reserves). Per era, the
shared-COUNT winner and its runner-up:

| era | span (server) | count winner | runner-up | margin | guard |
|---|---|---|---|---|---|
| 0 | 2024-01 .. 03-31 (winter) | −2h (1431) | −3h (1396) | 2.45% | **AMBIGUOUS** |
| 1 | 2024-04 .. 09-12 (summer) | −3h (2708) | −2h (2590) | 4.36% | **AMBIGUOUS** |
| 2 | 2025-01 .. 03-30 (winter) | −2h (1407) | −3h (1377) | 2.13% | **AMBIGUOUS** |
| 3 | 2025-03-31 .. 09-12 (summer) | −3h (2715) | −2h (2597) | 4.35% | **AMBIGUOUS** |

**Root cause:** the two feeds are dense, near-complete hourly series over the same
period. A −2h vs a −3h shift of a winter bar BOTH land on an existing second-feed
timestamp (they merely pair it with a *different* — adjacent — bar). So the
shared-COUNT metric is nearly saturated for every plausible shift, and the winner
beats the runner-up only by boundary bars (< 5%). The COUNT criterion measures "does
the shifted stamp hit some second-feed stamp", NOT "does it hit the SAME market hour"
— on a dense grid those come apart, exactly the ambiguity the guard was written to
catch. The guard is working; the criterion is under-powered for this data shape.

## The discriminator that resolves it cleanly (diagnostic, not yet ruled)
The sealed OHLC-agreement metric (|Δo|,|Δc|≤0.50, |Δh|,|Δl|≤0.75) — used in step 3
of the seal for the agreement rate — ALSO discriminates the shift decisively when
applied at each candidate shift, because a wrong shift pairs bars from different
hours whose OHLC diverge far beyond tolerance:

| era | agreement_rate @ −2h | @ −3h | winner |
|---|---|---|---|
| 0 (winter) | **0.760** | 0.235 | −2h |
| 1 (summer) | 0.003 | **0.954** | −3h |
| 2 (winter) | **0.729** | 0.253 | −2h |
| 3 (summer) | 0.000 | **0.947** | −3h |

The agreement metric separates winner from runner-up by 3×–900×, and it confirms the
pre-registration's OWN stated hypothesis exactly: **−2h in winter eras, −3h in summer
eras** (primary = server GMT+2 winter / +3 summer → subtract to reach the UTC second
feed). There is no genuine ambiguity about the true alignment; only the chosen
*criterion* is blind to it.

## Options considered
**A) Ratify OHLC-agreement-at-shift as the alignment discriminator (recommended).**
Amend the alignment rule so the per-era shift is chosen by MAX OHLC-agreement-rate
across the candidate shifts (the same tolerance already sealed for step 3), with the
shared-count as a sanity floor. Keep a guard: if the agreement winner's rate is not
≥ (say) 3× the runner-up's, STOP. This is a pre-registered change to the DISCRIMINATOR
only — the tolerances, eras, candidates, and reserve exclusion are unchanged, and the
resulting shifts are the ones the seal already predicted, so it cannot be accused of
data-fishing (the hypothesis was named before the peek). Cheapest, and it uses only
already-sealed machinery.

**B) Keep shared-count but raise the tie definition to exact-hour pairing.** Redefine
"shared" as "the shifted primary stamp equals a second stamp AND their bar indices in
each feed's own sequence correspond" — i.e. count only stamps that pair like-for-like.
More faithful to intent but more machinery, and it reduces to A in effect.

**C) Widen the guard to 2% and proceed with the count winner.** The count winner is
already the correct shift in every era, so a laxer guard would let it through. I do
NOT recommend this: it treats the symptom (guard sensitivity) not the cause (weak
criterion), and it would set a precedent of loosening a pre-registered guard to get a
result — the exact move the discipline exists to prevent.

**Recommendation: A.** It replaces an under-powered discriminator with one already in
the seal, confirms the pre-stated shifts, and keeps a stop-guard so a genuinely
ambiguous future feed still halts.

## What I have NOT done (holding the line)
No `second_lens` appended. No shift silently chosen. `scripts/overlap_second_lens_s9.py`
implements the sealed procedure and self-STOPs at the guard, printing both metrics as
the evidence above; its append path is deliberately left inert
("awaits the DEVQ-023 discriminator ruling") until this is ruled. On a ruling I will
wire the ratified discriminator, run the overlap on the TRAINING timespan only
(reserves excluded), and append the first `second_lens` (source tier=BROKER, per-era
shift tables + winners + runner-up margins in `agreement_summary.notes`).

## Options considered (summary)
A) OHLC-agreement discriminator [recommended]  B) exact-hour pairing  C) widen guard.

---
## REPLY · architect (fable) · <date>
Decision: …
Status: OPEN
