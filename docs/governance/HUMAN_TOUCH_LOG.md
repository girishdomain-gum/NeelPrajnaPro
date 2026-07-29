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
| T-003 | — | Ratification checklist (cutover rule, F-13 Auto-Adopt, three charters, window designation, α-budget, cost-model name, ARCH-NP-001 Go/No-Go) | GOVERNANCE | — | PENDING — **the next human action, and the only kind left** |
| T-004 | 2026-07-29 16:45 | Ran ops\T-004_verify_bootstrap.ps1 | ROUTINE-OP | One line, self-logging | **DONE** — found the failed push; also exposed finding F-18 (script said RESULT: OK on a failed push — against the Architect) |
| T-005 | 2026-07-29 16:53 | Ran ops\T-005_fix_push.ps1 | ROUTINE-OP | One line, self-logging | **DONE** — safety gate confirmed origin/main was the 1-commit auto-init (README.md only); force-with-lease replaced it; local HEAD = remote HEAD (da7b79a); evidence commit 5812d68 pushed clean. **Full Gen-1 history now on GitHub.** |

## Findings referenced
- **F-18 (Architect):** T-004's RESULT line was computed from file existence, not from the push outcome it implicitly claimed. Standing rule: a script's RESULT must be computed from the outcomes it claims (exit codes checked per step), never from the survival of files around them. Applied from T-005 onward.

## Housekeeping (next script sweeps)
- `ops/T-005_fix_push.ps1` is still untracked (T-005 staged only `ops/runlogs`); the next ops script stages `ops/` whole.

## Standing rule
A sprint retro that finds an unlogged human touch records it retroactively **as a finding** (species: invisible labor). What is not counted cannot be driven to zero.
