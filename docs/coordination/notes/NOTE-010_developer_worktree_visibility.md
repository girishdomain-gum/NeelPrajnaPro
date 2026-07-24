# NOTE-010 · FYI · 2026-07-25
Author: architect (fable)
Refs: NOTE-008 (open item: Developer `pwd`), PROTOCOL v1.2 §Sync discipline

## Finding
Claude Code does NOT work in F:\QRF directly. It creates a **git worktree**
per instruction at:

    F:\QRF\.claude\worktrees\<branch-slug>\

e.g. `arch-003-execution-t0-f0c36e`, checked out on the matching
`claude/...` branch. The main folder stays parked on `main` all sprint —
which is why it looks frozen mid-sprint and why status reads of F:\QRF
alone say nothing about Developer progress (NOTE-004 family).

## Consequences
1. **Mid-sprint visibility exists.** The Architect (via Filesystem access)
   can READ the worktree live — code, tests, journal, inbox — at the
   Owner's request. Ratified in PROTOCOL v1.2: read-only, never a
   substitute for session logs as the record.
2. **NOTE-008 `pwd` item is CLOSED.** The Developer works on F:, inside
   the repo's own `.claude\worktrees\` — no extra clone, no sync hop to
   shrink further. The "run `pwd` first" boot request can be dropped from
   future boot one-liners.
3. Runtime artifacts (e.g. `datastore/bulk/` parquet from the S3 real
   ingest) live in the WORKTREE's datastore and are gitignored; after a
   merge, main's datastore is rebuilt by the idempotent scripts (for S3:
   `scripts/ingest_xauusd_s3.py`). Verification at sprint close must run
   against a rebuilt datastore on main, not assume files travel via git.
