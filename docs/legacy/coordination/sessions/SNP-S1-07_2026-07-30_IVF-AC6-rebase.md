# Session SNP-S1-07 · Sprint NP-S1 · 2026-07-30
Role: **IVF / Validator**, continuing SNP-S1-06 in the same worktree
(`ivf-validator-neelprajnapro-a9bdfe`), same instruction
(`ops/ARCH-NP-002_IVF_instruction_AC6.md`).

## Outcome (one line)
Per Owner/Architect instruction: fetched and rebased onto `main` (`3e3bd71`, the NP-S1
merge) before reading anything else; confirmed the journal now holds 112 records with
both the target verdict and burn present; re-ran the full protocol (drill, then real
re-derivation, then both §3 recount/spot-checks) from the rebased branch. **Every result
is unchanged from SNP-S1-06's pre-rebase run.** Overall IVF verdict remains **RED**
(same two findings: non-equivalence statements not byte-verbatim; SWEEP recount
disagrees, 331 vs 325).

## What happened
1. `git status` clean (nothing uncommitted). `git fetch origin` — confirmed
   `origin/main` at `3e3bd71` ("Merge NP-S1 deliverables 1-6..."). `git rebase
   origin/main` — clean, no conflicts (this branch's one commit, `4508ee2`, replayed
   onto `3e3bd71` as `0c92789`).
2. Confirmed before reading anything else: `datastore/journal/journal.jsonl` = 112
   records; `01KYSGQR3D8SYSVJFSF9M77CMY` (verdict) and `01KYSGQR6K1HHRT66R78BV6Z8Y`
   (burn) both present. Both conditions held — did not stop/report-and-halt.
3. Confirmed `configs/venues.yaml` and `datastore/journal/journal.jsonl` are now
   byte-identical between this worktree and the previously-external source
   (`claude/np-adr-008-liquidity-sweep-7aa72b`) — they are native to `main` now. The
   H-07 trades/bars parquet under `datastore/bulk/` remains gitignored-and-therefore
   external on every branch by design (`.gitignore`: "derived/heavy... rebuildable");
   read read-only from that worktree, same as SNP-S1-06, nothing written there.
4. Re-ran `ivf/checks/drill_np_s1_ac6.py` (six plants + control) from the rebased
   branch's native journal/venues, trades parquet from the source above. **All six
   plants CAUGHT, control CLEAN** — identical to SNP-S1-06.
5. Re-ran `ivf/checks/check_np_s1_ac6.py` against the real verdict. **All chain checks
   (A-K) GREEN**, every figure to 1e-9 — identical to SNP-S1-06.
6. Re-ran `ivf/checks/sweep_recount_np_s1_ac6.py` and the bar-honesty spot-check —
   **331 sweeps (vs reported 325)** and first-bar/last-bar/weekend-seam all exact —
   identical to SNP-S1-06.
7. Updated `ivf/reports/IVF_NP-S1_AC6.md` §0's provenance note: it previously said the
   verdict/burn were absent from `main` (true at the time) and named the unmerged
   branch; now records that `main` has merged that work at `3e3bd71`, this branch was
   rebased onto it first, and only the gitignored bulk parquet remains externally
   sourced (by the bulk store's own design, not a gap). No other section of the report
   changed — no finding was affected by the rebase.
8. This log; committing and pushing now.

## State for the next session
- Unchanged from SNP-S1-06: IVF verdict on AC-6 is **RED**. Two items still need
  Architect/Owner disposition: (a) the registration wording gap against NP-ADR-008
  §2.1's verbatim requirement; (b) the 331-vs-325 SWEEP recount disagreement (cannot be
  resolved by IVF without reading the Developer's Python, which is ruled out by design).
- The provenance concern from SNP-S1-06 is now resolved: the verdict/burn are on `main`.
  Only the (by-design, always-gitignored) bulk parquet output remains something a fresh
  clone of `main` alone cannot reproduce without re-running ingestion — this is true for
  every sprint's bulk output, not specific to this verdict.
- No code written under `qrf/**`. No new hypotheses/registrations/runs/burns. No
  normative-document edits. Confirmed (again, post-rebase) exactly one `window_burn`
  for this (window, lineage) — still no second Battery run anywhere.

## Definition of Done status
Complete: rebase done and confirmed clean, presence check done and passed, drill and
real re-derivation both re-run and unchanged, report's provenance note corrected, this
log written.
