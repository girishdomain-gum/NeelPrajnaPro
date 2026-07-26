# QRF Architecture Roadmap — Generations 2, 3, 4
*The Architect's restructuring of "Observational Foundations v1" into a gated, evidence-first build sequence*

Status: **DRAFT — Architect (Fable) proposal for Owner review.**
Produced in a Generation-2 brainstorming session with **no write window**. Nothing here binds.
On ratification by the Owner, the Generation-2 portion becomes the substance of ARCH-011; the Generation-3/4 portions remain recorded intent, re-ratified at their own boundaries.
Companion documents: GENERATION_1_FINAL_REPORT.md · GEN2_PLANNING.md · QRF_Gen2_Observational_Foundations_v1
Historical note at commit time (2026-07-27): later sessions superseded parts of this document — Q5's lifecycle ruling replaced §6.3 item 5's placeholder, the Q6 cadence answer lives in GEN2_EXECUTION_ROADMAP, and "Concept" terminology was later renamed "Phenomenon" (see ADR R-002). Preserved as the original gating decision record.

---

## How to read this document

| You want... | Read |
|---|---|
| The one-page decision | §1 and §2 |
| What Generation 2 actually builds, in order | §3 |
| What is deliberately deferred, and the gates for un-deferring it | §4, §5 |
| The governance changes that must be signed explicitly | §6 |
| The risks I am carrying and the ones only you can carry | §7 |
| What I refuse to charter now, and why | §8 |

---

## 1. The one decision underneath this roadmap

The Observational Foundations document describes a true long-term vision: QRF as an autonomous scientific research platform. This roadmap accepts that vision as the **destination** and rejects it as the **next step**. The whole roadmap is one rule applied three times:

> **No layer of autonomy is built until the layer below it has produced scientific results that prove the need — and every new piece of machinery earns trust the way Generation 1's did: drilled, planted-fraud-tested, clean control, before it touches the real ledger.**

Generation 1's own history is the argument. The Battery was not trusted until the IVF re-derived it. The IVF was not trusted until it caught planted frauds. The lens was not trusted until its agreement threshold was sealed before computation. Twenty-one findings were caught because trust always followed demonstration. The Foundations document proposes roughly twenty-five subsystems; its own Part 9 filter concedes only three are genuine new capabilities and its own Part 16 marks the coordination layer *proposed, unbuilt, Critical*. Chartering all of it at once would grant trust before demonstration at a scale Generation 1 never permitted for a single subsystem.

**Therefore: the vision splits across three generations, with evidence gates between them.**

```
GEN 2  Knowledge + Foundations        humans propose, machinery labels
   │   GATE A: N verdicts + beliefs document + recorded pain points
   ▼
GEN 3  Supervised Discovery            machines propose, humans register
   │   GATE B: Discovery Engine certified + designer track record + graph populated
   ▼
GEN 4  Bounded Autonomy                machines propose AND schedule, inside sealed envelopes
```

The human's role narrows one notch per generation — never two.

---

## 2. What each generation is, in one paragraph each

**Generation 2 — "Knowledge, on labeled foundations."** Primary product: verdicts and a beliefs document (the ratified Q1 criterion, unchanged by the Foundations doc). Secondary product: the metadata layer — primitives vocabulary, Measurement→Observation→Concept decomposition, Observation Model categories, Observation Space scope labels, mechanism-tagged registration, narrow Atlas, OSS trust catalog, detector registry records. Nearly all of this is bookkeeping on frozen machinery (the Foundations doc's own Part 9 verdict), so the freeze survives with one signed, narrow amendment (§6). The binding constraint: **foundations work must never delay verdict production** — framework serves knowledge, never the reverse.

**Generation 3 — "Supervised discovery."** Built only after Gate A. The Discovery Engine (mining Observations, certified against planted nonsense with a clean control before touching real data), the Experiment Designer (power analysis, n-floors, placebo selection — mechanizing what the Architect does by hand), the Knowledge Gap report and Contradiction flagging (as scheduled *reports* first, subsystems only if reports prove insufficient), and the Knowledge Graph (only meaningful once Gen 2 has produced enough verdicts to relate). Every machine-proposed candidate still crosses a human hand at registration. Gen 3 is a real freeze amendment, ratified at its own boundary with Gen-2 evidence in hand.

**Generation 4 — "Bounded autonomy."** Built only after Gate B. The Research Orchestrator and its subordinates, running the Observe→Discover→Generate→Prioritize→Validate→Learn cycle **inside sealed envelopes**: the Owner pre-ratifies an α-budget, a family list, an Observation Neighborhood boundary, and a wall-clock window; the Orchestrator spends inside them and halts at the edge. Certain acts are permanently outside any envelope (§6.3). Gen 4 is where "Autonomous Scientific Research Platform" becomes an honest description rather than an aspiration.

---

## 3. Generation 2 in detail — two tracks, one priority

### Track 1 — Knowledge (primary; this is what "complete" means)

Unchanged from the Q1 discussion, now enriched by the Foundations doc's best ideas:

1. **N concept families** carried to decisive verdict, powered-absence verdict, or priced deprioritization. (N to be fixed by the Owner; Architect's recommendation: 4–6.)
2. Every registration carries: **build** (its Measurement→Observation composition), **kind** (Observation Model category), **scope** (Observation Space coordinates), **source** (human / behavioural / machine / atlas-browse), and **mechanism** (Part-11 style: the claimed market behavior, not the brand name).
3. Absence claims ("X has no edge") use a **pre-sealed smallest-effect-of-interest and powered equivalence design** — a FAIL is silence; Category-4 claims require proof of silence.
4. Output: the **auditable beliefs document** — append-only prose stances per family and per mechanism, regime-conditioned, α-annotated. Prose in Gen 2; Bayesian machinery is a Gen-3 candidate at the earliest, and only if verdict volume demands arithmetic.

### Track 2 — Foundations (secondary; metadata only; must not delay Track 1)

In build order, each with its freeze status:

| # | Item | What it is | Freeze impact |
|---|---|---|---|
| F1 | **Primitives session** | One dedicated session: the eleven candidate words through the four questions (primitive? derivable? overlapping? missing?). Output: settled vocabulary, sealed as a record. | None — a document |
| F2 | **Decomposition pass** | Every existing Gen-1 concept decomposed into Measurements → Observations → Concept; discrepancies recorded. | None — analysis on existing detectors |
| F3 | **Observation Model tags** | Category field (Event/Structure/State/Transition/Regime/Relationship) on registration records. | None — one field |
| F4 | **Observation Space schema** | Scope coordinates mandatory on every registration. Core dimensions fixed; Scientific dimensions exist as **versioned, append-only records** with the lifecycle (candidate → validated → accepted → deprecated). The lifecycle is a *procedure run by humans on records*, not an engine. | Metadata + procedure — inside the amendment (§6.1) |
| F5 | **State vocabulary** | 4–8 market states defined as sealed mechanical rules from Observations; evocative names attached only after the rule is sealed. States are detectors — exactly what the handover permits. | None — detectors are permitted arrivals |
| F6 | **Narrow Atlas** | Append-only catalog over burned/exploration windows only; descriptive, never ranked; VIRGIN reserves never cataloged; atlas-browse is a recorded, discounted source. | Inside the amendment (§6.1) |
| F7 | **OSS trust catalog + detector registry** | External libraries as candidates calibrated against planted truth; per-detector records (version, precision/recall on planted truth, dependencies). Records, not a subsystem. | None — records |

**The sequencing rule, binding:** F1–F3 complete before the first Gen-2 registration (they define what a registration *is*). F4–F7 proceed in parallel with Track 1 and yield to it. If at any Go/No-Go the sprint produced foundations but no progress toward verdicts, that is a **No-Go finding against the Architect** — recorded in the tally.

### What Gen 2 explicitly does NOT build
Discovery Engine · Experiment Designer · Orchestrator and all twelve subordinates · Knowledge Graph · Curiosity Engine · Resource Manager · microstructure ingestion · any Bayesian machinery · any continuous/scheduled observation process. All deferred to §4/§5 gates. Proposals to pull any of them forward must arrive as a written gate-waiver request to the Owner, never as drift.

---

## 4. Gate A — the door from Generation 2 to Generation 3

Generation 3 may be chartered only when **all** of the following are on the record:

1. **The Q1 criterion is met:** N families at verdict/deprioritization, beliefs document standing, IVF green on all of it.
2. **The pain is documented, not assumed:** at least three recorded instances where a human performed, by hand, exactly the work a Gen-3 subsystem would mechanize (e.g., the Architect hand-computing power analyses that an Experiment Designer would automate; a missed contradiction a graph would have surfaced). Automation is justified by demonstrated cost, in QRF's own ledger — not by architecture documents, including this one.
3. **The foundations held:** scope labels, mechanism tags, and dimension records were actually used across Gen 2 without schema churn. If the vocabulary needed constant repair while humans used it, it is not ready to be load-bearing under machines.

## 5. Gate B — the door from Generation 3 to Generation 4

1. **Discovery Engine certified:** rejected planted-nonsense families across repeated drills with clean controls; its real candidates carried a recorded hit-rate through registration and Battery over at least one full wave.
2. **Experiment Designer track record:** designs it produced were registered, judged, and IVF-verified with zero design-caused findings over a full wave.
3. **Knowledge layer populated:** enough verdicts that gap reports and contradiction flags have fired on real content at least once, correctly.
4. **Envelope doctrine drafted and drilled:** the sealed-envelope mechanism (§6.3) tested on a shadow run — Orchestrator proposing against a frozen copy, humans auditing every proposal — before it ever touches live registration.

---

## 6. Governance — what must be signed, and what may never be automated

### 6.1 The Generation-2 freeze amendment (narrow; requires the Owner's explicit ratified record)
> *Amendment to the Gen-1 freeze, proposed:* "The freeze on framework subsystems stands. The following are ruled to be applications and records on frozen machinery, not subsystems, and are permitted in Generation 2: (i) mandatory registration metadata — build, kind, scope, source, mechanism; (ii) Observation Space dimension records with a human-run lifecycle procedure; (iii) the Narrow Atlas as an append-only catalog over non-VIRGIN windows, descriptive and unranked; (iv) trust-catalog and detector-registry records; (v) sealed mechanical state definitions as detectors. Anything beyond (i)–(v) — in particular any engine that proposes, schedules, prioritizes, or searches — remains frozen pending the Gate A ratification."

### 6.2 The α doctrine for the new sources (restated so it cannot drift)
Registration spends the attempt (ADR-011, unchanged). Atlas-browse and machine-sourced candidates carry their source tag and exploration discount. The Observation Space is a labeling system; systematic search of it is a separately priced, Owner-approved proposal, with Observation Neighborhoods as the only pre-approved expansion pattern — and even neighborhoods are priced per step.

### 6.3 Permanently human, in every generation, including Generation 4
The following are **never** inside any autonomy envelope, and no future ARCH may move them without amending this section by the Owner's typed hand:
1. **VIRGIN reserve designation and unlock** — Owner's typed phrase only (Gen-1 Principle 8, unchanged and unamendable by the Architect).
2. **Verdict authority** — the Battery judges; no orchestrating layer overrides, re-weights, or re-litigates a verdict (the Foundations doc agrees; here it becomes binding).
3. **Freeze and charter amendments** — no generation's machinery may modify its own constitution.
4. **α-budget ceilings** — envelopes are set and renewed by the Owner; the Orchestrator may spend down, never up.
5. **Promotion and anything downstream of it** (per the Owner's Q5 answer, when given).
6. **The findings tally** — kept by humans, about everyone, including the machines.

### 6.4 Naming
The Foundations document's Part 1.5 mission ("Autonomous Scientific Research Platform; trading is the first domain") is adopted as the **destination statement** in the Gen-2 charter's preamble — explicitly labeled as describing Generation 4, so no reader mistakes the destination for the current claim. Part 15's domain-independence test is adopted immediately as a standing design check (it costs nothing and catches coupling).

---

## 7. Risks, honestly

**Risks this roadmap accepts:** Gen 2 may feel slow — verdicts on 4–6 families while grander machinery waits. A competitor-of-ideas reading the Foundations doc would build the exciting parts first; we are choosing not to, on Gen 1's evidence that trust-before-demonstration is how systems rot. Machine discovery arrives a generation later than the vision wants; the cost is real and chosen.

**Risks this roadmap reduces:** an unfalsifiable Gen 2 ("we built infrastructure" cannot fail, and therefore cannot succeed); autonomous α-spending before envelope doctrine exists; a Knowledge Graph of near-empty nodes; vocabulary churn beneath automated consumers; the freeze dying by relabeling rather than by decision.

**The risk only the Owner can carry:** this roadmap assumes the destination is genuinely wanted across three generations. If the honest ambition is "autonomous researcher within months," this roadmap is the wrong document — and the Architect's advice would then be to say so plainly and accept, with open eyes, the trust-before-demonstration debt that entails. The values choice is yours; my recommendation is on the record.

## 8. What I decline to charter now (the refusals, recorded)

Per Gen-1 Principle 12 — boundaries hold under convenience — I decline to draft, in Gen 2: any Orchestrator component, any continuous observation daemon, any curiosity/exploration engine, any resource manager, any Bayesian belief engine, and any Wide Atlas. Not because they are bad ideas — most are good — but because each would be machinery trusted before demonstration, and the one thing Generation 1 proved beyond argument is that the other order works.

---

## 9. Immediate next actions (gated on the Owner)

1. Owner rules on this roadmap's central decision: **gated three-generation split — yes or no.**
2. Owner supplies the two outstanding Q1 values: **N** (recommendation: 4–6) and beliefs-document form (recommendation: prose).
3. We resume the charter sequence at **Q5** (promotion appetite), then Q2 (first families — now with mechanism AND category-per-Part-13 stated per family), Q3 (instruments/2026 data — noting the Atlas raises the value of fresh data), Q4 (regime doctrine), Q6 (cadence — noting Track-2 foundations argue for Gen 2 running *slower* than Gen 1's two-day rhythm).
4. On ratification of Q1–Q6 + this roadmap's Gen-2 portion + the §6.1 amendment: ARCH-011 is drafted in a declared write window, and the first Gen-2 Developer session boots with the primitives session (F1) as T0.

---

*Anchor sentence for the whole roadmap: **trust follows demonstration — for hypotheses, for subsystems, and for the scientist we are building.***
