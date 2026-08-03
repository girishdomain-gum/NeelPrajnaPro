# CONCEPT SPECIFICATION — LS-01 · LIQUIDITY SWEEP
**Family:** liquidity_sweep · **Status:** v1, written BEFORE any measurement
is registered, per AM-04 and `docs/HYPOTHESIS_SPECIFICATION.md`.
**Authored:** Owner (O-018), drafted with the Architect. 2026-08-03.
**Detector of record:** `liquidity_sweep` v `H-07-v1.1-appendixB`
(NP-ADR-008 §5 v1.1 as pinned by Appendix B). §5 v1.0 is a different,
non-equivalent definition and is not this concept's detector.

---

## §1.1 SCIENTIFIC CLAIM (the Owner's words, unaltered)

A Liquidity Sweep is a market phenomenon in which price temporarily moves
beyond a previously established liquidity area, consumes available resting
liquidity, and changes the local market state.

The sweep itself is **not** claimed to be a trading signal, a guaranteed
reversal, or evidence of institutional intent. It is an observable market
event that may produce one or more measurable consequences.

*No constants appear in this section, by design. Every number in this
document belongs to an instrument, never to the concept.*

## §1.2 OBSERVABLE CONSEQUENCES

If the claim holds, then relative to comparable moments where no sweep
occurred, the bars following a sweep should differ in at least one of:

- **C1 — Direction.** Subsequent movement is not directionally symmetric
  about the swept level.
- **C2 — Asymmetry of excursion.** Favourable and adverse excursion after the
  event are not exchangeable.
- **C3 — Displacement.** The magnitude or character of movement changes
  (state change, per §1.1).
- **C4 — Structural consequence.** Identifiable structure forms afterwards
  more often than in comparable non-sweep moments — market structure change,
  order blocks, fair value gaps.
- **C5 — Interaction with origin.** Price's later relationship to the swept
  level or the origin zone is not what an unremarkable level would produce.

**If the claim is FALSE:** post-sweep bars are statistically exchangeable with
comparable non-sweep moments on every consequence above — direction balanced,
excursions exchangeable, no elevated structure formation, origin
interaction unremarkable. A consequence that would obtain either way is not a
consequence and does not belong in this list.

## §1.3 ALTERNATIVE MEASUREMENT METHODS

Ten measurement families, declared NOW (AM-04's anti-fishing rule). These are
alternative INSTRUMENTS for observing one concept — not different concepts.

| # | Family | What it computes | Observes | Registrable today? |
|---|---|---|---|---|
| M1 | Directional movement after the sweep | Sign of price change from the sweep bar to a fixed later point, versus the sweep's direction | C1 | **YES** |
| M2 | Reversal magnitude vs adverse movement | Favourable excursion against adverse excursion after the event, in the sweep's direction | C2 | **YES** |
| M3 | Displacement following the sweep | Magnitude/velocity of movement after the event vs comparable moments | C3 | **YES** |
| M4 | Return to origin / mitigation zone | Whether, and how, price revisits the swept level or the origin zone | C5 | **YES** |
| M5 | Market structure change following the sweep | Whether a structure shift occurs after the event | C4 | NO — needs an MSS detector |
| M6 | Order Block formation following the sweep | Whether an order block forms, and where | C4 | NO — needs an OB detector |
| M7 | Fair Value Gap creation following the sweep | Whether an FVG is created after the event | C4 | NO — needs an FVG detector |
| M8 | Continuation vs reversal behaviour | Classifies the outcome as continuation or reversal and compares rates | C1, C3 | **YES** |
| M9 | Time-to-event | Elapsed time until a defined subsequent event | C1–C5 | Partly — depends on the event chosen |
| M10 | Volatility-normalized variants | Any of the above expressed in units of local volatility rather than price | C1–C3 | **YES** |

**PARAMETERS ARE PART OF THE INSTRUMENT, AND CHOOSING THEM IS ALSO A CHOICE.**
A family becomes a registrable measurement only once its parameters are
frozen (horizon, thresholds, normalisation). Each registration freezes
EXACTLY ONE parameter set, chosen before the measurement is run. A different
parameter set is a DIFFERENT registration that spends again — running several
and reporting the best is the fishing AM-04 forbids, whether the variation is
across families or within one.

**Reporting duty:** every registered measurement's verdict is reported,
including those that find nothing.

## §1.4 DETECTOR DEPENDENCIES

- **Available now:** `liquidity_sweep` v`H-07-v1.1-appendixB` (S04, parity
  3,099 / 465 / 325). Supports M1, M2, M3, M4, M8, M10 and parts of M9.
- **Not yet built:** market structure shift (M5), order block (M6), fair
  value gap (M7). These measurements are SPECIFIED and NOT REGISTRABLE until
  their detectors exist and pass their own planted-truth / clean-control
  drills.

This section exists so that "we cannot test this yet" is a visible fact
rather than a silent omission. A measurement waiting on a detector is not a
gap in the concept; it is an instrument not yet built.

## §1.5 ASSUMPTIONS

| # | Assumption | Checked today? |
|---|---|---|
| A1 | Data is provably unaltered since export (sha256-bound provenance) | YES — S03 |
| A2 | Instrument is exactly `XAUUSD`; digits/point read from the terminal | YES — S03 |
| A3 | Server clock basis stable across the sample; no undetected DST shift mid-collection | PARTLY — drift between batches is detected; an absolute offset error in the first batch is NOT detectable |
| A4 | Bars are the timeframe they claim to be, contiguous, no silent gaps | PARTLY — row/span recorded; contiguity not yet independently verified |
| A5 | Window time judged has never been examined (VIRGIN) | STRUCTURAL — S02 ledger, with the known limit that unrecorded looking is invisible |
| A6 | The detector's mechanics match the pinned definition | YES — S04 parity, independent re-derivation |
| A7 | The null preserves the data's own dependence structure | YES — block resampling, block length derived from the detector's own constant |

## §1.6 BOUNDARY CONDITIONS

Conclusions are **not** claimed for:

- choppy or directionless market structure;
- sweeps occurring without meaningful structural context;
- sweeps occurring at insignificant liquidity levels;
- markets with abnormal data quality or integrity issues;
- situations where required detector dependencies are unavailable;
- conditions outside the documented assumptions of the measurement used.

> **BOUNDARY CONDITIONS DEFINE WHERE THE CONCEPT IS NOT BEING ASSERTED. THEY
> ARE NOT EXPLANATIONS FOR NEGATIVE RESULTS.** (Owner, O-018 — binding.)

A boundary invoked *after* a disappointing verdict, to explain it away, is a
violation of this specification, not an application of it. Boundaries are
declared here, in advance, and a measurement that ran inside them owns its
result whatever the result is.

**Open honesty about the present state:** several boundaries above
(structural context, level significance, choppiness) are not yet
*mechanically* enforceable — the detectors that would identify them are M5–M7,
which do not exist. A measurement registered today therefore runs over ALL
sweeps, including ones the Owner's own trading framework would reject. That
is a real limitation of the first measurement and must be stated in its
verdict — not used afterwards to discount it.

## §2 STATUS

- Concept specified; no measurement registered yet.
- Family budget: 100 registrations (AM-03), geometric alpha spending;
  registration #1 receives alpha = 0.025.
- S06 will register and judge **exactly one** measurement from §1.3, chosen
  by the Owner. Its verdict will speak about that measurement only, never
  about this concept (AM-04).
