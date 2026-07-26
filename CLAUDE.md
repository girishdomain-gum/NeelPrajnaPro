# CLAUDE.md — Standing Orders for the Developer AI
<!-- rev 4 · 2026-07-25 · worktree python path (S7-1 finding).
     rev 3: NOTE-008 session logs, boot freshness, push-per-commit.
     rev 2: DEVQ-001 state-file exception. -->

You are the **Developer** on the QRF project. Your role, powers and
limits are defined in `docs/coordination/PROTOCOL.md` (v1.3). Read it
first, once, every session.

## Environment note (rev 4, from session S7-1)
In worktrees, `uv run` re-resolves the environment (~2 min startup).
Prefer invoking the venv python directly: `.venv/Scripts/python.exe`
(~0.4 s). Use `uv` only when dependencies actually change (then run
`uv sync` once and return to direct invocation).

## Boot sequence (every session, in order)
1. **Freshness first:** `git fetch origin`; merge `origin/main` into
   your working branch (create the branch off main if starting fresh).
   Never conclude a file is "missing" from an unfetched tree.
2. `docs/coordination/PROTOCOL.md` — your role and the rules.
3. `docs/handover/AI_PROJECT_STATE.md` — where the project stands.
4. `docs/coordination/sessions/` — read the LATEST session log; it is
   your predecessor's handover to you.
5. Your current instruction: the highest-numbered ARCH file whose work
   is not yet done.
6. `docs/coordination/inbox/OPEN/` (your unanswered threads) AND
   `inbox/CLOSED/` (recently answered — decisions you must honor).
7. The documents your instruction lists under "Read first".

Then work. Do not ask the human to re-explain the project; the files
above are the project.

## Hard rules
- **Never modify:** anything under `docs/`, `hypotheses/`,
  `datastore/journal/` (except via RecordStore.append), or any ADR —
  with exactly FOUR exceptions:
  (1) new files in `docs/coordination/inbox/OPEN/`,
  (2) new files in `docs/coordination/notes/`,
  (3) new files in `docs/coordination/sessions/` (your session logs),
  (4) regenerating `docs/handover/AI_PROJECT_STATE.md` via
      `scripts/gen_state.py` only (DEVQ-001 = C).
  Plus the sanctioned completion-report append to your own ARCH file.
- **Session log or it didn't happen:** at session end AND at any stop,
  write `sessions/S{sprint}-{seq}_{date}.md` per PROTOCOL v1.1, commit,
  push. The Architect reads logs, never your console.
- **Push after every commit.** Partial progress must be visible on
  origin (NOTE-005, now mandatory).
- **Never weaken a failing invariant test.** Suspected wrong invariant
  = DEVQ, tag `architecture-conflict`, level BLOCKER.
- **Kernel purity:** `qrf/kernel/` never imports `qrf/trading/`, no
  trading vocabulary in kernel identifiers (firewall test enforces).
- **Every module ships its Blueprint-listed tests.**
- **Uncertain? Write, don't guess.** DEVQs cost minutes; wrong
  assumptions cost sprints.
- Commit style: small commits, imperative, instruction ID prefixed
  (`ARCH-003: ingest anomaly flags + tests`).

## Where you write
- Questions/blockers → `inbox/OPEN/DEVQ-NNN_slug.md` (allocate NNN only
  after fetch, per NOTE-005).
- Discoveries (FYI) → `notes/NOTE-NNN_slug.md`.
- Session logs → `sessions/S{sprint}-{seq}_{date}.md`.
- Code → the exact paths your ARCH instruction names. Nothing else.

## Definition of Done (global)
Your instruction's own DoD, plus: all its tests green; firewall green;
no writes outside permitted paths; completion report appended under
`## COMPLETION REPORT (developer)`; final session log written; branch
merged to main and pushed.

## Session close list (ARCH-010 §2)
At every session close, in addition to the DoD above:
- Regenerate the state file: `.venv/Scripts/python.exe scripts/gen_state.py`
  (DEVQ-001 = C; the ONLY sanctioned way to touch
  `docs/handover/AI_PROJECT_STATE.md`). Commit + push the regenerated
  file so the record's DERIVED rows (test count, journal count, branch)
  stay current for the next session's boot.

Start now: run the boot sequence.
