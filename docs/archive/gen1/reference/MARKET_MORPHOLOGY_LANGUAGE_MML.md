# The Market Morphology Language (MML)
## A universal, deterministic geometry language for market structure — QRF architectural standard, version 1

Status: **DRAFT for Owner ratification** — no-write session; nothing binds. On ratification: enters Volume 2 (the Market Science Model) as the observation-layer vocabulary for candle geometry; the ratification text is §14.
Companion: the CCC Hidden Patterns Handbook (source of the merge operator; its trading content is deliberately out of scope) · the ECF design · Volume 0.
Design standard applied: *assume classical candlestick literature never existed — could QRF invent this language from first principles?* This document is written in that order: geometry first, names never.

---

## 1. Purpose

QRF Generation 2 must describe market geometry — beginning with candles, single or merged — using descriptors that are **mathematically defined, deterministic, implementation-independent, extensible, human-readable, and machine-friendly**, and that carry **zero interpretation**: no bullish, no bearish, no reversal, no psychology, no trade. Classical names (Hammer, Doji, Shooting Star) are demoted permanently to optional aliases assigned *after* scientific standing, never before. Generation 1 recognized human-defined patterns; Generation 2 defines its own morphology and lets human patterns re-emerge as aliases only if the evidence makes them worth naming.

> **Anchor:** *Measure → classify → observe → establish → explain → and only then, if it helps communication, give it a name.*

## 2. Scientific motivation — what the handbook discovered, restated without trading

The CCC handbook contributes two genuinely scientific ideas, separable from every trading rule around them:

**The merge operator.** For any contiguous window of N candles: `O* = first Open · C* = last Close · H* = max High · L* = min Low`. Deterministic, discretion-free, and — the handbook's own sharpest observation — **identical to timeframe aggregation**: merging N consecutive M5 candles is exactly how the corresponding higher-timeframe candle is built. A merged window is therefore a *synthetic higher-timeframe candle anchored anywhere*, not only on clock boundaries. Merge-space is the space of all such anchored candles.

**The hidden gate.** A geometry is *merge-revealed* when the merged window exhibits it and no constituent candle does. This is a set-difference in descriptor space (§8), computable without any human judgment.

Both ideas survive the deletion of every trading sentence in the handbook. That is what makes them QRF material.

## 3. First principles: what a candle's geometry actually is

Any OHLC object — one candle or any merge — decomposes into exactly three non-negative components that partition its range:

```
   upper wick  u = H − max(O,C)
   body        b = |C − O|
   lower wick  l = min(O,C) − L
   range       R = H − L = u + b + l        (identity, always)
```

Normalize by the range: `U = u/R, B = b/R, L = l/R`, so **U + B + L = 1**. This identity is the deepest fact about candle geometry, and the language must be built on it:

> **The shape of a candle is a point on a 2-simplex.** Three fractions, but only two degrees of freedom — every candle shape lives inside a triangle whose corners are "all upper wick," "all body," "all lower wick."

Three consequences follow immediately. First, shape is **scale-free**: a 30-cent doji and a 30-dollar doji are the same point — so absolute size (range/ATR) is *not* shape and must live elsewhere (§6). Second, shape is **direction-free**: U, B, L are identical for a green and red candle of the same silhouette — so direction lives elsewhere too. Third, **not every descriptor can exist**: because the fractions sum to 1, a code claiming "huge upper wick AND huge body AND huge lower wick" describes a point outside the triangle. The language below inherits this honestly — its feasible codes are exactly the discretization of the simplex, roughly one-fifth of the naive code space, and any implementation emitting an infeasible code has a bug the language itself can catch. A vocabulary that can detect its own corruption is worth the geometry lesson.

## 4. The bucket system — the most consequential decision in this document

The descriptor encodes **classification buckets, never measurements** (no two candles are identical; biology records "long-wing class," not 12.371 cm — the precise numbers remain on the Scientific Object, §6). The design questions are how many buckets, and where the boundaries sit.

**Boundaries: equal-width deciles, fixed forever — and here is the scientific argument, because the tempting alternatives are traps.** Quantile-based or learned boundaries adapt to the dataset — which makes the *definition of the geometry a function of the data it will be tested on*. That is the definition-buys-evidence trap (ECF §2, Volume 0 §3) wearing a calibration costume, and it additionally destroys reproducibility across instruments, eras, and implementations: MD-115 on gold-2024 would not mean MD-115 on gold-2019. Logarithmic boundaries privilege one region of the simplex by *assumption* rather than evidence. Equal-width boundaries are the only choice that is deterministic, dataset-independent, era-stable, and implementation-trivial:

```
   digit(x) = floor(10 · x),  capped at 9        x ∈ {U, B, L}
   digit d  ⇔  component fraction ∈ [10d%, 10(d+1)%)   (digit 9: [90%, 100%])
```

**Count: ten buckets (0–9), not five.** Ten gives decile resolution — enough to separate a 3% body from an 8% body (both "tiny" in a 5-bucket scheme, meaningfully different near the doji edge) — while the simplex constraint keeps the feasible vocabulary small: digits sum to 8, 9, or 10 by the flooring arithmetic, giving **≈ 60–70 feasible codes**, a vocabulary a human can actually learn and a family-discovery process (§9) can actually cover. Finer resolution is *never* added by more digits: it already exists, losslessly, in the raw fractions on the Scientific Object. The descriptor is the compact summary; the measurements are the truth.

**Zero is a legal digit and means "under 10%," not "absent."** A body is never exactly zero in practice, but B = 0.4% is digit 0 — so `MD-306` is a near-doji with a meaningful upper wick, and no special case is needed. The digit alphabet carries no adjectives: 7 does not mean "large"; 7 means [70%, 80%). Interpretation is banned even from the legend.

## 5. Descriptor syntax — a core that never changes, a grammar that can grow

```
   MD-UBL                          the immutable three-digit core
        U = upper-wick decile
        B = body decile
        L = lower-wick decile

   MD-118        upper ∈ [10,20)% · body ∈ [10,20)% · lower ∈ [80,90)%
   MD-334        upper ∈ [30,40)% · body ∈ [30,40)% · lower ∈ [40,50)%
   MD-802        upper ∈ [80,90)% · body ∈ [0,10)%  · lower ∈ [20,30)%
```

Read left-to-right as the candle reads top-to-bottom: upper wick, body, lower wick. The identifier itself carries information — `MD-802` is legible at sight as "dominant upper wick, negligible body" without a name ever being uttered.

**The extension grammar (growth without redesign).** The core is shape only, forever. Everything else attaches as tagged, order-independent suffix fields, each one a separate measurement dimension that never modifies the core:

```
   MD-118                          shape only (always valid alone)
   MD-118 · dir=+                  direction as a field   (+ close>open, − close<open, 0 equal)
   MD-118 · n=4                    merge width: built from 4 candles (n=1 = a raw candle)
   MD-118 · sz=3                   size class: decile of range/ATR ratio (boundaries sealed separately)
   MD-118 · pos=…, ctx=…           future dimensions, same pattern
```

Rules of the grammar, binding: **(1)** the three-digit core is never reinterpreted, renumbered, or extended in place — a change to bucket boundaries or component definitions is a new *language version*, declared at the registration level (`MML v1`), never embedded per-descriptor; **(2)** no suffix may encode interpretation (no `bias=bull`); **(3)** any consumer may ignore any suffix and still read the shape — that is what backward-compatible means here. This answers the independence test honestly: derived from first principles, the design lands compatible with the proposed MD-UVW — same three-digit shape core — and differs in three defended ways: ten buckets not five, the simplex feasibility constraint made explicit, and growth moved out of the digits into a suffix grammar so the core can be immutable.

**The reflection operator — symmetry as a hypothesis, never an assumption.** Define `ρ(MD-ubl) = MD-lbu`: the vertical mirror (`ρ(MD-802) = MD-208`). Mirror pairs receive **distinct** descriptors, because price has a real vertical asymmetry (up and down are not interchangeable in markets) — but the operator makes symmetry *testable*: "mirror-pair descriptors have statistically indistinguishable arrangement behavior" is a registrable claim, judged by the ECF like any other. The language takes no side; it hands the question to the evidence.

## 6. Scientific Object integration — the descriptor is a summary, never the object

Ratified position on the classification-vs-measurement question: **the descriptor is one attribute of a measurement-rich Scientific Object** (Option B, adopted). If evidence one day shows that raw symmetry or ATR ratio matters more than the decile code, nothing is repainted — the richer truth was preserved from the start:

```
   Scientific Object · type: MorphologyObservation        (layer: Observation)
      window            {instrument, timeframe, start, n}     n=1 ⇒ raw candle
      merge             {O*, C*, H*, L*}                       Measurements
      fractions         {U: 0.146, B: 0.117, L: 0.737}         Measurements (lossless)
      descriptor        MD-117 · dir=+ · n=4 · sz=3            Observation (this language)
      derived           {range, range/ATR(14), symmetry |U−L|, …}
      hidden_gate       {revealed: true, constituent_descriptors: [MD-334, MD-244−, …]}
      detector          {name, version}                        provenance
      scope             Observation Space coordinates          per Volume 2
```

Placement in the Volume-0 layering is exact: OHLC values are **Measurements**; fractions and the descriptor are **Observations** (deterministic arithmetic, zero theory); any claim that a descriptor or family *recurs with structure* is a **candidate Phenomenon** — and only the ECF can promote it to established.

## 7. The universality clause

Nothing in §3–§5 mentions merging. The language describes **any OHLC object**: a raw H1 candle is the `n=1` case, a merged window the `n=k` case, a clock-aligned H4 candle a special case of the merge. One vocabulary spans them all — which is precisely what makes the handbook's central question expressible as a clean comparison: *does anchored merge-space contain descriptor structure that clock-aligned candle-space lacks?* And the same three-component-decile pattern generalizes beyond candles: a compression episode (depth/duration/decay), a gap (size/position/fill), an imbalance — each is a small set of normalized components, discretized by the same fixed-boundary discipline, under the same grammar. The MML is the first dialect of a general shape language; future dialects register their component definitions the same way this one does, and change nothing here.

## 8. The hidden gate, formalized

A window's geometry is **merge-revealed with respect to a descriptor set S** when:

```
   descriptor(merged window) ∈ S    AND    descriptor(candle_i) ∉ S  for every constituent i
```

— evaluated on shape cores only (suffixes excluded unless the claim seals them in). "Hidden" is thus a computable set-difference, free of judgment, and *parameterized by S*: what is hidden depends on which descriptor set you ask about, which is exactly how a claim should have to declare itself.

## 9. Geometry families — discovered, never predefined

A **Geometry Family (GF-nnn)** is a set of descriptors grouped because *evidence* showed they behave alike — similar arrangement statistics, similar associations, similar hidden-gate behavior — never because they look alike to a human. Families are Scientific Objects with the universal lifecycle: proposed (by a human or, in Gen 3, by Discovery mining descriptor co-behavior), **registered as a priced claim** ("the members of GF-007 share arrangement structure distinguishable from non-members"), judged, established or not. A family is a discovered fact about the market, not a naming convenience — and classical patterns, if they are real, will re-emerge here as families that happen to overlap old names. If they are not real, the families that *do* emerge will be the truth the names were approximating.

## 10. The alias system — names as courtesy, never identity

An append-only **alias registry** maps human names onto descriptor sets, in one direction only:

```
   alias "Hammer-like"        → { MD-0bL, MD-1bL : b ≤ 2, L ≥ 6 }     origin: classical, courtesy only
   alias "Doji-like"          → { MD-u0l : any u,l }                    origin: classical
   alias (none)               → GF-012                                   origin: QRF discovery, no name needed
```

Rules: the alias never appears in registrations, verdicts, or beliefs — scientific records speak MD and GF only; an alias may be attached, revised, or abandoned without touching any record; and a discovered family with no classical resemblance simply has no alias, which is the outcome to hope for — it would mean QRF found something the eye and the literature both missed.

## 11. Worked examples

```
   Merged window (n=3):  O*=2412.0  H*=2415.8  C*=2412.6  L*=2407.9      R=7.9
      u = 2415.8 − 2412.6 = 3.2  → U = 0.405 → digit 4
      b = |2412.6 − 2412.0| = 0.6 → B = 0.076 → digit 0
      l = 2412.0 − 2407.9 = 4.1  → L = 0.519 → digit 5
      descriptor: MD-405 · dir=+ · n=3          (feasible: 4+0+5=9 ✓)

   A "textbook hammer" silhouette:  U=0.05, B=0.13, L=0.82  →  MD-018
   Its mirror ρ(MD-018) = MD-810 — a distinct descriptor; whether the pair
   behaves alike is a claim for the ECF, not a property of the language.

   Infeasible (bug-detecting): MD-990 — impossible, the compiler of shapes rejects it.
```

## 12. Relationship to the ECF — and the multiplicity warning that must travel with this language

The pipeline, end to end: `Measurements → fractions → MD (Observation) → candidate Phenomenon (a descriptor/family + a recurrence-structure claim + a scope) → Existence claim (E1/E2/E3) → Mechanism claim → Predictive claim` — each stage priced, sealed, judged in order. Two ECF interactions deserve bold print:

**Overlapping windows are the arrangement problem incarnate.** Sliding an n-candle merge across the series produces massively dependent detections — window 1-2-3 shares two candles with 2-3-4. Raw counts are therefore meaningless; only ECF nulls that preserve the overlap structure (rotation nulls rotate the *event stream*, block nulls re-run the *detector*) can judge merge-space claims. The language emits descriptors; it never counts them as evidence.

**~65 feasible cores × suffix dimensions × window sizes × scope cells is a combinatorial family, and ADR-011 charges it at birth.** "Scan every descriptor for structure" is a several-thousand-trial registration the moment it is conceived. The honest openings are family-level claims sealed in advance. **Research Program 001**, drafted in that spirit: *"Does anchored merge-space (n ∈ {2,3,5}, sealed) contain merge-revealed descriptor arrangements — clustering, session concentration, or transition structure (E2/E3) — with respect to a pre-sealed descriptor set, beyond nulls that preserve overlap dependence and calendar structure, in scope XAUUSD H1-constituents 2024–25?"* — one family, one priced registration, one honest question. Not sixty-five.

## 13. Open research questions (registered, not answered here)

Bucket-boundary refinement (only via language version, with evidence of decile inadequacy) · the size-class (`sz=`) boundary scheme, sealed separately before first use · whether body-position needs its own suffix or remains derivable from U and L · mirror-symmetry (the ρ hypothesis) as an early registered claim · descriptor-sequence grammars (words made of shapes — Gen 3 at the earliest, Discovery territory) · the second dialect (compression geometry) as the universality clause's first real test.

## 14. Architectural decisions and recommended ratification text

Decisions taken in this standard, each reversible only by language version: **◆1** shape = simplex point (U,B,L of range) — direction and size excluded from the core; **◆2** equal-width decile buckets, 0–9, fixed forever — quantile/learned boundaries rejected as data-dependent definitions; **◆3** immutable 3-digit core + tagged suffix grammar; **◆4** mirrors distinct, ρ defined, symmetry left to evidence; **◆5** descriptor is an attribute of a measurement-rich Scientific Object (Option B); **◆6** families discovered and priced, never predefined; **◆7** aliases courtesy-only, absent from all scientific records; **◆8** the language is claim-silent — it describes, and only the ECF establishes.

> **Ratification text (proposed):** "The Market Morphology Language v1 is adopted as the observation-layer standard for candle geometry, single or merged, in QRF Generation 2. Its three-digit decile core (MD-UBL) is immutable; growth occurs only through suffix fields or a new ratified language version. No scientific record shall identify a geometry by a classical name. Morphology descriptors and geometry families are observations and candidates respectively; scientific standing is conferred exclusively by the Existence Claim Framework under the sealed methodology of Volume 0."

---
*Anchor for the whole standard: **the descriptor describes; only the evidence establishes.***
