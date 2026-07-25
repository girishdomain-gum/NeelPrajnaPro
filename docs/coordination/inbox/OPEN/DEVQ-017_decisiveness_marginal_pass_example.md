# DEVQ-017 · QUESTION · Sprint 7 · 2026-07-25
Author: developer (claude-code)
Refs: DEVQ-016 REPLY (a) — the decisiveness strength ruling; belief.py
`_decisiveness` / `_stance_and_strength`

## Question
DEVQ-016 ruled `strength = 2·|p − 0.5|` (DECISIVENESS) and gave three worked
examples. I implemented the formula literally (it is the code contract and it is
what produces the named H-001 anchor). But ONE of the three worked examples is
arithmetically inconsistent with the formula, and the inconsistency also touches
the ruling's stated *rationale*, so I want it on the record before REV-S7 — I am
NOT blocked (implemented, tested, running; H-001's re-derived belief is on the
journal at 0.887).

The three examples vs the formula:

| case | ruling says | `2·|p−0.5|` actually gives |
|---|---|---|
| H-001 FAIL, p=0.9435 | 0.887 | **0.887** ✔ |
| p ≈ 0.5 (coin-flip) | ≈ 0 | **0** ✔ |
| marginal PASS, p=0.049 | **0.098** | **0.902**  (MISMATCH) |

`2·|0.049 − 0.5| = 2·0.451 = 0.902`, not 0.098. Two points:

1. **The example is a slip.** No monotone formula reproduces BOTH `0.098` for the
   marginal PASS AND `0.887` for H-001's FAIL — they pull in opposite directions
   (a stance-split rule that hit 0.098 for a PASS would make a *more* decisive PASS,
   p→0, get strength→0, which is inverted). The H-001 anchor (0.887) forces
   `2·|p−0.5|`, under which the marginal PASS is `0.902`. I implemented `2·|p−0.5|`.

2. **The rationale it illustrates is not achieved by the formula.** The ruling
   rejected p-as-strength because "a PASS at p=0.049 would claim strength 0.951 from
   borderline evidence." But `2·|p−0.5|` gives that same case `0.902` — only
   marginally lower than 0.951. Decisiveness measures distance from a coin-flip
   (p=0.5), and p=0.049 is FAR from a coin-flip, so a p=0.049 PASS is (correctly, on
   this metric) decisive — it is only "marginal" relative to the α=0.05 *significance
   cutoff*, not relative to 0.5. So the formula does not make marginal-significance
   PASSes weak; it makes coin-flip-ish results weak.

**Why this is likely moot in practice (supports the formula standing):** a real PASS
must clear the DEFLATED alpha, which after the FVG family's 502 trials is
`effective_alpha ≈ 1e-4`. A genuine PASS therefore has `p ≤ 1e-4`, giving
decisiveness `≈ 0.9998` — near-maximal. "Marginal PASS at p=0.049" can only occur
at zero deflation, so the over-belief the ruling worried about barely arises.

## Options considered
A) **Formula stands as written** (`2·|p−0.5|`, as implemented); correct the ruling's
   commentary — the marginal-PASS example should read `0.902`, and the "weakly
   supported" gloss applies to p≈0.5, not p≈0.05. My belief test asserts `0.902` for
   the p=0.049 PASS with this note.
B) You actually want strength to be LOW for a *marginal-significance* PASS (weak when
   p is just under the cutoff). That needs a different, threshold-relative definition
   (e.g. decisiveness measured against effective_alpha, not 0.5) — a real redesign,
   and it would NOT give H-001 = 0.887 on the `2·|p−0.5|` branch, so the anchor would
   need restating too.
Recommendation: **A.** The formula is unambiguous, matches the H-001 anchor and the
coin-flip example, and is near-maximal for real (deflated) PASSes; the `0.098` is a
calculator slip in the commentary. If you meant (B), it is a follow-up DEVQ/ADR, not
a one-line fix.

## How this blocks (or not)
Non-blocking. Implemented on A; H-001's belief re-derived to strength 0.887 on the
real journal (01KYCHPV8ZNT2F41F8JABD12K2, prior state 01KYCFNKCGSYFKWTRYKW54E9C8
retained). If you rule B, it is a localized change to `_decisiveness` +
re-deriving the one belief (the current state stays in the append-only chain).
