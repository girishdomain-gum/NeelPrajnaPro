# NeelPrajna Overhaul — Phase Plan v1.1
Supersedes v1.0 (adds StrategyPortfolio, GateContext scope, Dashboard logic extraction).
Governing decisions: ADR-001. Process: NeelPrajna_Dev_Workflow_v1.0.md.
Rule: every phase ends compiling, with the Strategy Tester deal list matching the frozen baseline (byte-identical through Phase 3; documented-intentional diffs only in 4–6).

---

## Phase 0 — Repo bootstrap (once)
Create GitHub repo; commit v3.16.4 as-is, tag `v3.16.4-baseline`. Add `CLAUDE.md`, workflow doc, ADR-001, this plan, `tools/compile.bat`, `tools/backtest.bat`, `tools/baseline.ini`. Run backtest once; freeze `tools/report_baseline`. Move the .mq5 mega-comment version history into `CHANGELOG.md`.

## Phase 1 — Restructure (no logic change)
Folder layout per ADR-001 §2.1: `Core/ Gates/Bias/ Gates/Triggers/ Engine/ Apps/ UI/`. Fix all include paths in one sitting (MQL5 has no namespaces — all-or-nothing). Deliverable: identical behavior, clean include graph, one commit.
**Exit check:** compile OK · baseline diff byte-identical.

## Phase 2 — Communication spine (additive)
Add `Core/StateHub.mqh` + `Core/EventBus.mqh` (~400 lines). Domain/apps dual-write: legacy globals stay authoritative; StateHub populated alongside. EventBus wired but initially only logging. Add `exec.blocker` writes at every existing block site (spread, session, max-pos, retry).
**Exit check:** compile OK · baseline identical · manual: blocker text visible in log for a forced spread block.

## Phase 3 — Domain contracts (the heavy phase)
3a. `Gates/GateBase.mqh` + `GateContext` (spread, session, ATR, symbol info — everything gates currently pull from TM_/MM_).
3b. Migrate gates **one per commit**, simple first: B1, B2, B6, T1, T7, T8, T9, B3, T2, B4 → then T5, T4, T3 last. (Session-0 inventory correction: these three carry NO direct TM_ calls; T3/T4's only upward call is `MM_ATRPoints` → `ctx.AtrPoints` and T5 is a pure wrap. They go last for size/regression-surface, not double effort — see `phase3_gate_recipe.md`.)
3c. EntryGates → registry walk over GateBase; 2% rule moves from Dashboard into the pipeline (Dashboard keeps only the button posting `CMD_TWOPC_ARM`).
3d. **StrategyPortfolio** (`Apps/StrategyPortfolio.mqh`): absorb UniverseRoster registry role; introduce named active real strategy; move `BD_NPSU_ApplyStrategy`/restore out of Dashboard behind `CMD_APPLY_STRATEGY`; enforce ADR-001 §2.6 (real = one strategy, radio; concurrency virtual-only). UniverseEngine/Advisor/MetaSwitcher consume portfolio entries + StateHub instead of raw EG_ pulses (pulse birth/consumption semantics preserved exactly — design doc §6).
**Exit check per commit:** compile OK · baseline byte-identical · on-chart toggle round-trip test · NPSU apply/restore round-trip test.

## Phase 4 — Dashboard rewrite
`UI/Layout.mqh` (vertical-flow engine: Row/Chip/Cell — replaces hand-computed pixel constants) + `UI/Widgets/` (Chips, GateGrid, TFCandles, NPSUTable, PositionPanel, Buttons). Dashboard orchestrator ~300 lines; renders StateHub only, posts commands only. Tabbed panel: GATES · TRADE · NPSU · STATS. Keep Dark HUD theme via Core/ChartTheme.
**Exit check:** compile OK · baseline identical (UI must not change trading) · visual sign-off on demo chart · toggle/apply round-trips.

## Phase 5 — Legacy removal
Delete EG_ bulletin-board globals and all dual-writes; StateHub becomes sole source. Remove dead Dashboard code paths.
**Exit check:** compile OK · baseline identical · grep proves zero EG_ reads outside EntryGates/Gates.

## Phase 6 — New features (intentional behavior/UI additions)
Equity + drawdown sparkline (deal history) · per-gate win-rate % beside n·$ scoreboard · session clock strip (Asia/London/NY) · per-position BE / partial-close buttons (via `CMD_*`). Each feature its own commit + baseline note ("UI-only" or documented behavior change).
**Exit check:** compile OK · diffs documented · owner sign-off per feature.

## Effort & risk snapshot
| Phase | Size | Risk | Notes |
|---|---|---|---|
| 0 | small | low | paths in .bat need local MT5 fix |
| 1 | mechanical | low | all-or-nothing include fix |
| 2 | ~400 new lines | low | additive only |
| 3 | largest | medium | T3/T4/T5 last for size/regression-surface (not double effort — Session-0 inventory found no direct TM_ calls); one gate per commit keeps it bisectable |
| 4 | −2,000 net lines | medium | trading risk ~zero if Phase 3 done right |
| 5 | deletion | low | grep-verifiable |
| 6 | additive | low–med | research features |

## Standing risks
Tester nondeterminism → pinned model/date-range, cached history, never compare across history re-downloads. Dual-state window (Phases 2–4) → legacy authoritative until Phase 5; toggle round-trips tested on-chart each Phase-3 commit. Scope creep → one phase, one branch, one plan reference per Claude Code session.
