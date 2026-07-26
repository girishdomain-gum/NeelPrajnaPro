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

---
## CANDIDATES REPORT (Exploration Wave 2 — developer, 2026-07-26)
Appended per §3 AC ("a candidates report, families ranked, honest
multiplicity figures, for the Owner"). This wave produced CANDIDATES only —
**no hypothesis was registered** (registration is a Sprint-11 decision with
the Owner). The 2025-VIRGIN reserve is UNTOUCHED (still VIRGIN-designated, 0
burns reference it; total window_burn count unchanged at 5).

### What ran
The UNCHANGED S4 detector suite (`smc.fvg`) and the UNCHANGED 500-variant grid
(`hold_bars 1..25 × strength_min 0.0..0.9 × {long,short}`) over the
**2025-TRAINING** window `01KYDE784029NZNXPPN5PA8P8G` — a NEW year, same market,
same telescope. Reserve-safe by construction: the primary feed parquet spans
2024+2025 incl. the reserve, so the bars were sliced to the training interval
FIRST (`ts_start <= ts < ts_end`, the battery's own rule) and events detected on
that slice alone — an explicit guard asserts the slice ends before the VIRGIN
start. Screened in 13.1 s.

Records appended (journal 78 → 83, chain GREEN):
- bars slice `01KYED4A1YP8AZZ4M87AHATBRY` (`xauusd_h1_primary_2025train`, 4143 bars)
- FVG events `01KYED4AJ1MR7PSCNJXKB25Q6R` (851 events)
- shortlist manifest `01KYED4QB699QHXNBB0YH93M4N` (500 ranked rows)
- **trial_count `01KYED4QC5XYMRNMKP9AW2G8V6` (n=500, source=screener, family
  `xauusd_h1/smc.fvg`)** — every configuration counted from birth (§1)
- shortlist note `01KYED4QCVRZ38T0HARNGQVA4E` (declares metric + thresholds
  BEFORE ranking: net_sharpe; min_trades 30, min_sharpe 0.10, net_total > 0)
All three parquet datasets rebuild byte-identically via
`wave2_screen_s10.py --rebuild-bulk` (sha assert-equal, no journal writes).

### Families ranked, with honest multiplicity
One family was searched (the S4 suite is single-family):

| Family | Wave-2 trials | Family total m (after retro-count) | effective_alpha @ base 0.05 |
|---|---|---|---|
| `xauusd_h1/smc.fvg` | 500 | **1004** | **4.98e-5** |

The honest burden is the headline. `xauusd_h1/smc.fvg` now carries **1004**
recorded trials (502 from the 2024 estate + h001/h002 registrations retro-counted
this sprint + 500 from this wave). Any future FVG claim on this market is judged
at effective_alpha ≈ **5e-5**, not 0.05 — a ~1000× penalty. This is the ADR-011
machinery working as designed: pointing the telescope at a new year does not buy
back the multiplicity already spent on the family.

### The leads (screen-admitted; NOT edges)
39 of 500 variants cleared the screen's soft thresholds — **all long**, hold
7–25, strength_min ≤ 0.3 (the short side never cleared the 30-trade floor: its
few high-Sharpe variants had n=2). Best by the declared metric:

| rank | hold | smin | side | n | net_total | net_sharpe |
|---|---|---|---|---|---|---|
| 36 | 23 | 0.3 | long | 60 | 581.9 | 0.271 |
| 38 | 22 | 0.3 | long | 60 | 589.4 | 0.266 |
| 37 | 21 | 0.3 | long | 60 | 512.1 | 0.267 |
| 55 | 20 | 0.0 | long | 172 | 627.3 | 0.155 |

**Read these as leads, not results.** Screen admission is a soft filter
(min trades + positive net + a low Sharpe floor), NOT a significance test. The
strongest admitted variant is net_sharpe ≈ 0.27 over 60 trades; a crude
`net_sharpe·√n` scale tops out around **2.1** across all 39 — nowhere near what an
effective_alpha of 5e-5 would demand of a registered claim. A clustered long-only,
mid-hold, low-strength signature on one training year is exactly the shape a
screener surfaces from noise; whether any of it survives a pre-registered,
placebo-controlled, deflated verdict is the Sprint-11 question — to be decided
WITH the Owner, on a fresh window, under the trial burden recorded above.

### Recommendation to the Owner (Sprint-11 input, not a decision)
The FVG family is now expensive to the point of near-prohibitive (m=1004). If a
Wave-2 lead is ever promoted to a hypothesis, it should be a SINGLE, sharply
pre-registered variant (not a re-sweep), judged on the 2025-VIRGIN reserve, and
it must clear ~5e-5 — a very high bar the honest ledger now enforces. The
alternative the estate points to: a genuinely new instrument family (new claims,
fresh multiplicity), which is a Generation-2 conversation.
