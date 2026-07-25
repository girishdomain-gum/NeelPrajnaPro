# QRF Execution Process Guide — how we build, verify, and remember
Version 1.0 · 2026-07-25 · Authors: Owner (Girish) + Architect (fable)
Status: LIVING REFERENCE. Distilled from Sprints 1–4 as executed. This
document captures WHAT we do, HOW we do it, and WHY — as a reusable
template for this project and any future one built the same way.

---

## 1. Core philosophy

**Evidence before execution.** Nothing is believed because someone says
it — not the Developer, not the Architect, not a popular library, not a
beautiful backtest. A claim becomes true in this project only when an
independent mechanism has checked it and the check is on file.

**Prediction first, ontology later.** We do not start by declaring what
the market "is". We register predictions, test them on data nothing has
touched, and let the concepts earn their existence.

**Chat is scratch; files are the record.** AI sessions forget
everything. Consoles scroll away. So every decision, instruction,
ruling, sign-off, and lesson lives as a file in the git repository. If
it is not committed and pushed, it did not happen.

**Pictures illustrate, numbers decide.** Visual evidence (ADR-009) makes
claims human-checkable and archivable, but a verdict is always computed
from data. A screenshot can support or falsify; it can never be the sole
basis of a pass.

**Nobody is trusted on first contact — including the checkers.** Every
tool, every check, every detector is assumed wrong until a drill proves
it can catch planted fraud. The Architect's verification tools have
produced more first-contact bugs than the Developer's code (tally 10:2
at Sprint 4). That asymmetry is health: the side that writes the checks
gets checked hardest.

**Append-only truth.** The ledger (journal) never updates or deletes.
Corrections are new records pointing at old ones. Historical mistakes
stay visible with their reasons attached (e.g., an accepted AMBER),
because a record that can be quietly fixed is not a record.

---

## 2. The three parties (and the fourth)

| Party | Who | Powers | Hard limits |
|---|---|---|---|
| **Owner** | Girish (human) | Final say on everything. Runs commands, performs Human Checks, declares protected data (VIRGIN), signs off sprints with verbatim phrases. The only party who touches the real world (MT5, money, GitHub account). | Relays POINTERS between AIs, never content. |
| **Architect** | AI chat session ("Fable") | Writes instructions (ARCH-N), reviews (REV-SN), rulings (DEVQ replies), decisions (ADRs), process notes (NOTEs), and independent verification tools (IVF). Reads everything. | NEVER writes developer code. Writes only on `main`, only between Developer sessions. May READ the Developer's worktree mid-sprint, never write to it. |
| **Developer** | Claude Code (AI) | Writes all product code, tests, and scripts inside the repo on `claude/...` branches. Files DEVQs when anything is ambiguous. | Never edits `ivf/**` (verification is not self-graded). Never writes forbidden record types (enforced by tests + independent audit). |
| **Verifier** | IVF tools + the Owner's eye | The fourth party is a mechanism, not a person: independent re-implementations, drills, and captured visual evidence. | Independence rules: IVF imports nothing from product code; it re-derives from the written spec. |

Why three parties: separation of proposal (Architect), implementation
(Developer), and acceptance (Owner + Verifier). No party grades its own
homework.

---

## 3. Communication — everything is a file

All coordination lives under `docs/coordination/`:

- **`instructions/ARCH-N_*.md`** — the Architect's sprint instruction.
  Contains: read-first list, T0 (chain anchor), scope, out-of-scope,
  inlined normative contracts, acceptance criteria, required tests,
  Definition of Done, expected DEVQ areas, and the close-out plan.
  The Developer appends a COMPLETION REPORT to the same file.
- **`inbox/OPEN/DEVQ-N_*.md`** — Developer questions. Levels: QUESTION
  (proceed on recommended option; reversal must be additive) or BLOCKER.
  The Architect appends a REPLY with a ruling, then moves the file to
  `inbox/CLOSED/`. Closed threads are contracts; later completions get
  ADDENDA appended (e.g., the FVG definition).
- **`notes/NOTE-N_*.md`** — process lessons and FYIs, numbered after a
  fetch (IDs are allocated against the freshest tree).
- **`reviews/REV-SN.md`** — the Architect's sprint review: code review,
  verification results, findings (F-N), remaining steps, verdict.
  Sign-offs are appended as ADDENDA with the Owner's VERBATIM phrases.
- **`reviews/GO-SN.md`** — the sprint-close record: decision, both
  verbatim phrases, the full formula (AC+VC+HC+Drill), ledger state and
  record ids, ratified contracts, and a RETROSPECTIVE section (standing
  practice from Sprint 3, proposed by the Owner).
- **`sessions/S{N}-{k}_YYYYMMDD.md`** — the Developer writes a session
  log EVERY session (no-console rule). A session without a pushed log
  did not happen. Missed once (NOTE-011); healed with a RETROACTIVE log.
- **`docs/adr/ADR-N_*.md`** — architecture decisions (e.g., ADR-009
  visual evidence layer). Anyone may propose; the Owner accepts.
- **`docs/handover/ARCHITECT_HANDOVER.md`** — the Architect's memory
  across sessions. REWRITTEN AT EVERY GO-SN (protocol duty). Its final
  section always tells the next session how to VERIFY the handover
  itself before trusting it.

**The Owner-command rule (PROTOCOL v1.3, requested by the Owner):**
every command any AI or script gives the Owner must be COMPLETE
(copy-paste ready, no `...`, no `<placeholders>` — filled examples with
plain instructions on what to change), BASH-READY (git-bash syntax,
forward slashes, `/c/...` drive paths), and PLAIN (simple-English
explanation of what it does, what to expect, what to do if it fails).
Exactness is kindness.

---

## 4. Git, GitHub, branches, worktrees

- **One private repo** (`qrf` on GitHub). `main` is the shared truth.
- **The Architect writes directly to the working tree on `main`**
  (between Developer sessions); the Owner commits with an `ARCH:` prefix
  and pushes. Architect writes propagate ONLY via commit+push (NOTE-003).
- **The Developer works in a git worktree** it creates under
  `.claude/worktrees/<branch>/` on a `claude/arch-N-...` branch,
  pushing EVERY commit (push-per-commit). It merges to `main` and pushes
  at completion. The main folder stays parked on `main` all sprint —
  mid-sprint status lives in the worktree (NOTE-010), readable by the
  Architect at the Owner's request.
- **Status reads require freshness** (NOTE-004): compare
  `refs/heads/main` vs `refs/remotes/origin/main`, check FETCH_HEAD age,
  and never assert "not started" from an unverified lens.
- **Heavy data does not travel via git.** `datastore/bulk/` (parquet) is
  gitignored; only the journal and manifests are tracked. Every dataset
  must be REBUILDABLE: ingest/detector/screener scripts carry a
  `--rebuild-bulk` mode that regenerates files deterministically and
  verifies them against the EXISTING manifests, writing nothing to the
  journal. Hand-copying from worktrees is banned (learned twice, F-1/F-5).
- Verification evidence (JSON reports, HC PNGs) IS tracked, under
  `ivf/reports/`. Drill scratch (tampered copies) is gitignored — a
  deliberately corrupted dataset must never sit in the repo where
  anything could mistake it for data.

---

## 5. The sprint lifecycle, step by step

1. **ARCH-N written** by the Architect (during a write window), pushed
   by the Owner (`ARCH:` prefix).
2. **Owner boots the Developer** with a one-liner: "Boot per CLAUDE.md,
   execute ARCH-N completely, starting with T0. Session log every
   session."
3. **T0** — the Developer appends the previous GO note to the journal,
   parented to the sprint chain. Every record of the sprint descends
   from it.
4. **Development** on the worktree branch: code + tests together
   (a module without its tests is not done), DEVQs filed for anything
   ambiguous (non-blocking QUESTIONs proceed on the recommended option),
   session logs every session, push-per-commit.
5. **Completion report** appended to ARCH-N; merge to main; push.
6. **Architect rulings** — DEVQs answered and CLOSED; micro-tasks may
   be spawned (one short Developer session).
7. **IVF phase (Architect deliverables):**
   - Write independent CHECKS (re-implemented from spec text, no
     product imports).
   - Write the DRILL (planted fraud the checks must catch).
   - **RUN THE DRILL FIRST** — before the check touches anything real
     (standing rule earned in Sprint 4). A drill that says MISSED is a
     finding about the CHECK.
   - Run the real check. GREEN proceeds; AMBER gets a written reason
     (accepted or fixed); RED freezes everything until understood —
     RED between two independent implementations is the system's
     highest-value moment (it completed the FVG definition).
8. **Human Check (HC)** — the Owner's eye on captured evidence
   (see §7). Verbatim phrase (e.g., "HC-S4 PASS") recorded in REV-SN.
9. **Go/No-Go** — the Owner alone. Formula: **AC + VC + HC + Drill.**
   Verbatim sign-off phrase (e.g., "Signed off — Sprint 4 closed").
10. **Close-out writes (Architect):** GO-SN (with Retrospective) →
    ARCHITECT_HANDOVER.md rewritten → ARCH-(N+1) opened. Owner pushes.

**Write windows:** the Architect writes files only when no Developer
session is active and the Owner has confirmed `(main)`. The signal is
the Owner saying "write window" (and the Architect verifying refs
before believing it).

---

## 6. Tests and validation — the full stack

Layered, from inner to outer; every layer has caught something real:

1. **Unit + property tests (Developer).** Contracts, hand-computed
   examples ("to the cent"), determinism (same seed → byte-identical),
   and PROPERTY tests for causality: feed data incrementally and assert
   emissions/fills never change retroactively (anti-hindsight, §4.3).
2. **Structural firewalls (CI).** Kernel purity by AST/token scan;
   type-level audits proving a module CANNOT write forbidden record
   types (the screener cannot produce a verdict, by construction).
3. **Calibration (per instrument).** Every detector/judge passes
   planted-truth (must find it), structured-noise silence (must stay
   quiet), and insufficient-data cases before it may produce records.
   Failed calibration BLOCKS — no soft pass. Version bump ⇒
   recalibration.
4. **IVF checks (Architect, independent).** Re-implementations from the
   written spec, importing nothing from product code, run over REAL
   outputs: exact row/price accounting, full event recomputation
   (105/105), cross-counts (grid size == trial count), source audits.
   Verdicts GREEN/AMBER/RED with named findings; zero-findings-of-the-
   audited-thing is AMBER (vacuity is never silence — Sprint 4 bug #8).
5. **Drills (fraud injection).** Planted silent repairs, planted
   verdict-writers, planted under-counts, tampered quarantine — the
   checks must CATCH and NAME them, with correct controls unflagged.
   Drills gate the checks; checks gate the code.
6. **Human Check with captured evidence (ADR-009).** See §7.
7. **Protected data (VIRGIN).** A trailing reserve declared by the
   Owner's typed phrase (`DECLARE VIRGIN`), guarded in code
   (ContaminationError), spendable only once per lineage by the battery
   under a pre-registered hypothesis (WindowBurnedError on reuse).

---

## 7. Visual evidence (ADR-009) — the screenshot layer

Born from the Owner's proposal at Sprint 3: replace "trust me, I
looked" with captured, self-proving pictures.

**The pipeline:** a seeded Python SAMPLER picks rows/events from the
real parquet and emits an input file (two lines: PROV provenance line +
entries). An Architect-owned MQL5 SCRIPT (in `ivf/mt5/`, hand-copied to
the MT5 Scripts folder — repo copy is truth) reads the file, navigates
the chart, draws markers/zones, stamps captions, and saves PNGs.

**What a valid capture contains:** the claim (values from QRF records),
what MT5's OWN series shows (an independent lens — where possible the
script RECOMPUTES the object from its own bars and stamps
MATCH/MISMATCH), the verdict, and a PROVENANCE line: dataset, manifest
id, seed, tool name + rev. The PNG proves itself without the chat.

**Hard-won tool rules (S3/S4 bug history, baked into every new tool):**
input via FILE not the input dialog (truncation); print ABSOLUTE paths;
VERIFY navigation before capture and mark `_NAVFAIL` otherwise; capture
with ALIGN_LEFT after navigating; UTC vs server-time offset can only
fail loudly, never fake a MATCH; captions must not truncate or collide
with the chart title.

**The human stays in the loop.** The Owner confirms the chart context
and visually judges each capture; the Owner's eye caught a real bug
(wrong-year capture) that numeric logs hid. HC without a human is just
another VC. Evidence is archived in `ivf/reports/hc_sN/` and cited by
GO-SN.

---

## 8. Bugs, findings, and the tally

- Every defect is a FINDING, recorded where it was caught (NOTE, REV
  F-N, DEVQ addendum, drill report) — never silently fixed.
- **First-contact bug tally** per party (Architect 10, Developer 2 at
  GO-S4), kept honestly in GO retrospectives. Its purpose is not blame:
  it calibrates trust ("expect your own tools to be wrong first") and it
  proves the catching machinery works. Every one of the twelve was
  caught BEFORE anything real depended on it.
- A RED between independent implementations is treated as treasure:
  stop, inspect real evidence (the Owner pulled the actual bars), rule
  in writing, encode the completed contract, re-run.
- Definitions discovered to be underspecified get completed IN THE
  RECORD (DEVQ addendum) — the ruling includes the evidence that forced
  it.
- Ruling hygiene (added at GO-S7, bought by Architect bugs #11–13 and
  one near-miss): (1) numeric worked examples in rulings are
  MACHINE-VERIFIED before the ruling ships; (2) an independent
  re-implementation reads the NORMATIVE definition (spec/docstring),
  never prose summaries or completion reports; (3) every written
  artifact (input files, configs) is READ BACK and compared against its
  source before use. Instructors are audited like everyone else — the
  Developer catching a ruling's arithmetic is the system working, not
  failing.

---

## 9. Retrospection and memory

- **GO-SN Retrospective** (standing section, Owner's proposal): what
  went well, what to improve, what carries forward. Written at every
  close; carried items reappear in the next ARCH.
- **ARCHITECT_HANDOVER.md**: the Architect's cross-session memory,
  rewritten at every GO. It always ends with "how to verify state
  yourself before trusting this file" — memory that demands
  re-verification is the only honest kind for an amnesiac author.
- **NOTEs** capture process lessons the moment they are paid for.
- **AI_PROJECT_STATE.md** is GENERATED (gen_state) — derived status is
  recomputed, never hand-edited.
- The Owner's own additions to the process (retrospectives, visual
  evidence, the command rule, this guide) are recorded with attribution
  — the process improves by the same evidence-first loop as the product.

---

## 10. Reusing this template on a new project — checklist

1. Freeze an architecture; write a Blueprint whose every section says
   what to type; define the record/ledger contract first.
2. Stand up the three roles + PROTOCOL (session logs, write windows,
   pointers-only relays, Owner-command rule, worktree visibility,
   handover duty at every close).
3. Sprint 1 is always the LEDGER (append-only, hash-chained, verified);
   nothing else exists until the record does.
4. Every capability enters as an instrument: registered, versioned,
   calibrated against planted truth/noise before it may speak.
5. For every sprint: instruction → T0 chain → build with tests → DEVQs
   → completion → independent checks → drill the checks FIRST → human
   check with captured evidence → Owner's verbatim Go/No-Go →
   close record with retrospective → handover rewrite → next
   instruction.
6. Protect the future: declare the untouchable reserve early, guard it
   in code, and spend it only under pre-registration.
7. Keep the tally. Expect the checkers to be the buggiest. Celebrate
   every RED that turns out to be a definition getting completed.

---

*This guide reduces process uncertainty; it does not eliminate
judgment. Where practice and guide disagree, stop, record a NOTE,
decide once, amend here. — v1.0*
