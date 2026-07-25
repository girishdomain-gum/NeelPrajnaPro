# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-6→7 boundary (GO-S6) · Author: architect (fable)
Audience: the NEXT Architect chat session. Read this file first, then the
files it points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite this file at every GO-SN before session end.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF — evidence-first quant
trading research. Team: Owner **Girish** (human, Windows, MINGW64 git
bash, GitHub `girishdomain-gum`, private repo `qrf`; non-native English:
Teaching Standard + PROTOCOL v1.3 Owner-command rule — commands
COMPLETE, BASH-READY, PLAIN, prefixed "paste this in git bash").
Architect **you** (Filesystem access F:\ and C:\; instructions/reviews/
ADRs/IVF tools; NEVER developer code; write on main between Developer
sessions; may READ worktrees mid-sprint). Developer **Claude Code**
(worktrees under `.claude\worktrees\`; boots via CLAUDE.md rev 3).
Verifier = IVF + Owner. Motto: "prediction first, ontology later";
gate: "Evidence before execution". Girish's attachments often EMPTY;
screenshots come through. MT5 server = UTC; data folder id
E92643EDFF963E7E489F140FDF338076. READ
docs/reference/EXECUTION_PROCESS_GUIDE.md — the method, v1.0.

## 2. Governing documents
Architecture v1.1 (FROZEN; docx placement pending) · Blueprint v1.0
(§7 sprints — S7 next: observatory + beliefs; EDITORIAL QUEUE IS LONG,
consolidation pass due at S7 close) · Verification_Framework v1.0 ·
ADR-001..009 · PROTOCOL v1.3 · SMC_Concept_Glossary.md ·
EXECUTION_PROCESS_GUIDE.md · AI_PROJECT_STATE.md (generated).

## 3. Status at this rewrite — THE FIRST VERDICT EXISTS
- Sprints 1–6 **CLOSED** (GO-S1..S6, retrospectives from S3 on).
- **H-001 judged: FAIL** — hypothesis 01KYC7Y1S2534DVYHWHNCZGTGZ,
  verdict 01KYC7Y2KWYGXH73V1R9P57MYA (n=654, 4/4 folds negative, net
  −363.58, p=0.94), burn 01KYC7Y2PQ4KN58AVGAYBJ2P2A on the TRAINING
  window × lineage. Naive FVG follow-through is a verified loser after
  costs. The verdict survived hostile IVF audit (thresholds byte-equal,
  stats recomputed from raw trades, planted frauds caught).
- **Corrections BITE now** (DEVQ-015 ruling): multiplicity follows
  claims — (market, instrument-family), prefix-matched. Verified on the
  real ledger: family xauusd_h1/smc.fvg = 500 trials → alpha 1e-4 for
  any future FVG hypothesis on this market. H-001's honest family_m=0
  record stands; the tightening is dated.
- Hypothesis schema v2: thesis + outcome_interpretations (pre-committed
  interpretation, REQUIRED) + family. v1 (H-001) still validates.
- Ledger: **31 records, chain GREEN.** VIRGIN
  01KYB4SSD9VVKB577KRGB1W1P0 (1781 bars) untouched. 700 tests.
- **ARCH-007 (Sprint 7: observatory + beliefs) is WRITTEN and open** —
  verify whether the Developer has booted (sessions/, refs, worktrees).

## 4. Frozen contracts (do not drift)
Everything in GO-S6 §Contracts plus the standing set: canonical_bytes ·
EventFrame §4.3 · OBS-4/5 · DEVQ-005/6/7/8/9 · DEVQ-010+ADDENDUM (FVG =
gap AND displacement; OB break-bar gate STILL UNPAID — registry refuses
OB hypotheses) · DEVQ-011 (+battery embargo>=hold+1) · DEVQ-012 fills
("gaps can only hurt") · DEVQ-013 · DEVQ-014 (content_hash seal; v2
interpretation fields required) · DEVQ-015 (family multiplicity) ·
verdict+burn one code path; burn = once per (window, lineage) · arrow 8
· kernel firewall · ADR-009.

## 5. Process lessons paid for
All in EXECUTION_PROCESS_GUIDE.md; headlines: verify before asserting
(worktrees are the mid-sprint truth) · session logs every session ·
--rebuild-bulk, never hand-copy (F-1 recurred for verdict trades —
extension CARRIED) · drill your own tools BEFORE first real use (three
consecutive clean verification cycles since) · .ex5 ignored · seed
amber ACCEPTED (013) · sampled winners are anecdotes, the mean is the
truth (HC-S6 lesson, on file with pictures). Tally: **Architect 10,
Developer 2.**

## 6. Owner rhythm
Unchanged (GUIDE §5). HC pattern: sampler → I write his MT5 input file
directly → reuse/compile .mq5 from ivf/mt5/ → PNGs relayed →
countersign → verbatim phrase. Create ivf/reports/hc_sN/ BEFORE the cp
command. His commands sometimes land in chat — redirect gently.

## 7. Immediate next steps (in order)
1. Owner pushes the GO-S6 batch, boots Developer:
   "Boot per CLAUDE.md, execute ARCH-007 completely, starting with T0.
   Session log every session."
2. Architect deliverables for S7 (yours):
   (a) IVF S7 checks — observatory discipline (questions reference
   EXPLORATION/TRAINING scans only; no VIRGIN read anywhere in scan
   paths — audit imports/calls; question records well-formed and
   parented to their scan evidence), beliefs recomputation (belief
   state re-derived from the verdict set independently), ancestry audit
   (a hypothesis claiming observatory ancestry must trace to real
   question records); Drill S7 — plant a question referencing VIRGIN
   data and a belief that ignores a FAIL verdict; both must be caught.
   DRILL FIRST.
   (b) HC caption-layout fix across the three .mq5 tools.
   (c) IVF params-reading (open since GO-S3) — fold into the S7 check.
3. Sprint close: REV-S7 → HC → Go/No-Go → GO-S7 (+Retrospective) →
   Blueprint CONSOLIDATION amendment pass (the queue: NOTE-001,
   DEVQ-005/6/7, OBS-4, DEVQ-010, DEVQ-014 items) → REWRITE THIS FILE →
   ARCH-008 (Sprint 8: family waves / graduation, per Blueprint §7 and
   the Owner's glossary roadmap).

## 8. How to verify state yourself (before trusting this file)
refs/heads/main vs refs/remotes/origin/main + FETCH_HEAD mtime ·
sessions/ latest · inbox/OPEN · tail of newest ARCH file ·
journal.jsonl tail (31 at rewrite; the last three records should be
hypothesis → verdict → window_burn for H-001) · worktrees for
mid-sprint truth · empty bulk = --rebuild-bulk (verdict trades still
needs the hand-copy until the carried extension lands). NEVER assert
"not started" from an unverified lens.
