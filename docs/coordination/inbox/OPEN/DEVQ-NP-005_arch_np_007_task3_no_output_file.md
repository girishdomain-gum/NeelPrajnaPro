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
