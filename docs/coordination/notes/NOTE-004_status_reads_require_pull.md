# NOTE-004 · FYI · Sprint 2 · 2026-07-24
Author: architect (fable)
Refs: NOTE-003 (the mirror lesson, direction 1); this is direction 2

## Discovery (no reply needed)
The Architect reported "Sprint 2 not started" while reading F:\QRF —
but F:\QRF's git state shows local main at the ARCH publish commit with
FETCH_HEAD still at the older Sprint-1 close commit: the Owner's
checkout had never fetched since the publish. Meanwhile the Developer
works in its own mirror and pushes to GitHub. Conclusion: the
Architect's status check was reading a stale snapshot and produced a
confidently wrong verdict — the exact NOTE-003 failure, mirrored.

## The full model (three worktrees, one hub)
```
F:\QRF (Owner+Architect view) ──push──▶ GitHub ◀──push── Developer mirror
        ◀──pull──                (the hub)        ──pull──▶
```
No worktree is the project. GitHub is where the parties meet. Any
status read from a worktree is only as fresh as its last pull.

## Standing rules adopted (operational; completes NOTE-003)
1. After an Architect writing session: Owner commits + pushes F:\QRF
   BEFORE booting a Developer session (NOTE-003, unchanged).
2. Before an Architect status/review session: Owner runs `git pull` in
   F:\QRF. The Architect's first question in any progress check is now
   "has F:\QRF pulled?" — and its reports carry the caveat until
   confirmed.
3. The Developer pushes at completion (already in its DoD) and SHOULD
   push incrementally at each commit so partial progress is visible.
4. A "not started / not found" conclusion by ANY party requires a
   freshness check of their worktree (git log vs origin) before it is
   asserted. Both incidents to date were freshness illusions.
