# NeelPrajna Shadow Universe (NPSU)
## Multi-Universe & Virtual Trades — Design Document

| | |
|---|---|
| **Document version** | 1.6 |
| **Target EA version** | NeelPrajna v3.6.0 |
| **Author** | Claude (Fable) with Girish |
| **Date** | 2026-07-12 |
| **Status** | **APPROVED & IMPLEMENTED (v3.6.1).** v1.1 added §8.4 self-describing data, Appendix A, Phase 3. v1.2 adds §5.4 strategy files. v1.3: external strategy generator. v1.4: §13 Live Advisor. v1.5: §14 dashboard integration + one-click apply (v3.8–3.9), §15 verification (v3.10). v1.6: §13.8 runtime auto-adopt (v3.11), §13.9 meta-switchers with pre-registered predictions (v3.12) |

---

## 1. Purpose

One backtest run currently answers one question ("how does THIS config perform?").
NPSU makes one run answer **many questions at once**: while the real EA trades
normally, N *virtual universes* run in parallel inside the same EA. Each universe
is an independent strategy — its own combination of bias gates, trigger gates and
config (trail on/off, RR, T1 entry mode, Pattern A vs A+S…). Each universe opens
and manages **virtual trades** (never real orders), keeps its own virtual account,
and streams every closed virtual trade to CSV. A Python analyzer then reads the
CSVs and ranks the universes by our official survival-first criterion.

**The question NPSU answers:** *"Which gate combination + config survives best —
measured on identical market data, identical signals, identical timing?"*
Today, comparing 12 configs needs 12 backtest runs and the conditions are never
perfectly identical. With NPSU it is **one run, one dataset, 12 verdicts.**

### 1.1 Goals

1. Run up to 16 strategy universes in parallel with **zero influence** on real trading.
2. Universe = (bias-gate subset) × (trigger-gate subset) × (config overrides).
3. Stream one CSV row per closed virtual trade (no buffering — see §3, lesson L7).
4. Periodic + final summary CSV with survival-first metrics per universe.
5. `np_universe_analyzer.py` — offline Python report: ranking, equity curves,
   exit-reason breakdown, session heatmap, statistical-caution section.
6. A **mirror universe (U0)** that copies the real EA's exact config, used to
   validate that the virtual simulator matches reality (§10).

### 1.2 Non-goals (explicitly out of scope for v3.6.0)

- No automatic switching of the real strategy to the "best" universe. Research only.
  (Auto-switching on in-sample winners is exactly the selection-bias trap.)
- No per-universe money management differences — all universes use identical
  risk sizing so equity curves are directly comparable (§7.4).
- No tick-by-tick virtual management. Virtual books manage on closed M1 bars (§7.3).
- No ensemble voting (the DriftPro feature). Can be revisited after NPSU data exists.

---

## 2. Concept Overview

```
 every new bar
 ──────────────►  EG_EvaluateAllGates()
                  B1..B4 → EG_Bx_Buy/Sell (bias)
                  T1..T5,T7,T8,T9 → EG_Tx_Buy/Sell pulses
                              + EG_Tx_SL/TP/HasLevels
                  (evaluated ONCE, consumed by many)
                     │                    │
          ┌──────────┘                    └──────────┐
          ▼                                          ▼
 ┌─────────────────────┐             ┌─────────────────────────────┐
 │      REAL PATH      │             │    NPSU UniverseEngine      │
 │  (unchanged v3.5)   │             │  U0 mirror (validation)     │
 │  _EG_BiasAgree      │             │  U1 B1|T1 trail ON          │
 │  trigger walk       │             │  U2 B1|T1 trail OFF         │
 │  Tx_MarkConsumed()  │             │  U3 B1|T1(A+S) ...          │
 │  real orders        │             │  each: own bias-agree, own  │
 └─────────────────────┘             │  trigger walk + consumption │
                                     │  memory, own VirtualBook,   │
                                     │  own CSV rows               │
                                     └─────────────────────────────┘
```

The single most important architectural idea: **gates are evaluated once; the
signal layer is read-only and shared.** Universes differ only in *which* gate
outputs they combine and *how* they manage the resulting virtual position.

This directly fixes the biggest DriftPro design flaw: there, universes only saw
a signal when the *main* EA generated one, so "entry-type" universes produced
identical results (we saw this in your MultiUniverse_Summary CSV — universes
1/2/4 identical, 5/6 identical). In NeelPrajna the gate layer already publishes
state every bar regardless of trade state, so every universe genuinely sees the
full signal stream.

---

## 3. Lessons from DriftPro — applied as design rules

Every bug we found in DriftPro becomes a hard rule here:

| # | DriftPro bug we found | NPSU design rule |
|---|---|---|
| L1 | Logger "looked wired" but was never instantiated (dead feature) | §10 acceptance test AT-1: a fresh tester run MUST produce a trades CSV with >0 rows before v3.6.0 ships |
| L2 | Trailing/partial primitives were stubs — configured but never executed | Virtual management functions covered by mirror-universe parity test AT-2 |
| L3 | Spread deducted 2–3 times (balance 9999.87 rows) | Spread applied exactly once: entry fills at real Ask/Bid of the fire tick (§7.2), never adjusted again |
| L4 | Stats accumulators never updated (ProfitPips/MFE/MAE/Sharpe all 0.00) | No stat is computed at export time from stored trades; every stat is an accumulator updated **in the same function that closes the virtual trade** — one code path, impossible to skip |
| L5 | `GetPipSize` shadowed with wrong math (BTC 10× off) | All price→R conversion in ONE helper; unit test values in AT-3; everything expressed in **R-multiples** so symbol point-value bugs cannot distort rankings |
| L6 | Gap-blind SL fills (filled at SL price even when bar gapped past it) | Gap-aware fills: fill price = worse of (level, bar open) (§7.3) |
| L7 | Trades buffered in RAM, exported only at OnDeinit (export desync, data lost on crash) | Trades **stream** to CSV at close with `FileFlush` — same pattern as the proven v3.5 TradeLogger. Summary file is small and rewritten periodically + at deinit |
| L8 | ProfitFactor printed 0.00 when a universe had zero losses (best looked worst) | Summary prints `INF` for PF with no losses; analyzer handles it explicitly |
| L9 | Chart object name collisions between universe instances | Single `NPSU_` prefix, all names carry universe id: `NPSU_U3_...` |
| L10 | Export sorted the LIVE array → later exports desynced from indices | Engine never reorders universes; display sorting happens on a copy in the dashboard/analyzer only |
| L11 | 40 universes → multiple-comparisons trap | Analyzer prints a mandatory statistical-caution block and supports out-of-sample validation split (§9.4) |

---

## 4. Architecture

### 4.1 New files (all UTF-8, all following existing header conventions)

| File | Responsibility |
|---|---|
| `UniverseRoster.mqh` | Universe definition struct, DSL parser for input strings, built-in default roster, strict validation (invalid definition → journal error + universe disabled, **never** silently altered) |
| `VirtualBook.mqh` | One virtual account: open/manage/close virtual positions, gap-aware fills, BE/trail simulation, all survival-first accumulators |
| `UniverseEngine.mqh` | Owns N (roster, book) pairs; per-universe bias-agree + trigger walk + consumption memory; drives books on each closed bar; dashboard scoreboard |
| `UniverseLogger.mqh` | `NPSU_Trades_*.csv` (streamed) + `NPSU_Summary_*.csv` (rewritten); shares `run_id` stamp with TradeLogger so real and virtual rows join in Python |
| `analyzer/np_universe_analyzer.py` | Offline analysis + report (§9) |

### 4.2 The ONE structural change to existing code: the compute mask

Verified in v3.5.0 source: a disabled gate early-returns from its `Evaluate()`
and publishes nothing (`EG_B1_Buy/Sell` stay false). So today, a universe could
never use a gate the real EA has switched off.

Fix: split "enabled" into two flags per gate —

- `EG_Xn_Live`    — gate participates in the REAL entry decision (today's meaning;
  set from `InpXn_Enabled` exactly as now).
- `EG_Xn_Compute` — gate must evaluate and publish state each bar.
  Set at init to: `Live OR (referenced by any active universe)`.

`Evaluate()` early-returns only when `!Compute`. `_EG_BiasAgree()` and the real
trigger walk check `Live`. Gates that are compute-only (needed only by universes)
run with **drawings suppressed** — no chart noise, less CPU. This is a small,
mechanical change in each gate file plus `EntryGates.mqh`, and it is the only
change the real trading path will ever notice (it notices nothing: `Live`
semantics are byte-identical to today's `Enabled`).

### 4.3 What is guaranteed NOT to change

- Magic offsets, magic filtering, `CFG_MagicFor` — untouched. Virtual trades have
  **no magic and no tickets**; they exist only inside `VirtualBook`.
- `Tx_MarkConsumed()` is called by the REAL path only. Universes never consume
  a pulse globally (§6).
- TradeManager, MoneyManager, GroupSL, session logic — untouched.
- TradeLogger (real trades CSV) — untouched; NPSU logs to its own files.
- Closed-bar anti-repaint discipline — universes see exactly the same closed-bar
  gate outputs as the real path, at the same moment.

---

## 5. Universe Definition & Roster

### 5.1 Definition (what a universe IS)

```
Universe = {
  id            0..15
  name          short label, e.g. "T1_trailOFF"
  bias_mask     subset of {B1,B2,B3,B4,B6}     (empty = bias layer passes trivially,
                                             same rule as the real _EG_BiasAgree)
  trig_mask     subset of {T1,T2,T3,T4,T5,T7,T8,T9}  (must be non-empty; T8/T9 v3.14)
  overrides {
    trail       0/1        (default: real InpEnableTrail)
    be          0/1        (default: real InpEnableBE)
    rr          double     (default: real InpRRRatio; used when trigger TP=0)
    t1mode      IMM|RETEST (default: real InpT1_EntryMode)   [affects T1 only]*
    t1s         0/1        (default: real InpT1s_Enabled)    [affects T1 only]*
  }
}
```

\* **v3.6.0 limitation, stated honestly:** `t1mode` and `t1s` change what the T1
gate *detects*, and the gate is evaluated once for everyone. In v3.6.0 these two
overrides are therefore accepted by the parser but must match the real EA's
setting, otherwise the universe is disabled with a journal error. Making T1
publish A-only and A+S pulse streams side-by-side (so universes can choose) is
listed in §11 as the first v3.7 candidate — the `variant` column already tells
us per-trade which pattern fired, so A-vs-S analysis works from day one anyway.

### 5.2 Input format (the roster DSL)

16 plain string inputs — easy to store in .set presets, easy to read in the
config snapshot:

```
input bool   InpNPSU_Enabled = false;                    // master switch (OFF by default)
input bool   InpNPSU_DefaultRoster = true;               // true = ignore U1..U15, use built-in roster
input string InpNPSU_U1 = "name=T1_base;bias=B1;trig=T1";
input string InpNPSU_U2 = "name=T1_noTrail;bias=B1;trig=T1;trail=0";
...
input string InpNPSU_U15 = "";
```

Grammar: `key=value` pairs separated by `;`. `bias`/`trig` values separated by
`+` (e.g. `bias=B1+B4;trig=T1+T7`). Unknown key, unknown gate, empty `trig`,
duplicate name → **journal error naming the exact input and token, universe
disabled, dashboard shows "Un CONFIG ERR"**. No silent repair, ever.

U0 (mirror) is never user-defined — the engine builds it from the real EA's
live config automatically whenever NPSU is enabled.

### 5.3 Built-in default roster (used when `InpNPSU_DefaultRoster=true`)

Chosen around your research questions: T1 as the trusted anchor, T7's
add-on value, trail's contribution, and bias-layer strictness.

| Id | Name | Bias | Triggers | Overrides | Question it answers |
|---|---|---|---|---|---|
| U0 | MIRROR | (real) | (real) | (real) | Does the simulator match reality? |
| U1 | T1_base | B1 | T1 | — | Baseline: your trusted setup |
| U2 | T1_noTrail | B1 | T1 | trail=0 | Does the trail earn its keep? |
| U3 | T1_noBias | — | T1 | — | Is T1 self-sufficient? |
| U4 | T7_solo | B1 | T7 | — | T7 alone (your last run: PF 0.95) |
| U5 | T1_T7 | B1 | T1+T7 | — | Does T7 ADD to T1? (RES_4 question) |
| U6 | T1_strictBias | B1+B2+B4 | T1 | — | Do more bias filters help T1? |
| U7 | T1_SMCbias | B4 | T1 | — | Structure bias instead of MA bias |
| U8 | T3_sweep | B1 | T3 | — | Sweep+FVG under same conditions |
| U9 | T5_topo | B1 | T5 | — | Topography under same conditions |
| U10 | T1_rr3 | B1 | T1 | rr=3.0 | Higher RR target on T1 |
| U11 | ALLTRIG | B1 | T1+T2+T3+T5+T7 | — | Kitchen sink — usually a lesson in humility |

11 defined + U0 = 12 active by default.

### 5.4 Strategy FILES — one file = one universe (added v1.2, Girish's requirement)

Strategies must not be tightly coupled to the EA build or its inputs — they are
DATA, addable/editable/deletable without recompiling. With
`InpNPSU_UseFiles=true` (default) the roster is loaded from plain-text files:

```
<MetaQuotes>\Common\Files\NPSU_Strategies\
    T1_base.txt          bias=B1
                         trig=T1
    T1_noTrail.txt       bias=B1
                         trig=T1
                         trail=0
    README.txt           (auto-written usage guide)
```

Rules: one file = one universe (max 15 + automatic U0); the file NAME is the
strategy name unless a `name=` line overrides it; same keys and the same strict
validation as the DSL — a bad file disables only that universe and the journal
names the file and the exact bad token; files sort alphabetically into U1..U15;
changes load at EA init (reattach / next tester run).

**Loose coupling (v3.6.3, Girish's requirement):** the EA NEVER creates or
writes this folder — strategies are strictly EXTERNAL input. The folder is
generated by a separate tool, `analyzer/np_strategy_generator.py` (default
roster, `--grid` cartesian combinations, `--clear`, `--list`), or written by
hand in any text editor. EA responsibilities and strategy authoring are fully
separated: change strategies without touching the EA; change the EA without
touching strategies. No folder / empty folder → journal note + built-in
roster fallback, so the EA never silently idles. The folder sits in
Common\Files, so the strategy tester reads the same files. The real account
still loads exactly one normal .set file, unchanged.

---

## 6. Per-Universe Trigger Consumption

The real trigger contract is *consume-on-success*: a pulse stays valid until the
real path trades it (`Tx_MarkConsumed()`) or validity expires. Universes must
respect the same "one entry per pulse" idea **without** touching the global
pulse — otherwise universe A would eat universe B's signal, or worse, a virtual
trade would eat the REAL EA's signal.

Solution: pulses get an identity, consumption becomes local.

- Each trigger already implies a pulse identity: `(gate, direction, pulse birth
  time)`. **As built:** the engine derives it itself by rising-edge detection —
  it samples every `EG_Tx_Buy/Sell` each tick (AFTER `EG_EvaluateAllGates()`,
  BEFORE the real trigger walk, so a pulse the real path consumes this tick is
  still seen) and stamps the moment a flag flips false→true. No gate file
  needed any change for this.
- Each universe keeps `last_consumed[gate][dir]` (a datetime). It acts on a pulse
  only if `EG_Tx_PulseTime > last_consumed`, and updates its own memory when its
  virtual entry opens.
- The global `Tx_MarkConsumed()` remains exclusively for the real path.

Result: every universe sees every pulse exactly once, independently, and the
real EA's behaviour is bit-for-bit unchanged.

---

## 7. Virtual Execution Model

### 7.1 Position policy: ONE open virtual trade per universe

A universe with an open virtual position ignores new entry signals until it
closes, and increments a `skipped_signals` counter (reported in the summary —
so we can see how much opportunity the one-position rule costs). Rationale:
one clean equity curve per strategy, directly comparable across universes, and
matching your real `InpMaxPositions=1` research setup.

### 7.2 Entry

- Universes are driven at the same moment the real trigger walk runs (after
  `EG_EvaluateAllGates()` on the live tick following bar close) — same signals,
  same timing, no look-ahead.
- Fill price = current **Ask** (buy) / **Bid** (sell) of that tick. Spread is
  therefore paid exactly once, implicitly, at entry (rule L3).
- The real path's spread cap applies to universes too (a spread too wide for a
  real trade is too wide for an honest virtual one). Skips increment
  `skipped_spread`.
- SL/TP: from the firing trigger's `EG_Tx_SL/TP` when `HasLevels`, else the
  universe's `rr` override — identical logic to the real `_EG_TryTrigger` path.
- Multi-trigger universes walk their triggers in the **same priority order as
  the real path** (T3 → T5 → T4 → T1 → T2 → T7, first fire wins the tick), so a
  universe result is never an artifact of a different tie-break order.
- Entry snapshot recorded for the CSV: ATR(14), spread points, hour, day-of-week,
  bias states of ALL four B-gates (not just the universe's own — lets Python test
  "would adding B2 have filtered this loser?" **without** running a new universe).

### 7.3 Bar-close management (deterministic and cheap)

On each **closed M1 bar**, every open virtual position is updated in this order:

1. **Gap-aware SL check**: bull position, `low ≤ SL` → filled at `min(SL, open)`
   (worse of the two — if the bar opened below the SL, we take the gapped price).
   Mirrored for sells. (Rule L6.)
2. **Gap-aware TP check**: symmetric, filled at the *worse* price for us
   (`max(TP, open)` cannot happen in our favour — if the bar opened beyond TP we
   take `open`, which is *better*; honesty cuts both ways, we take open).
3. **Same-bar ambiguity** (bar range covers both SL and TP): counted as **SL**.
   Pessimistic by policy — survival-first means we would rather under-report a
   strategy than flatter it. The trade row carries `ambiguous_bar=1` so Python
   can report how often this happened (if it is frequent, SL/TP are too tight
   for M1 resolution and the number is flagged as unreliable).
4. **Break-even** (if `be=1`): when bar high/low proves ≥1:1 R reached, SL moves
   to entry. Same rule as real `InpEnableBE`.
5. **Trail** (if `trail=1`): the candle-structure trail computation is extracted
   from TradeManager into a **pure shared helper** (price-in → new-SL-out, no
   position side effects). Real path and virtual books call the same function —
   one implementation, no drift between them (rule L2). This extraction is
   refactor-only and is protected by acceptance test AT-2.
6. **MFE/MAE accumulators** updated from bar high/low (in R).

Known, accepted difference from reality: real trades manage on every tick;
virtual books on closed M1 bars. Effect is small at M1 and it is *systematic*
(same for all universes), so rankings are unaffected. U0's parity report (§10)
measures the actual gap so we are never guessing.

### 7.4 Sizing and accounting: everything in R

Every virtual trade risks exactly **1R** (distance entry→SL). Results are
recorded in R-multiples: `profit_R`, `mfe_R`, `mae_R`; the virtual account is an
R-denominated equity curve starting at 0. A USD column at a fixed reference lot
(0.01) is logged too, but **rankings use R**. Why: R-accounting is immune to the
whole class of point-value/pip-size bugs that poisoned DriftPro's numbers
(rule L5), and it makes XAUUSD and BTC universes comparable in one table.

### 7.5 End of run

Open virtual positions at deinit are closed at the last known Bid/Ask with
`exit_reason=END_OF_RUN` (excluded from PF by the analyzer, reported separately).

---

## 8. Logging

### 8.1 `NPSU_Trades_<SYM>_<TF>_<start>_<id>.csv` — streamed, one row per closed virtual trade

Same location rules as the v3.5 TradeLogger (FILE_COMMON by default, works in
tester), same `run_id` stamp so real NP_Trades rows and NPSU rows join.

| Group | Columns |
|---|---|
| Identity | `run_id, ea_version, symbol, chart_tf, universe_id, universe_name, trade_seq` |
| Signal | `gate` (firing trigger), `variant` (e.g. Pattern A/S), `direction` |
| Execution | `open_time, close_time, duration_s, open_price, close_price, sl_initial, tp_initial, sl_final, exit_reason` (TP / SL_LOSS / SL_TRAIL_BE / END_OF_RUN), `ambiguous_bar` |
| Results | `profit_R, mfe_R, mae_R, profit_usd_ref` |
| Context | `open_hour, open_dow, atr14_open, spread_pts_open, b1_state, b2_state, b3_state, b4_state` (each BUY/SELL/FLAT) |
| Config echo | `cfg` (the universe's normalized DSL string — every row self-describing) |

### 8.2 `NPSU_Summary_<...>.csv` — rewritten every tester-day and at deinit

One row per universe per export (append with `export_time` column — rule L10's
cousin: history of snapshots, never mutated):

`export_time, run_id, universe_id, name, cfg, trades, wins, losses, win_pct,
net_R, gross_win_R, gross_loss_R, pf` (`INF` when no losses — rule L8)`,
max_dd_R, worst_streak, current_streak, avg_win_R, avg_loss_R,
sharpe_per_trade, exits_tp, exits_sl, exits_betrail, exits_eor,
skipped_signals, skipped_spread, ambiguous_bars, avg_duration_min`

All values come from accumulators updated inside `VirtualBook::CloseTrade()` —
the only function that closes a trade (rule L4).

### 8.3 Dashboard

Compact text-only scoreboard (your light-theme rules: no background rectangles,
dark slate text), prefix `NPSU_`, toggle `InpNPSU_ShowBoard`:

```
NPSU 12 universes | bar 8412
U1  T1_base       17t  +9.4R  dd 3.1R  pf 1.6
U5  T1_T7         31t  +7.2R  dd 5.0R  pf 1.3
U0  MIRROR        16t  +8.9R  dd 3.2R  pf 1.5
...top 8 by net_R, U0 always shown...
```

Sorting happens on a display copy only (rule L10).

### 8.4 Self-describing data — the "no-dependency" rule (added v1.1, Girish's requirement)

**Goal:** any AI (or any person) must be able to open the output folder cold —
no chat history, no memory of this project — and resume the research. The data
must explain itself. Three mechanisms:

1. **`schema_version` column** — first data column in every CSV.
   `NPSU_Trades` rows carry `NPSU-T1`, `NPSU_Summary` rows carry `NPSU-S1`,
   and the real-trade log gains it too in v3.6.0 (`NPT-2`; the analyzer also
   accepts v3.5.0 files without the column as implicit `NPT-1`). Any tool
   reading a schema it does not know must **fail loudly**, never guess.

2. **Auto-written sidecar data dictionary** — at run start each logger checks
   the output folder for `NP_DataDictionary_<schema>.md` and writes it if
   missing. The sidecar contains: every column's name, type, unit, and meaning
   (the same text as Appendix A); the enum values (`exit_reason`, `bias_state`,
   gate names); the survival-first ranking rule; the file-naming and `run_id`
   join convention; and a short "how to resume this research" note pointing at
   the analyzer. The CSVs themselves keep a single clean header row (pandas-
   friendly, no comment lines).

3. **The continuity pack** — every release zip ships: this design document,
   `HANDOVER.md` (project state, gate map, magic offsets, non-negotiables,
   version history), the data dictionary, and the analyzer with its `--help`
   text. The rule going forward: **a release an AI cannot resume from is an
   incomplete release** — it becomes acceptance test AT-9.

| # | Test | Pass condition |
|---|---|---|
| AT-9 | Cold-start resume | A fresh AI session given ONLY the release zip + one output folder can correctly state: what the EA does, what each CSV column means, which universe won by the survival-first rule, and what to run next. (We will literally test this with a fresh session.) |

---

## 9. Python Analyzer — `np_universe_analyzer.py`

Plain Python 3 + pandas + matplotlib, run from anywhere:

```
python np_universe_analyzer.py "C:\...\Common\Files" [--run RUN_ID] [--split 2026-05-01] [--out report_dir]
```

### 9.1 Inputs

Globs `NPSU_Trades_*.csv` + `NPSU_Summary_*.csv` (and optionally `NP_Trades_*.csv`
for real-trade comparison). Multiple runs concatenate cleanly via `run_id`.

### 9.2 Report contents (markdown + PNGs)

1. **Survival-first ranking table** — sorted by the official criterion, in order:
   `max_dd_R` (lower better) → `worst_streak` → ranging-period net_R (worst
   rolling-20-trade window) → `pf`. Never raw ROI.
2. **Equity curves** — all universes on one R-denominated chart + small multiples.
3. **Exit-reason breakdown** per universe (your last run's T7 diagnosis —
   "42 of 86 died by SL_LOSS" — automated).
4. **Session heatmap** — net_R by hour × universe; day-of-week table.
5. **Pattern A vs S** — from `variant`, wherever T1 trades exist.
6. **Counterfactual bias filters** — using the logged `b1..b4_state` columns:
   "U3's losers: 61% had B2 disagreeing at entry" — cheap hypothesis generator
   for the next roster.
7. **Mirror parity** (when NP_Trades CSV present): U0 vs real trades — count
   match, per-trade profit_R correlation, mean absolute gap (§10 AT-2 uses this).
8. **Statistical caution block (always printed, not optional):** number of
   universes tested, reminder that the top-ranked universe is partly selected
   noise, and the rule we agreed: *a winner must validate on an unseen period*.
   With `--split DATE` the report adds an in-sample/out-of-sample table and
   flags universes whose ranking collapses out-of-sample.
9. Data-quality section: `ambiguous_bar` rate, `END_OF_RUN` counts, spread stats.

### 9.3 Explicitly handled edge cases

`pf=INF` (no losses, small n → shown as "INF (n=3) — insufficient data"),
universes with 0 trades (listed, not dropped — "never fired" is a finding),
duplicated run_ids, mixed symbols (grouped, never averaged together).

---

## 10. Acceptance Tests (must pass before v3.6.0 ships)

| # | Test | Pass condition |
|---|---|---|
| AT-1 | Fresh tester run, default roster, 1 month M1 XAUUSD | `NPSU_Trades` exists with >0 rows; every active universe appears in summary; no journal errors (rule L1 — never ship a "looks wired" feature again) |
| AT-2 | Mirror parity: same run, compare U0 vs real NP_Trades CSV | Trade count within ±10%; per-trade profit_R correlation ≥ 0.9; mean absolute profit gap ≤ 0.15R; documented explanation for every unmatched trade |
| AT-3 | R-conversion unit check on XAUUSD *and* BTCUSD | Hand-computed R values for 3 synthetic trades match logger output exactly (rule L5) |
| AT-4 | Real-path regression: NPSU **disabled** | Real trade list byte-identical to v3.5.0 on the same data (proves the compute-mask refactor changed nothing) |
| AT-5 | Real-path regression: NPSU **enabled** | Real trade list still byte-identical (proves read-only signal layer + no global consumption) |
| AT-6 | Config error handling | Malformed U-string → journal error naming input + token, universe shown as CONFIG ERR, run continues |
| AT-7 | Crash safety | Kill terminal mid-run → trades CSV complete up to last closed trade (streaming, rule L7) |
| AT-8 | Static verify + UTF-8 + semver | Existing pre-zip checks; `EA_VERSION` and `#property version` → 3.600 |

---

## 11. Rollout Plan

**Phase 1 (v3.6.0)** — everything in this document. Build order:
1. Compute-mask refactor + AT-4 regression (safest first, isolated).
2. `UniverseRoster.mqh` parser + validation (pure logic, testable alone).
3. `VirtualBook.mqh` + trail-helper extraction from TradeManager + AT-3.
4. `UniverseEngine.mqh` + per-universe consumption + dashboard.
5. `UniverseLogger.mqh` + AT-1/AT-7.
6. Python analyzer + AT-2 parity run.
7. Full acceptance pass, presets (`NP_NPSU_default.set`), zip.

**Phase 2 candidates (v3.7+, after NPSU data exists):**
dual T1 pulse streams (A-only + A+S side-by-side, unlocking `t1s`/`t1mode`
overrides); per-universe session filters; walk-forward automation in the
analyzer; ensemble/voting experiments (the DriftPro idea, done properly).

**Phase 3 (agreed direction, added v1.1): LIVE ADVISOR.**
The universes run on the live account's chart in real time, and the EA
*suggests* which strategy currently fits the live market structure. Design
principles agreed now so Phase 1 collects the right data:

- **Advisory only, never auto-switch.** The suggestion appears on the dashboard
  and in the journal ("NPSU ADVISOR: last 30 days favour U5 (T1+T7): dd 2.1R,
  streak 3, pf 1.4 — current live config = U1"). The human changes the config.
  Auto-switching chases in-sample winners — the exact trap rule L11 exists for.
- **Eligibility gate before a universe may be suggested:** ≥30 closed virtual
  trades in the evaluation window, AND it already validated out-of-sample in
  backtest (analyzer's `--split` verdict recorded in the roster preset).
- **Hysteresis:** the suggestion may only change after the challenger wins the
  survival-first comparison for N consecutive evaluation windows (default 3).
  No strategy-hopping on noise.
- **Rolling windows, not all-time:** live ranking uses a rolling window
  (default 30 trading days) so the advisor reflects *current* market structure;
  Phase 1's summary snapshots (`export_time` history) already give Python the
  data to prototype exactly this offline before any live code is written.
- Phase 3 needs nothing changed in Phase 1 except discipline: keep snapshots
  append-only and keep every universe's config self-describing (§8.4) — both
  already in the design.

---

## 12. Decisions — ✅ ALL APPROVED by Girish, 2026-07-12

| # | Decision | My default | Alternative you might prefer |
|---|---|---|---|
| D1 | Same-bar SL+TP ambiguity | Count as SL (pessimistic) | Count as TP, or 50/50 — I advise against both |
| D2 | Open positions per universe | 1 (clean curves) | Allow 2–3 with skip-counting |
| D3 | Virtual management cadence | Closed M1 bars | Tick-level (slower, non-deterministic across runs) |
| D4 | Ranking currency | R-multiples | USD at fixed lot |
| D5 | `t1s`/`t1mode` per universe | Deferred to v3.7 (parser rejects mismatch) | Build dual pulse streams now (+~1 week complexity) |
| D6 | Default roster | The 12 in §5.3 | Tell me your combos — the DSL takes anything |
| D7 | NPSU default state | OFF (`InpNPSU_Enabled=false`) | ON by default in research presets only |

---

## 13. Phase 3 — LIVE ADVISOR (detailed design, v1.4 — implemented v3.7.0)

The principles were agreed in §11; this section is the buildable spec.

### 13.1 What it does — and what it never does

Every `InpADV_EvalHours` (default 24) of chart time, the advisor ranks all
active universes over a ROLLING window of `InpADV_WindowDays` (default 30)
by the official survival-first rule, and maintains a RECOMMENDATION: the
strategy that currently fits the market. It announces the recommendation on
the dashboard, in the journal, in a CSV, and optionally via `Alert()`.

It NEVER: opens/closes/modifies real trades, changes the EA's real config,
consumes trigger pulses, or auto-switches anything. The human reads the
advice and decides. (Auto-switching on in-sample winners is the exact
selection-bias trap — rule L11.)

### 13.2 Data: per-universe ring buffer

VirtualBook gains a fixed ring of the last 256 closed trades per universe
(`close_time`, `profit_R`; END_OF_RUN excluded). Rolling metrics are
recomputed from the ring each evaluation — the all-time accumulators stay
untouched (lesson L4: one write path). Memory: 16 × 256 × 12 B ≈ 50 KB.

### 13.3 Window metrics + ranking

Per universe, over trades with `close_time ≥ now − WindowDays`:
trades `n`, `net_R`, `max_dd_R` (equity walk of the window), `worst_streak`,
`pf` (INF-guarded), `worst_roll20_R` (n≥20, else net_R). Ranking is the
official rule: max_dd ↑, worst_streak ↑, worst_roll20 ↓ ... i.e. lowest
drawdown → lowest streak → best worst-rolling-20 → highest pf.

### 13.4 Eligibility gate (before a universe may be recommended)

1. `n ≥ InpADV_MinTrades` (default 30) inside the window, AND
2. the strategy is marked out-of-sample validated: new optional strategy-file
   key `validated=1` (set it after the analyzer's `--split` verdict passed;
   default 0). `InpADV_RequireValidated=false` relaxes rule 2 for research.
   U0 MIRROR counts as validated by definition (it IS the live config).

No eligible universe → the advisor says exactly that (loudly) and keeps the
previous recommendation.

### 13.5 Hysteresis state machine (no strategy-hopping)

```
state: recommendation R, challenger C, wins W
eval: best = top-ranked eligible universe
  best == R            → C=∅, W=0                       (champion holds)
  best == C            → W++                            (challenger persists)
  best == other        → C=best, W=1                    (new challenger)
  W ≥ InpADV_ConfirmEvals (default 3) → R=C, announce RECOMMENDATION CHANGED
initial R = first eligible best (normally MIRROR once it has 30 trades)
```

A challenger must therefore win ~3 consecutive daily evaluations — one noisy
day cannot flip the advice.

### 13.6 Outputs (all four, every evaluation)

1. **Journal**: one line per evaluation; a `*** RECOMMENDATION CHANGED ***`
   banner on switches, with the "advisory only" reminder.
2. **Dashboard**: two `NPSU_ADV` text lines above the scoreboard —
   recommendation, window stats of the best universe, challenger progress.
3. **CSV** `NPSU_Advisor_<same tail>.csv`, schema **NPSU-A1** (append-only):
   `schema_version, eval_time, run_id, window_days, min_trades, eligible_count,
   recommendation, note, best_name, best_trades, best_net_R, best_dd_R,
   best_streak, best_pf, mirror_trades, mirror_net_R, challenger,
   challenger_wins`. Documented in the auto-written data dictionary (now
   `NP_DataDictionary_NPSU-2.md`).
4. **Optional** `Alert()` popup on recommendation change (`InpADV_Alert`).

### 13.7 Runtime auto-adoption (v3.11 — Director's decision)

`InpADV_AutoAdopt` = NONE (default) / WIN_RATE / EQUITY / LAST_TRADE lets the
EA adopt the best virtual performer into the REAL account at runtime, after a
per-universe warm-up (`InpADV_AutoWarmup`, default 10 trades;
`InpADV_AutoRequireAll` optional) and rate-limited by
`InpADV_AutoCooldownMins`. Adoption goes through the same apply path as a
human click (loud journal, panel highlight, session-only). This reverses the
§13.1 advisory-only default under research conditions — recorded with the
architect's objection (win-rate ignores trade size; last-trade is n=1
evidence) and the governing rule of §13.9: a criterion may drive the real
account only after its meta-switcher has won in backtest and validated
out-of-sample.

### 13.8 Meta-switchers — switching as a strategy under test (v3.12)

Three virtual participants race ALONGSIDE the base universes on identical
data: **M_EQUITY**, **M_WINRATE**, **M_LASTTRADE** (ids 16–18). Each holds
one base universe at a time by its criterion (warm-up `InpMETA_Warmup`,
cooldown `InpMETA_CooldownMins`) and inherits the held universe's closed
trades into its own book — via the same single accumulator path as every
book (`_VB_Accumulate`, lesson L4). Fairness rules: closed trades only (no
lookahead); a switch applies to trades that OPEN after it (clean
attribution); flat until warm-up; every adoption writes an ADOPT audit row
(verifiable timing). Switchers never touch gates, cannot be recommended by
the advisor, and cannot be applied to the real account (guarded). The
analyzer's "Meta-switchers vs holding" section reduces the question *does
adaptive switching beat holding?* to one table against the best
held-forever base universe.

**Pre-registered predictions (recorded before any data):**
Fable — M_EQUITY finishes within noise of the best held-forever base;
M_LASTTRADE finishes below it (n=1 form-chasing is the failure mode
survival-first exists to prevent). Girish — the market is dynamic; the
in-form strategy adapts best. The result becomes DR/LR entries either way.

### 13.9 Honest limitations

The recommendation is a HYPOTHESIS about the current regime, not a verdict:
a 30-day window on one symbol is small; regime shifts lag by up to a window;
and ranking 12+ universes daily re-introduces multiple comparisons — which is
exactly why the eligibility gate demands prior out-of-sample validation and
why nothing switches automatically. Backtests are the laboratory; the advisor
is only the messenger.

---

## 14. Dashboard Integration & One-Click Apply (v3.8–v3.9)

### 14.1 The NPSU section (v3.8)

The universe table is a NATIVE dashboard section that shares the CANDLE
TIMEFRAMES slot — the two views swap via a `[NPSU]/[TF]` button in the
section header (the `[-]` collapse works in both modes and reflows the
panel exactly as before). Advisor ON ⇒ the slot starts in NPSU mode;
advisor OFF ⇒ candles (both remain click-toggleable). Because both views
share one frame, overlap with POSITION/HISTORY is impossible by
construction. Rows: rank | strategy | EQ(R) (virtual account, R-multiples)
| P/L (wins/losses) | win% | POS (open virtual trade's live floating R).
Sorting: `InpNPSU_SortBy` = equity or winning trades, on a display copy
(rule L10); U0 MIRROR is always kept visible. `*` + gold = the Live
Advisor's current recommendation; the advisor status line (including the
warming-up state) closes the section.

### 14.2 One-click apply (v3.9) — the human pulls the trigger

Every row carries a swatch button styled and highlighted EXACTLY like the
signal-gate toggles (dark-green fill + bright teal border when active).
Clicking a row APPLIES that universe to the REAL account: its bias and
trigger gates via the same `Xx_SetEnabled()` paths the dashboard gate
toggles use, plus trail/BE/RR via the `CFG_*` runtime config. Rules:

- **Radio:** at most one strategy applied; clicking another switches,
  clicking the active one restores the preset/input defaults.
- **Master swatch** in the section header: green ⇔ some strategy applied;
  clicking it restores defaults.
- **Session-only:** reattach/reload inputs resets everything; the .set
  file on disk is never modified.
- **Loud journal** on every apply/restore; open positions keep being
  managed normally (management is magic-based, not gate-based).
- `InpNPSU_AllowApply=false` disables the feature for look-don't-touch
  sessions.
- Known caveat: after an apply, U0 MIRROR still mirrors the INIT-time
  config — the applied universe's own row is the live benchmark.

This preserves the Phase-3 principle: the advisor only advises; a HUMAN
CLICK moves the real account, and only for the current session.

---

## 15. Verification & Validation of Virtual Trades (v3.10)

**The bottleneck (Girish):** real trades are validated by MT5 itself —
fills are the broker's, visible on the chart. Virtual trades are computed
by VirtualBook; if it is wrong, every research conclusion is wrong. Who
verifies the verifier? Answer: FOUR independent layers — no single piece
of code has to be trusted.

### 15.1 Layer 1 — real trades as ground truth (mirror parity, AT-2)

U0 MIRROR trades the real config through the virtual engine. Every real
trade must have a virtual twin: same entry second, same entry price, same
exit type, R within tolerance. Status: **passed twice** on live tester
runs (6/6 trades matched, mean gap ≤ 0.05R). BE and trail use the SAME
shared MoneyManager functions as the real TradeManager, so every real
trade validated by eye also validates the shared logic.

### 15.2 Layer 2 — the audit trail (`NPSU_Audit_*.csv`, schema NPSU-D1)

With `InpNPSU_Audit=1` every management DECISION streams one row:

| event | meaning | justification carried |
|---|---|---|
| OPEN | virtual entry | ref1 = spread (pts), ref2 = risk distance (1R) |
| BE | SL → entry | ref1 = trigger level entry±1R, ref2 = risk; bar OHLC that reached 1:1 |
| TRAIL | SL followed structure | ref1 = the closed candle low/high it followed, ref2 = min-distance floor |
| CLOSE | fill | fill price, exit reason, full bar OHLC |
| VIOLATION | runtime invariant broke | the offending values — investigate immediately |

Any single trade can therefore be validated BY HAND against the chart —
the same way real trades are validated. `InpNPSU_DrawUniverse=<name>`
additionally draws that universe's virtual trades on the chart
(entry/exit arrows + dotted connector with an R tooltip) for visual audit.

### 15.3 Layer 3 — independent replay (`np_trade_verifier.py`)

A SECOND implementation of the rules, written independently in Python.
Level 1 needs only the CSVs; Level 2 takes raw M1 bars exported from MT5
by the user (chart → Ctrl+S) — data the EA cannot fabricate — and replays
every trade from scratch. Rules verified:

| # | rule |
|---|---|
| R1 | one OPEN + one CLOSE per trade; matches its NPSU_Trades row; profit_R recomputed from prices |
| R2 | SL only ever moves in the trade's favour (monotonic) |
| R3 | BE only after a bar's excursion reached 1R; at most once; TRAIL only after BE |
| R4 | every TRAIL lands on the recorded candle level (ref1) or the close−floor fallback (ref2) |
| R5 | SL fills at worse-of(SL, bar open); TP at worse-of(TP, bar open); same-bar SL+TP ⇒ SL + ambiguous_bar=1 |
| R6 | fill inside the closing bar's true range [min(l,o), max(h,o)] |
| R7 | (--bars) every audit event's recorded OHLC matches the exported bars |
| R8 | (--bars) walking ALL bars with the SL active at the time, the FIRST hit is exactly the logged close (no missed, no invented exits) |
| R9 | (--bars) BE was not late — no earlier bar had already reached 1R |

Two implementations (MQL5 + Python) must agree on every trade; any
disagreement names the trade, the bar and the broken rule. **Tested:** a
synthetic run with one clean and one deliberately corrupted trade — the
clean trade passed R1–R9, the corrupted one was caught on all six
violated rules.

### 15.4 Layer 4 — runtime invariants inside the EA

Every virtual close is self-checked (fill inside the closing bar's range);
a failure prints an `*** INVARIANT VIOLATION ***` journal banner AND a
VIOLATION audit row. Nothing can fail silently (rule from day one).

### 15.5 The trust chain, end to end

Your eyes on real trades → mirror parity → auditable decisions per trade
→ independent mathematical replay against broker-exported bars → runtime
self-checks. When the verifier prints ALL CHECKS PASSED, virtual results
deserve the same trust as real ones — and when it doesn't, it tells you
exactly which trade to look at.

---

## Appendix A — Data Dictionary (master copy; loggers auto-write this as the sidecar, §8.4)

### A.1 File naming & joining

- `NP_Trades_<SYM>_<TF>_<start>_<id>.csv` — REAL closed trades (TradeLogger, since v3.5.0).
- `NPSU_Trades_<SYM>_<TF>_<start>_<id>.csv` — closed VIRTUAL trades, all universes (v3.6.0).
- `NPSU_Summary_<SYM>_<TF>_<start>_<id>.csv` — per-universe metric snapshots (v3.6.0).
- All files from one EA run share the same `run_id` value — join on it.
- Location: MetaQuotes `Common\Files` by default (works in Strategy Tester too).

### A.2 `NP_Trades` columns (schema NPT-2; NPT-1 = same without `schema_version`)

| Column | Type/Unit | Meaning |
|---|---|---|
| schema_version | text | `NPT-2`. Unknown value → stop, do not guess |
| run_id | text | Unique per EA run; joins all files of that run |
| ea_version | text | NeelPrajna version, e.g. 3.600 |
| symbol / chart_tf | text | Instrument and chart timeframe of the run |
| position_id | int | MT5 position identifier (real ticket lineage) |
| gate | text | Which TRIGGER opened it: T1 Pattern, T2 AutoFibo, T3 Sweep+FVG, T4 TrendLines, T5 Topography, T7 MarketMetrics, MANUAL, CHAIN |
| variant | text | Sub-pattern within gate. T1: empty = Pattern A (3-candle reversal), `s` = Pattern S (sweep-and-reclaim) |
| direction | text | BUY / SELL |
| lots | double | Executed volume |
| open_time / close_time | datetime | Server time |
| duration_s | int | Seconds open. 0–2s + exit EA_CLOSE usually = GroupSL cross-gate kill |
| open_price / close_price | double | Fill prices |
| sl_initial / tp_initial | double | At entry; 0.00 = none set / closed before IN processed |
| profit | double USD | Net incl. swap+commission |
| exit_reason | enum | TP, SL_LOSS (original SL), SL_TRAIL_BE (SL at/beyond breakeven → managed exit), EA_CLOSE (EA closed it, e.g. GroupSL), MANUAL_CLOSE |
| open_hour / open_dow | int | Server hour 0–23; day 0=Sun..6=Sat |
| atr14_open | double price | ATR(14) chart-TF at entry |
| spread_pts_open | int points | Spread at entry; constant value across a backtest = fixed-spread tester setting |
| bias_state | text | Combined bias layer at entry (BUY/SELL/FLAT) |
| sweep_depth_atr / c3_body_atr | double ATR | T1 pattern metadata (Pattern S sweep depth; confirm-candle body). Empty for non-T1 |
| risk_pct…t7_on (9 cols) | mixed | Config snapshot: risk %, RR ratio, trail/BE/GroupSL on, T1 entry mode, Pattern S on, T7 on — every row self-describing |

### A.3 `NPSU_Trades` columns (schema NPSU-T1)

As §8.1. Differences from real log, spelled out: `universe_id`/`universe_name`
identify the strategy; `trade_seq` replaces position_id (no real ticket exists);
results are in **R-multiples** (`profit_R`: profit ÷ initial risk distance;
1R = the trade's own planned risk); `profit_usd_ref` is informational at fixed
0.01 lots; `sl_final` shows where management left the SL; `ambiguous_bar`=1
means the closing M1 bar spanned both SL and TP and SL was assumed (pessimistic
policy); `b1_state..b4_state` record ALL bias gates at entry (BUY/SELL/FLAT)
regardless of which the universe used — for counterfactual filter analysis;
`cfg` echoes the universe's full normalized definition string;
`exit_reason` adds END_OF_RUN (force-closed at deinit — exclude from PF).

### A.4 `NPSU_Summary` columns (schema NPSU-S1)

As §8.2. Notes for the reader: rows are append-only snapshots — take the latest
`export_time` per (`run_id`,`universe_id`) for final results, or the time series
for rolling analysis; `pf` = gross_win_R / gross_loss_R, literal text `INF`
when no losses (treat as "insufficient data" when trades < 20); `max_dd_R` =
peak-to-trough of the R equity curve; `worst_streak` = most consecutive losses.

### A.5 The official ranking rule (survival-first)

Rank universes by: **1)** lowest `max_dd_R` → **2)** lowest `worst_streak` →
**3)** best worst-rolling-20-trade net_R (ranging-market behaviour) →
**4)** highest `pf`. Raw ROI is never the criterion. A winner is provisional
until it validates on a period it was not selected on.

### A.6 How to resume this research (for a future AI or human)

1. Read the release zip's `HANDOVER.md` (project map) and this design doc.
2. Load the newest `NPSU_Summary` + `NPSU_Trades` CSVs; verify `schema_version`.
3. Run `python np_universe_analyzer.py <folder>` — the report reproduces every
   number and the ranking above.
4. The next experiment is always: take the current winner, validate out-of-sample
   (`--split`), then design the next roster from the counterfactual-bias section.

---

*End of document. Implementation of v3.6.0 in progress per §11 build order.*
