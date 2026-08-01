# ADR-004 amendment — summary and standing rules

One-page companion to `ADR-004-evaluation-cadence.md` §6. Written 2026-07-23, after the
v5.9.0 twin measurement (run 40906). Read this first; the ADR has the full working.

---

## The one-line version

We feared that evaluating sequences at bar close instead of every tick would lose trades.
**It loses nothing — because every gate is already computed on closed bars.** The fear was
sound, the answer was zero, and the reason is a condition that could stop being true.

## The numbers

XAUUSD M1, 2026.07.01–22, every-tick modelling, 7 static universes vs their compiled twins:

    trades   597 -> 596      (one trade in 597)
    net R    -3.806 -> -2.847

Five of seven pairs identical to three decimals. Three separate code paths — the legacy
tick-level law, a `.seq` sequence, and a compiled 1-step twin — all returned exactly
**17 trades, 64.7% win, +5.565 R, 3 TP / 6 SL / 8 BE**.

## Three rules earned here

### R1 — Separate deterministic claims from statistical ones

The equivalence above is *deterministic*: three code paths agreeing to three decimals cannot
happen by luck, so a 22-day window is sufficient to establish it.

Every claim about which strategy is *better* is *statistical*: those universes carry 15–18
trades each, and nothing about relative performance can be concluded from them.

The same run supports one kind of claim completely and the other not at all. Ask which kind
you are making before quoting a number from it.

### R2 — A comparison is valid only when the arms differ in exactly one thing

The v5.8.0 twin test read −3.00 R against +5.84 R and looked like a devastating cadence cost.
The entire 8.8 R gap was break-even: one arm had it, the other did not, because the 6a grammar
had no `BE`. The instrument was measuring itself.

Before trusting any A/B in this system, enumerate what differs between the arms and confirm
the list has one item on it.

### R3 — Only compare within a run

Run 94984 was 20,464 bars / 8,382,860 ticks. Run 40906 was 21,844 bars / 8,913,891 ticks.
Different data. Every universe gained trades between them, which no input change could cause.

A conclusion drawn across those two runs — that break-even had hurt `TrendPullback_Fibo` —
was wrong and has been withdrawn. Break-even cannot change trade count; the trade count
changed; therefore the difference was the dataset.

## The condition this all rests on

**Every gate is evaluated on the closed bar (shift 1).** That is why tick-level evaluation
has nothing extra to see, and it is not enforced anywhere in code.

> **Before adding any gate that reads the current, unclosed bar — tick momentum, spread or
> volume bursts, sub-bar sweeps — re-run the twin A/B.** Such a gate would be visible to the
> legacy walk and invisible to the sequence FSM, and the tick-mode split in ADR-004 §4 would
> become necessary rather than optional.

## What changed as a result

- ADR-004 C2 lifted: 6c unification is now supported by measurement, and can be gated on
  "twin books identical to source books" rather than the impossible "deal list byte-identical".
- ADR-004 §4 (tick-capable FSM split) is **not** being built.
- No window was widened and no parameter was tuned. `KL_SweepConfirm` and
  `StructBreak_Retest3` remain at zero trades — they are **untested, not rejected**, and the
  honest fix is timeframe-aware steps in the grammar (Phase 7), not a hand-picked M1 number
  chosen because it scored well.

## The trap that was avoided, and why it is worth remembering

The obvious next move after this run was to widen `WIN` until the dead sequences produced
trades, then keep whichever width scored best. On 15–18 trade samples that is fitting noise,
and it would have produced a confident-looking number with nothing behind it.

Widening a window is legitimate when the value comes from design intent — the doc conceived
`KL_SweepConfirm` as a 1H sweep with a 5m rejection, so "6 bars" plausibly meant 6 M5 bars,
i.e. 30 on M1. It stops being legitimate the moment the value is chosen by looking at the
result.

The tell is simple: **if the number was picked before seeing the outcome, it is design; if it
was picked after, it is fitting.**
