# Design-Stack Inventory — extraction only

*EXTRACTION, not assessment. No argument is summarized, no soundness is evaluated, no
recommendation is offered — that is Architect work, to be done from this extraction.
Where a fact could not be found verbatim in a file, this document says so rather than
supplying a plausible value.*

Generated per `ops/ARCH-NP-007_adr_registry_and_design_stack_inventory.md` Task 2 (and,
provisionally — see the note at the end of this file and `docs/coordination/inbox/OPEN/
DEVQ-NP-005_arch_np_007_task3_no_output_file.md` — Task 3).

Developer role · session: Claude Sonnet 5, Claude Code CLI · 2026-07-31.

---

## 1. `ops/NP-ADR-ARO_draft_v1.0.md`

**a. Heading tree (verbatim, in order — all `##`, no `###` present):**
```
§1 · The ADR proper
§2 · Architecture Row 13 — full definition (replaces "merely add a row")
§3 · Responsibility Matrix
§4 · Event Catalogue
§5 · State Machine (per lane / work item)
§6 · Escalation Policy
§7 · Operational Metadata (owned by ARO; zero epistemic standing)
§8 · Certification Plan (trust like an instrument)
§9 · Sprint Planning (Execution Plan integration — NP-S1 untouched)
§10 · Migration Strategy (each stage independently useful)
§11 · Repository Changes (execute only after ratification, one write window)
§12 · Naming Evaluation (mandate's additional requirement)
```

**b. Status line (verbatim):**
> "WORKING RECORD — DRAFT v1.0 for Chief Scientist review and Owner ratification
> (Constitution §7.3 path: amends the ratified Roles document; adds architecture row
> 13). Number **0XX deliberately unassigned** pending a registry check against
> docs\archive\gen1\adr\ — collision discipline per NP-D-006 (the ARCH-011 lesson)."

**c. Self-declared blockers/placeholders (verbatim):**
- "Number 0XX deliberately unassigned pending a registry check against
  docs\archive\gen1\adr\ — collision discipline per NP-D-006 (the ARCH-011 lesson)."
- §11 title itself: "Repository Changes (**execute only after ratification**, one write
  window)."
- Preamble: drafted "for Chief Scientist review **and** Owner ratification" — both
  named as outstanding.

**d. Cross-references to the other five named files:**
- `ops/OWNER_PACKET_ARO_ratification.md` — preamble line 2: "Companion:
  `ops\OWNER_PACKET_ARO_ratification.md`."
- No occurrence (by filename) of `NP-ADR-organization_and_roles_v1.0.md`,
  `REPOSITORY_AUTONOMY_v3.0.md`, `ARO_Execution_Process_v2.0.md`, or
  `WO-Q_ARO_implementation_ladder.md` anywhere in this file.

**e. What ratification would require/trigger (verbatim intent, condensed to exact statements):**
§11's table lists, "execute only after ratification, one write window": edits to
Architecture (+docx twin), Vision, Execution Plan, Automation Plan, Roles doc, Decisions
doc, V&V Plan, Journal (append), a new `ops\aro\` directory, and a CHANGELOG line.
§11's last row states explicitly: "Constitution — **no change** (verified) — —".

**f. Word count / last modified:** 3,499 words · last commit touching file: 2026-07-30.

---

## 2. `ops/NP-ADR-organization_and_roles_v1.0.md`

**a. Heading tree (verbatim, in order):**
```
1. Confirmed principles (Owner-stated; recorded verbatim as the ADR's basis)
2. THE THREE CATEGORIES — final definitions (the clarification requested)
   2.1 Organization Roles — accountable participants
   2.2 Operational Systems — instruments and infrastructure
   2.3 Governance Bodies — there are none, deliberately
3. Final organizational structure
4. Final responsibility matrix
5. Separation-of-duties policy (proposed Constitution §5.5)
6. Artifact attribution standard (proposed Roles §3.8)
7. Exact repository changes (on ratification; one write window)
8. Required amendment path
9. Owner ratification summary
```

**b. Status line (verbatim):**
> "Supersedes `ops\NP-ADR-model_agnostic_roles_draft_v1.0.md` (draft, never ratified).
> Status: FINAL DRAFT for Chief Scientist review → Owner ratification, Constitution
> §7.3. **Number 0YY unassigned** pending registry check (NP-D-006). No normative
> document has been edited; §7 lists every change, each executing only on ratification."

**c. Self-declared blockers/placeholders (verbatim):**
- "Number 0YY unassigned pending registry check (NP-D-006)."
- "FINAL DRAFT for Chief Scientist review → Owner ratification" — both named as
  outstanding.
- §7's changes each stated to be "executing only on ratification."

**d. Cross-references to the other five named files:**
- `ops/NP-ADR-ARO_draft_v1.0.md` — §7 repository-changes table, item 13: "ops\ARO_
  Architecture_Review_NP.md · ops\NP-ADR-ARO_draft_v1.0.md · DEVQ-NP-001/002 replies |
  append | attribution corrections; original bylines left visible (P5)."
- No occurrence (by filename) of `REPOSITORY_AUTONOMY_v3.0.md`,
  `ARO_Execution_Process_v2.0.md`, `WO-Q_ARO_implementation_ladder.md`, or
  `OWNER_PACKET_ARO_ratification.md` anywhere in this file.

**e. What ratification would require/trigger (verbatim intent):**
§7 lists 15 exact repository changes (Constitution §5.2/§5.3/new §5.4/new §5.5; Roles
§1/§2.2/§2.4/new §2.5–§2.6/new §3.8; Automation §3; `ops\DEVELOPER_BOOT_NP-S1.md`
header; `CLAUDE.md` top line; new `ops\ASSIGNMENT_REGISTER.md`; attribution corrections
appended to the ARO review/ADR files and DEVQ-NP-001/002 replies; Decisions Part 2;
Journal). §8: "One ADR, one §7.3 amendment... Path: this package → Chief Scientist
review on the record → Owner ratification → single write window → journal entry."

**f. Word count / last modified:** 2,350 words · last commit touching file: 2026-07-30.

---

## 3. `ops/REPOSITORY_AUTONOMY_v3.0.md`

**a. Heading tree (verbatim, in order — all `##`, no `###` present):**
```
0. The one principle that keeps this layer from becoming a liability
1. Repository Boot Specification
2. Repository Manifest Specification
3. Repository Discovery Protocol
4. Session Recovery Protocol
5. Repository State Model
6. Repository Lifecycle
7. Multi-session Coordination Rules
8. Repository Self-Description Standard
9. What must be built, and what it costs
```

**b. Status line (verbatim):**
> "Completes the ARO architecture. Governance, ARO and roles are **not** redesigned
> here — this layer only makes what already exists discoverable, verifiable and
> recoverable by a session that knows nothing. ... Status: DRAFT, rides with the ARO
> ADR to Chief Scientist review and Owner ratification."

**c. Self-declared blockers/placeholders (verbatim):**
- "Status: DRAFT, rides with the ARO ADR to Chief Scientist review and Owner
  ratification."
- §8, standard S8: "The standard applies to itself: this document is DRAFT until
  ratified, and `MANIFEST.json` will cite the ratified version, not this one."
- §9: "**Two Owner decisions this layer needs:** (1) one new root file —
  `MANIFEST.json`... the root structure law... should be read as permitting it, but
  that reading is **the Owner's to confirm**. `ORGANIZATION.md` is a second root
  file — alternatively it lives at `docs/organization/`... **recommendation:
  `docs/organization/`**... (2) Whether `scripts/gen_state.py`... is **retired in
  favour of `gen_manifest.py`** — the deferred D2 question, which this layer answers
  naturally."

**d. Cross-references to the other five named files:**
- `ops/ARO_Execution_Process_v2.0.md` — referenced twice: §2 manifest table, "`ops/
  ARO_Execution_Process_v2.0.md` | the workflow spec (exists) | referenced by manifest
  as `workflow_ref`; no `WORKFLOW.md` duplicate is created"; and inside the example
  `MANIFEST.json` block, `"workflow_ref": "ops/ARO_Execution_Process_v2.0.md"`.
- The preamble says "Completes the ARO architecture" and "rides with the ARO ADR" but
  does **not** name `NP-ADR-ARO_draft_v1.0.md` by filename anywhere in the file — the
  reference to "the ARO ADR" is by description only, not by path.
- No occurrence (by filename) of `NP-ADR-organization_and_roles_v1.0.md`,
  `WO-Q_ARO_implementation_ladder.md`, or `OWNER_PACKET_ARO_ratification.md`.

**e. What ratification would require/trigger (verbatim intent):**
§9's build list: `scripts/gen_manifest.py`, `scripts/verify_manifest.py`,
`ORGANIZATION.md`, six `ops/aro/roles/<role>.boot.md` cards, queue folder tree +
templates, a boot-sequence conformance CI test — plus the two Owner decisions quoted
in (c) above.

**f. Word count / last modified:** 2,028 words · last commit touching file: 2026-07-30
(this file's last commit timestamp, 16:14:56+05:30, is later in the day than
`NP-ADR-ARO_draft_v1.0.md` and `NP-ADR-organization_and_roles_v1.0.md`, both
15:21:19+05:30 — reported as a fact, not interpreted).

---

## 4. `ops/ARO_Execution_Process_v2.0.md`

**a. Heading tree (verbatim, in order — all `##`, no `###` present):**
```
1. Repository-first execution architecture
2. Repository directory structure
3. Standard work queue design
4. Standard handover package
5. Standard work order template
6. State transition rules
7. ARO workflow algorithm
8. Minimal Owner interaction model
9. Migration plan (chat-relay → repository-first)
```

**b. Status line (verbatim):**
This file contains **no line beginning "Status:"** anywhere in its text. The closest
self-description is the preamble: "*Supersedes `ops\ARO_Execution_Process_v1.0.md`
(which designed around today's chat relay instead of past it — Owner correction,
2026-07-30, accepted). Annex to `ops\NP-ADR-ARO_draft_v1.0.md`. Introduces no new
authority.*" No DRAFT/RATIFIED/ACCEPTED word is applied to this document itself.

**c. Self-declared blockers/placeholders (verbatim):**
- No explicit blocker language addressed at this document's own approval state (unlike
  files 1–3 and 6, it does not say it awaits Chief Scientist review or Owner
  ratification in its own text).
- §9 migration table, stage M3: "**External participants onboarded as repo-capable
  sessions**... Gate: **Constitution §5.2 amendment** (relay-only → *writes only to its
  own review lane*)" — a named prerequisite for that stage specifically, not for the
  document as a whole.
- §9: "**The shim, named with an expiry:** until M3, a non-repo-capable reviewer's
  output is pasted once, by the Owner... and it is recorded as a *shim touch*."

**d. Cross-references to the other five named files:**
- `ops/NP-ADR-ARO_draft_v1.0.md` — preamble: "Annex to `ops\NP-ADR-ARO_draft_v1.0.md`."
- No occurrence (by filename) of `NP-ADR-organization_and_roles_v1.0.md`,
  `REPOSITORY_AUTONOMY_v3.0.md`, `WO-Q_ARO_implementation_ladder.md`, or
  `OWNER_PACKET_ARO_ratification.md`.

**e. What ratification would require/trigger (verbatim intent):**
No section of this file frames itself as awaiting ratification directly; §9's table is
the only place a gate is named, and it gates stage M3 specifically ("Constitution §5.2
amendment"), not the document's adoption as a whole.

**f. Word count / last modified:** 1,733 words · last commit touching file: 2026-07-30
(16:14:56+05:30, same commit batch as `REPOSITORY_AUTONOMY_v3.0.md`).

---

## 5. `ops/WO-Q_ARO_implementation_ladder.md`

**a. Heading tree (verbatim, in order — all `##`, no `###` present):**
```
The ladder
v0.0 — PREFLIGHT CHECKLIST (no code; do this first, it is the highest-value item here)
v0.1 — STATUS (read only)
v0.2 — DASHBOARD (render only)
v0.3 — MOVE (first write permission)
v0.4 — PACKET
v0.5 — CREATE
v0.6 — RECOVER
Rules that apply at every rung
Accountability (unchanged by this ladder)
What this ladder is not
```

**b. Status line (verbatim):**
This file contains **no "Status:" line and no DRAFT/RATIFIED/ACCEPTED self-label
anywhere.** Its self-description is: "*A backlog, not a design document. Seven
milestones. Each adds **one permission**, has **one exit test**, has **one drill**,
and can be switched off.*"

**c. Self-declared blockers/placeholders (verbatim):**
No blocker or placeholder language about the document's own approval status. The
closest analogue is internal, per-rung gating, not a ratification blocker: "**Drill
before grant.** A permission is earned by catching planted faults, never by working
once," and the boxed epigraph: "**If ARO ever needs intelligence, the specification is
wrong.** Every time the orchestrator seems to need judgment, the fix is upstream in
the spec — never a smarter orchestrator."

**d. Cross-references to the other five named files:**
None. No occurrence (by filename) of `NP-ADR-ARO_draft_v1.0.md`,
`NP-ADR-organization_and_roles_v1.0.md`, `REPOSITORY_AUTONOMY_v3.0.md`,
`ARO_Execution_Process_v2.0.md`, or `OWNER_PACKET_ARO_ratification.md`.

**e. What ratification would require/trigger (verbatim intent):**
The document does not frame itself as subject to ratification; it frames each rung
(v0.0–v0.6) as gated by "one drill" per rung rather than by an Owner ratification
event. No statement ties this document's adoption to a write window or a ratification
wording.

**f. Word count / last modified:** 1,070 words · last commit touching file: 2026-07-31
— one calendar day later than all other five files in this set (2026-07-30), reported
as a fact.

---

## 6. `ops/OWNER_PACKET_ARO_ratification.md`

**a. Heading tree (verbatim, in order — all `##`, no `###` present):**
```
Summary
Benefits
Risks — and their controls
Dependencies
Open questions (only two)
Ratification wording (type one)
Recommendation
Expected impact
```

**b. Status line (verbatim):**
This file contains **no "Status:" line.** Its self-description is: "*One page.
Decision-ready. Everything referenced is on disk. 2026-07-30.*"

**c. Self-declared blockers/placeholders (verbatim):**
- "## Open questions (only two)
  1. **Name:** keep **ARO** (recommended, with the permanent subtitle 'Supervised
     Autopilot, Phase C') or fall back to **RO**.
  2. **O0 now?** The packet-file convention costs nothing and starts serving you
     today; it can be adopted with ratification or even on rejection of the rest."
- "## Dependencies
  - Detector-identity/fingerprint ADR (already queued from DEVQ-01) — feeds the
    preflight; seal it first or jointly.
  - One honesty correction to Automation Plan §3 — required **even if you reject the
    ARO**."

**d. Cross-references to the other five named files:**
- `ops/NP-ADR-ARO_draft_v1.0.md` — "## Summary" paragraph: "Full text:
  `ops\NP-ADR-ARO_draft_v1.0.md`."
- No occurrence (by filename) of `NP-ADR-organization_and_roles_v1.0.md`,
  `REPOSITORY_AUTONOMY_v3.0.md`, `ARO_Execution_Process_v2.0.md`, or
  `WO-Q_ARO_implementation_ladder.md`. (It separately cites `ops\ARO_Architecture_
  Review_NP.md` as "Evidence," a file outside this six-file set.)

**e. What ratification would require/trigger (verbatim intent):**
"## Ratification wording (type one)" gives three literal typed strings — APPROVE,
APPROVE with name fallback ("RO"), REJECT — and the APPROVE wording states: "Document
changes execute in the next write window."

**f. Word count / last modified:** 522 words · last commit touching file: 2026-07-30
(15:21:19+05:30, same commit batch as files 1 and 2 above).

**g. Owner-actionable completeness (factual, not evaluative, per instruction):**
All eight sections listed in (a) are present and contain text; none is empty and none
is marked TODO or left as a placeholder. The file supplies three literal typed
ratification strings the Owner could paste back verbatim (APPROVE / APPROVE with name
fallback / REJECT), and the APPROVE wording itself already resolves both items listed
under "Open questions" (it names "ARO" and states "O0 is adopted now"). Whether this
constitutes a sufficient decision record is an Architect/Owner judgment outside this
report's scope; the fact reported here is only that no section is blank or TODO-marked
and a directly-typeable decision string exists for all three outcomes.

---

## Cross-reference matrix (six files, exact-filename matches only)

| From \ To | ARO draft | org_and_roles | REPO_AUTONOMY | Exec_Process_v2 | WO-Q | OWNER_PACKET |
|---|---|---|---|---|---|---|
| **ARO draft** | — | no | no | no | no | yes (Companion) |
| **org_and_roles** | yes (§7 item 13) | — | no | no | no | no |
| **REPO_AUTONOMY** | no (describes "the ARO ADR" without filename) | no | — | yes (×2) | no | no |
| **Exec_Process_v2** | yes (Annex to) | no | no | — | no | no |
| **WO-Q** | no | no | no | no | — | no |
| **OWNER_PACKET** | yes (Full text) | no | no | no | no | — |

Every one of the six files at minimum references, or is referenced by, `NP-ADR-
ARO_draft_v1.0.md`. `WO-Q_ARO_implementation_ladder.md` is the only file with zero
cross-references in either direction among this set.

---

## Task 3 — Supersession chain (ops/-wide sweep)

**Placement note:** the boot instruction's SCOPE list names no output file for Task 3.
This is raised as `docs/coordination/inbox/OPEN/DEVQ-NP-005_arch_np_007_task3_no_output_file.md`.
Pending an answer, Task 3's findings are provisionally appended here, in the file whose
subject matter (the design-stack documents) both self-declared-SUPERSEDED cases found
below belong to.

**Method:** case-insensitive search for "supersed" across every file in `ops/` (14
files matched at least one occurrence), then manual inspection of each match to
distinguish (i) a file declaring **itself** superseded, (ii) a file declaring that it
supersedes **another**, and (iii) incidental uses of the word unrelated to document
lineage (e.g. a data-analysis sentence about "superseding" one argument with another).

### Files that declare themselves SUPERSEDED (self-banner present)

**1. `ops/ARO_Execution_Process_v1.0.md`**
> "**SUPERSEDED 2026-07-30 by `ops\ARO_Execution_Process_v2.0.md`.** Owner correction,
> accepted: ... Retained for provenance only."
Title itself: "ARO EXECUTION PROCESS v1.0 **(SUPERSEDED)** — the Autonomous
Development Workflow."
- Named successor: `ops/ARO_Execution_Process_v2.0.md` — **verified to exist** (it is
  file 4 in this inventory).
- Verified the successor does **not** itself declare supersession: confirmed by the
  same ops/-wide search — `ARO_Execution_Process_v2.0.md` contains no "SUPERSEDED"
  self-banner and no "Status:" line at all (see §4b above); it only states, in the
  active-successor direction, "Supersedes `ops\ARO_Execution_Process_v1.0.md`."

**2. `ops/NP-ADR-model_agnostic_roles_draft_v1.0.md`**
> "**SUPERSEDED 2026-07-30 by `ops\NP-ADR-organization_and_roles_v1.0.md`** (the final
> ratification package). Retained for provenance only — never ratified, never cited.
> Read the successor."
Title itself: "NP-ADR-0YY **(DRAFT, SUPERSEDED)** — Model-Agnostic Roles."
- Named successor: `ops/NP-ADR-organization_and_roles_v1.0.md` — **verified to exist**
  (it is file 2 in this inventory).
- Verified the successor does **not** itself declare supersession: confirmed —
  `NP-ADR-organization_and_roles_v1.0.md`'s preamble uses only the active-successor
  direction ("Supersedes `ops\NP-ADR-model_agnostic_roles_draft_v1.0.md`") and its own
  status line names no SUPERSEDED banner (see §2b above).

No other file in `ops/` carries a self-referential "I am SUPERSEDED" banner. All
remaining matches for "supersed" (`ops/ADR_REGISTRY.md`, `ops/ARCH-NP-007...md`,
`ops/DEVQ-01_NP-S1.md`, `ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`,
`ops/POST_CORRECTION_VERIFICATION_H07_v1.1.md`, `ops/REPOSITORY_AUTONOMY_v3.0.md`,
`ops/DEVELOPER_BOOT_NP-S1_RESUME.md`) use the word either as an active "X supersedes
Y" statement made by a successor about a predecessor, as an incidental description of
a data/argument superseding another, or (for `ops/ADR_REGISTRY.md` and this instruction
file) as meta-discussion of the search itself — none is the target document declaring
itself superseded.

### Asymmetric cases found (successor claims supersession; predecessor carries no matching self-banner) — reported as a fact, not resolved

**3. `ops/NP-ADR-H07_definition_v1.1_draft_v1.0.md`** is named as superseded by
`ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md`'s own preamble — "*Supersedes
`ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md`.*" — but `draft_v1.0.md` itself contains
**no** "SUPERSEDED"/"supersed" text anywhere and carries no self-banner announcing its
own supersession, unlike cases 1 and 2 above. Both files exist; the claim is
one-directional.

**4. `ops/DEVELOPER_BOOT_NP-S1.md`** is named as superseded by `ops/DEVELOPER_BOOT_
NP-S1_RESUME.md`'s own preamble — "*Supersedes `ops\DEVELOPER_BOOT_NP-S1.md` for all
work from this point.*" — but `DEVELOPER_BOOT_NP-S1.md` itself contains no
"supersed"-family text at all. Both files exist; the claim is one-directional. (This
pair falls outside the six-file design-stack set but was surfaced by the same ops/-wide
sweep and is reported for completeness of the Task 3 method.)

This registry does not judge whether an asymmetric (successor-only) supersession claim
is a defect; it reports that the two patterns — mutual/self-declaring (cases 1–2) and
successor-only (cases 3–4) — both exist in `ops/`, and that the QRF-known-collision-
style verification (does the claimed successor exist, and does it itself claim to be
superseded) checks out clean in all four cases.
