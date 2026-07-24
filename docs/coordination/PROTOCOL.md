# QRF Multi-AI Coordination Protocol v1.1

**Status:** Accepted (ADR-008; v1.1 per NOTE-008) · 2026-07-24
**Purpose:** written, auditable 1-to-1 communication between roles, with
history. Chat is scratch; files are the record. Consoles are chat.

## Roles

| Role | Held by | May | May NOT |
|---|---|---|---|
| Owner | Girish (human) | scope, priorities, sign-offs, final say | be bypassed on Go/No-Go |
| Architect | Fable (Claude chat) | write instructions, answer questions, review code, propose ADRs | write implementation code in sprints assigned to Developer; write while a Developer session is active |
| Developer | Claude Code (or any AI in the repo) | implement per instruction, write tests, ask questions, write notes + session logs | change architecture, Blueprint contracts, ADRs, or any file under docs/ except coordination inbox/notes/sessions and the state file via gen_state |
| Verifier | IVF tools + Owner | run checks, sign checklists | be skipped at sprint close |

**The one-direction rule:** Developer finds an architecture problem →
writes a DEVQ → Architect decides → (if needed) ADR → docs updated by
Architect. Developers never edit architecture, ever.

## Document IDs and homes

| Prefix | Meaning | Lives in |
|---|---|---|
| ARCH-NNN | Instruction, architect → developer | `instructions/` |
| DEVQ-NNN | Question/blocker, developer → architect | `inbox/OPEN/` → `inbox/CLOSED/` |
| REV-SN / GO-SN | Architect review / Owner Go-No-Go record | `reviews/` |
| NOTE-NNN | Discovery, FYI only | `notes/` |
| S{n}-{seq} | Developer session log (NEW, v1.1) | `sessions/` |
| ADR-NNN | Decision (the only home for decisions) | `docs/adr/` — referenced by number, never restated |

ID allocation: only after `git fetch origin`, checking main AND open
branches for the highest number (NOTE-005).

## Session logs (NEW in v1.1 — the no-console rule)

At every session END and at every STOP, the Developer writes
`sessions/S{sprint}-{seq}_{YYYYMMDD}.md`:

```markdown
# S3-1 · session log · 2026-07-25 · developer (claude-code)
Instruction: ARCH-003 · Branch: <name> · Pushed through: <commit>
DONE: …            IN-PROGRESS: …
BLOCKED-ON: <DEVQ-NNN or "-">      NEXT: …
Tests: <n> passed · ruff <clean/red> · journal <n> records
```

Commit + push the log before ending. The Architect reads session logs
and coordination files ONLY — never console transcripts. A session
without a pushed log did not happen, as far as the record is concerned.

## Sync discipline (promoted from NOTES 003/004/005, v1.1)

- Developer session START: `git fetch origin`; merge `origin/main` into
  the working branch; THEN read inbox/instructions. Never conclude
  "missing" from an unfetched tree.
- Developer pushes after EVERY commit (not only at DoD).
- Architect writes only on `main`, only between Developer sessions;
  Owner confirms `(main)` in the prompt first.
- Owner rhythm: push after an Architect session; pull before asking the
  Architect for status/review.
- Owner relays POINTERS, not content: "ruled — pull and resume",
  "delivered — review". Substance lives in files; a relay needing a
  second content sentence signals a missing file.

## Levels (exactly three)

- **FYI** — no reply needed (NOTEs, session logs).
- **QUESTION** — reply needed; other tasks may continue.
- **BLOCKER** — reply needed; STOP the affected task (whole sprint if
  it blocks the sprint — say so in the file).

## Thread format (one file per thread, reply appended)

```markdown
# DEVQ-006 · QUESTION · Sprint 3 · 2026-07-25
Author: developer (claude-code)
Refs: Blueprint §4.2, ARCH-003

## Question
<what is unclear, observed vs expected, exact file/line>

## Options considered
A) ...   B) ...
Recommendation: B

---
## REPLY · architect (fable) · 2026-07-25
Decision: B. Reason: ... Architecture impact: none | ADR-NNN raised.
Status: CLOSED
```

On CLOSED, the file moves to `inbox/CLOSED/`. One thread = one topic.

## Instruction format (ARCH files)

Self-contained, always: Read first · Scope · Out of scope ·
Deliverables (exact paths) · Key contracts (normative bits inlined) ·
Acceptance criteria · Required tests · Definition of Done (which
ALWAYS includes: merge to main + push) · How to ask.

## Escalation

QUESTION unanswered when needed → raise to BLOCKER in the same file.
Suspected architecture bug → BLOCKER + tag `architecture-conflict`.
Same check RED twice after a fix → freeze forward work (IVF §8).
Owner may close anything at any time.

## Hygiene

Filenames `ID_slug.md` · ISO dates · UTF-8 · reference by ID, never
copy contract text between files · coordination files are
append-and-move only.
