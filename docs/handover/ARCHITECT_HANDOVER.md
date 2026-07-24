# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-3→4 boundary (GO-S3) · Author: architect (fable)
Audience: the NEXT Architect chat session. Read this file first, then the
files it points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite this file at every GO-SN before session end.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF (Quantitative Research
Framework) — evidence-first quant trading research. Team: Owner
**Girish** (human, Windows, MINGW64 git bash, GitHub `girishdomain-gum`,
private repo `qrf`; non-native English — Teaching Standard, and
PROTOCOL v1.3 Owner-command rule: commands COMPLETE, BASH-READY, PLAIN,
no placeholders, no `...`). Architect **you** (Filesystem access to
F:\QRF and C:\; write instructions/reviews/ADRs/IVF tools; NEVER
developer code; write only on main between Developer sessions; may READ
the Developer worktree mid-sprint at Owner request). Developer **Claude
Code** (works in `F:\QRF\.claude\worktrees\<branch>\` on `claude/...`
branches; boots via CLAUDE.md rev 3). Verifier = IVF + Owner. Motto:
"prediction first, ontology later"; gate: "Evidence before execution".
Attachments from Girish often arrive EMPTY (ask for pastes); screenshots
and photos come through fine. MT5 broker server time = UTC (verified).

## 2. Governing documents (all on F:\QRF)
- docs/architecture/ v1.1 (FROZEN; docx placement may still be pending).
- docs/implementation/Implementation_Blueprint_v1.0.md — §1.3
  canonical_bytes NORMATIVE; §2 catalog; §4 interfaces; §5 arrows;
  §7 sprints (S4 = screener + costs + SMC); §8 deferred decisions.
- docs/implementation/Verification_Framework_v1.0.md — IND rules,
  tolerance classes, Go/No-Go = AC+VC+HC+Drill.
- docs/adr/ADR-001..009 — **ADR-009 (visual evidence layer)** is new:
  chart-anchored claims get captioned MT5 screenshot evidence; pictures
  illustrate, numbers decide.
- docs/coordination/PROTOCOL.md **v1.3** — READ IN FULL (session logs,
  worktree reads, handover duty, Owner-command rule).
- docs/handover/AI_PROJECT_STATE.md — generated; never hand-edit.

## 3. Status at this rewrite
- Sprints 1–3 **CLOSED**: GO-S1, GO-S2, **GO-S3** (all in
  docs/coordination/reviews/ — GO-S3 contains the full id list and the
  first standing Retrospective section).
- Ledger: journal **16 records, chain GREEN**, head 63d68e00d512….
  Datasets: `xauusd_h1_sample` (504 rows, TRAINING) and
  `xauusd_h1_full` (5938 rows = calendar 2024): **TRAINING window
  01KYB4SSC96SSS8RA7D1NMTPEX** (4157 bars) + **VIRGIN reserve
  01KYB4SSD9VVKB577KRGB1W1P0** (1781 trailing bars, Owner-declared).
  VIRGIN is untouchable: no observatory, no screener, no detector runs;
  only the battery under a pre-registered hypothesis may ever spend it.
- Instruments: seasonality.calendar@0.1.0 (recalibrated, gapped-feed
  suite .s3) and classical.rsi@0.1.0 — both 1.0/1.0.
- 133 tests, ruff clean (ivf/ excluded per NOTE-007), firewall GREEN.
- inbox/OPEN empty. Session logs S3-1 (retroactive), S3-2, S3-3 pushed.
- **ARCH-004 (Sprint 4) is WRITTEN and open** — Developer not yet booted
  at handover-rewrite time (check sessions/ + .git refs yourself).

## 4. Frozen contracts (do not drift)
canonical_bytes §1.3 · EventFrame §4.3 · DEVQ-005 DOW contract ·
OBS-4 (ts = open + timeframe, close basis, timeframe explicit) ·
OBS-5 (RSI amber ±0.5) · DEVQ-006 gap rule + ingest_report v2 `params` ·
DEVQ-007 `__flagged` reserved suffix + `flags` column · kernel firewall ·
window/burn semantics · one-direction rule · arrow (8): the screener
NEVER writes verdict-typed records · ADR-009 boundary: a screenshot can
never be the sole basis of a PASS.

## 5. Process lessons paid for (NOTES 001–012, GO-S3 retro)
003 writes travel only via commit+push · 004 never assert status from an
unverified lens · 005 push-per-commit, IDs after fetch · 007 ruff
excludes ivf/ · 008/010 Developer works in .claude\worktrees\ (read-only
peeks OK; main folder alone is NOT status) · 011 session-log rule was
missed once — check sessions/ at every review · 012 HC = captured
evidence + human eye (the eye caught a real bug). Owner-facing commands:
v1.3 rule, always. Bulk parquet is gitignored — rebuild via
`--rebuild-bulk`, never assume files travel via git. Bug tally:
**Architect 7, Developer 2** — expect your own tools to be wrong first;
that is a finding (NOTE-002 pattern), and the drills exist to prove the
checks.

## 6. Owner rhythm
Push after Architect writes (`ARCH:` prefix) → boot Developer with a
one-liner → pull before asking → HC + Go/No-Go with verbatim phrases →
GO-SN. Pointers, not content. Confirm `(main)` before writing. HC for
chart data: sampler → HC_S3_input.txt file route → IVF_S3_HC_Screenshot
rev 4+ → PNGs to Architect for countersign (ADR-009 / NOTE-012; the .mq5
repo copy is truth, the MT5 Scripts copy is a manual deployment).

## 7. Immediate next steps (in order)
1. Owner pushes the GO-S3 batch, then boots Developer:
   "Boot per CLAUDE.md, execute ARCH-004 completely, starting with T0.
   Session log every session."
2. Architect deliverables during/for S4 (yours):
   (a) IVF S4 checks per ARCH-004's close section — screener
   no-verdict audit, trial_count vs grid-size cross-count, SMC
   planted-case independent recomputation, cost-model spot recompute;
   Drill S4 — plant a screener that writes a verdict-typed record AND a
   trial_count under-count; both must be caught.
   (b) HC screenshot tool rev 5 (provenance caption line:
   dataset/manifest/row/seed/rev + title-collision fix) — extend to SMC
   zone overlays per ADR-009.
   (c) Update check_s3_dataplane-style checks to READ ingest_report v2
   `params` instead of CLI-passed parameters.
   (d) Blueprint editorial amendments queue (GO-S3 retro list).
3. Sprint close: REV-S4 → Owner HC (visual, ADR-009) + Go/No-Go →
   GO-S4 (with Retrospective section — standing practice) → REWRITE
   THIS FILE → ARCH-005 (Sprint 5: battery I, per Blueprint §7).

## 8. How to verify state yourself (before trusting this file)
Compare F:\QRF\.git\refs\heads\main with refs\remotes\origin\main
(pushed?) and FETCH_HEAD mtime (stale?). Read
docs/coordination/sessions/ (latest log), inbox/OPEN, tail of ARCH-004
(completion report?), datastore/journal/journal.jsonl tail (count +
chain by eye; 16 records at rewrite). Mid-sprint status lives in
F:\QRF\.claude\worktrees\<branch>\ — read-only. NEVER assert "not
started" from an unverified lens. If datastore/bulk/ is empty on a
fresh state, that is F-1: run the ingest scripts' --rebuild-bulk, do
not re-ingest.
