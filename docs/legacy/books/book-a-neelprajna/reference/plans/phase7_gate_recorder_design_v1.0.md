# Phase 7 design — Gate Recorder, Python Replay Engine, offline strategy search

- Status: **draft for review**, 2026-07-23
- Author: design session with Claude, owner Girish Kumar
- Depends on: Phase 6 (`phase6_completion_record.md`), ADR-003 (SequenceEngine), ADR-004 (cadence)
- Supersedes nothing. Adds no behaviour to the live entry path.

---

## 1. The problem

NPSU can race 63 shadow universes in one backtest pass. That was enough to
compare a handful of hand-written ideas. It is nowhere near enough for the
question Phase 6 actually opened up:

> Of all the bias/trigger combinations and all the sequences expressible in
> the SeqCodex grammar, which ones are worth trading?

The grammar's combinatorics are large. With 5 bias gates, 8 triggers, up to
4 steps, window lengths and RR, the space is millions of candidates. At one
backtest per configuration and 63 universes per pass, exploring it inside MT5
would take years of wall-clock time.

The obvious escape — export tick data and rebuild everything in Python — is a
trap, for a reason this project has already measured. See §3.

## 2. The insight

**Record the gate truth, not the price data.**

Every gate is already computed, correctly and causally, by the EA on every
tick inside `EG_EvaluateAllGates()`. That computation is the expensive,
error-prone, irreproducible part. The strategy layer above it — "which gates,
in what order, within what window" — is trivial arithmetic over booleans.

So: have the EA write down what the gates said, once. Then let Python replay
that recording as many times as we like, testing any number of strategies,
without ever recomputing an indicator.

Python never sees a moving average. It sees a stream of facts the EA
established.

## 3. Why the obvious alternative fails

Reimplementing the gates in Python means creating a **third evaluator**, in a
different language, with different indicator warm-up, different smoothing
conventions, different pivot tie-breaking and a different data pipeline.

We already know what a much smaller divergence costs. ADR-004 exists because
the same law evaluated at a different *moment* produced different trades. And
the v5.8.0 run showed a $2.76 difference in net profit between `Model=1` and
`Model=0` on **identical code**. That is the sensitivity scale of this system.

A Python reimplementation would diverge by far more than that, and unlike the
cadence gap, the divergence would be unbounded and undiagnosable. We would
spend months asking why Python says 18 trades and MT5 says 15.

**D1. Python never computes a gate.** Any proposal that requires Python to
reproduce indicator maths is out of scope for this phase, permanently.

## 4. What must be recorded

Gate booleans alone are insufficient. The replay must be able to answer
"what would this strategy have done", which needs the full decision context.

### 4.1 Gate stream (`GR_Gates_*.csv`) — write-on-change

One row each time the packed gate state changes.

    schema_version, run_id, time_msc, bid, ask, spread_pts, atr14, gate_mask

`gate_mask` packs 13 gates × 2 directions into one `uint`:

    bit  0..4   B1 B2 B3 B4 B6   buy
    bit  5..9   B1 B2 B3 B4 B6   sell
    bit 10..17  T1..T5 T7..T9    buy
    bit 18..25  T1..T5 T7..T9    sell

Packing gives compact rows and makes change detection a single integer
compare. Bit order is the SSE index space from `SequenceEngine.mqh`, so the
Python side needs no translation table.

**D2. Write-on-change, not per-tick.** Same discipline the UI already uses.
Gate state changes rarely relative to tick rate; a month of XAUUSD should be
hundreds of thousands of rows, not tens of millions.

### 4.2 Trigger levels (`GR_Levels_*.csv`) — on pulse birth

R is the currency of every comparison in this system, and R cannot be
computed without the stop distance. `_NPSU_TrigLevels()` already produces
per-trigger SL/TP; record them when a pulse is born.

    schema_version, run_id, time_msc, trig_idx, dir, has_levels, sl, tp, variant

**D3. Levels are recorded at pulse birth, not at consumption.** Different
strategies consume the same pulse at different times; the level belongs to
the pulse.

### 4.3 Price path (`GR_Bars_*.csv`)

The piece most easily forgotten. Gate rows say *when* to enter. They say
nothing about what happened next. Without OHLC the replay can open trades and
never close them.

    time, open, high, low, close, spread_avg

M1 OHLC for the whole range. Small next to tick data.

### 4.4 Provenance (`GR_Meta_*.csv`)

    ea_version, symbol, chart_tf, date_from, date_to, digits, point,
    broker, model, every Inp* value that affects gate computation

**D4. A recording is bound to the gate parameters that produced it.** Change
`InpB1_FastPeriod` or `InpT3_MinDisplacementATR` and every row in that file
becomes fiction. The meta file records the full gate parameter set, and the
replay engine refuses to run a strategy against a recording whose parameter
fingerprint differs from the one requested. This is the same idea as the
SeqCodex descriptor hash, applied to inputs.

## 5. The hard boundary

The recorder tests **strategy combinations** — which gates, in what sequence,
with what windows, RR and management. It can never test **gate tuning**.
Changing a gate parameter invalidates the recording and requires a fresh MT5
run.

This is a feature, not a limitation: it draws a clean line between "what the
market did" (expensive, authoritative, recorded once) and "what we do about
it" (cheap, exploratory, run millions of times).

## 6. The Python side

### 6.1 Architecture

    npreplay/
      loader.py     read + validate a recording, check parameter fingerprint
      stream.py     gate stream as an iterator of (time, bid, ask, mask, ...)
      fsm.py        port of SequenceEngine.mqh  (pure logic, no market maths)
      codex.py      port of SeqCodex grammar + normaliser + FNV-1a-32 hash
      book.py       port of VirtualBook + trade management (SL/TP/BE/trail)
      runner.py     evaluate N descriptors over one recording
      search.py     enumerate candidates, rank, deduplicate by hash
      validate.py   THE ACCEPTANCE HARNESS (§7)

`fsm.py` and `codex.py` are trustworthy precisely because they contain no
market mathematics. The FSM has already been ported once and tested through
nine transition scenarios during 6a development.

### 6.2 The hard part is not the FSM

It is `book.py`. Candle-structure trailing, break-even, the spread cap, the
one-position rule and GroupSL must behave identically to `VirtualBook.mqh`.
This is where divergence will actually appear.

The v5.8.0 run is the proof: break-even alone was worth **8.8 R across 15
trades**. A subtly different trailing implementation would produce
plausible-looking, wrong answers.

**D5. `book.py` is ported line-by-line from `VirtualBook.mqh`, not
reimplemented from its description.**

### 6.3 Intrabar ambiguity

When both SL and TP fall inside the same M1 bar, the outcome depends on the
path within the bar, which OHLC does not record. The EA's virtual book
already faces this and already counts it — `ambiguous_bars` is a column in
`NPSU_Summary`.

**D6. Python adopts the EA's existing convention exactly, and reports
`ambiguous_bars` identically.** Whatever the EA does — pessimistic, or
open-proximity ordering — Python does the same, so the two remain comparable
even where both are uncertain.

Measured incidence in the v5.8.0 run is reassuringly small: `ambiguous_bars`
was 0 for every reference universe, 1 across 142 trades for `T1_base` and 2
across 297 for `T1_noBias`. So intrabar ambiguity is a rounding concern here,
not a structural threat to the method — but the convention must still match,
because a single differently-resolved trade would break the D7 acceptance
gate for reasons that have nothing to do with a real defect.

## 7. The acceptance gate

This is what separates a measured instrument from a simulator we hope is
right.

**The replay must reproduce, trade for trade, virtual books the EA has
already produced.**

The July 1–22 run gives us the reference set today:

    TrendPullback_Fibo    15 trades   53.3% win   +13.000 R   8 TP / 7 SL
    T1_B1B6               15 trades   66.7% win    +5.842 R   3 TP / 5 SL / 7 BE
    Mirror1Step_T1_B1B6   15 trades   26.7% win    -3.000 R   4 TP / 11 SL
    T1_base              142 trades                +2.969 R

**D7. Phase 7 does not ship until `validate.py` reproduces these books:
same trade count, same open times, same directions, same R to within the
declared intrabar tolerance.** If it matches on universes the EA has already
run, it has earned the right to be believed about universes nobody has run.
If it does not match, we have found a real bug in one of the two — which is
also worth having.

This gate is the direct descendant of the §7 rule "baseline deal list
byte-identical", adapted per ADR-004 §5 to a case where the two paths are not
identical by construction.

## 8. What this unlocks

- **Combination search.** Every bias/trigger pair, every 1-step sequence, the
  full static space, ranked — in minutes rather than months.
- **Sequence search.** Step counts, window lengths, invalidator choices, RR
  and management, over the grammar Phase 6 already defines.
- **Timeframe questions.** The v5.8.0 run showed `WIN:6` is six minutes on M1
  and that `KL_SweepConfirm` and `StructBreak_Retest3` never complete there.
  A sweep over window length answers that in one pass instead of one run per
  value.
- **Honest overfitting control.** With millions of candidates, in-sample
  ranking is meaningless without out-of-sample discipline. See D8.

**D8. Every reported candidate must carry walk-forward results, not just
in-sample rank.** The search will always find something that looks
magnificent on three weeks of XAUUSD. The recording must be split into
train/test windows by default, and `search.py` must refuse to emit a ranking
that has not been evaluated out-of-sample.

## 9. The promotion path

A candidate found offline is a hypothesis, not a strategy. The route back:

    search.py ranks a descriptor
      -> seqgen.py writes the .seq file (same normaliser, same hash)
      -> the EA races it as a 6a shadow universe on real data
      -> if it survives, 6b dry-run on the real path
      -> only then armed

**D9. The descriptor hash is the identity across all four stages.** A
candidate discovered in Python, written by `seqgen.py`, raced in the shadow
books and armed on the real path is the same object with the same `#hash` at
every step. This is what the Phase 6 identity work was for.

## 10. Delivery

| stage | contents | gate |
|---|---|---|
| 7a | `Apps/GateRecorder.mqh`, four output files, meta fingerprint | recording completeness: replay one universe's entry times exactly |
| 7b | `npreplay` loader/stream/fsm/codex/book, `validate.py` | D7 — reproduce all four reference books |
| 7c | `runner`, `search`, walk-forward split, ranking, promotion to `.seq` | D8 — no ranking without out-of-sample |

7a is small and self-contained; the recorder is a passive observer on the
same snapshot the FSM already consumes, so it adds no decision path and
cannot change trading behaviour.

**D10. The recorder is off by default** (`InpGR_Enabled=false`) and writes
nothing when off, so the live EA is byte-identical to v5.9.0 unless the owner
turns it on.

## 11. Open questions for review

1. Should the gate stream also record `EG_BiasBuy/Sell` (the composed
   ALL-agree verdict), or only the individual gates? Recording only the
   individuals is more general — the composition can be recomputed — but the
   composed verdict is a useful cross-check that the replay agrees with the EA.
2. Do we record the real path's actual entries too, so the replay can be
   validated against the REAL deal list and not only the virtual books?
3. Recording size on a year of M1 — needs measuring on one month first.
4. Does `GroupSL` need porting for 7b, or can virtual books be validated
   without it? (The NPSU books may not use it; needs checking.)
