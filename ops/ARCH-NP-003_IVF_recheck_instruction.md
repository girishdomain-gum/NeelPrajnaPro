# ARCH-NP-003 — IVF RE-CHECK: AC-6 §3.2 and §3.3 against the pinned mechanics
*Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. Sealed instruction for the IVF / Validator. **Scope: two items only.** Everything else in `IVF_NP-S1_AC6.md` stands as reported and is not re-run.*

---

## 0. What is and is not being re-opened

**Standing, not re-run:** the drill (6/6 caught, control clean) · the entire §2 chain re-derivation (all 15 figures to 1e-9, all 8 numbered checks) · §3.1 undeflated-alpha survival · §3.4 bar-build honesty. **That work is accepted. Do not repeat it.**

**Re-checked here:** §3.2 (verbatim wording) and §3.3 (SWEEP recount) — the two RED lines, now that the Architect has dispositioned one and pinned the other.

**Your RED was correct and is recorded as such.** Neither item is being argued away; one is being ruled on, the other is being made checkable.

## 1. §3.2 — re-check as a substance test, and say so

`ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md` §B.7 rules that the registrations are **accepted as-is**: substance present, bytes not, re-registration refused because it would orphan the verdict from its hypothesis and spend two further family trials.

**Re-check accordingly, and report both results separately:**
- **substance test** — does each of the three non-equivalence propositions appear, in meaning, in `outcome_interpretations` or `thesis` of both registrations? Report PASS/FAIL per statement per registration.
- **byte test** — restate the byte result you already found (0 of 3), **as a recorded deviation, not a failure**, citing B.7.

**If the substance test fails for any statement, that is a genuine RED and B.7 does not save it** — B.7 accepts a wording deviation, never a missing proposition.

## 2. §3.3 — re-derive from the pinned text

Re-run the recount using **Appendix B §B.1–B.5 as the definition**, and nothing else. `np_feature_service.py` and `np_probability_engine.py` remain unopenable.

Five points are now pinned; check each against what your first run assumed, and **report which of your three disclosed choices changed**:
1. **B.1** strict-extremum pivots, both sides emittable at one bar, confirmed at *i+k*.
2. **B.2** membership **anchored on the newest pivot** — distance to *r* alone, never pairwise or transitive; *r* appended only after the search.
3. **B.3** level = max/min of members, frozen; suppression **entire** if an *active* same-side pool lies within `pool_tol` of the computed level; resolved pools do not suppress.
4. **B.4** per bar: sweep/invalidation checks **first**, pivot→pool processing **second**; a pool cannot form and be swept on the same bar.
5. **B.5** reclose is testable at bars *p*, *p+1* **and *p+2***; invalidation fires at the first bar with `i − p ≥ 2` and no reclose. **This is the most easily mis-read clause and the strongest single candidate for the gap.**

**Target: 3,099 pivots · 465 pools · 325 sweeps** (B.6). Report all three, not only the sweep count — the Architect's comparison against the Stage-3 report localizes the divergence to **pool formation** (pivots already agreed exactly, 3,099 = 3,099; pools differed by 11; sweeps by 6). If you still diverge, **the pool count is the diagnostic that matters**.

**If you still diverge after B.1–B.5:** that is a real finding and outranks the convenience of closing AC-6. Report the first bar index at which your pool set differs from what the pinned rules should produce, and which specific clause you believe is still under-specified. **Do not tune to reach 325.** A number reached by adjustment is worth less than a disagreement reported honestly — that is the whole reason this check exists.

## 3. Read B.8 before concluding

Appendix B's mechanics were written by the Architect **from the evidenced implementation**. A match therefore demonstrates **text-code fidelity, not code correctness** — weaker than the independence AC-6 was reaching for, and inherent to a documentary definition. **State this limitation in your conclusion.** Do not report a match as independent confirmation of the detector.

## 4. Output

Append to `ivf/reports/IVF_NP-S1_AC6.md` as **§7 — Re-check under ARCH-NP-003** (append-only; do not edit the original report — P5). Restate the overall verdict at the end: **GREEN only if §3.2's substance test passes and §3.3 reproduces 3,099 / 465 / 325.** Any other outcome stays RED, named plainly, and HC does not begin.

## 5. Non-goals

No code under `qrf/**`. No registrations, runs, burns, or normative-document edits. **No Battery re-run** — the window is burned and the refusal must hold. `ivf/` never imports `qrf/`.

---
*Anchor: **the first check found a gap; this one asks whether the gap was in the detector or only in the sentence describing it.***
