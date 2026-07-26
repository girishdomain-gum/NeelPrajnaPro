# ARCH-010 · Sprint 10 instruction · **FINAL** · 2026-07-26
Author: architect (fable) · For: developer (claude-code)
Status: FINAL. Owner approved 2026-07-26: §1 incl. RETRO-COUNT = YES
("recording historical trial counts as new ledger entries preserves
history while making future multiplicity accounting scientifically
honest"); §2 approved; §3 approved with the existing S4 detector list
unchanged, candidate discovery kept strictly separate from hypothesis
registration. BINDING ADDITION (Owner architectural recommendation):
**Sprint 10 is the formal conclusion of GENERATION 1** — see the
Generation-1 closure section at the end.

Theme: **count every attempt, then go looking again.** Sprint 9 opened
the second eye; Sprint 10 makes the trial ledger complete and points the
instruments at fresh ground.

## T0 — boot + note
Boot per CLAUDE.md (NEW session, own branch/worktree; PRUNE merged
worktrees first — housekeeping is part of T0 this sprint). Append the
GO-S9 note.

## §1 — Trial accounting (ADR-011 + implementation)
The gap: hypothesis attempts append no trial_count, so H-004 judged at
α=0.05 undeflated by H-003's prior family attempt (its FAIL was
a-fortiori honest; a PASS would NOT have been). BINDING going forward:
1. ADR-011: every hypothesis REGISTRATION appends trial_count
   {family, lineage, n_attempts: 1} in the same flow (registration =
   spending one family attempt, whatever the verdict later says).
2. RETRO-COUNT (Owner: YES): append back-dated trial_counts for the
   four existing attempts (h001..h004) as ordinary NEW records —
   history untouched, the ledger simply learns them now. Recorded
   family_m values on existing verdicts stay as history.
3. Tests: registration appends exactly one; deflation sees it; existing
   verdicts' recorded family_m untouched (they are history).

## §2 — Housekeeping (small, T0-adjacent)
gen_state regeneration at every session close (add to CLAUDE.md close
list); fix scripts/t0_s9.py:59 E501; delete the superseded primary2025
export pair if still present.

## §3 — Exploration Wave 2 (Owner-approved)
The estate: smc.fvg deprioritized (2 decisive FAILs, 502 trials);
seasonality.calendar 2 attempts no edge. Rather than a third Monday
variant, point the screener at data it has never seen:
APPROVED: a screener sweep over the 2025-TRAINING window
(01KYDE784029…) — same instrument, NEW year, the S4 detector suite
UNCHANGED. Every sweep configuration
trial-counted from birth under §1's rule; shortlist recorded exactly as
S4 did; NO hypothesis registration this sprint (the wave produces
CANDIDATES; registration is a Sprint-11 decision with the Owner). The
2025-VIRGIN reserve is untouched; the 2024 windows are burned for their
lineages but sweeps are trial-counted reads, not verdicts — the
screener's window discipline follows the S4 convention exactly.
AC (§3): sweep manifest + shortlist + trial_counts appended; reserve
untouched; a candidates report (families ranked, honest multiplicity
figures) appended to this instruction for the Owner.

## Acceptance (sprint)
§1 ADR + registration trial_count live + tests + the four retro-counts
appended · §2 done · §3 sweep + shortlist + report · journal
chain GREEN · reserves untouched · firewall GREEN · session logs ·
DEVQs at genuine decision points.

## Sprint close (Architect duties) — and the GENERATION-1 CLOSURE
IVF-S10: drill (planted unregistered-attempt fraud — a hypothesis with
no trial_count under the new rule; planted shortlist entry not in the
sweep manifest), checks (trial-ledger completeness; sweep/shortlist
recomputation per S4's IVF pattern on the new window). HC as fits the
wave. REV-S10 → Owner Go/No-Go → GO-S10 → then, per the Owner's
binding recommendation, NOT ARCH-011 but:
1. **GENERATION 1 FINAL REVIEW** (Architect authors, Owner reads): the
   permanent scientific report — architecture, principles, every
   subsystem (observatory, calibration, battery, placebo, IVF, HC,
   graduation, lens, trial ledger), the verdict record (4 hypotheses:
   3 FAIL 1 INSUFFICIENT, 0 promotions, 1 corroborated lens), the full
   findings tally with lessons, known limitations, and Generation-2
   recommendations. docs/reports/GENERATION_1_FINAL_REPORT.md.
2. **GENERATION 1 FREEZE**: the framework is evaluated as COMPLETED
   scientific infrastructure; no new framework subsystems after S10 —
   Generation 2 builds KNOWLEDGE on the operating system, not more
   operating system. Freeze recorded as a note in the journal.
3. **GENERATION 2 PLANNING** with the Owner → only then ARCH-011.
Handover rewrite reflects the generation boundary.
