# MEASUREMENT SPECIFICATION — LS-01-R001 · FILTERED LIQUIDITY SWEEP
**Concept:** LS-01 (`docs/concepts/LS-01_liquidity_sweep.md`)
**Status:** SPECIFIED, **NOT REGISTERED**. Nothing is spent until the Owner's
ceremony. Written before any data is judged, per AM-04.
**Owner's decisions:** O-023. **Drafted by the Architect.**

---

## 1. What is being measured

Among liquidity sweeps that occur while market structure is already defined,
does subsequent price behaviour differ from what the block-resampling null
produces on data with the same dependence structure?

**Which family this instantiates:** M1 (directional movement after the sweep),
**restricted by a declared context condition**. It is not a new family; it is
family M1 with its population narrowed by an instrument-level filter.

**RULING (Architect), recorded because AM-04 requires it:** a CONTEXT FILTER
IS PART OF THE INSTRUMENT, exactly as a parameter is. Restricting M1's
population by an M5 condition is therefore a distinct registrable measurement,
and testing M1 unfiltered later is a SEPARATE registration that spends again.
Neither can be presented as a variant of the other after the fact.
LS-01 §1.3 is amended by this ruling: filters, like parameters, are declared
before running and one registration freezes exactly one filter.

## 2. The frozen event definition

An observation is counted when BOTH hold:

1. **Sweep** — the `liquidity_sweep` detector (v `H-07-v1.1-appendixB`) emits
   a SWEEP observation at bar *b*.
2. **Context** — the `market_structure_shift` detector (M5) emitted a
   STRUCTURE_SHIFT observation at some bar in **[b−10, b−1]**.

**Causality:** the context must be strictly BEFORE the sweep bar. No future
information may define an event. Both detectors are causal by construction
(swings confirm only at *i+k*), and this must be drilled, not assumed.

## 3. Instrument parameters (declared, not inherited)

| Parameter | Value | Status |
|---|---|---|
| Context window | 10 bars preceding the sweep | Owner's deliberate choice (O-023) |
| Observation horizon | 10 bars after the sweep bar | Owner's deliberate choice (O-023) |
| Context detector | M5 market structure shift | Owner's choice — simplest, fewest assumptions |
| Direction convention | high-side sweep → expect down; low-side → expect up | from the detector (S04), not invented here |

**These are INSTRUMENT parameters.** LS-01 contains no constants and none of
these belong to the concept. An earlier draft attributed a "12-bar horizon" to
"LS-01 §3" — LS-01 has no §3 and no horizon; that attribution was withdrawn
by the Owner and is recorded here so the error cannot re-enter.

Changing any value above is a DIFFERENT measurement requiring its own
registration (AM-04).

## 4. The statistic

Computed over the qualifying events in the judged window: the mean forward
return from the sweep bar's close to the close 10 bars later, **signed by the
sweep's direction** so that a reversal-consistent move is positive.

Exact form to be fixed in the registration record and hashed. Requirements:
it must be computable from provenance-bound ObservationSets plus the bound
bar data, and it must be a pure function of them.

## 5. The null

**THE CIRCULAR-SHIFT NULL** (amended 2026-08-04 after F-09; see below for
what was rejected and why).

Detection runs EXACTLY ONCE, on the real data, and is never re-run for the
null. The null does not manufacture events, real or synthetic. It asks a
different question of the SAME real events: *would this event's outcome look
unusual if it had been paired with a different moment's return instead of its
own?*

Mechanism: for each resample, draw ONE integer offset `s` and apply it to
EVERY qualifying event simultaneously; each event's forward return is
recomputed from the close series at `(sweep_bar + s)` and
`(sweep_bar + s + horizon)`, wrapping circularly. The resample's statistic is
the mean of those signed returns. The p-value is the add-one estimator
(S05's `add_one_pvalue`, unchanged), which remains structurally incapable of
returning 0.0.

| Property | Value / rule |
|---|---|
| Offset magnitude | at least **MEMBER_WINDOW = 200** bars, and at most `n_bars - 200`, so the offset AND its wrapped complement both clear the detector's own dependence length. Derived with zero discretion from an already-frozen constant — the same derivation S05 used for block length, reused rather than reinvented |
| Offsets per resample | ONE, applied rigidly to all events. Independent per-event shifts would destroy the events' mutual clustering as well as their outcome link, testing two things at once and making any rejection ambiguous |
| Qualifying set | defined ONCE (`qualifying_events_with_valid_horizon`), excluding any event whose `sweep_bar + horizon` runs past the end of the data, and used identically for the observed statistic and every resample. The excluded count is recorded in the verdict |
| Seed | recorded in the verdict; same seed and inputs reproduce the null exactly |

**PRESERVES:** the real events (positions, directions, count); the real close
series' own structure; the events' clustering relative to each other.
**DESTROYS:** only the correspondence between a given event and the specific
return that actually followed it — exactly and solely the event-outcome link
the hypothesis is about.

### 5.1 What was rejected, and why (F-09 — this record is part of the spec)

The original specification named a **block-resampling null over the raw bar
series, with detection re-run inside each resample**. It was rejected before
any registration, because the S08 dress rehearsal proved it CANNOT DETECT ITS
OWN EFFECT.

At the real block length (200) and real alpha, on a realistic jittered
population of ~170 events, a planted effect returned p ≈ 0.561 — and scaling
that effect TEN-FOLD made p **worse** (0.762). A test that is merely
underpowered improves as the effect grows; this got worse, which is the
signature of blindness rather than weakness.

The reason: each resampled block carried its events AND the returns that
followed them, welded together, so every resample still contained the full
association. The effect was being compared against itself.

**THE RULE THIS FORGES: a null must DESTROY the thing being tested.**
Block-resampling a price series is the correct null for a question about the
SERIES; it is the wrong null for a question about an EVENT-OUTCOME LINK.
S05's null model is not at fault — the defect was the PAIRING of that null
with this statistic, which is a measurement-level choice and lives here.

### 5.2 Acceptance evidence (required before registration, and met)

On the same fixture that exposed F-09, at the real offset rule and real
alpha = 0.025:

| Check | Result |
|---|---|
| CONVICT — planted effect | p = 0.001996, significant |
| ACQUIT — effect removed | p = 0.830, not significant |
| MONOTONICITY — p must improve as effect size grows | 0.05x → p = 0.094 (not significant); 0.2x → p = 0.0020; 1x → p = 0.0020 (add-one floor at N = 500) |

The monotonicity check is the acceptance criterion, not a diagnostic: it is
the specific test whose failure exposed F-09, and it must positively confirm
any null this measurement is ever judged under.

### 5.3 N for the real judgment

N must be large enough to represent alpha = 0.025 (S05's
`check_alpha_achievable` refuses otherwise), and large enough that a real
result is not pinned to the add-one floor as it was at N = 500 above.
**N = 5,000 for the real run**, giving a floor of 1/5,001 ≈ 0.0002 — two
orders below alpha, so the verdict reports a resolved p-value rather than a
saturated one. The offset space (n_bars − 400 distinct values) is far larger
than N, so resamples are not exhausted.

**Matched controls (volatility regime, time-of-day, prior trend) are NOT used
and are NOT registered.** That engine does not exist and has never been
validated. It may become a separate measurement after it is built and
drilled — never assumed into being by a registration.

## 6. Alpha

Per AM-03: LS-01's first registration receives **α = 0.025** under
`geometric_alpha_spending_v1` (TOTAL_ALPHA 0.05, RATIO 0.5). Not "the full
family budget" — an earlier draft said so and was wrong.
The registration record carries the rule name, both constants, the allocated
alpha, family capacity (100) and the count spent at that moment.

**N must be large enough to represent α = 0.025** or the battery refuses
rather than returning a foregone negative (S05, drill N4).

## 7. MANDATORY PREREQUISITE — the data does not yet exist

The S03 export (5,000 M5 bars) has been **examined**: all four detectors were
run over it and counts reported in S04 and S06. Under S02's window ledger it
can never be VIRGIN again, and **it cannot be judged on**.

**S07 therefore begins with a fresh export of market time nobody has looked
at.** Binding conditions:

1. Export fresh XAUUSD data through the S03 pipeline (provenance-bound,
   clock-checked, hash-verified).
2. **Run NO detector over it. Compute NO counts. Look at NOTHING.** Ingest,
   verify, reserve as VIRGIN — and stop.
3. Reserve the window BEFORE any analysis exists.
4. Only then register, and only then judge.

The ledger cannot detect an unrecorded look (S02's known seam). This step
rests on honesty, which is precisely why the ceremony exists.

## 8. What the verdict may say

About THIS MEASUREMENT only — this statistic, this p-value, this alpha, this
null, this window. **Never that the concept is true** (AM-04). It must also
state that the population was restricted by the M5 context filter, and that
the unfiltered sweep remains untested.

## 9. Outstanding — the ceremony is blocked on these

- **Designation phrase** — the Owner's own words. Not the Architect's, not
  suggested by any AI. Supplied at ceremony time; only its hash is stored.
- **Burn word** — the Owner's own, and different from the phrase.
- The exact statistical form (§4), to be drafted by the Architect and shown to
  the Owner in plain language before anything is frozen.
