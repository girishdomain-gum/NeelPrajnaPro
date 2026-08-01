# ROADMAP.md — The Executable Plan to the Objective
*v1.0 · 2026-08-02 · Architect · Owner order O-014. Companion to
DEVELOPMENT_CYCLE.md (the ritual law). This file lists EVERY work order of the
whole development cycle, phase by phase, each with its own VALIDATION PLAN.
Describes the road; comms\STATE.md governs the day. Board wins on conflict.*

## The objective (Architecture Part A, verbatim intent)
Turn every TARGET box BUILT, honestly: R6 execution-feedback pipeline →
Observation Engine NP feed widened → first NP EXISTENCE judgment (ECF, NP-S3
window) → Knowledge Graph + versioned Belief releases → Communication Contract
v2 with the Publication Boundary → (only after Gate A) machine-proposed Pattern
Evolution. The wall stands throughout: QRF never trades; NeelPrajna never
learns on its own. Arming stays human forever.

## THE STANDARD VALIDATION GATE — "V-GATE" (runs at the end of EVERY feature)
No WO closes, and no next WO starts on top of it, until ALL of:
  V1. Every AT of the WO green, quoted from the runner (no sampling).
  V2. Full suite green (`.venv/Scripts/python.exe -m pytest tests/`, no -q)
      + kernel firewall test green — both summary lines quoted.
  V3. Every NEW checker/guard tamper-drilled RED on a copy, then GREEN control.
  V4. ruff clean on changed files.
  V5. Committed+pushed on dev (`S<nn>/WO-<xx>: ... (refs ...)`); TEST-RESULT
      message in comms\architect.md; board row cites it; consoles current.
  V6. Architect diff review at batch time → REVIEW-RESULT APPROVED.
  V7. Owner accept: ONE line `tools/accept.sh <Snn> <A-id>`; Architect reads
      comms\accept_<Snn>.log; COMPLETION RULE closes it.
  V8. VERDICT-BEARING features only: IVF re-derives independently, after its
      own drill (Architecture B.7). Origin grants no shortcuts.
  V9. CEREMONY features only: the Owner's typed confirmation on the record.
Legend below: each WO lists gate, maps_to, and its VALIDATION PLAN (which
V-gate items beyond V1-V7 apply, plus WO-specific proof obligations).

════════ PHASE P1 — R6 PIPELINE COMPLETE (Sessions S3-S4) ════════
Maps_to: "Execution feedback → Core (R6)" + "Observation Engine NP feed".

WO-03 · R6 foundations (scope mechanism, DST/UTC, ingest_r6, EventFrame
fidelity) · gate: approved (A-007/A-012/A-014) · STATUS: CODE-DONE, one
addendum open. VALIDATION: D-010 AT-1..5 + A-014 unregistered-dataset refusal
drill (RED) + V1-V7. Done-when: "934+1 passed" quoted, batch-accepted.

WO-10 · R6 ACTIVATION · gate: OWNER-CEREMONY · depends: WO-03 + first real
Vantage export. VALIDATION: zone pinned from quoted real evidence bracketing a
DST transition; ingest refusal-before-pin and acceptance-after-pin BOTH shown;
burn-check AT re-run on the ACTIVE scope; OOS designation typed → resolved span
echoed → Owner confirms (V9) → sealed + journaled; V1-V7. Done-when: scope
ACTIVE record in the journal citing the ceremony.

WO-11 · Observation-Engine NP feed for R6 · gate: none, ZERO new semantics.
VALIDATION: existing observatory suite untouched-green; new test proves an
R6-shaped event batch flows through with level/zone columns populated; no
writes outside the engine's contract; V1-V7.

WO-14 · R6 COLLECTION OPERATIONS (recurring, calendar-long) · gate: none after
WO-10 · the Owner exports Vantage ticks (~weekly) → JOB file → ingest_r6 →
journal batch record. VALIDATION per batch: RESULT: OK in the job log read by
the Architect; batch record appended (count grows by exactly 1); refusal on any
overlap/gap anomaly is a FINDING row, never silently skipped. Periodic:
ivf\verify_journal GREEN monthly. This WO closes only when the OOS window's
span completes.

WO-13 · IVF coverage for the R6 ingest path · gate: REVIEW-GATED (proposal) ·
VALIDATION: stage A = proposal message (batch continuity, UTC monotonicity,
zone-pin presence, journal linkage); Architect implements/commissions IVF-side;
the new IVF check is itself tamper-drilled RED before first trusted GREEN (V3
on the verifier itself).

──────── V-GATE P1 (phase exit) ────────
All five WOs at DONE · full suite + firewall quoted green · verify_journal
GREEN on the live ledger · WO-04-tail swept · board shows zero open P1 rows.
Phase P1 turns Part A's "Execution feedback → Core" box from TARGET(CSV
exists) to BUILT — the first box this cycle flips.

════════ PHASE P2 — LEDGER & LEGACY HYGIENE (Session S5, parallel-friendly) ════════
WO-08 · WindowLedger internal consistency + burn-accounting checker
(scripts/check_window_ledger.py) · gate: none (spec A-016) · VALIDATION: every
RED class (orphan burn, malformed span, overlapping burns same dataset+lineage,
reserve mismatch) tamper-drilled on copies; control GREEN on the real ledger;
V1-V7.

WO-07 · NPSU CSV → RecordStore/BulkStore migration · gate: REVIEW-GATED
two-stage (NP-D-012) · stage A: read-only INVENTORY + draft spec
(REVIEW-REQUEST); stage B on ratification. VALIDATION (B): idempotent re-run
proof (second run changes nothing, shown); every migrated record MECHANICALLY
typed zero-epistemic-weight (Architecture B.1) with a test proving no verdict/
burn/trial/belief path can consume it; counts reconciled source-vs-store;
V1-V7. Done-when: reconciliation table quoted + hygiene checker (WO-08) still
GREEN after migration.

──────── V-GATE P2 ────────
Both DONE · WO-08 checker GREEN post-migration · F-DOC-1 (17 vs 18 founding)
resolved by counting journal records, one-line doc correction committed.

════════ PHASE P3 — FIRST NP EXISTENCE JUDGMENT (the NP-S3 window; Sessions S6-S7) ════════
Maps_to: "Pattern Learning — first NP existence judgment" + Scientific Model
Diagrams 1/4/5 (Order of Inquiry · Lifecycle rungs · ECF).

WO-12 · ECF EXISTENCE-JUDGMENT PLAN · gate: REVIEW-GATED STRICT · the plan
names: hypothesis (from the founding registry), claim form E1/E2/E3, its null
family N1/N2/N3, the definition-trap check, dataset+window to be BURNED, cost
model = xauusd_retail_h07, α-accounting via TrialCountLedger. VALIDATION: my
APPROVED + the Owner's explicit burn authorization (V9) — no run before both.

WO-15 · ECF NULL LIBRARY (Diagram 7's TARGET half) · gate: REVIEW-GATED ·
implement the null constructions the approved WO-12 plan names · VALIDATION:
planted-truth (null correctly destroys a fabricated-by-definition rate) AND
clean-control (null spares a genuine planted effect) both shown; V1-V7.

WO-16 · THE JUDGMENT RUN · gate: OWNER GO/NO-GO (V9) · Battery nine-step on
the pre-registered hypothesis; atomic verdict+burn. VALIDATION: Battery
selftest gate green before the run; verdict record + burn record appear
atomically (count +2, linked); the verdict's sealed figures quoted verbatim on
the board with any Owner qualification QUOTED NEVER PARAPHRASED; V1-V7.

WO-17 · IVF RE-DERIVATION of the verdict · gate: independent (Architect-side
commission per WO-13's pattern) · VALIDATION: V8 in full — IVF drills its own
checks RED first, then independently re-derives the verdict from normative
texts + the ledger; GREEN or the discrepancy is a HIGH finding that freezes P3.

──────── V-GATE P3 ────────
A drilled, IVF-confirmed existence verdict (PASS or FAIL — both are success;
the FAIL of NP-S1 is the model) in the ledger · windows burned exactly as
authorized · Pattern Learning box: TARGET → first artifact exists.

════════ PHASE P4 — KNOWLEDGE & BELIEFS (NP-S3/S4; Session S8) ════════
Maps_to: "Knowledge Graph" + "Statistics & Confidence enrichment" + Graduation
Ladder (Diagram 7 of the Scientific Model).

WO-18 · Belief update from the P3 verdict · gate: REVIEW-GATED · belief.update
consumes Verdict-typed input ONLY (closed write-authority). VALIDATION: a test
proving non-Verdict inputs are refused (RED drill); belief state change traced
to the verdict id; V1-V7.

WO-19 · Knowledge release format v1 (versioned, dated belief releases) · gate:
REVIEW-GATED · sealed figures only, frozen at release date. VALIDATION: a
release artifact is reproducible byte-identically from the ledger; contains NO
unsealed/rolling statistic (negative test proves the refusal); V1-V7.

──────── V-GATE P4 ────────
One versioned Knowledge release derived end-to-end from a drilled verdict.

════════ PHASE P5 — CONTRACT v2 + PUBLICATION BOUNDARY (NP-S4; Session S9) ════════
Maps_to: "Continuous Communication" + B.4 (six object types, two prohibitions).

WO-20 · Contract v2 object schemas (Observation · Pattern · Knowledge ·
Recommendation · Execution Feedback · Performance — nothing else) · gate:
REVIEW-GATED · VALIDATION: schema tests refuse a seventh type (RED); the two
prohibitions are TESTS (runtime cannot query kernel internals; kernel object
set contains no BUY/SELL); V1-V7.

WO-21 · Publication Boundary implementation (batch release-as-event, dated;
publishes WHAT, never HOW) · gate: REVIEW-GATED · VALIDATION: boundary test
proves belief mechanics/raw streams/calibration state are unreachable from the
published surface (RED drill on an attempted leak); staleness is explicit
(release date carried, no extrapolation); V1-V7.

WO-22 · Consumption design packet for the Owner's NP-S4 ruling · gate:
OWNER-CEREMONY (V9) · a decision packet, not code. Done-when: Owner's ruling
recorded verbatim in the console + board.

──────── V-GATE P5 ────────
Contract v2 live behind its boundary tests · Owner's consumption ruling on
record · "Knowledge+Evidence → runtime" box: TARGET → BUILT (arming still and
forever human, B.6).

════════ PHASE P6 — PATTERN EVOLUTION (FUTURE-GATED, after Gate A only) ════════
WO-23 · Wave-2 machine-proposed registrations design · gate: HARD-LOCKED until
(Architecture Part A row "Pattern Evolution"): NP-S4 gate passed + Gate A +
ECF survival. No Developer self-start under any amendment — the lock is the
Architecture's own. VALIDATION: defined when unlocked, as its own plan.

## Sequencing & parallelism
Blocked-skip (AM-02) + question-pause (AM-03) apply throughout. Live order:
P1 core (WO-03→10→11→14) is the trunk; WO-08/WO-07(A)/WO-13(A) interleave in
any parked moment; P3 opens ONLY at V-GATE P1+P2; P4 only at P3; P5 only at
P4; P6 stays locked. Every accept is batched; every Owner action arrives as a
job file or a single accept line; ceremonies (WO-10, WO-12/16 burn word,
WO-22) are the Owner's judgment moments and are never rushed.

## Change record
v1.0 (2026-08-02): first full-cycle executable plan, per Owner order O-014,
derived strictly from Architecture v1.0 Part A/B and Scientific Model v1.0
(Order of Inquiry, Lifecycle, ECF, Graduation Ladder). Supersedes nothing —
extends the A-013 backlog to the whole objective; DEVELOPMENT_CYCLE.md remains
the ritual law; the board remains the single source of truth.
