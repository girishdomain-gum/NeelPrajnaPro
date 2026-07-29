# QRF — The Complete Architecture
## Generation 1 Foundations and the Generation 2 Vision, in one document
*Whiteboard Edition · written to the Teaching & Knowledge Transfer Standard v5*

Status: **DRAFT for Owner review** — produced by the Architect (Fable) in a no-write brainstorming session. Nothing binds until ratified. Sources: GENERATION_1_FINAL_REPORT.md · QRF_Gen2_Observational_Foundations_v1 · the Gen 2/3/4 Architecture Roadmap draft.

---

## How to read this document

You don't need all of it. Pick your row.

| **You are...** | **Read** | **You can skip on a first pass** |
|---|---|---|
| Deciding what to greenlight | Ch 1, Ch 4, Ch 16, Takeaways | The mechanics inside Ch 2, 5–11 |
| New to QRF entirely | Ch 1, Ch 2, Ch 3 | Everything after, until those land |
| Reviewing Generation 1's machinery | Ch 2 | Ch 5–15 |
| Designing Gen-2 foundations (vocabulary, coordinates) | Ch 5, Ch 6 | Ch 9–11 |
| Designing discovery / autonomy | Ch 8, Ch 9, Ch 16 | Ch 2's subsections |
| Deciding what belief attaches to | Ch 13 | Ch 6–11 |
| Checking what's built vs. proposed | Ch 15, Ch 16 | Everything else |

*One throughline for all sixteen chapters: never let a name — a concept, a "law," a subsystem, or a claim of "readiness" — carry more trust than the evidence behind it has actually earned.*

---

# PART I — GENERATION 1: THE SCIENTIFIC OPERATING SYSTEM

## Chapter 1. The one question QRF exists to answer

Start with a question that sounds too simple: **when a trading idea looks profitable in a backtest, how do you know you haven't fooled yourself?**

Why does that question matter more than any strategy? Because there are more ways to fool yourself than there are ways to be right. You can test a hundred variations and remember only the winner. You can let tomorrow's information leak into yesterday's signal. You can test on the same data that suggested the idea. You can define "success" after seeing the results. Each of these produces beautiful backtests of edges that do not exist — and none of them feels like cheating while you're doing it.

A simple picture: imagine a courtroom where the defendant's lawyer also gets to pick the jury, write the law, and grade the verdict. Every trial ends in acquittal, and every acquittal is worthless. Most trading research is that courtroom.

So before testing a single idea, Generation 1 built the honest courtroom first. The intuition: **separate the person who proposes from the machinery that judges, and make every step of the judging auditable by a stranger.** Only now the technical framing: QRF Generation 1 is not a trading system and not merely a backtester — it is a *scientific operating system*: an append-only, hash-chained ledger of every observation, claim, cost, and verdict; a judging pipeline whose every number is independently reproducible; and a governance loop in which no role can silently pay for its own mistakes.

Did it work? Ten sprints, 84 ledger records, four hypotheses judged, twenty-one integrity findings caught before harm — and **zero promotions**. That last number is the proudest line of the whole generation, and Chapter 2 explains why.

> **Anchor sentence:** *Generation 1's question was never "what works?" — it was "did we honestly count every opportunity to fool ourselves?"*

*Quick recap — before asking what works, QRF built machinery that makes self-deception countable; the deliverable is the honest courtroom, not any verdict it produced.*

---

## Chapter 2. The machinery, subsystem by subsystem

**How do you build a courtroom you can trust?** One safeguard at a time, each earning its place by catching a real mistake. Here is the machinery in the order it earned trust, with the confusion each piece exists to remove.

### 2.1 The governance loop — three roles that cannot cover for each other

**Why three roles instead of one smart researcher?** Because the failure modes are social, not just statistical. The **Owner** (human) holds values, budgets, and the untouchable decisions. The **Architect** designs rules and independently verifies. The **Developer** implements, in fresh sessions, inside worktrees. The Architect never writes developer code; the Developer never authors ADRs; the Owner alone declares write windows. When a role refuses work its rules forbid — and Generation 1 recorded exactly such refusals — that refusal is the system working, not failing.

### 2.2 The append-only ledger — history that cannot be quietly edited

Every observation, registration, cost, verdict, and correction is a record in a hash-chained journal (84 records at the Generation-1 freeze). Nothing is rewritten, ever; a correction is itself a new record. **Why so strict?** Because the easiest fraud in research is retroactive: adjusting yesterday's claim to fit today's result. A hash chain makes "when was this decided?" a mathematical fact instead of a memory.

### 2.3 VIRGIN reserves — unseen data, held by a human hand

Some stretches of history are designated *reserves*: never looked at, never touched, unlockable only by the Owner's typed phrase — never by any AI's judgment. **Why does looking matter?** Because market history barely grows — a few thousand new hourly bars a year — and once data has shaped an idea, it can never again independently test that idea. A companion **WindowLedger** tracks every burned window so no stretch of history is unknowingly used twice, and reservation follows *market time* (a bar's hours), not dataset labels.

### 2.4 The Observatory — detectors with knowability contracts

Detectors record market events under one contract: **nothing may be detected that could not have been known at its own bar.** No future information, ever, even by accident. This is where "observations before interpretation" is enforced in code: the detector records *what happened*; meaning is assigned later, under seal, or not at all.

### 2.5 Calibration & Screener — candidates are not claims

Parameter sweeps produce shortlists. A shortlist is a *candidate* — a suggestion of where to look — never evidence. **Why insist?** Because a sweep that tries 500 configurations has, by construction, manufactured its own winners; treating a screened winner as a validated edge is the garden of forking paths in one step. Every sweep is also *counted* (see 2.7).

### 2.6 The Evidence Battery — pre-registered judgment

The Battery judges sealed hypotheses under rules fixed **before** the data is examined: thresholds, methods, sample-size floors, anchored walk-forward splits, pessimistic fills. Verdicts are tri-state — PASS, FAIL, or **INSUFFICIENT** — and INSUFFICIENT is not a weak FAIL: when only 28 Mondays existed against a floor of 40, the floor refused to let 28 Mondays impersonate evidence.

### 2.7 Multiplicity pricing (ADR-011) — every attempt counts

**Here's the trap this closes.** Test twenty random ideas at 95% confidence and one will "pass" by luck alone. So QRF charges the scientific cost at *registration*, not at success: registering spends the attempt; sweeps are charged at birth, all their variations counted. Each concept *family* carries its running bill — after 1,004 counted trials, the smc.fvg family's effective bar tightened to α ≈ 5×10⁻⁵, and the family was deprioritized by its own pre-registered interpretation. The garden of forking paths is priced at the gate.

### 2.8 The Placebo engine — nulls matched to the claim

**The subtlest safeguard, so take it slowly.** Suppose Monday trades earn +5.00 each. Impressive? Wrong question. The right question: impressive *compared to what*? If the market drifted upward all year, trades at *random* times also earned money. So the null hypothesis must match the claim type: a **timing** claim is judged against random-timing placebos that inherit the market's drift by design. The bar is "beats random timing," never "beats zero." H-004's +5.00/trade died against exactly this bar (p = 0.108) — the profit was the trend, wearing a Monday costume.

### 2.9 Graduation — four gates that refuse before they write

A claim that survives the Battery still faces four sequential refuse-before-write gates before promotion. The record of a promotion existing is itself proof the gates held. In Generation 1, nothing ever reached them — honestly.

### 2.10 The Independent Observation Lens — a second witness

One data feed can be systematically wrong. So corroboration requires an *independently produced* second feed, with independence declared as a spectrum (broker / LP / venue) and never silently upgraded. The agreement threshold is sealed **before** computation. First lens: a second broker's feed, tier=broker, agreement 0.9544 against a pre-sealed 0.95.

### 2.11 The IVF — a verifier that must catch planted frauds first

The Architect-owned Independent Verification Framework re-implements every rule from the normative texts and re-derives every recorded number from raw CSVs — to 1e-9, bootstrap confidence intervals included. **And here's the part that makes it trustworthy:** before the IVF may judge the real ledger, it is drilled with deliberately planted frauds, with a clean control, and must catch them. A verifier that has never caught a planted fraud has never demonstrated it *can*.

> **Anchor sentence:** *A broken thermometer takes no temperatures — so QRF breaks its own thermometers on purpose, first, to prove they'd notice.*

### 2.12 HC — human eyes, because eyes see differently

A label-driven human-capture layer samples the record. Its standing proof of worth: it found an idealized-calendar error that **two machine layers had agreed on**. Machine recomputation, adversarial drills, and human eyes each see what the others cannot — the layers are useful precisely because they can disagree.

*Quick recap — eleven safeguards, one shape: propose and judge are separated, every attempt is priced, every number re-derives from raw data, and every verifier proves itself against planted frauds before judging anything real.*

### 2.13 The Twelve Design Principles (binding on all future generations)

The philosophy, sealed at the Owner's review — stated formally because these bind:

1. Observations before interpretation. 2. Registration before experimentation. 3. Every attempt counts. 4. Candidate discovery is not validation. 5. History is append-only. 6. Evidence must be reproducible, not merely archived. 7. Independence is a spectrum, declared and never upgraded. 8. Reserves are inviolable and human-held. 9. Verification is layered, and the layers must disagree to be useful. 10. Tripwires bind their authors. 11. Scientific integrity over positive findings. 12. Boundaries hold under convenience.

### 2.14 The scientific record, the tally, and the honest limitations

Four hypotheses judged on XAUUSD H1, 2024–2025 — all reproducible to the last digit:

| Hypothesis | Verdict | The lesson |
|---|---|---|
| H-001 FVG follow-through | FAIL | The flagship borrowed concept did not survive |
| H-002 intra-week FVG | FAIL (n=637, p=0.93) | Weekend exclusion does not rescue it — question answered |
| H-003 Monday drift | INSUFFICIENT (n=28<40) | The floor held against thin evidence |
| H-004 Monday drift v2 | FAIL (n=56, +5.00/trade, p=0.108) | Profitable ≠ better than random timing |

Findings tally: **Architect 17, Developer 4** — twenty-one integrity findings, every one caught before harm, the majority by the system's own tripwires firing on their own authors. Exploration Wave 2 screened 500 configs and shortlisted 39 — all long-side, one parameter neighborhood; the Owner's recorded read: *the trend in 39 costumes; candidates, not evidence.*

And the limitations, stated so Generation 2 inherits them honestly: one instrument, one timeframe, ~2 years; every negative conditioned on a trending-gold regime; a retail cost model (0.47/oz round trip); lens independence at broker tier only; belief records minimal; human coverage sampled, not exhaustive.

*Quick recap — Generation 1's record is four honest verdicts, zero promotions, twenty-one caught findings, and a limitations list written down on purpose; the machinery, not the verdicts, is the asset.*

---

# PART II — THE GAP GENERATION 2 MUST CLOSE

## Chapter 3. What Generation 1 never needed: a vocabulary

**Here's a question Generation 1 never had to answer.** Suppose two researchers each register a hypothesis about "liquidity sweeps." One means a sweep on the 5-minute chart in the London session; the other means a sweep on the 1-minute chart at any hour. Both call it "a sweep." One passes, one fails. Is that a discovery — sweeps work in London but not elsewhere — or two different experiments wearing the same name?

You cannot tell. Not because the Battery is weak — it's the most disciplined part of the project — but because the Battery judges *evidence*; it was never asked to judge whether two things with the same name are the same thing. Generation 1 never hit this gap for one reason: a human hand-picked and hand-named every hypothesis, one at a time, and quietly kept the distinctions in their head.

**Why does that stop working now?** Because Generation 2 asks whether some of that hand-picking can be assisted — patterns mined, queues prioritized by evidence gaps, a standing catalog consulted, and eventually a system that helps *propose* its next question. The moment anything is automated, "what counts as the same candidate" must be answered by software, consistently, at scale. Automation turns an implicit vocabulary into missing architecture.

> **Anchor sentence:** *A concept is not what you call it. A concept is what you can precisely say it is, built from what was actually measured, scoped to exactly where you looked.*

*Quick recap — Generation 1 needed an honest judge; Generation 2 additionally needs a shared, checkable vocabulary for what stands trial — because humans can keep definitions in their heads and machines cannot.*

## Chapter 4. The vision reframe — and the Architect's honest caution beside it

**Is Generation 2 just "more hypotheses on the frozen OS"?** The Foundations document answers no, and says so plainly:

> **Vision statement:** Generation 2 transforms QRF from a scientific hypothesis-validation framework into an autonomous scientific research system — capable of independently observing, discovering, hypothesizing, validating, learning, and expanding its own knowledge with minimal human supervision. Stated permanently: **Generation 2 is an Autonomous Scientific Research Platform. Trading is its first application domain, not its defining characteristic.**

The framing earns its keep by giving every future decision one test: *does this make QRF more capable of independent scientific research?* If yes, it's core platform; if no, it's a domain extension.

**Now the caution, which belongs in the same chapter as the vision so neither travels alone.** This vision describes roughly twenty-five subsystems. The document's own capability filter (Ch 12) finds only three genuine new capabilities among them; its own maturity table (Ch 15) marks the coordination layer *proposed, unbuilt, Critical*. Generation 1's deepest lesson is that trust follows demonstration — every subsystem was drilled and fraud-tested before it was believed. **Therefore this document adopts the vision as the destination and refuses it as the next step:** the build is split across Generations 2, 3, and 4 with evidence gates between them (Chapter 16). The human's role narrows one notch per generation — from writing hypotheses, to registering machine proposals, to setting missions and budgets — and never two notches at once.

> **Anchor sentence:** *The vision names the destination; the gates decide the speed.*

*Quick recap — Generation 2's ultimate identity is an autonomous research platform with trading as first domain; the same document that states the vision also stages it across three gated generations, because trust-before-demonstration is the one debt QRF refuses to take on.*

---

# PART III — THE SCIENTIFIC FOUNDATIONS (Generation 2, Track 2)

## Chapter 5. Primitives first — Measurement, Observation, Concept

**Before naming any categories, ask a harder question: how would we know we picked the right ones?** Not by pattern-matching to what sounds rigorous. Physics didn't begin with "the universe is made of Force and Energy"; it began with what an instrument can measure without any theory assumed — length, time — and built the grand concepts later, as combinations that behaved predictably.

The same distinction, made concrete. "Price moved from 3300 to 3305" — a number, then another number; nobody can dispute it. "That was a bullish move" — a judgment has been baked in. "That was a liquidity sweep" — a *label* carrying an implicit theory of why. Three different kinds of statement. Now the three layers:

```
   Measurement    (raw numbers off the tape — indisputable)
        ▼            price · time · volume · spread · tick count
   Observation    (a computed comparison — still no theory)
        ▼            higher-high · ATR percentile · gap size · duration
   Concept        (a label on a pattern of observations — theory enters HERE)
                     compression · sweep · trend · order block
```

**Watch what this does to "compression."** The instinct files it as a primitive State, sensed directly like temperature. But pin it down and compression turns out to be several Observations satisfying a joint condition — ATR percentile low AND range narrow AND sustained N bars. It is a *composition*, one full layer above where a first pass would place it.

```
   Weak foundation:    "This is a compression State."
                        → depends on a word meaning the same thing to everyone, forever.
   Strong foundation:  "ATR(14) pct < 20  AND  range < 0.4 × 20-day avg  AND  ≥ 6 bars"
                        → depends on nothing but arithmetic. "Compression" is its nickname.
```

Words drift; arithmetic doesn't. Human judgment isn't removed — it's *relocated* to one visible place: choosing which Observations to combine and where the threshold sits.

**The mandated first action of Generation 2:** one dedicated **primitives session**, before further architecture, running eleven candidate words — *Measurement · Observation · Event · State · Transition · Structure · Relationship · Hypothesis · Evidence · Verdict · Knowledge* — through four questions each: Is it primitive? Is it derivable from the others? Does it overlap another (is "Regime" just a long-duration "State"?)? Is anything missing? Get this wrong and every label built on top is silently half-wrong later.

> **Anchor sentences:** *A Concept is a name for a place where several numbers happen to agree.* — and — *Get the nouns right before you build any verbs on top of them.*

One naming note, settled the same way: "Ontology" overclaims ("this is what a market *is*"); QRF only needs "what can this system measure and compare?" The working name is **Observation Model**, provisionally.

*Quick recap — three layers (Measurement → Observation → Concept), theory entering only at the top; a dedicated primitives session settles the eleven-word vocabulary before anything else is built; compression is the cautionary example of a Concept masquerading as a primitive.*

## Chapter 6. The Observation Model and Observation Space — kind, and where

### 6.1 The Observation Model — what KIND of thing is each Concept?

A sweep happens at an instant; compression holds over a stretch. Nothing in Generation 1 records that difference. So every surviving Concept gets a category tag:

| Category | Meaning | Example | Built from |
|---|---|---|---|
| **Event** | Happens at one moment | Liquidity sweep | Observations crossing a threshold at a timestamp |
| **Structure** | A shape you can point to | Swing high, order block | Observations describing geometry |
| **State** | A condition over an interval | Compression | A joint condition, sustained |
| **Transition** | Movement between States/Events | Compression → Expansion | A sequence |
| **Regime** | Slow-moving backdrop | Risk-on/off | Possibly a long State — resolve in the primitives session |
| **Relationship** | A link across entities/timeframes | H1 compression vs M5 oscillation | A comparison of typed Concepts |

Cost: one field on a registration record. Discipline carried over: **mechanical rule first, friendly name after** — the name never smuggles in a claim the rule didn't earn.

### 6.2 Observation Space — a coordinate system, not metadata fields

**Two claims that are not the same claim:** "liquidity sweeps predict continuation" versus "…but only on M5, in London, in a trending regime, after compression." The second is smaller, more precise, and could be true while the first is false. Today, when a hypothesis fails, the ledger records FAIL — full stop — flattening exactly the nuance a later researcher needs. Medicine solved this by making trial *scope* mandatory on every result. Same fix here:

> **Observation Space** is the complete set of conditions under which a hypothesis is observed, generated, validated, and considered valid. A hypothesis is never universal — it is only ever true, or false, *inside a particular Observation Space*.

Twelve layers, from Domain down to Research Context:

| # | Layer | Answers | Examples |
|---|---|---|---|
| 1 | Domain | What kind of system? | Financial markets (today); medical, climate later |
| 2 | Instrument | Which object? | XAUUSD, EURUSD, NIFTY |
| 3 | Data Source | Which feed? | OHLC, tick, bid/ask, order flow |
| 4 | Temporal Space | When (period · session · timeframe · relative time) | 2024 · London · M5 · first hour |
| 5 | Market State | What condition? | Compression, expansion, range |
| 6 | Market Structure | What's present? | Swing high, liquidity pool, FVG |
| 7 | Statistical Context | Relative to its own history — **percentiles, not raw values** | ATR pct, volume pct |
| 8 | Event Context | Anything unusual now? | FOMC, NFP, holiday, gap open |
| 9 | Observation Window | What data produced this? | Previous 30 bars, rolling 5 days |
| 10 | Detector Context | Which code produced it? | SweepDetector_v4 |
| 11 | Confidence Context | How reliable is the data itself? | Quality, missing-data flags, noise |
| 12 | Research Context | How did this hypothesis come to exist? | Human · Discovery Engine · Atlas-browse · gap-driven |

Layer 12 is what tells a reader whether a claim is *exploratory* or *confirmatory* — the distinction that decides which evidence bar applies (Ch 13).

> **Anchor sentence:** *A FAIL without a scope teaches you almost nothing; a FAIL with a scope teaches you where not to look next.*

### 6.3 Observation Neighborhoods — disciplined generalization

A validated result at `{XAUUSD, M5, London, Compression}` has *neighbors* — points differing in exactly one coordinate: `{…, M1, …}`, `{…, NY, …}`, `{BTCUSD, …}`, `{…, Expansion}`. **Why is this more than a picture?** It turns "where next?" from an open grid-scan into a bounded, prioritizable step outward from validated ground — scientifically motivated (neighboring conditions are where a mechanism most plausibly still holds) and budget-respecting. This is the *one* pre-approved expansion pattern; each step is still priced.

### 6.4 The space must be able to grow — dimensions as knowledge, not schema

What happens when someone — human, machine, or research paper — proposes a dimension that doesn't exist yet (Dealer Gamma State, Liquidity Imbalance Persistence)? Ignoring it discards discoveries; hand-patching the schema forever is manual dependence. The resolution is a change of category:

> **Anchor sentence:** *If Observation Space lives in the architecture, every new dimension requires changing software. If it lives in the knowledge layer, the architecture stays stable while the science evolves.*

Every dimension gets a **lifecycle** — Idea → Candidate → Scientific Definition (built from Measurements/Observations) → Observation Rule → Calibration → Validation → Replication → Accepted — with one exceptionless rule: **origin never grants a shortcut.** Human, Discovery Engine, paper, external AI — identical pipeline. Dimensions split into **Core** (Instrument, Time, Window, Source — structural, stable) and **Scientific** (Compression, Liquidity State — versioned, evidence-gated, retirable). Each is a first-class *record*: name, definition, dependencies, status (Candidate/Experimental/Scientific/Core/Deprecated), evidence, version, origin. Old versions are never overwritten — every past experiment stays reproducible against the version it used. And growth has a symmetric shrink: a dimension that contributes nothing across thousands of experiments is deprecated through the same discipline, archived, historically intact.

> **Anchor sentence:** *Science progresses by removing poor abstractions as much as by introducing better ones.*

### 6.5 Four pillars, and the guardrail that never relaxes

```
   Measurement Space → Observation Space → Concept Space → Knowledge Space
   (what is measured)  (where you looked)   (what's inferred)  (what survived)
```

And the arithmetic that keeps everyone honest: 8 timeframes × 6 sessions × 6 states × 5 volatility bands × 5 structures = **7,200 cells before a single parameter varies** — worse across twelve layers. Under ADR-011 every cell searched is a counted trial. **Observation Space is mandatory labeling, never license to search.** Systematic search remains a separately priced, Owner-approved proposal; Neighborhoods are the only pre-approved path outward.

*Quick recap — every Concept gets a kind (six categories) and every hypothesis a twelve-layer address; the coordinate system grows and shrinks through an evidence-gated lifecycle where origin grants no shortcuts; and none of this richness relaxes multiplicity pricing by one trial.*

## Chapter 7. The Market Atlas — a catalog with a hidden price tag

**The natural next thought:** keep a running catalog of everything observed, so the next researcher starts from the map instead of zero. Astronomers do exactly this — and *looking at a star catalog doesn't use up the sky*; tomorrow the photons return.

**Markets are not the sky.** A few thousand new hourly bars arrive per year, and once a stretch of history has been looked at — even summarized — it can never again serve as untainted evidence for a later idea. That is the entire reason reserves exist.

> **Anchor sentence:** *A telescope doesn't spend the sky; an atlas spends the data.*

A rich browsable Atlas is, if careless, the garden of forking paths with a reading room attached: every idle browse quietly generates a candidate, and candidates are charged at conception. The Atlas survives only in one narrow shape:

| | **Narrow Atlas** (proposed) | **Wide Atlas** (not proposed) |
|---|---|---|
| Coverage | Burned / designated exploration windows only — **VIRGIN reserves never cataloged** | Any data including reserves |
| Content | Counts and distributions of typed, scoped Concepts — description only, **never rankings** | "Top cells by expansion" — a screener in a librarian's coat |
| Freeze | An application on existing machinery | Requires an explicitly signed amendment |
| Ideas drawn from it | Tagged `source = atlas-browse`, paying the machine-source discount | — |

*Quick recap — the Atlas is genuinely useful and genuinely dangerous for the same reason: browsing is looking; it survives by staying on spent data, staying descriptive, never ranking, and taxing everything drawn from it.*

---

# PART IV — DISCOVERY AND AUTONOMY (Generations 3–4 capability, specified now)

## Chapter 8. The Discovery Engine — who proposes the next question?

Today the research queue contains only what a human thought to ask. If a genuine repeatable pattern sits in the data that nobody has *named*, the current architecture cannot notice it — however good the Battery is at judging things once proposed. A self-learning system must eventually help propose.

The **Discovery Engine** mines for recurring patterns — and here the primitives layering pays off: it mines **Observations**, the arithmetic layer beneath named Concepts. Observations are objective comparisons, so a machine hunting recurring combinations of them can find *genuinely new* Concepts rather than re-finding whatever humans already named.

```
   Market Data → Measurements → Observations
        → Discovery Engine → candidate Concepts (categorized, scoped)
        → HUMAN REVIEW → Registration (source = machine, discounted)
        → Battery → Verdict
```

**What it must never become:** a judge. A found pattern is a *candidate*, never a *discovery* — same registration, same Battery, machine-source tag and exploration discount attached. And the certification bar, inherited from the IVF's own onboarding: before it is trusted with anything real, it must be run against **deliberately planted nonsense families, with a clean control, and reject them.** An engine that can't refuse noise isn't ready, however interesting its real candidates look.

> **Anchor sentence:** *A discovery engine's job is to generate suspects, never to convict them.*

## Chapter 9. The Autonomous Research Cycle — the Orchestrator and its twelve subordinates

**A Discovery Engine alone still waits to be asked.** An autonomous researcher doesn't. The pipeline bends into a loop that keeps running:

```
   Observe → Discover → Generate Hypotheses → Prioritize
      ▲                                          │
      └── Publish ← Update Beliefs ← Learn ← Validate
```

**Why can't existing subsystems just run this loop?** Because everything built so far is a *capability*; nothing decides *when* to use which one, *how much* budget each line of inquiry gets, or what happens when two capabilities disagree. That coordination role needs a name: the **Research Orchestrator** — where Generation 1's central subsystem *judges* (the Battery), Generation 4's central subsystem *coordinates*. The human's role shifts accordingly: from writing hypotheses, to defining **Mission · Constraints · Budgets · Ethics · Objectives** — and observation shifts from a one-time step to a continuous feed.

Coordination is several skills, each currently missing, hence twelve subordinates:

| Subsystem | The question nothing currently answers |
|---|---|
| Research Planner | Which inquiry first? (uncertainty, conflicts, unexplored regions, human requests) |
| Research Scheduler | When? (autonomous systems still need a calendar, incl. scheduled revalidation) |
| **Knowledge Gap Detector** | *What is missing?* — the practical mechanism behind the word "autonomous" |
| Experiment Designer | Question → hypothesis → scope → sample size → power → registration, end to end |
| Curiosity Engine | Exploration ⇄ exploitation, held in deliberate tension |
| Resource Manager | 1,000 CPU-hours: spent where, on purpose? |
| Research Memory | Rejected ideas, anomalies noticed, open questions — more than published results |
| Portfolio Manager | Hundreds of open inquiries, sorted by actionable status |
| Detector Registry | Every detector's version, precision/recall, bias, dependencies — as data |
| Self Evaluation | Which detectors underperform? Which Concepts are redundant? On a schedule |
| Scientific Communication | Daily discoveries, contradictions, confidence reports — designed, not an afterthought |
| Autonomous Bootstrapping | From a minimal mission to a running program, without pre-written hypotheses |

**The clause that keeps this chapter consistent with every other one:** none of these loosen anything. The Planner and Curiosity Engine operate inside Observation Neighborhoods, not grid scans; the Designer's registrations face the unchanged frozen Battery; the Resource Manager's budget is priced under ADR-011.

> **Anchor sentence:** *Autonomy is who decides what to test next — never a change in how rigorously it gets tested once decided.*

*Quick recap — the Orchestrator coordinates a continuous research loop through twelve subordinate subsystems while the human sets mission and budgets; every evidentiary guardrail from Generation 1 passes through unchanged.*

## Chapter 10. The knowledge layer — Concept lifecycle, Knowledge Graph, three subsystems

### 10.1 Concept Evolution — the lifecycle Concept Space still lacks

Observation Space dimensions got a full lifecycle (Ch 6.4). Concepts didn't — yet the Discovery Engine's output ("this Concept should exist") and the Gap Detector's findings ("these Concepts conflict / are redundant") need somewhere disciplined to land. The fix mirrors the dimension lifecycle exactly: **New Concept (any origin — no shortcuts) → Validation (unchanged Battery) → Ontology Update (does the category set itself need revising?) → Knowledge Update.**

> **Anchor sentence:** *A category system that can't learn from its own validated discoveries will eventually describe a system smaller than the one it's supposed to be describing.*

### 10.2 The Knowledge Graph — six questions a flat ledger cannot hold

"Compression" and "low volatility" are not independent list entries — one plausibly causes the other. A flat ledger stores both; it cannot store that they *relate*. A **Knowledge Graph** sits alongside the Ledger — Concepts and mechanisms as nodes, typed edges (causes / supports / contradicts) — and relationships are themselves evidence: two validated Concepts that contradict signal an over-broad scope or a hidden dimension. Six capabilities unlock:

1. **Negative Knowledge** — FAILs as a queryable repository, so nothing disproven gets silently re-proposed under the same scope.
2. **Contradiction Resolver** — flags conflicts, routes them to the Planner as priority gaps. *Flags; never re-judges.*
3. **Research Lineage** — Hypothesis → Concept → Observation → Measurement, queryable years later: "what is this claim actually built on?"
4. **Generalization Engine** — how far across Neighborhoods does a validated belief transfer, with what confidence per step?
5. **Knowledge Decay** — confidence decays absent fresh evidence; revalidation is scheduled, not hoped for.
6. **Reputation** — replication count, independence, history, absence of contradiction: standing *beyond* a single PASS, never overriding the verdict beneath it.

One discipline across all six: **knowledge about the Ledger, layered on top — never a second, competing judge.**

> **Anchor sentence:** *A ledger remembers what happened; a knowledge graph remembers how what happened relates to everything else that did.*

### 10.3 Three subsystems, not one architecture

Everything above sorts into three systems with different rates of change, different failure modes, different audiences:

```
   1. Scientific Research Engine      (mechanics of experimentation — changes RARELY; near the frozen core)
   2. Scientific Knowledge System     (what's been learned, how it relates and evolves — changes CONSTANTLY)
   3. Autonomous Research Orchestrator (who decides what's next, with what budget — changes OPERATIONALLY)

   Engine ──feeds──► Knowledge System ──read by──► Orchestrator ──drives──► Engine
```

Bundling them risks a budget tweak accidentally touching the Battery. The standing test for any new idea: *which of the three does it belong to, and does it respect the boundary?* An idea needing all three at once is mis-scoped — or is the Orchestrator's job by definition.

> **Anchor sentence:** *An engine that runs experiments, a library that remembers what they taught, and a planner that decides what to run next are three different jobs — even when one person is doing all three by hand today.*

*Quick recap — Concepts get the same lifecycle dimensions have; a graph beside the ledger holds relationships and unlocks six capabilities that describe but never re-judge; and the whole estate is three subsystems with different clocks, kept deliberately apart.*

## Chapter 11. Sharper instruments and borrowed code

### 11.1 Microstructure — when the data itself gets richer (deferred, data-gated)

MT5 provides candles, ticks, bid/ask — enough for structural Concepts, not enough to see the auction itself (footprint, volume-at-price, order-flow delta). The old EA-era architecture was wired to its feed; QRF isn't: **a detector doesn't care where its input came from, only that it's well-defined and calibrated against planted truth.** Richer feeds arrive as new Measurements → new Observations → same categorization, scoping, registration, Battery. Status: *deferred* until such data exists — a data-plane question, not a research question. One permanent caution: the visible order book is not the market's intentions — resting orders can be pulled without ever being real; that's a *meaning* problem no data access fixes.

> **Anchor sentence:** *The detector changes; the observatory does not.*

### 11.2 Open-source libraries — borrowed code is a candidate, not a citizen

"Already built" and "correct" are different claims. On record: a popular open-source smart-money library carries a look-ahead bias in its swing-point labeling — polished, widely used, and wrong in exactly the way Generation 1 exists to catch. Treatment: every external library is a **candidate implementation** — calibrated against planted truth, same bar as internal code, recorded in a trust catalog (library · purpose · role · status).

> **Anchor sentence:** *Popularity is not evidence; calibration is.*

*Quick recap — richer data extends what QRF can see without changing how it judges, and enters only when it exists; borrowed code earns citizenship through the same planted-truth calibration as everything home-grown.*

---

# PART V — EPISTEMOLOGY: WHAT TO BELIEVE, AND WHEN

## Chapter 12. The filter — which ideas are capability, and which are bookkeeping

For every idea in this document, one test decides where the engineering risk actually sits:

> **Does this let QRF ask a scientific question it literally could not ask before?**

| Idea | Verdict under the filter |
|---|---|
| Primitives / M-O-C layering (Ch 5) | Foundational discipline — not itself a capability |
| Observation Model categories (Ch 6.1) | Metadata |
| Observation Space, 12 layers (Ch 6.2) | Mostly metadata; the *evolving dimension registry* is one emerging capability ("does this newly proposed condition matter?") |
| Narrow Atlas (Ch 7) | Borderline — one small capability: "what has been seen across many windows at once" |
| **Discovery Engine** (Ch 8) | **Genuine new capability** — "what recurs that nobody has named?" is unaskable today |
| **Research Orchestrator + subordinates** (Ch 9) | **Genuine new capability** — "what should I research next, and why?" is a human's job today |
| **Microstructure** (Ch 11.1) | **Genuine new capability** — deferred, data-gated |
| OSS governance (Ch 11.2) | Process — existing calibration applied to borrowed code |

**Why keep this table in view:** most of the document is *cheap* precisely because it's bookkeeping — it changes how clearly asking gets recorded, not what can be asked. Three ideas are *expensive* for the opposite reason: they change what can be asked, or who asks — and that is exactly why they get the most caution and the latest gates.

## Chapter 13. Mechanisms, categories, themes, and the ladder to "principle"

### 13.1 Track belief on mechanisms, not names

When QRF keeps a prior on "Order Blocks," what is it a prior *about*? Names are moving targets: a school of thought rebrands, splits, drifts in what any follower means by it — while the market behavior underneath, if real, hasn't changed. So every registration carries two labels: the informal **name** (for humans) and the claimed **mechanism** (built from Observations, checkable — the thing that earns or loses trust):

| The name | The candidate mechanism |
|---|---|
| ICT | Liquidity Transfer — large participants displacing price around known reference points |
| Wyckoff | Inventory Redistribution — positions built or unwound gradually |
| Order Blocks | Institutional Absorption — a zone where resting size absorbed opposing flow |

Two differently-named families claiming the same mechanism should converge on the same evidence — itself a test of the mechanism framing. And one blunt corollary: a concept surviving decades of retail attention is evidence the *idea* was memorable — not that the mechanism is real.

> **Anchor sentences:** *Concepts evolve. Mechanisms persist.* — and — *Survivorship was memetic, not predictive.*

### 13.2 Five kinds of research, five evidence bars

```
 1 Validate existing theories      (does this named concept survive the Battery?)
 2 Build behavioural models        (how does this instrument behave, independent of any name?)
 3 Discover hidden structures      (Ch 8 — surface what nobody has named)
 4 Disprove weak theories          (a FAIL is the intended result, not wasted effort)
 5 Discover governing principles   (the most ambitious — see 13.4 before using that word)
```

Conflating them applies the wrong bar: exploratory work judged by confirmatory standards, or a confirmatory FAIL mourned as failure. One statistical warning binds Category 4: a FAIL is *silence* — "we could not show it works." Asserting **absence** ("X has no edge") requires a pre-sealed smallest-effect-of-interest and the sample size to bound the effect below it. *A FAIL is silence; proof of silence costs more.*

### 13.3 Four themes — a map for filing every future question

| Theme | Core question |
|---|---|
| **A — Autonomous Concept Discovery** | What is a concept, precisely, and can one emerge from data? |
| **B — Scientific Agency** | Who proposes the next question — and should that ever leave human hands? |
| **C — Mechanism Discovery** | What persists underneath a concept? Can competing mechanisms coexist while evidence accumulates? |
| **D — Meta-Science** | Can QRF catch flaws in its own reasoning, challenge its own priors? |

A theme is a promise about scope — it stops every new idea from re-litigating all four concerns at once. Theme D is deliberately **unbuilt**: a system needs a stable answer to "what is a concept" (A) and "what is a mechanism" (C) before it can meaningfully ask "am I biased about my own concepts and mechanisms."

### 13.4 The ladder to "principle" — no rung-skipping

One instrument, one timeframe, one dominant regime: any surviving claim has been tested in one narrow corner of everything a "law" must span. The honest progression:

```
   Evidence → Beliefs → Cross-market → Cross-regime → Maybe... → Principle
```

Every step down is a *different Observation Space* — a different instrument, a different regime — and a belief that hasn't left home hasn't earned the generality the word implies, regardless of how strong the bottom-rung evidence looks.

> **Anchor sentence:** *A principle is a belief that survived leaving home.*

*Quick recap — belief attaches to mechanisms, not brand names; five research categories carry five evidence bars, with absence claims costing extra; four themes file every future question; and nothing earns the word "principle" without surviving cross-market and cross-regime exile.*

## Chapter 14. The domain-independence test

**Forget trading. Delete every market-specific module tomorrow. Would the rest still function as a general-purpose scientific research system?** Run the test honestly:

| Component | Definition requires finance? |
|---|---|
| Evidence Battery · ADR-011 · Reserves · Ledger | No — statistics, and "don't reuse looked-at data" applies to any finite dataset |
| Measurement→Observation→Concept · Observation Model · Discovery Engine | No — domain-general; only the *specific* Measurements are financial |
| Observation Space | Mostly no — instrument/session are finance slots; "declare your scope" is universal |
| **The concept library itself** (ICT, sweeps, order blocks) + financial Measurements | **Yes — entirely** |

```
        ┌────────────────────────────────┐
        │  Domain plugin: "Trading"        │   concept families, financial Measurements
        └───────────────┬────────────────┘
                        ▼
        ┌────────────────────────────────┐
        │  Domain-independent core         │   M→O→C · Observation Model & Space ·
        │                                  │   Discovery · Battery · Reserves · Ledger
        └────────────────────────────────┘
```

Swap financial Measurements for medical or climate ones and the core doesn't change. **The practical value is not a pivot** — it's a standing test for accidental coupling: a variable named `price` inside the Battery is a boundary drawn in the wrong place, worth fixing whether or not QRF ever leaves trading.

> **Anchor sentence:** *A framework doesn't have to leave its domain to benefit from being able to.*

## Chapter 15. The honest maturity assessment

Enthusiasm for a well-argued idea is not evidence the idea is implemented. Deliberately the least aspirational chapter:

**Where QRF is genuinely distinctive** — it validates entire scientific objects (Concept + scope + lineage), evolves knowledge rather than retraining models, hunts mechanisms rather than features, keeps scientific memory rather than results, and treats its own vocabulary as evidence-gated. **Where existing systems are genuinely ahead, stated without hedging** — scalability, parallel execution, orchestration tooling, dataset management, workflow automation, literature integration, benchmarking, reproducibility tooling, deployment. Every one an *engineering* gap, not a conceptual one — solvable in a way conceptual confusion isn't. Conflating "the philosophy is sound" with "the system is ready" is the readiness version of calling something a law too soon.

| Capability | Status | Priority |
|---|---|---|
| Scientific Foundations · Observation Model (Ch 5–6.1) | Stable | — |
| Observation Space, static core (Ch 6.2) | Strong | — |
| Dynamic dimension registry (Ch 6.4) | Novel, unproven at scale | Validate early |
| Gen-1 Battery | Strong, frozen | — |
| Experiment layer / Designer | Major gap — proposed, unbuilt | **Critical** |
| Research Planning · Portfolio | Major gap — proposed, unbuilt | **Critical / High** |
| Knowledge Graph · Concept lifecycle | Proposed, unbuilt | High |
| Scientific Memory | Needs formalizing beyond a flat Ledger | Medium |
| Resource Management | Missing | High |
| Meta-Science / Self-Evaluation | Missing — deferred by design (Theme D) | Deferred |
| General engineering readiness | Behind mature open-source alternatives | Ongoing |

> **Anchor sentence:** *A strong foundation and a long list of unbuilt rooms are not a finished building — but they are, honestly, a very good reason to keep building on this specific foundation rather than a different one.*

*Quick recap — QRF leads on validation philosophy and knowledge evolution, trails on engineering infrastructure, and carries a stable foundation under a long list of proposed-but-unbuilt superstructure; the honest next work is the surrounding scientific infrastructure, not more trading concepts.*

---

# PART VI — THE BUILD SEQUENCE

## Chapter 16. Three gated generations — the Architect's binding synthesis

**Everything in Parts III–V is accepted. None of it is built at once.** The rule, applied three times (formal register, because this binds on ratification):

> **No layer of autonomy is built until the layer below it has produced scientific results that prove the need — and every new piece of machinery earns trust the way Generation 1's did: drilled, planted-fraud-tested, clean control, before it touches the real ledger.**

```
 GEN 2  KNOWLEDGE + FOUNDATIONS          humans propose · machinery labels
 ────────────────────────────────────────────────────────────────────────
 Track 1 (primary — defines "complete"):
    N families → decisive verdict / powered-absence verdict / priced
    deprioritization; every registration carries build + kind + scope +
    source + mechanism; output = auditable, regime-conditioned,
    α-annotated beliefs document (prose, append-only)
 Track 2 (secondary — must NEVER delay Track 1):
    F1 primitives session → F2 decomposition of existing concepts →
    F3 category tags → F4 Observation Space schema + dimension records →
    F5 sealed state vocabulary (detectors) → F6 Narrow Atlas →
    F7 OSS trust catalog + detector registry
 Explicitly NOT built: Discovery Engine · Designer · Orchestrator &
    subordinates · Knowledge Graph · Bayesian machinery · continuous
    observation · microstructure ingestion
           │
           ▼  GATE A: Q1 criterion met · ≥3 recorded instances of humans
              hand-performing work a Gen-3 subsystem would mechanize ·
              foundations used without schema churn
           │
 GEN 3  SUPERVISED DISCOVERY             machines propose · humans register
 ────────────────────────────────────────────────────────────────────────
    Discovery Engine (planted-nonsense certified, clean control) ·
    Experiment Designer · Gap & Contradiction REPORTS first, subsystems
    only if reports prove insufficient · Knowledge Graph (once there are
    enough verdicts to relate) · Bayesian beliefs ADR candidate
           │
           ▼  GATE B: Engine certified with recorded hit-rate over a full
              wave · Designer track record, zero design-caused findings ·
              graph populated and correctly firing · envelope doctrine
              drilled on a shadow run
           │
 GEN 4  BOUNDED AUTONOMY                 machines propose AND schedule
 ────────────────────────────────────────────────────────────────────────
    Orchestrator + twelve subordinates, running inside SEALED ENVELOPES:
    Owner pre-ratifies α-budget, family list, Neighborhood boundary, and
    time window; the system spends down inside them and halts at the edge
```

**Permanently human — outside every envelope, in every generation** (unamendable except by the Owner's typed hand): (1) VIRGIN reserve designation and unlock; (2) verdict authority — no layer overrides the Battery; (3) freeze and charter amendments — no machinery modifies its own constitution; (4) α-budget ceilings — envelopes renew downward from the Owner, never upward from the system; (5) promotion and everything downstream of it; (6) the findings tally — kept by humans, about everyone, including the machines.

**The Generation-2 freeze amendment required (narrow, explicit):** items F1–F7 are ruled applications and records on frozen machinery — mandatory registration metadata; dimension records with a human-run lifecycle; the Narrow Atlas (non-VIRGIN, descriptive, unranked); trust-catalog and registry records; sealed state detectors. Anything that proposes, schedules, prioritizes, or searches remains frozen pending Gate A.

**And one sequencing rule with teeth:** if any sprint's Go/No-Go shows foundations built but no progress toward verdicts, that is a recorded No-Go finding against the Architect. Framework serves knowledge — the moment that inverts, the tally says so.

> **Anchor sentence:** *The vision names the destination; the gates decide the speed — and trust follows demonstration, for hypotheses, for subsystems, and for the scientist we are building.*

---

## Key Takeaways

- **Generation 1 built the honest courtroom** — append-only hash-chained ledger, human-held VIRGIN reserves, knowability-contracted detectors, a pre-registered Battery with tri-state verdicts, ADR-011 multiplicity pricing, claim-matched placebos, four graduation gates, an independence-declared lens, a fraud-drilled IVF, human capture, and twelve sealed Design Principles. Its record: 4 verdicts, 0 promotions, 21 findings caught — and zero promotions honestly refused is a result, not an absence.
- **Generation 2's gap is vocabulary:** automation makes "what counts as the same candidate" a software question. The answer is layered — Measurement → Observation → Concept — settled in a primitives session before anything is built on it.
- **Every Concept gets a kind** (Event / Structure / State / Transition / Regime / Relationship) **and every hypothesis a twelve-layer address** (Observation Space), which may grow and shrink only through an evidence-gated lifecycle where origin grants no shortcuts — and which is labeling, never license to search.
- **The Narrow Atlas** survives its own price tag by staying on burned data, staying descriptive, never ranking, and taxing every idea drawn from it. *A telescope doesn't spend the sky; an atlas spends the data.*
- **Three genuine new capabilities** — Discovery Engine, Research Orchestrator, microstructure — carry the real risk, and therefore the latest gates; everything else is bookkeeping that makes the asking clearer.
- **Belief attaches to mechanisms, not names** (*concepts evolve, mechanisms persist; survivorship was memetic, not predictive*); five research categories carry five evidence bars; absence claims require proof of silence; and nothing earns the word "principle" without surviving cross-market and cross-regime exile.
- **The domain-independence test** shows the trustworthy core was never about markets — a standing check for accidental coupling, not a pivot.
- **The honest maturity table** keeps "Stable" and "Critical/Missing" in one view: strong foundation, long list of unbuilt rooms, and the next work is scientific infrastructure, not more trading concepts.
- **The build is three gated generations** — Knowledge + Foundations, Supervised Discovery, Bounded Autonomy — with six permanently-human powers outside every autonomy envelope, one narrow signed freeze amendment for Gen 2, and one rule ruling them all: **trust follows demonstration.**

*— End of document. Next artifact: the Owner's rulings (N; beliefs-document form; the gated-split yes/no), then Q5, and only then ARCH-011 in a declared write window.*
