# DEVQ-013 · QUESTION · Sprint 5 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-005 §4 + DoD ("selftest effect-size calibration (how strong is the
planted edge)"), Blueprint §4.7 step 3, qrf/kernel/battery/selftest.py

## Question
ARCH-005 §4 asks for three seeded synthetic suites the engine+stats must classify
PASS / FAIL / INSUFFICIENT, with the effect-size calibration left to me (the DoD
names it a likely DEVQ). This records the numbers, for ratification, since they
define what "the selftest passed today" asserts (Blueprint §4.7 gate).

## What I chose (implemented, tested — selftest.py)
Classifier: fewer than `MIN_N` trades → INSUFFICIENT; else a one-sided one-sample
t-test (H0: mean ≤ 0) at `ALPHA` — a significant positive mean → PASS, else FAIL.
A seeded percentile bootstrap CI is computed as groundwork for §4.7 step 6.
Zero-variance outcomes (a synthetic degeneracy) decide on sign alone.

| knob | value | why |
|---|---|---|
| `MIN_N` | 30 | matches the screener's `min_trades` floor (DEVQ-009) |
| `ALPHA` | 0.05 (one-sided) | conventional; the gate, not a verdict threshold |
| planted edge | 60 trades, drift 1.0, noise σ 1.0 | t ≈ 7.7 — a decisive, non-marginal PASS |
| pure noise | 60 trades, drift 0.0, noise σ 1.0 | mean not > 0 → FAIL |
| small-n | 8 trades, drift 1.0 | below `MIN_N` → INSUFFICIENT despite a real edge |

Data are episodic (each event → one non-overlapping trade), seeded via
`SeedSequence(seed).spawn(3)`, so the suite is deterministic and reproducible. The
engine is injected as a runner (kernel firewall stays clean); no verdict record is
written (AST-audited, mirroring the screener).

## Options considered
A) **Decisive edge (t ≈ 7.7), MIN_N = 30, α = 0.05** (as built). The planted edge
   is deliberately far from the decision boundary so a PASS is unambiguous and the
   selftest is a smoke test of the machinery, not a power study.
B) **Marginal edge near the α boundary** — tests statistical power too, but makes
   the daily gate flaky (a borderline suite can flip PASS/FAIL on reseed).
C) Different `MIN_N` (e.g. tie it to `split_spec`, or 50).

Recommendation: **A**. The selftest's job is "is the judge wired correctly today",
so the planted edge should be obvious and the noise obviously null; power analysis
belongs to the real verdict thresholds (S6, chosen independently). These are code
defaults; like DEVQ-009's thresholds they'd change only via a new DEVQ.

## How this blocks (or not)
Non-blocking. selftest.py is complete; tri-state correct on all three suites,
seeded and reproducible; wired to the real engine in tests.

## How to ask
Ratify A, or set a different (MIN_N, ALPHA, effect-size) triple.
