# GO-S3 · Sprint 3 (data plane) Go/No-Go record · 2026-07-25
Decision: **GO** · Owner sign-off, verbatim: **"Signed off — Sprint 3 closed"**
HC sign-off, verbatim: **"HC-S3 PASS"** (REV-S3 addendum)

## Formula (Go/No-Go = AC + VC + HC + Drill, Verification_Framework §8)
- **AC ✔** — ARCH-003 + ARCH-003A completion reports; 133 tests; ruff
  clean; firewall GREEN; gen_state current.
- **VC GREEN** — real dataset: ivf/reports/s3_verify.json (504/504 exact
  rows+prices, OBS-4 on every row). Quarantine path:
  ivf/reports/s3_quarantine_verify.json (9 rows, 3 clean / 6 flagged,
  all six anomaly classes, section B AUDITED).
- **Drill CAUGHT ×2** — ivf/reports/s3_drill.json (clean-partition silent
  repair, victim 1705456800, named) and
  ivf/reports/s3_quarantine_drill.json (both partitions, victims
  1704286800 / 1704297600, named).
- **HC PASS** — 5/5 MATCH captioned MT5 screenshots,
  ivf/reports/hc_s3/HC_S3_*.png (tool rev 4, NOTE-012 / ADR-009
  procedure; Architect countersigned).

## Ledger state at close
Journal: **16 records, chain GREEN**, head content_hash 63d68e00d512…
Key Sprint-3 records:
- Sample: ingest_report 01KYAWHZ77SYPEMPYDY25X8CC1 · manifest
  01KYAWHZ6A9X3YZQ2W0BDRFDS1 · TRAINING window 01KYAWHZ86ZNDGY4NZNCF4XFY0
  (`xauusd_h1_sample`, 504 rows, 0 flags)
- Gapped-feed recalibration 01KYAWJ0REJ7TSM4PRRT18DXD3 (suite .s3, 1.0/1.0)
- Full year (`xauusd_h1_full`, 5938 rows, 0 unexplained flags, report
  schema v2 with params): ingest_report 01KYB4RTD3T7NWMQQW2EV1YFYW ·
  manifest 01KYB4RTBY4Y1ZEJ6SG14SPSAK
- **TRAINING window 01KYB4SSC96SSS8RA7D1NMTPEX**
  [1704160800000000000, 1726128000000000000) — 4157 bars
- **VIRGIN window 01KYB4SSD9VVKB577KRGB1W1P0**
  [1726128000000000000, 1735689600000000001) — 1781 bars, declared by the
  Owner's typed phrase `DECLARE VIRGIN`. Untouchable until spent by the
  battery under a pre-registered hypothesis.

## Contracts ratified this sprint
DEVQ-006 (gap allowance rule; ingest_report v2 params) · DEVQ-007
(`__flagged` reserved suffix + flags column) · ADR-009 (visual evidence
layer) · PROTOCOL v1.2 (worktree reads; handover duty) · v1.3
(Owner-command rule).

---
## Retrospective (standing GO-SN section from S3 on — Owner's proposal)

**What went well.** Both close tools (check + drill) GREEN/CAUGHT on
first run against real data. DEVQs landed exactly in the two areas the
instruction predicted. The process healed itself: the missed S3 session
log (NOTE-011) was followed by logs every session. The Owner's two
proposals became permanent structure: visual evidence (ADR-009, which
caught a real tool bug — rev-2 wrong-period capture — via the Owner's
eye) and the Owner-command rule (PROTOCOL v1.3). Worktree discovery
(NOTE-010) gave mid-sprint visibility and closed the NOTE-008 item.

**What to improve.** (a) Session-log discipline needed one reminder —
watch it at S4 close. (b) Owner-facing commands failed twice (backslash
paths, placeholders) before v1.3 fixed the rule — scripts must comply
too (exercise_quarantine_s3.py queued). (c) .mq5 tools live twice (repo
+ MT5 Scripts) — deployment is manual; acceptable, documented in
ADR-009. (d) Bulk data does not travel via git (F-1) — solved by
--rebuild-bulk. (e) Architect first-contact bug rate stays the top
source (tally now Architect 7, Developer 2) — the drills and the human
eye exist precisely for this; keep both sharp.

**Carried to Sprint 4.** IVF checks read ingest_report v2 `params`
(Architect) · HC screenshot tool rev 5: provenance caption + title
collision (Architect) · exercise script bash-ready commands (Developer,
next touch) · Blueprint editorial queue (Architect): NOTE-001 wording,
DEVQ-005, OBS-4, DEVQ-006 §5(2), DEVQ-007 §4.2.
