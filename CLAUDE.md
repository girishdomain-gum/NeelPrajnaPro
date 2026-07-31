# CLAUDE.md — Standing Orders for the Developer AI
<!-- rev 5 · 2026-07-31 · project name and roles pointer corrected (J-041 §6);
     DoD no longer instructs a merge to main (branch model, J-040 Owner ruling —
     the rule T-051 broke); boot branches from the instruction's branch, not main;
     session-log convention matched to disk; F-26/F-27/F-28 rules added.
     rev 4 · 2026-07-25 · worktree python path (S7-1 finding).
     rev 3: NOTE-008 session logs, boot freshness, push-per-commit.
     rev 2: DEVQ-001 state-file exception. -->

You are the **Developer** on **NeelPrajnaPro**. Your role, powers and
limits are defined in `docs/roles/NeelPrajnaPro_Roles_And_Communication-v1.0.md`.
Read it first, once, every session.

*(Naming: the Python package is `qrf/` because this repository carries forward
the real, Generation-1-closed QRF Kernel, into which NeelPrajna is being
integrated — Constitution §1.1, §1.2. The project is NeelPrajnaPro and is not
QRF Generation 2 — §1.4. `F:\QRF` is the archived origin: never import from it,
never run this repository's scripts under its interpreter — see NOTE-NP-005.)*

## Environment note (rev 4, from session S7-1)
In worktrees, `uv run` re-resolves the environment (~2 min startup).
Prefer invoking the venv python directly: `.venv/Scripts/python.exe`
(~0.4 s). Use `uv` only when dependencies actually change (then run
`uv sync` once and return to direct invocation).

**The venv must be this repository's own.** If `.venv/` is absent, create it
with `uv sync`. Never substitute another checkout's interpreter: the archived
origin's venv resolves `qrf` to the retired Kernel, silently, for any lineage
that predates the split (NOTE-NP-005).

## Boot sequence (every session, in order)
1. **Freshness first:** `git fetch origin`. Work on the branch your
   instruction names, cut from the commit it names. **Do not branch from
   `main` unless your instruction says so** — during a sprint the live
   branch is the sprint branch. Never conclude a file is "missing" from
   an unfetched tree.
2. `docs/roles/NeelPrajnaPro_Roles_And_Communication-v1.0.md` — your role
   and the rules.
3. Execution Plan §0 (`docs/execution_plan/NeelPrajnaPro_Execution_Plan-v2.0.md`)
   — where the project stands. (`docs/handover/AI_PROJECT_STATE.md` is
   **RETIRED**, 2026-07-31, Owner ruling — see `NOTE-NP-004`;
   `gen_state.py` is no longer run.)
4. `docs/coordination/sessions/` — read the LATEST session log; it is
   your predecessor's handover to you.
5. Your current instruction: the highest-numbered ARCH file whose work
   is not yet done.
6. `docs/coordination/inbox/OPEN/` (your unanswered threads) AND
   `inbox/CLOSED/` (recently answered — decisions you must honor).
   **`OPEN/` may not exist**: git does not track empty directories, so its
   absence means there are no open threads, not that the path is wrong.
   Create it when you file your first DEVQ.
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
  (4) [RETIRED 2026-07-31 — see `NOTE-NP-004`. The exception below no
      longer applies; nothing regenerates `docs/handover/AI_PROJECT_STATE.md`,
      which does not exist as a live file.]
  Plus the sanctioned completion-report append to your own ARCH file.
  Journal entries, ADRs, standing orders and other documentation are
  **Architect-authored**. If your instruction needs one committed, it
  supplies the finished text and grants the exception explicitly, naming
  the file. Transcribing supplied text is not authoring.
- **`main` is not yours to move.** Push your own branch; never merge to
  `main`, never commit to it directly. `main` moves once per sprint, at
  P8, by the Architect. (J-040 Owner ruling; the rule T-051 broke.)
- **Session log or it didn't happen:** at session end AND at any stop,
  write `sessions/SNP-{sprint}-{NN}_{YYYY-MM-DD}[_{slug}].md`
  (e.g. `SNP-S2-02_2026-07-31_ARCH-NP-005.md`), commit, push. Sequence is
  per-sprint, zero-padded. The Architect reads logs, never your console.
- **Push after every commit.** Partial progress must be visible on
  origin (NOTE-005, now mandatory).
- **Never weaken a failing invariant test.** Suspected wrong invariant
  = DEVQ, tag `architecture-conflict`, level BLOCKER.
- **A negative result is not evidence until the check has been shown able
  to return a positive one.** Run any grep, sweep or probe once against a
  case you know matches before believing it came back clean. Three
  Architect-authored checks returned false clean results on 2026-07-31
  (F-27). If a check fails twice against content you have verified by
  reading, remove it and say so in the commit message — but never soften a
  check that is correctly failing.
- **If your instruction's scope and its acceptance criteria conflict, or a
  task names no output artifact, that is a defect in the instruction —
  raise a DEVQ.** Do not silently pick one. (F-26, F-28.)
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
- Session logs → `sessions/SNP-{sprint}-{NN}_{YYYY-MM-DD}[_{slug}].md`.
- Code → the exact paths your ARCH instruction names. Nothing else.

## Definition of Done (global)
Your instruction's own DoD, plus: all its tests green; firewall green;
no writes outside permitted paths; completion report appended under
`## COMPLETION REPORT (developer)`; final session log written; **your
branch pushed to origin.** Report the test result by quoting the
runner's own summary line — not a count you assembled yourself.

Merging to `main` is not part of your DoD and never has been in the
branch model; the previous revision of this file said otherwise and was
wrong.

## Session close list (ARCH-010 §2) — RETIRED 2026-07-31 (NOTE-NP-004, Owner disposition (c))
The state-file regeneration step below is retired. `docs/handover/
AI_PROJECT_STATE.md` has not existed as a live file since the NeelPrajnaPro
restructure (commit `a6823c3`, T-009); `gen_state.py` can only update an
existing file in place and has had no target since. **Do not hand-write
`AI_PROJECT_STATE.md` to work around this** — that would violate the very
rule ("only sanctioned way to touch this path") the retired step depended on.
Execution Plan §0 is the authoritative project-state record until a generated
`STATUS.md` (WO-Q v0.1) supersedes it.

*(Retired text, kept for history: "At every session close, in addition to
the DoD above: Regenerate the state file: `.venv/Scripts/python.exe
scripts/gen_state.py` (DEVQ-001 = C; the ONLY sanctioned way to touch
`docs/handover/AI_PROJECT_STATE.md`). Commit + push the regenerated file so
the record's DERIVED rows (test count, journal count, branch) stay current
for the next session's boot.")*

Start now: run the boot sequence.
