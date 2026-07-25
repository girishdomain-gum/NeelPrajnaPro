# DEVQ-012 · QUESTION · Sprint 5 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-005 §1 + DoD ("exact fill rule (next-open vs configurable)"),
Blueprint §2 hypothesis.execution, qrf/trading/simulator/engine.py + fills.py

## Question
ARCH-005 §1 requires "entries fill at the NEXT bar's open (or a documented,
pre-declared fill rule)" and a hand-computable micro-scenario. This records the
exact fill rule I implemented (and the intrabar tie convention), for ratification.

## What I chose (implemented, tested — fills.py, engine.py)
- **Entry:** an event decided at `signal_ts` fills at the OPEN of the first bar
  whose `ts` is strictly greater than `signal_ts` (next-open). Never the signal
  bar's close-in-hindsight. This is FIXED this sprint (not configurable).
- **Exit:** time stop = bar `entry_index + hold_bars`; if that bar is beyond the
  data the trade is NOT opened (cannot close without look-ahead — dropped).
  With no stop/target the exit fills at that bar's OPEN (reason `time_stop`).
- **Optional intrabar stop/target:** if `stop_offset`/`target_offset` are set,
  held bars `entry+1 … entry+hold` are checked against each bar's own high/low;
  the first bar to touch a level closes the trade there.
- **Pessimistic tie (declared):** if one bar's range spans BOTH the stop and the
  target, the STOP is assumed to fill first. A backtest must not resolve ambiguity
  in its own favour.
- Gross = `direction·(exit−entry)·size`; net = gross − cost_model round-trip
  charge (DEVQ-008 named reference). Micro-scenario (3 events) matches to the cent:
  gross +4.00, net +2.59.

No look-ahead is by construction: every fill reads only bars up to the trade's own
exit, so an incremental feed never changes an already-closed trade (property-test).

## Options considered
A) **Fixed next-open entry + time-stop + optional intrabar stop/target, pessimistic
   tie** (as built). Simple, hand-verifiable, matches §1's default.
B) **Configurable entry rule** (next-open | signal-close-with-declared-lag | next-
   VWAP …) selected per hypothesis. More faithful to varied strategies but a larger
   surface and more ways to smuggle in look-ahead.
C) **Optimistic or split-fill intrabar tie** (target first, or 50/50). Flatters
   ambiguous bars — rejected on principle.

Recommendation: **A**. One audited, pessimistic rule is the right foundation for a
judging simulator; configurability (B) can arrive as a declared, per-hypothesis
enum in a later sprint if a real strategy needs it, without changing the no-look-
ahead guarantee. Confirm the pessimistic stop-before-target tie is the house rule.

## How this blocks (or not)
Non-blocking. Engine + fills complete and green under A.

## How to ask
Ratify A (incl. pessimistic tie), or direct me to add the configurable entry enum.

---
## REPLY · architect (fable) · 2026-07-25
Decision: **A RATIFIED**, including the pessimistic stop-before-target
tie as the HOUSE RULE: a judging simulator never resolves ambiguity in
its own favour. Fixed next-open entry is right for the foundation;
configurability returns, if ever, as a declared per-hypothesis enum via
a new DEVQ, and every added rule must carry its own no-look-ahead
property test.

**Two clarifications to confirm (micro-task if either is absent):**
1. **Gap-through fills, pessimistic both ways:** if a bar OPENS beyond
   the stop level, the stop fills at that worse OPEN (not the level);
   if a bar opens beyond the target, the target fills at the LEVEL
   (never the better open). Confirm implemented or add + test.
2. **Dropped tails must be counted:** trades not opened because the
   time-stop bar lies beyond the data are correct to drop, but the
   engine result must REPORT `n_dropped_tail` so a sample is never
   silently trimmed — an edge concentrated at the window's end would
   otherwise vanish without trace. Confirm implemented or add + test.
Status: CLOSED
