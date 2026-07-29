# ADR-007 — AI_PROJECT_STATE.md Is Generated from the Ledger

**Status:** Accepted · 2026-07-24 · Owner: Ops

## Decision
The handover/status file is produced by `scripts/gen_state.py`:
status table from CI + ADR index, open questions from `question`
records, verification status from `verification_report` records,
current sprint from git. Only two sections are hand-maintained:
"Next immediate task" and "Don't change without discussion".

## Reason
The ledger already stores project state; a hand-written copy creates a
second source of truth that will diverge — the exact disease the
architecture exists to prevent. A stale dashboard is worse than none:
it is confidently wrong.

## Consequences
gen_state.py is a Sprint-1 deliverable (v0 may stub ledger queries
until the store exists). The committed file carries a generated-at
timestamp and a "do not edit above the line" marker.
