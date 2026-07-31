# NOTE-NP-004 · Sprint NP-S2 (WO-P) · 2026-07-31
Author: developer (claude-code)
Refs: `CLAUDE.md` "Session close list (ARCH-010 §2)"; `scripts/gen_state.py`; `docs/handover/AI_PROJECT_STATE.md` (target, missing); `docs/archive/gen1/handover/AI_PROJECT_STATE.md` (archived predecessor).
Tag: discovery (pre-existing, session-close step cannot run as written)

## Finding
CLAUDE.md's session-close list requires running
`.venv/Scripts/python.exe scripts/gen_state.py` to regenerate
`docs/handover/AI_PROJECT_STATE.md`, "the ONLY sanctioned way to touch" that
file (DEVQ-001 = C). Running it at the end of this session fails:

```
error: F:\...\docs\handover\AI_PROJECT_STATE.md not found
```

`scripts/gen_state.py` only **updates** an existing file's DERIVED rows in
place (preserving HAND rows/prose verbatim, ADR-007) — it has no
create-from-scratch path. `docs/handover/AI_PROJECT_STATE.md` does not exist
anywhere in this tree. Its Generation-1-era predecessor was moved to
`docs/archive/gen1/handover/AI_PROJECT_STATE.md` by commit `a6823c3`
("T-009: architecture folder = ONE doc... Gen-1 trees archived under
docs/archive/gen1") during the NeelPrajnaPro estate restructuring — and
nothing since has recreated a live file at the path `gen_state.py` still
targets. Every session log between T-009 and this one (through T-051) either
didn't run this step or it was silently skipped; this session is the first to
hit and report it.

## Disposition
Did not fix. Two reasons: (1) `scripts/` is outside WO-P's write scope
(`qrf/**` + `tests/**`, ARCH-NP-004 §9 addendum) — patching `gen_state.py`'s
create-from-scratch behavior or its hardcoded path is not this instruction's
to do; (2) hand-writing `docs/handover/AI_PROJECT_STATE.md` myself to work
around the script would violate CLAUDE.md's own rule that regeneration via
`gen_state.py` is the *only* sanctioned way to touch that path — routing
around a broken tool by doing the forbidden thing manually is worse than
leaving the gap visible.

## What I have NOT done
Not created or hand-edited `docs/handover/AI_PROJECT_STATE.md`. Not modified
`scripts/gen_state.py`. Recorded in this session's log
(`docs/coordination/sessions/SNP-S2-01_2026-07-31_WO-P.md`) and in the
handover (`ops/aro/handovers/WO-P/HANDOVER.md`) that this step was attempted
and blocked, rather than silently omitted.

## Disposition (appended 2026-07-31, Owner ruling, J-040)
**Option (c) — Retire.** `docs/handover/AI_PROJECT_STATE.md` is not
restored. `CLAUDE.md`'s session-close step is struck and replaced with a
pointer to Execution Plan §0 as the authoritative project-state record,
until WO-Q's `STATUS.md` (v0.1) supersedes it. `scripts/gen_state.py` is left
in place, marked deprecated in its own header, not deleted — preserves
history, zero behavioural risk. Owner's stated reasoning: Execution Plan §0
already fulfills the purpose, and recreating a file only to retire it again
once `STATUS.md` exists would create duplicate state and unnecessary
maintenance. Condition satisfied: the retirement is documented here, in
`CLAUDE.md` itself, in `CHANGELOG.md`, and in journal J-040.
