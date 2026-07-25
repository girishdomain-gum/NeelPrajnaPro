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
## DEVELOPER ADDENDUM · Owner-commanded refinement · 2026-07-25 (session S5-2)
The Owner directed two refinements to the DEVQ-012 fill rule, now implemented with
tests (still OPEN — this records them for the Architect's ruling, not a self-close):

1. **Pessimistic gap-through, both ways** (fills.py). A level the market GAPS
   THROUGH no longer fills at the untraded level. On the triggering bar the fill is
   the trader-adverse side of {level, bar open}, both exit types, both directions:
   - STOP fills at the WORSE of stop and open (long `min(stop, open)`, short
     `max(stop, open)`) — an adverse gap fills you BEYOND the stop.
   - TARGET is CAPPED at the level — a favorable gap-open past the target is NOT
     credited. Gaps can only ever hurt, never help.
   Tests: long/short stop gap-through → worse open fill; long/short target favorable
   gap → capped at target; non-gapping touch → exact level (unchanged).

2. **n_dropped_tail reporting** (engine.py). Eligible events the data tail cannot
   open+close (no next bar to enter on, or time-stop exit beyond the data) are still
   never filled on absent bars — but they are now COUNTED in `Trades.n_dropped_tail`
   and carried in the canonical image, so the drop is visible, not silent (the same
   no-silent-truncation discipline as the screener's trial_count). Tests: count of
   no-exit + no-entry tail drops; presence in canonical_payload.

Both are additive/realism-improving and do not touch the no-look-ahead guarantee or
the determinism byte-image contract (n_dropped_tail is deterministic; still byte-
identical across a process restart). 655 tests green, ruff clean, firewall GREEN.
If the eventual ruling prefers different semantics (e.g. crediting favorable target
gaps, or a separate no-entry vs no-exit split), both are localized one-place changes.
