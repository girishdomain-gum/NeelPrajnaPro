"""Fill primitives for the audited engine — no look-ahead by construction (ARCH-005 §1).

Where the engine (``engine.py``) walks events bar by bar, this module answers the
two pure geometric questions a fill poses, using ONLY bars that have already
printed relative to the decision:

* **Entry** — an event decided at ``signal_ts`` fills at the OPEN of the *next*
  bar (the first bar whose ``ts`` is strictly greater than ``signal_ts``). Never
  the signal bar's own close: that price is only known in hindsight at decision
  time. :func:`entry_bar_index`.

* **Exit** — from the entry bar, the position is held up to ``hold_bars`` bars (the
  time stop). If a stop-loss / take-profit level is declared, each held bar is
  checked *intrabar* against that bar's own high/low; the first bar to touch a
  level closes the trade there. Nothing later than the exit bar is ever read.
  :func:`resolve_exit`.

Intrabar tie convention (declared, pessimistic — DEVQ-012): if a single bar's
range spans BOTH the stop and the target, the **stop** is assumed to fill first.
A backtest that resolves ambiguous bars against itself cannot flatter a strategy.

Pessimistic gap-through, both ways (Owner refinement to DEVQ-012): a level that the
market GAPS THROUGH does not fill at the untraded level. On the triggering bar the
fill is the trader-adverse side of {level, bar open}, applied to BOTH exit types
and BOTH directions — so a gap can only ever hurt, never help:
  * STOP   — fills at the WORSE of the stop and the open (long: ``min(stop, open)``,
             short: ``max(stop, open)``); an adverse gap fills you beyond the stop.
  * TARGET — is CAPPED at the level: a favorable gap-open beyond the target is not
             credited (you never book more than the target).

Fill-rule scope this sprint (DEVQ-012): entries are next-open, fixed (not
configurable); exits are time-stop-at-next-open plus optional intrabar
stop/target. Alternative fill rules (signal-close with a declared lag, VWAP, …)
are out of scope and would be a new, declared rule.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass


@dataclass(frozen=True)
class ExitFill:
    """The resolved exit of one trade."""

    exit_index: int
    exit_price: float
    reason: str  # "time_stop" | "stop" | "target"


def entry_bar_index(signal_ts: int, ts_sorted: list[int]) -> int | None:
    """Index of the entry bar: the first bar with ``ts`` strictly greater than ``signal_ts``.

    ``ts_sorted`` is the ascending list of bar timestamps. Returns ``None`` if no
    such bar exists (the signal is at or after the last bar — nothing to fill on
    without look-ahead).
    """
    idx = bisect.bisect_right(ts_sorted, int(signal_ts))
    return idx if idx < len(ts_sorted) else None


def resolve_exit(
    *,
    entry_index: int,
    direction: int,
    entry_price: float,
    hold_bars: int,
    opens: list[float],
    highs: list[float],
    lows: list[float],
    stop_offset: float | None,
    target_offset: float | None,
) -> ExitFill | None:
    """Resolve the exit for a trade opened at ``entry_index`` in ``direction`` (+1/-1).

    The time stop is bar ``entry_index + hold_bars``; if that bar is beyond the
    data the trade cannot be closed without look-ahead and ``None`` is returned
    (the engine drops it). When ``stop_offset`` / ``target_offset`` are given,
    bars ``entry_index+1 … entry_index+hold_bars`` are checked intrabar in order;
    the first to touch a level closes the trade there — the stop before the target
    on a bar that spans both, and each level filled with pessimistic gap-through
    (see module docstring). If no level is touched, the trade closes at the OPEN of
    the time-stop bar.
    """
    n = len(opens)
    exit_index = entry_index + hold_bars
    if exit_index >= n:
        return None  # cannot close within the data — no look-ahead permitted

    stop_price = _stop_price(direction, entry_price, stop_offset)
    target_price = _target_price(direction, entry_price, target_offset)

    if stop_price is not None or target_price is not None:
        for j in range(entry_index + 1, exit_index + 1):
            hi, lo, op = highs[j], lows[j], opens[j]
            # Pessimistic: test the stop before the target within one bar.
            if stop_price is not None and _touched_stop(direction, hi, lo, stop_price):
                return ExitFill(j, _stop_fill(direction, stop_price, op), "stop")
            if target_price is not None and _touched_target(direction, hi, lo, target_price):
                # Cap at the target: a favorable gap-open is never credited.
                return ExitFill(j, float(target_price), "target")

    return ExitFill(exit_index=exit_index, exit_price=float(opens[exit_index]), reason="time_stop")


def _stop_fill(direction: int, stop_price: float, open_j: float) -> float:
    """Pessimistic gap-through: fill a stop at the WORSE of the stop level and the open.

    If the bar gaps open beyond the stop, the realistic fill is the gapped-open (a
    price that actually traded), not the stop level (which never did): a long fills
    at ``min(stop, open)``, a short at ``max(stop, open)``. A non-gapping touch
    (the bar opens on the safe side and only reaches the stop intrabar) fills at the
    stop exactly.
    """
    return float(min(stop_price, open_j) if direction > 0 else max(stop_price, open_j))


def _stop_price(direction: int, entry_price: float, stop_offset: float | None) -> float | None:
    if stop_offset is None:
        return None
    # A stop is adverse: below entry for a long, above entry for a short.
    return entry_price - stop_offset if direction > 0 else entry_price + stop_offset


def _target_price(direction: int, entry_price: float, target_offset: float | None) -> float | None:
    if target_offset is None:
        return None
    # A target is favorable: above entry for a long, below entry for a short.
    return entry_price + target_offset if direction > 0 else entry_price - target_offset


def _touched_stop(direction: int, high: float, low: float, stop_price: float) -> bool:
    return low <= stop_price if direction > 0 else high >= stop_price


def _touched_target(direction: int, high: float, low: float, target_price: float) -> bool:
    return high >= target_price if direction > 0 else low <= target_price
