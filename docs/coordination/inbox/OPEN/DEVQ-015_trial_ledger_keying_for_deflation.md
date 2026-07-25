# DEVQ-015 · QUESTION · Sprint 6 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-006 §2 (corrections), ARCH-006 H-001 thresholds, Blueprint §4.8,
trial_count 01KYB7X308YS3KMV8C95MZ028E

## Question
ARCH-006 §2 fixes the deflation contract as
`effective_alpha = base_alpha / max(1, N_trials)` where
`N_trials = TrialCountLedger.total(scope, lineage)` for **the hypothesis's
own scope + lineage** at judging time. H-001 declares `scope = xauusd_h1`,
`lineage = h001_fvg_follow_through`, and the note says "correction: Bonferroni
vs trial ledger scope=xauusd_h1 (currently 500 trials → effective_alpha ≈
1e-4)".

The ledger does not currently support that arithmetic. The only `trial_count`
record (01KYB7X308YS3KMV8C95MZ028E, n=500) is keyed
`data_scope = 01KYAWHZ86ZNDGY4NZNCF4XFY0` (the *sample* window id) and
`lineage = smc.fvg.screen.s4`. Neither key matches H-001's
`(xauusd_h1, h001_fvg_follow_through)`, so at judging time:

    TrialCountLedger.total("xauusd_h1", "h001_fvg_follow_through") == 0
    → effective_alpha = 0.05 / max(1, 0) = 0.05   (NOT ≈1e-4)

So the screener's 500 FVG trials do **not** deflate H-001's alpha under the
literal scope+lineage contract. This does not change H-001's pre-registered
EXPECTATION (FAIL/INSUFFICIENT is the likely, healthy outcome regardless), but
it does mean the "1e-4" illustration in the instruction is not what the
machinery will compute.

## Options considered
A) Implement the literal contract `total(scope, lineage)` exactly as §2 states;
   at judging time N_trials for H-001 is 0, effective_alpha = base_alpha = 0.05,
   reported transparently by judge_h001.py. The "500 → 1e-4" line is treated as
   an illustrative expectation, superseded by the standing rule "whatever the
   ledger says at judging time is what applies."
B) Re-key / re-scope the screener's 500 trials (or have judge_h001 bump a
   `trial_count` at `(xauusd_h1, h001_fvg_follow_through)`) so the FVG family's
   prior search burden actually deflates H-001. This needs an Architect ruling
   on the intended keying (the screener ran on the *sample*, H-001 judges the
   *full* dataset — are they the same "scope" for multiplicity accounting?).
Recommendation: **A** for this sprint — implement and unit-test the literal
`base/max(1,N)` formula against hand numbers, and have judge_h001 print the
actual N_trials + effective_alpha the real ledger yields (0 and 0.05). If the
Architect wants the screener burden to bite (option B), that is a keying
decision (scope granularity, family vs lineage) better ruled explicitly than
guessed — the verdict outcome is acceptance-valid either way.

---
(awaiting architect reply)
