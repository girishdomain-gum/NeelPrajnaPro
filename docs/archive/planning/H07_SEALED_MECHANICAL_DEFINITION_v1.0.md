# H-07 — Sealed Mechanical Definition v1.0
*Equal-high/equal-low pool sweep reversal · Sealed for ARCH-NP-001 · Author: Fable (Architect) · 2026-07-29*
*Source of mechanics: `F:\NeelPrajna\repo\Gates\Triggers\T3_SweepFVGGate.mqh` v2.1 (the merged Gate-7 EQH/EQL pool engine) — read from source this day, not from memory. Owner rulings incorporated: claim form E2; cost model `xauusd_retail_h07`.*

## 1. What is observed (raw observations — no interpretation)

Three event kinds, all computed from **closed bars only** (anti-repaint constitutional rule; nothing is emitted that was not knowable at its bar's close):

- **POOL_FORMED** — a price level at which ≥ `pool_min_touches` pivot highs (EQH pool) or pivot lows (EQL pool) cluster within `pool_tol`. The pool's level is **frozen at formation** as the average of its member pivots and does not drift on later rebuilds. Pools are rebuilt once per closed anchor-timeframe bar over `pool_lookback` bars.
- **SWEEP** — a closed execution-timeframe bar that (a) **opens inside** the pool's defended side, (b) **wicks through** the frozen pool level, and (c) **closes back** on the original side (stop-hunt rejection). A bar that *gaps through* the level at the open is **not** a sweep. The setup's furthest wick is tracked as the swing extreme.
- **REVERSAL_CONFIRMED** — within `mss_max_bars` of the sweep, a closed execution bar **closes beyond the pre-sweep swing** (the extreme of the prior `swing_lookback` closed bars). This is the Market Structure Shift; its bar is the event's confirmation bar and the earliest permissible emission time.

## 2. The mechanical rule (frozen parameters, from source defaults)

| Parameter | Frozen value | Source symbol |
|---|---|---|
| Anchor TF (pool source) | H1 | `InpT3_AnchorTF` |
| Execution TF (event bars) | M1 | `InpT3_ExecTF` (chart TF of the evidence runs) |
| pool_lookback | 500 closed H1 bars (hard cap 2000) | `InpT3_PoolLookback` |
| pool_pivot_len | 3 bars each side | `InpT3_PoolPivotLen` |
| pool_min_touches | 2 pivots | `InpT3_PoolMinTouches` |
| pool_tol | 0.15 × ATR14(H1) (the AUTO rule; 0-input) | `InpT3_PoolTolPoints` |
| swing_lookback | 10 closed exec bars | `InpT3_SwingLookback` |
| mss_max_bars | 30 closed exec bars | `InpT3_MSSMaxBars` |

The detector `qrf/trading/concepts/neelprajna/liquidity_sweep.py` implements exactly §1's three events with exactly this table. Downstream trade-blueprint stages in the source (displacement filter, FVG, order block, tap, entry modes) are the **prediction-layer playbook**, not the phenomenon, and are excluded from this definition. **DEVQ trigger:** if the historical 324-trade export is found at registration to have run under non-default values of any frozen parameter, the Developer halts and asks; the definition is then re-sealed as v1.1 with the evidenced values — never silently adjusted.

## 3. Observation Space (scope of every H-07 claim)

Domain: markets · Instrument: XAUUSD (retail feed, broker-tier independence) · Data source: MT5 CSV exports via `mt5_csv` (OBS-4 close-time) · Temporal: H1 pools / M1 events, 24×5 with weekend & DST seams computed from data · Market state/regime: 2024–2026 trending-gold conditions — every verdict is regime-conditioned and says so · Statistical context: `neelprajna` family, TrialCountLedger-priced, Owner α-budget · Event context: sweep events conditioned on prior POOL_FORMED · Window: Owner-designated (seen data — TRAINING/EXPLORATION, never VIRGIN) · Detector: `neelprajna.liquidity_sweep` v1.0, certified per V&V L1–L3 before observing · Confidence & research context: recorded per registration.

## 4. Claim form — E2 (Arrangement), per Owner ruling 2026-07-29

The **definition trap applies**: pool occurrence is partially purchased by the definition itself (`pool_tol`, `pool_min_touches` buy a base rate), so an E1 rate claim is uninformative. The testable content is the **arrangement**: *does REVERSAL_CONFIRMED follow SWEEP beyond what chance timing produces — in clustering, in sweep→reversal transition frequency, and in time-to-reversal structure?*

**Two-claim structure (sequencing honesty):**
- **E2 existence claim** — registered in NP-S1 (the attempt is counted at registration per QRF-ADR-011); **judged when the N2 null machinery is certified** (Gen-2 S3–S4 or the NP-side equivalent under the same V&V), because Gen 1 built no ensemble null library and an uncertified null may judge nothing.
- **Prediction claim** (trading H-07 nets positive after `xauusd_retail_h07` costs) — this is the claim the bespoke B1–B7 battery already judged (FAIL on cost sensitivity) and the claim ARCH-NP-001's real Battery run re-judges against Gen-1's certified random-timing placebo: the twice-judged comparison. The lifecycle ordering (existence before prediction) is honored by scope: NP-S1's prediction verdict inherits B-stage standing only; no phenomenon is declared "established" by it.

## 5. Null design — N2 block resampling (for the E2 claim)

**Why N2:** the arrangement claim spans multi-bar structure (H1 pools feeding M1 events across sessions). N1 whole-day rotation preserves each day internally but cannot destroy *within-day* sweep→reversal arrangement — it would leave the claim partly intact inside the null. **N2 seam-preserving, calendar-template block resampling** preserves the market's distributional character, session frames, and volatility clustering while destroying the specific cross-bar arrangement under test — it removes exactly the claim and nothing else. N3 model surrogates are reserved as a sealed robustness companion, not the primary. Block length, seed policy, and thresholds are sealed in the registration YAML before any judging data is touched.

---
*Seal: this definition is FROZEN on ARCH-NP-001's sealing. Any change is v1.1 by NP-ADR, never an edit. A phenomenon without a sealed definition is not a phenomenon — it's an opinion (Owner, 2026-07-29).*
