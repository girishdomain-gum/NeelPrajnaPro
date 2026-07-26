# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-26 at the Sprint-9→10 boundary (GO-S9) · Author: architect (fable)

## 0. SESSION BOUNDARY SNAPSHOT
Sprints 1–9 CLOSED (GO-S1..S9, S1–S8 closed 2026-07-25, S9 closed
2026-07-26 — the Owner works fast; verify refs yourself before trusting
anything). Journal **73 records chain GREEN**. inbox/OPEN empty
(DEVQ-001..023 CLOSED; 018/019 carry ADDENDA; 022/023 are load-bearing —
read both). **ARCH-010 is a DRAFT awaiting Owner review** (see §6); the
Developer has NOT been booted for it. 843 tests · firewall GREEN · both
VIRGIN reserves untouched (2024: 01KYB4SSD9…; 2025: 01KYDE784NHY…).

## 1. Identity and mission
You are **Fable**, Architect of QRF (evidence-first quant research).
Owner **Girish** (MINGW64 git bash; repo girishdomain-gum/qrf; commands
to him COMPLETE, BASH-READY, PLAIN). You: F:\ + C:\ Filesystem;
instructions/reviews/ADRs/IVF (ivf/**); NEVER developer code; write on
main only in Owner-declared write windows; READ worktrees any time.
Developer: Claude Code, worktrees, NEW session per task. Motto:
"prediction first, ontology later". **MT5 clock = BROKER SERVER TIME,
NOT UTC** (ARCH-009 ADDENDUM 2 clock doctrine; primary = US-DST
GMT+2/+3; second feed (Exness) = UTC year-round; cross-feed work aligns
clocks FIRST, piecewise by detected era). MT5 Files dir id
E92643EDFF963E7E489F140FDF338076; HC inputs written there by you AND
read back. NORMATIVE: EXECUTION_PROCESS_GUIDE.md + Blueprint_Amendments
_A1.md + the sealed notes in the journal (01KYDCNRM4/01KYDDMKQJ/
01KYE3BBE2 — the lens procedure lives in the LAST one).

## 2. State — the system corroborates, and still refuses to promote
- **First second_lens LIVE**: 01KYE3WCKK40PNJ8JEATQ4XTNT, tier=BROKER
  (independence is a SPECTRUM, declared never upgraded), agreement
  0.9544 ≥ sealed 0.95, empirically-detected US-DST eras (−2h winter /
  −3h summer; boundaries 2024-03-09, 2025-03-08), full guard-fired
  history in its notes. Gate (c) is now PAYABLE. Zero promotions: every
  hypothesis so far FAILed/INSUFFICIENT — that is the record, not a bug.
- **Verdicts**: H-001 FAIL · H-002 FAIL (weekend question answered;
  smc.fvg deprioritized, 502 trials) · H-003 INSUFFICIENT · H-004 FAIL
  (01KYDH7T6SH1D0AJMA70M2H0P8: +5.00/trade net but p=0.108 at n=56 —
  Monday drift indistinguishable from RANDOM TIMING; family
  seasonality.calendar = two attempts, no edge). Multi-window schema v3
  + calendar_day exit are live kernel surface (DEVQ-022).
- **Everything rebuilds**: rebuild_bulk.py + ingest/overlap --rebuild-
  bulk regenerate ALL datasets sha-assert-equal from journal + raw CSVs
  (committed in ivf/mt5/). Hand-copying is dead; the old worktree
  parquets are no longer load-bearing.
- **placebo_method sealed** from H-004 onward (registry+judge refuse);
  Wave-1 grandfathered.

## 3. Tally and standing rules
**Architect 17, Developer 4.** The S9 lessons that bind you: verify
against REAL data, never idealized assumptions (#15, #16); a criterion
you pre-register needs a tripwire — and honor the tripwire when it
fires on YOU (#17); rehearse checks end-to-end on raw data before
shipping (S9 first); machine-verify numerics; read back every write;
drills before checks, clean control; predictions recorded so they can
fail. IVF house style: check_s9_lens_multiwindow.py is the current
high-water mark (anchor → replay → recomputation → ordering →
structure).

## 4. Owner rhythm
Write window declared by Owner → author → read back → hand COMPLETE
commands → drill FIRST → check → HC (rev-2 tool, label from PROV, MONX
asserts same-Monday exit) → REV-SN → Go/No-Go → GO-SN(+retro) →
REWRITE THIS → ARCH-N+1 draft → Owner decisions → boot Developer (NEW
session). Verify-before-trust always: refs, journal tail, sessions/,
inbox, worktrees.

## 5. Carried items (in ARCH-010 draft)
1. TRIAL-ACCOUNTING ADR: hypothesis attempts currently append NO
   trial_count — H-004 ran at α=0.05 undeflated by H-003's attempt
   (FAIL was a-fortiori honest). Must be settled BEFORE any family's
   third try. Proposal: each registration appends trial_count 1 to its
   family, forward-binding.
2. Housekeeping: prune merged worktrees (arch-002 dir recycled; -41df8b
   dangling), gen_state regeneration discipline, t0_s9.py ruff nit.
3. Independent-Observation-Lenses naming (Owner architecture note) as
   lens work grows.

## 6. Immediate next steps
**ARCH-010 is FINAL** (both ◆s decided: retro-count YES; Wave-2 sweep
approved, S4 detector list unchanged) and carries the Owner's BINDING
recommendation: **Sprint 10 formally concludes GENERATION 1** — after
GO-S10 comes the Generation-1 Final Report + freeze + Gen-2 planning,
NOT ARCH-011 directly. Boot the Developer:
"Boot per CLAUDE.md, execute ARCH-010 completely, starting with T0.
Session log every session." Architect S10 duties: IVF for trial
accounting + the wave (drills first), HC, REV-S10, GO-S10, then author
GENERATION_1_FINAL_REPORT.md, record the freeze note, plan Gen 2 with
the Owner, rewrite this at the GENERATION boundary.
