# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-4→5 boundary (GO-S4) · Author: architect (fable)
Audience: the NEXT Architect chat session. Read this file first, then the
files it points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite this file at every GO-SN before session end.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF — evidence-first quant
trading research. Team: Owner **Girish** (human, Windows, MINGW64 git
bash, GitHub `girishdomain-gum`, private repo `qrf`; non-native English:
Teaching Standard + PROTOCOL v1.3 Owner-command rule — every command
COMPLETE, BASH-READY (/c/... paths), PLAIN, no placeholders, no `...`).
Architect **you** (Filesystem access to F:\ and C:\; write
instructions/reviews/ADRs/IVF tools; NEVER developer code; write only on
main between Developer sessions; may READ the Developer worktree
mid-sprint). Developer **Claude Code** (git worktrees under
`F:\QRF\.claude\worktrees\<branch>\`; boots via CLAUDE.md rev 3).
Verifier = IVF + Owner. Motto: "prediction first, ontology later"; gate:
"Evidence before execution". Girish's attachments often arrive EMPTY
(ask for pastes); screenshots/photos come through. MT5 broker server
time = UTC (verified). MT5 data folder id: E92643EDFF963E7E489F140FDF338076.

## 2. Governing documents
Architecture v1.1 (FROZEN; docx placement still pending — remind
gently) · Implementation_Blueprint_v1.0.md (§1.3 canonical_bytes
NORMATIVE; §7 sprints — S5 next: battery I) ·
Verification_Framework_v1.0.md (Go/No-Go = AC+VC+HC+Drill) ·
ADR-001..009 (**009 = visual evidence layer**: pictures illustrate,
numbers decide; screenshots never sole basis of a PASS) · PROTOCOL.md
**v1.3** (READ IN FULL) · docs/reference/SMC_Concept_Glossary.md
(Owner-contributed roadmap with knowability annotations) ·
AI_PROJECT_STATE.md (generated; never hand-edit).

## 3. Status at this rewrite
- Sprints 1–4 **CLOSED**: GO-S1..GO-S4 in reviews/ (each GO from S3 on
  has a standing Retrospective section — Owner's practice).
- Ledger: journal **25 records, chain GREEN** (bbc0096-era; verify
  yourself). Datasets: xauusd_h1_sample (504, TRAINING) ·
  xauusd_h1_full (5938 = 2024: TRAINING 01KYB4SSC96SSS8RA7D1NMTPEX +
  **VIRGIN 01KYB4SSD9VVKB577KRGB1W1P0**, 1781 trailing bars, untouched
  and guard-tested) · xauusd_h1_sample_smc_fvg_events (105) ·
  screener_shortlist (500 variants, 0 admitted — honest small-sample
  result).
- Instruments (all calibrated 1.0/1.0): seasonality.calendar@0.1.0,
  classical.rsi@0.1.0, smc.fvg@0.1.0, smc.order_block@0.1.0.
- Screener: telescope-only (AST-audited), exact trial counting, frozen
  named cost models, seeded (forward-only; one historical seed=null
  amber ACCEPTED per NOTE-013).
- 188 tests, ruff clean (ivf/ excluded), firewall GREEN. inbox/OPEN
  empty. Session logs complete through S4-2.
- **ARCH-005 (Sprint 5: battery I) is WRITTEN and open** — verify
  whether the Developer has booted (sessions/, refs, worktrees).

## 4. Frozen contracts (do not drift)
canonical_bytes §1.3 · EventFrame §4.3 · DEVQ-005 DOW · OBS-4 close
basis · OBS-5 RSI amber band · DEVQ-006 gap rule + ingest_report v2
params · DEVQ-007 __flagged suffix · DEVQ-008 cost-model name
immutability (freeze test) · DEVQ-009 screening metric + telescope
boundary (screener metric is NEVER evidence) · **DEVQ-010+ADDENDUM: FVG
= 3-bar gap AND displacement middle candle; smartmoneyconcepts==0.0.27;
OB knowability restated as break-bar rule REQUIRED before any OB
hypothesis reaches the battery** · arrow (8) screener writes no
verdict/window_burn · kernel firewall · window/burn semantics ·
ADR-009 boundary.

## 5. Process lessons paid for (NOTES 001–013, GO retros)
Writes travel only via commit+push (003) · never assert status from an
unverified lens; Developer lives in worktrees (004/010) · IDs after
fetch, push-per-commit (005) · session logs every session (008/011) ·
HC = captured evidence + human eye (012/ADR-009; the eye caught rev-2's
wrong-year capture) · Owner-command rule always (v1.3) · bulk parquet
never travels via git — every dataset now has --rebuild-bulk; NEVER
hand-copy again · seed contract forward-only (013; the amber is
accepted, do not silence it) · **run your own drills on your own tools
BEFORE first real use** (S4 retro: Architect bugs #8–10 caught by the
drill mechanism). Tally: **Architect 10, Developer 2** — the side that
writes the checks gets checked hardest; that asymmetry is health.

## 6. Owner rhythm
Push after Architect writes (`ARCH:`) → boot Developer one-liner → pull
before asking → HC (visual, ADR-009 tools) + Go/No-Go with verbatim
phrases → GO-SN with Retrospective → handover rewrite. Pointers, not
content. Confirm `(main)`. HC chart tools: sampler → input file in MT5
Files (write it for him directly at
C:\Users\giris\AppData\Roaming\MetaQuotes\Terminal\E92643...\MQL5\Files\)
→ .mq5 from ivf/mt5/ copied to MT5 Scripts by hand → PNGs relayed →
countersign. cp evidence into ivf/reports/hc_sN/ (create dir FIRST).

## 7. Immediate next steps (in order)
1. Owner pushes the GO-S4 batch, boots Developer:
   "Boot per CLAUDE.md, execute ARCH-005 completely, starting with T0.
   Session log every session."
2. Architect deliverables for S5 (yours):
   (a) IVF S5 checks — engine determinism cross-run (same seed, byte
   compare trades), fill-model spot recompute vs cost yaml, walk-forward
   split boundary + embargo independent recomputation, selftest
   tri-state audit (planted edge PASS / noise FAIL / small-n
   INSUFFICIENT re-verified from the records); Drill S5 — plant a
   look-ahead fill (fill at a price not yet knowable) and an embargo
   violation; both must be caught. RUN YOUR OWN DRILL BEFORE THE REAL
   CHECK (S4 lesson, standing).
   (b) HC zone tool rev 2 (caption split — queued nit).
   (c) IVF checks read ingest_report v2 params (still open).
3. Sprint close: REV-S5 → HC → Go/No-Go → GO-S5 (+Retrospective) →
   REWRITE THIS FILE → ARCH-006 (Sprint 6: verdict end-to-end — the
   first real pre-registered hypothesis; OB break-bar restatement gate
   applies if any OB hypothesis is proposed).

## 8. How to verify state yourself (before trusting this file)
refs/heads/main vs refs/remotes/origin/main (pushed?) + FETCH_HEAD
mtime · sessions/ latest log · inbox/OPEN · tail of newest ARCH file ·
journal.jsonl tail (25 records at rewrite; chain by eye) · worktrees for
mid-sprint truth · datastore/bulk emptiness = F-1: use the scripts'
--rebuild-bulk (ingest_xauusd_s3.py for bars, screen_s4.py for
events/shortlist), never re-ingest, never hand-copy.
