# REV — Architect Review of the Complete Backup Corpus (All Three Zips, Including Nested)
*Reviewer: Fable (Architect) · Date: 2026-07-29 · Companion to REV-DeepSeek-Estate (same date). Decisions marked ⚖ require an Owner ruling. Findings follow the house format: claimed / true / species / standing rule.*

---

## Part 1 — Complete inventory

**Zip structure:** `Backup.zip` (original state, ~05:00–07:30 timestamps) → `part2.zip` (corrected state, 08:12, contains a full nested copy of Backup.zip plus corrected files) → `part2-2.zip` (subset: the two corrected volumes + corrections log). The nested `NeelPrajna_Documentation_Redesign.zip` exists in two versions (original / bannered). After hash-deduplication, 23 unique artifacts:

| # | Artifact | Kind | Version state |
|---|---|---|---|
| 1 | QRF_NeelPrajna_Research_Architecture.docx (**Volume I**) | Analysis volume | Original + corrected (errata + 2 diagrams) |
| 2 | NeelPrajna_Vision_to_Verified_System.docx (**Volume II**) | Analysis volume | Original + corrected (errata + 2 diagrams) |
| 3 | QRF_Generation1_Deep_Analysis.docx (**Volume III**) | Analysis volume | Single version (source of corrections) |
| 4 | NeelPrajna_QRF_Integration_Path.docx (**Volume IV**) | Strategy volume | Single version (reviewed previously) |
| 5 | QRF_Architecture_Diagrams.docx | Diagram companion (7 diagrams, real Kernel) | Single version |
| 6 | NeelPrajna_Architecture_Diagrams.docx | Diagram companion (8 diagrams, programme) | Original + corrected (Diagrams 2 & 7 regenerated, 3 annotated) |
| 7 | NeelPrajna_Existing_Implementation_Diagrams.docx | Diagram companion (9 diagrams, as-built EA, Rev 2) | Single version |
| 8 | NeelPrajna_Auto_Adopt_Deep_Audit.docx | Audit addendum | Single version |
| 9–18 | Documentation_Redesign.zip → 10 markdown files (INDEX, DOCUMENTATION_ARCHITECTURE, core/×3, governance/AUTONOMY_LADDER, adr/ADR-008, registers/×2, roadmap/MIGRATION_PLAN, book-a README) | Doc-tree redesign | Original + corrected (banners on the 3 core files) |
| 19 | QRF_Research_Console_spec_v1.0.md | UI spec (amended v1.1→v1.3) | Original (→v1.2) + corrected (v1.3 amendment) |
| 20–22 | qrf_research_console_mockup{,_v1.1,_v1.2}.html | UI mockups | Original + "corrected" — **correction absent, see F-11** |
| 23 | NeelPrajna_Live_Advisor_Detail_spec_v1.0.md (v1.4 amendment) + neelprajna_advisor_detail_mockup.html + neelprajna_live_univ_mockup.html | Book-A dashboard spec + 2 mockups | Single version |
| — | HOW_THIS_DOC_WAS_BUILT.md, CORRECTIONS_LOG_2026-07-29.md | Process docs | Duplicates of loose uploads, reviewed previously |

---

## Part 2 — Document-by-document analysis

### 2.1 Volume I — "Architecture of a Living Scientific Ecosystem" (corrected)
The founding analysis of the organism vision. Its five key findings (separation of knowledge/action as load-bearing wall; Observation Space; concept-after-observation; six-object contract; autonomy as biggest opportunity and risk) all survived contact with the real repository, which is a genuine achievement for a document written before that repository was readable. The §8.2 risk table remains the best short statement of Gen-2/3 dangers in the corpus (multiple-testing explosion, feedback contamination, review bottleneck, spec–implementation drift). The errata is honest and correctly scoped: it moves autonomous discovery from "Gen 2" to Gen 3 per the ratified roadmap without editing the body — the right append-only discipline.
**Residual issues (body, unedited by design, must not propagate):** (a) §6.3/§7 still describe a continuous learning loop in which "every trade refines the knowledge that produced it" and QRF publishes a *recent win rate* to the runtime — this is the seed of the DeepSeek estate's F-2 flaw (unsealed rolling statistics crossing the contract). The Knowledge Publication Boundary proposed in my DeepSeek review is the fix; the new estate must adopt it. (b) §9's roadmap table still shows the pre-errata G2 meaning; a reader who skips the errata will re-learn the corrected error. **Lineage insight:** the DeepSeek estate's reintroduction of the generation error (F-1 of my prior review) is now explained — those documents digest Volume I's *body* without its errata. Root cause identified; the remedy is that all derivative documents must cite the corrected generation ladder, not Volume I §5.

### 2.2 Volume II — "From Vision to Verified System" (corrected)
The strongest analysis document in the corpus. Its contributions are permanent estate assets: the two-clock framing (operations clock vs research-infrastructure clock); the R1–R3 epistemic rules with their real-incident provenance (deterministic vs statistical claims; single-difference A/B; within-run-only comparisons; "picked before the outcome = design, after = fitting"); the ADR-005 Supervisor/Runner analysis with the seven G-invariants and the honest L2 recovery cap; the Phase Ledger reconciliation (three ladders → one, with named supersessions); and the H-07/H-16 stage results (H-07: 324 trades, +0.0763R gross, break-even at 19.0 ticks, gate-clearing at 12.5; H-16: 34,406 trades, break-even 2.0 ticks). Both errata corrections are properly executed with `[CORRECTED]` tags inline plus a dated errata section.
**Carry-forward items:** the Phase Ledger's own top-priority item — the **R6 long run** (3–6 months real-tick data with a withheld OOS window) — remains open and is the single answer to the data-starvation problem (candidate strategies at n=5–23; "nothing promoted survival-first at n<100"). See F-16.

### 2.3 Volume III — "Generation 1, Complete" (ground truth)
The document every other document must now align to. Verified key facts: the nine-step Battery with per-run selftest re-verification and atomic verdict+burn; the four-hypothesis record (H-001 FAIL, H-002 FAIL n=637 p=0.93, H-003 INSUFFICIENT n=28<40, H-004 FAIL p=0.108); family trial accounting at 1,004 counted trials pricing new smc.fvg claims at α≈5×10⁻⁵; the ADR-008 multi-AI protocol with its 21-findings tally (Architect 17, Developer 4); Gates A and B for Gen 3/4; the permanently-human powers list; and the broker-tier-only limitation of the single Independent Observation Lens. Its §7 documentation-hygiene finding (README/CHANGELOG stale at Sprint 2 while Sprint 10 closed) is small, actionable, and still apparently open — fold both into the AI_PROJECT_STATE.md generation step, as it recommends. No defects found in this volume itself.

### 2.4 Volume IV — Integration Path
Reviewed in my previous REV; standing unchanged: it is the strategic spine. The H-07-only first sprint with its gate-by-gate comparison acceptance criterion remains the correct next build. Two of its flagged tasks now graduate into the sprint's mandatory scope: cost-model reconciliation into one `configs/venues.yaml` entry, and window designation for the already-seen H-07 trade population (Owner power — see decision list).

### 2.5 The three diagram companions
**QRF_Architecture_Diagrams** (7 diagrams): clean; built from the real repository from the start; nothing to correct — the corrections log's "left unchanged" entry is accurate. **NeelPrajna_Architecture_Diagrams** (corrected): verified that Diagrams 2 and 7 were regenerated against real module paths and Diagram 3 now honestly states the Communication Contract is a design sketch, not implemented, pointing to Volume IV. Correct. **Existing_Implementation_Diagrams Rev 2** (9 diagrams): a faithful as-built companion; its Diagram 9 + appendix duplicate the Auto-Adopt audit's table verbatim — acceptable duplication since one is the audit and one the atlas, but if either changes the other must, so prefer a pointer in the next revision.

### 2.6 Auto-Adopt Deep Audit — the most operationally consequential document in the corpus
The core finding is exact and verified against its own quoted source: **two switching paths with different safety levels.** Path B (advisory) has eligibility + OOS validation + 3-consecutive-win hysteresis and never acts; Path A (Auto-Adopt) runs every bar even when the advisory module is disabled, applies to the *real account* on the first qualifying evaluation, and is guarded only by rate-based gates (10-trade warm-up, 60-min cooldown) — both satisfiable by variance. The corpus's own evidence (LAST_TRADE +29R then −25R on n=2; run 22078 showing switching did not beat holding) demonstrates the exposure is real, not theoretical. The audit's recommendations (file as DR-012; add ConfirmEvals-style hysteresis to Path A; audit SeqLive.mqh the same way) are all correct and, as far as this corpus shows, **all still open.** See F-13/F-14 — I am elevating the first from a documented observation to an Owner decision.

### 2.7 Documentation Redesign package (10 files, corrected)
The six-folder single-owner structure (core / books / governance / adr / registers / roadmap), the resurrection-test INDEX, the migration plan with byte-preserving SPLIT checks, and above all the two Registers are excellent. The Decision Register and Lesson Register capture exactly the "scar tissue" (LR-001 "looks wired is not wired," LR-002 unstable-sort false positives) that evaporates otherwise — these two files should survive every future reorganization untouched in spirit. The corrected version's banners on the three `core/` files are present and correctly calibrated (verified), including the important EPISTEMIC_RULES clarification that R1–R3 are Book-A conventions, not the real Battery's rules.
**Defect found — see F-12:** the package's `ADR-008-kernel-trading-plugin-split.md` collides with the *real* QRF repository's ADR-008, which is the multi-AI coordination protocol (per Volume III); the real Kernel/plug-in split is QRF's ADR-004. Two repos, same number, different decisions — a citation error waiting to happen.
**Status note:** the Integration Path decision partially supersedes this redesign's original intent (an independent NeelPrajna description of "the Kernel"); the banners already implement the right remedy (pointers, not parallel truth). The remaining migration phases should be re-sequenced behind the H-07 sprint per the inverted plan.

### 2.8 Console spec v1.0–v1.3 and its three mockups
The spec is disciplined design work: the on-chart-vs-browser rationale, five-lens shell, "silence is negative" freshness footer, and the v1.3 amendment's full before/after source-mapping table are all sound. The v1.3 amendment's stated precondition is the key sentence: the console cannot show real NeelPrajna KNOWLEDGE/EVIDENCE data until the hypotheses exist inside the real ledger — which makes the console *downstream of the H-07 sprint*, and it should be parked as DESIGNED until then. The three mockups: see F-11 — the claimed correction banners are absent from the backup and the files are slightly mangled.

### 2.9 Live Advisor spec v1.4 + two Book-A mockups
Grounded end-to-end in real fields (`NPSU-A1/S1/T1`, `AdvisorEngine.mqh`), with unusually good epistemic hygiene for a UI spec: the derived-session footnote, the PF `n<20` guard, the never-paraphrase-the-enum rule, and §1.5's gold Auto-Adopt banner — which directly operationalizes the audit's safety-asymmetry finding in the UI so a human cannot mistake the hysteresis-protected recommendation for the unprotected mechanism that may already have acted. Approve as-designed; implementation should re-verify every field name against the live schemas at build time.

---

## Part 3 — Findings (continuing numbering from the DeepSeek REV)

### F-11 — Claimed mockup corrections are not in the backup; files mangled ⚖ (finding against the Architect)
**Claimed** (CORRECTIONS_LOG §§6–8): all three console mockups gained banners inside `<body>` — red for v1.2's false "real Kernel data" claim, gold notes for v1.0/v1.1 — with a recorded fix-of-a-fix distinguishing the wordings.
**True:** byte-level diff of the part2.zip copies against the originals shows the *only* change in each file is a deleted 7-byte fragment removing the `<body>` tag. No banner exists in any of the three. v1.2 still opens with "GROUNDED IN THE REAL KERNEL CODE… Not hypothetical data anymore," citing NeelPrajna's bespoke scripts — the uncorrected error, live.
**Species:** working-tree state presented as verified record (the F-A standing rule, roles doc §2.2) and/or packaging from a pre-correction tree; either way the log's claim and the artifact disagree, and the repo-wins rule makes that a finding.
**Remedy:** regenerate all three banners (calibrated wordings per the log), restore the `<body>` tags, verify by actually rendering each file, re-hash, and append a correction entry to the corrections log citing this finding. Every markdown/docx correction in the log was independently verified present; only these three HTMLs failed. *(Remedy executed same day — see CORRECTIONS_LOG_ADDENDUM.)*

### F-12 — Cross-repository ADR number collision
NeelPrajna-side `ADR-008` (Kernel/plug-in split) vs. real QRF `ADR-008` (multi-AI protocol); the real split decision is QRF's ADR-004. **Remedy:** namespace ADRs per repository (e.g., `NP-ADR-###` vs `QRF-ADR-###`) or renumber the NeelPrajna-side draft before ratification; add a cross-reference table to the redesign's INDEX.

### F-13 — Auto-Adopt Path A can move real capital on variance today ⚖
Documented, evidenced (n=2 LAST_TRADE swing), and unremediated in this corpus. **Recommendation to the Owner:** either (a) confirm `InpADV_AutoAdopt = NONE` on the real account until Path A gains at minimum the advisory path's ConfirmEvals hysteresis (and preferably an OOS-validated eligibility check), or (b) accept the exposure explicitly on the record as "a strategy under test," with the acceptance dated and signed. Both are legitimate; the current state — exposure documented but neither closed nor accepted — is the only wrong option.

### F-14 — The SeqLive.mqh audit is still open
The Auto-Adopt audit named `SeqLive.mqh` (Phase 6b) as the *second* code path that can change what the real account does, explicitly flagged so it would not be silently assumed equivalent. No artifact in this corpus performs that audit. Schedule it with the same line-by-line, input-group-grep method before any further live-apply feature work.

### F-15 — The continuous-learning/recent-win-rate design must not propagate
Volume I's body (correctly unedited) still specifies rolling statistics and execution-outcome belief updates crossing the contract; the DeepSeek estate inherited it. The Fable-authored estate adopts the Knowledge Publication Boundary (prior REV, F-2 fix) as a constitutional rule, and every derivative document cites the corrected generation ladder, not Volume I §5.

### F-16 — R6 long run: reaffirmed as the highest-value pending data action
Every open statistical question in the EA line (sequence vs static, break-even net effect, B6 additivity, any survival-first promotion) is unanswerable at current n. The H-07 Kernel-integration sprint and the R6 data run are complementary, not competing: H-07 re-judges *existing* evidence through a better instrument; R6 manufactures the *new* evidence everything else is starved of. Recommend running them as the next two sprints in that order (H-07 is smaller and unblocks the console's data path).

**Also carried forward (low effort):** QRF README/CHANGELOG staleness (Volume III §7) — fold into the AI_PROJECT_STATE generation step.

---

## Part 4 — Synthesis: what this corpus changes in my previous review

Nothing in this corpus weakens the prior review's recommendations; three things strengthen them. (1) The DeepSeek estate's F-1 error now has an identified root cause (digesting Volume I's body without its errata), which makes the fix mechanical rather than judgmental. (2) The Integration Path's superiority over a standalone NeelPrajna brain (F-3) is reinforced by the redesign banners' own logic — the project already decided, three files at a time, that parallel descriptions of the Kernel are drift risks. (3) The document-production-trap warning (F-4) is reinforced by the corpus's own weight: this backup contains four analysis volumes, three diagram companions, two UI specs, five mockups, and a ten-file doc tree — and zero new sealed evidence since H-016's stage-4 scan. The next artifact must be a sprint, not a document.

## Part 5 — Consolidated decision list for the Owner ⚖
1. **F-13:** rule on Auto-Adopt — disable pending hysteresis, or accept exposure on the record.
2. **F-11:** authorize the mockup-banner regeneration + corrections-log addendum (Architect executes, IVF-style render check before repackage). *(Executed.)*
3. Prior list, unchanged: Integration-Path architecture as the frozen basis; inverted plan (minimal Level-1 → ARCH-NP-001/H-07 sprint → documents); Knowledge Publication Boundary as constitutional rule; role amendments; **window designation for the H-07 trade population** (permanently-human power).
4. **F-16 sequencing:** approve H-07 sprint then R6 long run as the next two sprints.
5. **F-12:** approve ADR namespacing before any NeelPrajna-side ADR is ratified.

*Anchor: the corpus's discipline is real and mostly verified — but one correction claimed is one correction owed, the one switch that can move real money has the weakest guard in the system, and the next thing this project needs is not its twenty-fourth document but its eleventh sprint.*
