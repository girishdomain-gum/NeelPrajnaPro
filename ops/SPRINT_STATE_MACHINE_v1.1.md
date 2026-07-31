# SPRINT EXECUTION STATE MACHINE v1.1
*A mechanical specification of how a sprint runs from open to close, with every notation term defined, and an execution layer that says who runs it. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. Status: DRAFT for Owner review — proposed for NP-S2. Built from NP-S1's own failures; each mechanism in §7 names the failure it exists to prevent.*

**Human twin:** `SprintExecutionStateMachine_v1.1.docx` — same content, ten diagrams. **Build backlog:** `ops\WO-Q_ARO_implementation_ladder.md`.

**Written under NP-D-012:** this specification is intended to be sufficient to run a sprint without asking its author what it meant. Where it is not, that is a defect — raise a DEVQ.

---

## 1. NOTATION — every term used below

### 1.1 Structural tokens

| Token | Name | Definition |
|---|---|---|
| **P0…P8** | **Phase** | A named span of sprint execution with explicit entry conditions, exit conditions, a responsible role, and one concurrency class. A sprint is in exactly one phase at a time (except `PX`, which overlays). |
| **G1, G2** | **Gate** | An Owner decision point. **The only places a sprint waits on a human.** A gate is passed by a typed ruling recorded in the journal. |
| **PX** | **Overlay phase** | A long-running background phase that runs *alongside* P0–P8 rather than in sequence. |
| **PS** | **Stop state** | Sprint halted. Enterable by any role; exitable only by the Owner. |
| **→** | Transition | Automatic, on the exit condition being met. |
| **⇢** | Exception transition | Conditional; always writes a record. |
| **■** | Terminal | Phase or sprint ends here. |

### 1.2 Concurrency classes — the bar drawn on each phase

| Class | Meaning | Rule |
|---|---|---|
| `⟦SERIAL⟧` | **Exactly one role acts.** All others idle. | A second session claiming work in a SERIAL phase is refused. |
| `⟦PARALLEL⟧` | **Named roles act simultaneously on disjoint artifacts.** | Each role's write scope is declared and must not overlap another's. |
| `⟦WRITER⟧` | **Single-writer.** Exactly one session may append to `datastore/journal/`. | Structural, not a preference: the ledger is hash-chained, so two appending branches produce two chains and no valid merge exists. |
| `⟦BG⟧` | **Background.** Long-running; polled, not waited on. | Does not block any other phase. |

### 1.3 Role tokens

| Token | Role | Human? | Ledger write |
|---|---|---|---|
| **OWN** | Owner / Project Coordinator | **Yes — the only one** | never directly |
| **ARC** | Architect | no | never |
| **DEV** | Developer | no | only in `⟦WRITER⟧` phases, when assigned |
| **VAL** | Validator / IVF | no | **never** — verification writes reports, not records |
| **CSC** | Chief Scientist | no | never |
| **RTM** | Runtime Manager | no | never (produces observations) |
| **ARO** | *(Operational System, not a role)* | — | never |
| **WDG** | Watchdog *(proposed, Operational System)* | — | never |

*Roles are permanent; the model or session filling one is a temporary assignment. No token above names a model.*

### 1.4 Artifact tokens

| Token | Artifact | Written by | Purpose |
|---|---|---|---|
| **WO** | Work Order | ARO (or ARC) | routing envelope; carries a content artifact, never replaces it |
| **HO** | Handover | the role completing a WO | the next role's entire briefing; **no chat explanation may be required** |
| **DP** | Decision Packet | ARO | one Owner decision, self-contained |
| **ADR** | Architecture Decision Record | ARC | a sealed decision; ratified by OWN |
| **DEVQ** | Developer Question | any role | a blocking question; **stops that line of work** |
| **FND** | Finding | any role | recorded against a name, never softened |
| **PFR** | Preflight Report | ARC | P0's output; GREEN or a blocker list |

### 1.5 Branch and commit model — **this is the change from NP-S1**

| Term | Definition |
|---|---|
| **`main`** | **Untouched for the whole sprint.** Receives exactly one merge, at P8. |
| **`sprint/<id>`** | The **shared sprint branch** — e.g. `sprint/NP-S2`. Every session commits here, continuously. **This is the shared working directory**, in a form that survives a crash and is visible to every session. |
| **worktree** | A session's local checkout of `sprint/<id>`. Sessions share the branch, not the directory. |
| **push cadence** | **Commit early, push often.** Uncommitted means nonexistent — a session that has not pushed is invisible to every other session. |
| **contention** | On push rejection: `git pull --rebase`, then push. Git's atomic ref update is the lock; whoever pushes first wins. |
| **merge to main** | One `--no-ff` merge at P8, after G2. Sprint history is preserved; `main` never sees a half-finished state. |

**Why not "local directories, commit at close":** every collision in NP-S1 had one root cause — *a session could not see work that already existed*. Committing only at close makes that blindness structural for the whole sprint instead of accidental. The shared branch gives the same clean `main` and the same single sprint commit, without the blindness.

---

## 2. THE MACHINE

```
                    ┌─────────────────────────────────────────────┐
                    │  PS  STOPPED  ■                             │
                    │  entered by ANY role · exited by OWN only   │
                    └──────────────▲──────────────────────────────┘
                                   ⇢ (any phase, any time)

   P0 PREFLIGHT ⟦SERIAL⟧ · ARC
   ────────────────────────────────────────────────────────────────
   verify every precondition EXISTS before anything is built
   → PFR: GREEN, or a blocker list
   ⛔ a non-GREEN preflight does not open a sprint
                                   │
                                   ▼
   G1  SEAL ── OWNER GATE ── all sprint decisions batched here
   ────────────────────────────────────────────────────────────────
   OWN rules everything decidable now: designations, α-budget,
   cost models, claim forms, scope. One sitting, one record.
                                   │
                                   ▼
   P2 BUILD ⟦PARALLEL⟧ ═══════════════════════════════════════════
   ├── DEV  implementation                    scope: qrf/**, tests/**
   ├── VAL  drill harness + checker           scope: ivf/**
   │        ↑ BUILT FROM THE SPEC, BLIND TO THE IMPLEMENTATION
   ├── RTM  ingestion, manifests              scope: datastore/bulk/**
   └── ARC  registration YAML, interpretation scope: configs/**, ops/**
   ⛔ NO LEDGER WRITES IN P2 — by rule, enforced at review
                                   │
                                   ▼
   P3 CERTIFY ⟦PARALLEL⟧ ═════════════════════════════════════════
   ├── DEV  planted-truth + clean-control cases green
   └── VAL  drill self-test green (plants caught, control silent)
   ⛔ neither may proceed on the other's word — each certifies itself
                                   │
                                   ▼
   P4 REGISTER ⟦WRITER⟧ · one session, one branch  ────────────────
   all registrations land BEFORE any judgment (deflation counts at
   judgment time; a partial family prices the claim wrongly)
                                   │
                                   ▼
   P5 JUDGE ⟦WRITER⟧ · one session  ───────────────────────────────
   verdict + burn, atomic. The window is spent here.
                                   │
                                   ▼
   P6 VERIFY ⟦SERIAL⟧ · VAL  ──────────────────────────────────────
   runs the checker BUILT IN P2 — fast, because it already exists
   → GREEN / RED.   RED ⇢ P2 (with a finding) or ⇢ PS
                                   │
                                   ▼
   P7 REVIEW ⟦SERIAL⟧ ─────────────────────────────────────────────
   HC (OWN — a human, by rule) → REV (CSC)
                                   │
                                   ▼
   G2  CLOSE ── OWNER GATE ── Go / No-Go + retro decisions
                                   │
                                   ▼
   P8 CLOSE ⟦SERIAL⟧ · ARC  ───────────────────────────────────────
   merge sprint/<id> → main (--no-ff) · §0 handover rewritten ·
   sprint outputs appended · findings tallied · branch retained  ■


   PX  BACKGROUND ⟦BG⟧  ── overlays P2…P7, never blocks them
   ────────────────────────────────────────────────────────────────
   long-running collection (e.g. NP-S2's months of R6 ticks)
   WDG/ARO polls; a stall raises a DP, not a wait
```

---

## 3. PHASE SPECIFICATIONS

| Phase | Entry condition | Owner | Exit condition | Fails to |
|---|---|---|---|---|
| **P0** | previous sprint closed; objective set | ARC | PFR is GREEN | PS (blockers listed) |
| **G1** | PFR GREEN | **OWN** | all decisions typed and journaled | PS |
| **P2** | G1 passed | DEV·VAL·RTM·ARC | every lane's DoD met + HO published | PS or DEVQ |
| **P3** | P2 complete | DEV·VAL | plants caught, controls silent, both lanes | ⇢ P2 |
| **P4** | P3 green | one assigned session | **all** registrations appended | PS |
| **P5** | P4 complete | one assigned session | verdict + burn appended atomically | PS |
| **P6** | P5 complete | VAL | report GREEN | ⇢ P2 or PS |
| **P7** | P6 GREEN | OWN then CSC | HC passed, REV filed | PS |
| **G2** | P7 complete | **OWN** | Go/No-Go typed | PS |
| **P8** | G2 = Go | ARC | merged, handover rewritten, outputs appended | — |

**Two gates, not four.** Everything decidable is decided at G1; everything else waits for G2. A mid-sprint decision is an **exception** that writes an interrupt record — permitted, but visible and counted, so drift toward "ask the Owner" is measurable.

---

## 4. THE STOP PROTOCOL (PS)

**Any role may STOP. Only the Owner may RESUME.** The asymmetry is deliberate: stopping is always safe, resuming is a judgment.

| | |
|---|---|
| **How** | write `ops/aro/STOP` containing: role · session identity · timestamp · **the rule or evidence it rests on** · what is unsafe to continue |
| **Effect** | all lanes finish their current commit and halt; no new WO is claimed; PX keeps running (stopping a months-long collection is destructive and needs its own decision) |
| **Required** | a STOP **must name a rule or a piece of evidence.** A STOP without one is itself a finding — this prevents defensive stops that cost more than they save |
| **Resume** | Owner deletes the file with a typed ruling recorded. **No role may resume its own STOP.** |
| **Never** | a STOP is never overridden by argument, only by an Owner ruling that addresses its stated basis |

---

## 5. WHAT RUNS IN PARALLEL, AND WHAT ONLY LOOKS LIKE IT

**Genuine parallelism exists in exactly two places: P2 and P3.** Everything else is serial by nature — you cannot certify before you build, judge before you register, or review before you judge. Do not engineer for parallelism that does not exist.

**The parallelism that matters most is not about speed.** In NP-S1 the IVF started after everything was finished, became the critical path, and then found a real defect that cost another round-trip. Building its checker **during P2, from the specification, blind to the implementation** does two things at once: it removes a phase from the timeline, and it makes the verification *stronger* — a checker written before the code exists cannot be contaminated by it.

---

## 6. SP2's CONCRETE GRAPH

```
        ┌── WO-P execution parity ──────────┐   DEV · Kernel-side
        ├── NPSU → RecordStore migration ───┤   DEV · independent
P0/G1 ──┼── windows.json ↔ WindowLedger ────┤   DEV · independent
        ├── VAL builds R6 ingestion checker ┤   VAL · blind
        └── LAB UNPAUSE RULING ─────────────┘   OWN · on no critical path
                                            ▼
                        PX: R6 COLLECTION ⟦BG⟧ (months)
                              gated on WO-P only (NP-D-011)
                                            │
                    OOS designation ────────┤  OWN · typed · BEFORE completion
                                            ▼
                        execution feedback → Performance Store
```

**Three tracks run from day one.** The Owner's unpause ruling gates only R6 collection, and NP-D-011 gates R6 behind WO-P — so WO-P and the migration proceed regardless of either. **NP-S2 has no judging phase**: P4–P6 are absent, and its exit is a designated, hashed, untouched dataset.

---

## 7. RISK REGISTER — every NP-S1 failure, and the mechanism that prevents its recurrence

| # | What happened in NP-S1 | Mechanism |
|---|---|---|
| 1 | Cost model, M5 scope and dataset didn't exist; discovered mid-flight | **P0 preflight** — existence is checked before the sprint opens |
| 2 | Lineage convention violated; caught by luck | **P0** includes convention checks against existing artifacts |
| 3 | Family string silently load-bearing on the α-budget | **P0** pins every registration constant before G1 |
| 4 | Four Owner round-trips, each stalling everything | **G1/G2 only**; mid-sprint decisions are counted exceptions |
| 5 | IVF idle all sprint, then the critical path | **P2 parallel lane**, blind-built |
| 6 | Sessions blind to uncommitted decisions (×4) | **shared sprint branch, continuous push** |
| 7 | Prompts referenced state the recipient couldn't fetch (×3) | **every WO names the commit that contains its inputs** |
| 8 | IVF branch cut before the merge it needed | **boot verifies a named commit is an ancestor**, else refuses |
| 9 | Ledger could have diverged across branches | **⟦WRITER⟧ phases** — P4/P5 only, one session |
| 10 | Registrations after judgment would misprice α | **P4 completes fully before P5 begins** |
| 11 | A session could review its own work | **SoD checked at claim**, refusal returns the WO |
| 12 | Design work interleaved with execution (15 docs) | **no design lane in P2**; design is a separate track between sprints |
| 13 | Eight "check logs" touches | **generated `STATUS.md`** on the sprint branch, refreshed each push |
| 14 | Verification pattern retyped, false negative | **patterns copied from the artifact**, ASCII-safe substrings (J-038) |
| 15 | Verbatim requirement without the quotable string | **instructions ship the string** (J-037 retro d) |
| 16 | Spec insufficient to reimplement | **NP-D-012** — insufficiency is a DEVQ against its author |

---

## 8. EXECUTION — WHO RUNS THE MACHINE

**v1.0 of this document drew the machine and never said who runs it.** It defined `ARO` and `WDG` in the notation and then used neither in any diagram — the same specification-versus-content inconsistency this programme has recorded findings about. The Owner caught it. This section is the correction.

**Half of the omission was deliberate and stays deliberate:** the machine is drawn so it works with a human doing the dispatch. A specification that only runs once a system is built is a specification you cannot start.

### 8.1 Where ARO sits

Roles write **content**. ARO moves **work**. The repository is split, and the split is enforced by write scope, not by good behaviour:

| Zone | Paths | ARO |
|---|---|---|
| **Operational** | `ops/aro/queue/**` · `handovers/**` · `leases/**` · `log/**` · `STATUS.md` · `OWNER_PACKET.md` | **may write** |
| **Scientific** | `datastore/**` · `docs/**` · `configs/hypotheses/**` · `qrf/**` · `ivf/**` · `.github/**` | **never writes** |

ARO reads **type, existence, timestamp and hash**. It never reads content for meaning — doing so would be reasoning, which it may not do.

### 8.2 Accountability

Sprint design → **Architect** · scientific validity → **Chief Scientist** · code correctness → **Developer** · verification → **Validator** · ratification and priorities → **Owner**.

**Operational execution stays with the Architect, with ARO as the instrument.** ARO is an Operational System: no epistemic standing, no dissent, no capacity to bear a finding. Making it accountable would create an accountability black hole — a skipped phase whose finding attaches to a script. **Findings attach to whoever built, invoked or trusted the machinery.** An AI takes the responsibility; a mechanism takes the work.

## 9. THE MACHINE, MADE EXECUTABLE

A transition is only mechanical if its exit condition can be evaluated without judgment. **Every check below is a file that exists or a string that matches.**

| Phase | Mechanical exit check | Then |
|---|---|---|
| P0 | `ops/preflight/PFR_<sprint>.md` exists and contains `RESULT: GREEN` | G1 |
| G1 | journal contains the sprint's seal entry | P2 |
| P2 | a `HANDOVER.md` exists under `ops/aro/handovers/` for every lane's WO | P3 |
| P3 | certification reports exist for detector and drill, both containing GREEN | P4 |
| P4 | `trial_count` records for the declared family total the expected number | P5 |
| P5 | ledger holds one verdict and one `window_burn` naming that verdict | P6 |
| P6 | the verification report contains GREEN and contains no RED | P7 |
| P7 | journal holds the HC entry and a review file exists | G2 |
| G2 | journal holds the Go entry | P8 |
| P8 | a merge commit on `main` has the sprint branch tip among its parents | closed |

**If an exit check cannot be written this way, the phase is not yet specified** — a defect to fix, not a gap for the executor to fill.

## 10. THE RUNBOOK

Executed literally, in order. When a script replaces the session doing this, the script is a **transcription, not a redesign**.

0. **BOOT** — pull the sprint branch with rebase. If `ops/aro/STOP` exists: write its contents to status, report, exit. Nothing else runs while it exists.
1. **SCAN** — rebuild state by walking the queue folders. The tree is the truth; any cache is regenerated, never trusted.
2. **PHASE** — evaluate the current phase's exit check (§9). Pass → advance the marker. Fail → leave it alone. Never interpret partial evidence.
3. **PROMOTE** — `waiting/ → inbox/` when every declared input path exists. Existence only, never an assessment of quality.
4. **REAP** — `active/ → inbox/` on lease expiry; log TIMEOUT, decrement retry budget; budget exhausted → `blocked/` plus escalation.
5. **HARVEST** — for each completion, verify the handover exists. Missing → `blocked/` plus a defect log; **a completion without a handover is not a completion.** Present → create the next WO from the declared template.
6. **PREFLIGHT** — fingerprint, register and window consistency, cost-model name resolvable. Any mismatch → hard stop that lineage plus an automatic finding.
7. **PACKET** — render exactly one file per Owner decision. Never bundle two.
8. **RULED** — for each decision moved to `ruled/`, record the typed wording verbatim and create the consequent WO.
9. **STATUS** — regenerate `STATUS.md` from the tree.
10. **BEAT** — heartbeat, commit, push. **An unpushed cycle did not happen.**

**At any step, if the answer is not mechanical: stop that lane, escalate, never guess.**

## 11. ADOPTION — AND WHY THE ORCHESTRATOR IS A SCRIPT

Four stages, each independently useful, none requiring the next. Full milestone ladder with drills: `ops\WO-Q_ARO_implementation_ladder.md`.

| Stage | What changes | Owner touches |
|---|---|---|
| **0 · manual** | phases named, a human moves files, preflight in force | ~30 |
| **1 · status** | a script *reads* and writes `STATUS.md`; cannot do harm | ~20 |
| **2 · routing** | the script moves work orders, detects stalls, builds packets | ~10 |
| **3 · dispatch** | sessions invoked automatically; leases and SoD enforced at claim | 4–6 |

**Stage 1 is the highest-return step in the whole design** — roughly fifty lines, read-only, and it removes the eight "check logs" touches outright.

> ### If the orchestrator ever needs intelligence, the specification is wrong.

Every step in §10 is a lookup on type, existence, timestamp or hash. None needs understanding, and that is the specification rather than an accident. A session in that seat imports four problems and solves none: it will route on **content** (reading a question and deciding what it is *really* about — forbidden, and undetectable afterwards) · it loses **replayability**, since a script's dispatch log reproduces deterministically from the same repo state and a session's does not · it accumulates **context drift** across a sprint, the failure that made disposable workers the ratified pattern · and it **fails badly**, because a crashed script is loudly dead and restartable from repo state while a confused session is quietly wrong.

**Measured cost of stage 0:** NP-S1 was orchestrated by hand, by an Architect session, with no automation and no persistent state. It worked, and it cost the Owner roughly thirty touches. Viable, and expensive.

## 12. WHAT THIS DOES NOT FIX

**The Owner's judgment load has a floor and this machine does not lower it.** HC requires a human by rule; ratifications, designations, α-budgets, Go/No-Go and arming are Constitution §6. Roughly four to six touches per sprint, and that is the system working.

**The real lever is elsewhere:** after every Owner decision, ask *"could a rule have made this mechanical?"* Three of NP-S1's eight judgment touches — the trial count, the lineage name, the cost figure — could have been rules instead of rulings. **Decision load falls when the rulebook grows, not when the plumbing improves.**

---

## DOCUMENT HISTORY

- **v1.1 (2026-07-30)** — execution layer added after the Owner caught that v1.0 defined the ARO and Watchdog tokens and then used neither, and never said who runs the machine. New §8 (where ARO sits, write scope, accountability), §9 (mechanical exit checks), §10 (the runbook), §11 (adoption, and why the orchestrator is a script). Accountability split refined per Chief-Scientist-style review, with one row declined: operational execution stays with the Architect, because a script cannot hold a finding. Build backlog issued separately as WO-Q. **The correction is recorded rather than made silently.**
- **v1.0 (2026-07-30)** — first draft: notation, the machine, phase specifications, STOP protocol, parallelism, SP2's graph, risk register.

---
*Anchor: **phases say when, concurrency bars say who may act at once, the single-writer bar says where the ledger may be touched — and the shared branch says that nothing anyone did is invisible to anyone else.***
