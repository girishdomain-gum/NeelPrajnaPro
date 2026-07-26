# QRF Master Architecture Rewrite — Chief Scientist Edition
*Conservative rewrite · Radical rewrite · Final recommendation · Self-critique*

Status: **DRAFT for Owner ratification** — no-write session; nothing binds.
Author: Fable, acting under the Master Rewrite Brief as Chief Scientist / Chief Architect / Devil's Advocate.
Verdict in one line: **adopt the Radical structure as the architecture's spine (Volumes 1–3), keep the Whiteboard Edition as the teaching layer, and accept the mission re-centering on markets — with three recorded disagreements.**

---

## 0. Rulings on the brief itself (exercising the granted authority)

Before rewriting, three places where I push back on the brief, and one where I reverse my own prior work:

**Disagreement 1 — the domain-independence test survives the mission change.** The brief re-centers QRF on markets permanently: accepted, and I'll argue it's *correct*, not merely permitted — a generic science platform is a bigger promise with zero evidence behind it, and "platform-itis" is how good systems dissolve into abstractions. But the *test* from the old Part 15 ("would this component work if finance were deleted?") is not a mission — it's an engineering instrument for catching accidental coupling (a `price` variable inside the Battery is a bug regardless of mission). The mission changes; the test stays, demoted from vision to lint rule.

**Disagreement 2 — "Market Theory" enters the pipeline but not the promise.** The brief's pipeline ends at Market Theory. I'll draw it — but under the same discipline that governed "principle": theory is what the far end of the ladder is *called*, never a deliverable any generation commits to. A theory is a set of principles that jointly explain phenomena across markets and regimes; QRF currently has zero principles. The word appears in the architecture exactly once, at the end of the ladder, with this caveat attached.

**Disagreement 3 — Phenomena replace Concepts entirely; I reject keeping both.** The brief says "Market Phenomena become the primary scientific objects." Taken seriously, "Concept" — the weakest word in the entire architecture, carrying no scientific commitment — should not survive alongside it. A phenomenon is standard scientific vocabulary with a precise meaning: *a reproducible regularity in observations*. So: **the type formerly called Concept is renamed and upgraded to Phenomenon**, with its scientific standing carried by lifecycle status, not by a second type: a *candidate phenomenon* is a sealed mechanical rule over Observations whose recurrence is unproven; an *established phenomenon* is one whose recurrence has survived the Battery beyond chance. The six categories (Event / Structure / State / Transition / Regime / Relationship) become *kinds of phenomena*. One word deleted, one word promoted, zero capability lost. This is the fifteen-year test passing: phenomenon → mechanism → principle → theory is how every mature science already talks.

**Self-reversal — my own v2 overweighted the platform framing.** v2's preamble said "trading is the first domain, not the defining characteristic." Under this brief that sentence is retired. The honest statement: the *machinery* is domain-general by construction (a fact, verified by the test above); the *mission* is markets, permanently. I wrote the earlier sentence; I strike it.

---

## 1. The scientific pipeline — the new spine (both rewrites share it)

```
   Measurements          raw numbers off the tape — indisputable
        ▼
   Observations          computed comparisons — arithmetic, no theory
        ▼
   MARKET PHENOMENA      reproducible regularities — candidate until
        ▼                 recurrence survives the Battery; established after
   Mechanisms            explanations of WHY a phenomenon exists
        ▼                 (liquidity transfer, inventory redistribution, absorption)
   Hypotheses            falsifiable claims — existence, mechanism, or predictive
        ▼
   Experiments           sealed designs: scope, n-floor, power, placebo type
        ▼
   Evidence              Battery output — Records, immutable
        ▼
   Beliefs               versioned stances, confidence-weighted, regime-conditioned
        ▼
   Market Knowledge      the organized whole: the Market Knowledge Graph
        ▼
   Market Principles     beliefs that survived leaving home (cross-market, cross-regime)
        ▼
   Market Theory         principles that jointly explain — named, never promised
```

Three claim types fall out of the pipeline naturally, each with its matching null: **existence claims** ("this phenomenon recurs beyond chance"), **mechanism claims** ("it recurs *because* of X" — testable by the mechanism's distinguishing predictions), and **predictive claims** ("conditional on the phenomenon, forward returns differ from the claim-matched placebo"). Generation 1 only ever tested the third kind. Naming all three is the single largest scientific upgrade in this rewrite: it lets QRF establish *that* something happens before spending α on *why* or *whether it pays*.

> **Anchor sentence:** *First establish that it happens; then why it happens; only then whether it pays.*

---

## 2. Version A — Conservative Rewrite (minimal structural change)

Keep the Whiteboard Edition's six parts and 21 chapters. Apply deltas in place:

1. **Preamble:** destination statement replaced — *QRF is an Autonomous Market Science Platform; XAUUSD is the first laboratory; trading is the experimental laboratory for discovering market phenomena, mechanisms, relationships, principles, and eventually an evidence-based market theory.* Five cores retained, fifth renamed **Trading Domain**.
2. **Ch 5–6:** "Concept" → "Phenomenon" throughout; the Observation Model becomes the **Phenomenon Taxonomy** (six kinds); candidate/established status added to the universal lifecycle's Validated/Replicated rungs.
3. **New Ch 5B:** the pipeline of §1, with the three claim types and their nulls.
4. **Ch 10.2:** Knowledge Graph → **Market Knowledge Graph**; "Reputation" and "Knowledge Decay" cease to be named capabilities and become properties of the Belief type (confidence composition and revalidation scheduling) — two boxes deleted, nothing lost.
5. **Ch 13.4:** ladder extended one rung to Theory, with Disagreement 2's caveat.
6. **Ch 14:** retitled *The coupling test* — an engineering lint rule, not a vision.

**Cost:** the document's chapter order still reflects its discovery history (Gen-1 machinery first, pipeline late), not the science. **Benefit:** full continuity with three rounds of review; every cross-reference survives.

---

## 3. Version B — Radical Rewrite (rebuilt from first principles)

Ignore the existing chapter order. The architecture is organized as the pipeline itself — machinery appears where the pipeline needs it, not where history built it. This becomes the shape of **Volumes 1–3**:

```
VOLUME 1 — THE CONSTITUTION (10–20 pages, ratified first, changes almost never)
   Mission (markets, permanently) · Twelve Principles · permanently-human
   powers · freeze & amendment procedure · evidence philosophy (claim-
   matched nulls · powered absence · every attempt counts · trust follows
   demonstration) · Record/Object distinction · the pipeline as the canon
   of stages · the Theory caveat

VOLUME 2 — THE MARKET SCIENCE MODEL (what exists)
   2.1  The two roots: Record (immutable) and Scientific Object (versioned)
   2.2  The universal lifecycle; α charged at Registered
   2.3  Pipeline stage types, in order:
        Measurement · Observation · Phenomenon (six kinds; candidate/
        established) · Mechanism · Hypothesis (three claim types) ·
        Experiment · Evidence(Record) · Belief · Principle
   2.4  Observation Space — the coordinate system every stage instance
        declares; Core vs Scientific dimensions; Neighborhoods; the
        labeling-never-search rule
   2.5  The Market Knowledge Graph — typed edges over pipeline objects;
        lineage as the pipeline made queryable; contradiction as evidence

VOLUME 3 — THE PLATFORM (what runs)
   3.1  Scientific Core (frozen): Battery · placebo engine · multiplicity ·
        graduation gates · lens · IVF — the only judge, unchanged
   3.2  Knowledge Core: Ledger of Records · Object store · the Graph ·
        beliefs document · Narrow Atlas (burned windows, descriptive, unranked)
   3.3  Research Core (Gen 3): Discovery Engine (mines Observations for
        candidate phenomena; planted-nonsense certified) · Experiment
        Designer · Gap & Contradiction services
   3.4  Autonomy Core (Gen 4): Orchestrator — Planner, Scheduler, Designer,
        Resource Manager, Memory, Reporter + services — inside sealed
        envelopes; the six permanently-human powers cited from Volume 1
   3.5  Trading Domain: financial Measurements · detectors · cost models ·
        instruments & reserves · the lens inventory — the only volume that
        knows what a pip is

VOLUME 4 — IMPLEMENTATION (modules, interfaces, storage; changes weekly)
+ RESEARCH HANDBOOK (themes, category mix, roadmap, portfolio — planning)
```

What the radical version **deletes** outright, under "never preserve complexity because it exists": the standalone Reputation and Decay capabilities (→ Belief properties); the Curiosity Engine as a named component (→ a Planner *policy*: an exploration weight, one parameter, not a subsystem); Autonomous Bootstrapping (→ a startup procedure); the Detector Registry (→ Objects of type Detector); "Concept" as a word; "Observation Model" as a name (→ Phenomenon Taxonomy); the generic-platform destination statement.

**Cost:** breaks continuity with three review rounds; every existing cross-reference must be remapped once. **Benefit:** the architecture finally *is* the science — a newcomer in year 15 reads the pipeline and knows where everything lives; the volume boundaries coincide with the five cores and with rates of change; nothing is located by historical accident.

---

## 4. Final Recommendation

**Adopt B — the Radical structure — as the architecture, with A's deltas applied to the Whiteboard Edition as the teaching layer.** The apparent conflict dissolves because the four-volume split already separates the two jobs: *architecture volumes* should be organized by the science (B); the *Whiteboard Edition* is pedagogy, where narrative continuity with the review history is a feature, not debt. Concretely: the Whiteboard Edition receives Version A's deltas now (becoming v3, terminology-aligned with B so the two never diverge in vocabulary); Volumes 1–3 are drafted to B's outline in Generation-2 write windows, Constitution first (F0). Trade-offs stated honestly: B costs one full remapping of references and some re-review; A alone would preserve comfort while cementing a historically-accidental structure for fifteen years. Pay the one-time cost.

---

## 5. Required Self-Critique

**What assumptions might still be wrong?** (1) That XAUUSD H1 contains establishable phenomena at all at retail-visible granularity — Gen 1's four verdicts are weak evidence *against*; the phenomenon-first pipeline may mostly produce well-scoped absences. That is still knowledge, but the Owner should want it knowingly. (2) That mechanism claims are testable with our data: distinguishing "liquidity transfer" from "trend" may require order-flow data we've deferred. (3) That the universal lifecycle fits Measurements — a raw feed may need only calibration status, and forcing ten rungs on it would be ceremony.

**What is over-engineered?** Observation Space's twelve layers — I expect Gen-2 practice to use six or seven; layers 8 (Event Context) and 11 (Confidence Context) are candidates for folding into others. The radical rewrite keeps them only because deletion should follow evidence of disuse, which the dimension-deprecation process will supply within one generation.

**What is under-specified?** The placebo taxonomy for the three claim types (existence-claim nulls need a permutation/synthetic-recurrence design that Gen 1 never built — this is the largest genuinely new *scientific* work in Gen 2 and it must be sealed before the first phenomenon registration); the cost model's venue-sensitivity for anything below H1; power analysis conventions for equivalence (absence) designs; interface contracts between the five cores.

**What would I remove if implementation started tomorrow?** Everything in the Research and Autonomy Cores (they're Gen 3–4 by charter anyway); the Market Knowledge Graph as software (Gen 2's verdict count fits in a prose beliefs document — the Graph earns code only when relationships outgrow prose); Atlas tooling beyond appended catalog records.

**What should never be automated?** The six powers, restated as Constitution material: reserve designation and unlock; verdict authority; constitution and freeze amendments; α-budget ceilings; promotion and everything downstream; the findings tally. I add a seventh from this session: **the decision to end a generation** — the strategy review at each boundary is the Owner's, forever, because it is where values re-enter the loop.

**What evidence would change my own recommendations?** If the primitives session collapses the six phenomenon kinds into three, the taxonomy shrinks and I was over-elaborate. If Gen-2 scope labels go substantially unused in rulings, Observation Space loses layers. If two full waves of phenomenon-first research produce zero established phenomena on XAUUSD, the honest moves are instrument expansion (Q3) or granularity change — not more architecture. And if the Battery's existing null designs prove sufficient for existence claims without a new placebo family, the "largest new scientific work" above shrinks to a memo — a welcome failure of my own forecast.

> **Closing anchor:** *The clearest architecture is the one where the table of contents is the scientific method itself.*
