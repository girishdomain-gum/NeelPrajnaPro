# NeelPrajna Platform & Integration Architecture v2.0

| | |
|---|---|
| **Version** | 2.0 (supersedes DeepSeek Platform Architecture v1.0 and the DeepSeek Research Architecture; absorbs Volume IV as the frozen basis per REV F-3) |
| **Date** | 2026-07-29 · **Status** | DRAFT — awaiting Owner ratification · **Layer** | Charter (normative); §8 is ASPIRATIONAL |
| **Predecessors** | Constitution v2.0 · Scientific Model v2.0 · **Successor** | ARCH-NP-001 (first sprint) |

---

## 1. The Frozen Basis

1.1 The architecture is **integration into the real, proven QRF Kernel** (carried forward into this repository). NeelPrajna's research questions are judged by the instrument that closed QRF Generation 1: ten sprints, IVF-drilled, four hypotheses judged, zero promoted.

1.2 NeelPrajna's bespoke research stack (`np_knowledge_base.py`, `np_probability_engine.py`, `np_hypothesis_zero.py`, `np_cost_threshold.py`, `np_trade_verifier.py` in its judging role) is **retired from evidentiary service** on ratification. It may run as exploratory tooling; its outputs carry no epistemic weight and may never write a verdict, burn a window, or update a belief.

1.3 No component of the Kernel is re-implemented on the NeelPrajna side. The imagined "QRF brain" (Knowledge Graph / Pattern Evolution / Confidence engine) of prior documents is ASPIRATIONAL-tier and appears only in §8.

## 2. The Kernel, As Actually Built (authoritative component list)

| Component | Real location | Role |
|---|---|---|
| RecordStore | qrf/kernel/records/store.py | Hash-chained, single-writer, fsync'd append-only ledger; torn-tail detection |
| BulkStore / schemas | qrf/kernel/records/ | Parquet + manifests; payload validation |
| InstrumentRegistry / CalibrationHarness | qrf/kernel/instruments/ | Registration; planted-truth and silence tests |
| WindowLedger | qrf/kernel/protocol/windows.py | TRAINING/EXPLORATION/VIRGIN designation; burn-on-use; structural refusal on reuse; reserve-by-market-time |
| EvidenceBattery | qrf/kernel/battery/battery.py | Sole verdict writer; nine steps; selftest gate re-verified every run; atomic verdict+burn |
| TrialCountLedger | qrf/kernel/corrections/trials.py | Registration spends the attempt (QRF-ADR-011); family deflation at judgment |
| BeliefLayer | qrf/kernel/belief/ | Updates from Verdict-typed inputs only |
| Observatory | qrf/kernel/observatory/ | Anomaly scans → questions only; no verdict, no burn |
| Kernel firewall | tests/test_kernel_firewall.py | CI-enforced: kernel never imports trading; forbidden-token scan |

2.1 **Write authority (closed list):** `store.append` (records) · Battery (verdict, window_burn) · Screener (trial_count bumps) · `belief.update` (from Verdicts only). Everything else proposes files or reads.

## 3. NeelPrajna as the Second Concept Family

3.1 New detector package: `qrf/trading/concepts/neelprajna/`, alongside classical, seasonality, and smc — a fourth family, not a fourth framework.

3.2 Data path: existing `NP_Trades_*` / `NPSU_Trades_*` MT5 CSV exports feed the existing `qrf/trading/adapters/mt5_csv.py` (explicit timeframe, OBS-4 close-time normalization). No new adapter.

3.3 Hypotheses: the founding set becomes `configs/hypotheses/h0NN_*.yaml` in the Kernel's existing format, each with `instrument_id` and `code_ref`, hashed into the ledger at registration.

3.4 **Cost-model reconciliation (bounded normative task):** QRF's `xauusd_retail_median` (round-trip $0.47/oz) and NeelPrajna's 26-tick round-trip figure shall be reconciled into one authoritative, named, versioned `configs/venues.yaml` entry before any NeelPrajna verdict is requested. Name immutability applies: once cited by any ledger record, frozen; every change is a new name.

3.5 **Window designation (Owner precondition):** the market time underlying already-seen NeelPrajna evidence (including H-07's 324 trades) shall be designated honestly (TRAINING/EXPLORATION — it cannot be VIRGIN) by the Owner's typed phrase before registration. Any future VIRGIN reserve for the NeelPrajna family is designated the same way.

## 4. The Communication Contract v2

4.1 Six object types only: Observation · Pattern · Knowledge · Recommendation · Execution Feedback · Performance. No internal variables cross.

4.2 Two prohibitions: the runtime never asks about Kernel internals; the Kernel never says BUY or SELL.

4.3 **Knowledge Publication Boundary (Constitution §3, restated operationally):**
- Knowledge and Pattern objects published to the runtime shall reference only sealed, Battery-verdicted beliefs, carried as **versioned, dated belief releases** — not streams.
- The fields `recent_win_rate` and any rolling/unsealed statistic are removed from published objects. Historical statistics in a Knowledge object are those computed inside the sealed evidence of its verdict, frozen at release.
- Execution Feedback and Performance flow to the Performance Store as observations only (P4/P1); they update no belief directly.

4.4 Publication semantics are **batch release, not tick-time heartbeat**. Freshness is a release date, and the runtime shall treat a stale release as stale knowledge, never extrapolate it.

## 5. What Stays Separate, On Purpose

| Stays with NeelPrajna (NP-ADR-005 governance; lives at F:\NeelPrajna) | Moves to / lives in the Kernel (this repository) |
|---|---|
| Live order execution: TradeManager, MoneyManager, EntryGates walk, 2% rule | Is this hypothesis statistically real? (EvidenceBattery) |
| Supervisor/Runner trust split; autonomy ladder L0–L3; seven G-invariants; the bridge | Is this window contaminated or burned? (WindowLedger) |
| NPSU shadow universes, Live Advisor, dashboards | How many attempts has this family made? (TrialCountLedger) |
| Per-trade risk, auto-close, session-only apply | Has the claim been independently reproduced? (IVF) |

5.1 The dividing line is QRF-ADR-004's Kernel/plug-in line applied one level up: execution machinery is domain-specific and stays; the question of whether a claim is true moves to the domain-blind judge.

## 6. Real-Account Switching Safety (normative; from the Auto-Adopt audit, REV F-13/F-14)

6.1 Any mechanism that can change what the real account trades without a human click (`InpADV_AutoAdopt` Path A; `SeqLive.mqh` live apply; successors) shall satisfy, before it may be armed:
(a) hysteresis at least equal to the advisory path's `InpADV_ConfirmEvals` consecutive-win requirement;
(b) an out-of-sample-validated eligibility check (`validated=1`), not trade-count warm-up alone;
(c) an Owner arming decision on the record (Constitution §6 — permanently human).

6.2 Until 6.1 is satisfied for a given mechanism, its default and armed state shall be OFF/NONE, and the dashboard shall display the audit's asymmetry banner whenever a recommendation is shown while any such mechanism is active.

6.3 The `SeqLive.mqh` line-by-line audit is a prerequisite for arming that path and shall use the same input-group-grep method as the Auto-Adopt audit.

## 7. Verification & Validation Requirements (per component this architecture adds)

7.1 The `neelprajna.liquidity_sweep` detector (and every subsequent family detector) ships with planted-truth cases and clean-control cases and must catch all planted frauds and stay silent on clean data before observing for any registered claim.

7.2 IVF re-derives every NeelPrajna-family verdict from normative texts, drilled first, exactly as for every other family. Origin grants no shortcuts.

7.3 Every sprint follows the ratified rhythm: ARCH → Developer sessions → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → handover rewrite.

## 8. ASPIRATIONAL Tier (recorded intent; not binding)

The living-organism framing; a continuous shared heartbeat; a populated Knowledge Graph acting as research collaborator; the Research Console's KNOWLEDGE/EVIDENCE lenses bound to live NeelPrajna beliefs (DESIGNED — unblocked only after migration per Console spec v1.3's stated precondition); SEA application books beyond markets. None of these may be cited as authority for any build decision.

## 9. Change Record (v1.0 → v2.0)

Retained: Kernel/plug-in split, firewall, contract's six objects and two prohibitions, audited-engine pessimism, name immutability, extensibility principles. Changed: imagined Kernel replaced by the real one (F-3); learning loop routed through the Publication Boundary with rolling stats removed from the contract (F-2); heartbeat demoted to §8 (F-6); window/α-budget/cost-model preconditions made normative (F-10); real-account switching safety added (F-13/F-14); ADR references namespaced (F-12).

---
*Anchor: **execution stays where the hands are; truth moves to where the judge is.***
