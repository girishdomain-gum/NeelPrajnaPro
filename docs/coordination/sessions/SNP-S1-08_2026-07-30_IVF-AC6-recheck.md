# Session SNP-S1-08 · Sprint NP-S1 · 2026-07-30
Role: **IVF / Validator**, continuing in worktree `ivf-validator-neelprajnapro-a9bdfe`.
Instruction: `ops/ARCH-NP-003_IVF_recheck_instruction.md` — scope: §3.2 and §3.3 only.

## Outcome (one line)
Rebased onto `main` (`02f1249`, carrying T-042/Appendix B); confirmed journal still 112
records with verdict + burn present; re-checked §3.2 as a substance test (**PASS, 6/6**,
byte deviation recorded per Appendix B §B.7, not a failure) and re-derived §3.3 from
Appendix B §B.1–B.5 (**PASS — 3,099 pivots / 465 pools / 325 sweeps, exact**, up from rev
1's 3,099/476/331). **Overall AC-6 verdict is now GREEN**, appended as §7 to
`ivf/reports/IVF_NP-S1_AC6.md` (§§0–6 untouched, per P5).

## What happened
1. `git fetch origin` — `origin/main` had advanced to `02f1249` (T-042, issuing
   ARCH-NP-003 + Appendix B). `git rebase origin/main` — clean, no conflicts.
2. Confirmed before reading anything else: `datastore/journal/journal.jsonl` = 112
   records; verdict `01KYSGQR3D8SYSVJFSF9M77CMY` and burn `01KYSGQR6K1HHRT66R78BV6Z8Y`
   both present. Force-pushed the rebase (`--force-with-lease`) immediately.
3. Read `ops/ARCH-NP-003_IVF_recheck_instruction.md` and
   `ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md` in full (B.1–B.10).
4. **§3.2:** wrote `ivf/checks/recheck_ac6_s32_substance.py` — substance test (regex
   markers per proposition, independent of exact wording) separate from the byte test.
   Result: substance PASS 6/6 across both registrations; byte test 0/6 (unchanged from
   the original run), restated per B.7 as a recorded deviation, not a failure.
5. **§3.3:** rewrote `ivf/checks/sweep_recount_np_s1_ac6.py` to rev 2, implementing
   Appendix B §B.1–B.5 literally in place of rev 1's own disclosed assumptions (rev 1's
   docstring is preserved inside rev 2's, for the record). Diagnosed, before running,
   which of rev 1's choices the pinned text actually changed:
   - B.1 (pivot test): unchanged — rev 1 already matched.
   - B.2 (anchored membership): unchanged in substance — rev 1's ordering of "fold r
     into the candidate list, then filter by tolerance" is mathematically identical to
     B.2's "search mates, then append r."
   - **B.3 (suppression): changed.** Rev 1 tested active-pool proximity against the new
     pivot's own raw price; B.3 requires testing against the candidate pool's *computed*
     level (max/min of the full cluster) — these differ whenever the new pivot isn't the
     cluster's own extremum. This was the primary source of rev 1's pool overcount.
   - **B.4 (per-bar order): changed**, and this was outside rev 1's three originally
     disclosed assumptions — rev 1 processed pivot→pool formation before the
     sweep/invalidation pass each bar; B.4 pins the reverse order, meaning a pool
     resolved mid-bar no longer suppresses a new candidate at that same bar. Rev 1's
     existing `formed_at >= bar_i` guard already handled the "can't sweep what you just
     formed" consequence by accident, but not this second one.
   - B.5 (reclose at p, p+1, p+2): unchanged, re-verified — rev 1 already checked exactly
     these three bars. ARCH-NP-003 flagged this as the likeliest culprit; it was not.
6. Ran rev 2 against the same 16,029-bar M5 series: **3,099 pivots / 465 pools / 325
   sweeps — exact match on all three**, first try after the B.3+B.4 fixes. No first-
   divergence bar to report; no tuning was done to reach the target (the fix was derived
   from reading B.3/B.4's text against rev 1's code, before running, not by adjusting
   parameters until the number matched).
7. Appended **§7** to `ivf/reports/IVF_NP-S1_AC6.md` (did not edit §§0–6): substance/byte
   test results, the B.1–B.5 diagnostic table above, the B.8-mandated limitation
   statement (text-code fidelity, not code correctness — Appendix B was written from the
   evidenced implementation, so a match does not independently confirm the detector
   against anything external), and the restated overall verdict.
8. This log; committing and pushing now.

## State for the next session
- **AC-6 overall verdict is now GREEN**, per ARCH-NP-003 §4's own stated criterion
  (§3.2 substance PASS + §3.3 exact reproduction), qualified by §7.3/B.8's limitation
  that this confirms text-code fidelity of Appendix B, not independent code correctness.
  Whether this is sufficient to begin HC is the Architect/Owner's decision, not IVF's —
  not declared here.
- `ivf/checks/sweep_recount_np_s1_ac6.py` is now at rev 2 (B.1–B.5 pinned mechanics);
  rev 1's assumptions are preserved in its docstring, not deleted, so the diagnostic
  trail (what changed and why) survives.
- `ivf/checks/recheck_ac6_s32_substance.py` is new — the substance/byte split test for
  §3.2, reusable if the registration wording question is revisited.
- No code written under `qrf/**`. No registrations, runs, burns, or normative-document
  edits. No Battery re-run — still exactly one `window_burn` for this (window, lineage).

## Definition of Done status
Complete: rebase done and pushed, presence check passed, both re-checked items run and
reported, §7 appended without disturbing §§0–6, this log written.
