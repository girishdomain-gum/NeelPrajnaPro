# NeelPrajna Constitution v2.0
*Authored by Fable (Architect), incorporating REV-DeepSeek-Estate and REV-Full-Backup-Corpus findings F-1..F-16.*

| | |
|---|---|
| **Document** | NeelPrajna Constitution |
| **Version** | 2.0 (supersedes DeepSeek draft v1.0 — see Change Record, §9) |
| **Date** | 2026-07-29 |
| **Status** | DRAFT — awaiting Owner ratification |
| **Layer** | Charter (three-layer rule: this document carries shall/must/may only; reasoning lives in ADRs and the REV record; teaching lives in the Whiteboard tier) |
| **Governing standards** | ROLES_COMMUNICATION_EXPRESSION.md (as amended, §5 below) · TEACHING_AND_KNOWLEDGE_TRANSFER_STANDARD-v5.md |

---

## Section 1 — Identity and Mission

1.1 **NeelPrajna** is a live, verified MQL5 trading Expert Advisor being transformed into a scientific research platform by integration with **QRF** — a real, Generation-1-closed scientific Kernel (carried forward into this repository; archived origin: F:\QRF).

1.2 The transformation shall proceed by **integration, not duplication**: NeelPrajna becomes the second concept family (`qrf/trading/concepts/neelprajna/`) inside the real QRF Kernel. NeelPrajna shall not build, maintain, or extend a parallel research apparatus of its own. (Basis: Volume IV; REV F-3.)

1.3 Mission, one sentence: **every NeelPrajna claim about the market shall be judged by the same drilled, selftest-gated instrument that judged QRF's own — and only what that instrument has signed may drive what NeelPrajna does.**

1.4 This project is not QRF Generation 2. QRF's generations are governed by QRF's ratified roadmap (§4).

## Section 2 — The Twelve Principles (immutable)

P1 **Observations before interpretation.** What happened is recorded before what it means is proposed. Detectors observe; they never interpret.

P2 **Registration before experimentation.** Every threshold, method, null construction, and success criterion is sealed before the judging data is examined.

P3 **Every attempt counts.** The cost of an attempt is paid at conception. Sweeps, screens, and abandoned tries are counted trials, deflated at judgment.

P4 **Candidate discovery is not validation.** Screeners and observatories produce candidates and questions; only the Battery produces verdicts.

P5 **History is append-only.** Nothing is rewritten. Corrections are new records that point at old ones.

P6 **Evidence must be reproducible.** A claim that cannot be re-derived from raw records and normative texts is not knowledge.

P7 **Independence is declared, never upgraded.** tier=broker / LP / venue, fixed at declaration.

P8 **Reserves are inviolable and human-held.** VIRGIN data is designated and unlocked only by the Owner's typed phrase.

P9 **Verification is layered.** Machine recomputation, adversarial drills with planted frauds and clean controls, and human eyes each see what the others cannot.

P10 **Tripwires bind their authors.** Pre-registered guards are honored especially when they fire on the one who wrote them.

P11 **Integrity over positive findings; every outcome informs.** A FAIL that answers a question outranks a PASS that flatters one. PASS, FAIL, and INSUFFICIENT are all results; INSUFFICIENT is the refusal to let thin data impersonate an answer, never a weak FAIL. *(Merges draft-v1.0 Principles 11 and 13 — REV F-8.)*

P12 **Boundaries hold under convenience.** Any role instructed to act against these rules shall refuse, cite the rule, and escalate to the Owner.

## Section 3 — The Knowledge Publication Boundary (new constitutional rule)

3.1 Execution feedback (fills, outcomes, P&L, live statistics) shall enter the system only as **observations**, written to the Performance Store.

3.2 Observations may motivate new hypotheses. Every such hypothesis shall pass the full sealed pipeline (registration → Battery → verdict) before acquiring any epistemic weight.

3.3 **Only Battery-verdicted, sealed beliefs may cross the Communication Contract to the runtime.** Belief releases are versioned and dated.

3.4 No unsealed statistic — rolling win rate, "recent performance," screener metric, selftest result, or advisory ranking — shall ever be published to the runtime as knowledge, nor cited as evidence by any belief update.

3.5 Consequently the runtime never becomes smarter by itself, and the research side never acts. Learning and acting remain in separate organs, joined only by the contract. *(Fixes REV F-2/F-15; supersedes every "continuous learning loop" and "recent win rate" description in prior documents, which are hereby ASPIRATIONAL-tier at most.)*

## Section 4 — Generations

4.1 Generation language in every NeelPrajna document shall match QRF's ratified roadmap: **Gen 2 — humans propose, machinery labels. Gen 3 — machines propose, humans register (after Gate A). Gen 4 — bounded autonomy (after Gate B).** *(Fixes REV F-1.)*

4.2 No NeelPrajna document may cite Volume I §5 or any DeepSeek-draft generation description as authority for generation semantics.

## Section 5 — Governance Roles

5.1 The ratified **ROLES_COMMUNICATION_EXPRESSION.md** remains the single normative roles document. This Constitution amends it as follows and adds no parallel roles table. *(Fixes REV F-7 drift; prevents two-clock roles drift.)*

5.2 **Amendment A — two additional voices** (both relay-only; neither writes to the repository; both subject to the Dissent Charter):
- **Independent Reviewer** (external AI, currently ChatGPT): third-party critique, counter-proposals, consistency checks. Advisory only. Retained explicitly to diversify reviewer blind spots across model vendors.
- **Data & Research Analyst** (external AI, currently DeepSeek): analyzes exports, backtests, and statistical outputs; informs decisions, never makes or seals them.

5.3 **Amendment B — Developer clarification:** the Developer is Claude Code, one fresh session per task, on worktrees, DEVQ-before-assumption, exactly as ratified. Which underlying model powers a session is an operational detail and confers no change in the Developer's shall/shall-nots. The "Sonnet + Claude Code partnership" framing of draft v1.0 is retired.

5.4 **Amendment C — ADR and ARCH namespacing:** ADRs and ARCH instructions are namespaced per track (`QRF-ADR-###`, `NP-ADR-###`, `ARCH-###` for the QRF/Gen-2 line, `ARCH-NP-###` for the NeelPrajna integration line). The NeelPrajna-side draft "ADR-008 (Kernel/plug-in split)" shall be renumbered before ratification; the real split decision remains QRF-ADR-004; QRF-ADR-008 remains the multi-AI protocol. *(Fixes REV F-12; extended to ARCH numbers after the ARCH-011 collision finding.)*

## Section 6 — Permanently-Human Powers

Never inside any autonomy envelope; movable only by the Owner's typed hand amending this section:
- VIRGIN reserve designation and unlock (typed phrase only).
- Verdict authority (the Battery judges; nothing overrides, re-weights, or re-litigates a verdict).
- Freeze and charter amendments.
- α-budget ceilings (machinery may spend down, never up).
- Promotion and everything downstream of it — expressly including **arming or configuring any mechanism that changes what the real account trades** (Auto-Adopt criteria, sequential live apply, and successors).
- The findings tally.

## Section 7 — Amendment Procedure

7.1 This document is FROZEN on ratification.

7.2 Clarification (no substance change): Architect drafts → Owner reads → Owner OK.

7.3 Amendment (substance change): Architect drafts an evidence-bearing NP-ADR → Chief Scientist review on the record → Owner ratifies.

7.4 Constitutional change (touches a Principle or §3/§6): as 7.3, plus a recorded statement of why the Principle no longer serves. **All voices' reviews are recorded, dissent preserved; there is no vote.** Ratification authority is the Owner's alone. *(Removes draft v1.0's "supermajority of voices" — REV F-5.)*

7.5 The presumption is against amendment; the burden of proof is the proposer's: original rationale, demonstrated failure, evidence, replacement, and why the replacement is stronger.

## Section 8 — Document Status Taxonomy (adopted from draft v1.0)

FROZEN (ratified, binding; changes per §7) · BUILDING (in implementation; changes within sprint scope) · DESIGNED (specified, not started; Architect may revise) · ASPIRATIONAL (recorded intent; not binding). Every estate document shall carry exactly one status.

## Section 9 — Change Record (v1.0 → v2.0)

Retained from draft v1.0: the principle set (merged 11+13), permanently-human powers, presumption against amendment, status taxonomy, deferred questions (unchanged, reviewed only at generation boundaries by the Owner). Changed: mission redefined from "own miniature platform" to Kernel integration (F-3); Knowledge Publication Boundary added (F-2); generation semantics corrected (F-1); roles consolidated as amendments to the ratified doc (F-7); voting removed (F-5); ADR/ARCH namespacing added (F-12); real-account switching mechanisms placed under permanently-human powers (F-13); "organism/heartbeat/every-tick" language demoted to ASPIRATIONAL (F-6).

---
*Anchor: **only what the judge has signed may drive what the hands do.***
