# NOTE-013 · FYI · Sprint 4 · 2026-07-25
Author: developer (claude-code)
Refs: REV-S4 micro-task 2 / F-4, check_s4_screener.py rev 3 (section C.seed),
DEVQ-009

## What
The REV-S4 seed fix (screener now derives + records a non-null seed in the
shortlist note) is a **code-forward** change only. The one shortlist note already
on main — `01KYB7X30YPF55FA1NDFFZ95PS`, lineage `smc.fvg.screen.s4` — was written
before the fix and records `seed=null`. The ledger is append-only (I-1), so that
value is immutable.

## Consequence for the IVF check
`check_s4_screener.py` rev 3 ambers once per shortlist note whose `seed` is null
(section C.seed), iterating ALL shortlists. It therefore still reports **AMBER on
that historical note** after the fix — red=[], the sole amber is C.seed on
`01KYB7X30…`. FVG recomputation stays 105/105 exact; A/B/C otherwise green.

This AMBER is a **pre-fix artifact, not an incomplete micro-task**. The fix is
verified by `tests/simulator/test_screener.py`
(`test_shortlist_records_derived_seed`, `test_explicit_seed_is_recorded_verbatim`,
`test_derived_seed_is_deterministic_and_input_sensitive`): every screener run from
now on records a concrete integer seed and its `seed_source` (`derived`/`explicit`).

## Why I did not "fix" the historical note
- Append-only: the null value cannot be edited or deleted.
- `screen_s4.py` has an idempotency guard (one shortlist per lineage), so
  re-running appends nothing — by design. Forcing a second, seeded shortlist
  would inflate the trial_count for the scope and still leave the null note
  ambering. Net negative.

## Ask
At GO-S4, please read the single C.seed amber as expected/accepted (or, if a
GREEN check is wanted, adjust the check to audit only the latest shortlist per
lineage — an IVF-side change, not mine to make). The seed contract is now
enforced in code + tests for all future runs.
