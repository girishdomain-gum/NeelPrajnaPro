DEVELOPER BOOT — ARCH-NP-007 (ADR registry + design-stack inventory)

You hold the Developer role for this session.

IGNORE CLAUDE.md's role section — it is a known defect (names the wrong project,
points at docs/coordination/PROTOCOL.md which exists only under docs/archive/).
Your role, powers and limits: docs/roles/NeelPrajnaPro_Roles_And_Communication-v1.0.md.
CLAUDE.md's environment note (invoke .venv/Scripts/python.exe directly) is valid.

This instruction is self-contained. It was NOT committed before you were launched,
so Task 0 exists to put it in the record — see below.

BRANCH
    git fetch origin
    git checkout main
    git pull --ff-only origin main
    git checkout -b maint/adr-registry
    git push -u origin maint/adr-registry

Do not touch main. Do not touch maint/gen1-cleanup (ARCH-NP-006 runs there
independently; your scopes do not overlap).

TASK 0 — enter the instruction into the record
Copy this entire boot prompt verbatim into
    ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md
Commit it as your first commit, then push. Every later commit in this session is
verifiable against it.

TASK 1 — generate the ADR registry
Create ops/ADR_REGISTRY.md. This is DERIVED, operational metadata with zero
epistemic standing — you enumerate what exists; you assign nothing and judge
nothing. Number assignment is an Architect decision and is explicitly NOT
yours (Roles §2.4: the Developer does not author ADRs).

Scan and enumerate three namespaces (Constitution §5.4 namespaces them
separately; they are NOT one series):

  QRF (Gen-1)   docs/archive/gen1/adr/
  Book A        docs/books/book-a-neelprajna/**/adr/
  NP            ops/NP-ADR-*, and anywhere else NP-ADR-* appears

For each entry record: number (or "UNASSIGNED"), slug, file path, and any status
string the file itself declares (RATIFIED / DRAFT / SUPERSEDED / placeholder such
as 0XX or 0YY). Quote the status verbatim from the file; do not infer one.

Flag every collision. Two are already known in the QRF namespace — ADR-009 and
ADR-010 each have two files, historically resolved by letter suffix (QRF-ADR-009b,
QRF-ADR-010b). Report any others you find, and report which NP numbers are
occupied and which are free.

Do not renumber, rename, or move any file. Enumeration only.

TASK 2 — design-stack inventory
Create ops/DESIGN_STACK_INVENTORY.md covering these six files:

    ops/NP-ADR-ARO_draft_v1.0.md
    ops/NP-ADR-organization_and_roles_v1.0.md
    ops/REPOSITORY_AUTONOMY_v3.0.md
    ops/ARO_Execution_Process_v2.0.md
    ops/WO-Q_ARO_implementation_ladder.md
    ops/OWNER_PACKET_ARO_ratification.md

This is EXTRACTION, not assessment. Do not summarize arguments, evaluate
soundness, or recommend anything — that is Architect work and I will do it from
your extraction. For each file report only:

  a. Full heading tree (every ## and ###, in order, verbatim).
  b. The status line the document declares about itself, verbatim.
  c. Every explicit blocker or unresolved placeholder it states about ITSELF
     (e.g. "Number 0XX deliberately unassigned pending...", "requires Chief
     Scientist review", "executes only after ratification").
  d. Which of the other five files it cross-references, and where.
  e. Any statement about what ratification of it would require or trigger.
  f. Word count and last-modified date.

For ops/OWNER_PACKET_ARO_ratification.md additionally report, factually: does it
contain a decision list the Owner could act on as-is, or is it incomplete? State
which sections are present and which are empty or marked TODO. Do not judge
whether it is good.

TASK 3 — supersession chain
Report every file in ops/ that declares itself SUPERSEDED, and by what. One known
case: ops/NP-ADR-model_agnostic_roles_draft_v1.0.md declares itself superseded by
ops/NP-ADR-organization_and_roles_v1.0.md. Verify that the named successor exists
and that it does not itself declare supersession.

SCOPE — by artifact class
  Generated ops metadata:  ops/ADR_REGISTRY.md, ops/DESIGN_STACK_INVENTORY.md
  Instruction record:      ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md
  Handover:                ops/aro/handovers/ARCH-NP-007/HANDOVER.md
  Session log:             docs/coordination/sessions/SNP-M2-01_2026-08-xx_ARCH-NP-007.md

Everything else in this repository is READ-ONLY for this session. No code changes.
No test changes. No edits to any existing document, normative or otherwise.

DONE WHEN
1. Tasks 0-3 complete, all four files committed and pushed.
2. No file outside the scope list is modified. Prove it:
       git diff --stat main...maint/adr-registry
   and paste that output into the handover.
3. Handover, ten sections.
4. Branch pushed. DO NOT MERGE TO main.

No test run is required — this session changes no code. If you find yourself
wanting to run pytest, that is a signal you have gone outside scope.

RULES
- Sign every artifact: Developer role · session: <model>, <interface> · date.
  Never a prior session's name.
- Report verbatim. Where you quote a status or a blocker, quote it exactly; where
  you cannot quote it, say the file does not state one rather than supplying a
  plausible value.
- A negative result is not evidence until the check has been shown able to return
  a positive one. Before reporting "no collisions in namespace X", run the same
  search against the QRF namespace, which is known to contain two — if it does not
  surface those, your method is wrong. (F-27: three Architect-authored checks
  returned false clean results on 2026-07-31.)
- If scope and acceptance criteria conflict, that is a defect in this instruction
  — raise a DEVQ, do not silently pick one.
- Corrections are appended, never edited (P5).
- Push after every commit.

Issued by: Architect role · session: Claude Opus 5, claude.ai · 2026-07-31.
