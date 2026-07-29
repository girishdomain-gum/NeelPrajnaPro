# REV — Architect Review of the DeepSeek Document Estate
*Reviewer: Fable (Architect) · Date: 2026-07-29 · Companion: REV-Full-Backup-Corpus (same date). Decisions marked ⚖ require an Owner ruling.*

**Documents reviewed:** NeelPrajna Constitution v1.0, Scientific Model v1.0, Platform Architecture v1.0, Research Architecture ("The Scientist in the Machine"), Team Structure & Documentation Review — all DeepSeek-authored — plus `NeelPrajna_QRF_Integration_Path.docx` (Volume IV), checked against `ROLES_COMMUNICATION_EXPRESSION.md`, `TEACHING_AND_KNOWLEDGE_TRANSFER_STANDARD-v5.md`, and `CORRECTIONS_LOG_2026-07-29.md`.

**Verdict in one sentence:** the DeepSeek estate is well-written and captures much of QRF's method faithfully, but it contains one already-corrected factual error reintroduced, one architectural design that violates the estate's own epistemic rules, and two irreconciled visions of the system — it must not be ratified as written; it should be rebuilt by the Architect around the Integration Path's grounding in the real Kernel.

---

## Findings (F-1 highest severity)

### F-1 — The corrected generation error is reintroduced ⚖
Research Architecture §2.3/§5.2 defines Generation 2 as "The Autonomous Scientist — system discovers concepts, humans review." `CORRECTIONS_LOG_2026-07-29.md` item 1 already corrected exactly this claim: the Owner-ratified `ROADMAP_GENERATIONS_2-4.md` places autonomous proposal in **Gen 3** (Gen 2: humans propose, machinery labels). The Constitution and Platform Architecture inherit the error via the QRF-brain "Pattern Learning / Pattern Evolution" boxes.
**Species:** claim contradicting the ratified record, post-correction.
**Disposition:** all generation language in the new estate must match the ratified roadmap. Non-negotiable before any freeze.

### F-2 — The "closed learning loop" violates the estate's own belief-gating rule ⚖
Platform Architecture Layer 5 ("Outcomes → Memory → Belief Updates"), the claim that "every trade refines the knowledge that produced it," and the Decision Process's "recent win rate" input jointly contradict §6.5 of the same document ("Belief updates from Verdicts only; beliefs never cite screener metrics as evidence"). Live trade outcomes are unsealed, multiplicity-uncorrected data; letting them update published beliefs — or letting a rolling "recent win rate" reach the runtime — is unregistered inference driving execution, and is NeelPrajna "becoming smarter by itself" through the back door.
**Proposed fix — the Knowledge Publication Boundary (new normative rule):**
1. Execution feedback enters the Performance Store as *observations* only.
2. Observations may motivate new sealed hypotheses through the normal ECF/Battery pipeline.
3. Only Battery-verdicted, sealed beliefs ever cross the Communication Contract.
4. No unsealed statistic (rolling win rate, recent performance, screener output) is ever published to the runtime.
This preserves the learning loop but routes every belief update through the judge.

### F-3 — Two irreconciled architectures ⚖
The Constitution/Platform docs describe an imagined QRF brain (Knowledge Graph, Confidence, Pattern Evolution) that the real Gen-1 Kernel does not have. The Integration Path describes the real one: NeelPrajna as the second concept family inside the proven Kernel (`RecordStore`, nine-step `battery.py`, `WindowLedger`, `TrialCountLedger`, IVF).
**Recommendation:** the Integration Path wins. It is grounded in code that exists, inherits ten sprints of adversarial drilling, and its H-07-only first sprint has a falsifiable acceptance criterion (real Battery vs. bespoke B1–B7, gate by gate). The organism metaphor stays as ASPIRATIONAL vision prose; the FROZEN architecture describes the real Kernel plus the `qrf/trading/concepts/neelprajna/` family.
**Steelman of the alternative** (a standalone NeelPrajna research brain): full independence from QRF's repo and freedom to evolve a knowledge graph without Kernel constraints. I recommend against it because it duplicates a drilled instrument with an undrilled one — the precise redundancy Volume IV's §2 table documents — and forfeits the shared Gate A/B roadmap.

### F-4 — The document plan walks into the document-production trap ⚖
Team Structure Phases 1–5 schedule six to nine sessions of consolidation (11 documents) before anything is built. Teaching Standard v5 §9's corollary names this failure mode exactly. The most valuable next artifact is the H-07 integration sprint, not a document.
**Recommendation — inverted plan:**
1. Ratify a minimal Level-1 core: Constitution (corrected) + one Architecture document (Integration-Path-based).
2. Run the H-07 sprint as a real ARCH instruction with IVF and Owner Go/No-Go.
3. Write the remaining estate documents *from* what the sprint teaches, at the finish line, not before.

### F-5 — Amendment procedure introduces voting ⚖
Constitution §6.1 requires "Owner + supermajority of voices" for constitutional changes. This quietly gives AI voices ballot power, contradicting "authority is decision-scoped, not rank-scoped" and the Owner's sole ratification authority. Replace with: Owner ratification + all voices' reviews recorded on the record (dissent preserved per the Dissent Charter), no vote.

### F-6 — Realtime claims overstate the instrument
"Continuous communication, shared heartbeat, everybody reacts on every tick" describes a tick-time service. The real Kernel is a batch scientific instrument; realtime knowledge push is at best a later-generation feature. Move these claims to ASPIRATIONAL status; the FROZEN contract should specify publication semantics (versioned belief releases), not tick-time streaming.

### F-7 — Role-definition drift from the ratified roles doc
- Chief Scientist: original doc specifies an *independent external session*; DeepSeek assigns Opus (same vendor as Architect). Shared blind spots concentrate. ChatGPT's Independent Reviewer seat partially mitigates and should be kept explicitly *for that reason*.
- The "Sonnet + Claude Code partnership" mostly re-describes what Claude Code already is (Claude Code runs on a Claude model); as written it blurs the fresh-session-per-task and DEVQ disciplines. Simplify to: Developer = Claude Code, fresh session per task, model choice an operational detail, all Developer shall/shall-nots unchanged.
- New seats (Independent Reviewer, Data & Research Analyst) are sound additions; both correctly relay-only. Add one line each to the ratified roles doc rather than maintaining a second parallel roles table (two-clock drift risk).

### F-8 — Principle duplication
Constitution Principle 13 restates Principle 11 nearly verbatim ("A FAIL that answers a question outranks a PASS that flatters one"). Merge into one principle covering both integrity-over-positives and tri-state informativeness (PASS/FAIL/INSUFFICIENT).

### F-9 — MML notation bug
Scientific Model §7.2: `lower wick L = min(O,C) - L` uses `L` for both the Low and the lower wick. Rename (e.g., `W_lo = min(O,C) − Low`). Also state the zero-range candle convention (R = 0 ⇒ descriptor undefined or reserved code) before any detector implements it.

### F-10 — Missing normative content the estate will need before a freeze
- Window/reserve policy for NeelPrajna data: which historical spans are TRAINING vs EXPLORATION vs VIRGIN, and the Owner's designation ceremony for them. (H-07's 324 trades have been *seen* — the sprint must declare their designation honestly.)
- α-budget for the NeelPrajna hypothesis family (18 founding hypotheses = 18 counted attempts at minimum; TrialCountLedger entries from day one).
- Cost-model reconciliation (QRF's $0.47/oz round-trip vs. NeelPrajna's 26-tick figure) as a named, bounded task with one authoritative `configs/venues.yaml` entry — flagged in Volume IV §4, must appear in the sprint scope.
- V&V plan for the new detector: planted-truth and clean-control cases for `neelprajna.liquidity_sweep` before it judges anything real (Principle: trust follows demonstration).

---

## What to retain from the DeepSeek work
- **Scientific Model** is the strongest document: ECF claim forms (E1–E3), the definition-trap rule, the three null families, the twelve-layer Observation Space, and the graduation ladder are faithful and well-taught. Carry forward nearly intact, with F-9 fixed.
- **Communication Contract** (six objects, two prohibitions) is correct; freeze after adding the Knowledge Publication Boundary (F-2) and versioned-release semantics (F-6).
- **Document status taxonomy** (FROZEN/BUILDING/DESIGNED/ASPIRATIONAL) is a genuinely useful addition — adopt it.
- **Dissent Charter rendering** (the four freedoms, the how-to-disagree format) is a good popularization of the ratified §4; keep as teaching-tier material, with the ratified doc remaining the normative source.

## Proposed decision list for the Owner ⚖
1. Rule on F-3: Integration-Path architecture as the frozen basis (my recommendation), or standalone brain.
2. Rule on F-4: inverted plan (minimal Level-1 + H-07 sprint first), or the 11-document consolidation first.
3. Ratify the Knowledge Publication Boundary (F-2) as a new constitutional rule.
4. Ratify role additions per F-7 as amendments to the existing roles doc.
5. Designate window status for the NeelPrajna historical data (F-10) — permanently-human power, so this is yours alone.

On the Owner's Go, the Architect will author the Fable-designed estate in this order: (1) Constitution v2 (corrected, merged principles, publication boundary), (2) Platform & Integration Architecture v2 (real-Kernel-based, one document), (3) the sealed H-07 integration sprint instruction. Everything else follows the sprint, per the finish-line rule.

*Anchor: the DeepSeek estate taught well but froze the wrong brain — ratify the real Kernel, publish only what the judge has signed, and let H-07 be the first proof.*
