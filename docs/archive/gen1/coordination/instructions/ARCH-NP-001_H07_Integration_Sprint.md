# ARCH-NP-001 — First Integration Sprint: H-07 into the Real Kernel

| | |
|---|---|
| **Type** | Sprint instruction (Architect → Developer) · **Status** | DRAFT — sealed on Owner Go |
| **Date** | 2026-07-29 · **Author** | Fable (Architect) |
| **Governed by** | Constitution v2.0 · Scientific Model v2.0 · Platform & Integration Architecture v2.0 |
| **Sprint rhythm** | ARCH → Developer sessions (fresh session, worktree) → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → handover rewrite |

## 0. Preconditions (block start; none may be assumed)

- [ ] **Owner:** window designation typed for the market time underlying H-07's 324-trade population (TRAINING or EXPLORATION; it is seen data and cannot be VIRGIN).
- [ ] **Owner:** α-budget ceiling set for the `neelprajna` family.
- [ ] **Owner ruling (REV F-13):** Auto-Adopt confirmed `NONE` on the real account, or exposure accepted on the record. (Out of this sprint's scope but a standing safety ruling; recorded in GO.)
- [ ] **Architect+Owner:** cost-model reconciliation ruled — one `configs/venues.yaml` entry (proposed name: `xauusd_retail_np_v1`) reconciling QRF's $0.47/oz round-trip with NeelPrajna's 26-tick figure; definition frozen once cited.

## 1. Scope (H-07 only)

Port **H-07 (equal-high/low sweep reversal)** — NeelPrajna's most evidence-rich hypothesis (324 trades; Stage-3 feature stability PASS on record) — into the real Kernel and judge it with the real EvidenceBattery.

**Deliverables**
1. `qrf/trading/concepts/neelprajna/liquidity_sweep.py` — detector implementing the standard Detector contract (EventFrame column spec; anti-hindsight invariant property-tested), ported from `LiquiditySweepGate.mqh` semantics via `np_feature_service.py` as reference only (it is not normative).
2. `planted_cases()` — planted-truth and clean-control calibration cases for the detector (Architecture §7.1). The detector must catch every planted fraud and stay silent on clean data before step 4 runs.
3. `configs/hypotheses/h007_np_liquidity_sweep.yaml` — sealed registration: claim, scope (full 12-layer Observation Space), n-floor, success criteria, placebo type, cost model name. Registration spends the attempt (TrialCountLedger).
4. One real `EvidenceBattery.run()` over the designated window against the same trade population NeelPrajna's bespoke B1–B7 battery already judged (its recorded result: FAIL on cost sensitivity).
5. Comparison report: the real Battery's nine steps vs the bespoke B1–B7 result, gate by gate, divergences named.
6. Founding-set trial accounting: register the remaining 17 founding hypotheses as counted attempts (no detectors, no runs — ledger entries only), per Scientific Model §8.

## 2. Acceptance criteria (falsifiable, sealed)

- AC-1: Detector passes all planted-truth cases and emits zero events on all clean controls.
- AC-2: Anti-hindsight property test passes under incremental feeds (no retroactive emission changes).
- AC-3: Exactly one Battery run writes exactly one verdict + one window burn, atomically, on the designated window.
- AC-4: The gate-by-gate comparison report exists and every divergence between real-Battery and bespoke-battery results is named with a stated cause. **Agreement (both FAIL on cost) is corroboration; divergence is the sprint's most valuable output — either outcome satisfies AC-4.** If they diverge, the more rigorously verified instrument's verdict stands; results are never averaged.
- AC-5: TrialCountLedger shows ≥18 counted attempts for the family after step 6.
- AC-6: IVF re-derives the verdict from normative texts after its own drill (planted fraud first), independently of the Developer's code.

## 3. Non-goals (violations are findings)

No change to live execution, TradeManager, MoneyManager, NPSU, or the real-account gates. No porting of hypotheses beyond H-07 (registration-only entries excepted, step 6). No console work (the Console remains DESIGNED until this migration exists — spec v1.3 precondition). No edits to `ivf/**`, the ledger internals, or any normative document.

## 4. DEVQ triggers (ask, do not assume)

Ambiguity in MQL5→Python sweep semantics; any EventFrame field the source logic cannot honestly populate; any mismatch between the CSV export shape and the adapter's expectations; any case where the designated window and the 324-trade population disagree; anything the cost-model ruling leaves undefined. Silence binds no one; assumptions in place of answers are findings.

## 5. What GO means

On Owner GO: retro recorded; handover rewritten; the follow-on decision — whether the remaining 17 hypotheses follow the same path — is scheduled as the Owner's ruling informed by AC-4's report; and the **R6 long run** (3–6 months real-tick with withheld OOS) is proposed as the next sprint (REV F-16 sequencing).

---
*Anchor: **one hypothesis, judged twice, by two instruments — and the divergence, if any, is the point.***

> **Renumbering note (2026-07-29, later):** originally issued as "ARCH-011"; renumbered ARCH-NP-001 after the Architect discovered GEN2_EXECUTION_ROADMAP.md already reserves ARCH-011 for Gen-2 Sprint 1. Tallied as a finding against the Architect (numbering collision, the F-12 species). Namespacing per Constitution v2.0 §5.4 now applies to ARCH numbers as well as ADRs.
