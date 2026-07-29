# NeelPrajna — Project Handover (v5.0.0)

**Purpose of this file:** any AI or person opening this zip cold must be able to
resume the work with no other context (the "no-dependency" rule, design doc §8.4).

## What this is

NeelPrajna is an MT5 Expert Advisor (XAUUSD / BTC, one auto-calibrating build)
built as a RESEARCH system. Owner: Girish (non-native English speaker — keep
explanations simple and step-by-step). No real-money trading planned short-term;
everything serves backtest research.

**Entry model — BIAS × TRIGGER:** `Entry(D) = ALL enabled BIAS gates agree on
direction D AND ANY enabled TRIGGER gate fires a pulse in D.`

| Gate | Kind | File | Notes |
|---|---|---|---|
| B1 Nexis MA crossover | bias | B1_NexisGate.mqh | |
| B2 MTF closed-candle colour | bias | B2_MTFCandle.mqh | |
| B3 key-level liquidity | bias | B3_KeyLevelGate.mqh | |
| B4 SMC structure | bias | B4_SMCGate.mqh | |
| B6 RegChannel MTF trend quality | bias | B6_RegChannelGate.mqh | v3.16; exact-OLS regression channels (Higher/Primary/Lower windows, auto TF presets) — slope agreement + per-window Pearson-R quality cut (`InpB6_MinR`); OVERLAPS B1 by construction, test as replacement AND addition (roster R5) |
| T1 Pattern (A + opt-in S) | trigger | T1_PatternGate.mqh | Owner's most trusted gate — never remove. Pattern A = 3-candle reversal; Pattern S = sweep-and-reclaim (v3.5, `InpT1s_Enabled`) |
| T2 AutoFibo | trigger | T2_AutoFiboGate.mqh | |
| T3 Sweep+FVG | trigger | T3_SweepFVGGate.mqh | |
| T4 TrendLines | trigger | T4_TrendLinesGate.mqh | can "join chain" as extra bias (`InpT4_Mode`); v3.15: PrecisionTrendPro v4.1 parity — 3 line groups L/M/S, angle labels |
| T5 Topography | trigger | T5_TopographyGate.mqh | |
| T7 Market Metrics (SMM HA momentum) | trigger | T7_MarketMetricsGate.mqh | v3.2; arrows-only visuals |
| T8 CMH Candlestick Patterns | trigger | T8_CMHCandleGate.mqh | v3.14; full signal-core port of the standalone CMH suite v1.5 (27 patterns, quality score, zones/trend gates); `InpT8_ConfirmBars` 0=immediate/provisional, N=confirmed-late; SL = pattern extreme |
| T9 CCC Hidden Patterns | trigger | T9_CCCHiddenGate.mqh | v3.14; full signal-core port of the standalone CCC suite v4.0 (merged-candle hidden reveals, 3 handbook gates, quality score); SL = merged-window extreme |
| T6 | — | RETIRED | A/B test concluded, removed v3.1 |
| B5 Money-Flow | — | RETIRED | superseded by T7's MFI gate, removed v3.4 |

**Trigger contract:** pulse held until the REAL path trades it
(`Tx_MarkConsumed`, consume-on-success only) or the gate expires it.
`EG_Tx_SL/TP/HasLevels` carry levels; TP=0 → RR-derived.

**Magic offsets (NEVER change):** base+0 manual, +1 chain, +3 T1, +5 T2, +8 T3,
+9 T4, +10 T5, +11 RETIRED(T6), +12 T7, +13 T8, +14 T9. `InpMagicBase=26071100`,
span 32.

## Non-negotiables

UTF-8 only. Closed-bars-only anti-repaint (replay history, fire live only).
No silent failures (throttled journal + dashboard indication). Magic filtering
everywhere. No ✓/✕ glyphs on dashboard labels. Semver: bump `EA_VERSION` in
Config.mqh AND `#property version` together. Static verify (braces/symbols/
duplicates) before zip — CTsLogger.mqh shows a known FALSE-POSITIVE brace
mismatch (apostrophe in a comment); the file is untouched and compiles.
Light-theme chart rules: text-only overlays, dark slate text, no background
rectangles. MQL5 gotchas: array initializers need constants; check every Copy*
return; tick volume is the only volume on retail MT5.

**Official evaluation rule (survival-first):** max drawdown → worst losing
streak → ranging-week behaviour → profit factor. Never raw ROI. A winner must
validate on an unseen period (multiple-comparisons bias).

## Architecture (v5.0.0 — post-overhaul)

The Phase 1–5 overhaul (ADR-001) restructured the EA into layers whose includes
point DOWNWARD only. Every phase ended execution-identical to the frozen
baseline; v5.0.0 (Phase 5) deleted the legacy world, proving the thesis a last
time. The layout:

- **Core/ (L1 primitives):** `Config` (single-source version + all `Inp*`/`CFG_*`),
  `StateHub` (`g_state` — the EAState struct the UI renders) + `StateHubPublish`
  (mirrors engine state into `g_state` each tick), `EventBus` (command queue —
  panel posts `CMD_*`, `Cmd_Dispatch` routes), `AtrMath` (`ATR_Points()` — the ATR
  primitive, extracted from MoneyManager in v5.0.0), the CSV loggers.
- **Gates/ (L2 domain):** `GateBase` + `GateContext` (the per-tick,
  direction-agnostic market snapshot the pipeline builds once and passes down to
  each gate's `Evaluate(ctx, dir)`). Gates make NO upward `TM_`/`MM_` calls;
  ATR comes via `ctx.AtrPoints()` → `ATR_Points()`. `Gates/Bias/*`, `Gates/Triggers/*`.
- **Engine/ (L2):** `EntryGates` (the pipeline: `EG_EvaluateAllGates` → `EG_OnTick`,
  owns the `EG_*` gate globals), `MoneyManager`, `TradeManager` (all trade ops go
  through TM), `TwoPCRule`.
- **Apps/ (L3 research):** `StrategyPortfolio` (the registry + the one applied real
  strategy, radio; ADR-001 §2.6), `UniverseEngine`/`UniverseRoster`/`VirtualBook`/
  `AdvisorEngine`/`MetaSwitcher` (the NPSU shadow-universe system).
- **UI/ (L3):** `Panel` (the ONLY on-chart panel since v5.0.0 — the tab-driven
  `NPUI_` panel: LIVE · CTRL · VIRT UNIV · SCOPE), `Layout` + `Widgets/*`. Renders
  `g_state` only, posts `CMD_*` only. The legacy `DVBDASH_` `Dashboard.mqh` and its
  `InpUseNewPanel` flag were deleted whole in v5.0.0.

**Data flow each tick:** `EG_EvaluateAllGates` (writes `EG_*`) → `EG_OnTick`
(entry path; also runs `NPSU_OnTick` inside it) → `SH_PublishAll` (mirrors `EG_*`
→ `g_state`) → `Panel_Update` (renders `g_state`).

### Sanctioned EG_ residuals (v5.0.0 — CLOSED list)

Full deletion of the `EG_*` bulletin-board globals is NOT achievable
execution-identically: **`NPSU_OnTick` runs inside `EG_OnTick`, before
`SH_PublishAll`** — so at NPSU's read point `g_state` still holds the PREVIOUS
tick. `EG_*` therefore stays the gate-internal source of truth. The Phase 5 exit
proof is "zero *ad-hoc* EG_ consumers, with this CLOSED set of documented,
sanctioned readers." **Adding to this list requires an explicit owner ruling — it
is not a growing exemption category.** Each site is annotated in-code
("SANCTIONED EG_ RESIDUAL"). The readers outside `Engine/EntryGates.mqh` + `Gates/`:

| File | Symbols read | Why sanctioned |
|---|---|---|
| `Core/StateHubPublish.mqh` | `EG_Bx_*`, `EG_Tx_*`, `EG_BiasBuy/Sell`, `EG_BuyEnabled/SellEnabled`, `EG_AutoEntry`, `EG_ManualFire`, `EG_lastFailedAttempt` | It IS the read-only publish bridge — mirroring gate internals into `g_state` is its designed job. |
| `Apps/UniverseEngine.mqh` | `EG_Tx_Buy/Sell/HasLevels/SL/TP`, `EG_Bx_Buy/Sell`, `EG_T1_VariantTag`, `EG_BIT_*` | Ordering-locked (S15b): reading `g_state` would inject a one-tick lag into the rising-edge birth-time logic. Retires only WITH the EG_ internals. |
| `Apps/UniverseRoster.mqh` | `EG_BIT_*`, `EG_Bx/Tx_Enabled`, `EG_InitFailMask` | Registry mask/enable vocabulary (builds + validates universe masks). |
| `Apps/StrategyPortfolio.mqh` | `EG_BIT_*` | Registry mask→`Bx_SetEnabled` application. `EG_BIT_*` are compile-time macros, not runtime globals. |
| `Core/TradeLogger.mqh` | `EG_Bx_Enabled/Buy/Sell`, `EG_T1_LastFireTime/LastVariant/LastSweepATR/LastBodyATR` | Deal logging fires on trade-event timing (`DEAL_ENTRY_IN`, inside the entry path) while StateHub publishes at tick-end — `g_state` would lag one tick at capture and skew the CSV. These CSVs are research truth; we do not trade research-data fidelity for include-graph tidiness. Migration is a possible future *deliberate* change with its own value-identity argument, never a sweep casualty. |

`Core/StateHub.mqh` and `Engine/MoneyManager.mqh` contain only EG_ *comment*
references (no code reads); `NeelPrajna.mq5` uses only the `EG_*` function API
(the engine's public interface), not the bulletin board.

## NPSU — shadow universes (NEW in v3.6.0)

Up to 16 virtual strategies (bias-subset × trigger-subset × trail/be/rr
overrides) run in parallel inside one EA run, each with an R-denominated
VirtualBook, streaming closed virtual trades to CSV. U0 MIRROR copies the real
config to validate the simulator. Full design: `NPSU_Design_Doc_v1.6.md`
(shipped in this zip). Key files: UniverseRoster.mqh (DSL parser + default
12-universe roster), VirtualBook.mqh (gap-aware bar-close fills, pessimistic
same-bar rule, shared MM trail helpers), UniverseEngine.mqh (per-universe pulse
consumption — never calls Tx_MarkConsumed), UniverseLogger.mqh (NPSU-T1 /
NPSU-S1 schemas + auto-written data dictionary sidecar). The real path is
bit-identical with NPSU off, and unaffected with it on (read-only signal layer).
Enable via `Presets/NP_NPSU_default.set`. Analyze with
`analyzer/np_universe_analyzer.py <Common\Files folder>` (pandas+matplotlib).

## CSV outputs & schemas

`NP_Trades_*` = real trades (schema NPT-2; NPT-1 lacks schema_version).
`NPSU_Trades_*` = virtual trades (NPSU-T1). `NPSU_Summary_*` = append-only
per-universe snapshots (NPSU-S1). All files of one run share `run_id`.
Column meanings: `NP_DataDictionary_NPSU-1.md` (auto-written next to the CSVs)
and design doc Appendix A.

## Version history

3.0 handover baseline → 3.1.0 T6 out, B5 in → 3.2.0 T7 in → 3.3.0 B5/T7
drawings → 3.4.0 B5 removed, T7 arrows-only → 3.5.0 T1 Pattern S + TradeLogger
CSV → 3.6.0 NPSU shadow universes + self-describing logs → **3.6.1 NPSU strategy FILES (this release): one plain-text file in `Common\Files\NPSU_Strategies\` = one virtual universe; folder auto-bootstrapped with the default roster + README on first run; add/edit/delete files without recompiling** → **3.6.2 (this release): summary snapshots every `InpNPSU_SummaryMins` chart-minutes (deinit no longer the only writer), every export journals its row count; AT-2 mirror parity PASSED on first tester run (3/3 trades matched, mean gap 0.045R) → **3.6.3 (this release): loose coupling — the EA only READS the strategy folder, never writes it; `analyzer/np_strategy_generator.py` generates it (default roster / --grid combinations / --clear / --list) → **3.6.4 (this release): EA prints ABSOLUTE paths of all input/output files at start and exit; `analyzer/README.md` documents the full generate→backtest→analyze loop → **3.7.0 (this release): LIVE ADVISOR (Phase 3, design doc §13) — AdvisorEngine.mqh evaluates all universes every `InpADV_EvalHours` over a rolling `InpADV_WindowDays` window (ring buffer of last 256 closed virtual trades per book), survival-first ranking, eligibility = ≥`InpADV_MinTrades` window trades + strategy-file key `validated=1` (MIRROR validated by definition), hysteresis = `InpADV_ConfirmEvals` consecutive wins before the recommendation changes; outputs journal + dashboard + `NPSU_Advisor_*.csv` (schema NPSU-A1, in data dictionary NPSU-2) + optional Alert(). STRICTLY ADVISORY — never trades, never auto-switches** → **3.7.1 (this release): NPSU chart PANEL — dashboard-style toggle button (`NPSU_BTN`), rows = rank | strategy | EQ(R) | P/L wins/losses | win% | floating R of open virtual trade, green/red by equity, `*` marks the advisor recommendation, sortable by equity or wins (`InpNPSU_SortBy`), advisor status line always visible incl. warming-up state** → **3.7.2 (this release): advisor ON ⇒ dashboard CANDLE TIMEFRAMES starts collapsed + NPSU panel starts open (vice versa; both stay click-toggleable), theme-adaptive panel colours (clrNONE = auto by chart background), panel default position beside the dashboard** -> **3.8.0 (this release): dashboard REDESIGN - the NPSU table is a native dashboard section sharing the CANDLE TIMEFRAMES slot ([NPSU]/[TF] swap button in the section header; the [-] collapse still works in both modes); floating panel and its inputs removed; rows rank|strategy|EQ(R)|P/L|win%|floating-R in the dashboard HUD palette, star+gold marks the advisor recommendation; advisor ON means the slot starts in NPSU mode (vice versa)** -> **3.9.0 (this release): ONE-CLICK APPLY (Girish) - every NPSU row has a gate-style swatch button; clicking APPLIES that universe (bias+trigger gates via Xx_SetEnabled, trail/BE/RR via CFG_*) to the REAL account, radio-style max one active; click again or the master header swatch = restore preset defaults; SESSION-ONLY (reattach resets), loud journal on every apply/restore, InpNPSU_AllowApply gates the feature; master swatch green = some strategy applied. NOTE: after an apply, U0 MIRROR still mirrors the INIT-time config - the applied universe's own row is the live benchmark** -> **3.10.0 (this release): VERIFICATION SUITE (Girish: who verifies the virtual trades?) - four layers: (1) mirror parity vs real trades, (2) NPSU_Audit_*.csv schema NPSU-D1: every OPEN/BE/TRAIL/CLOSE with bar OHLC + justification refs (`InpNPSU_Audit`), (3) analyzer/np_trade_verifier.py: independent re-implementation, Level 1 rule-checks the audit, Level 2 `--bars` replays every trade against MT5-exported M1 bars (rules R1-R9; tested to catch corrupted trades), (4) runtime invariant checks (fill inside closing-bar range) with loud VIOLATION banner; plus `InpNPSU_DrawUniverse` draws one universe's virtual trades on the chart for eyeball audit** -> **3.10.1: apply swatches highlight exactly like gate toggles** -> **3.11.0 (this release): RUNTIME AUTO-ADOPT (Director's decision; reverses the advisory-only default under research conditions) - `InpADV_AutoAdopt` = NONE(default)/WIN_RATE/EQUITY/LAST_TRADE; after warm-up (`InpADV_AutoWarmup`=10 trades per universe, `InpADV_AutoRequireAll` optional) the EA adopts the best performer through the SAME apply path as a human click (loud journal, panel highlight, session-only), rate-limited by `InpADV_AutoCooldownMins`; the auto-switcher is itself a strategy under test - real-trade rows carry config snapshots so Python can judge switching vs holding. Architect's recorded objection: win-rate ignores trade size, last-trade is n=1 evidence; of the three prefer EQUITY; backtest-only until validated** -> **3.12.0 (this release): META-SWITCHERS (Fable's counter-proposal, Girish approved) - M_EQUITY/M_WINRATE/M_LASTTRADE race as virtual universes (ids 16-18, NPSU_MAX now 19) inheriting the held strategy's closed trades via the shared _VB_Accumulate path; fairness: closed-trades-only, switch applies to trades opening after it, warm-up + cooldown, ADOPT audit rows; metas cannot be recommended or applied to real; analyzer gains 'Meta-switchers vs holding' section; PRE-REGISTERED predictions recorded in design doc 13.8 BEFORE data (Fable: EQUITY~=best-hold, LASTTRADE below; Girish: in-form adapts best). Rule: a criterion may drive the real account only after its meta wins in backtest + OOS** -> 3.12.1 panel paging (best on page 1, U0/applied/advisor pinned) -> 3.12.2 audit logs BE and TRAIL separately + verifier ADOPT/armed-BE/rounding fixes (found by verifying the real 9-day run 22078: 1,273 trades certified, regime shift observed, pre-registered predictions scored - switching did not beat holding, LAST_TRADE best criterion) -> **3.12.3 (this release): ROSTER R2 as generator default (15 strategies: 4 new hypotheses T1_pure/T1_rr15/T1_B2/T2_solo + controls kept), versioned report labels (--label <ROSTER>-<PERIOD> in np_post_validation.py, ROSTER_VERSION.txt in strategy folder), NP_REAL_default.set (formalized real baseline B1|T1 + promotion rule) and NP_NPSU_longrun.set (the long-backtest preset)** -> **3.13.0 (this release): capacity raised to 59 strategy FILES (NPSU_MAX_UNIVERSES 63; metas now ids 60-62); the 15 InpNPSU_U string inputs are LEGACY FALLBACK only — files are the roster. Strategy files always load from Common\Files\NPSU_Strategies (MQL5 sandbox: EAs cannot read the Experts folder; Common is the only location shared with tester agents).** -> **3.14.0 (this release): TRIGGER GATES T8 + T9 — full signal-core ports of the owner's two standalone indicator suites into single-file NeelPrajna gates: T8 = CMH Candlesticks v1.5 (27-pattern handbook registry with data-seeded priors, context/zone/trend gates, 0-100 quality score with the v1.5 reweight Trend30/Prior15/Shape25/Vol15/Size15, proven losers default OFF) and T9 = CCC Hidden Patterns v4.0 (2-5-candle merge windows, hidden/liquidation/context handbook gates, same score family, v4.0 priors). Firing mode selectable per gate: `InpT8/T9_ConfirmBars` 0 = fire on pattern close (suite-provisional, −6 quality, the default — a 6-bar-late trigger is not a trigger) or N = fire after N bars confirm the swing extreme. Structural SL = pattern/merged extreme, TP=0 → RR-derived. Magics base+13/+14; NPSU DSL gains trig tokens T8/T9 (NPSU_TRIGS 6→8); dashboard gains two trigger rows (BD_GATES_H 340→380, panel base 694→734); dropped from the ports: suite dashboards, alerts, CSV export, cross-suite confluence GlobalVariable bus, box rendering (arrows only). NPT-2 trade-log schema UNCHANGED (T8/T9 attribution flows through the magic map; their Inp*_Enabled flags are deliberately NOT appended to the config snapshot to keep old/new CSVs concatenable).** -> **3.15.0 (this release): (1) T4 PRECISIONTRENDPRO v4.1 PARITY — the gate now runs the indicator's THREE parallel line groups (Large 21 / Mid 14 / Short 5, Short opt-in `InpT4_ShowShort=false` because len-5 pivots are noisy on M1) each with its own bull+bear line, breakout events, failure watches and consumed-event latches; pulse priority L→M→S mirrors the v4.1 buffer order; touch labels gain the v4.1 true visual slope angle ("N touches | X.X°", chart-pixel atan2). DELIBERATELY KEPT vs the indicator (recorded, T7-style port notes): best-pair pivot selection per group (v4.1 still connects only the 2 newest pivots — the v2.1.2 rewrite documented why that starves the chart), closed-bars-only breakout tests (v4.1 tests the forming bar intra-tick — repaint), no SendNotification. `InpT4_PivotLen` REPLACED by `InpT4_LengthMain/Mid/Short` (old single-group len-14 ≈ the Mid group). (2) ROSTER R4 — 13-strategy T8/T9 audition roster (`--roster R4` in np_strategy_generator.py; ready-made files shipped in `NPSU_Strategies_R4_T8T9/` — copy into Common\Files\NPSU_Strategies). Generator's stale 15-file cap raised to 59 (v3.13 capacity). (3) NP_AUTO_1_WINRATE / NP_AUTO_2_EQUITY / NP_AUTO_3_LASTTRADE presets — one per `InpADV_AutoAdopt` criterion, real-default base + NPSU + advisor + auto-adopt (warm-up 10, cooldown 60 min); BACKTEST ONLY until the matching meta-switcher wins in backtest + OOS (v3.12 rule; architect prefers EQUITY).** -> **3.15.1 (this release): np_trade_verifier FALSE-POSITIVE fix — pandas sort_values() default quicksort is unstable and reordered same-minute BE/TRAIL audit rows, producing false R2/R3/R5 violations (1297 on the first v3.15 run); kind="stable" preserves the engine's write order. Run 81906 (Jul 1-15 XAUUSD M1, auto-adopt LASTTRADE) then certifies 2199/2199 virtual trades clean.** -> **3.16.0 (this release): BIAS GATE B6 — RegChannel MTF trend quality, ported from the owner's RegressionChannelMTF_Pro (exact-OLS rebuild of the Pine 'Regression Channel Alternative MTF V2'). Up to three TF-perspective regression windows (auto length table W1/D1/H1/M15/M5/M1; Higher+Primary on, Lower opt-in) must AGREE on slope direction and EACH clear |Pearson R| >= InpB6_MinR (default 0.55), else the bias is NEUTRAL. Closed bars only (the indicator's forming-bar channels deliberately dropped); breakout buffers/alerts dropped (bias gate, not trigger). Bit 0x1000 (bias masks now 0x00F|0x1000), NPSU token B6, dashboard bias row 5 (BD_GATES_H 400, panel base 754), NP_Trades bias_state string gains '|B6=x' (same column count, CSVs stay concatenable — Python readers that split('|') into exactly 4 parts need a one-line update). RECORDED CAVEAT: regression slope correlates with B1; the R cut + MTF agreement are the marginal information. ROSTER R5 (8 strategies) tests B6 as B1-replacement, as addition, and inside the strict stack; ready-made files in NPSU_Strategies_R5_B6/. R4 audition verdict (runs 81906/92546): T1 dominant survival-first, T8 negative, T9 flat — T1 stays; T8/T9 parked pending ConfirmBars=6/MinQuality=65 re-test.** -> **3.16.1 (this release): analyzer QoL — every Python script runs with NO arguments (folder auto-detect: NEELPRAJNA_FILES env → cwd → %APPDATA%\MetaQuotes\Terminal\Common\Files); NEW analyzer/np_dashboard.py generates NP_HourlyDashboard_<runid>.html: strategy totals + hour×strategy heat-map + per-strategy hourly detail (trades/netR/win%/PF/avgR), REAL included. R5 run 68484 findings recorded: real B1|T1 +19.8R PF 1.51; B6-as-replacement worse than B1; B6-as-ADDITION promising but starved (T1_B1B6 +0.34R/trade DD 1.2R n=11; T1_B6B2B4 +0.97R/trade n=5) — needs the LONG run; M_WINRATE positive third run running.** -> **3.16.2 (this release): GOVERNANCE PACK — docs/ folder added: NP_Architecture_Roadmap_v1.0.md (existing layer map documented; DECISION: Python is a research/screening layer, MT5 stays the only ground truth — twin-engine rejected for drift risk; phased roadmap: R6 long run → hourly filter → NP Lab → incremental OS evolution), AI_ROLE_PROMPTS.md (common brief + Gate Developer / Python Analyst / Verifier / Doc Keeper role briefs + escalation table), FABLE_COMMS_STANDARD.md (owner-issued communication standard — all reports follow it). ROSTER R6 shipped (NPSU_Strategies_R6_LONGRUN/): 6 racers for the months-long confirmation run that decides the next real default. No EA code changes.** -> 3.16.3 CONTEXT PACK — docs/SESSION_BOOTSTRAP.md (paste-first brief for fresh Fable sessions), WORK_ORDERS_v3.17.md moved into docs/, research-state section rewritten as the single source of truth for resuming work. Docs only. -> **3.16.4 (this release): B6 DRAWING PARITY (owner screenshot request) — all THREE regression channels are now always drawn (compute-all-windows, VOTE only enabled windows: `_B6_WindowOn` moved after the draw call, so `InpB6_UseLower=false` still shows the yellow channel but keeps it out of the bias vote), identity colours match the indicator (HIGHER blue / PRIMARY purple / LOWER yellow, `InpB6_ColHigher/Primary/Lower`), line widths 1/2/3, dashed midline + solid bands, and a per-channel accuracy label "NAME [TF] UP/DOWN + R=x.xx" (`InpB6_ShowLabels`, green up / red down). The indicator's scenario table is deliberately NOT ported — owner request. Names follow the indicator's ResolvePresets table (on M1: PRIMARY/LOWER/LOWEST). Bias logic, thresholds and CSV schemas are bit-identical to 3.16.3 — drawing-only change.**

## Current research state & next steps (updated 2026-07-20, v3.16.4)

WORKING MODE (owner decision): Fable = Chief Architect only — designs,
work orders, reviews. Other AI models implement via docs/AI_ROLE_PROMPTS.md
+ docs/WORK_ORDERS_v3.17.md. All communication follows
docs/FABLE_COMMS_STANDARD.md. Roadmap: docs/NP_Architecture_Roadmap_v1.0.md.

SETTLED BY DATA (July 2026 runs 81906 / 92546 / 68484):
1. T1 stays — T8 (CMH) and T9 (CCC) auditioned and PARKED: T8 negative,
   T9 flat, both dilute T1; noBias variants catastrophic (B1 carries them).
   Optional one-shot retest someday: ConfirmBars=6 + MinQuality=65.
2. B6 RegChannel: as B1 REPLACEMENT worse; as ADDITION very promising but
   data-starved (T1_B1B6 +0.34R/trade DD 1.2R n=11; T1_B6B2B4 +0.97R/trade
   n=5). Verdict pending the long run.
3. Auto-adopt: LASTTRADE scored +29R then −25R (n=2 = variance) — real
   account stays manual B1|T1; M_WINRATE positive 3 runs running (watch).
4. Mirror parity EXACT on clean runs (AT-2 passing); verifier certifies
   after the v3.15.1 stable-sort fix (open-at-stop R1 flags are benign).
5. Real benchmark (Jul 1–15, B1|T1, risk 0.5%): +19.8R, PF 1.51, DD 7.6R.

IN FLIGHT:
A. R6 LONG RUN (highest value, owner action): 6-strategy roster in
   NPSU_Strategies_R6_LONGRUN/ — 3–6 months XAUUSD M1 real ticks,
   auto-adopt OFF, real=B1|T1 (NP_R5_REAL_default.set), keep last 4–6
   weeks UNSEEN for OOS. Decides the next real default among T1_base /
   T1_strictBias / T1_B1B6 / T1_B6B2B4 / T1_strict_B6.
B. v3.17.0 via work orders (other AIs): WO-1 FeatureLogger.mqh (NPF-1
   per-bar feature CSV), WO-2 analyzer/np_lab.py (offline rule evaluator
   with mandatory MIRROR calibration). Specs: docs/WORK_ORDERS_v3.17.md.
   Fable reviews before merge.

QUEUED (roadmap order): hourly/session filter gate (evidence from
np_dashboard.py); dashboard/OS evolution incremental; parked ideas
(T10 Quad Stochastic, T1 Pattern F/C, per-universe T1 modes).

FRESH-CHAT BOOTSTRAP: attach the latest release zip + paste
docs/SESSION_BOOTSTRAP.md. That file + this section = full context.

## DriftPro (side project)

`/driftpro` v1.2: owner's other EA whose multiuniverse idea inspired NPSU.
All found bugs fixed (stub trailing, triple spread, dead stats, logger never
instantiated, GetPipSize shadow, export desync). Its lessons are encoded as
design rules L1–L11 in the NPSU design doc §3.
