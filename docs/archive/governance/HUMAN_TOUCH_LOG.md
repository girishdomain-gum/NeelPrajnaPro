# HUMAN TOUCH LOG — the register of every human action
*Purpose: make the Owner's operational involvement visible, countable, and shrinking. Reviewed at every sprint retro. Ruling basis: OWNER_RULINGS_2026-07-29.md R-3. Ultimate goal on the record: zero routine-operation touches; governance touches all judgment, no chores.*

## How to log
One row per touch. **Category:** `ROUTINE-OP` (a chore the machine should eventually do — must name its automation path) or `GOVERNANCE` (permanently human by Constitution §6 — logged, never minimized away). The Architect appends rows on the Owner's behalf when touches happen in-session; the Owner may append directly. Routine touches happen only through the ops channel (`ops\README_OPS.md`): the Architect writes a script, the Owner runs one line, the script logs itself, the Architect reads the log.

## Baseline (pre-log context, for honest retrospect)
| ID | Date | Touch | Category | Note |
|---|---|---|---|---|
| T-000a | ≤2026-07-27 | Started bridge agent + Supervisor on the lab machine; signed SUPERVISOR_CONTRACT v1.1 | GOVERNANCE + one-time setup | Agent self-starts at logon (D13) — the routine part already automated |
| T-000b | Gen 1, per sprint | git push/pull rhythm; Go/No-Go rulings; window designations | Mixed | Push/pull chore is the largest surviving ROUTINE-OP; automation path: Developer sessions inside this repo handle git from NP-S1 onward |

## Live log
| ID | Date | Touch | Category | Automation path (ROUTINE-OP only) | Status |
|---|---|---|---|---|---|
| T-001 | 2026-07-29 | Ran the one-time bootstrap block (robocopy core forward, Book-A copies, pause markers, git re-point) | ROUTINE-OP (one-time) | Unrepeatable by design; connector cannot execute or copy binaries | **DONE** — tree/Book-A/pause markers verified directly; push portion failed silently, repaired by T-005 |
| T-002 | 2026-07-29 | Drop the four .docx presentation copies + corrected mockups from the delivered zip into docs\planning\ and docs\reviews\ | ROUTINE-OP (one-time) | Future binaries: committed by Developer sessions, not by hand | PENDING (optional — .md is canonical) |
| T-003 | 2026-07-29 | Ratification memo delivered: estate RATIFIED as a whole; rulings — F-13 Auto-Adopt DISABLE pending hysteresis; cost model `xauusd_retail_h07`; H-07 claim form E2; boundary expansion ordered (delivered in Architecture §4.5); H-07 sealed definition required (delivered same day) | GOVERNANCE | — | **DONE-PARTIAL** — remaining Owner items: typed window designation · family α-budget · Go/No-Go on ARCH-NP-001 (then the sprint begins) |
| T-004 | 2026-07-29 16:45 | Ran ops\T-004_verify_bootstrap.ps1 | ROUTINE-OP | One line, self-logging | **DONE** — found the failed push; also exposed finding F-18 (script said RESULT: OK on a failed push — against the Architect) |
| T-005 | 2026-07-29 16:53 | Ran ops\T-005_fix_push.ps1 | ROUTINE-OP | One line, self-logging | **DONE** — safety gate confirmed origin/main was the 1-commit auto-init (README.md only); force-with-lease replaced it; local HEAD = remote HEAD (da7b79a); evidence commit 5812d68 pushed clean. **Full Gen-1 history now on GitHub.** |
| T-006 | 2026-07-29 17:05 | Downloaded working-set zip; ran ops\T-006_place_estate_from_zip.ps1 (twice — first run correctly refused on missing zip) | ROUTINE-OP | One line, self-logging; script fetches zip from Downloads itself | **DONE-PARTIAL** (commit 7559650, 72 files: reference volumes, specs, corrected mockups w/ verified banners, redesign tree, HOW_THIS_DOC) — honestly reported FAILED for 3 missing docx (older zip in Downloads) + exposed F-19 |
| T-007 | 2026-07-29 17:12 | Downloaded NP_planning_docx.zip; ran ops\T-007_finish_placement.ps1 | ROUTINE-OP | One line, self-logging | **DONE** (commit 3609350): three current planning docx placed; F-19 remedied — 41 scratch files untracked, ops/incoming gitignored forever. **Estate placement COMPLETE: every zip-corpus artifact now in the repository.** |

## Findings referenced
- **F-18 (Architect):** T-004's RESULT line was computed from file existence, not from the push outcome it implicitly claimed. Standing rule: a script's RESULT must be computed from the outcomes it claims (exit codes checked per step), never from the survival of files around them. Applied from T-005 onward — and proven twice in T-006 (refused loudly on missing zip; refused to call 95% success "OK").
- **F-19 (Architect):** T-006 staged the ops/incoming scratch area into history (5.7MB zip + extract tree incl. a stale pre-rename ARCH-011 copy). Standing rule: scratch areas are gitignored before the first script that writes to them. Remedied in T-007 (untracked + ignored); the T-006 commit remains in history as the honest record, per append-only.

## Housekeeping (next commit sweeps)
- `ops/T-007_finish_placement.ps1` untracked (T-007 staged selectively); the first Developer-session commit stages `ops/*.ps1` whole.
- T-002 is CLOSED by T-006+T-007 (all binaries placed via the ops channel instead of hand-drops).

## Standing rule
A sprint retro that finds an unlogged human touch records it retroactively **as a finding** (species: invisible labor). What is not counted cannot be driven to zero.
