# EXECUTION PLAN — the one living document: phases, sprints, and their outputs
*Version 2.0 · 2026-07-30 · Supersedes v1.0 (2026-07-29), which planned only NP-S1..S4 and stopped at acceptance — it never showed how the ratified architecture actually gets built. This version carries the path all the way to the destination. Predecessor preserved in git history. From now on: sprints are planned here, and their OUTPUTS are appended in §9 when they close.*

---

## 0. CURRENT STATE (rewritten at every sprint boundary — this is the handover)
**As of 2026-07-30 — SPRINT NP-S1 IS CLOSED AND ACCEPTED. Owner GO given 2026-07-30 (J-037). NP-S2 IS THE OPEN SPRINT.**

**The number that changed.** Integrated verdicts: **0 → 1**. Verdict `01KYSGQR3D8SYSVJFSF9M77CMY` — **FAIL** · 259 trades · mean net +1.52/oz · p 0.0574 · bar p < 0.00263 (19 family trials) · burn `01KYSGQR6K1HHRT66R78BV6Z8Y`, atomic · window `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)` TRAINING, **spent**. All six acceptance criteria met; IVF GREEN behind a 6/6 drill; HC passed; Chief Scientist REV **APPROVED 8.8/10**.

**THE QUALIFICATION THAT TRAVELS WITH THIS RESULT FOREVER** (Owner-ruled, REV-mandated; quote it, never paraphrase): *Under two independently implemented execution frameworks using different exit mechanics, neither framework produced statistically significant evidence supporting the hypothesis over the designated window.* **NP-S1 did not establish equivalence between the bespoke and Battery execution strategies.** And per NP-ADR-008 §2.1: **no verdict under v1.1 speaks for the historical T3/MSS gate** — which Appendix A established is H-08's, not H-07's.

**Scope limits any reader must carry:** the window was TRAINING, so the verdict is **corroborative, never confirmatory** · the E2 existence claim is registered and counted but **unjudged**, awaiting N2 null machinery · the IVF match demonstrates **text-code fidelity, not independent code correctness** (Appendix B.8) — genuine independence needs a population from a different implementation, which is NP-S2's path.

**NP-S2 opens with a ruled precondition (Owner, 2026-07-30, D2):** **execution-model parity is implemented BEFORE any further R6 evidence collection.** The audited engine must express variable stop distance, variable targets and richer exit rules; until it does, every population it judges inherits NP-S1's primary limitation and every future comparison carries the same qualification. This reorders §6 and is recorded there.

**Standing rule adopted (Owner, 2026-07-30, D3 — NP-D-012):** *any normative specification defining a computation must be sufficient for an independent implementation to reproduce that computation's outputs without consulting the implementation.* Proposed independently by the Architect (Appendix B.9) and the Chief Scientist after three instances surfaced in one sprint.

**Findings are permanent (Owner-ruled):** NP-S1's findings *"remain part of the permanent record and shall not be softened or removed."*

**Open items carried forward:** F-23 (Book A mockup vs Auto-Adopt ruling — bites at NP-S8) · F-24 consequence (Architecture docx twin stale) · non-frozen documentation fixes queued (Architecture §2 and V&V §3.4 "nine steps"; Architecture §3.2 adapter path) · attribution corrections on four ops/DEVQ artifacts · unratified design backlog (ARO ADR, organization/roles ADR, repository autonomy layer, detector-fingerprint ADR) — none blocking.

**Next Owner action:** none until NP-S2's own gates. The Architect opens NP-S2 with the execution-parity work order.

## 1. THE DESTINATION — what "NeelPrajna as per our architecture" concretely means

When every sprint below has closed, this exists:

- **One Observation Engine** feeding both organs — the same detectors, the same EventFrames, the same ledger. No research/production data divergence.
- **The Core (QRF Brain)** holding Scientific Memory, Statistics & Confidence, Pattern Learning, a populated Knowledge Graph, Pattern Evolution, and the drilled EvidenceBattery + WindowLedger that judge everything.
- **Book A (NeelPrajna Runtime)** still executing — TradeManager, MoneyManager, gates, NPSU, the on-chart dashboard — but now *informed by* sealed belief releases instead of by its own private statistics.
- **Contract v2 live between them**: six object types, event-driven releases, nothing else crossing. Knowledge flows toward the runtime; execution feedback flows toward the Brain, as observations only.
- **Two surfaces**: the browser-based Research Console (Kernel side) and Book A's own on-chart dashboard (runtime side), both built to their existing specs.
- **The wall intact, permanently**: *QRF never trades. NeelPrajna never learns on its own.*

**Every sprint below names which architecture box it turns from TARGET to BUILT** — by the row number in §A.1 of the docs\architecture\ master, which is the canonical box column. The docs\vision\ master uses the same rows. That mapping is the plan's own acceptance test: when no row still reads TARGET, the architecture is built.

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

## 4. SPRINT NP-S1 — H-07 twice judged *(**SEALED 2026-07-30 by Owner GO** — instruction text frozen from this point; changes require a new ARCH)*

**Architecture boxes delivered:** row 3 Observation Engine (NP feed, first detector) · row 2 Scientific Memory (first NP records)

**GO RECORD:** Owner typed **"Go"**, 2026-07-30, after all six preconditions were met and recorded. ARCH-NP-001 is sealed with §5's H-07 definition incorporated by reference. The Developer session boots per the boot sequence below.

**Preconditions — ALL MET as of 2026-07-30:** ☑ F-13 ruled (Auto-Adopt NONE) · ☑ cost model named `xauusd_retail_h07` (frozen once cited) · ☑ definition sealed (§5) · ☑ **α-budget ruled 0.05 (Owner-typed 2026-07-30) — per-claim bar at 18 trials: p < 0.0028; deflation recomputed against total family trials at every judgment** · ☑ **window designated TRAINING (Owner-typed 2026-07-30, verbatim): "The XAUUSD market time covered by the H-07 324-trade export is designated TRAINING."** — scope-based per method (b); **the Developer must resolve the exact span from the export and echo it back for Owner confirmation before the registration seals.** The designation BURNS that market time: no later claim may treat it as fresh, and H-07's verdict from it is in-sample — corroborative, never confirmatory.

**Awaiting only: Owner Go / No-Go.** — ✅ **GIVEN 2026-07-30. Sprint is live.**

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

**Architecture boxes delivered:** row 5 Execution feedback → Core (TARGET → BUILT) · row 3 Observation Engine (widened)

**Requires:** scoped lab unpause ruling (Owner) — the bridge must run.

**WO-P · EXECUTION-MODEL PARITY — RULED BY THE OWNER 2026-07-30 (D2) AS A HARD PRECONDITION.** *Before any further R6 evidence is collected*, the audited execution engine shall be extended to express **variable stop distance, variable targets, and richer exit rules**. Rationale, from NP-S1's REV: the engine could not express the evidenced per-trade stop/target, so H-007 was registered with `stop_offset: null, target_offset: null, exit_rule: time_stop` and the Battery judged *sweep-then-hold-12-bars* rather than the evidenced strategy (NOTE-NP-001). Every population judged before parity exists inherits that limitation, and **every comparison built on it carries NP-S1's qualification permanently.** Collecting months of R6 data first would multiply the defect across everything that data later judges. **Exit:** a registration expressing a per-trade variable stop and target round-trips through the engine and reproduces a hand-computed fixture exactly; the `h001` `stop_offset: null` precedent is no longer the only available shape.

**Deliverables (WO-P first, then):** 3–6 months real-tick collection, Owner-typed withheld-OOS designation **before** collection completes · R6 files run as bridge `experiment` jobs, watchdog-guarded, `preserve`-archived · **NPSU CSV → RecordStore/BulkStore migration**: exports land as hash-chained records with manifests, backward compatibility maintained · execution feedback (fills, outcomes) formalized as Performance Store observations · automated `tests/windows.json` ↔ WindowLedger consistency check.

**Exit:** WO-P complete · dataset designated, hashed, untouched beyond designation · data-quality report (gaps/seams/DST computed from data) on record · every NP export reproducible from a manifest · no judging performed this sprint.

**Carried from NP-S1 as the sprint's scientific opportunity:** NP-S1's IVF match demonstrated text-code fidelity, not independent code correctness (Appendix B.8). **Genuine independence requires a population produced by a different implementation** — NP-S2's fresh data is the first chance to provide one.

## 7. PHASE 2 — THE FAMILY

### SPRINT NP-S3 — Family migration (the 17)
**Architecture boxes delivered:** row 6 Pattern Learning (TARGET → BUILT, first NP existence judgments) · row 3 Observation Engine (widened further)

Opens with the Owner's ruling on the 17, informed by NP-S1's comparison report: subset, priority, n-floors. Then: **EntryGate and SequenceEngine semantics ported as detectors** (each with planted cases; no shortcuts by origin), sealed registrations, Battery runs as designated data permits, E2 judgments as null machinery certifies, deferrals recorded and priced against the family α-budget. Where a hypothesis needs fresh EA-side evidence, the capture pass produces annotated, provenance-stamped, verdict-drawn PNGs (gated on WO-B).

**Exit:** `neelprajna` is a real, honestly-counted concept family in the ledger; every verdict — PASS, FAIL, or INSUFFICIENT — treated as the result it is; the runtime's own gates unchanged and still executing.

### SPRINT NP-S4 — Acceptance & gate
**Architecture boxes delivered:** none new — this sprint *certifies* everything Phases 1–2 built.

Blinded campaign NB-1..NB-6 per VV_PLAN (Owner holds answer keys; negative-control instrument; tamper drills; stranger audit; interpretation-lock). Then Wave-1 review and Owner boundary rulings: proceed to Phase 3 · Wave 2 · close · or revise.

**Exit:** the integration is an accepted instrument, or the campaign says precisely why not. **Phase 3 does not open without this gate passed.**

## 8. PHASE 3 — THE NERVOUS SYSTEM *(the half the old plan was missing entirely)*

### SPRINT NP-S5 — Contract v2 goes live
**Architecture boxes delivered:** rows 7 Knowledge + Evidence → runtime and 8 Continuous Communication (both TARGET → BUILT)

The six object types actually cross, for the first time. **Belief releases** — versioned, dated, verdict-sealed — are published from the BeliefLayer and consumed by the runtime. **AdvisorEngine is re-pointed**: it stops computing beliefs from its own rolling statistics and starts consuming sealed releases. Event-driven publication (a release is an event with a date), never tick-streaming of unsealed figures. The Contract Feed becomes observable for debugging.

**Hard boundary, restated because this is the sprint where it could erode:** the Publication Boundary (Constitution §3, Architecture §4.5) governs every byte that crosses. No rolling win rate. No unsealed statistic. And **arming anything that changes what the real account trades remains a separate, permanently-human decision** — this sprint wires the nervous system; it does not pull any trigger.

**Exit:** a belief release, produced by a real verdict, consumed by the runtime, with the full chain of custody walkable in both directions and machine-checked in IVF.

### SPRINT NP-S6 — Knowledge Graph + Pattern Learning
**Architecture boxes delivered:** row 9 Knowledge Graph (TARGET → BUILT) · row 4 Statistics & Confidence (enriched)

The beliefs atlas becomes real: per-phenomenon stances, scoped and linked; contradictions surfaced as data for a human to weigh (never auto-resolved); supporting/missing-evidence edges; the next-experiment recommendation. Candidate discovery (Screener/Observatory) formally wired as a question source that produces candidates only — never verdicts.

**Exit:** a populated graph a human can navigate to answer "what do we currently believe, on what evidence, and where does it contradict itself?"

## 9. PHASE 4 — THE SURFACES *(closes the gap found 2026-07-30: both dashboard specs were designed but unscheduled)*

### SPRINT NP-S7 — Research Console (Kernel side)
**Architecture box delivered:** row 11 Surface — Research Console (TARGET → BUILT)

Build to `docs\specs\QRF_Research_Console_spec_v1.3-amended.md`, read-only v1.0 scope: five lenses (OBSERVE / KNOWLEDGE / DISCOVER / EVIDENCE / GOVERNANCE) + CYCLE, bound to the **real Kernel** per that spec's own v1.3 correction — never to the retired bespoke stack. Its precondition is already satisfied by then: NP hypotheses exist in the real ledger from NP-S1 onward.

### SPRINT NP-S8 — Book A dashboard depth (runtime side)
**Architecture box delivered:** row 12 Surface — Book A Dashboard (depth TARGET → BUILT)

Build to `docs\specs\NeelPrajna_Live_Advisor_Detail_spec_v1.0.md` (v1.4/v1.5 amendments): Live Advisor card with hysteresis meter, Observation Space panel, Analysis Details grid, plain-language Entry/Exit criteria, Advisor Settings in CTRL, plus the LIVE and VIRT UNIV deep views. **Note:** this sprint touches only display logic over existing StateHub/NPSU fields — its exit check is a byte-identical tester deal list, proving trading was not affected.

**MOCKUP CORRECTION REQUIRED BEFORE BUILD (finding 2026-07-30).** `docs\specs\mockups_book_a\neelprajna_advisor_detail_mockup.html` predates the F-13 Auto-Adopt ruling and depicts a state the Owner has since ruled against. Two places:
- **Line ~337, Advisor Settings dropdown:** shows `2: highest account value (net R)` as the **selected** option. The ratified default is `InpADV_AutoAdopt = NONE`. **The built UI must default to NONE**, not to any active criterion. This is the binding correction.
- **Line ~153, Live Advisor banner:** shows `AUTO-ADOPT is ACTIVE (EQUITY)`. This is *defensible as design communication* — the mockup's own caption says "the banner is the point," and demonstrating a conditional safety banner requires depicting the condition that fires it. **Keep the banner mechanism; it is a safety feature.** But the mockup should be annotated so no reader mistakes the illustration for the ruled default.

The second Book A mockup (`neelprajna_live_univ_mockup.html`) was checked and is clean — no Auto-Adopt dependency. Console mockups are unaffected (Kernel-side).

**Standing rule this creates:** mockups are DESIGNED-tier and non-normative, but a mockup that contradicts a ratified ruling is a trap for whoever builds from it later. Before any sprint builds from a mockup, that mockup is checked against the rulings in force, and any conflict is named in the sprint instruction — as here.

*NP-S7 and NP-S8 are independent of each other and may run in either order or in parallel.*

## 10. PHASE 5 — KNOWLEDGE ACCUMULATION (NP-S9+)
**Architecture box delivered:** row 10 Pattern Evolution (TARGET → BUILT)

Additional concept families beyond `neelprajna`. Hypothesis refinement as new sealed, priced registrations. First mechanism investigations on established phenomena. Principles named only when cross-instrument and cross-regime survival earns them. Machine-proposed hypotheses only after Gate A, per the ratified generation ladder — never before.

## 11. Pre/parallel work orders (details: docs\automation\ master §6)
WO-A doc truth pass · WO-B A4.0 tester-screenshot spike (gates NP-S3 visuals; needs lab unpause) · WO-C cross-repo evidence linkage · WO-D windows-register consistency check.

## 12. SPRINT OUTPUTS (appended at each close — empty is honest)

### NP-S1 — H-07 twice framed, once judged · CLOSED AND ACCEPTED 2026-07-30

**GO record (Owner, verbatim):** *"NP-S1 is GO. The sprint is closed and accepted. NP-S2 shall proceed with execution-model parity being implemented before additional R6 evidence collection. The specification-completeness standing rule is adopted... The findings recorded for NP-S1 remain part of the permanent record and shall not be softened or removed. The NP-S1 verdict is accepted within its documented scope and limitations."*

**The verdict.** `01KYSGQR3D8SYSVJFSF9M77CMY` — **FAIL**. 259 trades over 4 fold TEST ranges · mean net **+1.52/oz** · one-sided p **0.0574** · deflated bar **p < 0.00263** (19 family trials, α 0.05) · gross−net = 0.41 exactly, confirming the ratified cost model applied · fold means +3.19, +3.79, +0.49, −1.72 · burn `01KYSGQR6K1HHRT66R78BV6Z8Y`, atomic with the verdict · window `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)` TRAINING, **spent**. **The FAIL is robust to the sprint's most contested arithmetic:** p exceeds even the undeflated 0.05, so the 19-vs-18 trial ruling could not have changed it.

**Comparison report (AC-4).** `docs/coordination/notes/NOTE-NP-002_*`. Top-line agreement (both FAIL) with **seven divergences named by cause**, and the honest core: the two instruments **test substantially non-overlapping criteria** — B4–B7 are *unjudged by the real Battery, not corroborated* — while disagreeing on **expectancy sign** (bespoke negative OOS, Battery positive-but-insignificant) and running **different trade rules entirely**. **REV-mandated narrowing, §7, to be quoted not paraphrased:** *Under two independently implemented execution frameworks using different exit mechanics, neither framework produced statistically significant evidence supporting the hypothesis over the designated window.*

**Definition sealed.** NP-ADR-008 (§5 v1.1) + Appendix A (Gate 7/Gate 8 provenance) + Appendix B (pinned mechanics). **§5 v1.0 remains frozen and unedited.** Lineage `h007_np_liquidity_sweep_v1_1` · detector `neelprajna.liquidity_sweep@1.1.0` · family `xauusd/neelprajna` · scope `xauusd_m5_vantage` · cost model `xauusd_retail_h07` @ $0.41/oz.

**Verification.** IVF: drill 6/6 planted frauds caught with a silent control · full chain re-derived to 1e-9 · first pass **RED** (correctly) on two of four unchecked items · re-check after Appendix B reproduced **3,099 pivots / 465 pools / 325 sweeps exactly, no tuning** · **GREEN**, qualified as text-code fidelity. HC passed (Owner). REV **APPROVED 8.8/10**.

**The four discoveries worth more than the verdict.**
1. **The export was made by a structurally different detector than the sealed definition** — caught before registration, resolved by ADR rather than silent adjustment.
2. **`T3_SweepFVGGate.mqh` says "was Gate 8"** — §5 v1.0 documented a hybrid of H-07's absorbed pool engine and H-08's mandatory MSS/FVG chain. **H-07's true original is deleted and unrecoverable**, making the v1.1 detector its best surviving expression.
3. **The family string is load-bearing** — sibling families don't match in `deflation.py`, so a per-detector string would have voided the α-budget silently.
4. **A sealed definition two honest readers implement differently is not yet a definition** — 6 events wide, localized to pool formation, closed by Appendix B.

**Findings (permanent, Owner-ruled).** Against the Architect: "nine steps" propagated into three documents unsourced · §4/§5 mischaracterized the bespoke verdict as cost-sensitivity-only (it was five-gate) · a lineage recommendation violating the repository's own convention · requiring "verbatim" text without supplying it · signing artifacts with another session's name · **three prompts referencing repository state the recipient could not yet fetch** · naming B.5 as the recount culprit when it was B.3 and B.4. Structural, no name: **three normative texts could not reproduce their own outputs without reading code** — now closed by NP-D-012.

**Working as designed.** Four sessions independently refused to act on state they could not verify. The Developer found the Gate 7/Gate 8 misattribution unprompted and calibrated verifiable claims against unverifiable ones. **The IVF returned RED on the Architect's own instruction and was right.**

**Retro — what to change.** (a) An instruction naming repository state must name **the commit that contains it**. (b) Assumptions must be disclosed at the **granularity where two implementers could differ** — "full suppression" was disclosed; *which value is compared* was not, and that was the bug. (c) Decision records are committed **the same day** they are approved. (d) Verbatim requirements ship with the quotable string. (e) Design work stays off the critical path while a sprint is in flight — fifteen documents were produced on the day the first verdict was earned.

**Score.** Documents at sprint open: ~30, integrated verdicts 0. At close: **integrated verdicts 1**, and the answer is **no**.

---

## Change Record
- **v2.0 (2026-07-30):** rewritten after the Owner found v1.0 out of sync with the ratified architecture — correctly. v1.0 planned only NP-S1..S4 and stopped at acceptance, never showing how the two-organ destination gets built. v2.0 adds §1 (the destination, concretely), §2 (the component map), and Phases 3–5 (Contract v2, Knowledge Graph, both dashboards, Pattern Evolution), so that every architecture box has a sprint that turns it from TARGET to BUILT. Structure and the five-phase shape adopted from an external Execution Roadmap draft; its component-*replacement* framing (EntryGates→Detector, AdvisorEngine→BeliefLayer, etc.) was **corrected to integration framing** per Architecture §5 and NP-D-001 — nothing in the runtime is dissolved, only its claims become judgeable. NP-S1 (§4) and the H-07 sealed definition (§5) are carried forward **verbatim and unchanged**, being already ratified and sealed. Also closes the 2026-07-30 finding that both dashboard specs were designed but scheduled nowhere.
- v1.0 (2026-07-29): consolidation per the one-doc-per-thing ruling.

*Anchor: **when no architecture box is still marked TARGET, the architecture is built — and the wall between the organs is exactly where it started.***
