# Corrections Log — 2026-07-29
*Corrections applied to the delivered document estate after the Owner's review of 2026-07-28/29. Append-only; each entry states what was claimed, what was true, what changed, and where. The addendum of the same date (CORRECTIONS_LOG_ADDENDUM_2026-07-29.md) corrects entries 6–8 of this log and must be read with it.*

## 1. Generation ladder error (Volumes I & II; the founding error)

**Claimed:** Generation 2 = "The Autonomous Scientist — the system discovers concepts, humans review."
**True:** the Owner-ratified `ROADMAP_GENERATIONS_2-4.md` places autonomous proposal in **Generation 3** (after Gate A). Generation 2 is *humans propose, machinery labels*. Generation 4 is bounded autonomy (after Gate B).
**Change:** dated errata sections appended to Volume I and Volume II (bodies unedited, per append-only); every derivative document instructed to cite the ratified roadmap, never Volume I §5.
**Where:** QRF_NeelPrajna_Research_Architecture.docx (errata §E1); NeelPrajna_Vision_to_Verified_System.docx (errata §E1).

## 2. "Two-clock" architecture citations aligned

**Claimed:** several passages implied the research clock and operations clock share state directly.
**True:** they are joined only by the Communication Contract's six object types.
**Change:** clarifying errata + `[CORRECTED]` inline tags at the two affected passages in Volume II.
**Where:** NeelPrajna_Vision_to_Verified_System.docx §§4.2, 6.1.

## 3. Diagram regeneration (NeelPrajna_Architecture_Diagrams.docx)

**Claimed:** Diagrams 2 and 7 depicted Kernel modules by imagined names; Diagram 3 presented the Communication Contract as implemented.
**True:** module paths differ in the real repository; the Contract is a design, not code.
**Change:** Diagrams 2 and 7 regenerated against real module paths (`qrf/kernel/records/store.py`, `qrf/kernel/battery/battery.py`, `qrf/kernel/protocol/windows.py`, `qrf/kernel/corrections/trials.py`); Diagram 3 annotated "design sketch — see Integration Path (Volume IV)".
**Where:** NeelPrajna_Architecture_Diagrams.docx (corrected copy).

## 4. QRF_Architecture_Diagrams.docx — no change required

Verified against the repository at review time; built from real code from the start. Left unchanged, recorded here so the absence of a corrected copy is not mistaken for an omission.

## 5. Documentation-redesign core files — correction banners

**Claimed/true gap:** the three `core/` files described a NeelPrajna-local account of "the Kernel" that the Integration Path decision supersedes; EPISTEMIC_RULES presented R1–R3 without scoping them.
**Change:** banner inserted at the top of each of the three core markdown files: pointer to the Integration Path as the frozen basis; R1–R3 scoped as Book-A conventions, not the real Battery's rules.
**Where:** NeelPrajna_Documentation_Redesign.zip (bannered version): core/SYSTEM_OVERVIEW.md, core/ARCHITECTURE.md, core/EPISTEMIC_RULES.md.

## 6. Console mockup v1.2 — false "real Kernel data" claim ⚠ superseded by addendum

**Claimed in this log:** a strong red correction banner was inserted immediately inside `<body>` stating the mockup's data is illustrative and its "GROUNDED IN THE REAL KERNEL CODE" opening is withdrawn.
**Superseding finding (F-11, addendum):** the delivered file contains no banner; the only byte change removed the `<body>` tag. Remedied by regeneration; see the addendum.

## 7. Console mockups v1.0/v1.1 — clarifying notes ⚠ superseded by addendum

**Claimed in this log:** lighter gold notes inserted (these two made no false claim; the note prevents misreading them as live).
**Superseding finding (F-11, addendum):** notes absent in delivered files; remedied by regeneration; see the addendum.

## 8. Fix-of-a-fix: banner wording calibration ⚠ superseded by addendum

**Claimed in this log:** v1.0/v1.1 initially received the strong red wording; corrected to calibrated gold notes so severity tracks culpability.
**Superseding finding (F-11, addendum):** neither wording was present in any delivered file. The calibration described here was applied in the regenerated copies; see the addendum.

## 9. Console spec v1.3 amendment

**Claimed:** spec v1.2's source-mapping described NeelPrajna KNOWLEDGE/EVIDENCE lenses as bindable to current data.
**True:** those lenses have no real data source until NeelPrajna hypotheses exist inside the real ledger (post-migration).
**Change:** v1.3 amendment appended with a full before/after source-mapping table; KNOWLEDGE/EVIDENCE marked "blocked on migration"; the precondition stated in normative text.
**Where:** QRF_Research_Console_spec_v1.0.md (amendment section v1.3).

## 10. Volume III (QRF_Generation1_Deep_Analysis.docx) — source of truth, unchanged

Recorded: Volume III required no corrections and served as the reference against which entries 1–3 were verified.

## Standing rules resulting from this log

1. **Errata over edits:** analysis-volume bodies are never rewritten; corrections are appended, dated, and cross-referenced (P5).
2. **Derivatives cite the ratified record:** generation semantics come from `ROADMAP_GENERATIONS_2-4.md`; any document citing Volume I §5 for generation semantics is defective on its face.
3. **F-A rule (from the addendum):** a claimed correction is verified against the delivered artifact's bytes — render or parse the file — before this log records it as done. The log's word is not evidence; the artifact is.
