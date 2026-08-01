# NP-ADR-0ZZ — H-07 Detector Definition §5 **v1.1**: the evidenced definition, sealed

> **SUPERSEDED 2026-07-30** by `ops\NP-ADR-H07_definition_v1.1_draft_v2.0.md`, which
> was ratified as **NP-ADR-008** on 2026-07-30.
> Retained for provenance only — never ratified, never to be cited.
> This file keeps the placeholder `0ZZ` permanently and is assigned no ADR number
> (corrected Rule A, Architect ruling 2026-07-31, F-29).
> Banner added 2026-07-31 by the Architect. The file below is otherwise unaltered.

*WORKING RECORD — Architect-role draft, 2026-07-30, for Chief Scientist review → Owner ratification (Constitution §7.3, and §5's own "changes = v1.1 by NP-ADR, never edits"). **Number 0ZZ unassigned** pending registry check (NP-D-006). No normative document edited by this draft.*

**Attribution (per the proposed standard):** *Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Evidence base, all committed:** `ops\DEVQ-01_NP-S1.md` (Add. A–B) · `ops\H07_evidenced_definition_annex_NP-S1.md` (§1–§8, Add. A–C) · `docs\coordination\inbox\CLOSED\DEVQ-NP-001/002` · `docs\coordination\sessions\SNP-S1-01/02` · mainline `cdbb71c`.

---

## 1. The decision requested

Seal **§5 v1.1** as the documented detector definition embodied by the H-07 324-trade population, and rule the six consequential questions in §6 so Sprint NP-S1 can resume. **§5 v1.0 remains frozen and unedited forever.**

## 2. The provenance chain (source-verified on both sides)

1. **§5 v1.0 faithfully documents the historical MQL5 gate** `T3_SweepFVGGate.mqh` v2.1 — H1/M1, `PoolTol = 0.15×ATR14`, pool level = average of member pivots, mandatory MSS stage. Verified from source independently by the Developer session (commit `309843e`) and by a separate verification workflow.
2. **The divergence exists entirely within the Python lineage** — `np_feature_service.py` + `np_probability_engine.py`, the stack retired from evidentiary service by NP-D-001. The MQL5 path never executed for this population.
3. **Therefore v1.1 is not a correction of v1.0. It is the first authoritative documentation of the detector definition that actually produced the 324-trade evidence population.** *(Framing adopted verbatim from the Chief Scientist review, Owner-endorsed.)*

## 3. §5 v1.1 — THE SEALED DEFINITION (normative text on ratification)

**Lineage label:** `neelprajna.liquidity_sweep.v1_1` (bespoke-M5 lineage). **Implementation identity:** `np_feature_service.py` sha256 `1a0b5d9f…a6c0` · `np_probability_engine.py` sha256 `a9b75aeb…d2ff` · population `h07_trades.parquet` sha256 `0f242e2f…0133`. Values are hard-coded at the call site `build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2)` on 300 s bars — not CLI defaults.

**Observation space.** XAUUSD retail feed, Vantage Markets MT5, broker-tier · clean ticks only (bid>0, ask>0) · price = bid/ask **mid** · TICK_SIZE 0.01 · timestamps stored in broker server time (UTC+3, DST-clean across the span), **converted to int64 ns UTC at the adapter boundary**.

**Observed events (closed bars only).**
- **POOL_FORMED** — on each newly confirmed pivot: same-side pivots within the last **200 bars** whose price lies within **pool_tol = 30.0 ticks fixed**; ≥2 members required; level = **max of member prices (HIGH side) / min (LOW side)**, frozen at formation; no new pool within pool_tol of an active same-side pool; pool active until swept or invalidated.
- **SWEEP** — wick penetrates an active pool level by ≥ **min_pen = 5.0 ticks**; if the same bar closes back on the defended side → sweep (reclose_bars 0); else a reclose window of **2 bars** — closing back inside within it → sweep (max penetration retained); failing to → **invalidation**, pool resolved, no event.
- **There is no third event.** REVERSAL_CONFIRMED / MSS does not exist in this definition. The chain is **POOL_FORMED → SWEEP**, terminal.

**Frozen parameters.** bar timeframe **300 s (M5), single timeframe** · pivot_k **3** · member window **200 bars** · pool_tol **30.0 ticks (fixed, non-adaptive)** · min_pen **5.0 ticks** · reclose_window **2 bars**.

**Knowability / anti-repaint (v1.1's own terms — AC-2's normative target).** A pivot at bar *i* is confirmed only at bar *i+k*; a pool is emitted at its confirmation bar, never backdated; a sweep is emitted at the bar whose close resolves it (0–2 bars after first penetration). Every emission carries `ts ≥` the timestamp of the last input bar required to determine it, and no emission changes retroactively under incremental feeding.

**Prediction layer (frozen 2026-07-10, playbook — excluded from the existence claim).** SELL after HIGH-pool sweep / BUY after LOW-pool sweep · entry = mid at open of the bar after the sweep bar · stop = penetration extreme ±10 ticks · target 1.5R · time stop 12 bars · 1-second mid resolution, SL wins ties · costs 26 ticks round-trip (`xauusd_retail_h07`).

**Designated coverage (Owner-confirmed).** Broker EEST 2026-04-21 01:00:00 → 2026-07-10 17:33:00 = UTC **[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)**, half-open, TRAINING, burned. Population: 324 trades from 325 sweeps (one degenerate-geometry drop, risk < 5 ticks).

## 4. Why v1.1 does not inherit v1.0's unenforceable clauses

v1.0 requires the exec bar to **open inside** the defended side and excludes gap-through opens. The evidenced code reads `h, l, c` only and **never the bar open**, so both clauses are *unenforceable* in this lineage — not merely unimplemented. v1.1 therefore states neither, and the divergence is recorded rather than papered over.

## 5. RECOMMENDATIONS on the six questions *(Architect recommends; Owner rules)*

**Q1 · E2 restatement — RECOMMEND: restate the existence claim one link down the chain.**
v1.0's E2 content ("does REVERSAL_CONFIRMED follow SWEEP beyond chance timing?") is unjudgeable here. **E2-v1.1:** *does SWEEP follow POOL_FORMED beyond chance arrangement?* — i.e. do penetration-and-reclose events concentrate at previously frozen equal-high/low levels more than a null preserving session and volatility character but destroying the cross-bar level relationship. This keeps E2's form (arrangement, not base rate — the definition trap still applies: pool_tol and min_pen buy the event rate), keeps N2 as the null design, and remains judged only when null machinery certifies. Registered and counted now.

**Q2 · α-budget pricing — RECOMMEND: price by registrations, not by hypothesis names; and correct the family count to 19.**
QRF-ADR-011 is explicit: *registration spends the attempt.* NP-S1 registers **two** claims for H-07 (prediction + existence) plus **17** counted-only entries = **19 sealed registrations**, not 18. J-029's arithmetic (0.05 ÷ 18 → p < 0.0028) treated H-07's dual registration as one trial. Corrected: **0.05 ÷ 19 → p < 0.00263**. This is a tightening, never a loosening, and deflation recomputes against total family trials at every judgment regardless. **Owner confirmation requested explicitly, since J-029's number is on the record.**

**Q3 · Detector implementation target — RECOMMEND: NP-S1 builds the v1.1 detector only.**
`liquidity_sweep.py` implements v1.1's POOL_FORMED and SWEEP exactly, because that is the definition that produced the population being judged. A v1.0-faithful (T3) detector is **deferred to NP-S2+**, where fresh data exists to judge it honestly. Building both now doubles the work and judges one of them against no population.

**Q4 · Anti-repaint — RECOMMEND: adopt §3's knowability paragraph as AC-2's normative target**, property-tested by incremental feeding with the assertion that emissions never change retroactively.

**Q5 · Which population deliverable 4 judges — RECOMMEND Option C (the Owner's ruling, plus honest naming).**
Judge **the 324** under v1.1 — this is the Owner's ruling already ("the 324-trade population shall reference §5 v1.1") — and register the claims under the lineage label `neelprajna.liquidity_sweep.v1_1`, **not** as unqualified "H-07". Reasons: (i) AC-3/AC-4 require one population judged by two instruments; Option A would compare two instruments over two *different* populations, destroying the comparison the sprint exists to make; (ii) Option A additionally requires a **supplementary Owner designation** for a v1.0 detector's pool_lookback pre-roll (up to 500 H1 bars ≈ 21 days, cap 2000 ≈ 83 days) of market time the current designation does not cover — a P8 hard precondition; (iii) naming discipline keeps "H-07 proper" attached to the real EA gate, so the eventual T3 judgment on fresh OOS data is not pre-empted. **Scope honesty to be written into the verdict:** this verdict speaks to the bespoke-M5 lineage, *not* to the live EA's T3 gate behaviour.

**Q6 · The recorded bespoke verdict is a FIVE-gate FAIL, not "FAIL on cost sensitivity" — RECOMMEND: seal the corrected characterization before the run.**
*(New; found by the Developer session, verified independently in the annex.)* `Stage4_EvidenceReport_H07.json` shows **B1 pass** (194/130) and **B3, B4, B5, B6, B7 all `pass:false`**. The "cost sensitivity" phrasing in Execution Plan §4/§5 appears to derive from the separate descriptive `CostThreshold_Report`, which disclaims being a verdict. **Execution Plan §4 is frozen by the GO and must not be edited**; the correction lives here and in the comparison report's sealed interpretation table, so AC-4 maps against what was actually recorded.

## 6. Consequences for the sprint (nothing here reopens a frozen instruction)

- **Deliverable 1** — v1.1 detector + planted/clean cases (AC-1 unchanged).
- **Deliverable 3** — two registrations, both priced at birth, citing **v1.1** and cost model `xauusd_retail_h07`.
- **Deliverable 4 / AC-3** — one Battery run on the 324 over the designated window; verdict + burn atomic. The burn records the UTC half-open interval in §3.
- **Deliverable 5 / AC-4** — the comparison maps the real Battery against **B1 pass / B3–B7 fail**. **Open item to pin before sealing the mapping:** the Battery is described as nine steps while `battery.py` presents eight; the Developer resolves this by inspection and the mapping is sealed in the YAML *before* the run. If doc and code genuinely differ, that is a finding (code is authoritative for what ran; the document for what was claimed).
- **Deliverable 6 / AC-5** — 17 counted-only entries; family trial count **19**.

## 7. What does not change

§5 v1.0 (frozen, unedited) · the designated window and its TRAINING burn · cost model name · claim form E2 and null design N2 · Constitution §6 · the Twelve Principles · the wall · the Publication Boundary · write authority · Execution Plan §4's frozen instruction text · all history.

## 8. Findings recorded by this ADR

1. **Execution Plan §4/§5 mischaracterize the bespoke verdict** (single-gate vs five-gate FAIL) — against the Architect; not editable (frozen), corrected here.
2. **The M5 basis was visible in-repo before the sprint** — the Research Console mockup's scope chip reads "XAUUSD·M5·London·trend" — and was never reconciled against §5's frozen M1. J-032's alignment pass checked sprint pointers, not detector parameters. **Standing rule proposed:** alignment passes check parameter consistency between a sealed definition and any in-repo artifact describing the same detector, not only sprint pointers.
3. **`scripts/gen_state.py` targets a Gen-1 artifact** (`docs/handover/AI_PROJECT_STATE.md`) that does not exist in this estate; the Developer correctly deferred rather than regenerate it. **Needs a ruling** (WO-A scope): retire the script, or re-point it at Execution Plan §0.

## 9. Ratification wording (type one)

- **APPROVE:** *"NP-ADR H-07 §5 v1.1 is RATIFIED as written, including E2 restated as POOL→SWEEP arrangement, family trial count corrected to 19 (p < 0.00263), the v1.1-only detector target, Option C with lineage label `neelprajna.liquidity_sweep.v1_1`, and the five-gate FAIL characterization. §5 v1.0 remains frozen. NP-S1 registration is unblocked against v1.1."*
- **APPROVE WITH VARIATION:** as above, naming the variation (e.g. *"…trial count stays 18"* or *"…Option A, and I will designate the pre-roll span separately"*).
- **REJECT / RETURN:** *"Not ratified — [reason]. NP-S1 remains halted."*

---
*Anchor: **v1.0 says what the gate was; v1.1 says what the evidence was made by — and only the second may be judged on this population.***
