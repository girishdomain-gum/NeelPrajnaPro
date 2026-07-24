# DEVQ-005 · BLOCKER · Sprint 2 close-out · 2026-07-24
Author: developer (claude-code)
Tag: architecture-conflict
Refs: ARCH-002A T2; REV-S2; check_s2_detectors.py §B; SeasonalityDetector
docstring ("dow at the first bar of each UTC calendar weekday"); IND-1

## What happened
T1 export ran clean (seasonality 67, RSI 17, 84 events, CLOSE-time ts per
OBS-4, registered session spec london=28800-57600, emit_dow=True). T2 VC:

    [IVF s2] bars=454 qrf_events=76 verdict=RED (red=20 amber=0)

**All 20 REDs are day-of-week markers; RSI crossings and session open/close
are GREEN.** First 5 RED lines (verbatim):

    RED B.seas.1704412800000000000.seasonality.dow.fri.extra: unexpected marker
    RED B.seas.1704679200000000000.seasonality.dow.mon.extra: unexpected marker
    RED B.seas.1704758400000000000.seasonality.dow.tue.extra: unexpected marker
    RED B.seas.1704844800000000000.seasonality.dow.wed.extra: unexpected marker
    RED B.seas.1704931200000000000.seasonality.dow.thu.extra: unexpected marker

Per T2 I STOPPED: did not adjust thresholds, regenerate events, or touch the
check. Report at `ivf/reports/s2_verify.json` (committed). This is a genuine
disagreement between two independent implementations — the case the IVF exists
to surface.

## Root cause (read-only analysis of the MT5 CSV)
**This XAUUSD H1 feed has no 00:00-UTC-open bar on any day** — every day's
first bar opens 01:00 UTC (closes 02:00). The two sides define the dow marker
differently:

- **qrf detector** emits `dow.<weekday>` at the *first bar of each UTC calendar
  day* (its documented contract; close-time epoch-day change). Confirmed:
  - Fri 2024-01-05 → marker at 00:00 (bar 23:00→00:00 exists across Thu/Fri).
  - Mon 2024-01-08 → marker at **02:00** (post-weekend: no 23:00→00:00 bar; the
    first Monday bar opens 01:00 / closes 02:00).
- **IVF check §B** expects a dow marker **only if a bar opens exactly at 00:00**
  (`b["open_s"] == day`). Since NO bar opens at 00:00 in this feed, the check
  expects **zero** dow markers → every qrf dow marker is "extra".

The Sprint-2 fixtures were hourly from Monday 00:00, so every day started at
00:00 and the two definitions coincided (calibration passed truth 1.0). Real
broker data (gapped, no midnight bar) is the first place they diverge — exactly
what an independent VC should catch.

## Options considered
A) **The check's dow expectation is too strict for real feeds.** Requiring a
   00:00-open bar makes the dow comparison vacuous on any feed without midnight
   bars (this one expects zero). Align the check to the detector's documented
   contract — "first bar of each UTC calendar day" — so the comparison is
   meaningful. (Requires an IVF edit; Architect-side per IND-1.)
B) **Tighten the detector** to emit dow only at a 00:00-aligned bar. Rejected on
   its face: on this feed it would emit NO dow markers at all, discarding the
   day-of-week signal the detector exists to provide.
C) **Pin a canonical dow-marker contract** in the Blueprint (which bar
   represents a UTC day when midnight is absent — first-available-bar vs
   midnight-aligned), then whichever side violates it changes. This is the
   durable fix; A/B are the two candidate contracts.

Recommendation: **C, resolving to A's semantics** — the detector's
"first bar of each UTC day" is the robust, feed-agnostic definition; the check's
midnight-alignment assumption is the artifact of midnight-aligned fixtures. But
the contract is the Architect's to set, and the fix (check or detector) follows
from that. RSI + session markers already agree, so the detectors are otherwise
validated against MT5.

## Status
BLOCKER — Sprint-2 close-out (T3 drill, T4 close) is halted pending this
decision. Branch pushed so this thread + the RED report are visible (NOTE-005).
Not merged to main (close-out incomplete).

---
## REPLY · architect (…) · <date>
Decision: …
Status: OPEN
