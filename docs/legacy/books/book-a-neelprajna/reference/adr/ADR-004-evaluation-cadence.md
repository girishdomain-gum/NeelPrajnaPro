# ADR-004 — Evaluation cadence: bar-close sequences vs tick-level legacy walk

- Status: **Accepted (constraint recorded), 2026-07-23**; **AMENDED 2026-07-23 after
  measurement — see §6.** Owner ruling: proceed on the Phase 6 design as written (D3
  stands); this ADR records the consequence so every future design or architecture change
  can account for it instead of rediscovering it. The measured cost turned out to be zero,
  for a reason that is itself a constraint — §6 is the part to read first.
- Relationship: constrains ADR-003 (SequenceEngine). Does not modify ADR-001 or ADR-002.
- Applies from: v5.6.0 (6a) onward.

## 1. Context — what was found

Phase 6 introduced a second way for the EA to decide an entry. The two now coexist and they
do **not** run on the same clock:

| | legacy static law | sequence engine (SSE) |
|---|---|---|
| evaluated | every tick, inside `EG_OnTick` | once per **closed** chart bar (D3) |
| fires | the moment a trigger pulses and bias agrees | at the close of the bar the pulse appeared in |
| sees a pulse that appears and vanishes mid-bar | yes | **no** |

This was not a mistake in the implementation; D3 chose closed bars deliberately, because a
sequence's windows (`WIN:n`) are counted in bars and a chase must not advance twice inside one
bar. The consequence, however, was not written down when D3 was decided.

## 2. Consequences that follow from it

**C1 — a 1-step sequence is not behaviourally identical to its static twin.**
Same law, different clock: the sequence enters at the bar close, the static universe entered
at the tick. Entry prices differ on essentially every trade, and pulses that do not survive to
the bar boundary are missed entirely by the sequence.

**C2 — Phase 6c cannot be validated as a pure refactor.**
6c's acceptance test was "compile the legacy law into 1-step sequences and prove the deal list
is unchanged". Under C1 that test cannot pass by construction. 6c is therefore either
(a) a behavioural change that must be validated as a new strategy, or (b) blocked on making
the engine tick-capable. See §4.

**C3 — 6b entry latency.** An armed sequence enters up to one bar later than the same signal
would have entered on the legacy path. On M5 that is up to five minutes of the move given up.
This is a real cost, not a rounding error, and it should be measured rather than assumed small.

**C4 — shadow vs live sequences agree with each other.** Both the 6a shadow universes and the
6b live driver sample at bar close, so they stay in step. The divergence is strictly
sequence-vs-legacy, never sequence-vs-sequence.

## 3. Decision

Proceed on the design as written. D3 (closed-bar windows) stands. 6a and 6b ship and are
evaluated with bar-close cadence, and the cost in C3 is treated as a **measurable quantity**,
not an accepted assumption: the `Mirror1Step_T1_B1B6` sequence and the v5.8.0 static twins
exist precisely to size it against the legacy law.

## 4. The escape hatch, if the measurement says the cost is real

> **Superseded by §6.** The measurement came back at zero cost, so this hatch is NOT being
> built. It remains documented because §6.3 identifies exactly what would reopen it.

The FSM itself is cadence-agnostic. The only bar-coupled logic inside `SSE_OnBarClose` is the
window counter and the invalidator check. Making the engine tick-capable means splitting one
function into two concerns:

- **advance evaluation** — guards, advancers, direction lock → may run every tick
- **bar accounting** — `barsInStep++`, window expiry, invalidators → runs once per closed bar

`WIN:n` stays counted in bars, so no definition, `.seq` file or hash changes. Estimated blast
radius: one signature, two call sites, no change to SeqCodex or to any descriptor.

This is deliberately **not** being built now. It is recorded so that the option is understood
rather than reinvented, and so that whoever picks up the rest of 6c knows the choice they are
making.

## 5. Standing rule for future changes

Any change that introduces a new evaluator, moves an existing one, or alters when a decision is
taken **must state its cadence explicitly** and say how it relates to the tick-level legacy walk
and the bar-close sequence engine. "Same law" is not sufficient grounds to claim "same
behaviour" — two evaluators agreeing on a rule but sampling at different moments will produce
different trades, and the difference will show up as unexplained deal-list drift long after the
change is merged.

Corollary for acceptance gates: a refactor may only be gated on "deal list byte-identical" when
the old and new code paths are evaluated at the same moments. Where they are not, say so in the
plan and choose a different gate up front.

---

# 6. AMENDMENT — the measurement (v5.9.0, run 40906)

## 6.1 Result: the cadence cost is zero

XAUUSD M1, 2026.07.01–22, **every-tick modelling**, seven static universes each racing a
compiled 1-step twin driven by the FSM:

| | source (tick-level law) | 1-step twin (bar-close FSM) | delta |
|---|---|---|---|
| trades | 597 | 596 | −1 |
| net R | −3.806 | −2.847 | +0.959 |

Five of seven pairs were **identical to three decimals** on both trade count and net R. Only
`T1_noBias` differed in trade count (316 vs 315, one trade in 316) and `MIRROR` in R (0.041).

The sharpest form of it: `T1_B1B6` (legacy law), `Mirror1Step_T1_B1B6` (a `.seq` file) and
`T1_B1B6_1S` (a compiled twin) all returned **17 trades, 64.7% win, +5.565 R, 3 TP / 6 SL /
8 BE**. Three independent code paths, byte-identical output.

This is a *deterministic* claim, not a statistical one, so the 22-day window does not weaken
it. Three code paths cannot agree to three decimals by luck.

## 6.2 Why it is zero — and this is the real finding

C1 assumed the tick-level walk sees pulses the bar-close FSM misses. It does not, **because
the gates are themselves computed on closed bars**. A pulse is born at a bar boundary and
holds for the whole bar, so by the time either evaluator looks, both see the same thing. The
static walk's per-tick evaluation is re-reading a value that only changes at bar edges.

The test was run under every-tick modelling, which is the condition most favourable to
tick-level evaluation. It still found nothing.

## 6.3 The condition that would reverse this

**Any gate that can pulse and vanish inside a single bar breaks the equivalence immediately.**
An intrabar trigger — tick-level momentum, spread or volume bursts, sub-bar liquidity sweeps,
anything evaluated on shift 0 rather than shift 1 — would be visible to the legacy walk and
invisible to the FSM, and §4's tick-mode split would become necessary rather than optional.

**Rule: before adding any gate evaluated on the current (unclosed) bar, re-run the twin A/B.
This amendment's result is conditional on every gate being closed-bar computed, and that
condition is not enforced anywhere in code.**

## 6.4 What this licenses

C2 is lifted. Phase 6c unification — retiring `_NPSU_TryEnter` and routing the real path
through compiled 1-step sequences — is now supported by measurement rather than argument, and
can be gated on "twin books identical to source books" instead of the impossible "deal list
byte-identical".

C3 (6b entry latency) is likewise measured at zero on M1 for closed-bar gates.

## 6.5 What this does NOT license

- **Higher timeframes.** Measured on M1 only. Bar-close latency scales with the bar; on M15
  the same test could read very differently. Re-measure per timeframe.
- **Any conclusion about which strategy is better.** The universes in this run carry 2 to 316
  trades each; most are 15–18. Those are statistical claims and the sample cannot support
  them. Only the *engineering* equivalence is established here.
- **Cross-run comparison.** Run 94984 (20,464 bars / 8,382,860 ticks) and run 40906 (21,844
  bars / 8,913,891 ticks) are different datasets. An earlier reading that break-even had
  hurt `TrendPullback_Fibo` was drawn across those two runs and is withdrawn — break-even
  cannot change trade count, and the trade count changed, so the difference was the data.
  **Only within-run comparisons are valid.**

## 6.6 Method note worth keeping

The twin A/B only became a valid instrument once v5.9.0 put break-even into the grammar. In
the v5.8.0 run the same comparison read −3.00 R against +5.84 R, and the entire 8.8 R gap was
one side having break-even and the other not. The instrument was measuring itself.

**A comparison is only valid when the two sides differ in exactly one thing.** Before trusting
any A/B in this system, enumerate what differs between the arms and confirm it is one item.
