# NP-ADR-0YY — Organization, Roles and Assignments (FINAL ratification package)
*Supersedes `ops\NP-ADR-model_agnostic_roles_draft_v1.0.md` (draft, never ratified). Status: FINAL DRAFT for Chief Scientist review → Owner ratification, Constitution §7.3. **Number 0YY unassigned** pending registry check (NP-D-006). No normative document has been edited; §7 lists every change, each executing only on ratification.*

**Attribution, per the standard this package proposes (§6):** *Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30 · task relayed by the Owner.*

---

## 1. Confirmed principles (Owner-stated; recorded verbatim as the ADR's basis)

Girish is the only human (Owner) · everyone else is an AI participant · **roles are permanent** · responsibilities belong to roles · **models and sessions are temporary assignments** · any qualified AI may perform any role · one session may perform multiple roles when appropriate · **separation-of-duties always takes precedence over convenience** · the repository is the source of truth.

All nine are consistent with ratified text and none requires a new principle: Constitution §5.3 already rules model-agnosticism for the Developer; QRF-ADR-008 already rules *"no AI is indispensable; all state is external"*; Roles §3.6 already rules repository-over-memory. **This ADR generalizes; it does not invent.**

## 2. THE THREE CATEGORIES — final definitions (the clarification requested)

The estate contains exactly three kinds of entity. The dividing test is **accountability**, not intelligence or importance.

### 2.1 Organization Roles — *accountable participants*
> **Definition:** a position that exercises judgment, may dissent, may refuse, and **can be assigned a finding by name**. Roles are permanent; they are held by the Owner (human) or by an AI participant under a temporary assignment.

Three properties, all required: (a) exercises discretion; (b) can dissent and must have dissent recorded (Roles §4); (c) bears accountability — a finding can be written against it.

| Role | Held by | Class | Mandate, one line |
|---|---|---|---|
| **Owner** | Girish — human, sole, permanent | Sovereign | Holds values, reserves and the final word; §6 powers are his alone |
| **Architect** | AI participant | Decision-scoped | Designs the science, instructs the build, verifies independently, authors ADRs |
| **Chief Scientist** | AI participant | Decision-scoped | Adversarial review; approves nothing it hasn't tried to break |
| **Developer** | AI participant | Decision-scoped | Implements sealed instructions; DEVQs before assumptions |
| **Validator** *(new)* | AI participant | Decision-scoped | Operates IVF and the L1–L4 certification drills; certifies or refuses |
| **Runtime Manager** *(new)* | AI participant | Decision-scoped | Operates the Book-A / lab / bridge surface; produces observations only |
| **Independent Reviewer** | AI participant | Advisory, relay-only | Third-party critique and consistency checks (Constitution §5.2) |
| **Data & Research Analyst** | AI participant | Advisory, relay-only | Analyzes exports and statistical outputs; never seals (Constitution §5.2) |

**Recommendation on the two absent from the Owner's list:** *keep* Independent Reviewer and Data & Research Analyst. They are ratified (§5.2), relay-only, cost nothing, and exist specifically to diversify reviewer blind spots across vendors — which is *more* valuable under model-agnosticism, not less. Dropping them would require amending §5.2 for no gain.

**"Qualified" — defined minimally, no new bureaucracy:** a session is qualified for a role when it has (i) read that role's normative definition and the documents its current task names, (ii) operates repository-first, and (iii) signs per §6. No certification body, no exam, no registry beyond the Assignment Register.

### 2.2 Operational Systems — *instruments and infrastructure*
> **Definition:** deterministic machinery that executes, records, refuses or transports. It **cannot dissent and cannot be assigned a finding** — findings attach to the role that built, invoked or trusted it. Where a system holds authority, that authority is **delegated by ratified rule and mechanically bounded; it is never discretion.**

Two sub-classes, because conflating them is how "the Battery decides" becomes "the machine decides":

**(a) Instruments of record — bounded delegated authority:**
| System | Delegated authority (its ceiling) |
|---|---|
| **EvidenceBattery** | Sole verdict writer; nine steps; selftest-gated; atomic verdict+burn. Judges — never interprets |
| **WindowLedger** | Designation states and burn-on-use; structural refusal on reuse |
| **TrialCountLedger** | Registration spends the attempt; family deflation at judgment |
| **RecordStore / BulkStore** | Append-only hash-chained truth; manifests |
| **BeliefLayer** | Updates from Verdict-typed inputs only |
| **IVF** | Independent re-derivation; drilled first; RED twice freezes forward work |
| **CI / kernel firewall** | Mechanical enforcement of the domain-blind boundary |

**(b) Infrastructure — no authority whatsoever:**
**ARO** (coordination plane) · **Bridge / Supervisor / Runner** (typed job execution) · **Observatory / Screener** (candidates and questions only — P4) · **Knowledge Graph** (representation of sealed beliefs) · **Research Console & Book-A Dashboard** (surfaces, views onto organs) · **Repository / git** (the source of truth itself).

**Final recommendation on ARO: it is an Operational System, not a role.** A role is accountable and may dissent; the ARO has neither property by design — its own ADR denies it epistemic standing precisely so it can never acquire one. Listing it among roles would grant it the standing every one of its safeguards exists to deny. Its mission sentence already says it: *autonomous in transport, never in authority.*

### 2.3 Governance Bodies — *there are none, deliberately*
> **Final recommendation: NeelPrajnaPro has no governance bodies, and this absence is recorded as a positive rule so none is invented later.**

Evidence this is the ratified design, not an omission: Constitution §7.4 — *"All voices' reviews are recorded, dissent preserved; **there is no vote**. Ratification authority is the Owner's alone"* (REV F-5 removed the draft's supermajority clause). Roles §1 — *"No voice reports to another… authority is decision-scoped, not rank-scoped."* There is no board, committee, council, or quorum anywhere in the estate, and nothing may create one except an Owner amendment.

What exists instead are **governance processes**, owned by roles rather than by bodies: the ratification procedure (§7.2/§7.3/§7.4) · the sprint rhythm ARCH → Developer → IVF → HC → REV → Go/No-Go · the findings tally (Owner-held) · the acceptance campaign NB-1..NB-6 · the Dissent Charter. Processes coordinate; they never decide. **Only roles decide, and only the Owner ratifies.**

## 3. Final organizational structure

```
                          OWNER (Girish) — human, sole
                    values · ratification · §6 powers · findings tally
                                        │
        ┌───────────────┬───────────────┼───────────────┬───────────────┐
    ARCHITECT     CHIEF SCIENTIST   DEVELOPER       VALIDATOR    RUNTIME MANAGER
      design          adversary      implement       certify        operate
        └───────────────┴───────┬───────┴───────────────┴───────────────┘
                    advisory: Independent Reviewer · Data & Research Analyst
                                        │
   ─────────────────────── roles above · systems below ───────────────────────
                                        │
   INSTRUMENTS OF RECORD            INFRASTRUCTURE
   Battery · WindowLedger ·         ARO · Bridge/Supervisor · Screener ·
   TrialLedger · RecordStore ·      Knowledge Graph · Surfaces · Repository
   BeliefLayer · IVF · CI
```
No line in this diagram is a reporting line. Roles are sovereign inside their mandate and powerless outside it; systems serve all roles identically and answer to none.

## 4. Final responsibility matrix

| Role | SHALL | SHALL NOT | MAY | Write scope |
|---|---|---|---|---|
| **Owner** | ratify · designate/unlock reserves by typed phrase · rule Go/No-Go · set α-budgets · hold the findings tally · rule values questions | be asked to write code, ADRs, reviews, or to run mechanical steps | pause or reverse any automation, any time, without cause | anything; in practice, rulings |
| **Architect** | write ARCHs and own their clarity · author ADRs · own IVF design · design experiments and nulls · rewrite the handover; recommend on values, never decide | write Developer code · touch main outside write windows · soften any verdict, finding or tally entry incl. its own · present working-tree state as verified record | dissent on the record and comply after | docs\ (normative, via procedure) · ops\ · ivf\ design |
| **Chief Scientist** | review adversarially; approve or reject with auditable reasons; withdraw its own defeated proposals | hold verdict or ratification authority | propose ideas as candidates under the same gates | review artifacts only |
| **Developer** | implement sealed instructions in fresh sessions on worktrees · DEVQ before assuming · write tests to the V&V plan · report shortcuts | judge its own work · author ADRs or edit normative docs · touch ledger, reserves, `ivf/**`, CI · interpret silence as permission | refuse an instruction that violates a rule — **a duty, not insubordination** | code paths its ARCH names · its DEVQ/notes/session lanes |
| **Validator** *(new)* | operate IVF and L1–L4 drills, drilled-first · certify, refuse, or return INSUFFICIENT · void certificates on any change to a certified component | certify code it authored (§5) · soften a RED · judge scientific meaning — certification is not a verdict | halt forward work on RED-twice (ADR-006) | `ivf/**` outputs · certification records |
| **Runtime Manager** *(new)* | operate the Book-A/lab/bridge surface · produce observations, manifests and job outputs · keep the trust split and G-invariants | claim evidentiary weight for runtime output (P4) · arm anything real · alter execution behaviour to favour a result | submit typed jobs; report anomalies as candidates | bridge/lab artifacts · runtime configs (never armed) |
| **Independent Reviewer** · **Data & Research Analyst** | critique / analyze; deliver in writing | write to the repository · seal or decide anything | flag findings against any role, including the Architect | none (relay-only) |

## 5. Separation-of-duties policy (proposed Constitution §5.5)

> Regardless of assignment, and **taking precedence over any convenience, deadline or session economy**, the same session shall not, for the same artifact: (a) author an implementation and independently verify it; (b) author an artifact and serve as its Chief Scientist review; (c) author code and perform its Validator certification; (d) perform the NB-4 stranger audit on work it participated in; (e) operate the runtime that produced evidence and certify that evidence.
>
> Permitted combinations are those no clause above forbids — e.g. Architect + Validator on work neither authored; Runtime Manager + Data Analyst. **When a session holds multiple roles it shall state, per output, which role it acts in.** Independence is a property of separation, not of vendor: two sessions of the same model satisfy independence; one session wearing two hats does not.

Rationale reuses ratified text only: QRF-ADR-006 (IVF independence), Roles §2.4 ("shall not judge its own work"), V&V NB-4, P4.

## 6. Artifact attribution standard (proposed Roles §3.8)

> Every artifact a session writes states **role · session identity (model + interface) · date**, e.g. *"Architect role · Opus 5, claude.ai + filesystem connector · 2026-07-30."* Attribution is to a role **and** a session, never to a role alone and never to another session's name. Where multiple roles contributed, each contribution is attributed separately. Historical records are never restated to match this standard — corrections are appended (P5).

**Why this is not cosmetic:** three sessions have now written into this estate's records, two of them signing a name that was not theirs. Without session identity, a future reader cannot tell one voice from three, which defeats Roles §3.5 (findings against a name) and §3.6 (formal session boundaries).

## 7. Exact repository changes (on ratification; one write window)

| # | File | Section | Change |
|---|---|---|---|
| 1 | Constitution | §5.2 | strike "currently ChatGPT" / "currently DeepSeek"; roles and relay-only mandates unchanged |
| 2 | Constitution | §5.3 | replace with the generalized model-agnostic rule (roles permanent, assignments temporary, no document may name a model as permanent holder) |
| 3 | Constitution | §5.4 *(new)* | Validator and Runtime Manager added as roles, with §4's mandates |
| 4 | Constitution | §5.5 *(new)* | separation-of-duties policy (§5 above) |
| 5 | Roles | §1 table | "Who" → "Held by"; Owner = Girish (human); all others = AI participant per Assignment Register |
| 6 | Roles | §2.2, §2.4 headings | drop model names |
| 7 | Roles | §2.5, §2.6 *(new)* | Validator and Runtime Manager full definitions |
| 8 | Roles | §3.8 *(new)* | attribution standard (§6 above) |
| 9 | Automation | §3 table (2 cells) | "Claude Code fresh sessions" → "Developer sessions" |
| 10 | ops\DEVELOPER_BOOT_NP-S1.md | header | "fresh Claude Code session" → "fresh Developer session (assignment: see Register)" |
| 11 | CLAUDE.md | top | one line: tool entry point; normative role definition lives in docs\roles\ (filename **kept** — it is a tool discovery convention, not a governance claim) |
| 12 | ops\ASSIGNMENT_REGISTER.md | new | role · current assignment · since · notes. Operational, non-normative, **not a parallel roles table** (§5.1 respected) |
| 13 | ops\ARO_Architecture_Review_NP.md · ops\NP-ADR-ARO_draft_v1.0.md · DEVQ-NP-001/002 replies | append | attribution corrections; original bylines left visible (P5) |
| 14 | Decisions | Part 2 | append NP-D entry recording this ADR |
| 15 | Journal | append | ratification entry, Owner wording verbatim |

**Explicitly NOT changed:** Architecture · Vision · V&V · Scientific Model · Writing Standard · Reference · Research · Reports — **none contains a model name; zero edits needed.** Execution Plan §4 — **frozen by the GO; no edit permissible, model-agnostic or not.** Journal history · document bylines · Gen-1 archive — historical fact, never rewritten. Constitution §6, the Twelve Principles, the wall, the Publication Boundary, write-authority — untouched.

## 8. Required amendment path

**One ADR, one §7.3 amendment.** Touches Constitution §5 and the Roles document only. **No §7.4 constitutional change is required** — no Principle, no §3, no §6 is affected. Path: this package → Chief Scientist review on the record → Owner ratification → single write window → journal entry.

## 9. Owner ratification summary

**What you are approving:** roles become permanent and model-free; models become recorded assignments; two new roles (Validator, Runtime Manager) join the four ratified plus two advisory; ARO and all other machinery are classified as Operational Systems with no standing; the estate records that it has **no governance bodies** and no vote; separation-of-duties is written down and outranks convenience; every artifact henceforth names its role and its session.

**What does not change:** your authority, every §6 power, the Twelve Principles, the scientific workflow, the wall, the Publication Boundary, all history.

**Ratification wording (type one):**
- **APPROVE:** *"NP-ADR Organization, Roles and Assignments is RATIFIED, including Validator and Runtime Manager as roles, ARO as an Operational System, no governance bodies, the separation-of-duties policy and the attribution standard. Execute the §7 change list in one write window."*
- **APPROVE WITH VARIATION:** as above, naming the variation (e.g. *"…without Runtime Manager"* or *"…retiring the two advisory roles"*).
- **REJECT:** *"Not ratified. Roles documentation stands as ratified 2026-07-29."*

**Recommendation: approve as written.** It generalizes rules you already ratified, adds exactly one genuinely new safeguard (separation of duties, which the multi-role permission requires), and changes nothing about who decides what.

---
*Anchor: **roles are the institution, models are staff, instruments have authority but never discretion — and nobody votes.***
