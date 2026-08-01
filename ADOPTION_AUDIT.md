# ADOPTION_AUDIT.md — F:\NeelPrajnaPro
*Phase A output of kit\EXISTING_PROJECT_ADOPTION.md · Architect · 2026-08-01*
*Owner rulings already given (chat, 2026-08-01): (1) this chat's assistant is the Architect; (2) the Fable kit model governs — only and only the kit; (3) everything related to the existing process — sprint execution docs, validation-process docs, coordination machinery — retires to archive forever (retire = move, never delete; kit law).*

---

## 1. REALITY MAP — what actually runs today

**Code truth lives in git.** Remote: `https://github.com/girishdomain-gum/NeelPrajnaPro.git` (private). Local HEAD: `main`. The live working branch is `sprint/NP-S2` (tip ≈ T-058); `main` last moved at NP-S1's close. ~10 stale `claude/*` work branches and 2 `maint/*` branches exist — normalization candidates.

**What genuinely runs (verified from the last two session logs, 2026-07-31):**
- `pytest tests/` via the repo's own `.venv` (Python 3.13, uv-managed): **887 passed**, 1 known pre-existing failure (`tests/adapters/test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags` — missing external CSV).
- `tests/test_kernel_firewall.py` — the wall test (8 passed): kernel imports no trading code.
- `ivf/` — independent verification: journal verifier + drilled checks (NP-S1: 6/6 drill, GREEN).
- `scripts/` — the real pipeline: `ingest_*`, `register_*`, `judge_*`, `rebuild_bulk.py` (`rebuild_all()` now covers all 5 journaled lineages h001–h004 + h007).
- `datastore/` — the append-only hash-chained ledger (journal + bulk + index). This is the project's crown jewel and is healthy.

**External data dependencies (on this machine, undocumented as requirements):**
- `F:\NeelPrajna\Validation\Stage2\parquet` (raw Vantage ticks — needed by `rebuild_all()`).
- IVF export CSVs (one missing → the single red test).

**No MT5 terminal is in this repo's loop.** `ivf/mt5/` content is reference only. This is a pure-Python research repo; the kit's deploy.bat / bridge / TERMID machinery does not apply here in v1 (see §5, Decisions D-5).

**Last three real runs:**
1. 2026-07-31 · SNP-S2-02 (ARCH-NP-005): rebuild_bulk h007 lineage fixed; suite 887 green; h007 manifest reproduces byte-identically.
2. 2026-07-31 · SNP-S2-01 (WO-P): execution-model parity capability shipped (`engine.s5.2`); AC-1..AC-7 pass.
3. 2026-07-30 · NP-S1 close: first integrated verdict `01KYSGQR3D8SYSVJFSF9M77CMY` (FAIL, 259 trades, p 0.0574), IVF re-derived it after its own drill; Owner GO.

**The honest score:** the science works (1 real drilled verdict). The process around it required, in ~3 days: 5 revisions of CLAUDE.md, 57 one-off T-scripts in `ops\`, 13 session logs, 5 DEVQs, findings F-13…F-28, 3 ADR numbering/provenance corrections, and a retired state-file with an orphaned generator (`scripts/gen_state.py` → NOTE-NP-004). That ratio is the disease this adoption cures.

## 2. IN-FLIGHT LEDGER — unfinished work someone cares about

| # | Item | Where it stopped | Evidence it works so far | Board status at seeding |
|---|---|---|---|---|
| 1 | **NP-S2 core: R6 long run + Observation-Engine NP feed** | Not started; precondition (execution parity) now met by WO-P | WO-P AC-1..7 green on `sprint/NP-S2` | PENDING (largest item; becomes its own session) |
| 2 | **Wire a detector to the new per-trade stop column** | Capability built (WO-P), deliberately not wired | Engine tests green; no detector uses it yet | PENDING |
| 3 | **Red test: missing IVF export CSV** (`test_mt5_csv.py`) | Documented by WO-P, untouched since | Failure reproduces; cause known (external file) | PENDING — proposed **First Resume Task** (small, real, provable) |
| 4 | **`sprint/NP-S2` → `main` reconciliation** | Sprint open; branch ahead of main | Both tips on origin | PENDING-VERIFY (git normalization, Phase C.3) |
| 5 | WO-Q (STATUS.md generator / ARO ladder) | Designed only | None | RETIRE-to-legacy — **superseded by the kit's STATE.md board** (it was a hand-rolled version of exactly what the kit ships) |
| 6 | Unratified design backlog (ARO ADR, org/roles ADR, repository-autonomy v3, detector-fingerprint) | Drafts in `ops\` | None (never ratified) | RETIRE-to-legacy per Owner ruling 3 (quarry if ever needed) |
| 7 | Doc corrections carried from NP-S1 (F-23, F-24 docx twin, Architecture §2/§3.2, V&V §3.4) | Queued | — | DISSOLVED by Owner ruling 3: the docs they correct retire to archive; the *specs* that survive get one-line legacy stamps instead |
| 8 | Stale `claude/*` branches ×10 | Merged or abandoned | On origin | PENDING (cleanup line in git normalization) |

DEVQ inbox: `OPEN\` empty (does not exist — correct meaning: no open threads). All 5 DEVQs CLOSED and honored.

## 3. KEEP / QUARRY / RETIRE — one verdict, one reason each

**KEEP (the product — untouched or lightly stamped):**
| Thing | Reason |
|---|---|
| `qrf/` (kernel + trading), `tests/` (887), `ivf/` + drills, `datastore/` ledger, `configs/`, `hypotheses/`, `scripts/` pipeline, `pyproject.toml`/uv, full git history, `.github/` CI | This IS the project. The architecture is simple and sound; the wall test enforces it. Nothing here changes in adoption. |
| Normative specs the code answers to: H-07 sealed definition (Exec-Plan §5 → extracted), `docs\architecture\` master (.md), `docs\scientific_model\`, `docs\constitution\` (the wall, the permanently-human powers) | **Doc-is-spec**: IVF re-derives verdicts from normative texts; retiring the spec would orphan the verifier. They move to a flat `docs\spec\` shelf as *reference specs* — they describe; only the board governs. |
| `docs\journal\` + `datastore\journal\` | Append-only records are history; kit law: never delete history. Frozen — new governance events go to the board/handovers, not here. |

**QUARRY (heavy code/process mined for mechanics, then shelved):**
| Thing | Reason |
|---|---|
| `ops\` ARO process suite (v1.0/v2.0), `REPOSITORY_AUTONOMY_v3.0`, `SPRINT_STATE_MACHINE_v1.1`, WO-Q design | Exactly the kit's AM-10 precedent: tooling heavier than its documentation. Fable declined this class on purpose and never missed it. → `docs\legacy\` |
| `scripts/gen_state.py` (+ its test) | Orphaned since a6823c3; its job is the STATE board's now. → `tools\legacy\` |
| 57 `T-0xx` PowerShell rituals | One-off history; useful patterns only. → `ops\legacy\` |
| ten-section HANDOVER shape (`ops\aro\handovers\`) | Good pattern; the kit's handover template supersedes; keep as examples. |

**RETIRE-to-archive forever (Owner ruling 3 — the process layer):**
| Thing | Governance test result |
|---|---|
| CLAUDE.md rev 5, `docs\roles\` (Roles & Communication), boot sequences | Replaced verbatim by kit BOOT_PROMPT_ARCHITECT / BOOT_PROMPT_DEVELOPER + COMMS_PROTOCOL (constants adapted, laws untouched). |
| ARCH / DEVQ / NOTE / session-log species, `docs\coordination\` | Five artifact species to say four things. Replaced by kit comms\: two inboxes, two consoles, one STATE board, handovers. |
| Structure Law (`docs\README.md`), **md+docx twin rule**, `docs\writing_standard\` | Gate nothing an Owner can name; twins already went stale once (F-24). All .docx renders → archive. |
| Execution Plan v2.0 as *governing* document, `THE_ONE_PAGE`, vision/vv_plan/automation/reports/research/reference/reference_volumes/specs/books as *governing* folders | Content mined: §0 state → STATE.md seed rows; sprint ladder → future board sessions; the rest → `docs\legacy\` with an INDEX.md line each. The **scientific qualifications inside them survive** — NP-S1's verdict qualification travels onto its board row verbatim, as ruled ("quote it, never paraphrase"). |
| Journal J-/F-/T-numbering as live governance | Frozen as history. New mistakes get owned by id in the kit's way (incident → rule), on the board. |

## 4. PAIN LIST — Owner's words (adoption is judged against this)
1. *"This project become unnecessary very complex from user point of view and development and validation point of view."*
2. *"Its architecture is simple but development validation is highly complex and architecture development communication etc."*
3. *"I am losing grip of understanding... too many documents."* (2026-07-29, recorded in THE_ONE_PAGE)
4. Owner ruling: *"we will follow only and only kit model"* — one process, not a bespoke one per project.
5. Owner ruling: the entire existing process layer goes to archive forever.

**Success measure (kit's own line):** on any evening the Owner can type one line into one window and trust what comes back.

## 5. DECISIONS — Phase B (Owner: confirm or amend each, one short exchange)
- **D-1 Paths:** project root `F:\NeelPrajnaPro` · source = `qrf/` + `scripts/` + `ivf/` · git remote exists (above) · no EA folder, no TERMID (D-5).
- **D-2 First Resume Task (small on purpose):** In-flight item 3 — make `test_mt5_csv.py` green or formally baseline it (locate/regenerate the CSV, or convert to a skipped-with-reason external-data test recorded on the board). One session, real evidence, proves the loop.
- **D-3 Freeze Line:** everything not in §2's ledger is frozen reference until explicitly resumed as a future session.
- **D-4 Git normalization:** keep ALL history; reconcile `sprint/NP-S2` → `main` so main = current accepted reality; create `dev`; add `comms/` (+ `bridge/` if ever installed) to `.gitignore` in the first new commit; delete-nothing, prune stale `claude/*` branch *pointers* only after main contains their work.
- **D-5 MT5/bridge scope:** Python-adapted adoption. deploy.bat + np_agent bridge NOT installed now (nothing to deploy to a terminal); installed later only if MT5 jobs enter this repo's loop. Acceptance tests adapted accordingly (§6).
- **D-6 One-window law (v1.6 / O-051):** Owner confirms all old NeelPrajnaPro Architect/Developer chats are closed with a handover note before Phase C. **Required: yes/no.**
- **D-7 Comms location:** kit way — gitignored `comms\` at root; `docs\coordination\` freezes into archive.

## 6. ADOPTION ACCEPTANCE TESTS (Python-adapted; nothing resumes until these pass)
- **AT-AD1** Boot round-trip: fresh Architect + Developer windows boot from the adapted kit prompts, read handovers, exchange one message through comms\.
- **AT-AD2** (was compile): full `pytest` + firewall run through the new loop, result pasted to console by the Owner-executed ritual; the one known red baselined in writing.
- **AT-AD3** One real verification end-to-end: `ivf/verify_journal.py` (or drill runner) against the live ledger; result recorded honestly on the board — a failure is a FINDING row, not a blocker.
- **AT-AD4** Drill law: the two most safety-critical checkers (journal hash-chain verifier + firewall test) each shown able to go RED via a tamper drill on a throwaway copy, then GREEN on control.
- **AT-AD5** Evidence signed: Owner eyeballs and two-key signs the AT-AD2/AT-AD3 outputs.
- **AT-AD6** (adoption-specific): after archiving, `pytest` still 887-green and firewall green — proving the process layer's removal touched zero product code.
- Close of Phase D: point-by-point reply to §4's pain list; unaddressed pains become board rows.

## 7. WORKSHEET
| Field | Value |
|---|---|
| Project root | F:\NeelPrajnaPro |
| Source folders | qrf\ · scripts\ · ivf\ · tests\ |
| Git remote (private) | github.com/girishdomain-gum/NeelPrajnaPro |
| Laboratory TERMID | N/A (no MT5 in loop — D-5) |
| Terminal INSTALL folder | N/A |
| Symbol / digits / --point | XAUUSD (from real CSV at first need; never assumed) |
| First resume task (small!) | D-2: the missing-CSV red test |
| Old chats closed + handover (v1.6) | **AWAITING OWNER (D-6)** |
| Top execution pains | §4, Owner's words |

---
*Phase A complete. Nothing was modified; this file is the phase's sole output. STOP — awaiting Owner ruling on §5 D-1…D-7 before Phase C (INSTALL).*
