# NeelPrajna — Architecture & Roadmap v1.0 (2026-07-20)

Written by Fable (Chief Architect role) per the Fable Communication Standard
(`docs/FABLE_COMMS_STANDARD.md`). Owner: Girish. Companion documents:
`HANDOVER.md` (project state), `NPSU_Design_Doc_v1.6.md` (shadow universes),
`docs/AI_ROLE_PROMPTS.md` (role briefs for other AI models).

---

## 1. Executive Summary

NeelPrajna is a working, verified research machine. The owner's two notes
(26 June, 20 July) ask for: (a) an offline Python model to backtest ideas,
and (b) evolution of NeelPrajna toward an "OS" with clean layers, a new
dashboard, and an hourly filter. This document records the agreed direction:
**keep MT5 as ground truth, add Python as a research/screening layer, evolve
the EA incrementally (never big-bang), and let data-months — not new
features — decide promotions.** The next concrete action is the R6 long run.

## 2. Problem Statement

Three problems, in priority order:

| # | Problem | Why it exists | Why it matters |
|---|---------|---------------|----------------|
| 1 | Candidate strategies are data-starved (T1_strictBias n=23, T1_B1B6 n=11, T1_B6B2B4 n=5) | Quality-stacked bias filters trade rarely; runs so far are 2 weeks long | Nothing can be promoted survival-first at n<100; conclusions at n=5 are noise |
| 2 | Idea testing requires the MT5 terminal | The EA is the only simulator | The owner wants to create/test ideas offline, continuously |
| 3 | Growing feature surface strains one-file-per-gate structure | 15 gates + NPSU + advisor accreted over 16 minor versions | Future work (new dashboard, hourly filter, more analysis) needs clear layer boundaries |

## 3. Background

Everything below already exists and is verified:

```
┌─ APPLICATION LAYER ──────────────────────────────────────────┐
│ NPSU shadow universes · Live Advisor · meta-switchers        │
│ CSV logs (NPT-2 / NPSU-T1/S1/D1/A1) · Python analyzers       │
│ np_dashboard.py (hourly) · verifier (independent replay)     │
├─ LOGICAL LAYER 1 — SIGNALS ──────────────────────────────────┤
│ Bias gates:    B1 Nexis · B2 MTF · B3 KeyLvl · B4 SMC · B6   │
│ Trigger gates: T1 Pattern · T2 Fibo · T3 Sweep · T4 TL ·     │
│                T5 Topo · T7 SMM · T8 CMH · T9 CCC            │
│ Contract: EG_Xx_Buy/Sell (+ SL/TP for triggers), closed bars │
├─ LOGICAL LAYER 2 — EXECUTION ────────────────────────────────┤
│ EntryGates (BIAS×TRIGGER walk) · TradeManager (SL/TP/BE/     │
│ trail) · MoneyManager (lots, spread) · magic attribution     │
├─ SKELETON ───────────────────────────────────────────────────┤
│ NeelPrajna.mq5 events · Config.mqh · Dashboard containers ·  │
│ loggers · verification invariants                            │
└──────────────────────────────────────────────────────────────┘
```

The owner's sketched layers map 1:1 onto this. Conclusion: the "OS" already
has its kernel; it needs *documentation and discipline*, not a rewrite.

## 4. Simple Intuition

Think of the project as a laboratory. MT5 is the physical experiment — slow
but real. Python is the whiteboard — fast but approximate. You sketch on the
whiteboard, and only promising sketches earn an expensive real experiment.
The mistake to avoid is building a *second laboratory* and then arguing
about which laboratory is right.

## 5. Key Decision: Python layer = research, NOT a second engine

| Option | Benefits | Costs / Risks | Verdict |
|--------|----------|---------------|---------|
| A. Re-implement gates in Python (twin engine) | Full offline backtests | Dual-engine drift: two versions of every rule, endless parity debugging (we needed mirror+verifier just to trust ONE simulator) | **Rejected** |
| B. Python = screener + counterfactual miner over logged data & exported bars | Fast offline idea loop; reuses existing CSVs; verifier `--bars` replay is half-built already | Coarse fills; cannot fully replace tester | **Chosen** |
| C. Buy/adopt external backtest framework | Mature tooling | Different fill model again + learning curve + no NPSU concepts | Rejected |

Promotion pipeline under option B:

```
idea → Python screener (bars, coarse fills, survival-first report)
     → if promising: implement as gate/universe in MT5
     → NPSU shadow run (real ticks)  → long run → OOS → promotion
```

## 6. Roadmap

| Phase | Deliverable | Depends on | Effort | Status |
|-------|------------|-----------|--------|--------|
| 0 | **R6 long run**: 6-strategy roster (`--roster R6`), 3–6 months XAUUSD M1 real ticks + unseen OOS window | nothing | 1 tester run + analyzer | **READY — files shipped** |
| 1 | **Hourly/session filter**: global hours mask input + per-universe `hours=` DSL key; evidence from np_dashboard | Phase 0 data | small EA change | planned |
| 2 | **Python research layer** ("NP Lab"): bar loader (MT5 Ctrl+S export) · counterfactual engine over logged trades (hour/bias/quality/RR what-ifs) · coarse vectorized screener with survival-first output | none (parallel) | medium, pure Python | planned |
| 3 | **Docs & multi-model workflow**: this document + `AI_ROLE_PROMPTS.md`; other models take bounded tasks | none | done in v3.16.2 | **DONE** |
| 4 | **Dashboard/OS evolution**: HTML report v2, EA dashboard refresh — incremental, layer by layer | 0–2 | ongoing | later |

## 7. Validation Plan

Unchanged constitution, applied to every phase: survival-first ranking
(max DD → worst streak → ranging weeks → PF, never raw ROI); mirror parity
(AT-2) on every run; independent verifier certification; winners must
confirm on unseen data; pre-registered predictions before looking at
results where a hypothesis race is involved.

## 8. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Big-bang rewrite breaks the verified machine | high if attempted | severe | Incremental evolution only; layers change when a feature demands it |
| Dual-engine drift (if option A creeps back in) | medium | high | Python screener never claims truth; MT5 validates everything |
| Multiple-comparisons bias (many racers, short windows) | already observed | high | Focused rosters (R6=6), OOS confirmation, roster version labels |
| Switching criteria promoted on n=2 evidence | observed (LASTTRADE +29R then −25R) | high | v3.12 rule: meta must win backtest + OOS first |
| Feature work displacing data collection | medium | medium | Phase 0 gates all promotions; long runs run while features are built |

## 9. Key Takeaways

1. The architecture the owner sketched already exists — document it, do not rebuild it.
2. Python becomes the fast offline whiteboard; MT5 stays the only source of truth.
3. The single most valuable next action is the R6 long run — everything else can proceed in parallel.
4. The hourly filter is the next EA feature, and it will be justified by data the new dashboard already produces.
5. Other AI models plug in through the role briefs; the no-dependency rule is what makes that safe.

## 10. Next Steps

1. Owner: copy `NPSU_Strategies_R6_LONGRUN/` files into `Common\Files\NPSU_Strategies\`, load `NP_R5_REAL_default`-style settings (or `NP_NPSU_longrun.set`), run 3–6 months + keep a later unseen window for OOS.
2. Fable: on results, produce the survival-first verdict and (if a winner validates) the promotion recommendation.
3. Parallel: Phase 2 NP Lab skeleton; Phase 1 hourly-filter design note.
