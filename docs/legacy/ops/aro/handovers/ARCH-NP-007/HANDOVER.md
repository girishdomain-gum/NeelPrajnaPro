# HANDOVER · ARCH-NP-007 · Developer → Architect

Role: Developer · Session: Claude Sonnet 5, Claude Code CLI · Completed: 2026-07-31 ·
Commits: `ec1a039`..`2e0288d` on `maint/adr-registry` (branched from `origin/main@8ad7bab`)

---

## 1. What was asked

Enumerate three ADR namespaces (QRF Gen-1, Book A, NP) into a registry with zero
epistemic standing; produce a factual, non-evaluative extraction of six named
design-stack documents (headings, self-declared status, self-declared blockers,
cross-references, ratification triggers, word count/mtime); report every file in
`ops/` that declares itself SUPERSEDED and verify each chain; do it all on a new
branch off main, touching nothing outside four named scope files, and prove that with
`git diff --stat`. No code changes, no test runs, no renumbering, no judgment calls
about which ADR number should go where.

## 2. What I did

Branched `maint/adr-registry` from `origin/main` (main was checked out in the sibling
worktree, so I based directly on `origin/main` rather than a local `git checkout main`
— same result, no local `main` touched). Wrote the boot prompt verbatim into
`ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md` (Task 0) and committed it
first, per instruction, so every later commit is checkable against it.

For Task 1, scanned all three namespaces by directory listing plus filename/content
grep, read every file's own header for its self-declared status, and — per the
F-27 method-validation rule — ran the collision-detection method against the QRF
namespace first (it surfaced both known collisions, ADR-009 and ADR-010, before I
trusted it on Book A and NP). That same method then surfaced a **third, previously
unflagged collision** in Book A (`ADR-004`, two files) and clarified that the NP
namespace has zero numeric collisions but three files sharing unassigned placeholder
tokens (`0XX`/`0YY`/`0ZZ`), plus a title/filename mismatch on the one ratified NP-ADR
(the file titled `NP-ADR-008` is not named `NP-ADR-008*.md` on disk).

For Task 2, read all six named files in full and extracted headings, status lines,
self-declared blockers, cross-references (verified by exact-filename grep both ways,
not just skimmed), ratification triggers, word counts, and last-commit dates.

For Task 3, ran a case-insensitive sweep of "supersed" across every `.md` in `ops/`
(14 files matched), then manually classified each match as self-declaration,
successor-declaration, or incidental use. Found the two self-declared cases (one of
them, `ARO_Execution_Process_v1.0.md`→`v2.0.md`, not previously named in the
instruction) plus two asymmetric cases where a successor claims supersession but the
predecessor carries no matching self-banner.

**Before writing Task 3's findings anywhere**, I hit a scope gap: the instruction's
SCOPE list names no output file for Task 3. Per the instruction's own rule ("if scope
and acceptance criteria conflict, raise a DEVQ, do not silently pick one"), I filed
`DEVQ-NP-005` and, pending an answer, provisionally appended Task 3's report as a
labeled section at the end of `ops/DESIGN_STACK_INVENTORY.md` (a file already in
scope) rather than inventing a new path.

## 3. What changed

| File | Change |
|---|---|
| `ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md` | New. Verbatim copy of the boot prompt (Task 0). |
| `ops/ADR_REGISTRY.md` | New. QRF/Book A/NP namespace enumeration, collision flags, occupied/free NP numbers (Task 1). |
| `ops/DESIGN_STACK_INVENTORY.md` | New. Six-file extraction (Task 2) + provisionally-placed supersession-chain report (Task 3). |
| `docs/coordination/inbox/OPEN/DEVQ-NP-005_arch_np_007_task3_no_output_file.md` | New. Scope-gap DEVQ (see §6). |
| `ops/aro/handovers/ARCH-NP-007/HANDOVER.md` | This file. |
| `docs/coordination/sessions/SNP-M2-01_2026-07-31_ARCH-NP-007.md` | This session's log (committed alongside this handover). |

No other file was modified. Proof:

```
$ git diff --stat main...maint/adr-registry
 docs/coordination/inbox/OPEN/DEVQ-NP-005_arch_np_007_task3_no_output_file.md |  49 +++
 ops/ADR_REGISTRY.md                                                         | 171 +++++++++
 ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md                  | 123 ++++++
 ops/DESIGN_STACK_INVENTORY.md                                               | 416 +++++++++++++++++++++
 4 files changed, 759 insertions(+)
```
(Run before this handover and the session log were added; both are additive, in-scope,
new files and do not change the stat's shape — only its file count, from 4 to 6, all
still inside the SCOPE list.)

## 4. Decisions I made

- **Branched off `origin/main` directly instead of `git checkout main` first.** The
  instruction's literal BRANCH steps assume `main` isn't already checked out
  elsewhere; in this worktree it was (a sibling worktree owns it). `git checkout -b
  maint/adr-registry origin/main` reaches the identical tip commit without touching
  the other worktree's checkout — no rule violated, "do not touch main" honored more
  strictly than the literal steps required.
- **Placed Task 3's findings inside `ops/DESIGN_STACK_INVENTORY.md`, provisionally,
  rather than picking a standalone path.** Authority: none granted — this is exactly
  the DEVQ-worthy ambiguity the instruction itself names, so I raised DEVQ-NP-005 and
  chose the least-committal option (append to an already-in-scope file, invent no new
  path) while waiting.
- **Reported the Book A `ADR-004` duplicate as a collision despite the file's own
  self-description as a "companion," not a competing decision.** Task 1 says "flag
  every collision" without qualification; I flagged it, but also quoted the file's own
  companion-framing verbatim rather than characterizing it as equivalent to the
  QRF-009/010 pattern — reporting the fact without asserting a judgment the instruction
  reserves for the Architect.
- **Did not resolve or comment on the ADR_REGISTRY.md's own internal contradiction**
  (`NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s preamble still says "0ZZ unassigned"
  under a title that says "NP-ADR-008, RATIFIED") — reported both verbatim strings as
  they stand, per the instruction's "report verbatim... do not infer" rule.

## 5. What I did NOT do

- Did not renumber, rename, or move any ADR, NP-ADR, or design-stack file.
- Did not run pytest, or touch any file under `qrf/`, `tests/`, `datastore/`, `ivf/`,
  or any existing normative document — this session changes no code, per the
  instruction's own "if you find yourself wanting to run pytest, that is a signal you
  have gone outside scope."
- Did not edit `maint/gen1-cleanup` or any file ARCH-NP-006 might touch — no such
  branch or file was read or written this session.
- Did not merge to `main`. Branch `maint/adr-registry` is pushed and sits ahead of
  `origin/main` only by this session's five commits.
- Did not resolve DEVQ-NP-005 myself — it is filed open, awaiting the Architect.

## 6. Open questions

- **DEVQ-NP-005** (`docs/coordination/inbox/OPEN/DEVQ-NP-005_arch_np_007_task3_no_output_file.md`):
  the instruction's SCOPE list names no file for Task 3's output. I provisionally
  appended it to `ops/DESIGN_STACK_INVENTORY.md`; confirm or redirect.
- Not filed as a separate DEVQ, but worth the Architect's attention when next
  assigning NP-ADR numbers: `ops/ADR_REGISTRY.md` §3 notes that NP-ADR-001 through 007
  are asserted (by `NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s own preamble) to be
  occupied by "NeelPrajna-side ADRs," but no file on disk under that literal name
  exists in that range — only Book A's separately-namespaced `ADR-005` matches by
  number and subject. This is reported as a discrepancy in the registry, not resolved.

## 7. Evidence of DoD

- All four Task 0–2/3(provisional) files committed and pushed; `git diff --stat
  main...maint/adr-registry` shown in §3, matching (plus the DEVQ and this
  handover/session-log pair, all inside SCOPE).
- Collision-detection method validated against the QRF namespace before being trusted
  on Book A/NP (F-27 compliance) — documented in `ops/ADR_REGISTRY.md`'s "Method note."
- Every status/blocker quotation in `ops/ADR_REGISTRY.md` and
  `ops/DESIGN_STACK_INVENTORY.md` is a verbatim excerpt with its source file named;
  every "no cross-reference found" claim was produced by an exact-filename grep run
  both directions, not by skimming.
- No test suite run this session (correctly, per the instruction — this session
  changes no code).

## 8. What the next role must do

- Rule on DEVQ-NP-005 (confirm or redirect Task 3's placement).
- Decide NP-ADR number assignment for the three pending placeholders (`0XX` = ARO,
  `0YY` = Organization/Roles, `0ZZ` = H07 draft v1.0, already superseded within its own
  lineage) — explicitly an Architect decision per Roles §2.4, not attempted here.
- Decide whether the Book A `ADR-004` duplicate (companion vs. collision) needs the
  same letter-suffix treatment QRF-009/010 received, or is fine as-is given its
  self-declared companion relationship.
- Decide whether the `NP-ADR-008` title/filename mismatch (ratified content living in
  a file still named `..._draft_v2.0.md`) should be corrected, and by whom — this
  Developer session made no rename per the instruction's "enumeration only" rule.

## 9. How to verify me

```bash
git fetch origin
git log --oneline origin/maint/adr-registry -5
git diff --stat main...maint/adr-registry
# Expect exactly the 6 files listed in §3 (4 generated/instruction/DEVQ files +
# this handover + the session log), zero changes elsewhere.
```
Every quoted status/blocker/cross-reference string in `ops/ADR_REGISTRY.md` and
`ops/DESIGN_STACK_INVENTORY.md` can be independently re-checked with `grep -n
"<quoted string>" <named file>` — all are exact excerpts, not paraphrases.

## 10. Risks / uncertainties

- **DEVQ-NP-005 is unresolved.** If the Architect wants Task 3's report in a different
  file, `ops/DESIGN_STACK_INVENTORY.md`'s final section will need to move — flagged
  clearly at both ends (the DEVQ itself and a placement note at the top of that
  section) so this is not a silent assumption.
- **The "0XX"/"0YY"/"0ZZ" placeholder scheme and the "NeelPrajna-side ADRs run 001–007"
  claim in `NP-ADR-H07_definition_v1.1_draft_v2.0.md` were reported as-is; I did not
  attempt to trace whether that claim is a stale artifact from an earlier drafting
  pass or reflects a numbering intention that exists nowhere else on disk.** This
  registry treats the filesystem as ground truth over that one sentence, per the
  instruction's "the filesystem scan is enumerated here as fact" standard — worth the
  Architect's independent check.
- **Word counts use `wc -w`** (whitespace-delimited tokens), not a prose-word
  estimator; markdown table pipes and punctuation inflate the count slightly relative
  to a reader's intuitive "word." Reported as a raw, reproducible number, not a
  stylistic judgment.
