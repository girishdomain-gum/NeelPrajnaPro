# NP-ADR-008 — APPENDIX C: numbering-space correction

**Appended under P5. This appendix corrects two factual statements in the body of
NP-ADR-008. It edits nothing, and it changes no normative content: the H-07 Detector
Definition §5 v1.1 and its ratification of 2026-07-30 stand unaltered.**

*Architect role · session: Claude Opus 5, claude.ai · 2026-07-31.*
*Basis: ops/ADR_REGISTRY.md (ARCH-NP-007 T1), filesystem enumeration of all three ADR namespaces.*

---

## C.1 — The NP numbering space is not occupied at 001-007

NP-ADR-008's preamble states:

> "NeelPrajna-side ADRs run 001-007 (NP-ADR-005 = operational autonomy and governance,
> cited in Architecture §5)"

**This is incorrect as a statement about the NP namespace.** A filename and content
scan of the entire repository finds no file claiming any number in `NP-ADR-001`
through `NP-ADR-007`. The NP namespace contained exactly one occupied number - 008,
this document - until 2026-07-31.

The document referred to as "NP-ADR-005 = operational autonomy and governance" is
`docs/books/book-a-neelprajna/reference/adr/ADR-005-operational-autonomy-and-governance.md`.
That file belongs to the **Book A** namespace, which Constitution §5.4 namespaces
separately from `NP-ADR-###`. It is `ADR-005` in its own series and carries no NP
number.

**Corrected statement:** NP-ADR-001 through NP-ADR-007 are FREE. The Book A series
runs 001-008 independently, and the QRF Gen-1 series runs 001-011 independently.
Three namespaces, three sequences, no shared numbering.

### Why this mattered

Three subsequent drafts - the ARO ADR, the organization/roles ADR, and this
document's own predecessor draft - each parked on an unassigned placeholder token
(`0XX`, `0YY`, `0ZZ`) rather than taking a low number, and each cited NP-D-006
collision discipline as the reason. The belief that 001-007 were occupied is the most
likely origin of that caution. It held two finished ADRs out of the ratification queue
for a day.

Recorded plainly: an incorrect factual claim inside a ratified document propagated
into the working practice of three later drafts. The claim was never checked against
the filesystem until ARCH-NP-007.

## C.2 — The `0ZZ` placeholder text in §0 is spent

NP-ADR-008's §0 preamble still reads:

> "Number 0ZZ unassigned pending registry check (NP-D-006)"

while this same document's title and status line declare it sealed as **NP-ADR-008,
RATIFIED 2026-07-30**. Both strings are present in the file simultaneously.

**Corrected statement:** the `0ZZ` token is spent. This document's number is
**NP-ADR-008**, assigned at ratification on 2026-07-30. The registry check the token
awaited was performed on 2026-07-31 (ARCH-NP-007 T1) and is recorded in
`ops/ADR_REGISTRY.md`.

The `0ZZ` token was carried by this document's predecessor draft
(`ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md`), which this document supersedes. That
predecessor retains `0ZZ` permanently as provenance and is assigned no number, under
corrected Rule A of the Architect's ruling of 2026-07-31 (F-29). The lineage
terminates here, at NP-ADR-008.

## C.3 — Number-to-path mapping

This document is named on disk `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md` - a
filename retaining "draft_v2.0" and containing no "008". No file named
`NP-ADR-008*.md` exists as the primary document; only Appendices A, B and this one
carry "008" in their filenames.

**Architect ruling, 2026-07-31: no rename.** Renaming a ratified document breaks every
existing citation to it. The mapping is authoritative and permanent:

> **NP-ADR-008 = `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`**

recorded in `ops/ADR_REGISTRY.md` §3 and here.

## C.4 — What this appendix does not touch

- The §5 v1.1 detector definition: unchanged.
- The ratification of 2026-07-30: stands.
- Appendix A (provenance correction) and Appendix B (pinned detector mechanics):
  unaffected.
- NP-S1 registration against v1.1: remains unblocked.

Nothing in C.1-C.3 bears on whether the detector definition is correct. These are
corrections to this document's claims about the *numbering space it sits in*, not
about the thing it decides.

---
*Anchor: **a ratified document is permanent, not infallible; the remedy is to append the correction where the next reader will find it, never to quietly repair the text.***
