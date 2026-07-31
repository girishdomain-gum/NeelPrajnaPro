# ARCHITECT BOOT — resume point, Sprint NP-S2
*Written 2026-07-31 by the outgoing Architect session (Opus 5, claude.ai + filesystem connector) as its own handover. Read this first, in full, before acting. Everything here is verifiable in the repository — verify rather than trust.*

---

## 1. Who you are

You hold the **Architect** role. Roles are permanent; the model and session filling one are a temporary assignment (proposed NP-ADR, `ops\NP-ADR-organization_and_roles_v1.0.md`, **drafted not ratified**).

**Sign every artifact you write** with role + session identity + date, e.g. *"Architect role · session: <model>, <interface> · 2026-08-xx."* Do **not** sign as "Fable" or any prior session's name — that error was made in this estate and is on the record.

**Your mandate and limits:** `docs\roles\NeelPrajnaPro_Roles_And_Communication-v1.0.md`. You design, instruct, verify independently, author ADRs, and rewrite the handover. You do **not** write Developer code, and you do **not** ratify — only the Owner does.

## 2. Read in this order

1. `docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md` **§0** — the live handover.
2. `docs\journal\NeelPrajnaPro_Journal.md` — **J-037 through J-040** are today's decisions. J-001…J-036 are history.
3. `docs\decisions\NeelPrajnaPro_Decisions-v1.0.md` — **NP-D-011, NP-D-012, NP-D-013** are new and binding.
4. `ops\SPRINT_STATE_MACHINE_v1.1.md` — how sprints run (**drafted, not ratified**; being used in practice).
5. `docs\constitution\NeelPrajnaPro_Constitution-v1.0.md` §6 — the permanently-human powers. Never assume one.
6. `ops\ARCH-NP-005_fix_rebuild_bulk_h007.md` — the open work order.

## 3. Exactly where things stand

| | |
|---|---|
| **Branch** | `sprint/NP-S2` at **`491955f`** (T-057, G1 seal). Verify with `git fetch && git log --oneline -1 origin/sprint/NP-S2`. |
| **`main`** | Last at the T-051 attach-log commit. **Deliberately untouched since the sprint opened** — it moves once, at P8. |
| **NP-S1** | **CLOSED and accepted** (J-037). One integrated verdict: `01KYSGQR3D8SYSVJFSF9M77CMY`, **FAIL**, window burned, all six AC met, REV approved 8.8/10. |
| **NP-S2** | **Open. Scope is WO-P only** (Owner ruling, J-040). WO-P is **complete** (J-039). |
| **Next work** | `ARCH-NP-005` — the `rebuild_bulk.py` h007 lineage fix. **Issued, not started.** |
| **Then** | P8: one `--no-ff` merge of `sprint/NP-S2` → `main`. NP-S2 closes. |
| **Then** | **NP-S3** — R6 collection, with its own fresh P0 preflight and G1. |

## 4. The immediate next action

Release a fresh Developer session on `ops\ARCH-NP-005_fix_rebuild_bulk_h007.md`, on `sprint/NP-S2`, **naming commit `491955f` or later** so it can verify it has the instruction before starting. Scope is `scripts/**` only. Done when both failing `test_rebuild_bulk_s9.py` tests pass, a regression test proves `rebuild_all()` reproduces the h007 manifest byte-identically, the full suite and kernel firewall are green, and a ten-section handover exists.

## 5. Rules earned today — a fresh session will otherwise repeat these

- **An instruction naming repository state names the commit that contains it.** Three prompts this session referenced state the recipient could not fetch. (J-037 retro a)
- **Disclose assumptions at the granularity where two implementers could differ.** "Full suppression" was disclosed; *which value is compared* was not — and that was the actual bug. (J-037 retro b)
- **Decision records are committed the same day they are approved.** (J-037 retro c)
- **A verbatim requirement ships with the quotable string.** (J-037 retro d)
- **Design work stays off the critical path while a sprint is in flight.** ~15 documents were produced on the day the first verdict was earned; none was on the path to it. (J-037 retro e)
- **A verification pattern is copied from the artifact it verifies, never retyped** — and an ASCII-only script matches an ASCII-safe substring, never punctuation it cannot reproduce. (J-038)
- **Any script inserting a journal entry checks for its own heading first and refuses if present.** T-053 wrote J-039 twice. (J-040)
- **`main` is untouched until P8.** T-051 broke this on the rule's first day.
- **NP-D-012:** a specification defining a computation must let an independent implementation reproduce it *without reading the code*. If yours doesn't, that's your defect — expect a DEVQ.
- **NP-D-013:** no sprint's "done" may depend on waiting for calendar time.

## 6. The failure mode most likely to bite you

**Verification apparatus costing more than the thing it verifies.** Four scripts (T-054…T-057) were spent committing content that was correct on the first attempt — the checks kept misfiring, not the edits. One check reported zero matches against a heading confirmed present by three direct reads; the cause was never established. **If a check fails twice on content you have verified by reading, remove the check and say so in the commit message. Do not soften a check that is correctly failing — but do not keep rewriting one that is wrong.**

## 7. Open items, none blocking ARCH-NP-005

- **NP-S3 preflight blockers already identified** (`ops\preflight\PFR_NP-S2.md` §5): the R6 scope is unnamed · **a DST transition will fall inside a 3–6 month collection window** (this estate already lost a bug-and-revert cycle to timezone handling) · the NPSU migration and windows.json checks have no written specification, which NP-D-012 forbids.
- **Unratified design stack** — ARO ADR, organization/roles ADR, repository autonomy v3.0, state machine v1.1, WO-Q ladder, detector-fingerprint ADR. All drafted, none ratified. Do not cite any as settled.
- **WO-A, deferred since J-012:** `CLAUDE.md` is entirely Gen-1 vintage (names "the QRF project", points at an archived PROTOCOL path); `CHANGELOG.md` was frozen at 2026-07-24 until today's one-line entry.
- **Attribution corrections** pending on two ops artifacts and two DEVQ replies signed with another session's name.
- **Architecture docx twin** stale against its md (F-24 consequence).
- **F-23:** a Book A mockup contradicts the ratified Auto-Adopt disable; bites only at NP-S8, correction already written into that sprint's text.

## 8. What this estate values, in one paragraph

Evidence over documents. A FAIL that answers a question outranks a PASS that flatters one. Findings are recorded against names, including the Architect's, and are never softened — the Owner ruled explicitly that NP-S1's findings are permanent. Corrections are **appended**, never edits (P5). The repository is the only source of truth; if chat and repo disagree, the repo wins. Silence binds no one — an assumption in place of an answer is a finding. And the one number that matters is integrated verdicts, which went from **0 to 1** on 2026-07-30.

---
*Anchor: **read the record, verify what it claims, and add to it honestly — including when what you must add is your own mistake.***
