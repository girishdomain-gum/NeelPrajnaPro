# ADR-008 — Multi-AI Coordination Protocol (File-Based Roles)

**Status:** Accepted · 2026-07-24 · Owner: Owner + Architecture

## Decision
The project operates as a role-based multi-AI team coordinated through
files, not chat: Owner (human) · Architect (Fable) · Developer (Claude
Code or any repo-resident AI) · Verifier (IVF + Owner). The channel is
`docs/coordination/` (PROTOCOL.md, instructions/, inbox OPEN→CLOSED,
reviews/, notes/) plus `CLAUDE.md` at repo root as the Developer's
auto-loaded standing orders. IDs: ARCH / DEVQ / REV / NOTE. Levels:
FYI / QUESTION / BLOCKER. Threads are single files with replies
appended, then moved to CLOSED.

## Reason
The Developer AI lives in the repository and cannot read chat; files
are the physical communication medium. Written threads give auditable
engineering history and make AI substitution safe (extends the existing
principle: no AI is indispensable; all state external).

## Alternatives rejected
- Decisions/handover/verification folders inside coordination —
  rejected: duplicate ADRs, the state file, and IVF outputs (violates
  ADR-001 unique-responsibility). Coordination references them by ID.
- Heavy templates (15 fields, 5 priority levels, separate reply files) —
  rejected: process outweighing a 1-human/2-AI team gets abandoned.
- Free-form chat coordination — rejected: no history, no handover.

## Consequences
- ADR-001's artifact list gains one entry: the coordination channel
  (PROTOCOL.md + its folders) — a process artifact, not a framework doc.
- Developers may write only in inbox/OPEN and notes/ under docs/;
  the one-direction rule (ask → decide → ADR → docs) is absolute.
- ARCH instructions must be self-contained (Developer has no session
  memory).
