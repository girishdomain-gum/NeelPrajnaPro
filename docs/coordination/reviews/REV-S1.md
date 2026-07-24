# REV-S1 · Architect Review of Sprint 1 (Ledger Core) · 2026-07-24
Reviewer: architect (fable) · Basis: completion report + full read of
record.py and store.py; tests/schemas reviewed via report evidence.
Verdict: **APPROVED — high quality**, with 3 observations (none blocking)
and 1 required follow-up already issued via DEVQ-001=C.

## What is right (worth naming, not just passing)
1. **record.py is spec-faithful.** canonical_bytes is verbatim §1.3;
   content_hash covers exactly the six semantic fields and the docstring
   states what is deliberately excluded and why — that sentence will save
   a future debugging day. ULID monotonicity via increment-on-collision
   is the correct, boring solution.
2. **store.py invariants are real, not decorative.** verify() re-reads
   from DISK (not memory) — the tamper test is therefore honest.
   Torn-tail vs corrupt-line distinction is exactly right: incomplete
   append is healable with consent; a complete-but-invalid line is
   corruption and halts. Per-line fsync inside a cross-platform lock.
3. **Process discipline.** Developer hit a genuine rule conflict
   (gen_state vs Hard rules) and STOPPED with a well-argued DEVQ rather
   than guessing — the protocol working as designed on day one.
   NOTE-001's "leaf" interpretation is correct and adopted.
4. Session 0 done properly: .gitignore before first commit;
   .gitattributes for LF + journal `-text` (an AC-saving detail the
   instruction did not even ask for). Fresh-clone reproducibility
   verified — the Sprint-1 exit gate's substance.

## Observations (record for Sprint 2+; no rework required)
- OBS-1 **resolve() returns a view whose content_hash is recomputed over
  the corrected payload**, so it differs from the journal's stored hash
  for that record_id. Acceptable as a view, but callers must never
  persist or chain a resolved record. Follow-up (Sprint 2, small): give
  the resolved view a marker (e.g. `meta={"resolved": true}`) or a
  distinct ResolvedView type so misuse fails loudly.
- OBS-2 **Multi-instance staleness:** two RecordStore instances on one
  journal are single-writer-safe per append (file lock) but a second
  instance's in-memory index does not see the first's appends.
  Single-operator assumption makes this fine; when the dashboard gains a
  long-lived reader (Sprint 7), readers must re-open or re-verify.
  Note for ARCH-007's author.
- OBS-3 **Amendment ordering uses ULID order** (= append order). Correct
  today; when amendments themselves get amended (unlikely but legal),
  shallow-override chains should be tested explicitly. Add one test in
  Sprint 2's test budget.

## Follow-ups
- DEVQ-001 → Decision C applied; CLAUDE.md rev 2 in force. Developer:
  run gen_state.py against the real state file next session and commit.
- Blueprint §3 wording amendment ("records imports no kernel subsystem
  beyond errors") — Architect's editorial queue, next Blueprint rev.
- OBS-1/OBS-3 land in ARCH-002's test budget.

## Sprint close status
Developer work: DONE. Remaining for close (Owner + Architect):
1. Owner: private remote + push (CI first run).
2. Architect: ivf/verify_journal.py — delivered alongside this review.
3. Owner: IVF Sprint-1 VC (run verify_journal), HC (5-record read),
   Drill S1 (byte flip on a COPY of the journal → verifier must name the
   record). Then Go/No-Go per IVF §8.
