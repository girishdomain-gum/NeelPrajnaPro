# Tech-debt register
Findings noticed outside a session's phase scope land here (see CLAUDE.md).

## Closed in Phase 5 (v5.0.0) — recorded for provenance, pruned from the active table
- **EG_* globals sweep** (review, 2–5): resolved *with residuals*. The whole
  legacy `DVBDASH_` dashboard (167 EG_ reads) is deleted; full deletion is NOT
  achievable (S15b ordering forces EG_ to stay the gate-internal source of truth).
  Exit proof = "zero ad-hoc EG_ consumers + a CLOSED sanctioned-residual list"
  (HANDOVER §Sanctioned EG_ residuals; CHANGELOG v5.0.0). Any addition to that
  list needs an explicit owner ruling.
- **ATR→L1 primitive** (phase3-s0): DONE — `MM_ATRPoints` retired to
  `Core/AtrMath.mqh::ATR_Points`; GateContext drops its Engine include.
- **B3 ATR reroute** (phase3-b3, ATR half): DONE — B3:640 calls `ATR_Points`
  directly (ctx-less lifecycle/replay paths → primitive, not ctx).
- **B3 ATR+spread lifecycle-ctx question**: resolved by ruling — do NOT thread
  ctx; the live-spread read is a self-contained downward call, left in-gate.
- **B3 warmup-spread quirk** (phase3-b3): CLOSED-as-assessed — live-spread-across-
  replay matches baseline; any fix would alter seeded state → baseline violation.
  Revisit only in a dedicated behavioral phase.
- **Legacy DVBDASH_ panel + toggle machinery** (phase3-s15 b): DONE — deleted whole.
- **UniverseEngine per-tick raw EG_ reads** (phase3-s15b b): now a documented
  sanctioned residual (ordering-locked), not debt.
- **ChartTheme.mqh orphan** (phase1): DONE in Phase 4 — wired into the new panel
  via `UI/Layout.mqh`.
- **Dashboard owns 2% rule + NPSU apply** (review): DONE in Phase 3 (moved to the
  pipeline + StrategyPortfolio behind `CMD_*`).

## Active register (genuine survivors)

| Date | Found in | Finding | Status / phase |
|---|---|---|---|
| 2026-07-21 | phase1 | TradeLogger (Core/L1) includes Engine/EntryGates (L2) and reads `EG_Bx_*`/`EG_T1_Last*` — the upward include remains. | **Deferred — sanctioned residual (v5.0.0).** Deal logging captures at trade-event timing (`DEAL_ENTRY_IN`), which precedes `SH_PublishAll`, so routing through StateHub would skew the research CSVs by one tick. Migration is a possible future *deliberate* value-identical change, never a sweep casualty. |
| 2026-07-22 | phase2b | No session-based entry block exists in code, though D6/spec assume one — is session gating a missing feature, or should SESSION leave the enum via ADR amendment? | Deferred — undecided; needs an ADR call. Not touched by Phase 5. |
| 2026-07-22 | phase3-s14 | Compute-pass consolidation (compute fn-ptr in descriptor, registry-driven compute) — the 13 `Bx_Evaluate` compute calls stay explicit in `EG_EvaluateAllGates` in exact legacy order (Decision A). | Deferred — needs proof of compute order-independence (or registry re-ordering to match legacy) with tester evidence. Not a deletion; out of Phase-5 scope. |
| 2026-07-22 | phase3-s15 | Gate-local `Bx_Init` `EG_Bx_Enabled = InpBx_Enabled` seeding not yet retired (7 gates — B1/B3/B4/T2/T7/T8/T9 — branch on their own enable inside Init; B3 does a full history recalc). | Deferred — removing changes init behavior and needs per-gate care; not required for the EG_ sweep (EG_ survives). |
| 2026-07-22 | phase3-s15b | Physical roster absorption — move `npsu_ros` ownership + `NPSU_ParseRoster` into StrategyPortfolio. | Deferred — a pure refactor, not needed by the tabs. |
| 2026-07-22 | phase4-p4-3 | NPSU engine + advisor line are not runtime-mutable (gates read `InpNPSU_Enabled`/`InpADV_Enabled`; MQL5 cannot reassign an `input`). Runtime toggling needs those inputs refactored to `CFG_`/runtime globals seeded at init. | Phase 6 (feature) — touches UniverseEngine/AdvisorEngine gating; wants a tester-gated slot. |
| 2026-07-22 | phase4-p4-3 | CTRL 2% stepper bounds are fixed constants (`TWOPC_MIN/MAX/STEP_PCT`) — no dedicated bound-input. | Phase 6 (feature) — add inputs only if the owner wants configurable bounds. |
| 2026-07-22 | phase4-p4-5 | SCOPE §3.5 recent-virtual: the VirtualBook ring retains only time+R for the last N closes; full detail (DIR/EXIT/MFE/MAE) survives only for the newest close. | Phase 6 (feature) — a true last-N detail ring needs VirtualBook instrumented; deeper history already in the UniverseLogger CSVs. |
| 2026-07-22 | phase4-p4-4 | VIRT UNIV §2.1 header wants `ROSTER {id}` but no roster-id field exists in StateHub/roster (renders counts instead). | Phase 6 (feature) — add a roster identifier if the owner wants the id shown. |
| 2026-07-22 | phase4-p4-4/5 | Spec-amendment candidates (in code comments): §2.1 SORT ships as a cycle button (no native MT5 dropdown); §3.3 equity ships as pixel-anchored vertical bars (OBJ_TREND unusable in a HUD). Both legibility-equivalent. | Doc — fold into a `dashboard_spec` amendment if accepted. |
| 2026-07-23 | v5.5.1 | Panel re-front signature now catches per-bar delete-and-recreate (type + bar-quantized anchor) but anchor-less per-tick movers (price-only OBJ_HLINE, e.g. trailed SL lines) still evade it and can paint over the panel between rebuilds. | Deferred — full fix needs OBJPROP_BACK on chart-side drawers (gate/TM change, out of UI scope) or a periodic forced rebuild; revisit if seen on-chart. |
| 2026-07-23 | v5.0.2 screenshot review | Spec-amendment candidates (owner-driven legibility redesign): opaque full-height body card behind every tab (spec assumed HUD-transparent bodies — unreadable over live gate drawings); LIVE §1.3 gains a SIGNAL section header + separators and plain-word verdicts; PANEL_BODY_H 414→456. | Doc — fold into the same `dashboard_spec` amendment. |

| 2026-07-23 | v5.2.0 | Legacy `CFG_CLR_*` names survive only as compatibility aliases in Config.mqh (HDR/SEC_A/SEC_B/INNER/BORDER/SECTION_LBL/BTN_*/TF_*/BAR_*). | Removal candidates for v5.3 — delete the alias block once every reader is migrated to the primary v5.2.0 tokens (grep must show zero old-name uses). |
| 2026-07-23 | v5.2.0 | LIVE + SCOPE vitals still build via two per-cell `LAY_Cell` loops; the spec's shared `LAY_KpiGrid` builder was deferred (LAY_Cell restyle achieved the visual with zero rename risk). | Phase-6 refactor candidate — consolidate when a third KPI grid appears. |
| 2026-07-23 | v5.2.0 | `PANEL_BODY_H` (456) retained by inspection after the LIVE session-row removal; not re-measured on a live terminal. | Verify on the first demo-chart sign-off; shrink if LIVE leaves a visible dead band. |

## Checkpoint findings

Referee-diff triage recorded per checkpoint. Environmental (broker-side)
differences are noted here so they are not re-litigated as regressions.

### Checkpoint 1 — Phase 3 gate migrations (2026-07-22)

**Verdict: PASS (execution-identical).** `report_baseline.html` vs
`report_baseline-phase3.html`, 1827 deals each. Differences confined to Swap
(4 deals) and Balance (1269 rows = cumulative carry from the first swap change
at deal 559 onward). Cause: broker swap-rate drift between baseline freeze and
re-run — environmental, not behavioural. All 11 execution columns byte-identical.
`diff_deals.py` default mode now encodes this (Swap/Balance advisory); referee
not re-frozen. `diff_deals.py --summary` output:

```
SUMMARY - 1269 differing row(s) of 1827 deal(s).

Columns that ever differ:
  Swap            4 row(s)   max|delta| = 0.09
  Balance      1269 row(s)   max|delta| = 0.21
Columns never differing: Time, Deal, Symbol, Type, Direction, Volume, Price, Order, Commission, Profit, Comment

Balance-tracks-cumulative-Swap check:
  rows with a Balance on both sides: 1827
  CONSISTENT - every Balance delta equals the running Swap delta.

Hypothesis (differences confined to Swap + Balance, Balance tracking cumulative Swap):
  SATISFIED - all differences are Swap + Balance, and Balance deltas track cumulative Swap exactly.
```
