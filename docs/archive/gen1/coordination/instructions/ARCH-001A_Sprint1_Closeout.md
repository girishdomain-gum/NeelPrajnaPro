# ARCH-001A · Sprint 1 Close-Out · 2026-07-24
Author: architect (fable) · Level: INSTRUCTION · Status: OPEN
Parent: ARCH-001 (delivered; this instruction closes it)

## Context (read first)
1. `docs/coordination/inbox/CLOSED/DEVQ-001_gen_state_writes_docs.md` —
   your question, answered: decision C; CLAUDE.md is rev 2.
2. `docs/coordination/reviews/REV-S1.md` — your Sprint 1 review:
   APPROVED, three observations queued for Sprint 2.
3. `docs/coordination/notes/NOTE-002_ivf_first_run_bug.md` — the IVF
   verifier crashed on first run (Architect's bug, fixed in rev 2).
4. `ivf/verify_journal.py` (rev 2) — you may READ it and RUN it, but
   never edit it (IND-1: IVF is Architect-side).

## Tasks (in order)

### T1 — Run gen_state.py against the real state file (DEVQ-001 = C)
`docs/handover/AI_PROJECT_STATE.md` via the generator only. Confirm the
two hand-maintained sections survive byte-for-byte.
Commit: `ARCH-001A: gen_state first run (DEVQ-001=C)`.

### T2 — Seed the genesis records
The journal does not exist yet. Append exactly two `note` records via
RecordStore (producer `human:girish` — these are Owner statements you
are transcribing):
1. "Genesis: QRF journal initialized. Sprint 1 (ledger core) delivered;
   IVF Go/No-Go in progress."
2. (parents=[record 1]) "IVF first-run finding: verifier rev1 crashed
   on missing-file path; fixed rev2. See NOTE-002."
Print both record_ids.
Commit: `ARCH-001A: genesis records` (journal is tracked; it will be
in the diff — that is correct).

### T3 — Verification check (VC)
Run: `ivf/verify_journal.py datastore/journal/journal.jsonl
      --report ivf/reports/s1_verify.json`
(create `ivf/reports/`). Expected: records=2, verdict=GREEN.
If RED: STOP, do not fix anything, file a DEVQ (BLOCKER,
tag `architecture-conflict` if the disagreement is between the
implementation and the verifier — that is exactly the disagreement the
IVF exists to surface).

### T4 — Drill S1 (planted tamper; the verifier must catch it)
Programmatically, on a COPY only:
- copy the journal to a temp path OUTSIDE datastore/
- flip exactly one character inside the payload text of record 2
- run the verifier on the copy with
  `--report ivf/reports/s1_drill.json`
Expected: verdict=RED with a `C2.<record2_id>.content_hash` finding
naming record 2. Delete the tampered copy afterwards. The real journal
must be untouched (re-run T3's command to prove it; still GREEN).
If the verifier does NOT go RED: STOP — that is a failed drill; DEVQ,
BLOCKER.

### T5 — Close the books
Append to ARCH-001's completion report a short
`### CLOSE-OUT (developer)` block: record_ids, T3/T4 verdicts, report
file paths, and confirmation the real journal re-verified GREEN.
Commit everything; `git push`.

## Out of scope
Any edit to ivf/**, docs/** (beyond the state file via generator and
the ARCH-001 completion-report append), any Sprint 2 work.

## Reserved for the Owner (not yours)
- HC: read both journal records raw in a text editor (5-record read,
  scaled to the 2 that exist) and confirm they say what he meant.
- Final Go/No-Go sign-off per IVF §8 — the Architect will collect it.

## Definition of Done
T1–T5 complete, pushed; expected verdicts observed (GREEN / RED-naming-
record-2 / GREEN); close-out block appended; zero edits outside
permitted paths.
