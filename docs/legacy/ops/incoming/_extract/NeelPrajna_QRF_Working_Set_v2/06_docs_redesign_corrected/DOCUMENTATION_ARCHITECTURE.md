# Documentation Architecture Redesign — Rationale and Migration Table

Status: PROPOSED — awaiting owner ratification (same approval pattern as an ADR).
Written from four sources: the original architecture vision notes, the
Platform Architecture v1.0 ("Document 4"), the two prior research-analysis
volumes, and the live 410-file repository export. Supersedes no content —
every existing document keeps its words; this plan only gives each one a
clearer address and closes the small number of structural gaps found while
reading them together.

---

## 1. Why redesign the documentation, not just the code

The Platform Architecture asks for a Kernel that is domain-blind by
construction, enforced by a CI firewall. The repository already enforces an
analogous rule in code — ADR-001's four-layer, downward-only dependency rule
for the MQL5 EA. **Documentation has no equivalent firewall today.** Kernel
philosophy (Observation Space, the six-object contract, epistemic rules) is
currently written three times, in three different documents, at three
different levels of formality:

| Idea | Where it lives today | Problem |
|---|---|---|
| Six-object Communication Contract | Platform Architecture §5, and re-derived informally in `HANDOVER.md`'s StateHub/EventBus description | No single canonical source; a future editor could let the two drift apart |
| Epistemic rules (deterministic vs. statistical claims, single-variable A/B, within-run-only comparisons) | `docs/adr/ADR-004-amendment-summary.md`, written as an MQL5-specific lesson | The rule is Kernel-level (it belongs to the EvidenceBattery), but its only address is a trading-specific ADR |
| Observation Space / mandatory scoping | Vision notes, Platform Architecture §7.4, and implicitly in NPSU's `run_id`/session columns | No standalone doc a new Kernel component author can cite |
| Institutional memory (why a decision was made, what failure forced it) | Scattered across `HANDOVER.md`'s changelog prose and `docs/tech-debt.md` | Real and valuable, but not in the register form the Architect's Response already recommended and the owner never formally rejected |

The redesign's job is narrow: **give each idea exactly one address**, matching
the Core/Application-Book split the Platform Architecture and the Architect's
Response both independently arrived at.

## 2. The organizing principle

Six top-level categories, each with a single owner and a single question it
answers:

| Folder | Owner | Answers |
|---|---|---|
| `core/` | Chief Research Architect role | "What does the Kernel guarantee, regardless of domain?" |
| `books/<book>/` | Domain implementer (NeelPrajna today) | "How does this guarantee become code for THIS domain?" |
| `governance/` | Owner (permanent) | "Who may approve what, and what is automated vs. human?" |
| `adr/` | Whoever proposes the change | "What was decided, why, and what did we reject?" |
| `registers/` | Whoever closes a session | "What happened, and what did it teach us?" |
| `roadmap/` | Whoever reconciles status | "What phase are we actually in?" |

A document that tries to answer two of these questions at once is the
recurring failure mode this plan removes (see the Phase Ledger's own account
of three disagreeing roadmaps, item 8 below).

## 3. Full migration table

Action key: **KEEP** = same content, address unchanged. **MOVE** = same
content, new path. **SPLIT** = content divided across two new homes.
**NEW** = did not exist before. **NO ACTION** = intentionally left in place
(code, not documentation).

| # | Existing file (as exported) | Action | New location | Note |
|---|---|---|---|---|
| 1 | `repo/README.md` | MOVE | `README.md` (repo root, unchanged) | Root README stays as the single-page orientation; it should gain one line pointing to `docs/INDEX.md` |
| 2 | `repo/CLAUDE.md` | KEEP | `CLAUDE.md` (repo root) | Session-start checklist; add `docs/INDEX.md` as read-before item 0 |
| 3 | `repo/HANDOVER.md` | SPLIT | Architecture prose → `books/book-a-neelprajna/ARCHITECTURE.md`; version history → `books/book-a-neelprajna/CHANGELOG_NARRATIVE.md` | The file currently mixes a resurrection brief with a running changelog; both are valuable but are different documents |
| 4 | `repo/CHANGELOG.md` | KEEP | unchanged | Machine-readable semver log stays as-is |
| 5 | `repo/docs/adr/ADR-001…007*.md` | MOVE | `docs/adr/` | Renumbering NOT required; existing numbers stay valid |
| 6 | `repo/docs/PHASE_LEDGER.md` | MOVE | `docs/roadmap/PHASE_LEDGER.md` | No content change — it is already the reconciled single ladder |
| 7 | `repo/docs/tech-debt.md` | MOVE | `books/book-a-neelprajna/TECH_DEBT.md` | Stays scoped to the trading plug-in; Core gets its own tech-debt file only if/when it accumulates any |
| 8 | `repo/docs/coding_guidelines.md` | MOVE | `books/book-a-neelprajna/CODING_GUIDELINES.md` | MQL5-specific; not a Core concern |
| 9 | `repo/docs/dev_workflow.md` | MOVE | `books/book-a-neelprajna/DEV_WORKFLOW.md` | — |
| 10 | `repo/docs/NP_Architecture_Roadmap_v1.0.md` | KEEP (historical) | `docs/roadmap/archive/NP_Architecture_Roadmap_v1.0.md` | Already superseded per Phase Ledger §2.2; kept for provenance, not deleted |
| 11 | `repo/docs/plans/overhaul.md` | KEEP (historical) | `docs/roadmap/archive/overhaul.md` | Superseded per Phase Ledger §2.1; historical record |
| 12 | `repo/docs/plans/phase3_gate_recipe.md`, `phase4_session_plan.md`, `phase6_completion_record.md`, `phase6_sequential_strategy_engine_design_v1.0.md`, `phase7_gate_recorder_design_v1.0.md` | MOVE | `books/book-a-neelprajna/plans/` | Concrete engineering plans for the trading plug-in; grouped together |
| 13 | `repo/docs/plans/automation_v2_*.md` (design v1.0, v1.1, amendment v1.2) | MOVE | `governance/automation/` | These are operations/autonomy design docs, not trading-domain docs — belong beside ADR-005, not beside gate designs |
| 14 | `repo/docs/plans/dashboard_spec*.md` | MOVE | `books/book-a-neelprajna/plans/` | UI spec for the EA |
| 15 | `repo/docs/plans/PARKED.md` | MOVE | `books/book-a-neelprajna/plans/PARKED.md` | — |
| 16 | `repo/docs/AI_ROLE_PROMPTS.md` | MOVE | `governance/AI_ROLE_PROMPTS.md` | Applies to any AI on any book, not just NeelPrajna |
| 17 | `repo/docs/AUTOMATION_BRIDGE.md` | MOVE | `governance/AUTOMATION_BRIDGE.md` | Describes the job-bridge mechanism underlying the autonomy ladder |
| 18 | `repo/docs/FABLE_COMMS_STANDARD.md` | MOVE | `governance/COMMUNICATION_STANDARD.md` | Owner-issued, applies programme-wide |
| 19 | `repo/docs/BOOT_PROMPT.md`, `BOOT_PROMPT_post_phase6.md` | SPLIT/CONSOLIDATE | `books/book-a-neelprajna/BOOT_PROMPT.md` (keep only the current one; fold the superseded one into `roadmap/archive/`) | Two boot prompts existing at once is exactly the "which one is current?" problem this redesign removes |
| 20 | `repo/docs/SESSION_BOOTSTRAP.md` | MOVE | `books/book-a-neelprajna/SESSION_BOOTSTRAP.md` | — |
| 21 | `repo/docs/WORK_ORDERS_v3.17.md` | MOVE | `books/book-a-neelprajna/work-orders/WORK_ORDERS_v3.17.md` | Establishes a `work-orders/` folder for future versions instead of new top-level files each time |
| 22 | `repo/NPSU_Design_Doc_v1.6.md/.docx` | MOVE | `books/book-a-neelprajna/NPSU_DESIGN.md` | Keep both formats; `.md` is the source of truth, `.docx` is the distributable |
| 23 | `repo/NPSU_PostValidation_Guide_v1.0.md/.docx` | MOVE | `books/book-a-neelprajna/NPSU_POST_VALIDATION_GUIDE.md` | — |
| 24 | `repo/methodology/Architect_Response_and_Production_Plan_v1.0.md/.docx` | KEEP (historical charter) | `docs/roadmap/archive/Architect_Response_and_Production_Plan_v1.0.md` | This is the P0 Charter that led to the current programme structure; preserved as the founding document, referenced by `DOCUMENTATION_ARCHITECTURE.md` §2 |
| 25 | `repo/analyzer/README.md` | NO ACTION | unchanged | Tool-adjacent documentation, correctly colocated with the tool |
| 26 | `repo/tests/longrun/README.md`, `PREDICTIONS.md` | NO ACTION | unchanged | Pre-registered predictions belong beside the test they predict |
| 27 | `repo/tests/phase6/README.md` | NO ACTION | unchanged | — |
| 28 | `lab/SUPERVISOR_CONTRACT.md` | MOVE | `governance/SUPERVISOR_CONTRACT.md` | Content unchanged (it is a frozen, owner-signed contract); only its documentation address moves — the actual `np_supervisor.py` stays in `lab/` |
| 29 | *NeelPrajna Platform Architecture v1.0 (this conversation's upload)* | MOVE, pending ratification | `docs/core/` (split into `KERNEL_OVERVIEW.md`, `COMMUNICATION_CONTRACT.md`; Trading-plug-in sections move to `books/book-a-neelprajna/TRADING_PLUGIN.md`) | Its own §1–3 and §5–7 are Core; its §4 (Trading plug-in) and §6 (interface contracts naming trading-specific paths) are Book A |
| 30 | *QRF × NeelPrajna Research Architecture (Volume I, this conversation)* | KEEP (historical analysis) | `docs/roadmap/archive/analysis-volume-1.md` | Analytical, not normative — kept for provenance, does not govern anything |
| 31 | *NeelPrajna: From Vision to Verified System (Volume II, this conversation)* | KEEP (historical analysis) | `docs/roadmap/archive/analysis-volume-2.md` | Same as above |
| 32 | *(did not exist)* | NEW | `docs/registers/DECISION_REGISTER.md`, `docs/registers/LESSON_REGISTER.md` | Recommended by the Architect's Response P1, never formally started; seeded in this redesign from real history already on record |
| 33 | *(did not exist)* | NEW | `docs/adr/ADR-008-kernel-trading-plugin-split.md` | Ratifies the Core/Book split at ADR level, the same way ADR-001 ratified the internal EA layering |
| 34 | *(did not exist)* | NEW | `docs/core/EPISTEMIC_RULES.md` | Promotes ADR-004's amendment rules (R1–R3) from an EA-specific ADR to a Kernel-level standing rule, cited by both books |
| 35 | *(did not exist)* | NEW | `docs/roadmap/MIGRATION_PLAN.md` | The execution plan for this very redesign, gated like any other phase |

## 4. What this redesign deliberately does not do

- It does not rewrite, shorten, or edit the substance of any existing
  document. Every ADR, every plan, every design doc keeps its words.
- It does not touch code, `.set`/`.ini` files, or CSV schemas.
- It does not create Book B, C, ... for biology, robotics, or any future
  domain. Those folders are created only when a second project actually
  starts, per the Architect's Response's "growth by mitosis, never by
  pre-allocation" rule.
- It does not resolve any open engineering question (R6 long run, Phase 7
  Gate Recorder, hourly filter). Those stay exactly where the Phase Ledger
  already puts them.

## 5. Approval

This document follows the same approval pattern as an ADR: proposed here,
ratified by the owner, then executed per `roadmap/MIGRATION_PLAN.md`.

- Status: **PROPOSED**
- Ratified by: _______________________ Date: _______________
