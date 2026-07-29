# Corrections Log — 2026-07-29

Record of every modification made to prior deliverables in this engagement,
and the reason for each. Written as its own document rather than folded
silently into the files it corrects, for the same reason QRF's own ledger
never rewrites history: a correction is itself evidence, and it stays more
useful as a dated, standalone record than as an invisible edit.

**Trigger:** a deep-dive analysis of the real `F:\QRF` repository
(`QRF_docs_export.txt`, `QRF_work_export.txt`) revealed that QRF's
Generation 1 is not a proposal — it is a real, ten-sprint, closed
implementation (RecordStore, EvidenceBattery, WindowLedger, TrialCountLedger,
Observatory, all built and IVF-verified). Several earlier deliverables had
been written before that repository was available, from the abstract
Platform Architecture document or from NeelPrajna's own bespoke scripts —
reasonable at the time, but now known to be incomplete or wrong in specific,
checkable ways. This log is the result of auditing all 14 prior output files
against that new evidence.

**Method used to decide what to touch:** every file was checked for one of
three problems — (1) a factual claim later proven false, (2) a data source
misattributed as "the real Kernel" when it wasn't, or (3) content that would
now duplicate a better original elsewhere. Files with none of these three
were left untouched and are listed at the bottom for completeness.

---

## 1. `QRF_NeelPrajna_Research_Architecture.docx` (Volume I)

**What changed:** appended a dated Errata section (new page 13; the volume
was 12 pages, now 13).

**Reason:** Section 5, *"From Validation to Discovery: Generation 1 →
Generation 2,"* treated Generation 2 as the point where the Kernel begins
autonomously proposing hypotheses — a Screener and Observatory generating
candidates with only human review at the end. That was a faithful reading
of the original architecture vision notes this volume analyzed. It is not,
however, what the real Owner-ratified roadmap says. `ROADMAP_GENERATIONS_2-4.md`
draws the line one generation later:

> Generation 2 — "Knowledge, on labeled foundations." Humans propose,
> machinery labels. Generation 3 — "Supervised discovery." Machines propose,
> humans register. Built only after Gate A.

**What the correction does NOT change:** the volume's core analysis of the
Observation Space, the concept-after-observation ordering, the six-object
Communication Contract, and the Chief Scientist Principle. All four held up
unchanged against the real implementation. Only the generation number
attached to autonomous discovery moved — from 2 to 3 — and the correction
explains why that move is a strengthening of discipline, not a walk-back.

---

## 2. `NeelPrajna_Vision_to_Verified_System.docx` (Volume II)

**What changed:** two claims corrected inline with `[CORRECTED 2026-07-29]`
tags in the risks table (Section 9), plus a dated Errata section appended
(new page 15; the volume was 14 pages, now 15).

**Reason 1 — the "Two-clock drift" risk row.** Originally: *"the QRF Kernel
is specified but its code was not found in this export."* True of the
NeelPrajna export specifically (it contains no Kernel code) but understated
as a description of reality — the Kernel exists, fully built, in a separate
repository, and had already closed an entire Generation 1 (four hypotheses
judged, zero promoted) by the time this was written. Corrected to point at
`QRF_Generation1_Deep_Analysis.docx` for the real account.

**Reason 2 — the belief-gating enforcement row.** Originally recommended
*"confirm the BeliefLayer's update() path is programmatically restricted to
Verdict-typed inputs, not merely documented."* It already is: `battery.py`
is the sole writer of verdict records by construction, and the
Screener/Observatory code paths have no route to a belief update at all —
not a policy that could be violated, a code path that does not exist. The
recommendation is now marked satisfied rather than open.

**What the correction does NOT change:** the volume's central finding —
that NeelPrajna's own engineering discipline (independent verifiers, sealed
evidence, pre-registered predictions) anticipated the Kernel's formal rules
before the Kernel was in reach. The Errata notes this finding is, if
anything, stronger now: two teams converged on the same disciplines
independently.

---

## 3. `NeelPrajna_Documentation_Redesign.zip` — `docs/core/*.md` (3 files)

**Files touched:** `KERNEL_OVERVIEW.md`, `COMMUNICATION_CONTRACT.md`,
`EPISTEMIC_RULES.md`.

**What changed:** each file gained a banner at the top redirecting to the
real `F:\QRF\docs\` tree as the authoritative source, and stating explicitly
that the file's own body is now historical / pre-integration record, not
current truth.

**Reason:** these three files were written to be NeelPrajna's own
description of "the Kernel," authored from the abstract Platform
Architecture document. That was the wrong design the moment a real Kernel
repository with its own excellent, ratified documentation (`docs/architecture/`,
`docs/adr/`, `Architecture_Map.md`) became known. Maintaining a second,
independent description of the same Kernel inside NeelPrajna's own repo is
exactly the "two-clock drift" risk Volume II warned about — a divergence
waiting to happen, not a hypothetical one. The fix is a pointer, not a
rewrite: each file now tells the reader where the real source lives, and
keeps its own body only as a labeled pre-integration sketch.

**Specific note on `EPISTEMIC_RULES.md`:** this file's R1–R3 rules are
NeelPrajna-side conventions (promoted from one MQL5 measurement incident),
not identical to the real Battery's actual enforced rules (a selftest gate,
anchored walk-forward, claim-matched placebo, trial-count deflation). The
banner clarifies these are a Book-A-local supplement, not a substitute, so
a future reader does not mistake NeelPrajna's own rules for the Kernel's.

---

## 4. `NeelPrajna_Architecture_Diagrams.docx`

**What changed:** Diagram 2 image replaced; Diagram 7 image replaced;
Diagram 3 caption and body text annotated; an intro-page correction
paragraph added. Page count unchanged (10 pages) — image swaps, not
insertions, except the one new intro paragraph.

**Reason — Diagram 2 ("Core Kernel Components").** The original used
component names abstracted from the Platform Architecture document
("RecordStore," "BeliefLayer," etc. as generic boxes). Regenerated against
the real `qrf/kernel/` module tree — `records/store.py`, `battery/battery.py`,
`protocol/windows.py`, `corrections/trials.py` — so the diagram now shows
real file paths, not invented ones.

**Reason — Diagram 7 ("The Evidence Pipeline").** The original sketched a
five-path pipeline in the abstract (Detector / Hypothesis / Screener /
Observatory / Belief). The real Battery (`battery.py`) implements a more
specific, more defensive nine-step version — a type check, a selftest gate
re-verified on every run, window checks, anchored splits, an audited
simulator, a claim-matched placebo, trial correction, a tri-state verdict,
and an atomic write of the verdict with its window burn. Replaced with the
diagram built directly from that code (reused from
`QRF_Architecture_Diagrams.docx`, Figure 3).

**Reason — Diagram 3 ("The Communication Contract").** Left as-is visually,
but annotated: there is no implemented Communication Contract between the
real QRF Kernel and NeelPrajna today. This diagram is a design sketch, and
the annotation says so explicitly, pointing to
`NeelPrajna_QRF_Integration_Path.docx` for the concrete, buildable first
step (porting hypothesis H-07 into the real Kernel) that would make it real.

---

## 5. `QRF_Research_Console_spec_v1.0.md`

**What changed:** appended a v1.3 Amendment (the third amendment in this
file, following v1.1 and v1.2 — same file, same append-only convention
throughout its history).

**Reason:** this is the most consequential correction in this pass. The
v1.2 amendment grounded the console's KNOWLEDGE and EVIDENCE lenses in
`np_knowledge_base.py`'s 18-hypothesis founding set and
`np_probability_engine.py`'s seven-gate battery, explicitly describing them
as "real Kernel data" to distinguish them from earlier illustrative mockup
content. That framing was a genuine error, not a simplification: those two
scripts are NeelPrajna's own small, bespoke research tooling — never
IVF-drilled, never planted-fraud-tested, no selftest-gate discipline, no
governance record behind them. They are not the QRF Kernel.

The v1.3 amendment states this plainly, includes a full before/after table
mapping every wrongly-sourced console element to its real Kernel
equivalent (e.g., the pattern table's source corrected from
`np_knowledge_base.py` to `qrf/kernel/records/store.py`; the battery gates
corrected from the bespoke B1–B7 script to the real `battery.py`'s nine
steps), and states the new precondition this creates: the console cannot
show real NeelPrajna KNOWLEDGE/EVIDENCE data until NeelPrajna's hypotheses
actually exist inside the real ledger — a migration that is proposed, not
yet done (see `NeelPrajna_QRF_Integration_Path.docx`).

---

## 6–8. The three companion mockup HTML files

**Files touched:** `qrf_research_console_mockup.html` (v1.0),
`qrf_research_console_mockup_v1.1.html`, `qrf_research_console_mockup_v1.2.html`.

**What changed:** each gained a banner immediately inside `<body>`. The
banners are **deliberately worded differently per file** — this itself is
a correction-of-a-correction worth recording:

- **v1.0 and v1.1** used only illustrative placeholder data (fictional
  pattern IDs like `#a3f9`, no specific source ever claimed for them). No
  factual claim in either file was actually wrong, so each received a
  lighter, gold-toned note: the Kernel these were sketched for is now known
  to be real, and the design shell is still reasonable, but the eventual
  data binding should be the real Kernel's.
- **v1.2** made the specific incorrect claim ("real Kernel data" citing
  NeelPrajna's scripts), so it received the stronger, red-toned correction
  banner naming the error directly.

An earlier pass of this same edit briefly applied the strong red banner to
all three files uniformly before this distinction was drawn; that was
itself corrected within the same session, before publication, once it was
noticed that v1.0/v1.1 had made no false claim to correct. Recorded here so
the fix-of-a-fix isn't lost.

**Reason for keeping the files otherwise unedited beneath the banners:**
matches the append-only, corrections-are-new-records principle this whole
correction pass borrows from QRF's own Generation 1 design — the historical
mockups remain exactly as originally built; the banner is the correction,
not a silent edit to the content below it.

---

## Files audited and left unchanged

For completeness — these were checked against the same three failure modes
and found clean:

| File | Why it needed no change |
|---|---|
| `HOW_THIS_DOC_WAS_BUILT.md` | Process playbook; worked correctly for the QRF diagrams too, no factual claims about either codebase's maturity |
| `NeelPrajna_Existing_Implementation_Diagrams.docx` | Pure MQL5-EA-as-built content; no QRF-related claims at all |
| `NeelPrajna_Auto_Adopt_Deep_Audit.docx` | Same; already superseded by the diagrams doc above regardless |
| `NeelPrajna_Live_Advisor_Detail_spec_v1.0.md` + its 2 mockup HTMLs | Grounded entirely in real NeelPrajna EA code (`AdvisorEngine.mqh`, `MoneyManager.mqh`, `UnivTab.mqh`); no claim about QRF's maturity anywhere in them |
| `QRF_Architecture_Diagrams.docx` | Built *from* the real QRF repository in the first place — nothing in it needed correcting |
| `QRF_Generation1_Deep_Analysis.docx` | Same — this is the source of the corrections, not a target of them |
| `NeelPrajna_QRF_Integration_Path.docx` | Built from the corrected understanding; the baseline the other corrections point back to |

---

## Net effect of this pass

Two analysis volumes now carry dated errata rather than silently-updated
claims. One documentation package now points at a real external source
instead of duplicating an invented one. One diagrams document has two
regenerated figures and one newly-honest caption. One specification has a
named, detailed correction of its most consequential error, with a
before/after table. Three mockups carry banners calibrated to what each
one actually got wrong — including, in two of the three, an explicit
statement that nothing in them was wrong at all, only incomplete relative
to information that did not yet exist when they were built.

---

## Addendum — 2026-07-29 (later the same day): diagrams added to Volumes I and II

**What changed:** four new diagrams added, two per volume, at the points
in each text where a diagram earns its place rather than decorates it.
Neither volume's page count changed by more than the images themselves
require — no restructuring, no rewritten prose.

- **Volume I**, Section 4.3 (The Full Scientific Ladder): a ladder diagram
  (Reality → Instrument → Observations → ... → Knowledge) placed directly
  after the text that already described it, so the ten-rung structure is
  visible, not just narrated.
- **Volume I**, Errata section: a corrected-generation-ladder diagram
  placed directly inside the correction itself — GEN 1 (done) → GEN 2
  (ratified next step) → GEN 3 (what this volume originally called "Gen 2")
  → GEN 4, with a small panel stating plainly what the correction changes
  and what it doesn't.
- **Volume II**, the epistemic-rules section: a diagram of R1–R3 with each
  rule's one-line real-incident evidence, plus the design-vs-fitting test.
- **Volume II**, Errata section: a side-by-side before/after diagram —
  what the volume stated (from the evidence available at the time) on the
  left, what the real F:\QRF repository showed on the right — making the
  nature of the correction (an accurate read of incomplete evidence, not a
  mistake) visible at a glance rather than requiring the prose to carry it
  alone.

**Reason this was worth doing:** both volumes were pure text, including at
points describing highly diagram-friendly structures (a ten-rung ladder, a
four-generation roadmap, a three-rule framework, a before/after
correction) that a reader was previously asked to hold in their head from
prose alone. The two dedicated diagram companions
(`NeelPrajna_Architecture_Diagrams.docx`, `QRF_Architecture_Diagrams.docx`)
cover different content — programme-level architecture and Kernel/sprint
history — not these specific in-text structures, so this was additive, not
duplicated effort.

**Why hand-drawn SVG again, not Figma or Canva:** unchanged from
`HOW_THIS_DOC_WAS_BUILT.md`'s original finding — those tools render an
interactive widget back to the user, not an exportable asset this pipeline
can embed. The same draw-and-rasterize workflow (`diagram_lib.py` →
`rsvg-convert` → `ImageRun`) used for every other diagram in this
engagement was used here.

