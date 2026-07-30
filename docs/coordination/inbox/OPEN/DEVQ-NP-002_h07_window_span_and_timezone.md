# DEVQ-NP-002 · QUESTION (blocks the burn record) · Sprint NP-S1 · 2026-07-30
Author: developer (claude-code)
Refs: Execution Plan v2.0 §0 + §4 precondition (resolve-and-echo the span), §4 DEVQ trigger "window-vs-population disagreement"; Journal J-030 (Owner-typed TRAINING designation); Scientific Model v2.0 §3.2 (Observation Space); `qrf/kernel/protocol/windows.py` (WindowLedger, half-open `[ts_start, ts_end)`, ts = int64 **ns UTC**); `qrf/kernel/instruments/base.py` (EventFrame ts = int64 **ns UTC**).
Tag: specification-silence (window designation scope)

## Context
The Owner's typed designation (J-030) is scope-based: *"The XAUUSD market time covered by the H-07 324-trade export is designated TRAINING."* My blocking first obligation is to resolve the concrete span and echo it for confirmation before registration seals. Two things must be decided for the burn to be recorded correctly; neither is fixed by any ratified document.

## The resolved span (the export = `F:\NeelPrajna\Validation\Stage4\h07_trades.parquet`, 324 rows)
Entry timestamps lie on an exact **M5 grid**; 324 trades, 311 distinct timestamps.

| Basis | First entry | Last entry | Duration |
|---|---|---|---|
| Broker server clock (Vantage EEST, as stored in the file) | 2026-04-21 08:55:00 | 2026-07-10 06:05:00 | 79.9 d |
| **True UTC** (−3 h) | **2026-04-21 05:55:00** | **2026-07-10 03:05:00** | 79.9 d |

Full market-**data** footprint the bespoke detector consumed (`bars_300s`): 2026-04-21 01:00 → 2026-07-10 17:30 stored = **2026-04-20 22:00 → 2026-07-10 14:30 UTC**; the first bar precedes the first trade by only 7 h 55 m (no long lookback pre-roll, because the bespoke M5 stack does not use a 500-H1-bar lookback — see DEVQ-NP-001).

## Question 1 — what does "market time covered" bound?
The Scientific Model v2.0 is **silent** on whether "covered" means the trade-entry span or the full span of market data the detector consumed (grep-confirmed: no burn/lookback/pool vocabulary in that doc; window-state semantics live only in the non-authoritative Reference Handbook + J-030). This is material because it depends on *which detector*:
- For the **actual M5 export**, entry-span and data-span nearly coincide (Apr 21 → Jul 10; difference ~8 h).
- For a **§5-faithful detector** (DEVQ-NP-001 Option A), POOL_FORMED consumes up to **500 H1 bars (~21 days, cap 2000 ≈ 83 days)** *before* the first trade — so the seen-and-burned window would start weeks earlier (~late-March / early-April 2026). Under P8/J-030 ("the data has been seen … burns that market time"), any market time the detector saw is seen, lookback included.
**Ask:** does the TRAINING burn cover (i) the trade-entry span, (ii) the export's consumed-data footprint, or (iii) the maximal consumed window of whichever detector the sprint ends up judging? I recommend (iii) — the honest superset — but this is the Owner's designation to confirm.

## Question 2 — timezone basis for the ledger window
The export stores **broker server time (Vantage EEST = UTC+3 for this window)**; the WindowLedger and EventFrame operate in **int64 nanoseconds UTC**. The two differ by a fixed **3 hours** across the whole span (independently confirmed: gold's daily settlement break sits at 00:00 stored = 17:00 New York; Friday closes at 23:55 stored; the two US-holiday half-days 2026-06-19 and 2026-07-03 truncate at 19:55 stored = 13:00 ET early close; zoneinfo shows no EU/US DST transition inside the window, so +3 is clean throughout). If the window is recorded in the wrong basis, a future "fresh" window designated in UTC could overlap this burned one by 3 hours at each boundary and be silently refused — or a genuinely fresh slice could be wrongly treated as burned.
**Ask:** confirm the window is recorded in **true UTC** (2026-04-21 05:55 → 2026-07-10 03:05 for entries, or the data-footprint bounds if Q1 = ii/iii). I recommend recording in UTC (the ledger's native basis) and noting the broker-EEST source for provenance.

## What I have NOT done
No window designated in the ledger, no registration, no burn. Presenting the resolved span to the Owner for confirmation only, as instructed; the concrete UTC bounds above are the numbers to confirm.

## How this blocks
Blocks the burn/registration record's correctness once DEVQ-NP-001 is resolved and registration is allowed to proceed. Not independently actionable before DEVQ-NP-001, but both answers are needed before anything seals. Silence binds no one.

---
## REPLY · [Owner designation-scope + Architect ledger-basis] · [pending]
Status: OPEN
