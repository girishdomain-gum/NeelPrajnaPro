# ARO EXECUTION PROCESS v1.0 — the Autonomous Development Workflow
*Annex to `ops\NP-ADR-ARO_draft_v1.0.md` (Phase C operating manual). Introduces **no new authority**: every routing rule below moves artifacts between roles that already hold the mandate to produce them. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. Status: DRAFT, rides with the ARO ADR to Chief Scientist review and Owner ratification.*

---

## 0. The finding that must be stated before the design

**Coordination machinery alone cannot eliminate the Owner as relay, because two participants have no repository presence by rule.**

Constitution §5.2 defines the Independent Reviewer and the Data & Research Analyst as *"both relay-only; **neither writes to the repository**"*, and Roles §2.3 places the Chief Scientist in an external independent session. A coordinator can only route what is in the repository. Every artifact that exists solely inside another vendor's chat window **must** be carried by a human — and there is exactly one human. Today's Chief Scientist review reached the record because the Owner pasted it.

So the bottleneck has two halves, and only one is machinery:

| Half | Cause | Fix |
|---|---|---|
| Routing, dispatch, chasing, packaging | no coordinator exists | the ARO (this document) |
| **Getting external participants' words into the repo at all** | **Constitution §5.2 "relay-only" + external sessions** | **a §7.3 amendment: give every participant a repository mailbox lane** |

**Recommendation (Owner decision, not mine):** amend §5.2 so relay-only means *"advisory — writes only to its own review lane, never to normative documents or the ledger,"* rather than *"writes nothing."* The safeguard §5.2 actually intends is *no authority*, not *no keyboard*. Until that changes, the design below reduces Owner relay touches by roughly the share of traffic that is internal (Architect ↔ Developer ↔ Validator ↔ ARO — the majority), and leaves external review as a single, deliberate paste into one file.

---

## 1. The Autonomous Development Workflow

The eight stages, reconciled with the ratified sprint rhythm (ARCH → Developer → IVF → HC → REV → Go/No-Go → GO + retro → handover). **Note the reconciliation:** the requested lifecycle places "Implementation" *after* the Owner decision; in this estate "Development" is building under a sealed instruction, and "Implementation" is executing a *ratified decision* (the write window). Both exist; they are different stages, and the table keeps them apart.

| # | Stage | Started by | Required inputs | Expected outputs | Auto-routed to | Escalates when | Complete when |
|---|---|---|---|---|---|---|---|
| 1 | **Idea / Objective** | **Owner** (priority) or any role (candidate) | objective statement, or a candidate with rationale | `WO-IDEA` in the intake lane | Architect | Owner priority is absent or two objectives conflict | Architect accepts it into design |
| 2 | **Architecture** | Architect | objective, normative docs, prior art, open findings | sealed ARCH instruction **or** ADR draft | ADR → Chief Scientist; ARCH → Developer | scope touches §6, an amendment, or an unratified dependency | artifact sealed and committed |
| 3 | **Development** | Developer (on `ARCH_SEALED`) | sealed ARCH, boot artifact, fresh worktree | code + tests + session log; or a DEVQ | CI on push; DEVQ → Architect | DEVQ raised · red CI · instruction conflicts with a rule (refusal duty) | CI green + DoD met + session log committed |
| 4 | **Validation** | Validator (on `BUILD_COMPLETE`) | commit, tests, sealed registration | IVF report GREEN/RED, drill results, certificates | GREEN → HC bundle; RED → Architect + Owner packet | RED twice (forward-work freeze, ADR-006) · certificate voided by a change | IVF GREEN, drilled-first evidenced |
| 5 | **Scientific Review** | Chief Scientist (on `VALIDATION_COMPLETE`) | HC bundle, evidence, ADR under review | review with auditable reasons; concurrence or rejection | REV lane → Owner packet | reviewer cannot obtain evidence · disputes a verdict's basis | review filed in its lane |
| 6 | **Owner Decision** | **Owner** (on `REVIEW_COMPLETE` / `DECISION_REQUIRED`) | the decision packet (§6) | typed ruling: ratify / vary / reject / Go / No-Go | ARO records, dispatches consequent lane | — (this stage *is* the escalation terminus) | ruling recorded in the journal, verbatim |
| 7 | **Implementation** | role named by the ruling (usually Architect) | ratified decision + its change list | executed change list, one write window | Validator (consistency check) → Completion | a change list item touches a frozen document | every listed change executed and committed |
| 8 | **Completion** | ARO assembles; Architect closes | outputs, findings, retro | sprint outputs appended, handover §0 rewritten, findings tallied | next `WO-IDEA` / next sprint | outputs exist but no verdict or artifact (standing tripwire) | handover rewritten and committed |

**The invariant across all eight:** every arrow is a file appearing in a lane. No stage advances on a conversation.

## 2. Work Order lifecycle

**A WO is an envelope, never a new instruction system.** QRF-ADR-001 (unique responsibility) and NP-D-009 (one document per thing) forbid a parallel channel, so the WO *carries* existing artifact types — ARCH, ADR, DEVQ, REV, drill, write-window — and adds only routing metadata. The content artifact remains the truth; the WO tracks where it is.

States are those of the ARO ADR §5, unchanged:

```
WAITING → READY → DISPATCHED → RUNNING → COMPLETED
                        │           │
                        │           ├─→ BLOCKED ──(answer)──→ RUNNING
                        │           ├─→ ESCALATED ─→ OWNER_REVIEW ─→ READY / CANCELLED
                        │           ├─→ TIMEOUT ──→ RETRY ──→ DISPATCHED
                        │           │                  └─→ FAILED ─→ ESCALATED
                        └───────────┴─→ RECOVERY (ARO restart: rebuild from repo)
```

Rules: single-flight lock per lane · no dispatch without a manifest · idempotency by `event_key` · a completed WO **emits its completion event, which is what creates the next WO** — the Owner never triggers a successor · a cancelled WO keeps its record (P5).

## 3. Work Order template

```yaml
wo_id: WO-NPS1-014                # sequential, namespaced by sprint
type: ARCH | DEV | VALIDATION | REVIEW | DECISION | WRITE_WINDOW | RETRO
title: one line, imperative
assigned_role: Developer          # a ROLE, never a model (org ADR §1)
session_identity: null            # filled by the session that picks it up
state: READY
created_by: ARO                   # or a role, for hand-raised WOs
created_ts: 2026-07-30T15:40:00Z

content_ref: docs/.../ARCH-NP-002.md   # the artifact; the WO is only the envelope
inputs:
  - ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md   # must exist, else WAITING
  - configs/venues.yaml#xauusd_retail_h07
depends_on: [WO-NPS1-013]
blocks: [WO-NPS1-015]

definition_of_done:
  - the artifact's own DoD
  - session log committed
  - CI green (DEV only)
completion_event: BUILD_COMPLETE

escalation:
  to_role: Architect              # non-§6 questions
  to_owner_if: [constitution_s6, go_no_go, designation, ratification, unclassifiable]
  answer_clock: 24h               # expiry nudges the packet; never auto-answers

separation_of_duties:
  forbidden_same_session_as: [WO-NPS1-013]   # e.g. its own validation
audit:
  dispatch_manifest: ops/aro/dispatch.log.jsonl#...
```

## 4. Routing rules

| Completion event | ARO creates next WO | Assigned role | Notes |
|---|---|---|---|
| `WO_IDEA_ACCEPTED` | ARCH | Architect | — |
| `ARCH_SEALED` | DEV | Developer | fresh session, worktree, boot artifact attached |
| `DEVQ_OPEN` | (no new WO) | Architect | source WO → BLOCKED; answer clock starts |
| `DEVQ_RESOLVED` | — | — | source WO → RUNNING; answer delivered **verbatim** |
| `BUILD_COMPLETE` (CI green) | VALIDATION | Validator | drill-first flag set |
| `VALIDATION_GREEN` | REVIEW | Chief Scientist | HC bundle assembled first; human eyes mandatory |
| `VALIDATION_RED` | — | Architect | + Owner packet entry; RED twice → all forward lanes frozen |
| `REVIEW_COMPLETE` | DECISION | **Owner** | packet entry built (§6) |
| `OWNER_DECISION` = ratify/Go | WRITE_WINDOW | role named in the ruling | change list attached |
| `OWNER_DECISION` = reject/No-Go | RETRO | Architect | lane halted, reasons recorded |
| `WRITE_WINDOW_COMPLETE` | VALIDATION (consistency) | Validator | docs-vs-code check |
| `RETRO_COMPLETE` | handover rewrite → next IDEA | Architect | closes the sprint |
| `FINGERPRINT_MISMATCH` · `REGISTER_DIVERGENCE` · unexpected `WINDOW_BURNED` | **hard stop** + auto-finding | Owner + Architect | no WO proceeds on that lineage |

**Routing is mechanical.** The ARO chooses the destination from the event type and the WO's own metadata. It never chooses *based on content*, because reading content for meaning is reasoning, which it may not do.

## 5. Escalation rules

**Handled automatically (transport only):** sequencing, dispatch, harvest, retry within budget, duplicate suppression, packet assembly, preflight hard stops, generated-state refresh.

**Escalated to a role, not the Owner:** compile errors, red tests, missing or ambiguous inputs, detected document-vs-document conflicts, any scientific question whatsoever.

**Escalated to the Owner, always:** every Constitution §6 power · Go/No-Go · window designations · ratifications · α-budget changes · arming anything real · the findings tally · any WO whose class the ARO cannot determine (**the residual clause: unclassifiable escalates, never guesses**).

**Never escalated, because never ARO business:** the *content* of any answer, review, verdict or ruling. The ARO carries words; it does not weigh them.

**Answer clocks nudge; they never decide.** An expired clock moves the WO to `OWNER_REVIEW` as a visibility item. Silence still binds no one (Roles §3.7).

## 6. Owner decision packet format

One file, `ops\aro\OWNER_PACKET.md`, append-only per cycle, each entry self-contained so no other document must be opened to decide:

```markdown
## DP-014 · Ratify H-07 §5 v1.1 · RAISED 2026-07-30 · BLOCKS: NP-S1 (all deliverables)

**Decide:** whether to seal the evidenced detector definition as §5 v1.1.
**Why it reached you:** ratification is a §6 power. Chief Scientist review: FILED ✅

**What you are approving** — 3 bullets, no jargon.
**Evidence** — ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md · ops/PRE_RATIFICATION_REVIEW_H07_v1.1.md
**Embedded decisions you must also rule:** cost model figure ($0.26 vs $0.47/oz) · trial count (19 vs 18)
**If you approve:** NP-S1 resumes at deliverable 1; first verdict expected in N sessions.
**If you reject:** sprint stays halted; the 324-trade population remains unjudgeable.
**Architect recommendation:** APPROVE with trial count 19 — reasoning in §9 of the ADR.

**Typed wordings:** ▸ APPROVE: "…"  ▸ VARY: "…"  ▸ REJECT: "…"
```

Rules: newest first · one entry per decision, never bundled · **no entry may ask the Owner to run, route, or relay anything** — such an entry is an ARO defect and a finding · dismissed entries keep their record with the reason.

## 7. Workflow state diagram

```
   OWNER: objective ──▶ [WO-IDEA] ──ARO──▶ ARCHITECT
                                              │ seals ARCH / drafts ADR
                    ┌─────────────────────────┴──────────────┐
                    ▼                                        ▼
              [WO-DEV] DEVELOPER                       [WO-REVIEW] CHIEF SCIENTIST
                    │ DEVQ ──ARO──▶ ARCHITECT ──answer──┐         │
                    │ ◀─────────────────────────────────┘         │
                    ▼ CI green                                    │
            [WO-VALIDATION] VALIDATOR                             │
                    │ RED ──▶ ARCHITECT (+packet)   GREEN         │
                    ▼                                             │
              HC BUNDLE ──▶ human eyes ──▶ REV ────────────▶──────┤
                                                                  ▼
                                              ┌──── [OWNER_PACKET] ────┐
                                              │   OWNER: typed ruling   │  ◀── the ONLY
                                              └────────────┬────────────┘      Owner touch
                                     ratify/Go             │            reject/No-Go
                                              ▼            │                 ▼
                                 [WO-WRITE_WINDOW]         │            [WO-RETRO]
                                              │            │                 │
                                              └────────────┴─────────────────┘
                                                           ▼
                                        [WO-RETRO] ──▶ handover rewrite ──▶ next IDEA
```
Every arrow: a file in a lane, carried by the ARO. The Owner appears once.

## 8. Required repository updates

| Path | Purpose | Kind |
|---|---|---|
| `ops\aro\OWNER_PACKET.md` | the single decision inbox | **new — O0, adoptable today, no code** |
| `ops\aro\workorders\{OPEN,BLOCKED,DONE}\WO-*.yml` | WO envelopes | new — O0 conventions, O1 automation |
| `ops\aro\{state.json,queue.jsonl,dispatch.log.jsonl,routing.log.jsonl,heartbeat.json}` | operational metadata, zero epistemic standing, outside `datastore\` | new — O1 |
| `docs\coordination\inbox\{OPEN,CLOSED}\` | DEVQ lane (exists, in use) | unchanged |
| `docs\coordination\review\` | **review lane for external participants** | new — needs the §5.2 amendment |
| ARO ADR §4 event catalogue | add `WO_CREATED`, `WO_COMPLETED`, `WO_CANCELLED` | amend the draft |
| Roles §3 | machine-carried transport clause | in the org/roles ADR already |
| Automation Plan §3 | honesty correction + orchestration layer | already listed |
| Execution Plan | O-track WO-E / NP-O2 / NP-O3 | already listed |
| Constitution §5.2 | **relay-only → advisory-with-a-lane** | **new amendment, §0 above** |

## 9. What this achieves, honestly staged

- **O0 (today, zero code):** the Owner reads one packet instead of scattered asks; WOs exist as files humans update. Relay touches unchanged, but *decisions* are consolidated.
- **O1 (WO-E, alongside NP-S2):** routing, notification, packet assembly, preflight stops automatic. **Internal relay touches → 0.** Dispatch still human.
- **O2:** dispatch automatic — the Owner stops starting sessions.
- **O3:** full cycle; Owner touches are packet judgments only, with the ADR-010b drills armed.
- **The residual:** external-participant relay, until §5.2 is amended. That is the honest ceiling of the machinery, and it is a governance decision, not an engineering one.

---
*Anchor: **the Owner sets the destination and signs the map; the ARO does the walking — and every step it takes is a file, so anyone can audit the route.***
