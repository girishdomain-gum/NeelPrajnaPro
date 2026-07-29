# NeelPrajna × QRF — Integration Execution Roadmap, Wave 1
## Four sprints from ratification to a migrated, verdicted family

Status: **DRAFT — Architect proposal, conditional on the Owner's ratifications** (Constitution v2.0, Scientific Model v2.0, Platform & Integration Architecture v2.0). On ratification this becomes the operational half of **ARCH-NP-001** (issued in a declared write window). Companion: all testing, verification, validation, and acceptance content lives in NP_INTEGRATION_VV_ACCEPTANCE_PLAN (same directory). Presentation copy: NP_INTEGRATION_EXECUTION_ROADMAP.docx.

**Relationship to the Gen-2 track (cross-track ruling embedded):** this roadmap runs as a parallel track to GEN2_EXECUTION_ROADMAP's S1–S8 and is the direct execution of the Generation 1 Final Report's Recommendation 1 and 2 — *build knowledge, not framework; new families over deeper mining*. The `neelprajna` concept family arrives exactly as Gen-1 prescribed: family + detectors + sealed hypotheses — an application, not a subsystem. **Critically, NP-S1 and NP-S2 depend only on Generation-1-certified machinery** (the existing Battery, WindowLedger, TrialCountLedger, IVF); they need nothing from Gen-2's new MML/ECF certification sprints (S2–S4) and may therefore run in parallel with them. The one shared dependency is Gen-2 S1 (Ratify & Speak): both tracks boot from the same ratification write window. ARCH numbering is namespaced (ARCH-NP-###) per Constitution v2.0 §5.4 to avoid collision with Gen-2's ARCH-011+ sequence — a rule adopted after the Architect committed exactly that collision, and tallied it.

---

## 1. Cadence and roles

**Roles: unchanged and shared with the QRF tracks.** Owner ratifies, declares write windows, types window designations, holds reserves and α-budgets, rules every Go/No-Go. Architect writes ARCH-NP instructions and owns IVF. Developer implements in fresh sessions on worktrees, DEVQs at boundaries. Independent Reviewer and Data & Research Analyst participate relay-only per Constitution v2.0 §5.2. The rhythm per sprint is Generation 1's, proven: *instruction → Developer sessions → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → handover rewrite.*

**Cadence: quality gates, not clocks.** The Owner sets calendar pace at each Go/No-Go. Standing tripwires: (a) any sprint that produces documents but no progress toward a verdict or toward the R6 dataset is a recorded No-Go finding against the Architect; (b) any evidentiary use of the retired bespoke stack (`np_probability_engine.py` as judge, `np_knowledge_base.py` as ledger) is a finding against whoever invoked it.

## 2. The four sprints

```
 NP-S1  H-07 TWICE-JUDGED       NP-S2  R6 LONG RUN            NP-S3  FAMILY MIGRATION       NP-S4  ACCEPTANCE & GATE
 detector certified · H-07      3–6 months real-tick ·        Owner ruling on the 17 ·      NP-family acceptance drills ·
 sealed · real Battery run ·    withheld OOS window ·         detectors + registrations     console unblock ruling ·
 gate-by-gate comparison        designation ceremony          for approved subset ·         Wave-1 review · findings tally ·
                                                              verdicts as data permits      boundary ruling
        │                              │                             │                              │
        ▼                              ▼                             ▼                              ▼
 first NP verdict in the        the data every open            the family exists in the      the integration is an
 real ledger                    question is starved of         ledger, honestly counted      accepted instrument
```

**Sprint NP-S1 — H-07, twice judged.** The full ARCH-NP-001 scope: the `neelprajna.liquidity_sweep` detector implemented to the standard contract and certified against its planted-truth and clean-control cases before observing anything real; H-07 registered as a sealed Hypothesis YAML on the Owner-designated window (seen data — TRAINING or EXPLORATION, never VIRGIN); one real EvidenceBattery run; the gate-by-gate comparison report against the bespoke B1–B7 result (its recorded verdict: FAIL on cost sensitivity); the remaining 17 founding hypotheses entered as counted attempts in the TrialCountLedger — registrations only, no runs. Preconditions (block start): Owner's window designation typed; family α-budget set; cost-model reconciliation ruled into one frozen `configs/venues.yaml` name; the standing Auto-Adopt ruling recorded. *Exit: Generation-quality NP verdict on the board, reproducible; comparison report ruled on; family trial count ≥18.*

**Sprint NP-S2 — R6 long run.** The Phase Ledger's own highest-value pending item, executed at last: 3–6 months of real-tick data collection with a withheld out-of-sample window, designated by the Owner's typed phrase **before** collection completes (reserve-by-market-time: the hours are reserved, not the file). The EA side runs its already-shipped R6 files; the QRF side receives the export through the existing mt5_csv adapter path into designated windows. No judging in this sprint — this sprint manufactures the evidence every open question (sequence-vs-static, break-even net effect, B6 additivity, survival-first promotion at n≥100) is currently starved of. *Exit: the dataset exists, designated, hashed, untouched beyond its designation; a data-quality report (gaps, seams, DST boundaries verified from data) is on the record.*

**Sprint NP-S3 — Family migration.** Opens with the Owner's ruling, informed by NP-S1's comparison report: which of the remaining 17 hypotheses proceed, in what priority, under what per-hypothesis n-floors. For the approved subset: detectors written and certified one by one (each with planted cases; no shortcuts by origin), sealed registrations, Battery runs as designated data permits — including, where the Owner rules it, first claims against R6 exploration windows. Deprioritized hypotheses are recorded with reasons in the Rejected/Deferred register, priced by the family α-budget. *Exit: the neelprajna family is a real, honestly-counted concept family in the ledger, with every verdict — PASS, FAIL, or INSUFFICIENT — treated as the result it is.*

**Sprint NP-S4 — Acceptance & gate.** The NP-family acceptance campaign per the V&V Plan (drill classes NB-1 through NB-5, sealed criteria, single unbroken campaign) — including the negative-control instrument run of the full NP program on a synthetic series where every claim must return NOT ESTABLISHED or INSUFFICIENT. Then the Wave-1 review: findings tally, retro, and the Owner's boundary rulings: (a) does the Research Console's KNOWLEDGE/EVIDENCE unblock now that real NP records exist (Console spec v1.3's precondition satisfied or not); (b) does live consumption of any belief release by the runtime enter design (Contract v2 semantics, Publication Boundary enforced — a DESIGN decision only; arming anything real remains its own permanently-human ruling under Architecture §6); (c) Wave 2, close, or framework revision. *Exit: the integration is an accepted instrument, or the acceptance campaign has said precisely why not.*

## 3. What NP-S4's Owner ruling decides

With acceptance passed: the console unblock; the shape of runtime consumption design work, if any; whether NP hypotheses judged on R6 virgin-tier windows begin contributing to any future promotion conversation (independence-tier and regime-honesty caveats from the Gen-1 Final Report §5 restated alongside every such verdict); and the standing generation-boundary question — is the strategy mix still right? Per the Constitution: that review is the Owner's, forever.

## 4. Cross-track synchronization points

| Point | NP track | Gen-2 track | Rule |
|---|---|---|---|
| Ratification write window | NP-S1 boot | S1 boot | One window, both charters; Owner's hand only |
| Battery / IVF machinery | Consumes as-is | Consumes as-is | Frozen; any change re-triggers V&V on both tracks |
| TrialCountLedger | neelprajna family | MRCG/PLM families | Same ledger; families priced independently |
| VIRGIN reserves | R6 OOS window | Q3 2026 designation | Separate designations, same ceremony, same typed hand |
| Findings tally | Shared | Shared | One tally, all voices, kept by the Owner |
| Wave-1 reviews | NP-S4 | S8 | May converge into one boundary session at the Owner's option |

---
*Anchor: **the family arrives the way Gen 1 said all knowledge must — a detector, a seal, a verdict — and the first thing it proves is whether two judges agree.***
