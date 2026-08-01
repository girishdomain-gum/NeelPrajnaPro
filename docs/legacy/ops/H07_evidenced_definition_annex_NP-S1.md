# H-07 Evidenced Definition — Annex for the §5 v1.1 ADR
*WORKING RECORD ONLY — not a normative document. Written 2026-07-30 on Owner approval. Purpose: ready-to-lift material for the Architect's v1.1 re-seal ADR. Framing per Chief Scientist review, Owner-endorsed: **v1.1 is not a correction of v1.0; it is the first authoritative documentation of the detector definition embodied by the evidence.** Every statement below was read from source, not inferred.*

---

## 1. Implementation identity (the code that produced the population)

| Artifact | Path | SHA-256 |
|---|---|---|
| Feature engine (Stage 3) | `F:\NeelPrajna\np_feature_service.py` v1.0 | `1a0b5d9f1971171081d058466f0177a07f06b5eb1b96d4646f7db69cac38a6c0` |
| Probability engine (Stage 4) | `F:\NeelPrajna\np_probability_engine.py` v1.0 | `a9b75aebf142c433eec915d5a37b97b23bf1bb77fabfe2471e6b1bba55dfd2ff` |
| 324-trade population | `F:\NeelPrajna\Validation\Stage4\h07_trades.parquet` | `0f242e2f6a89836fdb9e60e3e7b2b803b04688af7e59c01fd707fd8ac8de0133` |

Stage 4 invokes Stage 3 as a library with hard-coded arguments `build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2)` on 300s bars — the evidenced values are therefore fixed in code, not merely CLI defaults. Trade rule frozen 2026-07-10 per the Stage 4 module docstring; pre-registered seed **20260710**, no reroll. Reports: `Stage3_FeatureValidationReport.*` (2026-07-10T18:08:42Z, PASS) · `Stage4_EvidenceReport_H07.json` (2026-07-10T18:19:13Z, verdict FAIL). Per-tick input identities: 60 SHA-stamped daily files in `Stage2_DataValidationReport.*` (overall PASS).

## 2. Evidenced observation-layer definition (Stage 3)

**Data basis.** Vantage Markets MT5 XAUUSD ticks (`clean` only, bid>0, ask>0), price = bid/ask **mid**; TICK_SIZE 0.01. Timestamps: broker server time (UTC+3 this span) as epoch integers.

**F-BAR.** OHLC bars of the mid at **300 s** (M5), single timeframe. No anchor/exec pair.

**F-SWING.** k-bar pivot highs/lows, **k = 3**: bar i is a pivot HIGH iff high[i] strictly exceeds the k bars each side (symmetric for LOW). Anti-lookahead: a pivot at bar i is **confirmed only at bar i+k**.

**F-POOL (POOL_FORMED).** On each newly confirmed pivot: candidate mates = same-side pivots within the last **200 bars** whose price lies within **pool_tol = 30.0 ticks**. If ≥1 mate (i.e., ≥2 members total), a pool forms with level = **max of member prices (HIGH side) / min (LOW side)** — the defended extreme, not the average. Duplicate suppression: no new pool within pool_tol of an active same-side pool. Pool stays active until swept or invalidated.

**F-SWEEP (SWEEP).** Against each active pool per bar: penetration = wick beyond level by ≥ **min_pen = 5.0 ticks**. If the same bar closes back on the original side → single-bar sweep (reclose_bars 0). Otherwise a reclose window opens: if any bar within **reclose_window = 2 bars** of first penetration closes back inside → sweep (max penetration tracked); if not → **invalidation** (pool resolved, no event). Recorded per sweep: bar_ts, side (SELL for HIGH-pool, BUY for LOW-pool), pool_price, pool_members, penetration_ticks, close_back_ticks, reclose_bars, pool_age_bars.

**There is no third event.** REVERSAL_CONFIRMED / MSS does not exist in this pipeline. The evidenced chain is POOL_FORMED → SWEEP, full stop.

## 3. Evidenced prediction-layer rule (Stage 4, frozen 2026-07-10)

- **Direction:** SELL after HIGH-pool sweep, BUY after LOW-pool sweep.
- **Entry:** mid at the open of the bar **after** the sweep bar (bar_ts + 300 s); skipped if no tick within one bar of the entry time.
- **Stop:** penetration extreme ± **10 ticks** buffer. Degenerate-geometry skip if risk < 5 ticks.
- **Target:** **1.5R**. **Time stop:** **12 bars (1 h)**, exit at mid.
- **Resolution:** 1-second mid series; SL and TP in the same second → **SL** (conservative tie rule).
- **Costs:** **26 ticks** round-trip per trade (cost_r = 26×TICK_SIZE / risk).

## 4. Evidenced battery constants (Stage 4, pre-registered)

B1 floors ≥100 IS and ≥100 OOS · B2 OOS = final **40%** chronologically, evaluated once · B3 bootstrap (10,000 resamples) CI of mean net R excludes 0 on OOS at **97.5%** (Bonferroni, family m=2, α_family 0.05) · B4 four sequential folds, WFE = late/early ≥ **0.5**, both positive · B5 ±10% perturbation grid over {pool_tol, min_pen, stop buffer, R-mult}, PF ≥ 1.0 in every variant, full sample · B6 1,000 order-shuffles, p95 max drawdown ≤ **15R** on OOS · B7 net expectancy > 0 at **1.5× costs (39 ticks)** on OOS. Seed 20260710 throughout. Recorded outcome on this population: B1 pass (194/130); B3–B7 fail; **verdict FAIL**.

## 5. The seven divergences from §5 v1.0 (Chief Scientist classifications retained)

| # | Dimension | §5 v1.0 (MQL5-derived, frozen) | Evidenced (this population) | Class |
|---|---|---|---|---|
| 1 | Timeframes | H1 anchor + M1 exec | single 300s (M5) mid-bar stream | detector definition change |
| 2 | Pool tolerance | 0.15×ATR14(H1), adaptive | 30.0 ticks fixed; plus min_pen 5.0t (absent in v1.0) | detector philosophy change |
| 3 | Pool level | average of member pivots, frozen | max (HIGH) / min (LOW) of members | mathematical definition change |
| 4 | Pool memory | pool_lookback 500 H1 bars (cap 2000), rebuilt per anchor bar | 200-bar recent-pivot window, event-driven | parameter-level, part of detector identity |
| 5 | Sweep semantics | open inside + wick through + close back, single closed bar; gap-throughs excluded | penetration ≥5t; reclose within 2 bars else invalidation; no open-inside condition | event definition change |
| 6 | Third event | REVERSAL_CONFIRMED: close beyond pre-sweep swing (swing_lookback 10) within mss_max_bars 30 | **does not exist**; entry is simply next bar after sweep | fundamental causal model change |
| 7 | Code lineage | `T3_SweepFVGGate.mqh` v2.1 pool engine (InpT3_* symbols) | Python pipeline above; MQL5 path never executed | provenance change |

## 6. Designated coverage of the population (Owner-confirmed 2026-07-30)

**Vantage server time (UTC+3): 2026-04-21 01:00:00 → 2026-07-10 17:33:00** (UTC: 2026-04-20 22:00:00 → 2026-07-10 14:33:00). TRAINING tier per J-030 — burned; in-sample; corroborative, never confirmatory. Population: 324 trades (160 BUY / 164 SELL), entries 2026-04-21 08:55 → 2026-07-10 06:05 server, all on 300s boundaries; 11 weekend gaps, daily 00:00–01:00 maintenance break, one intraday >300s tick gap on 2026-07-10 (Stage 2, PASS).

## 7. Questions the v1.1 ADR must answer (flagged, not decided here)

1. **E2 restatement.** v1.0's E2 content ("does REVERSAL_CONFIRMED follow SWEEP beyond chance timing?") is unjudgeable on a population with no REVERSAL_CONFIRMED events. Restate the existence claim against the POOL→SWEEP chain (and its N2 null design), or rule its disposition.
2. **α-budget pricing.** If v1.1 is a different hypothesis (per review), rule whether it prices as one trial or two against the family α-budget 0.05 (per-claim bar currently p < 0.0028 at 18 trials — recomputed at every judgment).
3. **Detector target.** §4 deliverable 1 ("exactly §5's events") must resolve to **v1.1's** events for the NP-S1 detector, so the Battery judges the phenomenon that actually produced the population.
4. **Anti-repaint note.** v1.0's closed-bars-only/anti-repaint language maps to v1.1's pivot confirmation lag (k bars) and close-based reclose test; the ADR should state the anti-hindsight property in v1.1's own terms so AC-2's property test has a normative target.
5. **Which population deliverable 4 judges** *(added Addendum B, from DEVQ-NP-001)*: the Developer's Options **A** (fresh §5-v1.0-faithful population over the same window) / **B-as-ruled** (judge the 324 under documented v1.1) / **C** (split: v1.0 stays H-07 proper; the 324 registered as an explicitly-labelled bespoke-M5 artifact) — **with the hard precondition that Option A requires a supplementary Owner designation for the §5 pool_lookback pre-roll** (up to 500 H1 bars ≈ 21 days before the designated start; cap 2000 ≈ 83 days), since a §5 detector would *see* market time the current designation does not cover (P8).

## 8. Recommendation to the Architect (Owner-directed inclusion; for architecture review, NOT part of the current re-seal)

**Proposed ADR: immutable detector identities and machine-verifiable definition fingerprints** (origin: Chief Scientist review 2026-07-30; endorsed by Owner as a recommendation).

- **Identity model:** detector identity = **family + definition version + immutable fingerprint** — never the bare name ("H07"). Evidence belongs to a definition and fingerprint, not to a family.
- **Fingerprint:** SHA-256 over a canonical representation of {detector family · definition version · complete event graph · feature definitions · parameter names+values · execution assumptions · prediction assumptions · implementation identity · source file identities}.
- **Manifest:** a machine-readable detector manifest as the single authoritative technical description (family, version, fingerprint, event sequence, timeframe architecture, implementation modules, prediction modules, registration identifiers). Documentation explains the detector; the manifest defines it; the implementation realizes it; the Battery verifies it; the ledger references it.
- **Enforcement points:** fingerprint carried in detector registration · detector manifest · Stage-3-style exports · Stage-4-style reports · Battery preflight · ledger entries. **The Battery refuses execution whenever population fingerprint ≠ registered fingerprint.**
- **Rationale:** converts this DEVQ's manual forensic investigation into an automatic hard stop; eliminates the provenance-ambiguity class entirely. The platform must version event definitions, detector semantics, execution assumptions, and implementation lineage — not only numeric parameters.

---
*Cross-reference: `ops\DEVQ-01_NP-S1.md` (question, evidence trail, review, Owner ruling, status). Both files are working records; per the F-22 standing rule the next commit stages `docs` and `ops` together.*

---
*Append below this line only.*

## Addendum A · 2026-07-30 · v1.0 fidelity independently confirmed against MQL5 source — provenance chain closed

An independent verification session (Claude Code, workflow `np-s1-h07-verify`) read **`T3_SweepFVGGate.mqh` directly** and confirmed that **§5 v1.0 faithfully seals the original MQL5 gate**: H1/M1 architecture · `PoolTol = 0.15×ATR14` · pool level = average of member pivots · mandatory MSS = REVERSAL_CONFIRMED stage — all matching v1.0's text. This annex's §1–§5 had established the Python side of the divergence from source; the MQL5 side was previously inferred from the Execution Plan's provenance note. Both sides are now source-verified.

**Consequence for the ADR (Chief Scientist recommendation, Owner-endorsed):** record the full provenance chain explicitly — *§5 v1.0 faithfully documents the historical MQL5 detector; the divergence exists entirely within the Python lineage; therefore v1.1 is not a correction of v1.0 but the first authoritative documentation of the detector definition that actually produced the 324-trade population.* The header framing of this annex now rests on checked fact on both sides of the divergence table.

**Span compatibility note, for completeness:** the verifying session's interim table reports first/last **trade entries** (2026-04-21 08:55 → 2026-07-10 06:05 server); the Owner's designation (§6) records full **market-time coverage** (2026-04-21 01:00 → 2026-07-10 17:33 server). Different quantities, entirely compatible; the designation correctly burns the coverage the detector consumed. Full corroboration record and the reconciliation instruction for the verifying session: `ops\DEVQ-01_NP-S1.md`, Addendum A.

## Addendum B · 2026-07-30 · DEVQ-NP-001/002 evidence adopted; §7 gains question 5; divergence #5 sharpened

Source: the Developer session's committed DEVQs on branch `claude/neelprajnapro-sprint-np-s1-a8171d` (commit 309843e); full account in `ops\DEVQ-01_NP-S1.md` Addendum B. Adopted into this annex with attribution:
- **§7 question 5 added above** (population choice A / B-as-ruled / C, with the Option-A pre-roll supplementary-designation precondition).
- **Divergence #5 sharpened:** the evidenced code reads `h,l,c` only, never bar **open** — v1.0's open-inside condition and gap-through exclusion are *unenforceable* in that code path, not merely unimplemented.
- **Population construction fact:** 325 sweeps → 324 trades (exactly one degenerate-geometry drop); essentially every sweep trades — the population carries no reversal-selection content, reinforcing §7 question 1.
- **Third in-repo witness to the M5 basis:** `knowledge_base/kb.json` ("XAUUSD M5").
- **Timezone evidence of record upgraded:** settlement break 00:00 stored = 17:00 New York · Friday 23:55 closes · half-day truncations 2026-06-19 and 2026-07-03 at 19:55 stored (13:00 ET early close) · zoneinfo: no DST transition inside the span. Conclusions unchanged; argument stronger.
- **Ledger-basis ruling (Architect, DEVQ-NP-002 Q2):** the burn is recorded in true UTC as half-open **[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)**, broker-EEST source noted as provenance.

## Addendum C · 2026-07-30 · Placement correction (worktree copy)

This file was claimed as placed in the worktree by the DEVQ-NP-001 reply ("the records now exist in your worktree at `ops\DEVQ-01_NP-S1.md` **and** `ops\H07_evidenced_definition_annex_NP-S1.md`") but only the first was actually written; a directory listing found this annex absent from `.claude\worktrees\neelprajnapro-sprint-np-s1-a8171d\ops\`. Corrected by placing this copy, 2026-07-30. **Finding recorded against the Architect-analog session (F-A species: stating intended state as accomplished state).** Content is identical to the mainline master at time of placement, mainline remains authoritative, and both converge in git at the next commit.
