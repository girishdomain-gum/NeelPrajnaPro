# Migration Plan — Documentation Re-architecture (Phase 8)

Enters the one authoritative ladder in `PHASE_LEDGER.md` as **Phase 8**, gated
the same way any other phase is gated: nothing is declared done until its
exit check is actually true, and any exit check that turns out to be
unachievable as written is re-scoped in the open (per the Phase 5 precedent),
not quietly abandoned.

---

## 1. Scope

Documentation only. No `.mqh`, `.mq5`, `.py`, `.set`, `.ini`, or CSV schema
changes result from this plan. See `DOCUMENTATION_ARCHITECTURE.md` §4 for the
explicit non-goals.

## 2. Pre-conditions

- `DOCUMENTATION_ARCHITECTURE.md` ratified by the owner (§5 of that document).
- `ADR-008-kernel-trading-plugin-split.md` ratified by the owner.
- Both ratifications recorded with a date and signature, same pattern as
  every other ADR in this repository.

## 3. Steps

| Step | Action | Exit check |
|---|---|---|
| 8.1 | Create the new directory tree (`docs/core/`, `docs/books/book-a-neelprajna/`, `docs/governance/`, `docs/registers/`, `docs/roadmap/`) alongside the existing `docs/` tree — additive, nothing deleted yet | New folders exist; old folders untouched |
| 8.2 | Copy (not move) every file per the migration table in `DOCUMENTATION_ARCHITECTURE.md` §3 into its new location | Every row in the migration table has a corresponding file at its new path, byte-identical to the original except where the table specifies a SPLIT |
| 8.3 | For SPLIT rows (`HANDOVER.md`, `BOOT_PROMPT*.md`), perform the split by hand, preserving every sentence — moving text is not editing it | A diff of (old file) against (concatenation of its new-location pieces) shows only whitespace/heading changes, no content loss |
| 8.4 | Update cross-references: every doc that links to a moved file's old path gets its link updated | `grep` for the old paths across `docs/` returns zero hits outside `docs/roadmap/archive/` |
| 8.5 | Add the new files created by this redesign (`INDEX.md`, `DOCUMENTATION_ARCHITECTURE.md`, `core/*.md`, `registers/*.md`, `ADR-008`, this file) — these have no "old path" to migrate from | Files exist and are internally consistent (no broken cross-links) |
| 8.6 | Root `README.md` gains one line pointing to `docs/INDEX.md` | Line present, no other change to README |
| 8.7 | Delete the old, now-duplicated files **only after** step 8.4's exit check passes | Old paths return 404 / do not exist; new paths hold identical content |
| 8.8 | Record this migration as its own entry in `registers/DECISION_REGISTER.md` | Entry present, citing this document as evidence |

Steps 8.1–8.6 are non-destructive and reversible at every point. Step 8.7 is
the only destructive step and is deliberately last and separately gated.

## 4. Rollback

Because 8.1–8.6 never delete anything, rollback before step 8.7 is simply:
delete the new tree. After step 8.7, rollback is: restore from version
control history, exactly as any other reverted commit would be.

## 5. Ownership

Per `governance/AUTONOMY_LADDER.md`: executing this plan (copying files,
updating links) is an **operations** task and may be automated. Ratifying
`DOCUMENTATION_ARCHITECTURE.md` and `ADR-008` in the first place is a
**governance** decision and stays with the owner.

## 6. Relationship to the existing ladder

This is additive to the existing four items (A–D) in `PHASE_LEDGER.md` §1,
not a replacement for any of them. It does not compete for priority with
Item D (the R6 long run) — the R6 long run remains the highest-value pending
engineering action; this migration is a documentation-only task that may
proceed in parallel, exactly as the original NP Architecture Roadmap's
Phase 3 ("Docs & multi-model workflow") proceeded alongside engineering work
without blocking it.
