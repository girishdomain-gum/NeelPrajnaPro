# ADR Registry — enumeration only

*DERIVED, operational metadata. Zero epistemic standing. This document assigns nothing
and judges nothing — it enumerates what exists on disk. Number assignment is an
Architect decision (Roles §2.4: the Developer does not author ADRs). No file was
renamed, moved, or renumbered to produce this registry.*

Generated per `ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md` Task 1.

Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.

**Updated 2026-07-31** (same session date, second pass): STATUS and SUPERSEDED_BY
columns added, and the NP-namespace number assignment below applied, per the
Architect's ruling on `DEVQ-NP-005` (`docs/coordination/inbox/CLOSED/DEVQ-NP-005_arch_np_007_task3_no_output_file.md`).
Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.

**Corrected 2026-07-31** (same session date, third pass): NP-ADR-011 WITHDRAWN. The
Architect's follow-up ruling on `DEVQ-NP-005` corrects the original Rule A (recorded
as F-29 against the Architect) and withdraws the NP-ADR-011 assignment made in the
second pass. See "Correction — 2026-07-31 (third pass): NP-ADR-011 WITHDRAWN (F-29)"
at the end of this document. No prior row above is rewritten; this is an appended
correction (P5).
Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.

---

## Method note (F-27 compliance)

Before trusting a "no collisions" result in any namespace, the method was run against
the QRF namespace first, which is known to contain two collisions (ADR-009, ADR-010).
The method (list files in the directory, sort by declared/filename number, flag any
number held by more than one file) surfaced both known collisions. See §1. The same
method was then applied unchanged to Book A and NP. It surfaced a third collision in
Book A (§2) that was not previously flagged in this instruction. It found no numeric
collision in the NP namespace, but did find three files sharing unassigned
placeholder tokens (0XX/0YY/0ZZ) rather than numbers — reported in §3.

**SUPERSEDED_BY method note (2026-07-31 pass):** the original Task 3 sweep (case-
insensitive search for "supersed") was scoped to `ops/` only — it did not cover
`docs/archive/gen1/adr/` or `docs/books/book-a-neelprajna/**/adr/`. Before populating
SUPERSEDED_BY for §1 and §2 below, the same search was run against both of those
directories for this update. QRF (§1): zero matches. Book A (§2): four matches, all
read in context; none is a document declaring **itself** superseded by another file —
one is a hypothetical future ADR mentioned inside `ADR-001`, one describes evidence-
bundle file versioning inside `ADR-005`, one describes a rejected alternative inside
`ADR-002`, and one (`ADR-004-evaluation-cadence.md`, "Superseded by §6") is an internal
cross-reference to a later section of the *same* document, consistent with that file's
own recorded status ("AMENDED 2026-07-23 after measurement — see §6"). SUPERSEDED_BY is
therefore "none" for every §1 and §2 row, checked rather than assumed.

---

## §1 — QRF (Gen-1) namespace: `docs/archive/gen1/adr/`

14 files scanned.

| Number | Slug | File | Status (verbatim) | STATUS | SUPERSEDED_BY |
|---|---|---|---|---|---|
| 001 | documentation-policy | `ADR-001-documentation-policy.md` | `Accepted · 2026-07-24 · Owner: Architecture` | ACCEPTED | none |
| 002 | append-only-ledger | `ADR-002-append-only-ledger.md` | `Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)` | ACCEPTED | none |
| 003 | manifest-pattern | `ADR-003-manifest-pattern.md` | `Accepted · 2026-07-24 · Owner: Implementation` | ACCEPTED | none |
| 004 | kernel-firewall | `ADR-004-kernel-firewall.md` | `Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)` | ACCEPTED | none |
| 005 | two-speed-simulation | `ADR-005-two-speed-simulation.md` | `Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)` | ACCEPTED | none |
| 006 | independent-verification | `ADR-006-independent-verification.md` | `Accepted · 2026-07-24 · Owner: Verification` | ACCEPTED | none |
| 007 | generated-state | `ADR-007-generated-state.md` | `Accepted · 2026-07-24 · Owner: Ops` | ACCEPTED | none |
| 008 | multi-ai-coordination | `ADR-008-multi-ai-coordination.md` | `Accepted · 2026-07-24 · Owner: Owner + Architecture` | ACCEPTED | none |
| **009** | research-program-track | `ADR-009-research-program-track.md` | `Accepted · 2026-07-24 · Owner: Owner + Architecture` | ACCEPTED | none |
| **009** | visual_evidence_layer | `ADR-009_visual_evidence_layer.md` | `Accepted · 2026-07-25 · Proposed by: Owner (Girish) · Drafted by: Architect` | ACCEPTED | none |
| **010** | observational-neutrality | `ADR-010-observational-neutrality.md` | `Accepted · 2026-07-25 · Owner: Owner + Architecture` | ACCEPTED | none |
| **010** | supervised_autopilot | `ADR-010_supervised_autopilot.md` | `Accepted · 2026-07-25 · Proposed by: Owner (Girish) · Drafted by: Architect` | ACCEPTED | none |
| 011 | trial-accounting | `ADR-011.md` | `ACCEPTED · Author: architect (fable) · Owner-approved (ARCH-010 §1, retro-count YES) · Implemented: HypothesisRegistry.register (S10), scripts/retro_trials_s10.py · Verified: DEVQ-024 REPLY, IVF-S10 check §A.` | ACCEPTED | none |
| — (unnumbered register, not an ADR) | REJECTED_CONCEPTS_REGISTER | `REJECTED_CONCEPTS_REGISTER.md` | `DRAFT for ratification alongside the Constitution. Append-only once ratified; entries are Records.` | DRAFT | none |

### §1 collision: ADR-009 (two files) — KNOWN, resolved by letter suffix

Both files are titled `ADR-009` in their own headers and both declare `Accepted`. This
instruction's boot prompt names this as a known, already-resolved collision. The
resolution is recorded elsewhere in the repo, not in either ADR-009 file itself:
`docs/decisions/NeelPrajnaPro_Decisions-v1.0.md` lines 23 and 25 name them, verbatim:
- `QRF-ADR-009a · Research program track.` → `ADR-009-research-program-track.md`
- `QRF-ADR-009b · Visual evidence as a standing verification layer.` → `ADR-009_visual_evidence_layer.md`

### §1 collision: ADR-010 (two files) — KNOWN, resolved by letter suffix

Both files are titled `ADR-010` in their own headers and both declare `Accepted`.
Resolution, verbatim from `docs/decisions/NeelPrajnaPro_Decisions-v1.0.md` lines 27 and 29:
- `QRF-ADR-010a · Observational neutrality (permanent principle).` → `ADR-010-observational-neutrality.md`
- `QRF-ADR-010b · Supervised autopilot — phased automation with a drilled human gate.` → `ADR-010_supervised_autopilot.md`

No suffix assignment (`a`/`b`) is stated inside the ADR-009 or ADR-010 files themselves —
only in the separate Decisions document. This registry does not assign or infer letters;
it reports where the existing assignment is recorded.

---

## §2 — Book A namespace: `docs/books/book-a-neelprajna/**/adr/`

Two `adr/` directories exist under Book A. Per this instruction's `**` glob they are one
namespace. 9 files scanned.

| Number | Slug | File | Status (verbatim) | STATUS | SUPERSEDED_BY |
|---|---|---|---|---|---|
| 001 | statehub-eventbus-portfolio | `reference/adr/ADR-001-statehub-eventbus-portfolio.md` | `Accepted (owner-approved, 2026-07-21)` | ACCEPTED | none |
| 002 | dashboard-strategy-interaction | `reference/adr/ADR-002-dashboard-strategy-interaction.md` | `Accepted (owner-approved, 2026-07-21)` | ACCEPTED | none |
| 003 | sequence-engine | `reference/adr/ADR-003-sequence-engine.md` | `Accepted direction — design pending (owner-approved, 2026-07-22)` | ACCEPTED (design pending) | none |
| **004** | amendment-summary | `reference/adr/ADR-004-amendment-summary.md` | *(file states no status line of its own; opens "One-page companion to `ADR-004-evaluation-cadence.md` §6. Written 2026-07-23, after the v5.9.0 twin measurement (run 40906).")* | NONE DECLARED (companion doc) | none |
| **004** | evaluation-cadence | `reference/adr/ADR-004-evaluation-cadence.md` | `Accepted (constraint recorded), 2026-07-23; AMENDED 2026-07-23 after measurement — see §6.` | ACCEPTED (AMENDED) | none |
| 005 | operational-autonomy-and-governance | `reference/adr/ADR-005-operational-autonomy-and-governance.md` | `ACCEPTED — owner ruling recorded 2026-07-27 (§9)` | ACCEPTED | none |
| 006 | git-job-type | `reference/adr/ADR-006-git-job-type.md` | `PROPOSED — awaiting owner ruling (§8)` | PROPOSED | none |
| 007 | evidence-preservation | `reference/adr/ADR-007-evidence-preservation.md` | `ACCEPTED — owner ruling recorded 2026-07-27 (§10). ... No items remain open.` | ACCEPTED | none |
| 008 | kernel-trading-plugin-split | `docs_redesign/adr/ADR-008-kernel-trading-plugin-split.md` | `PROPOSED — awaiting owner ratification` | PROPOSED | none |

### §2 collision: ADR-004 (two files) — NOT previously flagged in this instruction

Both files live in `reference/adr/` and both are titled `ADR-004`. Unlike the QRF-009/010
case, `ADR-004-amendment-summary.md` self-describes as a **companion**, not a competing
decision: verbatim, "One-page companion to `ADR-004-evaluation-cadence.md` §6. ... Read
this first, the ADR has the full working." `ADR-004-evaluation-cadence.md` is the ADR
proper; `ADR-004-amendment-summary.md` is its summary annex, sharing its number rather
than contesting it. Reported here as a fact (two files, one number, same directory);
this registry does not judge whether that makes it a "real" collision — only that the
QRF-009/010-style search surfaces it and the QRF cases do not self-describe this way,
so the two situations are not identical in kind.

No other duplicate numbers found in this namespace (001, 002, 003, 005, 006, 007 each
have exactly one file; 008 appears once, in the other of the two `adr/` directories).

---

## §3 — NP namespace: `ops/NP-ADR-*`, and any other `NP-ADR-*` occurrence

Search performed two ways: (a) filename glob `*NP-ADR*` repo-wide, (b) content grep for
the string `NP-ADR` repo-wide (to catch mentions/cross-references, listed separately at
the end of this section, not as registry entries — a mention is not a file).

Filename-glob results — 7 files, all under `ops/`:

| Number/token | Slug | File | Status (verbatim, from the file's own title/preamble) | STATUS | SUPERSEDED_BY |
|---|---|---|---|---|---|
| **008** | H07 Detector Definition §5 v1.1 (RATIFIED text) | `NP-ADR-H07_definition_v1.1_draft_v2.0.md` | Title: `NP-ADR-008 — H-07 Detector Definition §5 v1.1 · RATIFIED 2026-07-30`. Body: `Status: RATIFIED 2026-07-30 by the Owner. ... NP-S1 registration is UNBLOCKED against v1.1.` | RATIFIED | none |
| — (appendix to 008) | Appendix A — provenance correction | `NP-ADR-008_APPENDIX-A_provenance_correction.md` | Title line: `**ACCEPTED 2026-07-30**` | ACCEPTED | none |
| — (appendix to 008) | Appendix B — pinned detector mechanics | `NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md` | *(file states no explicit status line; the appendix is framed as "Appended under P5" and does not declare ACCEPTED/RATIFIED/DRAFT anywhere in the text scanned)* | NONE DECLARED | none |
| **NP-ADR-009** (assigned 2026-07-31, Architect ruling on DEVQ-NP-005; was `0XX`) | ARO — Research Orchestrator | `NP-ADR-ARO_draft_v1.0.md` | `WORKING RECORD — DRAFT v1.0 for Chief Scientist review and Owner ratification ... Number 0XX deliberately unassigned pending a registry check against docs\archive\gen1\adr\ — collision discipline per NP-D-006` | DRAFT (never ratified) | none |
| **NP-ADR-011** (assigned 2026-07-31, Architect ruling on DEVQ-NP-005; was `0ZZ`) | H07 definition v1.1, draft v1.0 | `NP-ADR-H07_definition_v1.1_draft_v1.0.md` | `WORKING RECORD — Architect-role draft, 2026-07-30 ... Number 0ZZ unassigned pending registry check (NP-D-006). No normative document edited by this draft.` | DRAFT (never ratified) | **NOT self-declared.** `NP-ADR-H07_definition_v1.1_draft_v2.0.md` (NP-ADR-008) claims, one-directionally, to supersede this file ("Supersedes `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`"). This file itself contains no "supersed"-family text anywhere. Asymmetric case — see the dedicated flag below. |
| `0YY` (**retained permanently — Rule A**: self-declared SUPERSEDED, never ratified, consumes no number) | Model-Agnostic Roles (draft, superseded) | `NP-ADR-model_agnostic_roles_draft_v1.0.md` | Header banner: `SUPERSEDED 2026-07-30 by ops\NP-ADR-organization_and_roles_v1.0.md ... Retained for provenance only — never ratified, never cited.` Title: `NP-ADR-0YY (DRAFT, SUPERSEDED)` | SUPERSEDED (self-declared), DRAFT, never ratified | `ops/NP-ADR-organization_and_roles_v1.0.md` (self-declared; successor verified to exist and to carry no SUPERSEDED banner of its own) |
| **NP-ADR-010** (assigned 2026-07-31, Architect ruling on DEVQ-NP-005; was `0YY`) | Organization, Roles and Assignments (final package) | `NP-ADR-organization_and_roles_v1.0.md` | `Status: FINAL DRAFT for Chief Scientist review → Owner ratification, Constitution §7.3. Number 0YY unassigned pending registry check (NP-D-006).` | DRAFT (never ratified) | none |

### §3 notes — no numeric collision, but flagged discrepancies

1. **Placeholder reuse, not a numbering collision.** Two files carried the token `0YY`:
   the superseded draft and its final-draft successor. This was the same ADR lineage
   (draft → final draft) declaring the same pending number twice, not two competing
   ADRs contesting one number. Reported per the instruction's "flag every collision"
   requirement; this registry does not characterize it as equivalent to QRF-009/010.
   Resolved 2026-07-31 by number assignment below — the successor now carries
   NP-ADR-010; the superseded draft keeps `0YY` permanently under Rule A and is
   assigned no number.
2. **Title/filename mismatch on NP-ADR-008.** The file whose own title declares it to
   be `NP-ADR-008, RATIFIED` is named on disk `NP-ADR-H07_definition_v1.1_draft_v2.0.md`
   — the filename retains "draft_v2.0" and contains no "008". No file named
   `NP-ADR-008*.md` exists as the primary document; only the two appendix files
   (`NP-ADR-008_APPENDIX-A...`, `NP-ADR-008_APPENDIX-B...`) carry "008" in their
   filenames. **Architect ruling (2026-07-31): no rename** — renaming a ratified
   document breaks every existing citation to it. This registry is the record of the
   number-to-path mapping: **NP-ADR-008 = `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`
   on disk, permanently, filename notwithstanding.**
3. **Stale placeholder text survives sealing.** `NP-ADR-H07_definition_v1.1_draft_v2.0.md`
   §0 preamble still reads "Number 0ZZ unassigned pending registry check (NP-D-006)"
   even though the document's own title and status line elsewhere declare it sealed as
   NP-ADR-008. Both strings are quoted verbatim above and in this note; this registry
   does not resolve the discrepancy, only reports both statements as they stand in the
   file.
4. **A fourth placeholder token, not a file.** `ops/ARO_Architecture_Review_NP.md` line
   135 refers to a future ADR by the token "NP-ADR-00X" — this is a mention inside a
   review document, not a filename, and is not counted as a registry entry.

### Asymmetric supersession — priority finding (flagged, not resolved here)

Two files in `ops/` are named by a successor's own preamble as superseded, but do not
themselves carry any "SUPERSEDED"/"supersed" text — a reader opening either file directly
sees an ordinary document with no warning attached:

- **`ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md`** (now NP-ADR-011) — claimed successor:
  `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s (NP-ADR-008) own preamble: *"Supersedes
  `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`."* `draft_v1.0.md` itself contains no
  "supersed"-family text anywhere.
- **`ops/DEVELOPER_BOOT_NP-S1.md`** (outside the ADR namespaces; surfaced by the same
  ops/-wide sweep, included here for completeness) — claimed successor:
  `ops/DEVELOPER_BOOT_NP-S1_RESUME.md`'s own preamble: *"Supersedes
  `ops\DEVELOPER_BOOT_NP-S1.md` for all work from this point."* `DEVELOPER_BOOT_NP-S1.md`
  itself contains no "supersed"-family text at all.

Both predecessor files remain live citation traps as of this update — no banner has been
added to either. Per the Architect's instruction, adding that banner text is reserved to
the Architect and is not done in this pass.

### Occupied vs. free NP numbers

- **Occupied:** NP-ADR-**008** (H07 Detector Definition §5 v1.1, RATIFIED),
  NP-ADR-**009** (ARO draft, DRAFT, assigned 2026-07-31), NP-ADR-**010**
  (Organization/Roles final draft, DRAFT, assigned 2026-07-31), NP-ADR-**011** (H07
  draft v1.0, DRAFT, assigned 2026-07-31).
- **Permanently retired, no number:** `0YY` as carried by
  `NP-ADR-model_agnostic_roles_draft_v1.0.md` — self-declared SUPERSEDED, never
  ratified, retained for provenance only (Rule A, Architect ruling 2026-07-31).
- **Free:** NP-ADR-001 through NP-ADR-007, and NP-ADR-012 onward. No file anywhere in
  the repository claims any number in this range under the `NP-ADR-*` name. One
  document — `NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s own preamble — asserts
  "NeelPrajna-side ADRs run 001–007 (NP-ADR-005 = operational autonomy and governance,
  cited in Architecture §5)"; this appears to refer to Book A's
  `reference/adr/ADR-005-operational-autonomy-and-governance.md` (§2 above), not to a
  file literally named `NP-ADR-005`. No such file exists. This registry reports the
  discrepancy between that preamble's claim and what is actually on disk without
  resolving it — the claim and the filesystem scan disagree, and only the filesystem
  scan is enumerated here as fact.

---

## Number assignment — Architect ruling, 2026-07-31 (DEVQ-NP-005 reply)

Applied mechanically, per the Architect's rules:

> Rule A. A document that declares itself SUPERSEDED and was never ratified keeps its
> placeholder permanently. It is provenance-only and consumes no number. Do not assign
> one.
>
> Rule B. Live drafts take the next free NP numbers.

| Placeholder | File | Self-declares SUPERSEDED? | Rule applied | Result |
|---|---|---|---|---|
| `0XX` | `NP-ADR-ARO_draft_v1.0.md` | No | B | **NP-ADR-009** |
| `0YY` (live) | `NP-ADR-organization_and_roles_v1.0.md` | No | B | **NP-ADR-010** |
| `0YY` (dead) | `NP-ADR-model_agnostic_roles_draft_v1.0.md` | Yes (self-banner, never ratified) | A | retains `0YY`, no number |
| `0ZZ` | `NP-ADR-H07_definition_v1.1_draft_v1.0.md` | No (asymmetric case — successor claims supersession, this file does not self-declare) | B | **NP-ADR-011** |

No ADR file was edited to insert its number. This table and the §3 table above are the
only record of the assignment; per the Architect's instruction, inserting the number
into each ADR file's own text is reserved to the Architect.

---

## Summary table

| Namespace | Files scanned | Numbers occupied | Collisions found |
|---|---|---|---|
| QRF (Gen-1) | 14 | 001–011 | 2 (ADR-009, ADR-010 — both known/already resolved) |
| Book A | 9 | 001–008 | 1 (ADR-004 — not previously flagged; self-described as companion, not contest) |
| NP | 7 | 008, 009, 010, 011 (as of 2026-07-31) | 0 numeric; 1 placeholder-token reuse (0YY, same lineage, resolved by number assignment above) |

*(The NP row above is the second-pass figure. It is corrected below — not rewritten
here, per P5.)*

---

## Correction — 2026-07-31 (third pass): NP-ADR-011 WITHDRAWN (F-29)

**This section corrects, by appending — it does not edit — the "Number assignment"
table, the "Occupied vs. free NP numbers" list, and the Summary table's NP row, all
above, all dated 2026-07-31 (second pass). Where this section's figures disagree with
those above, this section is the current record; the earlier text is left in place as
the provenance of the withdrawn assignment (P5).**

**F-29 (against the Architect, per the Architect's own ruling):** the original Rule A
tested self-declaration ("a document that declares itself SUPERSEDED and was never
ratified keeps its placeholder permanently"). The asymmetric case this registry itself
flagged in §3 ("Asymmetric supersession — priority finding") is exactly where
self-declaration fails: `NP-ADR-H07_definition_v1.1_draft_v1.0.md` is named as
superseded by its successor's own preamble but carries no self-banner. Under the
original Rule A this file tested "No" on self-declaration and fell to Rule B, taking
**NP-ADR-011**. The Architect ruled that test wrong.

**Rule A, corrected (Architect ruling, 2026-07-31):**
> A document that is superseded — whether or not it says so — and was never ratified
> is provenance-only and consumes no number. Supersession is established by any
> document naming it superseded, not by self-declaration. Where a lineage terminates
> in a ratified document, that number covers the lineage; predecessor drafts take
> none.

**Applied:**

| Placeholder | File | Superseded (by any naming, corrected test) | Rule applied | Result |
|---|---|---|---|---|
| `0ZZ` | `NP-ADR-H07_definition_v1.1_draft_v1.0.md` | Yes — named superseded by `NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s (NP-ADR-008) own preamble: *"Supersedes `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`."* Lineage terminates in NP-ADR-008, RATIFIED. | A (corrected) | **NP-ADR-011 WITHDRAWN.** Retains `0ZZ` permanently. No number assigned. |

**NP-ADR-009 and NP-ADR-010 stand — no change.** Neither `NP-ADR-ARO_draft_v1.0.md`
(0XX) nor `NP-ADR-organization_and_roles_v1.0.md` (0YY, live) is named superseded by
any document under either the original or the corrected Rule A test; Rule B applied to
both, unaffected by this correction.

**Occupied vs. free NP numbers — corrected, 2026-07-31 (third pass):**
- **Occupied:** NP-ADR-**008** (H07 Detector Definition §5 v1.1, RATIFIED),
  NP-ADR-**009** (ARO draft, DRAFT), NP-ADR-**010** (Organization/Roles final draft,
  DRAFT).
- **Permanently retired, no number:** `0YY` (`NP-ADR-model_agnostic_roles_draft_v1.0.md`
  — self-declared SUPERSEDED, never ratified) and, as of this correction, `0ZZ`
  (`NP-ADR-H07_definition_v1.1_draft_v1.0.md` — named superseded by its successor,
  never ratified). Both provenance-only under corrected Rule A.
- **Free:** NP-ADR-001 through NP-ADR-007, and NP-ADR-011 onward. **NP-ADR-011 is free
  again** — it was assigned to `NP-ADR-H07_definition_v1.1_draft_v1.0.md` in the
  second pass above and is withdrawn by this correction; it is not reused for anything
  else in this pass, and the next assignment to occupy it is a future Architect
  decision.

No ADR file was edited by this correction, and no supersession banner was added to
`NP-ADR-H07_definition_v1.1_draft_v1.0.md` — both reserved to the Architect per this
ruling. `NP-ADR-H07_definition_v1.1_draft_v2.0.md` (NP-ADR-008, RATIFIED) was not
touched.

Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.
