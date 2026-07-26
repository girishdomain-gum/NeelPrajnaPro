# The Existence Claim Framework (ECF)
## How QRF establishes that a market phenomenon recurs beyond chance — design specification

Status: **DRAFT for Owner review** — no-write session. On ratification: enters the Gen-2 freeze amendment explicitly (it extends the Scientific Core's null-design library — the one piece of genuinely new judging machinery in Generation 2), is drafted as sealed methodology in a write window, and is drilled with planted truth before judging any real claim.
Position in the estate: Volume 0 defines *that* existence precedes mechanism precedes prediction; this document defines *how* existence is judged. The Battery remains the only judge; ECF gives it the null constructions and verdict semantics for a claim type Generation 1 never faced.

---

## 1. The question, stated precisely

Generation 1 could answer: *"Does trading on X outperform an appropriate null?"* Generation 2's first question is different and prior: *"Does phenomenon X objectively recur in XAUUSD beyond what chance produces?"*

"Beyond chance" is where all the difficulty lives, because market data is not a fair coin. Gold's H1 series carries drift, volatility clustering, session structure, weekend seams, fat tails, and serial dependence — and a naive null (shuffled bars, IID returns) destroys all of that nuisance structure, making almost *any* detector rule look like a discovery. The entire framework is one commitment:

> **The null must keep everything about the market that is not the claim, and destroy only the claim.**

## 2. The trap that must be designed around first: definitions that guarantee their own recurrence

Take compression defined as "ATR(14) percentile < 20 over the trailing year." That rule fires ~20% of the time **by construction** — the percentile sets the base rate. A claim that "compression exists because compression bars occur" is empty; the definition purchased the occurrences.

So the ECF's first sealed rule: **an existence claim must state which property of the phenomenon is NOT fixed by its own definition, and claim recurrence structure in that property only.** For percentile-anchored or threshold-anchored phenomena, the testable content is never the *amount* of occurrences — it is their *arrangement*: duration distributions, clustering in time, positioning within sessions, or transitions to and from other phenomena. Anchor sentence: **for a rule that buys its own base rate, existence lives in the arrangement, not the amount.**

## 3. The three existence claim forms (each with its matching null)

Every existence registration declares exactly one form:

**E1 — Rate claims.** "Detector D fires more often than structure-free markets produce." Valid only when D's definition does not fix its own rate (absolute thresholds, pattern completions). Statistic: occurrence rate vs the null ensemble's rate distribution.

**E2 — Arrangement claims.** "D's firings are non-randomly arranged" — they cluster, persist (duration distributions differ from the null's), or concentrate in declared scope coordinates (sessions, states). This is the natural form for percentile-anchored phenomena. Statistic: a pre-sealed arrangement measure (e.g., inter-event spacing distribution, run-length distribution) vs the null ensemble.

**E3 — Association claims.** "Phenomenon A is followed by / co-occurs with phenomenon B beyond chance" — the transition-structure claims your behavioural models are made of ("sweeps follow compression"). Statistic: conditional co-occurrence or transition frequency vs nulls that break only the A→B linkage.

## 4. The null constructions (the new sealed library)

Three families, each preserving different nuisance structure; every existence claim pre-seals which it will face — and a claim of any weight faces more than one:

**N1 — Rotation nulls (cheapest, most assumption-free).** Circularly rotate the detector's event stream against the price series (or rotate B's events against A's for E3), preserving both series' internal structure entirely and destroying only their alignment. Session-aware variant: rotate by whole days within matched weekday/session frames so calendar structure survives. Primary null for E3; supporting null for E2.

**N2 — Block-resampling nulls.** Stationary/block bootstrap of returns with pre-sealed block lengths chosen to preserve volatility clustering and serial dependence at the scales the claim does NOT concern, then detector re-run on each surrogate. Primary null for E1 and duration-form E2. Weekend seams and session boundaries are preserved by resampling within a calendar template — seams are data, never convention (Finding #4's lesson, carried forward).

**N3 — Model-based surrogates (strongest, most assumption-laden).** Fit a null process (e.g., a GARCH-family volatility model with empirical innovations) on the burned calibration window; simulate ensembles; re-run the detector. Every use of N3 records its model dependence explicitly — per Volume 0 assumption 3, the null's own assumptions are stated, not hidden. N3 is corroborating, never sole.

**Sealed before data:** the claim form, the null family set, ensemble size, the test statistic, the decision threshold at the family-corrected α, and the interpretation of every outcome — all before the judging window is examined. Registration spends the attempt; an existence claim is priced exactly like any other.

## 5. Verdict semantics (tri-state, unchanged in spirit)

- **ESTABLISHED** — the arrangement/rate/association survives *every* pre-sealed null family at the corrected threshold, on data that did not shape the detector's definition. The phenomenon's lifecycle advances candidate → established. **Establishment is always operationalization-scoped:** the Record reads "established as operationalized by detector D-vN in scope S," never "true." The abstract phenomenon accumulates standing only through such detector-scoped verdicts; a future, better detector opens a new sealed investigation of the same phenomenon — convergence across independent operationalizations raises the phenomenon's standing, divergence localizes what was artifact of the instrument, and no prior Record is ever invalidated by either. Establishment licenses mechanism and predictive claims about it; it licenses **no** trading conclusion whatsoever.
- **NOT ESTABLISHED** — a decisive failure against the sealed nulls within the declared scope. Recorded as a scoped negative ("no arrangement structure in London-session compression durations, 2024–25"), feeding the beliefs document. Silence, not proof of absence — a *powered* absence claim remains its own sealed design with a smallest-effect-of-interest.
- **INSUFFICIENT** — the pre-sealed event-count floor was not met. Floors for existence claims are set by injection-calibrated power (see §6), not convention; 28 Mondays could not impersonate evidence in Gen 1, and 30 sweeps will not impersonate a phenomenon in Gen 2.

## 6. Certification before first use (the G-3 discipline, inherited whole)

Before the ECF judges any real claim, it is drilled — and the drills are themselves sealed and recorded:

1. **Planted-truth drills:** inject synthetic phenomena of known form and strength into N2/N3 surrogate series (clustering injected into event streams, manufactured A→B couplings); the ECF must detect them at its claimed power.
2. **Clean-control drills:** run the full pipeline on surrogates with *nothing* planted; the ECF must establish nothing at the sealed false-positive rate. An existence framework that cannot stay silent in silence is not ready.
3. **Injection-calibrated power curves:** the drills produce, per claim form and null family, the minimum event counts at which stated power is achieved — these become the sealed n-floors of §5.
4. **IVF parity:** the verifier re-implements the null constructions independently from the normative text of this document and re-derives every ensemble statistic before any ECF verdict is relied upon.

## 7. What the ECF explicitly does not do

It does not rank phenomena, search the Observation Space, or propose candidates (Discovery is Gen 3; the ECF only judges what is sealed before it). It does not upgrade an established phenomenon into a tradeable signal — that requires a separate predictive claim against G-3's placebos, priced separately. And it does not soften for machine-sourced or atlas-browse candidates — same nulls, same floors, discounted priors already paid at registration.

## 8. Honest limitations, stated at birth

All nulls are models of "no structure," and "structure-free" is itself theory-laden; N1–N3 triangulate but cannot exhaust the ways chance can masquerade. Establishment is always conditional on the declared scope and on 2024–26 gold's regimes until cross-regime rungs are climbed. And the deepest limitation is Volume 0 assumption 1 working as intended: **it is a live possibility that nothing at H1 retail granularity reaches ESTABLISHED — and the framework is built so that this outcome, honestly reached, is a scientific result about gold, not a failure of the ship.**

## 9. Scope of applicability

The Generation 2 Existence Claim Framework is designed for **detector-definable market phenomena** — those expressible as a sealed mechanical rule producing an event stream or state series (compression, sweeps, imbalance, displacement, and their kin). The scientific principles beneath it — claim registration, nulls matched to the claim, pre-sealed methodology, planted-truth certification, independent verification — are intended to be stable across generations. Future generations may introduce additional claim forms for **latent, probabilistic, or learned phenomena** (hidden states inferred by distribution rather than fired by rule) without invalidating this framework; such an extension is recorded as a deferred item, promotable only when the science demands it, through the front door. Generation-2 capability is not to be mistaken for universal scientific truth — this framework solves Generation 2's problem completely, and claims nothing more.

---
*Anchor: **keep everything that is not the claim; destroy only the claim — then see if the claim survives.***
