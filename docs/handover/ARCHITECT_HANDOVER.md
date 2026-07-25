# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-5→6 boundary (GO-S5) · Author: architect (fable)
Audience: the NEXT Architect chat session. Read this file first, then the
files it points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite this file at every GO-SN before session end.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF — evidence-first quant
trading research. Team: Owner **Girish** (human, Windows, MINGW64 git
bash, GitHub `girishdomain-gum`, private repo `qrf`; non-native English:
Teaching Standard + PROTOCOL v1.3 Owner-command rule — every command
COMPLETE, BASH-READY (/c/... paths), PLAIN; prefix command blocks with
"paste this in git bash" (GO-S5 retro)). Architect **you** (Filesystem
access F:\ and C:\; write instructions/reviews/ADRs/IVF tools; NEVER
developer code; write on main only between Developer sessions; may READ
the Developer worktree mid-sprint). Developer **Claude Code** (worktrees
under `F:\QRF\.claude\worktrees\<branch>\`; boots via CLAUDE.md rev 3).
Verifier = IVF + Owner. Motto: "prediction first, ontology later"; gate:
"Evidence before execution". Girish's attachments often arrive EMPTY;
screenshots/photos come through. MT5 server = UTC; data folder id
E92643EDFF963E7E489F140FDF338076. Read
docs/reference/EXECUTION_PROCESS_GUIDE.md — the whole method, v1.0.

## 2. Governing documents
Architecture v1.1 (FROZEN; docx placement still pending) ·
Implementation_Blueprint_v1.0.md (§1.3 NORMATIVE; §4.7 battery pipeline;
§4.8 corrections; §7 sprints — S6 next: verdict end-to-end) ·
Verification_Framework_v1.0.md · ADR-001..009 · PROTOCOL.md v1.3 ·
SMC_Concept_Glossary.md (Owner's roadmap, knowability-annotated) ·
AI_PROJECT_STATE.md (generated; never hand-edit).

## 3. Status at this rewrite
- Sprints 1–5 **CLOSED**: GO-S1..GO-S5 in reviews/ (Retrospectives from
  S3 on). S5 was the first zero-first-contact-bug sprint.
- Ledger: **26 records, chain GREEN** (head after ebc9a7e-era commits;
  verify). Latest: T0 GO-S4 note 01KYBX4SWX0DJXSV59526CZHD6.
- Data: xauusd_h1_sample (504, TRAINING; CONTAMINATED for FVG-hold-4
  style hypotheses — engine results observed at HC-S5) · xauusd_h1_full
  (2024: TRAINING 01KYB4SSC96SSS8RA7D1NMTPEX 4157 bars, engine has
  NEVER run on it · **VIRGIN 01KYB4SSD9VVKB577KRGB1W1P0** 1781 bars,
  untouchable) · FVG events (105) · shortlist (500 variants).
- Instruments calibrated 1.0/1.0: seasonality.calendar, classical.rsi,
  smc.fvg, smc.order_block (OB gated for battery use — see §4).
- Battery I foundations DONE: audited engine (no-look-ahead by
  construction, byte-deterministic, pessimistic fills, n_dropped_tail),
  anchored walk-forward + embargo, seeds, selftest tri-state. 655 tests.
- **ARCH-006 (Sprint 6: verdict end-to-end) is WRITTEN and open**,
  including the PRE-REGISTERED first hypothesis H-001 with its
  thresholds declared BEFORE any run. Verify whether the Developer has
  booted (sessions/, refs, worktrees).

## 4. Frozen contracts (do not drift)
canonical_bytes §1.3 · EventFrame §4.3 · DEVQ-005 DOW · OBS-4/OBS-5 ·
DEVQ-006 gap rule + report v2 params · DEVQ-007 __flagged · DEVQ-008
cost-name immutability · DEVQ-009 telescope boundary · DEVQ-010+ADDENDUM
FVG = gap AND displacement candle; **OB break-bar restatement REQUIRED
before any OB hypothesis reaches the battery** · DEVQ-011 embargo
geometry + **BINDING: battery enforces embargo_bars >= max hold_bars+1**
· DEVQ-012 fills: next-open, time stop, pessimistic tie + gap-through
("gaps can only hurt, never help"), n_dropped_tail visible · DEVQ-013
selftest is a wiring gate, never evidence · arrow (8) screener never
judges · window burn = once per (window, lineage) · kernel firewall ·
ADR-009 pictures illustrate, numbers decide.

## 5. Process lessons paid for (NOTES 001–013, GO retros)
Everything is in EXECUTION_PROCESS_GUIDE.md §§4–9; headline reminders:
verify state before asserting (004/010, worktrees) · session logs every
session (011) · bulk parquet rebuilds via --rebuild-bulk, never
hand-copy · seed contract forward-only, the historical amber is ACCEPTED
(013) · **drill your own tools before first real use** (S4; S5 proved
it) · .ex5/.ex4 are ignored build artifacts · HC caption-layout fix
still owed across tools. Tally: **Architect 10, Developer 2.**

## 6. Owner rhythm
Push (`ARCH:`/`OWNER:` prefixes) → boot Developer one-liner → pull
before asking → HC (ADR-009 tools; write his MT5 input file directly at
C:\Users\giris\AppData\Roaming\MetaQuotes\Terminal\E92643...\MQL5\Files\;
create ivf/reports/hc_sN/ BEFORE giving the cp command) → verbatim
phrases → GO-SN + Retrospective → handover rewrite. Pointers, not
content. Two of his commands have landed in chat — gently redirect.

## 7. Immediate next steps (in order)
1. Owner pushes the GO-S5 batch, boots Developer:
   "Boot per CLAUDE.md, execute ARCH-006 completely, starting with T0.
   Session log every session."
2. Architect deliverables for S6 (yours):
   (a) IVF S6 checks — corrections recomputation (Bonferroni vs the
   trial ledger, independent), verdict-record audit (thresholds in the
   verdict match H-001's pre-registration byte-for-byte; burn record
   present and correct; selftest gate ran first), fold-level stats
   recomputation from the engine's trades; Drill S6 — plant a
   threshold-swap (verdict claiming looser thresholds than registered)
   and a double-burn attempt; both must be caught. DRILL FIRST.
   (b) HC caption-layout fix across the three .mq5 tools (one shared
   pattern).
   (c) IVF params-reading (open since GO-S3).
3. Sprint close: REV-S6 → HC (visual: the verdict's fold trades on the
   chart) → Owner Go/No-Go → GO-S6 (+Retrospective) → REWRITE THIS
   FILE → ARCH-007 (Sprint 7: observatory + beliefs, per Blueprint §7).
4. NOTE for the first verdict: H-001's outcome is expected to be FAIL
   or INSUFFICIENT under the deflated threshold — and that is a SUCCESS
   of the machinery. Prepare the Owner: the first verdict proving the
   system can say NO is worth more than a flattering yes.

## 8. How to verify state yourself (before trusting this file)
refs/heads/main vs refs/remotes/origin/main + FETCH_HEAD mtime ·
sessions/ latest log · inbox/OPEN · tail of newest ARCH file ·
journal.jsonl tail (26 at rewrite) · worktrees for mid-sprint truth ·
empty datastore/bulk = rebuild via scripts' --rebuild-bulk. NEVER assert
"not started" from an unverified lens.
