# ARO EXECUTION PROCESS v2.0 — Repository-First Autonomous Execution
*Supersedes `ops\ARO_Execution_Process_v1.0.md` (which designed around today's chat relay instead of past it — Owner correction, 2026-07-30, accepted). Annex to `ops\NP-ADR-ARO_draft_v1.0.md`. Introduces no new authority. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**The correction this version encodes:** v1.0 treated "external participants cannot write to the repository" as a design constraint. It is an **implementation limitation of today's sessions, not a property of the architecture.** v2.0 assumes every participant is a repository-capable session. The manual paste is a temporary shim with an exit date, recorded in §9 — never a design principle.

---

## 1. Repository-first execution architecture

**Four rules, and everything else follows.**

1. **The repository is the only communication channel.** No instruction, answer, review, or result exists until it is a committed file. Chat is a viewport, never a transport.
2. **Work is PULLED, not pushed.** A session boots, reads *its own mailbox*, claims the top unblocked item, works, publishes, releases. Nobody — not the Owner, not the ARO — tells a participant to start. This is what actually removes the Owner from coordination: there is no "tell" left to do.
3. **Every participant reads exactly one mailbox** — its own role's queue. Isolation is what makes the system auditable and what makes wrong-routing detectable rather than silent.
4. **The ARO keeps the queue; it never keeps the meaning.** It creates work orders from completion events, moves state, detects blockage, and packages decisions. It reads *types and metadata*, never content-for-meaning.

**The one honest dependency:** a repository cannot start a process. Something must *invoke* a session — a scheduler, a supervisor, or the platform's own runner. The ARO (or the existing Supervisor) performs invocation only; the session then pulls its own work. Invocation is not instruction: an invoked session with an empty inbox does nothing and exits.

## 2. Repository directory structure

```
ops/aro/
├── queue/
│   ├── architect/          {inbox, active, waiting, blocked, review, completed}/
│   ├── developer/          {inbox, active, waiting, blocked, review, completed}/
│   ├── validator/          {inbox, active, waiting, blocked, review, completed}/
│   ├── chief_scientist/    {inbox, active, waiting, blocked, review, completed}/
│   ├── runtime_manager/    {inbox, active, waiting, blocked, review, completed}/
│   ├── independent_reviewer/ {inbox, active, completed}/
│   ├── data_analyst/       {inbox, active, completed}/
│   └── owner/
│       ├── decisions/pending/     DP-NNN_*.md      ← the ONLY Owner-facing folder
│       └── decisions/ruled/       DP-NNN_*.md
├── handovers/              WO-NNN/HANDOVER.md + attachments
├── leases/                 WO-NNN.lease           ← atomic claim, git-enforced
├── state/                  workflow.json (cache), heartbeat.json
└── log/                    dispatch.jsonl, routing.jsonl, escalation.jsonl (append-only)
```

**Boundaries that must not blur:** everything above is **operational metadata with zero epistemic standing** and lives outside `datastore/` (the ledger). Normative artifacts still live in `docs/` and code in `qrf/`; a WO only *references* them. A citation of `ops/aro/` as evidence in any scientific artifact is a finding.

## 3. Standard work queue design

Each role's queue is six folders, and **the folder is the state** — no second state vocabulary, no state file that can disagree with the tree:

| Folder | State | Meaning | Who moves it |
|---|---|---|---|
| `inbox/` | READY | claimable now; dependencies met | ARO puts in; participant claims |
| `active/` | RUNNING | claimed under a live lease | participant (on claim) |
| `waiting/` | WAITING | dependency unmet | ARO |
| `blocked/` | BLOCKED | question open, clock running | participant (on raising) |
| `review/` | REVIEW | output awaiting another role | ARO |
| `completed/` | COMPLETED | done, handover published | participant, then ARO archives |

**Claiming is atomic, and git provides the lock.** A session writes `leases/WO-NNN.lease` (role, session identity, timestamp, expiry), commits, and **pushes**. If the push is rejected as non-fast-forward, another session claimed it first — the loser re-pulls and takes the next item. No lock server, no race, fully auditable. An expired lease is reclaimable and the expiry is logged as a TIMEOUT.

**Separation of duties is enforced at claim time, mechanically.** The WO carries `forbidden_session_identities` and `forbidden_same_session_as`. A session whose identity matches refuses the claim and returns the WO to `inbox/` with a logged reason. This is where the organization ADR's §5.5 stops being prose and becomes a check.

## 4. Standard handover package

Published by every participant at completion, at `ops/aro/handovers/WO-NNN/HANDOVER.md`. **Its acceptance test: the next participant needs no chat explanation, ever.**

```markdown
# HANDOVER · WO-NPS1-014 · Developer → Validator
Role: Developer · Session: <model, interface> · Completed: <ts> · Commits: abc1234..def5678

## 1. What was asked            (WO id + one-line restatement)
## 2. What I did                (facts, in order)
## 3. What changed              (files + commits; nothing implied)
## 4. Decisions I made          (and the authority for each)
## 5. What I did NOT do         (and why — scope, refusal, or block)
## 6. Open questions            (DEVQ refs; or "none")
## 7. Evidence of DoD           (test output, CI ref, drill results)
## 8. What the next role must do (concrete first action)
## 9. How to verify me          (exact commands a stranger can run)
## 10. Risks / uncertainties    (honest; "none" is a claim you own)
```

Section 9 is the load-bearing one: it makes every handover independently checkable, which is what lets the next role start without trusting the last.

## 5. Standard work order template

```yaml
wo_id: WO-NPS1-014
type: ARCH | DEV | VALIDATION | REVIEW | DECISION | WRITE_WINDOW | RETRO
title: <imperative, one line>
assigned_role: developer            # a ROLE, never a model
state: inbox
priority: 2                         # Owner-set at the objective level only
created_by: aro
created_ts: 2026-07-30T16:10:00Z

content_ref: docs/coordination/instructions/ARCH-NP-002.md   # the WO is an envelope
inputs:                             # ARO holds the WO in waiting/ until all exist
  - ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md
  - configs/venues.yaml#xauusd_retail_h07
depends_on: [WO-NPS1-013]
blocks:     [WO-NPS1-015]

definition_of_done: [<artifact DoD>, handover published, session log committed]
completion_event: BUILD_COMPLETE
next_wo_template: VALIDATION        # what ARO creates on completion

separation_of_duties:
  forbidden_same_session_as: [WO-NPS1-013]
  rule_ref: constitution §5.5

escalation:
  to_role: architect
  to_owner_if: [constitution_s6, go_no_go, designation, ratification, unclassifiable]
  answer_clock_hours: 24            # nudges the packet; never answers

lease: {holder: null, session_identity: null, expires: null}
audit: {events: [], log_ref: ops/aro/log/routing.jsonl}
```

## 6. State transition rules

```
waiting ──inputs present──▶ inbox ──claim (lease won)──▶ active
                                                           │
     ┌─────────────────────────────────────────────────────┤
     ├─ question raised ─────▶ blocked ──answer committed──▶ active
     ├─ output for another role ─▶ review ──consumed───────▶ completed
     ├─ DoD met + handover ──────────────────────────────▶ completed
     ├─ lease expired ─────▶ inbox (TIMEOUT logged, retry budget --)
     ├─ retry budget exhausted ─▶ blocked + escalation entry
     └─ §6-class question ─▶ owner/decisions/pending/  (the terminus)

completed ──ARO reads completion_event──▶ creates next WO in the next role's inbox
```

**Invariants:** every transition writes an append-only log line · no WO leaves `active/` without either a handover or a logged failure · `blocked/` never auto-resolves · illegal transitions move to escalation with reason `illegal_transition` · **ARO state is a cache; the folder tree is the truth**, and recovery is a full rescan.

## 7. ARO workflow algorithm

```
loop every N seconds:
  1. SCAN     git pull; walk ops/aro/queue/**; rebuild state from the tree
  2. PROMOTE  for each WO in waiting/: if all inputs exist and deps completed → move to inbox/
  3. REAP     for each WO in active/: if lease expired → return to inbox/, log TIMEOUT,
              decrement retry budget; if exhausted → blocked/ + escalation entry
  4. HARVEST  for each WO newly in completed/:
                verify handover exists (else → blocked/, log defect)
                read completion_event  (TYPE ONLY — never content-for-meaning)
                create next WO from next_wo_template in the target role's inbox/
                copy input refs; set forbidden_same_session_as = this WO
  5. PREFLIGHT run mechanical checks: fingerprint match, window/register consistency,
              cost-model-name resolvable. On mismatch → HARD STOP the lineage,
              write an auto-finding, raise a DP entry
  6. PACKET   for each escalation with to_owner: render DP-NNN into
              queue/owner/decisions/pending/ (one decision per file, §8 format)
  7. RULED    for each file in decisions/ruled/: record the ruling verbatim,
              create the consequent WO, move the DP to archive
  8. BEAT     write heartbeat.json; commit + push all queue movements
  on any ambiguity at any step: STOP that lane, escalate, never guess
```

**What is absent from this algorithm is the point:** no branch reads an artifact to decide what it means. Every decision it makes is a lookup on type, existence, timestamp, or hash.

## 8. Minimal Owner interaction model

**The Owner has exactly three verbs.** Everything else is somebody else's.

| Verb | Where | Form |
|---|---|---|
| **DIRECT** | `queue/owner/objectives.md` | set or reorder objectives and priorities |
| **RULE** | `queue/owner/decisions/pending/` → `ruled/` | approve · reject · vary · Go/No-Go · typed §6 phrases |
| **HALT** | `ops/aro/PAUSE` (file exists ⇒ everything stops) | no cause required, no negotiation |

**The Owner never:** starts a session · tells a role what to do next · copies anything between participants · asks for a review · chases a blocker · reads a queue folder other than `decisions/pending/`.

**Decision packet, one file per decision:**
```markdown
# DP-014 · <decision> · RAISED <ts> · BLOCKS: <what>
**Decide:** one sentence.   **Why you:** which authority (§6 / Go-No-Go / ratification).
**What you're approving:** 3 bullets, plain language.
**Evidence:** <links>       **Prerequisites met:** CS review ✅ / IVF GREEN ✅
**If approved:** …          **If rejected:** …
**Recommendation + reasoning:** …
**Typed wordings:** ▸ APPROVE "…" ▸ VARY "…" ▸ REJECT "…"
```
Ruling = move the file to `ruled/` with the typed line appended. That single move is the entire interface.

**A DP that asks the Owner to run, route, relay, or chase is an ARO defect and a finding** — this is the machine-checkable form of "the Owner is not the message broker."

## 9. Migration plan (chat-relay → repository-first)

| Stage | What becomes true | Owner relay touches | Gate |
|---|---|---|---|
| **M0 — today** | queue folders + WO/handover/DP templates exist; humans move files by hand | unchanged, but all traffic is *in the repo* | none (adoptable now) |
| **M1** | ARO watcher runs: SCAN/PROMOTE/REAP/HARVEST/PACKET. Sessions still invoked by hand, but pull their own work | **internal relay → 0** | O1 certification |
| **M2** | Invocation automated (scheduler/supervisor); leases + SoD checks enforced at claim | Owner stops starting sessions | O2 drills + Owner gate |
| **M3** | **External participants onboarded as repo-capable sessions** — Chief Scientist, Independent Reviewer, Data Analyst pull from their own inboxes | **external relay → 0** | **Constitution §5.2 amendment** (relay-only → *writes only to its own review lane*) |
| **M4** | Full cycle; Owner drills armed; the three verbs are the whole interface | Owner = DIRECT, RULE, HALT | O3 |

**The shim, named with an expiry:** until M3, a non-repo-capable reviewer's output is pasted **once, by the Owner, into that role's `inbox/`** — and it is recorded as a *shim touch*, counted separately from governance touches, so the number visibly falls to zero rather than quietly becoming normal.

---
*Anchor: **nobody is told to start; everybody knows where to look — the queue is the instruction, the handover is the explanation, and the Owner's only inbox is the one holding decisions.***
