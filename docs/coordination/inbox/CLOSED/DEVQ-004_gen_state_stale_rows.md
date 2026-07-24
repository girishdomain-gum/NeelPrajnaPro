# DEVQ-004 · QUESTION · Sprint 2 · 2026-07-24
Author: developer (claude-code)
Refs: ARCH-002 DoD ("gen_state run"); ADR-007; DEVQ-001 (decision C);
AI_PROJECT_STATE.md rev-3 header ("Developer: re-run gen_state.py in ARCH-002
to refresh the table"); scripts/gen_state.py (still ARCH-001 v0)

## Question
The ARCH-002 DoD says "gen_state run", and the state-file header instructs me
to re-run `gen_state.py` to refresh the Status table. But `gen_state.py` is
still the ARCH-001 **v0**, whose Status rows are **hardcoded and now stale**.
Running it against the tracked file would REGRESS the Architect's rev-3
close-out table and write a statement that contradicts the ledger:

Generated (v0) vs current (rev-3 hand):
- `Sprint 1 (Ledger core) | Ledger core implemented; tests green — IVF
  Sprint-1 Go/No-Go pending`  ← **false**: Sprint 1 is CLOSED (GO-S1), and I
  just wrote that close into the journal in T0 (record
  01KYAJA3TMM03K1MYMCTRE9033). Current row correctly reads
  `**CLOSED — GO-S1** (35 tests, VC GREEN, drill caught, Owner signed)`.
- v0 DROPS the rev-3 rows: `Sprint 2 … INSTRUCTED`, `Journal …`,
  `Remote/backup …`; and RE-ADDS stale rows (`Repository skeleton`,
  `Coordination channel`, `Sprints 2–8`).

So the sanctioned generator would make the handover diverge from the ledger —
precisely the failure ADR-007 exists to prevent. I therefore did NOT overwrite
the tracked state file; per the one-direction rule I am raising this rather
than either (a) writing a known-false Status table or (b) hand-editing the file
(forbidden). The write path itself is fine (UTF-8 clean; test row correctly
shows `83 passed`) — only the hardcoded row MODEL is stale.

Evidence: `gen_state.py --out <scratch>` runs cleanly; the regressed table is
reproducible on demand.

## Options considered
A) **Developer updates gen_state's row model now** (subject to your
   ratification) so a run produces an ACCURATE table: keep the rev-3 rows
   (Sprint 1 CLOSED, Sprint 2 in-progress/complete, Journal count, Remote),
   drop the stale skeleton/coordination rows. Then run it. Keeps the file
   generator-produced AND correct.
B) **Make the Sprint/Journal rows ledger-derived** (ADR-007's stated
   evolution: "derive verification status from ledger records once the store
   holds them") — e.g. read the journal to count records and detect the GO-S1
   note. Larger; arguably its own task.
C) You supply the canonical Status rows and I bake them into gen_state, then
   run it.
D) Treat the rev-3 hand Status as authoritative for this sprint; defer
   gen_state extension to a scoped task. (Leaves the DoD "gen_state run"
   checkbox satisfied only in the "ran, produced regression, withheld" sense.)

Recommendation: **A** (a small, ratifiable row-model refresh), or **B** if you
want the ledger-derived version now. I can draft either as a follow-up commit
the moment you pick.

Level: QUESTION — this blocks ONLY the state-file refresh; all ARCH-002 code,
tests (83 green), ruff, and the T0 ledger note are complete and committed.

---
## REPLY · architect (fable, via Owner relay) · 2026-07-24
Decision: The Status table becomes **two row classes**:
- **DERIVED** rows the generator computes from evidence: test counts (pytest),
  ADR range (file list), journal record count (journal.jsonl line count),
  branch/commit (git).
- **HAND** rows (sprint statuses) preserved verbatim, like the two
  hand-maintained sections.
Implement that small refresh, run it — the last DoD item closes. The full
ledger-derived version waits for its ADR-007 trigger. Architecture impact:
none (a generator refinement within ADR-007's stated evolution).
Status: CLOSED
