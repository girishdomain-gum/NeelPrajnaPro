# NeelPrajna — Work Orders for v3.17.0 (issued by Chief Architect, 2026-07-20)

How to use: open a fresh session with any capable AI model. Paste the COMMON
BRIEF from `docs/AI_ROLE_PROMPTS.md`, then the matching ROLE brief, then ONE
work order below. Attach the latest release zip. Deliverables come back to
Fable for design review before merge.

---

## WORK ORDER 1 — FeatureLogger (Role: Gate Developer, MQL5)

GOAL
One new module `FeatureLogger.mqh`: write ONE CSV row per closed M1 bar
with every gate's published state, so Python can evaluate strategy ideas
offline without re-implementing any gate. This is the "sensors write the
logbook" design (docs/NP_Architecture_Roadmap_v1.0.md, Phase 2).

SPEC
- Inputs: `input group "==== Feature Logger (v3.17) ===="`,
  `InpFLog_Enabled=false`, `InpFLog_UseCommon=true`.
- File: `NP_Features_<SYM>_<TF>_<runstamp>.csv` in Common\Files (same
  naming/run_id pattern as TradeLogger; share the run stamp).
- Schema NPF-1, exactly these columns, one header row:
  `schema_version,run_id,time,open,high,low,close,tick_volume,atr14,
  hour,dow,spread_pts,
  b1,b2,b3,b4,b6,b6_minR,
  t1,t1_sl,t1_variant,t2,t2_sl,t3,t3_sl,t4,t4_sl,t5,t5_sl,
  t7,t7_sl,t8,t8_sl,t8_q,t9,t9_sl,t9_q`
  - bias columns: `B` / `S` / `-` (neutral) / `off` (disabled+not compute)
  - trigger columns: `B` / `S` / `-` (pulse state on that bar)
  - `*_sl`: the gate's published SL while pulsing, else 0
  - `b6_minR`: weakest enabled window |R| (expose a small accessor in
    B6_RegChannelGate.mqh: `double B6_MinAbsR()` returning `_b6_minR`)
  - `t8_q`/`t9_q`: live pulse quality (expose `double T8_LastQuality()` /
    `T9_LastQuality()` returning `_t8_lastQ` / `_t9_lastQ`)
- Write timing: once per newly CLOSED M1 bar, AFTER EG_EvaluateAllGates()
  (hook from EG_OnTick next to NPSU_OnTick, or from OnTick after EG_OnTick
  — state your choice and why). Multiple missed bars: write one row per
  missed bar is NOT required — one row per observed new bar is accepted;
  document this in the header.
- Gates evaluated only under the NPSU compute mask still log (read the
  published EG_* globals exactly as the dashboard does; do NOT force
  evaluation of disabled gates).
- Buffered writes are optional; if you buffer, flush on deinit and note it.
- Version: 3.17.0 (Config + #property + HANDOVER entry + one-line in the
  data dictionary sidecar about NPF-1).

ACCEPTANCE TESTS (deliver evidence)
- AT-F1: with InpFLog_Enabled=false, zero behaviour change (no file, no
  journal noise beyond one init line).
- AT-F2: short tester run with logger on → row count equals closed-bar
  count observed (state both numbers), header matches NPF-1 exactly.
- AT-F3: rows during a T1 pulse show `t1=B/S` with nonzero `t1_sl`, and
  the matching NP_Trades entry time falls inside the pulse window.
- Static verify per the COMMON BRIEF.

OUT OF SCOPE: any change to existing gates beyond the three tiny
accessors named above; any schema change to existing CSVs.

---

## WORK ORDER 2 — NP Lab offline evaluator (Role: Python Research Analyst)

GOAL
New `analyzer/np_lab.py`: evaluate rule-based strategy ideas offline over
(a) the NPF-1 feature matrix and (b) an MT5-exported M1 bars CSV, with the
project's fill rules, producing the survival-first report. Python results
are hypotheses; MT5 remains ground truth.

SPEC
- No-argument mode like the other scripts (same `_auto_folder()` pattern);
  newest run by default.
- Inputs: NPF-1 features CSV (hard-error on unknown schema) + `--bars`
  M1 export (Ctrl+S format, comma or tab — reuse the verifier's loader).
- Rule definition: a small JSON/text file or `--rule` string, e.g.
  `entry: t1 in [B,S]; require: b1==t1, b6_minR>=0.6, hour in 4-16;
   sl: t1_sl; rr: 2.0; trail: 1; be: 1`
  Exact grammar is yours to design — document it in the module docstring
  and keep it declarative (no Python code in rule files).
- Fill simulation: entry at next bar open after the signal bar; SL/TP/BE
  at 1:1/candle-trail per the documented VirtualBook rules (the verifier's
  Level-2 replay implements them — reuse/factor that code, do not fork a
  third copy). Pessimistic same-bar SL+TP rule. One position at a time.
- Output: survival-first table (n, netR, maxDD_R, worst streak, PF, win%,
  R/trade) + per-hour breakdown + the count of rules tried this session
  printed on every report (multiple-comparisons honesty).
- CALIBRATION MODE (mandatory): `--calibrate` runs the baseline rule
  `entry t1, require b1==t1, rr 2.0, trail 1, be 1` over a period that
  also has a real run, and prints Python-vs-MIRROR deltas (n, netR, PF).
  The delta is the fill-model error and must be shown; if |netR delta| >
  20% flag the report as LOW CONFIDENCE.

ACCEPTANCE TESTS
- AT-L1: calibration vs run 68484 MIRROR (n=110, +9.14R, PF 1.17) with
  deltas printed.
- AT-L2: the same rule with `hour in 4-16` added produces a different,
  internally consistent report (subset n, recomputed stats).
- AT-L3: unknown feature column or schema → hard error, no guess.

OUT OF SCOPE: ML models, tick-level fills, any MQL5 change.

---

## REVIEW GATE (Fable)

Merge requires: acceptance evidence attached, static verify clean,
no contract violations, HANDOVER updated. Escalations per the role pack.
Sequencing: WO-1 first (WO-2 consumes its output); WO-2 may start against
a hand-made NPF-1 sample.
