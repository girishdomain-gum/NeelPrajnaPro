# EXECUTION PLAN — the one living document: phases, sprints, and their outputs
*Version 2.0 · 2026-07-30 · Supersedes v1.0 (2026-07-29), which planned only NP-S1..S4 and stopped at acceptance — it never showed how the ratified architecture actually gets built. This version carries the path all the way to the destination. Predecessor preserved in git history. From now on: sprints are planned here, and their OUTPUTS are appended in §9 when they close.*

---

## 0. CURRENT STATE (rewritten at every sprint boundary — this is the handover)
**As of 2026-07-30:** Repo bootstrapped, full Gen-1 history on GitHub. Estate RATIFIED (Owner memo, journal J-004). H-07 definition SEALED (§5 below). Rulings in force: Auto-Adopt DISABLE pending hysteresis · cost model `xauusd_retail_h07` · claim form E2 · vision ruling · one-doc-per-thing law · **neelprajna family α-budget = 0.05 (Owner-typed 2026-07-30; per-claim bar at 18 registered trials = p < 0.0028)**. All 14 docs carry PDF-verified docx twins. Legacy repos paused. **Blocking items remaining, both Owner, both typed lines: (1) the H-07 window designation — method (b) selected by the Owner (scope-based; Developer resolves the exact span from the export at registration and echoes it back for confirmation before the seal), designation line itself still to be typed; (2) Go/No-Go on Sprint NP-S1.** On Go: Developer boots per §3 boot sequence.

## 1. THE DESTINATION — what "NeelPrajna as per our architecture" concretely means

When every sprint below has closed, this exists:

- **One Observation Engine** feeding both organs — the same detectors, the same EventFrames, the same ledger. No research/production data divergence.
- **The Core (QRF Brain)** holding Scientific Memory, Statistics & Confidence, Pattern Learning, a populated Knowledge Graph, Pattern Evolution, and the drilled EvidenceBattery + WindowLedger that judge everything.
- **Book A (NeelPrajna Runtime)** still executing — TradeManager, MoneyManager, gates, NPSU, the on-chart dashboard — but now *informed by* sealed belief releases instead of by its own private statistics.
- **Contract v2 live between them**: six object types, event-driven releases, nothing else crossing. Knowledge flows toward the runtime; execution feedback flows toward the Brain, as observations only.
- **Two surfaces**: the browser-based Research Console (Kernel side) and Book A's own on-chart dashboard (runtime side), both built to their existing specs.
- **The wall intact, permanently**: *QRF never trades. NeelPrajna never learns on its own.*

**Every sprint below names which architecture box it turns from TARGET to BUILT.** That mapping is the plan's own acceptance test: when no TARGET boxes remain, the architecture is built.

## 2. THE COMPONENT MAP — what happens to each existing NeelPrajna component

This is the table the plan was missing. **Read the middle column carefully: nothing is deleted or replaced.** Each component keeps doing its job; what changes is that its *claims* become judgeable, and its *inputs* become sealed knowledge instead of private opinion.

| Existing component | What actually happens to it | Where it ends up |
|---|---|---|
| **EntryGates (B1–B6, T1–T9)** | Gate *semantics* are ported as `neelprajna` detectors so their claims can be judged. The gates themselves keep firing in the EA, unchanged. | Runtime keeps them · Kernel gains detectors mirroring them |
| **SequenceEngine** | Sequence *claims* ("this 2-step chase has an edge") get registered as sealed hypotheses. The engine keeps running sequences live. | Runtime keeps it · Kernel gains its hypotheses |
| **VirtualBook / NPSU** | Keeps shadow-trading. Its outputs become **observations and candidates**, never evidence — exactly the P4 line (candidate discovery is not validation). | Runtime keeps it · feeds the Observation Engine |
| **UniverseEngine (ranking)** | Keeps ranking for operational purposes. Ranking never becomes a verdict — the Battery alone issues those. | Runtime keeps it · Battery judges separately |
| **UniverseRoster** | Stays the runtime's strategy list. Hypotheses *about* those strategies are registered in the Kernel's HypothesisRegistry. | Runtime keeps it · Kernel gains the registrations |
| **AdvisorEngine** | Keeps recommending — but **consumes sealed belief releases** instead of computing beliefs from its own rolling stats. This is the single most important change in the whole programme. | Runtime keeps it · now fed by Contract v2 |
| **TradeManager / MoneyManager / TwoPCRule** | Untouched. Execution machinery is domain-specific and stays where the hands are. | Runtime, unchanged |
| **On-chart dashboard** | Gains the depth its v1.4/v1.5 spec already designs (Live Advisor detail, LIVE/VIRT UNIV deep views). | Runtime, extended (NP-S8) |
| **NPSU CSV logging** | Becomes RecordStore + BulkStore records with manifests — immutable, hash-chained, reproducible. | Migrates to Kernel storage |
| **`np_probability_engine.py` / `np_knowledge_base.py`** | **Retired from evidentiary service** (ratified). May run as exploration; carries no epistemic weight. | Retired |

**The correction this table encodes:** an earlier draft roadmap described these as *replacements* (`EntryGates → Detector`, `AdvisorEngine → BeliefLayer`). Read literally that dissolves the runtime into the Kernel and breaks the wall. The truth is narrower and better: **execution stays where the hands are; only the question "is this claim true?" moves to the judge.** That is Architecture §5 and NP-D-001, both Owner-ratified, and this plan is built to satisfy them.

## 3. THE PHASE LADDER

```
 PHASE 1              PHASE 2              PHASE 3              PHASE 4            PHASE 5
 FOUNDATION           THE FAMILY           THE NERVOUS SYSTEM   THE SURFACES       KNOWLEDGE
 NP-S1 · NP-S2        NP-S3 · NP-S4        NP-S5 · NP-S6        NP-S7 · NP-S8      NP-S9+

 H-07 twice judged    the 17 migrated      Contract v2 live     Research Console   more families
 R6 data + NP feed    acceptance passed    Knowledge Graph      Book A dashboard   mechanisms
                                           Pattern Learning     depth              principles
 ↓                    ↓                    ↓                    ↓                  ↓
 the pipeline works   the family is real   the organs connect   humans can see it  it accumulates
```

Cadence: quality gates, not clocks. Per-sprint rhythm (Gen-1's, proven): instruction → Developer sessions → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → §0 rewrite. Standing tripwires: a sprint producing documents but no verdict or artifact = No-Go finding against the Architect; any evidentiary use of the retired bespoke stack = finding against the invoker.

---

## 4. SPRINT NP-S1 — H-07 twice judged *(SEALED — ratified 2026-07-29, unchanged from v1.0)*

**Architecture boxes delivered:** Observation Engine (NP feed, first detector) · Scientific Memory (first NP records)

**Preconditions:** ☑ F-13 ruled (Auto-Adopt NONE) · ☑ cost model named `xauusd_retail_h07` (frozen once cited) · ☑ definition sealed (§5) · ☑ **α-budget ruled 0.05 (Owner-typed 2026-07-30) — per-claim bar at 18 trials: p < 0.0028; deflation recomputed against total family trials at every judgment** · ☐ Owner window designation (method (b) selected; line still to be typed).

**Deliverables:**
1. `qrf/trading/concepts/neelprajna/liquidity_sweep.py` — standard Detector contract; implements exactly §5's events and frozen parameters; MQL5 gate + `np_feature_service.py` are reference only, §5 is normative.
2. `planted_cases()` — planted-truth + clean-control cases; all frauds caught, silence on clean, before any real run.
3. `configs/hypotheses/h007_np_liquidity_sweep.yaml` — TWO sealed registrations, both priced at birth: (a) prediction claim, judged this sprint by the real Battery vs random-timing placebo; (b) E2 existence claim (N2 nulls), judged when null machinery certifies.
4. One real `EvidenceBattery.run()` on the designated window over the same 324-trade population B1–B7 judged (recorded bespoke verdict: FAIL on cost sensitivity).
5. **The comparison report** — nine steps vs B1–B7, gate by gate, mapping and every agree/disagree interpretation sealed before the run.
6. Remaining 17 founding hypotheses registered as counted attempts (ledger entries only).

**Acceptance criteria (sealed):** AC-1 all plants caught, zero events on clean · AC-2 anti-hindsight property test passes · AC-3 exactly one verdict + one burn, atomic, on the designated window · AC-4 comparison report exists, every divergence named with cause; agreement is corroboration, divergence is the sprint's most valuable output; the drilled instrument's verdict stands, never averaged · AC-5 family trial count ≥ 18 · AC-6 IVF re-derives the verdict from normative texts after its own planted-fraud drill.

**Non-goals (violations are findings):** no live-execution/TradeManager/NPSU changes; no hypotheses beyond H-07 (registrations excepted); no console work; no edits to `ivf/**`, ledger internals, or normative docs.

**DEVQ triggers:** MQL5→Python semantic ambiguity; unfillable EventFrame fields; export/adapter mismatch; window-vs-population disagreement; anything the cost ruling leaves undefined; §5's parameter-mismatch trigger. Silence binds no one.

**Developer boot sequence (on Go):** read docs\constitution\, docs\scientific_model\, docs\architecture\ (the .md twin) masters in that order → this document's §4+§5 → docs\vv_plan\ master §§1–3; fresh worktree; DEVQ at every ambiguity; the sealed definition is normative.

## 5. H-07 SEALED MECHANICAL DEFINITION v1.0 *(FROZEN; changes = v1.1 by NP-ADR, never edits)*
*Source: `F:\NeelPrajna\repo\Gates\Triggers\T3_SweepFVGGate.mqh` v2.1 pool engine, read from source 2026-07-29. Owner rulings: claim form E2; cost model `xauusd_retail_h07`.*

**Observed events (closed bars only; anti-repaint):**
- **POOL_FORMED** — ≥ pool_min_touches pivot highs (EQH) / lows (EQL) clustered within pool_tol; level FROZEN at formation (average of member pivots), never drifts; rebuilt once per closed anchor bar over pool_lookback.
- **SWEEP** — closed exec bar opens inside the defended side, wicks through the frozen level, closes back (rejection). Gap-through opens are NOT sweeps. Furthest wick tracked as swing extreme.
- **REVERSAL_CONFIRMED** — within mss_max_bars, a closed exec bar closes beyond the pre-sweep swing (extreme of prior swing_lookback closed bars). Its bar is the earliest permissible emission.

**Frozen parameters:** anchor TF H1 · exec TF M1 · pool_lookback 500 H1 bars (cap 2000) · pool_pivot_len 3 · pool_min_touches 2 · pool_tol 0.15×ATR14(H1) · swing_lookback 10 · mss_max_bars 30. *(Source symbols: InpT3_PoolLookback/PoolPivotLen/PoolMinTouches/PoolTolPoints/SwingLookback/MSSMaxBars.)* Trade-blueprint stages (displacement, FVG, OB, tap, entry/TP modes) are prediction-layer playbook, excluded. **DEVQ:** if the 324-trade export ran under non-defaults, halt; re-seal as v1.1.

**Observation Space:** XAUUSD retail feed, broker-tier · mt5_csv/OBS-4 · H1 pools/M1 events, seams from data · regime-conditioned (2024–26 trending gold) · neelprajna family, α-budgeted · events conditioned on POOL_FORMED · Owner-designated seen window · detector v1.0 certified L1–L3 first.

**Claim form E2 (Owner-ruled):** definition trap applies (pool_tol/min_touches buy the base rate → E1 uninformative); testable content = arrangement: does REVERSAL_CONFIRMED follow SWEEP beyond chance timing? **Two-claim structure:** E2 existence — registered+counted NP-S1, judged when N2 certifies; prediction claim — judged NP-S1 by Gen-1 Battery vs random-timing placebo; no phenomenon declared "established" by a prediction-gate verdict.

**Null design N2** (block resampling, seam-preserving, calendar-template): destroys cross-bar arrangement, preserves sessions/volatility character; N1 rotation can't destroy within-day arrangement; N3 reserved as sealed robustness companion. Block length, seeds, thresholds sealed in the YAML before data is touched.

---

## 6. PHASE 1 (cont.) — SPRINT NP-S2: R6 long run + the Observation Engine's NP feed

**Architecture boxes delivered:** Execution feedback → Core (TARGET → BUILT) · Observation Engine (widened)

**Requires:** scoped lab unpause ruling (Owner) — the bridge must run.

**Deliverables:** 3–6 months real-tick collection, Owner-typed withheld-OOS designation **before** collection completes · R6 files run as bridge `experiment` jobs, watchdog-guarded, `preserve`-archived · **NPSU CSV → RecordStore/BulkStore migration**: exports land as hash-chained records with manifests, backward compatibility maintained · execution feedback (fills, outcomes) formalized as Performance Store observations · automated `tests/windows.json` ↔ WindowLedger consistency check.

**Exit:** dataset designated, hashed, untouched beyond designation · data-quality report (gaps/seams/DST computed from data) on record · every NP export reproducible from a manifest · no judging performed this sprint.

## 7. PHASE 2 — THE FAMILY

### SPRINT NP-S3 — Family migration (the 17)
**Architecture boxes delivered:** Pattern Learning (TARGET → BUILT, first NP existence judgments)

Opens with the Owner's ruling on the 17, informed by NP-S1's comparison report: subset, priority, n-floors. Then: **EntryGate and SequenceEngine semantics ported as detectors** (each with planted cases; no shortcuts by origin), sealed registrations, Battery runs as designated data permits, E2 judgments as null machinery certifies, deferrals recorded and priced against the family α-budget. Where a hypothesis needs fresh EA-side evidence, the capture pass produces annotated, provenance-stamped, verdict-drawn PNGs (gated on WO-B).

**Exit:** `neelprajna` is a real, honestly-counted concept family in the ledger; every verdict — PASS, FAIL, or INSUFFICIENT — treated as the result it is; the runtime's own gates unchanged and still executing.

### SPRINT NP-S4 — Acceptance & gate
**Architecture boxes delivered:** none new — this sprint *certifies* everything Phases 1–2 built.

Blinded campaign NB-1..NB-6 per VV_PLAN (Owner holds answer keys; negative-control instrument; tamper drills; stranger audit; interpretation-lock). Then Wave-1 review and Owner boundary rulings: proceed to Phase 3 · Wave 2 · close · or revise.

**Exit:** the integration is an accepted instrument, or the campaign says precisely why not. **Phase 3 does not open without this gate passed.**

## 8. PHASE 3 — THE NERVOUS SYSTEM *(the half the old plan was missing entirely)*

### SPRINT NP-S5 — Contract v2 goes live
**Architecture boxes delivered:** Knowledge+Evidence → runtime (TARGET → BUILT) · Continuous Communication (TARGET → BUILT)

The six object types actually cross, for the first time. **Belief releases** — versioned, dated, verdict-sealed — are published from the BeliefLayer and consumed by the runtime. **AdvisorEngine is re-pointed**: it stops computing beliefs from its own rolling statistics and starts consuming sealed releases. Event-driven publication (a release is an event with a date), never tick-streaming of unsealed figures. The Contract Feed becomes observable for debugging.

**Hard boundary, restated because this is the sprint where it could erode:** the Publication Boundary (Constitution §3, Architecture §4.5) governs every byte that crosses. No rolling win rate. No unsealed statistic. And **arming anything that changes what the real account trades remains a separate, permanently-human decision** — this sprint wires the nervous system; it does not pull any trigger.

**Exit:** a belief release, produced by a real verdict, consumed by the runtime, with the full chain of custody walkable in both directions and machine-checked in IVF.

### SPRINT NP-S6 — Knowledge Graph + Pattern Learning
**Architecture boxes delivered:** Knowledge Graph (TARGET → BUILT) · Statistics & Confidence (enriched)

The beliefs atlas becomes real: per-phenomenon stances, scoped and linked; contradictions surfaced as data for a human to weigh (never auto-resolved); supporting/missing-evidence edges; the next-experiment recommendation. Candidate discovery (Screener/Observatory) formally wired as a question source that produces candidates only — never verdicts.

**Exit:** a populated graph a human can navigate to answer "what do we currently believe, on what evidence, and where does it contradict itself?"

## 9. PHASE 4 — THE SURFACES *(closes the gap found 2026-07-30: both dashboard specs were designed but unscheduled)*

### SPRINT NP-S7 — Research Console (Kernel side)
Build to `docs\specs\QRF_Research_Console_spec_v1.3-amended.md`, read-only v1.0 scope: five lenses (OBSERVE / KNOWLEDGE / DISCOVER / EVIDENCE / GOVERNANCE) + CYCLE, bound to the **real Kernel** per that spec's own v1.3 correction — never to the retired bespoke stack. Its precondition is already satisfied by then: NP hypotheses exist in the real ledger from NP-S1 onward.

### SPRINT NP-S8 — Book A dashboard depth (runtime side)
Build to `docs\specs\NeelPrajna_Live_Advisor_Detail_spec_v1.0.md` (v1.4/v1.5 amendments): Live Advisor card with hysteresis meter, Observation Space panel, Analysis Details grid, plain-language Entry/Exit criteria, Advisor Settings in CTRL, plus the LIVE and VIRT UNIV deep views. **Note:** this sprint touches only display logic over existing StateHub/NPSU fields — its exit check is a byte-identical tester deal list, proving trading was not affected.

*NP-S7 and NP-S8 are independent of each other and may run in either order or in parallel.*

## 10. PHASE 5 — KNOWLEDGE ACCUMULATION (NP-S9+)
**Architecture boxes delivered:** Pattern Evolution (TARGET → BUILT)

Additional concept families beyond `neelprajna`. Hypothesis refinement as new sealed, priced registrations. First mechanism investigations on established phenomena. Principles named only when cross-instrument and cross-regime survival earns them. Machine-proposed hypotheses only after Gate A, per the ratified generation ladder — never before.

## 11. Pre/parallel work orders (details: docs\automation\ master §6)
WO-A doc truth pass · WO-B A4.0 tester-screenshot spike (gates NP-S3 visuals; needs lab unpause) · WO-C cross-repo evidence linkage · WO-D windows-register consistency check.

## 12. SPRINT OUTPUTS (appended at each close — empty is honest)
*(none yet — the first entry here will be NP-S1's: verdict id, comparison-report summary, findings, retro, GO record)*

---

## Change Record
- **v2.0 (2026-07-30):** rewritten after the Owner found v1.0 out of sync with the ratified architecture — correctly. v1.0 planned only NP-S1..S4 and stopped at acceptance, never showing how the two-organ destination gets built. v2.0 adds §1 (the destination, concretely), §2 (the component map), and Phases 3–5 (Contract v2, Knowledge Graph, both dashboards, Pattern Evolution), so that every architecture box has a sprint that turns it from TARGET to BUILT. Structure and the five-phase shape adopted from an external Execution Roadmap draft; its component-*replacement* framing (EntryGates→Detector, AdvisorEngine→BeliefLayer, etc.) was **corrected to integration framing** per Architecture §5 and NP-D-001 — nothing in the runtime is dissolved, only its claims become judgeable. NP-S1 (§4) and the H-07 sealed definition (§5) are carried forward **verbatim and unchanged**, being already ratified and sealed. Also closes the 2026-07-30 finding that both dashboard specs were designed but scheduled nowhere.
- v1.0 (2026-07-29): consolidation per the one-doc-per-thing ruling.

*Anchor: **when no architecture box is still marked TARGET, the architecture is built — and the wall between the organs is exactly where it started.***
