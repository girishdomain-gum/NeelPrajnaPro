# HUMAN TOUCH LOG — the register of every human action
*Purpose: make the Owner's operational involvement visible, countable, and shrinking. Reviewed at every sprint retro. Ruling basis: OWNER_RULINGS_2026-07-29.md R-3. Ultimate goal on the record: zero routine-operation touches; governance touches all judgment, no chores.*

## How to log
One row per touch. **Category:** `ROUTINE-OP` (a chore the machine should eventually do — must name its automation path) or `GOVERNANCE` (permanently human by Constitution §6 — logged, never minimized away). The Architect appends rows on the Owner's behalf when touches happen in-session; the Owner may append directly.

## Baseline (pre-log context, for honest retrospect)
| ID | Date | Touch | Category | Note |
|---|---|---|---|---|
| T-000a | ≤2026-07-27 | Started bridge agent + Supervisor on the lab machine; signed SUPERVISOR_CONTRACT v1.1 | GOVERNANCE + one-time setup | Agent now self-starts at logon (design D13) — the routine part already automated |
| T-000b | Gen 1, per sprint | git push/pull rhythm between Architect and Developer sessions; Go/No-Go rulings; window designations | Mixed | The push/pull chore is the largest surviving ROUTINE-OP; automation path: repository-hosted sessions / hooks (candidate work order after NP-S1) |

## Live log
| ID | Date | Touch | Category | Automation path (ROUTINE-OP only) | Status |
|---|---|---|---|---|---|
| T-001 | 2026-07-29 | Run the one-time bootstrap block: robocopy F:\QRF → F:\NeelPrajnaPro, Book-A copies, git re-point + push, freeze/pause markers in both legacy repos; paste outputs back | ROUTINE-OP (one-time) | None needed — unrepeatable by design; the connector cannot execute programs or copy binaries, so this is the irreducible first touch | PENDING |
| T-002 | 2026-07-29 | Drop the four .docx presentation copies + corrected mockups from the delivered zip into docs\planning\ and docs\reviews\ | ROUTINE-OP (one-time) | Connector writes text only; binaries need one manual drop. Future docx are generated in-session and delivered the same way — candidate automation: commit binaries via git from a Developer session instead of by hand | PENDING |
| T-003 | — | Ratification checklist (cutover rule, F-13 Auto-Adopt, three charters, window designation, α-budget, cost-model name, ARCH-NP-001 Go/No-Go) | GOVERNANCE | — | PENDING |

## Standing rule
A sprint retro that finds an unlogged human touch records it retroactively **as a finding** (species: invisible labor). What is not counted cannot be driven to zero.
