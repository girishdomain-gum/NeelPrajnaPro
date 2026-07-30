# NP-ADR-0ZZ — H-07 Detector Definition §5 **v1.1** (DRAFT v2.0 — M1–M7 incorporated)
*Supersedes `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`. Corrections per `ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md` (M1–M7) and `ops\CS_REVIEW_H07_v1.1_2026-07-30.md` (Q1's three binding statements). **Number 0ZZ unassigned** pending registry check (NP-D-006). No normative document edited. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Status:** Chief Scientist review **FILED and accepted** ✅ · corrections applied ✅ · verification pass `ops\POST_CORRECTION_VERIFICATION_H07_v1.1.md` ✅ · **awaiting two Owner rulings (§7) and ratification (§9).**

---

## 1. Decision requested

Seal **§5 v1.1** as the documented detector definition embodied by the H-07 324-trade population, and rule the two embedded decisions in §7. **§5 v1.0 remains frozen and unedited forever.**

## 2. Provenance chain (source-verified on both sides)

1. **§5 v1.0 faithfully documents the historical MQL5 gate** `T3_SweepFVGGate.mqh` v2.1 — H1/M1, `PoolTol = 0.15×ATR14`, pool level = average of member pivots, mandatory MSS stage.
2. **The divergence exists entirely within the Python lineage** (`np_feature_service.py` + `np_probability_engine.py`, retired from evidentiary service by NP-D-001). The MQL5 path never executed for this population.
3. **v1.1 is not a correction of v1.0. It is the first authoritative documentation of the detector definition that actually produced the 324-trade evidence population.**

### 2.1 Non-equivalence — the three binding statements *(Chief Scientist Q1, adopted verbatim; must survive into every derived artifact)*

1. **E2-v1.1 is not equivalent to the original v1.0 hypothesis.**
2. **It is a new hypothesis bound to the documented v1.1 detector lineage.**
3. **Any future judgment of the original T3/MSS detector requires a separate implementation and fresh out-of-sample evidence.**

**Consequence, stated so no reader can miss it:** *no verdict produced under v1.1 validates, corroborates, or speaks to the historical T3 gate.* This sentence is copied into the registration YAML's `outcome_interpretations` and into the verdict's scope note.

## 3. §5 v1.1 — THE SEALED DEFINITION (normative on ratification)

**Identity (M1 — corrected to the repository's actual conventions).**
- **lineage:** `h007_np_liquidity_sweep_v1_1` — flat dotless slug, version carried in the slug, per the `h004_dow_monday_drift_v2` precedent and Execution Plan §4's own `h007_np_liquidity_sweep.yaml` naming.
- **detector / instrument id:** `neelprajna.liquidity_sweep@1.1.0` (dotted + `@version`, per `seasonality.calendar@0.1.0`).
- **event types:** `neelprajna.liquidity_sweep.pool_formed` · `neelprajna.liquidity_sweep.sweep`.
- **family (M2 — load-bearing):** **`xauusd/neelprajna`**, declared identically in **all 19 registrations**. `deflation.py::_trial_belongs_to_family` matches on the declared family with prefix-segment logic; sibling per-detector families do **not** match each other, so a per-detector family string would give every hypothesis its own budget and the α-budget would silently not bind.
- **scope (M7):** `xauusd_m5_vantage`.
- **implementation identity:** `np_feature_service.py` sha256 `1a0b5d9f…a6c0` · `np_probability_engine.py` sha256 `a9b75aeb…d2ff` · population `h07_trades.parquet` sha256 `0f242e2f…0133`. Values are hard-coded at the call site `build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2)` on 300 s bars — not CLI defaults.

**Observation space.** XAUUSD, Vantage Markets MT5 retail feed, broker-tier · clean ticks only (bid>0, ask>0) · price = bid/ask **mid** · TICK_SIZE 0.01 · timestamps stored in broker server time (UTC+3, DST-clean across the span), **converted to int64 ns UTC at the adapter boundary**.

**Observed events (closed bars only).**
- **POOL_FORMED** — on each newly confirmed pivot: same-side pivots within the last **200 bars** priced within **pool_tol = 30.0 ticks fixed**; ≥2 members; level = **max of member prices (HIGH) / min (LOW)**, frozen at formation; no new pool within pool_tol of an active same-side pool; active until swept or invalidated.
- **SWEEP** — wick penetrates the level by ≥ **min_pen = 5.0 ticks**; same-bar close back on the defended side → sweep (reclose_bars 0); else a **2-bar** reclose window — closing back inside → sweep (max penetration retained); failing → **invalidation**, pool resolved, no event.
- **No third event.** REVERSAL_CONFIRMED / MSS does not exist here. The chain is **POOL_FORMED → SWEEP**, terminal.

**Frozen parameters.** bar timeframe **300 s (M5), single**; pivot_k **3**; member window **200 bars**; pool_tol **30.0 ticks fixed**; min_pen **5.0 ticks**; reclose_window **2 bars**.

**Knowability / anti-repaint (AC-2's normative target).** A pivot at bar *i* is confirmed only at *i+k*; a pool is emitted at its confirmation bar; a sweep at the bar whose close resolves it (0–2 bars after first penetration). Every emission carries `ts ≥` the last input bar needed, and no emission changes retroactively under incremental feeding.

**Clauses v1.1 does NOT inherit.** v1.0 requires the exec bar to *open inside* the defended side and excludes gap-through opens. The evidenced code reads `h, l, c` only and never the bar **open**, so both are *unenforceable* in this lineage. v1.1 states neither.

**Prediction layer (frozen 2026-07-10; playbook, excluded from the existence claim).** SELL after HIGH-pool sweep / BUY after LOW-pool sweep · entry = mid at the open of the bar after the sweep bar · stop = penetration extreme ±10 ticks · target 1.5R · time stop 12 bars · 1-second mid resolution, SL wins ties · costs per the sealed model (§7 decision A).

**Designated coverage.** UTC half-open **[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)** (broker EEST 2026-04-21 01:00 → 2026-07-10 17:33), TRAINING, burned. Population: 324 trades from 325 sweeps (one degenerate-geometry drop, risk < 5 ticks).

## 4. What the Battery actually does (M3, M4, M6 — corrected)

**M3 · The Battery has EIGHT pipeline steps, not nine.** `battery.py`'s docstring and **ARCH-006 §3** (Gen-1 normative) enumerate the identical 1–8: type gate · selftest gate · window checks · splits · engine per fold TEST range · statistics · tri-state at deflated α · append verdict + burn. "Nine steps" in Architecture §2, Execution Plan §4/AC-4 and V&V §3.4 has no source and most likely derives from Blueprint §5 **arrow (9)**, cited in `battery.py`'s header. Execution Plan §4 is **frozen and must not be edited**; Architecture §2 and V&V §3.4 are not frozen and are corrected in the next write window.

**M4 · "B1–B7" is SIX reported criteria, not seven.** The report's keys are B1, B3, B4, B5, B6, B7. **B2 (OOS discipline) is not a reported gate** — it is a procedural property ("OOS = final 40%, evaluated once"). Recorded outcome: **B1 pass (194/130); B3, B4, B5, B6, B7 all fail; verdict FAIL** — a five-gate failure, not "FAIL on cost sensitivity" as Execution Plan §4/§5 state (that phrasing derives from the descriptive `CostThreshold_Report`, which disclaims being a verdict). **AC-4's mapping is therefore 8 Battery steps ↔ 6 reported criteria + B2 as a procedure**, sealed in the YAML before the run.

**M6 · The Battery does not judge the 324 trades.** It re-simulates from `bars` + `events` using the injected audited simulator, **per fold, over TEST index ranges only**, dropping and counting trades that cannot open and close inside their block. The comparison is therefore: *same window, same detector definition, same trade rule — different instrument, therefore a different judged trade set by construction.* **The judged n will be materially smaller than 324.** This is pre-registered here so a smaller n is read as arithmetic, not as defect; `min_n` is set accordingly in the registration.

## 5. Data path (M7 — corrected)

Architecture §3.2 describes the data path as `NP_Trades_*` / `NPSU_Trades_*` CSVs through `mt5_csv.py`. **That path does not apply to this population.** The evidenced source is the Stage-2 **tick parquet** (60 SHA-stamped daily files, `Stage2_DataValidationReport` PASS) aggregated to M5 mid bars. Required for the run: scope `xauusd_m5_vantage` registered; ticks → M5 mid bars (`(bid+ask)/2`, 300 s buckets) → BulkStore with manifest; events from the v1.1 detector; both anchored int64 ns UTC. Recorded as a documentation divergence against Architecture §3.2, correctable in the next write window (not frozen).

## 6. E2-v1.1, restated

**Existence claim (E2-v1.1):** *does SWEEP follow POOL_FORMED beyond chance arrangement?* — do penetration-and-reclose events concentrate at previously frozen equal-high/low levels more than a null preserving session and volatility character while destroying the cross-bar level relationship. Null design **N2** unchanged (block resampling, seam-preserving, calendar-template); block length, seeds and thresholds sealed in the YAML before data is touched. The definition trap still applies — pool_tol and min_pen buy the event rate, so the testable content is arrangement, never base rate. Registered and counted now; **judged only when N2 machinery certifies.** Governed by §2.1's three statements.

**Prediction claim:** judged this sprint by the certified Battery against the random-timing placebo.

## 7. The two decisions the Owner must rule *(Chief Scientist concurs with both; a concurrence is not a ruling)*

**Decision A · Cost model (M5).** `xauusd_retail_h07` does not yet exist in `configs/venues.yaml`; registration hard-errors on an unknown cost model (ARCH-006 §1, V&V §2.3). **Recommended: $0.41/oz round-trip**, entered as:

```yaml
  xauusd_retail_h07:
    instrument: XAUUSD
    unit: troy_ounce
    currency: USD
    spread: 0.24              # MEASURED median across the 60 Stage-2 tick files (24 ticks)
    slippage_per_side: 0.05   # adopted from xauusd_retail_median (declared estimate)
    commission_per_side: 0.035 # adopted from xauusd_retail_median (declared estimate)
    version: "1.0.0"
    note: >
      Round-trip = 0.24 + 2*(0.05 + 0.035) = 0.41 USD/oz. Spread is MEASURED from
      the evidence dataset itself; slippage and commission are QRF's declared
      estimates. The bespoke stack charged 26 ticks (0.26 USD/oz) — approximately
      spread-only, charging almost nothing for slippage or commission.
```
Alternatives: $0.26 (bespoke as-run) or $0.47 (`xauusd_retail_median`). **Name immutability applies: frozen once cited by any ledger record.**

**Decision B · Trial count.** J-029 recorded 18. QRF-ADR-011 spends an attempt per registration, and NP-S1 makes **19** (H-07's two + 17 counted-only). Recommended: **19 → per-claim bar p < 0.00263** (a tightening, never a loosening; recomputed against family totals at every judgment).

## 8. Consequences for the sprint

Deliverable 1 — v1.1 detector + planted/clean cases (AC-1). Deliverable 3 — two registrations citing lineage `h007_np_liquidity_sweep_v1_1`, family `xauusd/neelprajna`, scope `xauusd_m5_vantage`, cost model per Decision A. Deliverable 4 / AC-3 — one Battery run, verdict + burn atomic on the UTC interval in §3. Deliverable 5 / AC-4 — mapping 8 steps ↔ 6 criteria + B2, sealed before the run, with §4's population caveat in the interpretation table. Deliverable 6 / AC-5 — 17 counted-only entries, same family string; total 19.

## 9. What does not change

§5 v1.0 (frozen, unedited) · the designated window and its TRAINING burn · claim form E2 and null design N2 · Constitution §6 · the Twelve Principles · the wall · the Publication Boundary · write authority · Execution Plan §4's frozen text · all history.

## 10. Ratification wording (type one)

- **APPROVE:** *"NP-ADR H-07 §5 v1.1 is RATIFIED as drafted v2.0, including the three non-equivalence statements, lineage `h007_np_liquidity_sweep_v1_1`, family `xauusd/neelprajna`, scope `xauusd_m5_vantage`, cost model `xauusd_retail_h07` at $0.41/oz, trial count 19 (p < 0.00263), the eight-step / six-criteria mapping, and Option C. §5 v1.0 remains frozen. NP-S1 registration is unblocked against v1.1."*
- **APPROVE WITH VARIATION:** as above, naming the variation (e.g. a different cost figure or trial count).
- **REJECT / RETURN:** *"Not ratified — [reason]. NP-S1 remains halted."*

---
*Anchor: **v1.0 says what the gate was; v1.1 says what the evidence was made by — and no verdict under v1.1 speaks for the gate.***
