# NPSU Post-Validation Guide

## Validating Virtual Trades & Strategies After Every Run

| | |
|---|---|
| **Document** | Post-Validation Guide v1.0 |
| **Applies to** | NeelPrajna v3.10+ (audit trail required); pipeline script v3.12.2+ |
| **Companion tools** | `analyzer/np_post_validation.py` (one command), `np_trade_verifier.py`, `np_universe_analyzer.py` |
| **Principle** | No ranking is believed until the data producing it is certified. Verification gates analysis. |

---

## 1. Why post-validation exists

Real trades are validated by MT5 itself — broker fills, visible on the chart.
Virtual trades are computed by VirtualBook, so their correctness must be
*established*, not assumed. Post-validation is the standing procedure that
does this after every run, using four independent layers (design doc §15):

1. **Mirror parity** — U0 MIRROR runs the real config virtually; every real
   trade must have a virtual twin.
2. **Audit trail** — every OPEN / BE / TRAIL / CLOSE decision is logged with
   the bar and its justification (`NPSU_Audit_*.csv`, schema NPSU-D1), so any
   trade can be checked by hand against the chart.
3. **Independent replay** — `np_trade_verifier.py`, a second implementation
   of the rules, re-checks every decision (Level 1) and, given raw M1 bars
   exported by the user, replays every trade from scratch (Level 2).
4. **Runtime invariants** — the EA self-checks each close and writes loud
   VIOLATION rows if anything is off.

## 2. What a run produces (collect these)

| File | Content | Needed for |
|---|---|---|
| `NP_Trades_*.csv` | real closed trades (NPT-2) | parity (Step 4) |
| `NPSU_Trades_*.csv` | virtual closed trades (NPSU-T1) | everything — **required** |
| `NPSU_Audit_*.csv` | per-decision audit (NPSU-D1) | verification — **required** |
| `NPSU_Summary_*.csv` | per-universe snapshots (NPSU-S1) | cross-checks — optional |
| `NPSU_Advisor_*.csv` | advisor evaluations (NPSU-A1) | advisor review — optional |
| M1 bars export | chart → **Ctrl+S** in MT5 | Level-2 replay — recommended |

The EA prints the absolute path of every file at START and EXIT in the
Experts journal. **Copy files — never move them while the EA is attached**
(a moved file is silently recreated without its header).

## 3. The procedure — one command

```
python np_post_validation.py <folder-with-CSVs> --split <mid-date> --bars <M1-export.csv>
```

This runs, in order, and writes `post_validation/POST_VALIDATION_REPORT.md`:

| Step | What happens | Pass looks like |
|---|---|---|
| 1 Inventory | checks required/optional files | both required files present |
| 2 Verification | rules R1–R9 over every decision | **ALL CHECKS PASSED** (or explained items only) |
| 3 Analysis | survival-first ranking, walk-forward split, exit/session tables, meta-switchers vs holding, equity PNG | `report.md` + `equity_curves.png` |
| 4 Mirror parity | real↔U0 trade matching | ≥90% matched, mean gap ≤0.15R |

The three scripts can also be run individually; the pipeline simply chains
them and adds the parity reconciliation.

## 4. The verification rules (what "certified" means)

| # | Rule |
|---|---|
| R1 | one OPEN + one CLOSE per trade; matches its trades-row; profit_R recomputed from prices (risk-proportional rounding tolerance) |
| R2 | SL only ever moves in the trade's favour |
| R3 | BE only after a bar reached 1R excursion; at most once; "armed (SL already better)" rows allowed; TRAIL only after BE |
| R4 | every TRAIL lands on the recorded candle level or the close−floor fallback |
| R5 | SL fills at worse-of(SL, bar open); TP at worse-of(TP, bar open); same-bar SL+TP ⇒ SL with ambiguous_bar=1 |
| R6 | every fill inside the closing bar's true range |
| R7 | *(--bars)* recorded bar OHLC matches the exported bars |
| R8 | *(--bars)* replaying ALL bars, the first SL/TP hit is exactly the logged close |
| R9 | *(--bars)* BE was not late |

ADOPT rows (meta-switcher adoptions) are events, not trades — validated for
timing, excluded from R1 structure checks.

## 5. Reading the analysis (after — and only after — Step 2 passes)

**Ranking is survival-first**: max drawdown → worst losing streak → worst
rolling-20-trade net → profit factor. Never raw ROI. Rows flagged `n<20`
are anecdotes, not evidence. With `--split`, trust universes that rank well
in BOTH halves; a winner selected in-sample is provisional until it repeats
out-of-sample. The **meta-switchers section** scores switching against the
best held-forever base universe — the standing experiment of §13.8. The
**counterfactual bias table** generates hypotheses for the next roster; it
is never a validated result by itself.

## 6. Worked example — run XAUUSD 22078 (9 days, 2026-07-02→10)

- Inventory: complete (all five files). Bars export not provided → Level 1.
- Verification: **1,273 trades certified** — 1,523 SL moves all favourable,
  640 BE events, all fills inside their bars, 0 runtime violations. Flags:
  492 same-bar BE+TRAIL rows conflated by the v3.12.1 audit (fixed in
  v3.12.2 — trading math was correct), 96 ADOPT rows (verifier updated),
  3 rounding nits on sub-1.0 risk distances.
- Analysis: regime shift mid-run. In-sample leader T1_noTrail (+23.4R)
  collapsed out-of-sample (−15R, 13-loss streak) — the trail's defensive
  value demonstrated; walk-forward winner T1_strictBias held rank 2 OOS.
  Advisor switched its recommendation to T1_SMCbias after 3 confirmed
  evaluations — hysteresis worked as designed.
- Meta-switchers: best hold +14.8R; M_LASTTRADE +12.9R (104 switches),
  M_WINRATE +10.2R, M_EQUITY −9.9R. Pre-registered predictions scored:
  switching did not beat holding (Fable's core claim held), but LAST_TRADE
  was by far the best criterion (Girish's instinct beat Fable's EQUITY
  preference).
- Parity: 69/72 real trades matched (96%), mean gap 0.187R (above the
  0.15R target — under observation; Level-2 replay with bars will localize
  the drift), exits identical 88%.

## 7. Troubleshooting — flags you may see and what they mean

| Symptom | Meaning | Action |
|---|---|---|
| R3 "BE landed at X, entry Y" on pre-3.12.2 logs | audit merged same-bar BE+trail into one row | upgrade EA to v3.12.2; old logs stay flagged (math was correct) |
| R1 structure fails on M_ universes with old verifier | ADOPT events unknown before v3.12.2 | use the v3.12.2 verifier |
| profit mismatch ~0.02R on tiny-risk trades | 2-digit CSV rounding | v3.12.2 tolerance handles it |
| header missing from a CSV | file was MOVED while EA attached; EA recreated it | copy, don't move; headers only write at init |
| summary header-only | run shorter than snapshot interval on pre-3.6.2 builds | v3.6.2+ writes every `InpNPSU_SummaryMins` |
| parity match < 90% | real path skipped/added entries (margin, retry throttle, spread timing, GroupSL) | inspect unmatched trades in NP_Trades vs audit OPEN rows |
| VIOLATION rows in audit | runtime invariant broke | report the trade immediately — this must never be ignored |

## 8. The record rule

The post-validation report is part of the run's record. Keep
`POST_VALIDATION_REPORT.md`, `report.md` and `equity_curves.png` next to the
CSVs that produced them. A run without its validation report is an anecdote;
a run with one is evidence.
