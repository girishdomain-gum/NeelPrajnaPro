# REV-S3 · Architect review · Sprint 3 (data plane) · 2026-07-25
Author: architect (fable)
Refs: ARCH-003 (+completion report), DEVQ-006/007 (CLOSED), NOTE-009/010/011,
S3-1 (RETROACTIVE) + S3-2 session logs, ivf/reports/s3_verify.json,
ivf/reports/s3_drill.json

## Code review (read-only, main @ f68fe17)
- `qrf/kernel/records/bulk.py`, `window` machinery, data-plane schemas
  (4, incl. window_burn per NOTE-009): consistent with Blueprint §4.2/§4.6;
  manifests + hash-verified read; burn test-only. PASS.
- `qrf/trading/adapters/mt5_csv.py` + `schemas.py`: OBS-4 normalization is
  load-bearing and explicit (`timeframe_seconds` required, never inferred);
  flag-never-repair honored end-to-end; gap rule matches the DEVQ-006
  ratified text; quarantine matches DEVQ-007 (reserved suffix now rejected
  at the door; `QUARANTINE_SUFFIX` single-sourced). ingest_report schema v2
  adds the required `params` object additively — v1 untouched, existing
  records stand. PASS.
- Carried items: gapped-feed calibration (01KYAWJ0REJ7TSM4PRRT18DXD3,
  4-case suite, 1.0/1.0) parented to the S2 registration — correct: same
  instrument, no registration re-mint. Rename to calibration_audit_s2.py
  with honest docstring. PASS.
- Tests 127, ruff clean, firewall GREEN, journal 12 records chain GREEN.

## Verification (VC)
- `check_s3_dataplane.py` rev 1 — **GREEN, first run.** source=504,
  clean=504, flagged=0; exact row accounting; numeric price equality on
  every row vs a FRESH MT5 export; OBS-4 property held for all 504 rows.
  Section B **VACUOUS** (0 flagged rows) — reported visibly, not passed
  silently; flagged-path behavior is covered by adapter planted-anomaly
  tests and will be exercised end-to-end in ARCH-003A (scratch datastore),
  so vacuity does not carry into GO-S3 unexamined.
- `drill_s3.py` rev 1 — **CAUGHT.** One-pip silent repair planted at
  time=1705456800; check exited RED and named the victim. Drill 2 SKIPPED
  (no quarantine dataset) — to be exercised in ARCH-003A.

## Findings
- F-1 (process, minor): gitignored bulk data does not travel via git and
  the ingest script's journal-based idempotency makes "rebuild" a no-op on
  a fresh checkout — dataset restored by manual copy from the Developer
  worktree this time (byte-deterministic write, manifest-covered).
  Remedy: `--rebuild-bulk` in ARCH-003A.
- No substance findings. First-contact bug tally unchanged
  (Architect 4, Developer 2).

## Remaining for GO-S3 (in order)
1. HC: Owner samples bars via `ivf/human/sample_s3_bars.py` vs the MT5
   chart (instructions in the script).
2. ARCH-003A execution (rebuild-bulk; quarantine exercise closing the
   drill-2 SKIP; VIRGIN declaration script).
3. Owner runs the VIRGIN declaration over the bigger export — Owner's
   act, verbatim sign-off recorded.
4. Owner Go/No-Go → GO-S3.md → Architect rewrites
   docs/handover/ARCHITECT_HANDOVER.md (PROTOCOL v1.2 duty) → ARCH-004.

Architect verdict on the development scope: **PASS — recommend GO** once
HC + VIRGIN + sign-off complete.

---
## ADDENDUM · HC-S3 result · 2026-07-25
Owner sign-off, verbatim: **"HC-S3 PASS"**

Evidence (NOTE-012 procedure, tool IVF_S3_HC_Screenshot.mq5 rev 4,
server offset 0 = broker on UTC): 5/5 MATCH — ivf/reports/hc_s3/
HC_S3_1704402000.png, HC_S3_1704783600.png, HC_S3_1705039200.png,
HC_S3_1705554000.png, HC_S3_1705647600.png. Sampler seed=3 over
xauusd_h1_sample (manifest 01KYAWHZ6A9X3YZQ2W0BDRFDS1). Architect
countersigned the PNGs (axis dates, marker placement, candle-vs-caption
agreement) before the Owner's verdict.

Tool first-contact bugs, all caught by process before any wrong evidence
entered the record: rev1 input-dialog truncation (0/0), rev2 unverified
navigation (PNG showed chart end — caught by the OWNER's eye), rev3
ALIGN_RIGHT capture anchor. Bug tally now: **Architect 7, Developer 2.**
Standing improvement queued for S4 (NOTE-012): provenance caption line
(dataset/manifest/row/seed/rev) + title-collision fix.
