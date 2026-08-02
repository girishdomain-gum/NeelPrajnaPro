# NeelPrajna Platform & Integration Architecture

> **Twin rule (Owner-confirmed 2026-07-29):** this file is the machine-readable normative TEXT of the programme's one architecture document, `docs\architecture\NeelPrajnaPro_Architecture-v1.0.docx` (the human master, which additionally carries the eight rendered diagrams). They are one document in two forms and version in lockstep; any divergence between them is a finding. Machines (Developer sessions, IVF) read this file; humans read the docx.

## Part A — The Destination (Owner vision ruling, 2026-07-29)

The two-organ architecture is this development cycle's TARGET: Market → Observation Engine (one shared reality) → Core QRF Brain (domain-blind) ‖ Book-A NeelPrajna Runtime (trading plug-in) → Knowledge+Evidence / Orders+Execution-Feedback → event-driven communication. **The load-bearing wall, permanent: QRF never trades; NeelPrajna never learns on its own.** *(Failure asymmetry, added 2026-07-29 from cross-review: bad knowledge is filtered by review before it can act; a bad trade is bounded by the risk layer before it can compound — neither organ's failure mode can reach the other's blast radius.)*

### A.1 The box column — canonical (aligned to Execution Plan v2.0, 2026-07-30)

**This table is the spine.** The docs\vision\ master and the docs\execution_plan\ master use these exact box names and this exact sprint mapping. A divergence between any of the three is a finding.

| # | Architecture box | Status | Delivered by |
|---|---|---|---|
| 1 | EvidenceBattery / WindowLedger | BUILT | Gen-1 (closed) |
| 2 | Scientific Memory | BUILT | Gen-1; NP records begin **NP-S1** |
| 3 | Observation Engine | BUILT (Kernel side) | NP feed **NP-S1**; widened **NP-S2**, **NP-S3** |
| 4 | Statistics & Confidence | BUILT (core) | enriched every verdict; further at **NP-S6** |
| 5 | Execution feedback → Core | TARGET | **NP-S2** (R6 pipeline + RecordStore migration) |
| 6 | Pattern Learning | TARGET | **NP-S3** (first NP existence judgments; ECF nulls certify on the Gen-2 track) |
| 7 | Knowledge + Evidence → runtime | TARGET | **NP-S5** — Contract v2 goes live (built, not merely ruled) |
| 8 | Continuous Communication | TARGET | **NP-S5** — event-driven belief releases; never tick-streaming of unsealed statistics |
| 9 | Knowledge Graph | TARGET | **NP-S6** (+ Gen-2 S7 synthesis) |
| 10 | Pattern Evolution | TARGET | **NP-S9+** (Phase 5; machine-proposed only after Gate A) |
| 11 | Surface — Research Console (Core side) | TARGET | **NP-S7** (spec v1.3, five lenses + CYCLE) |
| 12 | Surface — Book A Dashboard (Runtime side) | BUILT (basic); depth TARGET | **NP-S8** (spec v1.4/v1.5) |

**On rows 11–12:** the two surfaces are *views onto* the organs, not organs themselves — which is why they do not appear as boxes in the two-organ diagram. They are enumerated here so that every sprint in the Execution Plan maps to a row, and no delivered work sits outside the box column. Arming anything real remains permanently human at every row (Constitution §6).

**The plan's acceptance test:** when no row still reads TARGET, the architecture is built.

## Part B — The Binding Architecture (ratified 2026-07-29)

| | |
|---|---|
| **Version** | 2.0 (supersedes DeepSeek Platform Architecture v1.0 and the DeepSeek Research Architecture; absorbs Volume IV as the frozen basis per REV F-3) |
| **Date** | 2026-07-29 · **Status** | **RATIFIED by the Owner, 2026-07-29** (with §4.5 Knowledge Publication Boundary expansion incorporated per the ratification memo) · **Layer** | Charter (normative); §8 is TARGET (evidence-gated) per the vision ruling |
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

4.5 **The Knowledge Publication Boundary, expanded (Owner ruling, 2026-07-29).** QRF publishes *what it knows*, never *how it knows*. The boundary in one table:

| QRF publishes (across Contract v2) | QRF keeps internal (never crosses) |
|---|---|
| Pattern ID, applicability scope, regime conditioning | Internal belief state and belief-update mechanics |
| Verdict-sealed statistics — win rate, expectancy, confidence — **computed inside the sealed evidence of the verdict and frozen at the release date** | Raw observations, event streams, calibration and drill state |
| Recommendations (advisory objects; never orders) | The decision-making process that produced them |
| Knowledge (validated: Battery-verdicted, versioned, dated) | Knowledge-in-progress: candidates, screener output, unsealed analyses |

Two clarifying rules so this table and §§3.3–3.4 of the Constitution can never be read against each other: (a) any statistic in a published object is the **frozen, sealed-verdict** figure — a published "win rate" is the one inside the verdict's evidence at release, never a rolling or live figure; (b) the boundary protects both organs symmetrically — the runtime cannot reach into Kernel internals, and the Kernel cannot see runtime internals beyond the Execution-Feedback and Performance observation objects the contract defines.

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

## 8. TARGET Tier (re-tiered from ASPIRATIONAL by the Owner's vision ruling, 2026-07-29 — see the docs\vision\ master)

The two-organ destination architecture — Pattern Learning (row 6), Knowledge Graph (row 9), Pattern Evolution (row 10), Continuous (event-driven) Communication (row 8), the Research Console including its KNOWLEDGE/EVIDENCE lenses (row 11, **NP-S7**), the Book A dashboard's designed depth (row 12, **NP-S8**), SEA application books — is the TARGET of this development cycle: each element becomes real only through the sealed sprint named against its row in §A.1, and none may be cited as existing before its verdict-bearing artifact does. Tick-time streaming of unsealed statistics remains excluded permanently (§4.3–§4.5).

## Part C — The Visual Atlas (renders live in the docx master; captions and statuses are normative here)

Diagram 1 programme top-down — the destination (Part A). · Diagram 2 Core Kernel components — BUILT (real module paths; exercised by the 853-test suite). · Diagram 3 Communication Contract — TARGET (design sketch; **implemented at NP-S5** via Contract v2 + §4.5 boundary — rows 7–8 of §A.1). · Diagram 4 Book-A four-layer MQL5 refactor — BUILT (live EA, paused at F:\NeelPrajna). · Diagram 5 NPSU shadow universes — BUILT (runtime-side; outputs are observations/candidates, never evidence). · Diagram 6 Supervisor/Runner trust split — BUILT (contract v1.1 owner-signed; live-verified HEALTHY 2026-07-29). · Diagram 7 evidence pipeline — BUILT core + TARGET null library. · Diagram 8 documentation-tree redesign — SUPERSEDED with honor by the one-doc-per-thing law; its Registers' spirit lives in the journal master.

## 9. Change Record (v1.0 → v2.0)

Retained: Kernel/plug-in split, firewall, contract's six objects and two prohibitions, audited-engine pessimism, name immutability, extensibility principles. Changed: imagined Kernel replaced by the real one (F-3); learning loop routed through the Publication Boundary with rolling stats removed from the contract (F-2); heartbeat demoted to §8 (F-6); window/α-budget/cost-model preconditions made normative (F-10); real-account switching safety added (F-13/F-14); ADR references namespaced (F-12).

**Unified-doc v1.0 (2026-07-29, later):** restructured as the text twin of NeelPrajnaPro_Architecture-v1.0.docx per the Owner-confirmed twin rule — Part A (destination) and Part C (atlas captions) added; Part B = the ratified v2.0 body unchanged; §8 re-tiered TARGET per the vision ruling. From here the two forms version in lockstep.

**Alignment correction (2026-07-30, Constitution §7.2 clarification — Owner-approved).** Finding F-24: Part A's box-to-sprint mapping was written when Execution Plan v1.0 ended at NP-S4, so it described Contract v2 consumption, Continuous Communication, the Knowledge Graph, and Pattern Evolution as *rulings at the NP-S4 boundary* rather than scheduled builds. Execution Plan v2.0 (2026-07-30) schedules them as real sprints, and Part A had not been back-propagated. **Corrected here:** Part A's prose replaced by the canonical box table §A.1 (12 rows) matching v2.0 exactly — rows 7–8 at NP-S5, row 9 at NP-S6, row 10 at NP-S9+, and rows 11–12 added for the two surfaces (Research Console NP-S7, Book A dashboard NP-S8), which were previously enumerated nowhere. §8 and Part C's Diagram-3 caption updated to match. **No requirement changed** — the wall, the Publication Boundary, the separation table, and the write-authority list are untouched; only stale sprint pointers were corrected against a plan the Owner had already approved. Recorded as a clarification, not an amendment, per §7.2.

---
*Anchor: **execution stays where the hands are; truth moves to where the judge is.***
