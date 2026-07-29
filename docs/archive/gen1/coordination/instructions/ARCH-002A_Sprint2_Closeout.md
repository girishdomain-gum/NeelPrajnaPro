# ARCH-002A · Sprint 2 Close-Out (mechanical VC/drill) · 2026-07-24
Author: architect (fable) · Level: INSTRUCTION · Status: OPEN
Parent: ARCH-002 (delivered, REV-S2 APPROVED; this closes the mechanics)

## Context (read first)
1. `docs/coordination/reviews/REV-S2.md` — your review; note OBS-4
   (close-time ts basis) and OBS-5 (RSI amber band).
2. `ivf/human/checklist_s2.md` — the Owner's checklist; you execute its
   mechanical parts, the Owner keeps the chart HC and sign-off.
3. `ivf/checks/check_s2_detectors.py` (rev 2) and `ivf/checks/drill_s2.py`
   — READ + RUN only, never edit (IND-1).
4. The Owner has placed the MT5 reference export at repo root:
   `IVF_S2_XAUUSD_PERIOD_H1.csv` (validated by the Architect: header
   correct, H1 close=open+3600, starts Jan 2 2024, RSI pre-seeded from
   history — hence the check's --skip-bars 50).

## Tasks
### T1 — qrf-side event export
Produce `s2_events.csv` (header ts,event_type,direction; ts int ns,
CLOSE-time basis) by running both Sprint-2 detectors over the MT5 CSV's
bars (use time_close_sec * 1e9 as ts — REV-S2 OBS-4). Session params for
SeasonalityDetector: copy EXACTLY from its instrument_registered record
in the journal (01KYAKYY1298M1N3JWAA8HBQ5P). The checklist's snippet is
a valid starting point; a small committed script under scripts/ is
fine too (it is qrf-side code, permitted).

### T2 — VC
Run check_s2_detectors.py with --mt5 <csv> --events s2_events.csv
--sessions <exact registered spec, e.g. london=28800-57600>
--skip-bars 50 --report ivf/reports/s2_verify.json.
Expected: GREEN, or AMBER only. For each AMBER, add a one-line
explanation in your completion report (near-threshold RSI cases per
OBS-5 are the anticipated kind). ANY RED: STOP. Do not adjust
thresholds, do not regenerate events, do not touch the check. File a
DEVQ (BLOCKER) quoting the first 5 RED lines — a RED here is a genuine
disagreement between independent implementations and is exactly what
this framework exists to surface. It may be the Architect's check that
is wrong; that is a valid and valuable outcome.

### T3 — Drill S2
Run drill_s2.py (--bar-seconds 3600) to produce a tampered copy, run
the check on it with --report ivf/reports/s2_drill.json.
Expected: RED with timestamp mismatches. If it does NOT go RED: STOP,
DEVQ (BLOCKER) — a missed drill outranks everything.
Delete the tampered file. Re-run T2's exact command afterwards and
confirm the real result is unchanged.

### T4 — Close the books
Append `### CLOSE-OUT (developer)` to ARCH-002's completion report:
T1 event counts per detector, T2 verdict (+ amber explanations),
T3 RED confirmation, report paths. Run gen_state. Commit everything
(including s2_events.csv and both reports; NOT the tampered file),
merge/push per NOTE-005 rule 1.

## Out of scope
Any edit under ivf/**; any detector/kernel change (if the VC exposes a
detector bug, that is a DEVQ first, fix only after Architect decision);
the chart HC (Owner's); Sprint 3 work.

## Definition of Done
T1–T4 done and pushed; expected verdicts observed (GREEN/AMBER-explained,
drill RED, re-run stable); OPEN inbox empty or DEVQs filed.
Remaining after you: Owner chart HC (hand_audit_s2) + Go/No-Go.
