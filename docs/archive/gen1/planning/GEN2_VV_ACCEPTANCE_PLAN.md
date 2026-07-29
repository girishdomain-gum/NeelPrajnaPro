# QRF Generation 2 — Verification, Validation & Acceptance Plan
*Four levels of assurance: unit testing · verification · validation · black-box acceptance*

Status: DRAFT, conditional on ratification. Companion: GEN2_EXECUTION_ROADMAP.md (sprint mapping lives there). Presentation copy: GEN2_VV_ACCEPTANCE_PLAN.docx.

**Governing rule, from Volume 0:** trust follows demonstration — for claims, for instruments, and for the platform itself. Every pass threshold in this plan is sealed before any test runs (tripwires bind their authors). Every failure is a tallied finding: root cause, fix, re-run from a clean state — never explained away.

## 1. The Four Levels at a Glance

| Level | Question it answers | Method | Primary sprint |
|---|---|---|---|
| L1 — Unit Testing | Does each component compute what its specification says? | Fixtures, property tests, boundary tests | S2–S4 (continuous after) |
| L2 — Verification | Do independent implementations agree on every number? | IVF re-implementation from normative text; parity to tolerance | S2–S6 (every sprint) |
| L3 — Validation | Does the instrument detect what exists and stay silent when nothing does? | Sealed planted-truth drills, clean controls, injection-calibrated power | S3–S4 (re-run on any change) |
| L4 — Acceptance | Does the whole platform, treated as a black box, behave as a trustworthy scientific instrument? | Blinded adversarial campaign BB-1…BB-6 | S8 |

**The levels nest:** L1 failures invalidate L2 runs; any L1–L3 change after certification voids the affected certificates and re-triggers the level above it. L4 runs only once L1–L3 are GREEN, and acceptance is granted only when all six L4 drill classes pass in a single unbroken campaign.

## 2. Level 1 — Unit Testing

### 2.1 MML descriptor engine
- Hand-computed fixtures: OHLC tuples with known fractions and known digits, including every decile boundary (x = 0.100000 vs 0.099999), the B ≈ 0 near-doji edge, and digit-9 capping at 100%.
- Simplex feasibility: every emitted code's digits must be geometrically consistent; a synthetic infeasible input must raise a hard error, never a silent code.
- Suffix grammar: order-independence of suffix fields; unknown suffixes ignored by consumers without altering core parsing.

### 2.2 Merge operator and hidden gate
- Merge identity test: merging N consecutive candles must equal the platform-aggregated higher-timeframe candle where clock boundaries coincide.
- Weekend and DST seam tests: merges spanning Friday close → Monday open, and the US spring-forward/fall-back weekends, computed from data, never convention (Generation-1 Finding #4's standing rule).
- Hidden gate: set-difference correctness against fixtures where the merged descriptor is present in zero, one, and all constituents.

### 2.3 Ordinal swing detector
- Knowability contract: no extremum may be emitted before its confirmation bar (k bars later); machine-checked over the full test corpus.
- **Monotone-invariance property test:** raw price and log price must yield the identical extremum set on every corpus — the design's central claim, executed as a test, not an assertion.
- Tie handling and plateau highs: sealed rule, fixture-tested.

### 2.4 Null constructions
- Rotation: rotated streams preserve each series' internal statistics exactly (they are the same series); only alignment changes. Rotation by whole days respects weekday/session frames.
- Block resampling: sealed block lengths; calendar-template preservation of sessions and seams; reproducibility under recorded seeds.
- N3 surrogates: fitted-parameter recording; seeded reproducibility; simulated series pass the same seam and calendar checks as real data.

## 3. Level 2 — Verification (Independent Re-derivation)

Verification means an independent hand reaches the same numbers. The IVF re-implements every rule from the normative documents alone — the MML standard, the ECF design, the sealed registrations — never from the Developer's code.

1. MML parity: the IVF's classifier must agree to the digit on every L1 fixture and on a sealed random sample of real burned-window candles.
2. Ensemble parity: every null-ensemble statistic re-derived to tolerance 1e-9; bootstrap confidence intervals included.
3. Verdict parity: every Battery ruling re-derived end-to-end from raw CSVs before it is relied upon (Volume 0 §3's independent-hand requirement, executed literally every sprint).
4. Drill-before-judge: the IVF itself is drilled with planted frauds, with a clean control, before it verifies anything real — the Generation-1 tradition, unchanged.

## 4. Level 3 — Validation (Scientific Certification)

Validation asks whether the instrument measures reality: does it find planted structure and stay silent in its absence? All drill designs are sealed before running.

### 4.1 Planted-truth drills (sensitivity)
- Injected descriptor clustering of sealed strengths into surrogate event streams; manufactured A→B couplings for E3; injected level-interaction structure for the PLM pipeline.
- Pass: detection at or above the claimed power at each sealed effect size.

### 4.2 Clean-control drills (specificity)
- The identical pipeline on surrogates with nothing planted but realistic nuisance (drift, volatility clustering, seams, sessions).
- Pass: establishment rate at or below the sealed false-positive rate. A framework that finds phenomena in silence is not ready — this drill has veto power over Phase C.

### 4.3 Injection-calibrated power curves
- Per claim form (E1/E2/E3) and null family (N1/N2/N3): minimum event counts at which stated power is achieved.
- **These curves become the sealed n-floors** of every Wave-1 registration; no registration may set a floor below its curve.

### 4.4 Re-certification triggers
- Any change to a detector, a null construction, bucket boundaries, or the language version voids the affected certificates; the drill class re-runs from a clean state before the changed component touches a real claim.

## 5. Level 4 — Black-Box Acceptance (Sprint 8)

**Definition:** Generation 2 is a claim-judging pipeline, so its acceptance test is adversarial and blinded — the examiner (the Architect, with the Owner holding the answer keys) feeds the whole system inputs whose ground truth the operator does not know, observes only outputs, and grades sensitivity, specificity, and auditability. QRF is treated as an instrument under test, exactly as it treats its own detectors.

**BB-1 · Blinded planted-phenomenon trial (sensitivity).** Synthetic OHLC datasets with known injected structure — descriptor clustering and level-interaction at sealed strengths — indistinguishable in format from real exports, interleaved with empty datasets. The Developer runs detection → registration → ECF → verdict without knowing which is which. Pass: planted phenomena at or above certified effect sizes are ESTABLISHED at the predicted rate.

**BB-2 · Blinded empty-world trial (specificity).** The interleaved no-structure datasets from BB-1, carrying realistic nuisance only. Pass: nothing establishes beyond the sealed false-positive rate. A failure of BB-2 fails Generation 2 outright, whatever else passed.

**BB-3 · Negative-control instrument.** The complete Wave-1 program — MRCG and PLM, same seals, same floors — executed end-to-end on a synthetic instrument (stochastic-volatility random walk, calendar-matched to gold). Pass: every claim returns NOT ESTABLISHED or INSUFFICIENT. This is the whole-system clean control: the dress rehearsal where nothing must happen.

**BB-4 · Stranger audit (black-box reproducibility).** An independent session with no access to the Developer's code — raw CSVs, the ledger, and the normative documents only — re-derives every Wave-1 number: descriptors, ensembles, statistics, verdicts. Pass: agreement to IVF tolerance. Volume 0 §3's independent-hand requirement, executed as an acceptance gate.

**BB-5 · Tamper drills (integrity).** Planted frauds in a sacrificial copy: an edited record; a back-dated seal; a descriptor census touching one VIRGIN bar; a registration whose hash post-dates its data access. Pass: chain verification, seal-order audit, and the WindowLedger each catch their plant, and the untampered control raises nothing.

**BB-6 · Interpretation-lock audit (epistemology as text).** A human-led sweep of every Wave-1 record for Ontological Discipline: no explanatory names, no classical identities outside the alias registry, every verdict operationalization-scoped, every belief scope-conditioned. Pass: zero violations; any violation is corrected by appended record, never by edit.

### 5.1 Grading and the acceptance decision
1. Each drill class passes or fails against criteria sealed before the campaign begins.
2. Any failure: tallied finding → root cause → fix → full re-run of the failed drill class from a clean state.
3. Generation 2 Wave 1 is ACCEPTED only when all six classes pass in a single unbroken campaign. Only then does the Gate-A evidence conversation begin.

---
*Anchor: **an instrument earns trust by being tested the way it tests everything else — blinded, priced, and with a clean control.***
