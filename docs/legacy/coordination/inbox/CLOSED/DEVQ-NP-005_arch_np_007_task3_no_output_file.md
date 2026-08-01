# DEVQ-NP-005 — ARCH-NP-007 Task 3 has no designated output file (scope/DoD conflict)

Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.

## The conflict

`ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md`'s SCOPE section names
exactly four scoped artifacts:

```
Generated ops metadata:  ops/ADR_REGISTRY.md, ops/DESIGN_STACK_INVENTORY.md
Instruction record:      ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md
Handover:                ops/aro/handovers/ARCH-NP-007/HANDOVER.md
Session log:             docs/coordination/sessions/SNP-M2-01_2026-08-xx_ARCH-NP-007.md
```

Task 3 ("supersession chain") is a distinct enumerated task with its own acceptance
criteria (report every file in `ops/` that declares itself SUPERSEDED; verify the named
successor exists and does not itself declare supersession) — but no file is named for
its output anywhere in SCOPE. DONE WHEN item 1 says "Tasks 0-3 complete, all four files
committed and pushed," which counts four files total across four tasks, reinforcing that
no fifth file was intended for Task 3's findings — yet Task 3's own instructions describe
a "Report" as a deliverable, which under the RULES section's *"Report verbatim"* standard
reads as expecting a written artifact, not merely an in-session mention.

Per this instruction's own RULES: *"If scope and acceptance criteria conflict, that is a
defect in this instruction — raise a DEVQ, do not silently pick one."* This is exactly
that case, so it is raised here rather than resolved silently.

## What I did pending an answer

I did not silently pick a location and move on without flagging it. To avoid stalling
Tasks 0-2/4 on this single ambiguity, I have **provisionally** appended Task 3's findings
as a clearly labeled, separate top-level section at the end of `ops/DESIGN_STACK_INVENTORY.md`
(a file already inside SCOPE), rather than creating any new file outside SCOPE. Rationale
for that provisional placement, offered for correction: both self-declared-SUPERSEDED
cases found in the `ops/`-wide sweep involve documents directly inside or adjacent to the
six-file design-stack set already covered by that file (`ARO_Execution_Process_v1.0.md`
→ `v2.0.md`, the latter one of the six named files; and `NP-ADR-model_agnostic_roles_draft_v1.0.md`
→ `NP-ADR-organization_and_roles_v1.0.md`, the latter also one of the six). No new file
was created for this purpose, and nothing outside the named SCOPE list was written to.

## Question for the Architect

Is appending Task 3's report to `ops/DESIGN_STACK_INVENTORY.md` the intended resolution,
or should Task 3's findings live in their own file (and if so, what path — none is named
in SCOPE) or in `ops/ADR_REGISTRY.md` instead? This does not block Tasks 0, 1, 2, or 4,
which proceed independently; it blocks only a confident final placement of the Task 3
content, which is provisionally in place pending this answer.

---

## REPLY · Owner/Architect ruling, relayed this chat · 2026-07-31

**Status: CLOSED.**

**1 · Placement confirmed as-is.** Task 3's report stays where it was provisionally
placed, in `ops/DESIGN_STACK_INVENTORY.md`. No move, no rewrite. The Architect's
ruling, verbatim: *"Your provisional placement was right and churning a committed
derived file to satisfy a table I wrote badly costs more than it buys."*

**2 · The defect was in the instruction, not the response.** Verbatim: *"ARCH-NP-007
§4 specified four artifact classes and four tasks, and never mapped T3 to one. You
filed instead of guessing, which is the behaviour the DEVQ mechanism exists for."*
Recorded on the Architect's side as **F-28**.

**3 · Consequential ruling — `ADR_REGISTRY.md` gains STATUS and SUPERSEDED_BY
columns**, populated from the Task 3 sweep (extended, for this pass, to also check
QRF and Book A for self-declared supersession, which the original ops/-scoped sweep
had not covered — zero found in either). Applied in the same commit as this reply;
see `ops/ADR_REGISTRY.md`.

**4 · Number assignment — Architect ruling, applied mechanically:**
- Rule A: a document that self-declares SUPERSEDED and was never ratified keeps its
  placeholder permanently and consumes no number.
- Rule B: live drafts take the next free NP numbers.
- Result: `NP-ADR-ARO_draft_v1.0.md` (was `0XX`) → **NP-ADR-009**.
  `NP-ADR-organization_and_roles_v1.0.md` (was `0YY`) → **NP-ADR-010**.
  `NP-ADR-model_agnostic_roles_draft_v1.0.md` (`0YY`, self-declared SUPERSEDED, never
  ratified) → retains `0YY` permanently, no number, per Rule A.
  `NP-ADR-H07_definition_v1.1_draft_v1.0.md` (was `0ZZ`; does not self-declare
  SUPERSEDED, so Rule A does not remove it — "live" by that test) → **NP-ADR-011**.
  Recorded in `ops/ADR_REGISTRY.md` only. No ADR file's own text was edited to insert
  its number — that edit is reserved to the Architect.

**5 · NP-ADR-008 filename mismatch — no rename.** Verbatim: *"Renaming a ratified
document breaks every citation pointing at it. The registry carries the mapping from
number to actual file path; that is precisely what a registry is for."* `ADR_REGISTRY.md`
§3 note 2 now states this mapping explicitly: NP-ADR-008 = `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`
on disk, permanently, filename notwithstanding.

**6 · Asymmetric supersession — reported, not resolved.** Two files in `ops/` are
named by a successor's own preamble as superseded but carry no self-banner of their
own — a reader opening either directly sees an ordinary document with no warning:
  - `ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md` (now NP-ADR-011) — claimed
    superseded by `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md` (NP-ADR-008), whose
    own preamble states "Supersedes `ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`."
  - `ops/DEVELOPER_BOOT_NP-S1.md` (outside the ADR namespaces, surfaced by the same
    ops/-wide sweep) — claimed superseded by `ops/DEVELOPER_BOOT_NP-S1_RESUME.md`,
    whose own preamble states "Supersedes `ops\DEVELOPER_BOOT_NP-S1.md` for all work
    from this point."
  Neither predecessor file was edited. Banner text for either is Architect-authored,
  per the ruling, and is not written here.

Transcribed and executed by: Developer role · session: Claude Sonnet 5, Claude Code
CLI · 2026-07-31. The ruling text quoted above was issued directly by the Owner/
Architect in chat this session; this reply records it into the file per instruction
and performs the mechanical registry update it specifies.
