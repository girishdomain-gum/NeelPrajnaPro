# NOTE-NP-002 · Execution Plan §4 deliverable 5 — the H-007 comparison report
Author: developer (claude-code) · Sprint NP-S1 · 2026-07-30
Refs: `verdict` record `01KYSGQR3D8SYSVJFSF9M77CMY` (hypothesis `01KYSETR2C85MRRVWZCM8V0GMC`, lineage `h007_np_liquidity_sweep_v1_1`); `window_burn` `01KYSGQR6K1HHRT66R78BV6Z8Y`; the sealed AC-4 interpretation table in `configs/hypotheses/h007_np_liquidity_sweep_v1_1_prediction.yaml` (committed `2e938bd`, before this run); `ops/H07_evidenced_definition_annex_NP-S1.md` §4 (bespoke B1–B7); `ops/NP-ADR-008_APPENDIX-A_provenance_correction.md`; `docs/coordination/notes/NOTE-NP-001_engine_cannot_express_evidenced_stop_target.md`.

**AC-4 status: satisfied.** Every divergence below is named with its cause, using exactly the interpretation the YAML sealed before this run. Agreement is corroboration; divergence is reported as this sprint's most valuable output, per the boot doc. Results are never averaged — this is the real, drilled instrument's verdict, standing on its own.

## 1. AC-3 — one verdict, one burn, atomic
`EvidenceBattery.run()` produced exactly one `verdict` record (`01KYSGQR3D8SYSVJFSF9M77CMY`) and exactly one `window_burn` (`01KYSGQR6K1HHRT66R78BV6Z8Y`, lineage `h007_np_liquidity_sweep_v1_1`) on the designated UTC window `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)`, in the same code path (`battery.py`'s own invariant — a verdict without its burn is impossible by construction). Journal chain verified (`n_records=112`, `ok=True`) immediately after.

## 2. Top-line verdict
**Real Battery: FAIL.** **Bespoke recorded: FAIL** (five-gate failure — B1 pass, B3–B7 fail — per `ops/H07_evidenced_definition_annex_NP-S1.md` §4). **This is agreement at the top line** — two independent implementations of H-007's own definition (NP-ADR-008 Appendix A: the evidenced Python *is* H-007 as H-007 was always defined, not a degraded version of a richer original) both land on FAIL. Per the sealed interpretation, this corroborates that the direction+timing effect, whatever its sign, does not clear either instrument's bar.

The real Battery's own numbers show *why* it is a genuine, non-trivial FAIL, not a floor-failure or a data problem:
- `n_trades = 259` (from 325 SWEEP events the detector emitted on the real M5 bars — clearing `min_n=100` comfortably; `n_dropped_tail = 0`, so nothing was silently lost at the data tail).
- Net result is **positive**: mean net/trade `+1.5196` (total `+393.57`), mean gross/trade `+1.9296` — the direction+timing rule is not *losing* money on this window.
- But the one-sided t-test gives `stat=1.5822, p=0.05742` — **above even the plain 0.05 threshold before any deflation**, and far above the ratified deflated bar `p < 0.002632` (base 0.05 / 19 family trials). The 95% CI `[-0.3067, 3.3891]` includes zero.
- Per-fold means are inconsistent in sign: fold 1 `+3.19` (n=64), fold 2 `+3.79` (n=70), fold 3 `+0.49` (n=63), fold 4 `−1.72` (n=62) — a positive-then-fading-then-negative pattern across the walk-forward folds, consistent with the FAIL: whatever effect appears early in the window does not hold up later in it.

**Verdict: real Battery FAIL is a genuine statistical non-clearance, not an artifact of an unreasonably strict floor or a broken run.**

## 3. The 8-steps ↔ 6-criteria mapping (as sealed)
Reproduced from the YAML's own sealed table (part A) — see the file for the full version with per-row notes:

| Real Battery step | Bespoke counterpart |
|---|---|
| 1 type gate, 2 selftest gate, 3 window checks, 8 append verdict+burn | *(no bespoke analog — Kernel-only ledger/safety machinery)* |
| 4 splits (walk-forward, embargo) | B2 (OOS = final 40%, evaluated once) — **procedure, not a gate** (NP-ADR-008 M4) |
| 5 engine per fold TEST range | B1 (sample floors) — closest analog, but the judged trade set differs by construction (§4 below) |
| 6 statistics (pooled 1-sided t + bootstrap) | B3 (bootstrap CI) — closest structural analog; different family-correction machinery |
| 7 tri-state at deflated α | *(bespoke's own overall verdict)* |
| *(none)* | B4 (WFE), B5 (perturbation grid), B6 (drawdown-shuffle), B7 (cost-sensitivity margin) — **no real-Battery analog; simply unjudged by this run** |

**B4/B5/B6/B7 are not corroborated or refuted by this run.** Their bespoke recorded values (WFE fails the ≥0.5 late/early bound; the perturbation grid finds PF<1 in some variant; the drawdown-shuffle p95 exceeds 15R; net expectancy fails at 1.5× costs) stand as the bespoke instrument's own, uncontested-by-this-run findings. This is named explicitly, not glossed over: **the real Battery's FAIL and the bespoke's FAIL agree at the verdict level while testing substantially non-overlapping criteria.**

## 4. Every divergence, named with cause

| # | Divergence | Bespoke | Real Battery | Cause |
|---|---|---|---|---|
| 1 | Judged trade count | 324 (325 sweeps, 1 degenerate-geometry drop) | 259 | **M6, pre-registered**: the real Battery re-simulates from bars+events per fold, over TEST index ranges only, dropping trades that cannot open+close inside their block. `325 → 259` (79.7% retention) is the concrete instance of the pre-registered "materially smaller than 324." Arithmetic, not defect. |
| 2 | Trade rule | Stop = penetration extreme ±10 ticks; target = 1.5R; 1-second mid resolution; SL wins ties | No stop, no target; pure 12-bar time-stop; bar-level (open/high/low/close) resolution | **NOTE-NP-001**: `EventEngine`/`ExecutionSpec` supports only a single fixed stop/target per hypothesis, not a per-trade-variable one. Sealed in the YAML (part C) before this run, following the `h001` precedent (`stop_offset: null`) rather than a fabricated fixed approximation. |
| 3 | Cost model | 26 ticks round-trip (~$0.26/oz), approximately spread-only | `xauusd_retail_h07`, $0.41/oz (measured spread 0.24 + declared slippage/commission 2×0.085) | NP-ADR-008 Decision A (ratified) — the bespoke figure under-charges slippage/commission almost entirely; the real cost model is the more honest one. A **more conservative** cost basis than the bespoke run. |
| 4 | Statistical test | Bootstrap, 10,000 resamples, CI excludes 0 at 97.5% (Bonferroni, fixed `FAMILY_M=2`) | Pooled one-sided t-test (`stat=1.582, p=0.0574`) + seeded bootstrap CI, Bonferroni over the real family ledger (`FAMILY_M=19`) | Different machinery entirely — the bespoke fixes its own multiplicity burden at a hand-set `FAMILY_M=2`; the real Battery deflates against the honestly-counted 19-trial family ledger (NP-ADR-008, DEVQ-015). The real Battery's bar is *harder to clear* (α 0.05/19 = 0.00263 vs the bespoke's own 97.5%/`m=2` framing). |
| 5 | Validation topology | Single chronological 60/40 IS/OOS split, OOS evaluated once (B2) | 4-fold walk-forward, embargo ≥ hold_bars+1, TEST ranges pooled across all folds | Kernel-native walk-forward (`ARCH-006 §3`) vs the bespoke's single-split design — not a defect on either side, a different cross-validation topology by design. |
| 6 | Pool-engine mechanics (within H-007 itself) | Pool level = frozen average of member pivots (v1.0/T3 absorbed-pool-engine text) | Pool level = frozen max(HIGH)/min(LOW) of members (v1.1, matching the evidenced `np_feature_service.py`) | **Genuinely within H-007's own lineage** — NP-ADR-008 Appendix A part A.2 identifies this as one of only two divergences (with #7) that are *not* cross-hypothesis. The v1.1 detector matches the evidenced Python exactly; this is a real MQL5-vs-Python difference inside H-007's own pool engine. |
| 7 | Member-window depth | 200-bar recent-pivot window (event-driven) | 200-bar recent-pivot window, identical | **No divergence** — the real detector matches the evidenced parameter exactly (verified in SNP-S1-03's fixture-vs-oracle check). Listed for completeness against the annex's own divergence #4 framing, which is now understood (Appendix A) to describe a difference between the *evidenced Python* and *T3's absorbed-pool-engine defaults* (500 H1 bars) — not between v1.0 and v1.1 as sealed here. |

**Divergences 1–5 above are what this sprint's run adds beyond NP-ADR-008's own M1–M7 catalogue** (M1–M7 concern the *definition* and its documentation; 1–5 here concern what changes when that definition is actually *run* through the real, drilled Kernel instrument). Divergence 6 is the one substantive definitional gap that survives Appendix A's cross-hypothesis correction — the pool-level formula genuinely differs between the historical MQL5 pool engine and the evidenced Python, within H-007's own lineage.

## 5. What this run does NOT speak to
Per NP-ADR-008 §2.1 (verbatim, carried into every derived artifact): **no verdict under v1.1 validates, corroborates, or speaks to the historical T3/MSS gate** — and per Appendix A, that gate is now understood to be H-008's, not H-007's at all. This FAIL is a finding about H-007 (the equal-high/low sweep + reclose hypothesis, as H-007 was always defined) — it says nothing about H-008's 1H-sweep→MSS→FVG→tap sequence, which remains an unjudged, counted-only entry (`np_h08_sweep_mss_fvg_tap_ny_open`, family `xauusd/neelprajna`) pending its own future registration and evidence, per Appendix A.3.

The **E2 existence claim** (hypothesis `01KYSETR3VACRBCWN9QYRRX6DW`) is registered and counted but **not judged** — N2 (block-resampling) null machinery does not exist in this Kernel yet (NP-ADR-008 §6). This run says nothing about whether SWEEP events concentrate at pool levels beyond chance arrangement; that question awaits N2 machinery, exactly as sealed at registration.

## 6. Conclusion
**AC-4 satisfied.** Agreement (top-line FAIL) and divergence (five distinct, causally-named mechanical differences, plus one genuine within-H-007 definitional difference) are both present and both named. Per the boot doc's own framing, divergence is the more valuable output here: it shows that even where two independent instruments agree on the headline verdict, they arrive there through substantially different machinery, testing substantially non-overlapping criteria (B4–B7 remain entirely unaddressed by the real Battery) — a fact any future reader must know before treating "H-007: FAIL, corroborated twice" as a stronger claim than the evidence actually supports.

---
## 7. REV-MANDATED SCOPE NARROWING (appended 2026-07-30 — Chief Scientist REV, Owner-relayed; P5 append, §§1–6 unedited)

The Chief Scientist approved NP-S1 at 8.8/10 **with one qualification that must remain explicit in all downstream documents**: this report must not imply that the two execution strategies were equivalent. The comparison is **same detector definition + different execution rules**, never same-detector-same-execution.

**The canonical claim, to be quoted rather than paraphrased wherever this result is cited:**

> **Under two independently implemented execution frameworks using different exit mechanics, neither framework produced statistically significant evidence supporting the hypothesis over the designated window.**

**Preferred phrasing in place of "both instruments agree":**

> **Both evaluation frameworks independently failed to reach their predefined acceptance criteria, although they differed materially in execution model and intermediate behavior.**

**What this narrowing forbids:** any statement that NP-S1 established equivalence between the bespoke execution strategy and the Battery execution strategy. It did not. It established only that each framework, under its own execution model, failed to find statistically significant support for the registered hypothesis over the burned window — with opposite expectancy signs, different exit mechanics, and four bespoke criteria never evaluated at all.

**Chief Scientist's added structural finding, recorded here and in the journal:** *executable implementation details were distributed across code rather than fully represented in normative specifications; future detector specifications should be sufficiently complete to enable an independent reimplementation without consulting source code.* Process finding, no individual fault — independently converged with Appendix B.9's proposed standing rule.
