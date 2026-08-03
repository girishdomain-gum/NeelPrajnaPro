# SPRINT EXECUTION MODEL v2 — "Fresh-Start" model
**Status:** DRAFT v0.1 — written by the ARCHITECT from the Owner's order O-072 (2026-08-03).
Becomes law only when the Owner says "approved" in chat. Until then the current model
(COMMS_PROTOCOL.md v1.6 + AM-01..AM-11) stays in force.

**One-line summary:** the project restarts as an EMPTY `F:\NeelPrajnaPro`. Everything built
so far becomes read-only REFERENCE material. All sprints are fully planned up front by the
Architect; the Developer then builds each sprint independently (including MT5 compile and
execution); every sprint ends with Architect review → Owner review → retrospective → close.

---

## 1. The Reference Folder (Owner point 1)

- ALL existing code, scripts, reports, docs — everything produced until now — moves into a
  single read-only **reference folder**.
- After that move, `F:\NeelPrajnaPro` is treated as a **completely empty project**. The new
  build starts from scratch; the reference folder is a quarry (read, copy from, cite), never
  a workplace.
- Same discipline as the F:\Fable rule (AM-11): reference material is read-only, effective
  from the day this model is approved; anything taken from it is copied with its origin
  named.

**OPEN DECISION (Owner must choose, see §9):** the exact path of the reference folder.

## 2. All sprint planning happens up front (Owner point 2)

Before any development starts, the Architect produces the **complete sprint plan** for the
whole project, sprint by sprint. For EVERY sprint the plan states:

| Item | Meaning |
|---|---|
| Features | What capability exists after this sprint that did not exist before |
| Modules | The named code modules built or changed |
| Folders + files | Exactly which folders and files this sprint introduces (see §7) |
| Validation process | How the sprint's work is proven correct (tests, drills, MT5 runs, evidence) |
| Complete outcome | The one-paragraph "definition of done" the reviews check against |

- When the plan is written, **all project .md docs are updated** to match it (architecture,
  file structure, glossary, this doc, boot prompts). Doc update is part of stage 2, not an
  afterthought.
- The plan is versioned in git like any doc; changes to it after approval go through the
  normal AMENDMENT mechanism (§4).

## 3. Sprint lifecycle (Owner point 3) — the same loop every sprint

1. **Architect opens the sprint**: sends the Developer the sprint's full briefing (see §5)
   through the normal inbox message.
2. **Developer builds the whole sprint independently**: all development decisions AND all
   validation decisions for that sprint are the Developer's. No mid-sprint approvals.
3. **Developer reports completion**: one message to the Architect's inbox using the standard
   message template (COMMS_PROTOCOL.md §3), stating what was built, how it was validated,
   and where the evidence lives.
4. **Architect review**: verifies and reviews ALL development and validation
   (APPROVED / APPROVED-WITH-CHANGES / REJECTED, as today).
5. **Owner review**: the Owner personally reviews the development and validation
   (his eyeball, not a relayed claim — the two-key principle survives unchanged).
6. **Retrospective**: a short retrospective doc is written for the sprint (what went well,
   what went wrong, what rule changes if any), then the sprint is CLOSED on the board.
7. **Next sprint** opens the same way. Never two sprints open at once.

## 4. What we KEEP from the current model (Owner point 4)

Unchanged and still binding:

- **BOOT_PROMPT files** for both roles; chat windows stay disposable; handover/status ritual.
- **Written communication only**, via the standard message template and the comms files
  (inboxes, consoles, STATE.md board) at `F:\NeelPrajnaPro\comms\`.
- **One live window per role** (protocol v1.6), append-only message files, id numbering
  max+1 across all four message files.
- **Completion rule** (nothing landed until Owner-pasted output is read), **drill law**,
  **two-key** for anything real, **no history rewrite / no force-push**.
- AMENDMENT mechanism: only the Architect changes the plan/spec, by numbered AM messages.

## 5. Sprint briefings must be COMPLETE (Owner point 5)

At the start of each sprint the Architect provides **everything the Developer needs to
finish the sprint without coming back**: goals, the sprint's rows from the master plan
(§2 table), file/folder allocations (§7), interfaces and constraints, validation
requirements, and the definition of done. If the Developer must ask a blocking question,
that is a defect in the briefing — record it in the retrospective and fix the briefing
style, not just the answer.

## 6. Developer executes end-to-end, including MT5 (Owner point 6)

The Developer, in its own environment, independently:

- writes and compiles the code (MetaEditor), 
- runs it in the **MT5 terminal** (opens and closes the terminal as needed),
- runs the Strategy Tester / live-chart checks its validation plan calls for,
- writes ALL outputs — logs, reports, analysis, screenshots — into
  **`F:\NeelPrajnaProData\`** (the external data/evidence store; AM-07's law extends to all
  sprint evidence: bulk artifacts never in git, provenance/hashes in git).

This replaces the old "Owner compiles with F7" loop — the Owner is no longer the compile
and test executor. The Owner's hands remain required ONLY for the ceremonies the
constitution reserves to him (arming anything real, burns, registrations, sign-offs).

## 7. Architect owns the folder & file structure, first sprint to last (Owner point 7)

- The Architect decides, **up front in the master plan**, the complete folder and file
  structure of the project as it will grow from sprint 1 to the final sprint — each sprint's
  plan names exactly which folders and files it introduces.
- Because `F:\NeelPrajnaPro` starts EMPTY, sprint 0 (setup) is the Architect's own job:
  the Architect writes/copies into the empty root everything the Developer needs to start
  smoothly — the BOOT_PROMPT files, COMMS_PROTOCOL, GIT_WORKFLOW, the comms\ skeleton,
  STATE.md, the master sprint plan, and the core docs.
- Standing rule kept: **the tree wins over the doc** — any divergence between the real tree
  and FILE_STRUCTURE.md is a finding.

## 8. Owner visibility after every sprint (Owner point 8)

Every sprint-close report to the Owner ends with a plain-English **inventory section**:

- what was developed this sprint, in simple words;
- how many folders and files were introduced, and their names;
- the running total of the project tree so far;
- where the sprint's evidence lives under `F:\NeelPrajnaProData\`.

This is in addition to the sprint-end TRUTH CHECK (board vs git vs status, from output
actually run — AM-10's duty survives).

## 9. OPEN DECISIONS — must be answered before this model activates

These are raised, not settled; settling them by accident is forbidden.

1. **Reference folder path.** Options: (a) `F:\NeelPrajnaPro\reference\` inside the repo
   (simple, but then the root is not truly "empty"); (b) a sibling outside the repo, e.g.
   `F:\NeelPrajnaProReference\` (root truly empty; matches the AM-07 pattern of keeping
   bulk outside); (c) other.
2. **The existing git repo and its history.** The project never rewrites history. Options:
   (a) keep the SAME repo — move everything into `reference/` via normal commits, history
   preserved in place; (b) archive/rename the current repo and start a NEW repo in the
   empty `F:\NeelPrajnaPro` (old history preserved in the archived repo); (c) other.
3. **The unmerged approved work** (dev 22aa64a, approved but not merged): merge it to main
   first so the reference snapshot is complete, or freeze as-is? Architect recommendation:
   merge first — the reference should be the full accepted state.
4. **Sealed evidence and the real journal** (windows, burns, H-07 lineage, evidence store):
   these are records of the world, not code — they stay where they are and stay sealed,
   regardless of the restart. Stated here so it is confirmed, not assumed.
5. **Numbering continuity.** Message ids, O-ids, AM numbers, incident ids: continue the
   existing sequences (recommended — one continuous record) or restart at 1?
6. **Effective date** — the Owner's explicit "approved" in chat, recorded as a DIRECTIVE.

## 10. Path spellings (for the record)

The correct paths are `F:\NeelPrajnaPro` (project) and `F:\NeelPrajnaProData` (data/evidence
store). Any other spelling in notes or chat (e.g. "NeelprajanPro", "NeelPrajanProData") means
these two paths.
