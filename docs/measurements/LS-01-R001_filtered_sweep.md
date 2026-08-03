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

**The block-resampling null built and drilled in S05.** Block length derived
from the detector's own constant by the stated zero-discretion rule. The
add-one p-value estimator, structurally incapable of returning 0.0. Seeded and
reproducible; the seed is recorded in the verdict.

**Matched controls (volatility regime, time-of-day, prior trend) are NOT used
and are NOT registered.** That engine does not exist and has never been
validated. The Owner withdrew it for exactly that reason. It may become a
separate measurement after it is built and drilled — never assumed into being
by a registration.

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
