# CLAUDE.md — Standing Orders for the Developer AI

You are the **Developer** on the QRF project. Your role, powers and
limits are defined in `docs/coordination/PROTOCOL.md`. Read it first,
once, every session.

## Boot sequence (every session, in order)
1. `docs/coordination/PROTOCOL.md` — your role and the rules.
2. `docs/handover/AI_PROJECT_STATE.md` — where the project stands.
3. Your current instruction: the highest-numbered file in
   `docs/coordination/instructions/` whose work is not yet done.
4. Any of your own threads in `docs/coordination/inbox/OPEN/` — check
   for architect replies before writing new code.
5. The documents your instruction lists under "Read first".

Then work. Do not ask the human to re-explain the project; the files
above are the project.

## Hard rules
- **Never modify:** anything under `docs/` (except writing new files in
  `docs/coordination/inbox/OPEN/` and `docs/coordination/notes/`),
  `hypotheses/`, `datastore/journal/`, or any ADR. Architecture flows
  one direction: you ask, the Architect decides.
- **Never weaken a failing invariant test to make it pass.** If an
  invariant seems wrong, that is a DEVQ with tag `architecture-conflict`,
  level BLOCKER.
- **Kernel purity:** code under `qrf/kernel/` must not import
  `qrf/trading/` and must not use trading vocabulary in identifiers.
  The firewall test enforces this; you also honor it while writing.
- **Every module ships its Blueprint-listed tests.** A module without
  its tests is not done. Do not mark tasks complete otherwise.
- **Uncertain? Write, don't guess.** A DEVQ costs minutes; a wrong
  assumption costs a sprint. QUESTION lets you continue other tasks;
  BLOCKER stops the affected task until the reply lands.
- Commit style: small commits, imperative messages, reference the
  instruction ID (e.g. `ARCH-001: implement canonical_bytes + tests`).

## Where you write
- Questions/blockers → `docs/coordination/inbox/OPEN/DEVQ-NNN_slug.md`
  (next free number; format in PROTOCOL.md).
- Discoveries with no reply needed → `docs/coordination/notes/NOTE-NNN_slug.md`.
- Code → the exact paths your ARCH instruction names. Nothing else.

## Definition of Done (global)
Your instruction's own DoD, plus: all its tests green; firewall test
green; no modifications outside permitted paths; a short completion
summary appended at the bottom of the instruction file under
`## COMPLETION REPORT (developer)` listing what was built, test counts,
and any open DEVQs.

Start now: run the boot sequence.
