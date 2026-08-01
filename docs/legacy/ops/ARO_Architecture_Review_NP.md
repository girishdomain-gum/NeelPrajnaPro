# ARO Architecture Review — Autonomous Research Orchestrator Evaluation
*WORKING RECORD — Architect proposal, 2026-07-30. Status: DRAFT awaiting Chief Scientist review and Owner ratification (Constitution §7.3 path — this proposal, if adopted, amends the ratified Roles document and adds an §A.1 row, so it travels as an evidence-bearing NP-ADR, never as an edit). Nothing below changes any normative document; every proposed edit is enumerated in §11 and executes only after ratification. Author: Fable (Architect). Requested by the Owner, 2026-07-30 ("ARO Evaluation" request).*

---

## 1. Architecture Review — what the estate already says, with evidence

**Read for this review, end to end:** Architecture v1.0 (twin) · Constitution v2.0 · Vision v1.0 · Execution Plan v2.0 · Automation Plan v1.0 · Roles & Communication v1.0 · V&V Plan v1.0 · Decisions v1.0 · Journal J-001..J-033.

### 1.1 The decisive prior decision the request did not know it already had

**QRF-ADR-010b — "Supervised autopilot: phased automation with a drilled human gate"** (Decisions v1.0, Part 1) is already Owner-ratified and already defines the ladder this request asks about:

> *Phases A (tireless CI) → B (autonomous Developer) → C (orchestrated cycle + Owner packet), each Owner-gated and reversible. Permanently human: Go/No-Go phrases, VIRGIN acts, changes to ivf/CI/this decision, audits of the automation. Binding constraints R-1..R-7 including Owner drills (planted defects the Owner must catch — a miss pauses autopilot), Developer-write-refusal on ivf/** and workflows, scratch-datastore default, typed-phrase journal grants, no-web least-privilege agents, budget caps, heartbeat-or-STALE plumbing.*

**Phase C is the ARO.** The orchestrated cycle with an Owner packet — decisions batched and presented as complete judgment points instead of the Owner carrying messages — is precisely the subsystem this request names. The architectural question was answered in Generation 1; what never happened is its scheduling into the NeelPrajnaPro Execution Plan. **This is the same species as finding F-24 / J-028** (both dashboard specs complete, scheduled nowhere): a ratified capability with no sprint owning it.

### 1.2 The four-document evidence table (the request's "evaluate current documents" task)

| Document | Autonomous capability that EXISTS | Still manual | Intentional? | Classification |
|---|---|---|---|---|
| **Architecture** | Execution automation on both surfaces; WindowLedger burn-on-use with *structural refusal on reuse* (the "window burned → lock" example already exists); Battery atomic verdict+burn (verdict recording already automatic); closed write-authority list §2.1 | The arrows between roles: dispatch of sessions, routing of DEVQs/reviews/rulings | Partly — §2.1's closed list is deliberate and must survive any orchestrator | Row 8 is correctly scoped (see 1.3); the SDLC arrows are an **architectural gap** with a ratified but unscheduled answer (ADR-010b Phase C) |
| **Vision** | Row 8 "Continuous Communication" defined precisely: event-driven belief releases between the organs; "nobody waits" = asynchronous events, not tick-streaming | — | **Yes** — row 8 is a runtime-platform property by design | Not a gap in row 8; the request's tension ("architecture says nobody waits, yet development blocks") dissolves once row 8's scope is read: it governs the organs, not the software-development lifecycle |
| **Execution Plan** | Within-sprint execution automated (Claude Code sessions, bridge jobs, IVF) | Sprint *progression* is manually coordinated: the Owner pastes boot prompts (J-033 created `ops\DEVELOPER_BOOT_NP-S1.md` for manual pasting), relays reviews, carries screenshots between sessions | No — the plan inherits the rhythm as a protocol but never assigns the arrows to machinery | **Architectural gap** (unscheduled ADR-010b Phase C) |
| **Roles & Communication** | QRF-ADR-008's file-based coordination substrate: ARCH/DEVQ/REV/NOTE ids, inbox OPEN→CLOSED, "no AI is indispensable; all state is external" | The *transport*: files exist, but a human notices them and summons the next role. Communication is person-driven over a file substrate that was designed to be machine-watchable | No — ADR-008 was built for exactly this and is under-used | **Documentation-vs-practice gap** riding on the architectural one |
| **Automation Plan** | §3's table: two execution surfaces, typed jobs, watchdog, manifests, supervisor G-invariants; touch budget "routine ops → 0" | §3 *claims* "the joint sprint loop, fully automated end-to-end… every arrow except the last is machine-executed." **This is documented, not true.** The nodes are automated; the arrows are human-carried | The claim was aspiration written as description | **Documentation defect inside the plan** (F-17's own species — docs vs reality) + the architectural gap it papers over |
| **Decisions** | ADR-010b (the ladder) · ADR-008 (file coordination) · ADR-007 (generated state) — the three pillars an orchestrator needs already exist as ratified decisions | Their composition into a running Phase C | No | Gap = composition + scheduling, not invention |
| **V&V** | Drill culture ready to certify an orchestrator like any instrument | No drills defined for orchestration itself | N/A (subsystem didn't exist) | Follows the recommendation |

### 1.3 Continuous Communication — the specific ruling requested

Row 8 currently governs the **runtime platform** (organ-to-organ, Contract v2, NP-S5) and should stay exactly there: widening a ratified box's meaning mid-flight is how definitions rot. The development lifecycle needs the *same philosophy* delivered by a *different, separately named* subsystem — the ARO — so that "Continuous Communication" never becomes an ambiguous term meaning two things. **Recommendation: do not extend row 8; add a new row (see §4).**

### 1.4 The live exhibit

This very sprint is the evidence the request asked for: the Owner hand-relayed the Chief Scientist's DEVQ-01 review, hand-carried a screenshot from the verifying Claude Code session, and hand-instructed the reconciliation between sessions — five relay touches in one day, none of them judgment, all of them routing. Under the Automation Plan's own success measure ("the fraction of the Owner's remaining touches that are pure judgment toward one hundred percent"), each was a measurable miss. The Owner is the message bus because nothing else is.

---

## 2. Gap Analysis — the one-sentence findings

1. **The gap is real and it is orchestration, not execution.** Execution (work inside a node) is automated to near-zero routine touches. Orchestration (the arrows: notice a completion event, dispatch the next role, route questions, queue decisions) has no owner, so the Owner is it.
2. **The gap is already architecturally answered** by QRF-ADR-010b's Phase A→B→C ladder — ratified, constrained, reversible, Owner-drilled. Nothing new needs inventing at the principle level.
3. **The gap is a scheduling omission** (F-24 species): Phase C appears in no sprint, no work order, no §A.1 row.
4. **One documentation defect:** Automation Plan §3 describes the arrows as machine-executed; they are not. That sentence must be corrected whatever else is decided (honesty rule; F-17 species).
5. **Constitution: no gap.** §6 is untouched by any of this; ADR-010b already carved the envelope.

**Answer to the Primary Question:** *No — not today.* NeelPrajnaPro cannot execute a sprint with minimal Owner intervention because sprint arrows are human-carried. *Yes — after building what is already ratified:* ADR-010b Phase C, specified for this estate as the ARO, closes the gap without touching a single permanently-human power.

---

## 3. Recommendation

**Introduce the ARO as the NeelPrajnaPro realization of QRF-ADR-010b Phase C** (name accepted from the Owner's request; lineage subtitle: *"Supervised Autopilot, Phase C"*). Adopt via a new NP-ADR (§10), build via a phased migration (§12) in which each phase is Owner-gated per ADR-010b's own rule. Classification in the architecture: **coordination plane — infrastructure, not an organ** — exactly as rows 11–12 are surfaces, not organs. The ARO never appears inside the two-organ diagram and never touches the wall.

---

## 4. ARO Architecture

**Purpose.** Machine-execute the arrows of the ratified sprint rhythm so every remaining Owner touch is pure judgment.

**Mission, one sentence.** *The ARO carries messages and dispatches work; it never has an opinion.*

**Scope.** The software-development lifecycle of this repository: sprint rhythm progression, role-session dispatch, question/review routing, decision queueing, mechanical-invariant watching. Out of scope forever: the runtime platform's Contract v2 (row 8), anything inside the two organs, anything on the §2.1 write-authority list.

**Inputs (all files in the repository — repository-first per QRF-ADR-008):** sealed ARCH instructions · DEVQ files · IVF/HC/REV outputs · bridge job status/manifests · CI results · the journal · the fingerprint/manifest artifacts of the queued detector-identity ADR.

**Outputs (all files; none of them ledger records):** dispatch records (which session was started, with which boot artifact, why) · the **Owner Packet** — a single decision inbox file listing every pending judgment as a complete, self-contained decision point with its evidence links · routing notices (DEVQ-opened → Architect queue; REV-filed → Owner packet) · heartbeat/state file · auto-findings for *mechanical* invariant violations only (§7).

**Interfaces & event model.** Events are file appearances/changes in named repo locations (extending ADR-008's inbox convention): `ARCH_SEALED`, `DEVQ_OPENED`, `DEVQ_ANSWERED`, `IMPL_COMPLETE` (commit + tests green), `IVF_GREEN/RED`, `HC_FILED`, `REV_FILED`, `DECISION_REQUIRED`, `DECISION_RECORDED`, `JOB_DONE` (bridge), `FINGERPRINT_MISMATCH`, `REGISTER_DIVERGENCE` (WO-D). The ARO is a watcher + state machine over these. State transitions mirror the ratified rhythm **exactly, in order, no step skipped or reordered** — the rhythm is configuration the ARO obeys, never logic it owns.

**Interaction with each party (one line each):** *Owner* — receives the packet; is never asked to relay or run anything (a routing request reaching the Owner is an ARO defect and a finding). *Architect* — receives routed DEVQs/reviews; its sealed ARCHs are the ARO's dispatch triggers. *Developer* — sessions are dispatched with the boot artifact; their DEVQs stop their lane automatically. *Chief Scientist / Independent Reviewer / Research Analyst* — receive review bundles; their outputs route back as events; relay-only status unchanged. *IVF* — dispatched after implementation completes; RED freezes the lane (ADR-006 rule, now machine-enforced). *HC* — receives assembled bundles; a human still looks (ADR-009b: HC without a human is just another VC). *Battery/WindowLedger/BeliefLayer/Knowledge Graph/Repository/CI/Bridge* — the ARO submits jobs, reads results, and **never** holds write authority to any of them; §2.1's closed list is unchanged.

**Failure modes & recovery (inherited constraints, named):** heartbeat-or-STALE (ADR-010b) — a dead ARO is loudly dead, never silently absent; silence is negative and fail-closed (G-1/G-2) — an unrecognized state or schema is STALE + escalate, never a guess; duplicate-work prevention by idempotent event keys and single-flight dispatch per lane (D26's dual-identity discipline applied to tasks); every dispatch produces a manifest or it is not a dispatch (D4); repo-vs-ARO-state divergence → repo wins, lane halts, finding (Roles §3.6). Recovery is always: rebuild state from the repository, because all state *is* the repository (ADR-007/008).

---

## 5. SHALL / SHALL NOT (the role definition, drafted for the Roles amendment)

**The ARO is not a voice.** It has no mandate to speak, no epistemic standing, no place in the Dissent Charter except as a subject of findings. It is machinery, defined here with role-grade precision because machinery near governance must be.

**SHALL:** watch the repository for rhythm events; dispatch the next role session per the sealed rhythm with the correct boot artifact; route questions and reviews to the accountable voice's queue; assemble and maintain the Owner Packet; enforce mechanical invariants by hard stop (fingerprint mismatch; register divergence; window-reuse attempt reaching it before the WindowLedger's own refusal); record every action in its append-only dispatch log; go STALE loudly on any ambiguity.

**SHALL NOT:** answer a DEVQ; summarize, soften, or reorder any voice's words in transit (Roles §3.5 applies to machinery too); skip, reorder, or parallelize rhythm steps beyond what the rhythm itself declares; dispatch work when its preconditions are absent; escalate to the Owner anything that is not a judgment.

**MAY:** batch non-blocking notifications; retry transient failures within budget caps (ADR-010b); propose (as a routed task, authored by no one) that a human look at an anomaly.

**MUST NEVER:** perform scientific reasoning, judge evidence, write or influence verdicts, author ARCH/ADR/review/code/documentation content, write ledger records, modify normative documents, touch `ivf/**` or CI workflows (Developer-write-refusal extended to it verbatim), create registrations, or acquire any authority from the §2.1 list or Constitution §6. **An automation proposal that would move one of these into the ARO is refused by rule, not debated per case** (Automation Plan §5, inherited).

**Automatic vs escalated decisions — the policy table (with three corrections to the request's examples, recorded as Architect dissent per the charter):**

| Trigger | ARO action | Basis / correction |
|---|---|---|
| Compile/tests green | dispatch validation | plain sequencing |
| Battery verdict (PASS **or** FAIL) | record dispatch of next rhythm step; refresh generated state; packet entry | verdict recording is already the Battery's atomic act; **correction 1:** the request's "Battery PASS → register automatically" is inverted for this estate — registration precedes evidence (P2, QRF-ADR-011) and is a scientific act, never automatic; machine-proposed registrations arrive only after Gate A (Constitution §4) |
| Battery FAIL | **no finding** — route to retro | **correction 2:** FAIL is a *result*, not misconduct (P11). Auto-converting FAIL to a finding would corrupt the tally's meaning. Findings name defects and violations, not disappointing evidence |
| Fingerprint mismatch | hard stop + auto-finding | aligns with the queued detector-identity ADR; DEVQ-01 is the proof case |
| Register divergence (windows.json vs WindowLedger) | auto-finding | WO-D already rules exactly this |
| Documentation missing/stale | open a routed task for the accountable voice | **correction 3:** the request's "generate draft" would make the ARO an author; authorship belongs to voices. It opens the task; the Architect (or Developer, per lane) writes |
| Window burned | nothing to add | WindowLedger already refuses structurally; the ARO merely surfaces the refusal in the packet |
| Anything in Constitution §6 · Go/No-Go · designations · ratifications · DEVQ answers · review content · ambiguity of any kind | **escalate, always** | the permanently-human list and "silence binds no one" |

---

## 6. Updated architecture diagram (proposed §A.1 change — executes only on ratification)

Add **row 13**: `Automation — Research Orchestrator (ARO, coordination plane)` · Status TARGET · Delivered by **NP-O1..O3** (§12). Caption rule mirroring rows 11–12: *the ARO is infrastructure around the organs, not an organ; it appears nowhere in the two-organ diagram; it holds no write authority and no epistemic standing.* The acceptance test sentence ("when no row reads TARGET…") is unaffected in spirit; the ARO row is TARGET like any other and earns BUILT only through its verdict-bearing drills (§9).

## 7. Updated sprint flow (target state, Phase C)

```
ARCH sealed ──ARO──▶ Developer session (auto-boot, worktree)
      │ DEVQ opened ──ARO──▶ Architect queue ──answer──▶ lane resumes
      ▼ impl complete (commit+CI green)
   ──ARO──▶ IVF (drill first)  ── RED ──▶ lane frozen + packet entry
      ▼ GREEN
   ──ARO──▶ HC bundle ──▶ human eyes ──▶ REV
      ▼ REV filed
   ──ARO──▶ OWNER PACKET  ◀── the single place judgment is requested
      ▼ Owner: Go/No-Go (typed, human, forever)
   ──ARO──▶ GO record + retro dispatch + handover-rewrite task ──▶ next ARCH
```
Every arrow machine-carried; every box's *content* exactly as today; the Owner appears once, at the packet, as judge.

## 8. Updated communication model

ADR-008 extended, not replaced: communication remains **files, not chat** — the ARO adds the missing courier. Voices write to their lanes; the ARO watches, routes, and dispatches; attribution is preserved verbatim end-to-end; findings travel un-softened (Roles §3.5); the journal remains the only log of record and the ARO's dispatch log is operational, never a second changelog (NP-D-009 respected: it is a machine artifact, not a document).

## 9. V&V for the ARO itself (it earns trust like everything else)

Certification before Phase C arms: **planted-event drills** (synthetic DEVQ/REV/verdict events; the ARO must route each to the correct queue and only there) · **escalation drills** (planted §6-class decisions; any auto-action = certification FAIL) · **duplicate-storm drill** (replayed events; exactly-once dispatch proven) · **dead-courier drill** (kill the ARO mid-sprint; STALE must be loud within its heartbeat budget and recovery must rebuild from repo alone) · **Owner drills** per ADR-010b R-constraints (planted defects the Owner must catch; a miss pauses autopilot — the constraint is inherited verbatim). Any certified-component change voids certificates (VV §4.4 applies).

## 10. Required ADRs

1. **NP-ADR-00X — "ARO: NeelPrajnaPro realization of QRF-ADR-010b Phase C."** Carries: this review as evidence · the role definition (§5) · the policy table with its three corrections · the §A.1 row · the phased migration with Owner gates · the certification drills. §7.3 path (amends the ratified Roles doc).
2. **The already-queued detector-identity/fingerprint ADR** (DEVQ-01 annex §8) — now a *dependency*: the ARO's fingerprint hard-stop preflight consumes its artifacts. Sequence: fingerprint ADR first or jointly.

## 11. Required document changes (each executes only after ratification, in one write window)

| Document | Change | Kind |
|---|---|---|
| Architecture | §A.1 +row 13 with caption; new short §10 "Coordination Plane (ARO)" pointing at the NP-ADR; Part C atlas note | Amendment (§7.3, via the NP-ADR) |
| Vision | delivery table +row 13, same wording (spine rule) | Same pass |
| Execution Plan | new parallel track NP-O1..O3 (§12); §0 handover notes the track; Automation-plan cross-reference | Same pass |
| Automation Plan | **honesty correction to §3's "every arrow machine-executed" sentence (required even if ARO is rejected)**; new §8 "Orchestration layer" distinguishing execution vs orchestration; touch-budget table gains relay-touch counting | Correction + amendment |
| Roles & Communication | ARO defined as non-voice machinery with §5's shall/shall-nots; §3 gains "machine-carried transport" clause | Amendment (the reason §7.3 applies) |
| Decisions | new NP-D entry recording the ADR | Append |
| V&V | §9's drill classes added as a new level-adjacent section | Amendment |
| Constitution | **no change** — §6 untouched; verified line by line against §5's tables | — |
| Research | optional RQ: "orchestration telemetry as evidence of process health" | Append if wanted |

## 12. Migration plan (evolution, not replacement — each phase Owner-gated and reversible per ADR-010b)

- **Phase O0 — conventions only (no code, can start immediately):** create the decision-inbox file (`OWNER_PACKET.md`) and the event-file naming conventions in ops\; humans use them manually. Cost: near zero. Benefit: the Owner's judgment queue becomes one place *today*, and the later phases automate an already-practiced convention rather than a new one.
- **Phase O1 = ADR-010b Phase A — tireless watching:** a watcher process (bridge-style, supervised, heartbeat) that *notifies and assembles*: routes DEVQs/reviews to queues, refreshes the packet, runs the WO-D consistency check and fingerprint preflight. Dispatches nothing. Owner gate to proceed.
- **Phase O2 = Phase B — autonomous dispatch:** the watcher may boot Developer/IVF sessions on their trigger events, with manifests, budget caps, and single-flight locks. Owner gate + certification drills (§9) to proceed.
- **Phase O3 = Phase C — the full orchestrated cycle:** all arrows machine-carried; Owner touches = packet judgments only; Owner drills run per ADR-010b; any drill miss pauses autopilot. Success measured by the Automation Plan's own two numbers: routine+relay touches per sprint → 0; judgment fraction of remaining touches → 100%.
- **Scheduling recommendation:** O0 now; O1 as a work order (WO-E) alongside NP-S2 (whose months-long R6 runs are the natural first beneficiary); O2/O3 gated behind O1's observed behavior across at least one full sprint. The ARO must never be on any scientific sprint's critical path until certified.

---

## 13. Closing assessment

The request feared an architectural gap; the record shows something better and slightly embarrassing: the architecture already decided this (ADR-010b), built its substrate (ADR-008 files, the bridge, the supervisor), wrote its philosophy (Automation Plan §5's two numbers) — and then never scheduled the last layer, while the Automation Plan described it as done. One documentation defect to correct regardless; one ratified decision to finally schedule; zero constitutional changes; zero reduction of Owner authority — the Owner's authority is what remains when the relaying is gone.

*Anchor: **the ARO carries messages and dispatches work; it never has an opinion — and the day it has one is the day it is switched off by the rule that built it.***
