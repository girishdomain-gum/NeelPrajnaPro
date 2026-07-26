# Generation 2 — Execution Roadmap, Wave 1
## Eight sprints from ratification to the first verdicts

Status: **DRAFT — Architect proposal, conditional on the Owner's ratifications.** On ratification this becomes the operational half of ARCH-011 (issued in a declared write window). This roadmap also constitutes the Architect's recommended answer to charter question **Q6** (cadence & roles).
Binding clause carried in from the review board: **after these ratifications, no major architectural additions until RP-001/RP-002 evidence challenges the framework. The market is the next reviewer.**
Companion: all testing, verification, validation, and black-box acceptance content lives in GEN2_VV_ACCEPTANCE_PLAN (same directory). Presentation copies: GEN2_EXECUTION_ROADMAP.docx.

---

## 1. Cadence and roles (Q6 answered)

**Roles: unchanged.** Owner ratifies, declares write windows, holds reserves, rules Go/No-Go. Architect writes ARCHs and owns IVF. Developer implements in fresh sessions, DEVQs at boundaries. The rhythm per sprint is Generation 1's, proven: *instruction → Developer sessions → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → handover rewrite.*

**Cadence: deliberate, not Gen 1's two-day tempo.** Gen 1's sprints shipped machinery; Gen 2's certification sprints (S3–S4) gate everything downstream and must not be rushed — a mis-certified null library poisons every later verdict. Recommendation: sprints complete on quality gates, not clocks; the Owner sets calendar pace at Go/No-Go. One standing tripwire from the charter: **any sprint that produces foundations but no progress toward verdicts is a recorded No-Go finding against the Architect.**

## 2. The eight sprints

```
 S1  RATIFY & SPEAK        S2  MML LIVE           S3  ECF FORGE          S4  ECF CERTIFIED
 constitution · vocabulary  descriptor engine      null library N1/N2     N3 · power curves ·
 · ARCH-011                 · calibration          · first drills         detectors certified
        │                        │                      │                      │
        ▼                        ▼                      ▼                      ▼
 S5  RP-001 JUDGED         S6  RP-002 JUDGED      S7  SYNTHESIS          S8  BLACK BOX & GATE
 MRCG sealed · run ·        PLM sealed · run ·     beliefs document ·     acceptance drills ·
 verdict · beliefs v1       verdict · MCEC null    atlas · wave-2 prep    Wave-1 review ·
                            design task            · Q3 data decision     boundary ruling
```

**Sprint 1 — Ratify & Speak.** Write window: Volume 0, the Constitution (Twelve Principles + P13 Informative Outcomes + Ontological Discipline + the Ethos + permanently-human powers + freeze amendment §6.1 + the VIRGIN Challenge ceremony specification per Q5.4), the MML standard, the ECF design, and the Rejected Concepts Register enter the repo as ratified records; the Owner's rulings become journal entries by the Owner's hand. Then **F1, the primitives session** — the eleven words through the four questions, output sealed — and **F2**, decomposition of every Gen-1 concept into Measurement→Observation→Phenomenon form. ARCH-011 issued. *Exit: constitution ratified, vocabulary sealed, Developer booted.*

**Sprint 2 — MML Live.** Developer implements the descriptor engine: component fractions, decile classifier, simplex feasibility check (infeasible code ⇒ hard error), merge operator, hidden-gate evaluator, suffix grammar. Calibration against planted truth per the V&V Plan (L1 fixtures; L2 IVF parity to the digit on every fixture). Descriptor census over **burned exploration windows only** seeds the Narrow Atlas. *Exit: MML certified; atlas seeded; zero VIRGIN contact.*

**Sprint 3 — ECF Forge.** Null library construction: N1 rotation (session-aware day rotation), N2 block resampling (calendar-template, seam-preserving). First planted-truth drills (injected clustering, manufactured A→B couplings) and clean-control drills, with the drill designs themselves sealed before running. *Exit: N1/N2 running; first drill report; findings tallied.*

**Sprint 4 — ECF Certified.** N3 model-based surrogates (assumptions documented per Volume 0 §0). Injection-calibrated power curves per claim form → **sealed n-floors**. Clean-control false-positive rates at sealed thresholds. IVF parity on every ensemble statistic. Detector certifications: merge/hidden-gate detector and ordinal-k swing detector — knowability contracts verified, DST/weekend boundary tests, monotone-invariance property test for the ordinal detector (log vs raw price must yield identical extrema — the MML/PLM design claims, machine-checked). *Exit: the ECF may judge real claims; certification records GREEN.*

**Sprint 5 — RP-001 judged (MRCG).** Registration sealed **before** the judging window is touched: descriptor set S, windows n ∈ {2,3,5}, claim forms E2+E3, null set, thresholds at family-priced α, event floors from S4's power curves, every outcome's interpretation. Run. Battery rules. IVF re-derives to the last digit. HC samples. Belief record v1 written — whatever the verdict, per Informative Outcomes. *Exit: Generation 2's first phenomenon verdict, reproducible.*

**Sprint 6 — RP-002 judged (PLM).** Same discipline: ordinal-k primary + sealed robustness companion, E2 (revisit/dwell arrangement) + E3 (approach→interaction association), rotation-null primary. Run, rule, verify, record. In parallel, the **MCEC null-design task** registers as a design deliverable (clustering-vs-discrete-states null specification) — designed, not judged. *Exit: second verdict; MCEC's hard problem in progress.*

**Sprint 7 — Synthesis.** The auditable **beliefs document** assembled: per-phenomenon stances, operationalization-scoped, regime-conditioned, α-annotated, negatives included. Atlas entries appended. Contradiction check across all standing records. Sealed **regime-definition design task** delivered (per Q4: trend/flat/bear by mechanical rule, named after definition). Wave-2 candidate list drafted (MCEC if its null certifies; taxonomy-guided successors). The **Q3 decision package** finalized for the Owner (2026 reserve designation; second-instrument deferral confirmation). *Exit: Generation 2 has a knowledge estate, not just verdicts.*

**Sprint 8 — Black Box & Gate.** The full acceptance campaign per the V&V Plan (drill classes BB-1 through BB-6, sealed criteria, single unbroken campaign), then the Wave-1 review: findings tally, retro, Gate-A evidence assessment, and the Owner's boundary ruling — Wave 2, generation close, or framework revision if acceptance demanded it.

## 3. What Sprint 8's Owner ruling decides

With the black box passed: whether Gate-A evidence has begun accumulating (verdicts on the board; hand-work instances recorded), whether Wave 2 opens (MCEC if certified; taxonomy-guided successors), the Q3 data ruling's execution, and the standing question every generation must answer at its boundary — is the strategy mix still right? Per the Constitution: that review is the Owner's, forever.

---
*Anchor: **the dry dock proved the design; the black box proves the instrument; only the market proves the science.***
