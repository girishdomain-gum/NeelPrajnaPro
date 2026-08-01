> **SUPERSEDED 2026-07-30 by `ops\NP-ADR-organization_and_roles_v1.0.md`** (the final ratification package). Retained for provenance only — never ratified, never cited. Read the successor.

# NP-ADR-0YY (DRAFT, SUPERSEDED) — Model-Agnostic Roles: roles are permanent, assignments are temporary
*WORKING RECORD — Architect-role draft, 2026-07-30, for Chief Scientist review and Owner ratification via Constitution §7.3. **Number 0YY unassigned** pending registry check (NP-D-006 collision discipline). No normative document has been edited by this draft; every change below executes only after ratification.*

**Authorship, stated in the convention this ADR proposes:** *Architect role · session: Opus 5, claude.ai interface with filesystem connector · 2026-07-30 · task relayed by the Owner.* This is not the session that authored the ratified estate; see §7.

---

## 1. What the Owner ruled (restated for the record)

NeelPrajnaPro has **one human: Girish (Owner)**. Every other participant is an **AI team member**. Roles, responsibilities and governance are permanent; **AI models and sessions are temporary assignments**. Any model or session may perform any role if assigned; a session may temporarily hold more than one role. The repository must never depend on a specific model.

## 2. Evidence — the principle is already half-ratified

- **Constitution §5.3 (ratified 2026-07-29):** *"Which underlying model powers a session is an operational detail and confers no change in the Developer's shall/shall-nots. The 'Sonnet + Claude Code partnership' framing of draft v1.0 is retired."* The rule exists; it is scoped to one role.
- **QRF-ADR-008 (ratified):** *"No AI is indispensable; all state is external."* The architectural ancestor.
- **Roles §3.6:** *"the repository — not any session's memory — is the single source of truth."*
- **Constitution §5.2:** already hedges with *"currently"* before each external model name.

**Therefore this ADR is a generalization, not a new principle** — which is why it travels as §7.3 (amendment to §5) and not §7.4 (no Principle, no §3, no §6 is touched).

## 3. Change inventory — every place a model name appears

**Legend:** *Change* = edit on ratification · *Keep* = leave, with reason · *Register* = move the volatile fact to the Assignment Register (§5).

| # | File | Location | Current | Disposition |
|---|---|---|---|---|
| 1 | Constitution v2.0 | §5.2 Amendment A | "Independent Reviewer (external AI, **currently ChatGPT**)" · "Data & Research Analyst (external AI, **currently DeepSeek**)" | **Register** — strike the parenthetical model, keep the role and its relay-only mandate |
| 2 | Constitution v2.0 | §5.3 Amendment B | "the Developer is **Claude Code**, one fresh session per task" | **Change** — "the Developer works in fresh sessions, one per task, on worktrees"; generalize the model-agnosticism sentence to all roles (§4 text) |
| 3 | Constitution v2.0 | header byline | "Authored by **Fable** (Architect)" | **Keep** — authorship is historical fact (P5). Add nothing; do not rewrite history |
| 4 | Roles v1.0 | §1 four-voice table | "Architect \| **Fable** (AI, chat session)" · "Developer \| **Claude Code** (AI, fresh session per task)" | **Change** — column "Who" becomes "Held by"; entries become "AI team member, assigned (see Assignment Register)"; Owner row unchanged: "Girish (human)" |
| 5 | Roles v1.0 | §2.2 heading | "Architect (**Fable**)" | **Change** → "Architect" |
| 6 | Roles v1.0 | §2.4 heading | "Developer (**Claude Code**)" | **Change** → "Developer" |
| 7 | Roles v1.0 | §2.4 body | "the Gen-1 precedent stands: *the Developer once declined…*" | **Keep** — historical precedent, no model named |
| 8 | Automation v1.0 | §3 table, both rows | "**Claude Code** fresh sessions per ARCH-NP" | **Change** → "Developer sessions per ARCH-NP" |
| 9 | Execution Plan v2.0 | §4 boot sequence | "Developer session boots…" | **Keep** — already role-generic **and §4 is FROZEN by the GO (T-036): no edit is permissible, model-agnostic or not; a change requires a new ARCH** |
| 10 | ops\DEVELOPER_BOOT_NP-S1.md | header | "Hand this file's contents to a fresh **Claude Code** session" | **Change** (working record, freely editable) → "a fresh Developer session (current assignment: see Register)" |
| 11 | CLAUDE.md (repo root) | filename | Claude Code's discovery convention | **Keep — deliberately.** This is a *tool integration point*, not a governance claim; renaming breaks tool discovery and buys nothing. Body already reads "Standing Orders for the Developer AI". Add one line: "This file is a tool entry point; the normative role definition is docs\roles\." (Its stale Gen-1 paths remain WO-A's job) |
| 12 | Decisions v1.0 | byline; QRF-ADR-008 | "Author: **Fable**"; "No AI is indispensable" | **Keep** — byline is history; ADR-008 is the supporting citation |
| 13 | Journal (all entries) | J-001…J-033 | names Fable, Claude Code, DeepSeek, ChatGPT throughout | **Keep — mandatory.** The journal is append-only (P5, NP-D-009). Sanitizing it would be a rewrite of history and a finding against whoever did it. Historical entries record *who actually acted*, which is exactly what the register model preserves |
| 14 | ops\ARO_Architecture_Review_NP.md · ops\NP-ADR-ARO_draft_v1.0.md | bylines | "Author: **Fable** (Architect)" | **Change (correction, append-only)** — these were authored by an Opus 5 claude.ai session, not by the session named. False attribution; corrected per §7 |
| 15 | docs\coordination\inbox\OPEN\DEVQ-NP-001/002 (worktree branch) | reply signatures | "— **Fable** (Architect)" | **Change (correction, append-only)** — written by a session other than the one named; same defect, same remedy |
| 16 | THE_ONE_PAGE.md | "findings… pointing at me… today I earned two" | first-person Architect voice, no model named | **Keep** — model-agnostic already. Note only: first person presumes one continuing voice; under this ADR it reads as "the Architect role" |

**Not found anywhere:** model names in Architecture, Vision, V&V, Scientific Model, Writing Standard, Reference, Research, or Reports masters. Those documents are already model-agnostic and need **no changes at all** — the blast radius is two normative documents plus working records.

## 4. Proposed amendment text (drop-in)

**Constitution §5.3 replaced by §5.3 (Amendment B, generalized):**
> **Roles are permanent; assignments are temporary.** Every role in the ratified Roles document is held by an AI team member except the Owner, who is human and whose powers are §6. Which model or session holds a role at any time is an operational assignment, recorded in the Assignment Register, and confers no change to that role's shall/shall-nots. No normative document shall name a model as a permanent role holder; no workflow, test, or record shall depend on the identity of the model performing a role. A session may hold more than one role **only where no separation-of-duties invariant (§5.5) forbids the combination.**

**New Constitution §5.5 — Separation of duties (the safeguard that makes multi-role safe):**
> Regardless of assignment, the following may never be performed by the same session for the same artifact: (a) authoring an implementation and independently verifying it (QRF-ADR-006; Roles §2.4 "shall not judge its own work"); (b) authoring an artifact and serving as its Chief Scientist review; (c) authoring code and performing its Validator/IVF certification; (d) performing the NB-4 stranger audit on work the session participated in. Where a combination is permitted, the session states which role it acts in for each output. **Model-agnosticism does not dilute independence: independence is a property of separation, not of vendor.**

**Roles §1 table, "Held by" column:** Owner — Girish (human). Architect · Chief Scientist · Developer · [Validator] · [Runtime Manager] — AI team member, per the Assignment Register.

**Roles §3.8 (new):** *Every artifact a session writes states its role and its session identity (model, interface, date). Attribution is to a role and a session, never to a role alone.*

## 5. The Assignment Register (how volatile facts leave the frozen documents)

`ops\ASSIGNMENT_REGISTER.md` — operational, non-normative, append-only, updated by whoever changes an assignment. Columns: role · current assignment (model + interface) · assigned since · notes. **It is not a parallel roles table** (Constitution §5.1 forbids that): roles and mandates live only in the Roles document; the register carries only *who is doing it today*. Zero epistemic standing, like all ops\ metadata.

## 6. Three questions the Owner's list raises (flagged, not assumed)

1. **Two roles are new.** *Validator* and *Runtime Manager* do not exist in the ratified Roles document. Validation is currently performed by machinery (IVF, Battery, L1–L4 drills), not by a voice; runtime operations sit with the bridge/Supervisor. Ratifying them means drafting their shall/shall-nots to the same standard as the existing four. **Recommendation:** define *Validator* as the role that operates IVF and the certification drills (with §5.5(c) barring it from certifying its own code), and *Runtime Manager* as the role that operates the Book-A/bridge lab surface (with no evidentiary authority whatsoever — its outputs are observations, per P4). Draft text on request.
2. **Two ratified roles are missing from the list:** Independent Reviewer and Data & Research Analyst (Constitution §5.2). Are they retired, or merely unlisted? Silence would leave §5.2 contradicting the new list — a finding waiting to happen.
3. **ARO is listed as a role; the pending ARO ADR deliberately defines it as *non-voice machinery*.** Recommendation: **keep it machinery.** A role is accountable and may dissent; the ARO has no epistemic standing and cannot bear accountability. Listing it as a role would grant it standing the safeguards were built to deny. If the Owner prefers it listed, the ARO ADR's §5 must be reopened, not quietly reinterpreted.

## 7. Attribution correction carried by this ADR

Two ops artifacts and two DEVQ replies are signed with a role-holder name by sessions other than the one named (inventory rows 14–15). Under P5 the remedy is **appended correction, never rewrite**: each file gains a note stating true authorship, with the original byline left visible. This ADR's own header demonstrates the proposed convention. **Finding recorded against the sessions that signed another's name, including this one.**

## 8. One consequence the Owner should see before ratifying

Making every non-Owner participant an AI does not remove the estate's human-required steps — it **concentrates them on the Owner**. HC ("HC without a human is just another VC", QRF-ADR-009b), NB-6's human-led interpretation sweep, NB-4's stranger audit, and the Owner drills of QRF-ADR-010b all require a human, and there is now exactly one. This is not an objection; it is the load-bearing consequence, and it strengthens the case for the ARO's packet (one place where that concentrated human attention is spent).

## 9. Governance path

§7.3 amendment: **this draft → Chief Scientist review on the record → Owner ratification.** Then one write window executes rows 1, 2, 4, 5, 6, 8, 10, 11, 14, 15 plus the register and a journal entry. **Row 9 (Execution Plan §4) executes never** — it is frozen by the GO. Constitution §6, the Twelve Principles, the wall, the Publication Boundary, the write-authority list, and every scientific workflow are untouched by this ADR.

---
*Anchor: **the roles are the institution; the models are staff. Independence is a property of separation, not of vendor.***
