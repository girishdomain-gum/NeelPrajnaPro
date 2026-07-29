# GO-S2 · Sprint 2 Go/No-Go Record · 2026-07-24
Decider: Owner (Girish) · Recorded by: architect (fable)
Decision: **GO — Sprint 2 CLOSED**

## The four conditions (IVF §8)
1. AC met — ARCH-002 + ARCH-002A completion reports; REV-S2 APPROVED;
   87 tests green; firewall GREEN; journal 7 records chain GREEN. ✔
2. VC GREEN — `ivf/reports/s2_verify.json` (check rev 3): red=0 amber=0
   over 404 compared bars of REAL XAUUSD H1; RSI crossings, session
   markers and DOW markers all agree between qrf detectors and the
   MT5-derived independent reference. ✔
3. HC signed — Owner chart-verified real sampled events on MT5,
   including the DEVQ-005 case live (post-weekend `dow.mon` at the
   day's first bar), an oversold cross at its exact bar, session
   boundaries, and a near-miss RSI peak whose silence both
   implementations independently confirmed. Sign-off verbatim:
   "S2 VC GREEN, drill RED caught, HC done — sign off Sprint 2". ✔
4. Drill caught — `ivf/reports/s2_drill.json`: planted one-bar
   hindsight shift → RED (144 findings); real result re-ran unchanged. ✔

## Findings register for this sprint (all closed)
- DEVQ-005 (BLOCKER, architecture-conflict) → detector's DOW contract
  RATIFIED ("first bar of each UTC epoch-day"); check was the artifact
  (midnight-bar assumption), fixed rev 3. The deepest lesson to date:
  the check AND the calibration fixtures shared the same hidden
  assumption, so they agreed with each other and only independent real
  data could expose it.
- HC-sampler finding (caught by Owner+Architect at HC): the Sprint-2
  hand_audit script sampled synthetic calibration fixtures, not real
  events — an Architect spec gap (data source unpinned in ARCH-002).
  Fixed with `ivf/human/sample_s2_events.py` (real evidence,
  deterministic seed); HC redone against real data before sign-off.
- NOTE-007 (Developer): ivf/ excluded from qrf's ruff — RATIFIED here;
  IND-1 expressed in tooling. No further thread needed.
- MQL5 compile fix (TimeDayOfWeek → TimeToStruct), export rev 2;
  check rev 2 (--skip-bars for MT5's history-seeded RSI).

## First-contact bug tally (all caught pre-verdict)
Architect 4 (verifier crash, MQL4-ism, midnight assumption, HC data
source) · Developer 1 (gen_state -qq). Every one surfaced at first
contact with reality; none reached a verdict. The verification layer
is where the misses cluster — which is why the Verifier role includes
the Owner's eyes, not only the Architect's tools.

## Carried into Sprint 3 (in ARCH-003)
Gapped-feed seasonality calibration case (fixtures must never
re-encode midnight alignment) · rename hand_audit_s2 →
calibration-suite inspector · Blueprint editorial amendments queued
(NOTE-001 "leaf" wording; the ratified DOW contract; OBS-4 close-time
adapter duty).
