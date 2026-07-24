# DEVQ-006 · QUESTION · Sprint 3 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-003 §Trading plug-in (b), AC "0 unexplained flags"; Blueprint §5
arrow (2); mt5_csv.py `flag_anomalies` / `_gap_excused`

## Question
ARCH-003 flags a `gap` "larger than K×timeframe outside weekends" and names the
weekend/holiday allowance an expected DEVQ area. I implemented a documented,
parameterized rule; this asks the Architect to ratify it (or amend), so the
contract is pinned before Sprint-4 adapters depend on it.

Implemented rule (mt5_csv adapter):
- `hole = (t1 - t0) - timeframe_seconds` for consecutive OPEN times; a bar is
  flagged `gap` iff `hole > gap_k × timeframe` (default `gap_k = 1.0`, i.e. more
  than one missing bar) AND the hole is not weekend/holiday-explained.
- **Weekend allowance** (default on): any expected-missing bar open time in the
  hole whose UTC weekday ∈ {Sat, Sun} excuses the whole hole.
- **Holiday allowance**: any expected-missing open time whose UTC date is in a
  caller-supplied `holidays` set excuses the whole hole.

Observed on the real `xauusd_h1_sample` feed (H1, 504 bars): every day's first
bar opens 01:00 (no 00:00 bar) → a routine 1-missing-bar daily hole (tolerated by
`gap_k=1`); Fri→Mon weekend holes (weekend-excused); one 2024-01-15 mid-week hole
= US market holiday (MLK), passed via `holidays={"2024-01-15"}`. Result: **0
flags**. Without the holiday parameter, exactly that one hole flags — so the rule
is doing real work, not rubber-stamping.

## Options considered
A) **Ratify as-is** (parameterized rule; per-ingest `gap_k`, `weekend_allowance`,
   `holidays`). Simple, no new module; holidays are an explicit per-dataset input.
B) A **trading-calendar module** (`configs/calendars.yaml` or a pandas-market-
   calendars-style dependency) resolving weekends + exchange holidays + session
   hours, so the adapter infers non-trading spans rather than taking a holidays
   set. More faithful; heavier; a new dependency and config surface.
C) Ratify A now, defer B until a feed needs exchange-hour precision (multi-venue
   Sprint 4+), recording B as a deferred decision (Blueprint §8 style).

Recommendation: **C**. A is sufficient and correct for CSV feeds this sprint; the
known simplification (any single weekend/holiday candidate excuses the *entire*
hole, so a genuine multi-day outage that happens to straddle a weekend would be
excused) is acceptable for TRAINING-designated sample data and is cheap to tighten
later under B. Please confirm `gap_k`'s default and whether holidays should be
config-file-driven rather than a call parameter.

## Status
QUESTION — not blocking. The adapter ships with rule A and the real sample
ingests with 0 flags; a later ratification that changes the rule would be a new
ingest (new manifest), never a mutation.
