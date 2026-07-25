# DEVQ-019 · QUESTION · Sprint 8 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-008 §3 (H-003 h003_dow_monday_drift), A1.5 (splits/embargo, DEVQ-011),
seasonality.calendar detector (emits `seasonality.dow.mon`, direction 0)

## Question
ARCH-008 §3 sets H-003's setup as "enter next-open after the first Monday bar's
signal; hold_bars = declare via DEVQ from the session structure (recommend 22 to
approximate Mon close; embargo >= hold+1 accordingly)." I need to fix (a) the
entry signal source, (b) hold_bars, (c) embargo, (d) the direction.

Session structure of the real xauusd_h1_full: H1 UTC bars, ~23 bars/day (gold
trades Mon 00:00 UTC through the week; the 00:00–01:00 hour is thin/absent on
some days). The `seasonality.calendar@0.1.0` detector emits
`seasonality.dow.mon` at the FIRST UTC bar of each Monday (direction 0,
directionless marker). A UTC Monday holds up to 24 H1 bars.

## Options considered / decisions
(a) Entry signal = `seasonality.dow.mon` marker; the setup lifts it to a LONG
    entry (direction +1) at next-open (parallels how H-001 lifts an FVG event to
    a follow-through trade). "Long-at-open" ⇒ direction +1, fixed.
(b) hold_bars = **22** (ARCH-008's recommendation): from Monday 00:00 UTC, +22 H1
    bars lands ≈ Monday 22:00 UTC, approximating the Monday active-session close
    while staying strictly within the calendar Monday (≤24 bars). "Hold to Monday
    close" is thus a fixed 22-bar time-stop (A1.5 fill: time-stop exit).
(c) embargo_bars = **23** (= hold + 1, DEVQ-011 BINDING minimum). n_folds = 4.
(d) min_n = 40 (≈52 Mondays in 2024 minus fold/tail drops), base_alpha 0.05,
    Bonferroni over the FRESH family xauusd_h1/seasonality.calendar (expected
    N_trials 0/near-0 — the DEVQ-017 zero-deflation boundary in the wild).

Recommendation: hold_bars **22**, embargo **23**, direction **+1 long**, entry at
next-open after `seasonality.dow.mon`. This is what I am registering H-003 with.

## Note
If the Architect wants "Monday close" pinned to a session-close marker rather than
a fixed 22-bar hold, that is a setup_dsl change (and a new hypothesis id, since
the YAML content is the pre-registration seal). Flagging for REV-S8; proceeding on
22/23 so the wave can be judged this session.

---

## REPLY (Architect ruling) · 2026-07-25

**RULING: RATIFIED as registered** — hold_bars 22, embargo_bars 23, direction
+1 long, entry next-open after `seasonality.dow.mon`.

Machine-verified (per GO-S7 ruling hygiene, checked before this reply shipped):
signal on the [00:00,01:00) Monday bar ⇒ entry at the 01:00 open; 22 H1 bars
later exits at the 23:00 open — strictly within calendar Monday. Embargo 23 =
hold+1, exactly the DEVQ-011 binding minimum. All consistent with A1.5.

One caveat RECORDED for any H-003 successor, not relitigated here: on Mondays
where the thin 00:00 bar is ABSENT, a bar-count hold shifts everything one hour
later and the exit can land on the first Tuesday bar. For a calendar-drift
claim this smears the boundary slightly; it does not invalidate the sealed
registration, and the verdict came back INSUFFICIENT (n=28) regardless — any
successor needs more data before it needs a sharper close rule. IF a successor
is ever registered (new id, per the seal), its setup should pin the exit to
"last bar whose open falls on the same UTC Monday" rather than a fixed count.
That is a design note for the future, not an amendment to H-003.

Status: CLOSED (ratified as built; successor design note recorded).
— architect (fable)
