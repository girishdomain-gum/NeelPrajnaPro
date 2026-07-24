# QRF Multi-AI Coordination Protocol v1.0

**Status:** Accepted (ADR-008) · 2026-07-24
**Purpose:** written, auditable 1-to-1 communication between roles, with
history. Chat is scratch; files are the record.

## Roles

| Role | Held by | May | May NOT |
|---|---|---|---|
| Owner | Girish (human) | scope, priorities, sign-offs, final say | be bypassed on Go/No-Go |
| Architect | Fable (Claude chat) | write instructions, answer questions, review code, propose ADRs | write implementation code in sprints assigned to Developer |
| Developer | Claude Code (or any AI in the repo) | implement per instruction, write tests, ask questions, write notes | change architecture, Blueprint contracts, ADRs, or any file under docs/ except coordination inbox/notes |
| Verifier | IVF tools + Owner | run checks, sign checklists | be skipped at sprint close |

**The one-direction rule:** Developer finds an architecture problem →
writes a DEVQ → Architect decides → (if needed) ADR → docs updated by
Architect. Developers never edit architecture, ever.

## Document IDs and homes

| Prefix | Meaning | Lives in |
|---|---|---|
| ARCH-NNN | Instruction, architect → developer | `instructions/` |
| DEVQ-NNN | Question/blocker, developer → architect | `inbox/OPEN/` → `inbox/CLOSED/` |
| REV-SN | Architect review of a delivered sprint | `reviews/` |
| NOTE-NNN | Implementation discovery, FYI only | `notes/` |
| ADR-NNN | Decision (the only home for decisions) | `docs/adr/` — referenced by number, never restated |
| VERIFY / drills | Verification results | IVF outputs + ledger records — referenced, never restated |

## Levels (exactly three)

- **FYI** — no reply needed (all NOTEs).
- **QUESTION** — reply needed; work on other tasks may continue.
- **BLOCKER** — reply needed; STOP work on the affected task. If the
  whole sprint is blocked, stop the sprint and say so in the file.

## Thread format (one file per thread, reply appended)

```markdown
# DEVQ-003 · QUESTION · Sprint 1 · 2026-07-26
Author: developer (claude-code)
Refs: Blueprint §4.1, ARCH-001

## Question
<what is unclear, observed vs expected, exact file/line>

## Options considered
A) ...   B) ...
Recommendation: B

---
## REPLY · architect (fable) · 2026-07-26
Decision: B. Reason: ... Architecture impact: none | ADR-NNN raised.
Status: CLOSED
```

On CLOSED, the developer (or owner) moves the file to `inbox/CLOSED/`.
One thread = one topic. New topic = new file, next number.

## Instruction format (ARCH files)

Every ARCH instruction is self-contained: the Developer has no memory
between sessions and must be able to work from the instruction plus the
referenced docs alone. Mandatory sections: Read first · Scope ·
Out of scope · Deliverables (exact paths) · Key contracts (inline the
normative bits) · Acceptance criteria · Required tests · Definition of
Done · How to ask.

## Escalation

QUESTION unanswered when needed → raise to BLOCKER in the same file.
Suspected architecture bug → BLOCKER + tag `architecture-conflict`;
Architect must reply with either a clarification or a Proposed ADR.
Owner may close anything at any time.

## Hygiene

- Filenames: `ID_short-slug.md`. Dates ISO. UTF-8.
- Reference by ID; never copy contract text between files (drift risk) —
  the Blueprint is the single source for contracts.
- Coordination files are append-and-move only; do not rewrite history.
