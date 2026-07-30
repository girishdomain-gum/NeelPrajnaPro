# ARCH-NP-002 — IVF INSTRUCTION: independent re-derivation of the NP-S1 verdict (AC-6)
*Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. Sealed instruction for the session assigned **IVF / Validator**. Scope: AC-6 only. Every figure below was read from the committed ledger by the Architect this session and is quoted so the IVF has a target to *disagree with* — never a value to copy.*

---

## 0. Who may execute this

**Not the session that built the detector or ran the Battery.** ADR-006's independence is the whole point, and Roles §2.4 bars the Developer from judging its own work. A fresh session, assigned the IVF/Validator role, working from raw records and normative texts.

**`ivf/` never imports `qrf/`** (QRF-ADR-006, CI-enforced). Re-derive from file outputs — the journal, the bulk parquet, the YAML, the venues file — and from the normative texts. **Never from the Developer's Python.** If you find yourself reading `qrf/trading/concepts/neelprajna/detector.py` to learn what a sweep is, stop: read NP-ADR-008 §3 instead. That substitution *is* the failure mode this check exists to catch.

## 1. Drill first — nothing real is judged until the drill passes

Build a sacrificial copy. Plant each fraud **separately**, run the full re-derivation, and record catch/miss. **Six plants and one clean control:**

| # | Plant | What must be caught |
|---|---|---|
| P1 | alter one trade's `net` in the trades parquet | pooled mean / p / verdict no longer reproduce |
| P2 | change verdict `corrections.family_m` from 19 → 18 | effective alpha no longer equals 0.05 ÷ family trials |
| P3 | delete one `trial_count` record from the family | family total ≠ 19; deflation mismatch |
| P4 | swap the cost model to $0.26 | gross-minus-net per trade ≠ 0.41 |
| P5 | move the window `ts_end` by one bar | trade set and fold boundaries shift |
| P6 | edit the registration's `thresholds` after the fact | verdict `thresholds` no longer byte-equal to the hypothesis record |
| C0 | **untampered control** | **must raise nothing** |

**A miss on any plant, or a false alarm on C0, is RED and the real re-derivation does not proceed.** Record the drill in the IVF report before touching real records.

## 2. Re-derive the real verdict

**Target record:** verdict `01KYSGQR3D8SYSVJFSF9M77CMY` · hypothesis `01KYSETR2C85MRRVWZCM8V0GMC` · window `01KYSEDSM6K5ZKWK0XRCC4SVZ7` · burn `01KYSGQR6K1HHRT66R78BV6Z8Y` · trades manifest `01KYSGQQKWABAZS4Y6TNF9Q7SP`.

Re-derive independently, then compare. **Tolerance 1e-9** on every float.

| Quantity | Ledger value to disagree with |
|---|---|
| n_trades | 259 |
| net mean | 1.5195945945945775 |
| gross mean | 1.9295945945945765 |
| one-sided p | 0.057415412388292036 |
| t stat | 1.5821919583845476 |
| CI | [−0.3067311776062075, 3.389103764478732] |
| family_m / effective_alpha | 19 / 0.002631578947368421 |
| fold n | 64, 70, 63, 62 |
| fold means | +3.1896093750000145, +3.7879285714285915, +0.4915079365079102, −1.7206451612904061 |
| verdict | FAIL |

**Chain checks, each a separate pass/fail line:**
1. **Hash chain intact** across the whole journal; no torn tail.
2. **Burn is atomic with the verdict** — the burn names this verdict as `consumed_by`, on this lineage, on this window. A verdict without its burn, or a burn naming a different verdict, is RED.
3. **Family total is exactly 19** by summing `trial_count.n_attempts` over records matching `xauusd/neelprajna` — and **re-derive membership from `deflation.py`'s stated rule**, not by trusting the `family` string. Confirm no sibling-family record was miscounted in either direction.
4. **Cost model applied:** gross mean − net mean = **0.4100** (±1e-9), and `configs/venues.yaml`'s `xauusd_retail_h07` computes 0.24 + 2×(0.05+0.035) = 0.41.
5. **Thresholds byte-equal** between the hypothesis record as registered and the verdict's copy.
6. **Window designation** is TRAINING and its bounds equal the ratified UTC half-open interval `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)`.
7. **Selftest gate** is recorded on the verdict (`selftest_seed 20260725`), and the run's seed is reproducible from `seeds.for_run`'s stated derivation.
8. **`embargo_bars ≥ hold_bars + 1`** holds as registered (15 ≥ 13).

## 3. Four things to check that no one has checked

These are not in the Battery's own gates, and the Architect has not verified them either. **They may fail; that is why they are here.**

1. **The verdict does not depend on deflation.** p = 0.0574 exceeds even the undeflated 0.05. Confirm the FAIL survives at base alpha — i.e. that the 19-vs-18 ruling could not have changed the outcome. If this is false, say so loudly.
2. **The three non-equivalence statements** (NP-ADR-008 §2.1) appear in the registration's `outcome_interpretations`, verbatim. Their absence would mean the verdict can be read as speaking for the historical T3 gate.
3. **Detector fidelity, independently:** re-derive the SWEEP event count from the M5 bars using **NP-ADR-008 §3's text alone**. The Developer reports 325 against the bespoke stack's historical 325. Agreement corroborates; disagreement is more valuable.
4. **The bar build is honest:** 16,029 M5 bars from the 60 Stage-2 tick files, mid = (bid+ask)/2, clean ticks only, timestamps converted from broker UTC+3. Spot-check at least the first and last bar and one weekend seam.

## 4. Report

`ivf/reports/IVF_NP-S1_AC6.md` — drill results first, then each check as an explicit **PASS / FAIL** line with the re-derived value beside the ledger value. **GREEN only if every line passes.** RED anywhere: name it, do not soften it, do not average it, and do not proceed to HC. Per QRF-ADR-006, **a check RED twice freezes forward work.**

**State honestly what you could not verify** — anything requiring `F:\NeelPrajna` artifacts outside this repository, and the fact that `LiquiditySweepGate.mqh` is deleted so H-07's MQL5 original cannot be re-derived from source by anyone.

## 5. Non-goals

No code in `qrf/**`. No new hypotheses, registrations, runs, or burns. No edits to normative documents or to NP-ADR-008. No re-run of the Battery — **the window is burned, and a second run must be structurally refused**; if it is not refused, that itself is a RED finding of the first order.

---
*Anchor: **the instrument that judged is not the instrument that checks — and the checker earns its standing by catching planted frauds before it is trusted with a real one.***
