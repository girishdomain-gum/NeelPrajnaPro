# EXECUTION PLAN — the one living document: phases, sprints, and their outputs
*Version 1.0 · 2026-07-29 · This document absorbs and supersedes: NP_INTEGRATION_EXECUTION_ROADMAP.md, ARCH-NP-001_H07_Integration_Sprint.md, H07_SEALED_MECHANICAL_DEFINITION_v1.0.md, ARCHITECT_HANDOVER_NP.md (all preserved in docs\archive\ and in git history). From now on: sprints are planned here, and their OUTPUTS are appended here when they close. One document, black and white, versioned in git and in the Change Record.*

---

## 0. CURRENT STATE (rewritten at every sprint boundary — this is the handover)
**As of 2026-07-29 evening:** Repo bootstrapped, full Gen-1 history on GitHub (commit 3609350+). Estate RATIFIED (Owner memo in JOURNAL). H-07 definition SEALED (§3 below). Rulings in force: Auto-Adopt DISABLE pending hysteresis · cost model `xauusd_retail_h07` · claim form E2 · vision ruling (VISION.md). Legacy repos paused. **Blocking items, all Owner, all typed lines: (1) H-07 window designation, (2) neelprajna α-budget, (3) Go/No-Go on Sprint NP-S1.** On Go: Developer boots per §2 boot sequence.

## 1. The phase ladder
```
 PHASE 0            PHASE 1: NP-S1        PHASE 2: NP-S2       PHASE 3: NP-S3        PHASE 4: NP-S4
 BOOTSTRAP+RATIFY   H-07 TWICE-JUDGED     R6 LONG RUN          FAMILY MIGRATION      ACCEPTANCE & GATE
 ✅ DONE 2026-07-29  detector certified ·  3–6mo real tick ·    Owner ruling on 17 ·  blinded NB-1..NB-5 ·
                    sealed dual reg ·     withheld OOS by      certified detectors   console ruling ·
                    real Battery run ·    typed phrase ·       one by one ·          runtime-consumption
                    B1–B7 comparison ·    data-quality report  verdicts as data      design ruling ·
                    18 attempts counted                        permits               Wave-1 review
```
Cadence: quality gates, not clocks. Per-sprint rhythm (Gen-1's, proven): instruction → Developer sessions → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → §0 rewrite. Cross-track: NP-S1/S2 need only Gen-1-certified machinery; Gen-2 S1–S8 runs parallel (its plan: GEN2_EXECUTION_ROADMAP.md, carried forward, its own single doc). Standing tripwires: documents-without-verdict sprint = No-Go finding against the Architect; any evidentiary use of the retired bespoke stack = finding against the invoker.

## 2. SPRINT NP-S1 — H-07 twice judged (instruction: sealed on Owner Go)
**Preconditions:** ☑ F-13 ruled (Auto-Adopt NONE) · ☑ cost model named `xauusd_retail_h07` (frozen once cited) · ☑ definition sealed (§3) · ☐ Owner window designation · ☐ Owner α-budget.
**Deliverables:**
1. `qrf/trading/concepts/neelprajna/liquidity_sweep.py` — standard Detector contract; implements exactly §3's events and frozen parameters; MQL5 gate + `np_feature_service.py` are reference only, §3 is normative.
2. `planted_cases()` — planted-truth + clean-control cases; all frauds caught, silence on clean, before any real run.
3. `configs/hypotheses/h007_np_liquidity_sweep.yaml` — TWO sealed registrations, both priced at birth: (a) prediction claim, judged this sprint by the real Battery vs random-timing placebo; (b) E2 existence claim (N2 nulls), judged when null machinery certifies.
4. One real `EvidenceBattery.run()` on the designated window over the same 324-trade population B1–B7 judged (recorded bespoke verdict: FAIL on cost sensitivity).
5. **The comparison report** — nine steps vs B1–B7, gate by gate, mapping and every agree/disagree interpretation sealed before the run.
6. Remaining 17 founding hypotheses registered as counted attempts (ledger entries only).
**Acceptance criteria (sealed):** AC-1 all plants caught, zero events on clean · AC-2 anti-hindsight property test passes (no retroactive emissions) · AC-3 exactly one verdict + one burn, atomic, on the designated window · AC-4 comparison report exists, every divergence named with cause; agreement is corroboration, divergence is the sprint's most valuable output; the drilled instrument's verdict stands, never averaged · AC-5 family trial count ≥ 18 · AC-6 IVF re-derives the verdict from normative texts after its own planted-fraud drill.
**Non-goals (violations are findings):** no live-execution/TradeManager/NPSU changes; no hypotheses beyond H-07 (registrations excepted); no console work; no edits to `ivf/**`, ledger internals, or normative docs.
**DEVQ triggers:** MQL5→Python semantic ambiguity; unfillable EventFrame fields; export/adapter mismatch; window-vs-population disagreement; anything the cost ruling leaves undefined; §3's parameter-mismatch trigger. Silence binds no one.
**Developer boot sequence (on Go):** read docs\constitution\, docs\scientific_model\, docs\architecture\ (the .md twin) masters in that order → this document's §2+§3 → docs\vv_plan\ master §§1–3; fresh worktree; DEVQ at every ambiguity (the definition's §3 names one explicit trigger); the sealed definition is normative — MQL5 and `np_feature_service.py` are reference only; first commit sweeps `ops/*.ps1`.

## 3. H-07 SEALED MECHANICAL DEFINITION v1.0 (frozen; changes = v1.1 by NP-ADR, never edits)
*Source: `F:\NeelPrajna\repo\Gates\Triggers\T3_SweepFVGGate.mqh` v2.1 pool engine, read from source 2026-07-29. Owner rulings: claim form E2; cost model `xauusd_retail_h07`.*
**Observed events (closed bars only; anti-repaint):**
- **POOL_FORMED** — ≥ pool_min_touches pivot highs (EQH) / lows (EQL) clustered within pool_tol; level FROZEN at formation (average of member pivots), never drifts; rebuilt once per closed anchor bar over pool_lookback.
- **SWEEP** — closed exec bar opens inside the defended side, wicks through the frozen level, closes back (rejection). Gap-through opens are NOT sweeps. Furthest wick tracked as swing extreme.
- **REVERSAL_CONFIRMED** — within mss_max_bars, a closed exec bar closes beyond the pre-sweep swing (extreme of prior swing_lookback closed bars). Its bar is the earliest permissible emission.
**Frozen parameters:** anchor TF H1 · exec TF M1 · pool_lookback 500 H1 bars (cap 2000) · pool_pivot_len 3 · pool_min_touches 2 · pool_tol 0.15×ATR14(H1) · swing_lookback 10 · mss_max_bars 30. *(Source symbols: InpT3_PoolLookback/PoolPivotLen/PoolMinTouches/PoolTolPoints/SwingLookback/MSSMaxBars.)* Trade-blueprint stages (displacement, FVG, OB, tap, entry/TP modes) are prediction-layer playbook, excluded. **DEVQ:** if the 324-trade export ran under non-defaults, halt; re-seal as v1.1.
**Observation Space:** XAUUSD retail feed, broker-tier · mt5_csv/OBS-4 · H1 pools/M1 events, seams from data · regime-conditioned (2024–26 trending gold) · neelprajna family, α-budgeted · events conditioned on POOL_FORMED · Owner-designated seen window · detector v1.0 certified L1–L3 first.
**Claim form E2 (Owner-ruled):** definition trap applies (pool_tol/min_touches buy the base rate → E1 uninformative); testable content = arrangement: does REVERSAL_CONFIRMED follow SWEEP beyond chance timing (clustering, transition frequency, time-to-reversal)? **Two-claim structure:** E2 existence — registered+counted NP-S1, judged when N2 certifies; prediction claim — judged NP-S1 by Gen-1 Battery vs random-timing placebo (the twice-judged comparison); no phenomenon declared "established" by a prediction-gate verdict.
**Null design N2** (block resampling, seam-preserving, calendar-template): destroys cross-bar arrangement, preserves sessions/volatility character; N1 rotation can't destroy within-day arrangement; N3 reserved as sealed robustness companion. Block length, seeds, thresholds sealed in the YAML before data is touched.

## 4. SPRINT NP-S2 — R6 long run
3–6 months real-tick collection; Owner types the withheld-OOS designation BEFORE collection completes (reserve-by-market-time); EA-side R6 files run under the bridge (**requires scoped lab unpause ruling**); exports flow via mt5_csv into designated windows; no judging. Exit: dataset designated, hashed, untouched beyond designation; data-quality report (gaps/seams/DST from data) on record. *This sprint manufactures the evidence every open question is starved of.*

## 5. SPRINT NP-S3 — Family migration
Opens with the Owner's ruling on the 17 (informed by AC-4's report): subset, priority, n-floors. Certified detectors one by one (planted cases each; no shortcuts by origin); sealed registrations; Battery runs as designated data permits; E2 judgments as null machinery certifies; deferrals recorded and priced. Exit: neelprajna is a real, honestly-counted family; every verdict treated as the result it is.

## 6. SPRINT NP-S4 — Acceptance & gate
Blinded campaign NB-1..NB-5 per VV_PLAN (Owner holds answer keys; negative-control instrument; tamper drills; stranger audit). Then Wave-1 review and Owner boundary rulings: console unblock · runtime-consumption design (Contract v2; arming stays permanently human) · Wave 2 / close / revise. Exit: the integration is an accepted instrument, or the campaign says precisely why not.

## 7. Pre/parallel work orders (details: docs\automation\ master §6)
WO-A doc truth pass · WO-B A4.0 tester-screenshot spike (gates NP-S3/S4 visuals; needs lab unpause) · WO-C cross-repo evidence linkage · WO-D windows-register consistency check.

## 8. SPRINT OUTPUTS (appended at each close — empty is honest)
*(none yet — the first entry here will be NP-S1's: verdict id, comparison-report summary, findings, retro, GO record)*

## Change Record
- v1.0 (2026-07-29): consolidation per Owner ruling "one doc per thing" — absorbed roadmap, ARCH-NP-001 (ratified 2026-07-29, pending seal on Go), sealed H-07 definition v1.0, handover; predecessors archived.
