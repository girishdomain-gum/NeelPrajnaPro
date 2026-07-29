# GENERATION 1 FINAL REPORT · QRF — a scientific operating system for market hypotheses
Author: architect (fable) · Approved for the record at GO-S10 · 2026-07-26
Scope: Sprints 1–10, journal records 1–83 (+ the freeze note), repo
girishdomain-gum/qrf. This document is the permanent reference; the
ledger is the evidence.

## 1. What Generation 1 built
Not a trading system. Not merely a hypothesis-testing framework. A
**scientific operating system**: an append-only, hash-chained ledger of
every observation, claim, cost, and verdict; a judging pipeline whose
every number is independently reproducible; and a governance loop
(Owner ⇄ Architect ⇄ Developer) in which no role can silently pay for
its own mistakes. Subsystems, in the order they earned trust:
- **Observatory & detectors** (S1–S3): events with knowability
  contracts; nothing detected that could not have been known at its bar.
- **Calibration & screener** (S4): parameter sweeps as counted trials,
  shortlists as candidates — never claims.
- **WindowLedger & VIRGIN reserves** (S3+): data reserved by a human's
  typed phrase; burned windows unusable twice; reserve-by-market-time
  doctrine (a bar's hours, not its dataset label, are what is reserved).
- **Battery** (S5–S6): pre-registered thresholds, anchored walk-forward
  splits (DEVQ-011), pessimistic fills (DEVQ-012), family-deflated
  alphas (DEVQ-015), tri-state verdicts where INSUFFICIENT ≠ weak FAIL.
- **Placebo (G-3)** (S8): nulls matched to CLAIM TYPE, sharing the
  judge's own pipeline; the null for a timing claim carries the
  market's drift — the bar is "beats random timing", never "beats zero".
- **Graduation (G-1)** (S8): four refuse-before-write gates; a
  promotion record's existence is itself proof the gates held.
- **Independent Observation Lens** (S9): a second, independently
  produced feed (independence a declared SPECTRUM: broker/LP/venue);
  clock-era alignment detected empirically; agreement pre-thresholded
  BEFORE computation. First lens: Exness, tier=broker, 0.9544 ≥ 0.95.
- **Trial ledger completion** (S10, ADR-011): registration spends the
  attempt; sweeps charged at birth; the garden of forking paths priced
  at the gate.
- **IVF** (every sprint): an Architect-owned verifier that re-implements
  every rule from the NORMATIVE texts, re-derives every recorded number
  (to 1e-9 and beyond, bootstrap CIs included), replays every seeded
  null, and is itself drilled with planted frauds — clean control
  mandatory — before it may judge the real ledger. Since S9 the checks
  are rehearsed end-to-end on raw data before shipping.
- **HC**: the human layer, label-driven capture tooling, and the
  standing proof of its worth: it found what two machine layers agreed
  on (the idealized-calendar error) because eyes see differently.

## 2. Generation 1 Design Principles (added at Owner review — the
## philosophical foundation Generation 2 is bound to preserve)
1. **Observations before interpretation.** Detectors record what was
   knowable at the bar; meaning is assigned later, under seal, or not
   at all. Prediction first, ontology later.
2. **Registration before experimentation.** Thresholds, methods,
   placebo constructions, agreement criteria — sealed BEFORE the data
   is looked at; the ordering is auditable in the chain and audited.
3. **Every attempt counts.** The scientific cost is paid at
   registration, not at success; sweeps are charged at birth; the
   garden of forking paths is priced at the gate (ADR-011).
4. **Candidate discovery is not validation.** Screeners produce
   candidates; only a sealed hypothesis, judged placebo-first against
   its claim-matched null, produces a verdict.
5. **History is append-only.** Nothing is rewritten; the ledger
   learns by new records; corrections are themselves records.
6. **Evidence must be reproducible, not merely archived.** Every
   dataset rebuilds hash-identical from raw sources; every verdict
   re-derives independently from normative texts.
7. **Independence is a spectrum, declared and never upgraded.**
   Corroboration requires an independently produced observation, and
   the depth of that independence is on the record.
8. **Reserves are inviolable and human-held.** Unseen data is
   designated, and would only ever be unlocked, by the Owner's typed
   hand — never by an AI's judgment.
9. **Verification is layered, and the layers must disagree to be
   useful.** Machine recomputation, adversarial drills with clean
   controls, and human eyes each see what the others cannot.
10. **Tripwires bind their authors.** Pre-registered guards are
    honored especially when they fire on the one who wrote them;
    predictions are recorded so they can fail.
11. **Scientific integrity over positive findings.** A FAIL that
    answers a question outranks a PASS that flatters one; zero
    promotions honestly refused is a result, not an absence.
12. **Boundaries hold under convenience.** Roles refuse work their
    rules forbid, even when compliance would be easier — the system
    is its behavior at exactly those moments.

## 3. The scientific record
4 hypotheses judged, 0 promoted, every verdict reproducible:
- H-001 FVG follow-through — FAIL.
- H-002 intra-week FVG — FAIL (n=637, p=0.93): the weekend question
  ANSWERED; excluding weekend-born FVGs does not rescue follow-through.
- H-003 Monday drift — INSUFFICIENT (n=28<40): the floor refused to let
  28 Mondays impersonate evidence.
- H-004 Monday drift v2 (multi-window, calendar exit, sealed placebo) —
  FAIL (n=56, +5.00/trade net, p=0.108): Monday's profit is
  indistinguishable from RANDOM TIMING.
Families: xauusd_h1/smc.fvg — 1004 counted trials, two decisive FAILs,
deprioritized by its own pre-registered interpretation (any new claim
faces α≈5e-5). seasonality.calendar — 2 attempts, no edge shown.
Wave-2 (2025): 39/500 leads, long-only, one parameter neighborhood —
the Owner's read, on the record at GO-S10: the trend in 39 costumes;
candidates, not evidence. One corroborated lens; gate (c) payable,
never yet paid — because nothing earned it. **Zero promotions is the
proudest line in this report.**

## 4. Findings tally and its lessons — Architect 17, Developer 4
Twenty-one findings across ten sprints, every one caught BEFORE harm,
most by the system's own tripwires. The recurring species and the
rules they left behind:
- Prose asserting unverified properties (#14 ruling-vs-artifact, #15
  idealized calendar, #16 circular "UTC verified", #17 saturated
  criterion) → verify against the REAL artifact/data; attach tripwires
  to your own criteria and HONOR them when they fire on you; record
  predictions so they can fail (the US-DST prediction: confirmed
  0.966/0.953 at the US spring-forward weekends).
- Boundary arithmetic (Dev #3 one-bar reserve claim; #4 hardcoded DST)
  → seams and clocks are verified from data, never conventions.
- The finest moments were refusals: the placebo engine's SELF-STOP
  under its own guard; the Developer declining to author an ADR its
  rules forbade. A system is its behavior when compliance would be
  easier.

## 5. Known limitations (stated so Generation 2 inherits them honestly)
One instrument (XAUUSD), one timeframe (H1), ~2 years judged; broker
server clocks (doctrine handles it; absolute UTC never needed but never
available); retail cost model (0.47/oz round trip — a spread-sensitive
edge would look different at other venues); lens independence declared
at BROKER tier only (LP/venue independence unknown); bootstrap CI
recorded but never load-bearing; belief records minimal (single-verdict
stances; the Bayesian ADR was deliberately deferred); HC coverage is
sampled, not exhaustive; and every negative result is conditioned on
THIS market regime — 2024–25 trending gold — a fact the placebo
measured (6/20, 1/20 null passes) but cannot remove.

## 6. Recommendations for Generation 2
1. **Build knowledge, not framework.** The OS is frozen. New concepts
   (CRT, TBS, momentum, order flow, anything) arrive as families +
   detectors + sealed hypotheses — applications, not subsystems.
2. **New families over deeper mining**: the Owner's strategic read
   stands — smc.fvg's α-burden says broaden, don't optimize.
3. **Independence up the spectrum** when a promotion is ever near:
   LP-tier or venue-tier corroboration for anything that would trade.
4. **Regime honesty**: any Gen-2 claim should state the regimes it was
   judged in; consider a bear/flat-regime reserve when data allows.
5. Deferred deliberately, revisit only on need: Bayesian beliefs ADR,
   OB break-bar gate, HC coverage expansion, additional lenses under
   the Independent-Observation-Lenses naming.

## 7. Closing
"By the end of Generation 1, QRF no longer needs to know whether a
future hypothesis is based on FVG, CRT, TBS, momentum, moving
averages, order flow, or an entirely new market concept. It already
knows how to evaluate scientific claims about them." — the Owner,
2026-07-26. That sentence is the deliverable. The framework asked one
question for ten sprints — *did we honestly count every opportunity to
fool ourselves?* — and the ledger can now answer: yes, and here is the
proof, reproducible from raw CSVs to the last digit.
