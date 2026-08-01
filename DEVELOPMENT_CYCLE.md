# DEVELOPMENT_CYCLE.md — NeelPrajnaPro's cycle law, task template & per-task ritual
*v1.0 · 2026-08-02 · Architect · Owner order O-013. Describes the cycle; the board
(comms\STATE.md) governs. If this document and the board disagree, the board wins
and the disagreement is a finding.*

## 1. The objective chain (why any task exists)
Every WO must trace, in one line on its board row, to a box in the Architecture
(docs\architecture\ Part A) or a rung in the Scientific Model. The programme's
anchors, binding on all work:
- **The wall (permanent):** QRF never trades; NeelPrajna never learns on its own.
- **Order of Inquiry:** existence → mechanism → prediction. A claim licensed at
  one stage never borrows a later stage's authority. No rung skipped.
- **Two Roots:** Records (what happened — append-only, hash-chained) never mix
  with Scientific Objects (what we think it means — versioned, evidence-gated).
- **Write authority (closed list):** store.append · Battery (verdict,
  window_burn) · Screener (trial_count) · belief.update (Verdicts only).
  Everything else proposes or reads.
- **Evidence law:** the bespoke NPSU stack is retired from evidentiary service —
  its data may migrate as records but carries ZERO epistemic weight, forever.
- **Cost model:** registrations cite the frozen `xauusd_retail_h07` venue entry;
  any change requires a NEW name. Tests may use other entries; registrations may
  not.
- **Data source:** Vantage only (O-009). Exness never enters this repo.
- **Arming stays human, forever** (Architecture B.6). The machine recommends;
  only the Owner arms.

## 2. The standard WO template (every backlog row, no field optional)
```
WO-<nn> · <title>
session:    S<nn> (label for commits/logs, not a fence — AM-02)
depends_on: <WO ids or —>
gate:       none | REVIEW-GATED | REVIEW-GATED STRICT | OWNER-CEREMONY
maps_to:    <Architecture box / Scientific-Model rung, one line>
spec:       <message id(s) that ratify what "correct" means>
write_set:  <exact folders/files; qrf\kernel\** and ivf\** only by explicit grant>
ATs:        <numbered, each independently checkable, quoted from the runner>
DoD:        ATs green in Developer's run + committed/pushed + board row updated
            citing the TEST-RESULT id + inbox message sent. DONE only after the
            Owner-side acceptance (two-key) at merge.
```

## 3. The per-task ritual (Owner order O-013 — binding on every WO)
1. **Read** the WO's spec messages + this file's §1 anchors. Ambiguity on any
   execution-capable component → QUESTION, pause per AM-03. Never guess.
2. **Build** inside the write set. Small honest commits (GIT_WORKFLOW §3).
3. **Validate — ALL acceptance criteria, no sampling:** run every AT of the WO,
   plus always: full suite (`.venv/Scripts/python.exe -m pytest tests/`, NO
   extra -q), the kernel firewall test, ruff on changed files, and any drill the
   WO's checkers require (a new guard is not trusted until shown RED). Quote the
   runner's own summary lines — never a hand-assembled count.
4. **Only when every AT is green** does the WO close dev-side. A red AT means
   fix-or-QUESTION; it never means proceed.
5. **Commit & push** the finished WO on dev: `S<nn>/WO-<xx>: <what> (refs <ids>)`.
   An uncommitted task is an unfinished task.
6. **Report:** one TEST-RESULT message to comms\architect.md (ATs quoted,
   commit hash, deviations owned); update the WO's board row citing that
   message id; record any Owner chat order in developer_console.md first.
7. **Move on** to the next unblocked WO (AM-02 priority order), or pause on a
   blocking doubt (AM-03), or run §7e handover if the window is fatiguing.

## 4. Acceptance & release rhythm
Accepts are batched (AM-02 §4): Developer messages "batch ready" → Architect
reviews diffs → posts REVIEW-RESULT APPROVED → Owner runs ONE line
(`tools/accept.sh <Snn> <A-id>`) → Architect reads comms\accept_<Snn>.log and
confirms per the COMPLETION RULE. Jobs the Owner must run arrive only as job
files (comms\jobs\pending\) executed by `./tools/run_job.sh`.

## 5. Message & console templates (verbatim shapes)
TEST-RESULT (Developer → architect.md):
```
id: D-0NN / type: TEST-RESULT / refs: WO-xx, S-nn / reply_to: <spec id>
requires_reply: NO / priority: NORMAL
subject: S<nn>/WO-<xx> CODE-DONE — <one line>
WHAT WAS BUILT: … (files, mechanisms)
ATs: AT-1 "…runner line…" · AT-2 "…" · (every AT, quoted)
DEVIATIONS/OWNED MISTAKES: … (or "none")
COMMIT: <hash> pushed on dev. Board row updated citing this id.
NEXT: <which WO, or pause reason per AM-03>
```
QUESTION (Developer → architect.md): id/type QUESTION/requires_reply YES/honest
priority · the exact spec text vs the exact file reality · a costed decision
menu (a), (b), (c) · what is parked meanwhile (AM-03 choice stated in one line).
CONSOLE entry (either console): id O-0NN · date · from OWNER (chat) ·
recorded_by · order: verbatim words. Cite an O-id only after it exists (I-05).

## 6. The honesty rules that outrank speed
Evidence decides, not exit codes. Zero results is never a quiet success. A
check is not trusted until it has been shown able to go RED. Statuses never
skip: nothing is DONE past an open AT. Mistakes are owned by id and forged into
rules — the incident log is the project's immune memory, not its shame list.
