# GO-S4 · Sprint 4 (screener + costs + SMC) Go/No-Go record · 2026-07-25
Decision: **GO** · Owner sign-off, verbatim: **"Signed off — Sprint 4 closed"**
HC sign-off, verbatim: **"HC-S4 PASS"** (REV-S4 addendum)

## Formula (Go/No-Go = AC + VC + HC + Drill)
- **AC ✔** — ARCH-004 + micro-tasks complete; 188 tests; ruff clean;
  firewall GREEN; 500-variant grid in ~12s with shortlist + exact
  trial_count in one run; random no-edge grid → empty shortlist; SMC
  planted cases 1.0/1.0; costs hand-computed to the cent.
- **VC** — check_s4_screener.py rev 3: **red=[]**, FVG independent
  recomputation **105/105 exact** on real data; screener no-verdict AST
  audit, trial-count cross-count (500==500), declarations complete.
  One AMBER: historical shortlist seed=null — **ACCEPTED** per NOTE-013
  ruling (true of the ledger, stays visible, reason on file).
  Report: ivf/reports/s4_verify.json.
- **Drill CAUGHT** — drill_s4.py rev 3: planted verdict-writing screener
  and 180-of-500 trial under-count both caught, correct control pair
  unflagged, scratch FVG recomputation clean.
  Report: ivf/reports/s4_drill.json.
- **HC PASS** — ADR-009 zone overlays: 5/5 FVG MATCH (chart-side
  recomputation from MT5's own bars), Architect-countersigned PNGs in
  ivf/reports/hc_s4/, provenance captions embedded.

## Ledger state at close
Journal: **25 records, chain GREEN.** Key Sprint-4 records:
T0 GO-S3 note 01KYB5ARJPK3YK0AKCE9FP7DAH · smc.fvg registered
01KYB7QQ7Y38PP5MKHEQ3X2G5Z / calibrated 01KYB7QQA5W466QRPWCBC76K5S ·
smc.order_block registered 01KYB7QQASN2429EKEQN0DKPT9 / calibrated
01KYB7QQDQFCAQVV0BMPHDMK9R · FVG events manifest
01KYB7WQFND907DMH550GPKMW0 (105 events) · shortlist manifest
01KYB7X2YNXZKXR4E97HMQ1PFC (500 variants, 0 admitted on the small
sample — honest) · trial_count 01KYB7X308YS3KMV8C95MZ028E (n=500).
VIRGIN reserve 01KYB4SSD9VVKB577KRGB1W1P0 untouched by every S4 code
path (guard-tested).

## Contracts ratified this sprint
DEVQ-008 (cost models = frozen named config; name immutability + freeze
test) · DEVQ-009 (net-Sharpe screening metric + thresholds; telescope
boundary) · DEVQ-010 + ADDENDUM (smartmoneyconcepts==0.0.27 pin;
knowability wrapper; **completed FVG definition: 3-bar gap AND
displacement middle candle**) · NOTE-013 (seed forward-only; amber
accepted) · SMC_Concept_Glossary.md (Owner-contributed roadmap
reference with knowability annotations).

---
## Retrospective (standing GO-SN section)

**What went well.** The sprint's crown: the Developer independently
discovered the SMC library's non-causality and the IVF independently
caught the underspecified FVG definition (2/107 delta on first real
contact) — two different truth mechanisms, both firing, both resolved
with evidence (the Owner's own bar inspection ruled it). ADR-009's
first zone HC worked end-to-end with chart-side recomputation. All
three predicted DEVQ areas materialized. Session logs every session.
The Owner-command rule (v1.3) held all sprint.

**What to improve.** (a) Architect first-contact bugs #8–10 (soft-pass
check, drill format lag, impure scratch data, zone-caption truncation)
— all caught pre-reliance by the drill mechanism, but the rate says:
Architect tools need their own drills run BEFORE first real use, now
standing practice. (b) F-1 recurred for detector/screener datasets
before MT3 closed it — rebuild-bulk is now the norm; hand-copies end
here. (c) Zone HC tool rev 2 owed (caption split). Tally: **Architect
10, Developer 2.**

**Carried to Sprint 5+.** OB knowability restated as explicit break-bar
rule BEFORE any OB hypothesis reaches the battery (S6 gate; DEVQ-010) ·
weekend-spanning FVG research question (S7 observatory) · cost-model
calibration ADR if empirical slippage arrives (Gen-2 horizon) ·
IVF checks read ingest_report v2 params (Architect, still open from
GO-S3) · HC zone tool rev 2 caption fix (Architect).
