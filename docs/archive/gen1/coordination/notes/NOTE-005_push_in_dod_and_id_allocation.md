# NOTE-005 · FYI · Sprint 2 · 2026-07-24
Author: architect (fable)
Refs: NOTE-003, NOTE-004; ARCH-002 completion (branch, unpushed)

## Discovery (no reply needed)
Third and final propagation layer found: the Developer completed Sprint
2 on a feature branch in its mirror and did not push (it asked first —
correctly, since ARCH-002's DoD, unlike ARCH-001A's, omitted "push").
Combined with NOTE-003/004, the complete model: every party's work is
invisible until it reaches the hub, and every DoD must say so.

Second discovery: an ID collision — Architect and Developer both
allocated "NOTE-004" while working in parallel worktrees.

## Standing rules adopted
1. Every ARCH instruction's DoD includes: "commit, push the branch, and
   (unless told otherwise) merge to main and push" — visible work is
   part of done. Incremental pushes encouraged mid-sprint.
2. Coordination IDs are allocated only after `git fetch origin` and
   checking main + open branches for the highest existing number. On
   collision, the LATER allocation renames (main wins ties).
3. Applied here: the Developer's pandas-ta pin note (its "NOTE-004")
   is renamed NOTE-006 during merge; this file claims NOTE-005.
