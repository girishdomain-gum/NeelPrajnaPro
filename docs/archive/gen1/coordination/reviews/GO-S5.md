# GO-S5 · Sprint 5 (Battery I: engine + splits + selftest) Go/No-Go record · 2026-07-25
Decision: **GO** · Owner sign-off, verbatim: **"Signed off — Sprint 5 closed"**
HC sign-off, verbatim: **"HC-S5 PASS"** (REV-S5 addendum; Experts log 5/5 MATCH)

## Formula (Go/No-Go = AC + VC + HC + Drill)
- **AC ✔** — ARCH-005 complete incl. DEVQ-012 confirmations; 655 tests;
  ruff clean; firewall GREEN; determinism byte-identical twice in one run
  AND across a process restart; hand micro-scenario gross +4.00 / net
  +2.59 to the cent; tri-state correct on all three selftest suites.
- **VC GREEN, first run, zero amber** — check_s5_battery.py rev 1
  (ivf/reports/s5_verify.json): cross-process byte determinism; all
  micro trades equal to an independent re-simulation field-by-field;
  split geometry equal to an independent re-derivation over 6 cases;
  selftest tri-state audited with the planted-edge t recomputed
  independently (agreement 1e-6).
- **Drill CAUGHT ×3** — drill_s5.py rev 1 (ivf/reports/s5_drill.json):
  planted look-ahead fill (signal-bar entry at a better price), planted
  embargo-swallowing train, planted broken determinism — all caught and
  named; clean control NON-RED. Drill-first rule (GO-S4) followed.
- **HC PASS** — ADR-009 generation 3: five REAL engine trades over the
  real FVG events drawn on the MT5 chart; entry AND exit prices verified
  equal to the bars' opens in MT5's OWN series (the no-look-ahead rule,
  independently witnessed). PNGs in ivf/reports/hc_s5/. Notable: the
  weekend-spanning short (row-adjacency convention visible); the sole
  winner exiting at its time stop BEFORE an unknowable crash; 4/5
  sampled trades losing after costs — the honest reminder of why the
  battery exists.

## Ledger state at close
Journal: **26 records, chain GREEN.** S5 appended exactly one record —
T0 GO-S4 note **01KYBX4SWX0DJXSV59526CZHD6** (parent: GO-S3 note). The
engine, splits, seeds, and selftest write no records by design; their
first ledger footprint will be Sprint 6's verdict machinery. VIRGIN
reserve 01KYB4SSD9VVKB577KRGB1W1P0 untouched (guard-tested again).

## Contracts ratified this sprint
DEVQ-011 (contiguous boundary-gap embargo; BINDING S6 rule:
battery must enforce embargo_bars >= max hold_bars + 1) · DEVQ-012
(next-open entry; time stop; pessimistic stop-before-target HOUSE RULE;
pessimistic gap-through both ways — "gaps can only hurt, never help";
n_dropped_tail in the canonical image) · DEVQ-013 (MIN_N=30, α=0.05
one-sided, decisive planted edge; selftest is a wiring gate, never
evidence).

---
## Retrospective (standing GO-SN section)

**What went well.** The first ZERO-first-contact-bug sprint on both
sides of the verification boundary (REV-S5 F-6): DEVQ-before-build,
drill-before-check, and the Owner-command rule all held without a single
correction cycle. The Developer handled a mid-session ruling arrival
with model record-keeping. The HC reached its strongest form yet —
the engine's core promise (never touch a price it couldn't know)
verified visually by an independent lens on real data.

**What to improve.** (a) Two Owner commands landed in chat instead of
the terminal — harmless, but the boot/push blocks could carry a one-line
"paste this in git bash" header every time (adopted, Architect-side).
(b) A compiled .ex5 binary reached the repo before .gitignore caught
up — build artifacts now ignored (*.ex5/*.ex4). (c) Caption-vs-title
collision persists across HC tools — one shared caption-layout fix owed
(rev queue, Architect). Tally unchanged: **Architect 10, Developer 2.**

**Carried to Sprint 6.** Battery must validate embargo_bars >=
max hold_bars + 1 (DEVQ-011) · OB break-bar restatement REQUIRED before
any order-block hypothesis reaches the battery (DEVQ-010) · F-7: flat
per-trade cost is the current model; empirical slippage returns as an
ADR when data exists · HC caption-layout fix · IVF checks read
ingest_report v2 params (still open, Architect).
