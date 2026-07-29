# NOTE-003 · FYI · Sprint 1→2 boundary · 2026-07-24
Author: architect (fable)
Refs: ARCH-002 "missing" incident; ADR-008; CLAUDE.md boot sequence

## Discovery (no reply needed)
First fresh-session handover surfaced a propagation gap: the Architect
writes files directly to the working tree (F:\QRF), but a new Developer
session operates on a git-based mirror of the repository — so any
Architect output that is not COMMITTED AND PUSHED is invisible to it.
The Developer booted, found no ARCH-002 (it existed on disk,
uncommitted), correctly refused to invent an instruction under the
one-direction rule, and stopped. The handover design worked; the
publication step was missing.

Secondary finding: git does not track empty directories, so
inbox/OPEN/ vanished from the mirror once DEVQ-001 moved to CLOSED.
Fixed with a tracked .gitkeep.

## Standing rule adopted (operational, no ADR needed)
The Architect's outputs are PUBLISHED, not merely written: after any
Architect writing session, the Owner commits and pushes before booting
a Developer session. Suggested commit prefix: `ARCH:`. A Developer that
cannot find its instruction should always check `git log`/`git status`
freshness before concluding the instruction does not exist — and then
do exactly what this Developer did: stop and ask.

Credit where due: the refusing session behaved perfectly. A Developer
that guesses at missing architecture is the failure mode; this one is
the design working.
