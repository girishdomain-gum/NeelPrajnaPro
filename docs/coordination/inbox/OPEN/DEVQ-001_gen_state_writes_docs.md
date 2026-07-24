# DEVQ-001 · QUESTION · Sprint 1 · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-001 (DoD; deliverable scripts/gen_state.py), ADR-007, CLAUDE.md
("Hard rules" — Never modify anything under docs/…), PROTOCOL.md

## Question
ARCH-001's Definition of Done says: "`scripts/gen_state.py` runs and updates
the state file" (docs/handover/AI_PROJECT_STATE.md). ADR-007 designates that
file as *generated* by exactly this script.

But CLAUDE.md's Hard rules state: "Never modify: anything under `docs/` (except
writing new files in `docs/coordination/inbox/OPEN/` and
`docs/coordination/notes/`) …". docs/handover/AI_PROJECT_STATE.md is not in the
allowed set.

So I built and fully verified gen_state.py but did **not** run it against the
real file. Evidence it works: run with `--out <tmp> --no-tests` produced a diff
touching only (a) the generated-at header comment and (b) the `## Status` table
rows; the two hand-maintained sections ("Next immediate task", "Don't change
without discussion") and every other section were preserved byte-for-byte.

May the Developer run `python scripts/gen_state.py` against the tracked file as
part of normal Sprint work, or is regenerating AI_PROJECT_STATE.md reserved to
the Owner/Architect?

## Options considered
A) Treat gen_state.py's write to docs/handover/AI_PROJECT_STATE.md (and only
   that path) as a sanctioned exception to the docs Hard rule, since ADR-007
   makes it generated and ARCH-001 DoD requires it. Developer runs it.
B) Keep the Hard rule absolute; the Owner/Architect runs gen_state.py (or the
   CI/backup pipeline does). Developer never writes under docs/handover/.
C) Amend CLAUDE.md Hard rules to add docs/handover/AI_PROJECT_STATE.md to the
   Developer-writable set (via the generator only), for symmetry with ADR-007.

Recommendation: A (with the spirit of C documented). The write is mechanical,
non-architectural, idempotent, and preserves all hand-maintained prose; gating
it behind the Owner defeats the "generated, never stale" intent of ADR-007.
Until this is decided the file is left untouched and Sprint-1 completion is
recorded only in the ARCH-001 completion report.
