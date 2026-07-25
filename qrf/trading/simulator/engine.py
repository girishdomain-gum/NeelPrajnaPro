"""The audited event engine — the battery's judging simulator (ARCH-005 §1).

Where the screener is a telescope (a vectorized grid sweep for a shortlist), this
is the **judge's** simulator: event-driven, bar by bar, applying a named
:class:`CostModel` per trade to compute gross AND net. It is the ``Simulator``
type the battery accepts (``is_audited_simulator = True``); the screener is
rejected by that type (Blueprint §4.7).

HARD RULES (ARCH-005 §1), enforced by construction:

* **No look-ahead.** Every fill is resolved by :mod:`qrf.trading.simulator.fills`,
  which reads only bars up to a trade's own exit. An event decided at ``signal_ts``
  fills at the NEXT bar's open — never the signal bar's close-in-hindsight — and a
  trade whose time-stop exit bar is not yet in the data is not opened. Feeding the
  same data incrementally therefore never changes an already-closed trade
  (property-tested).
* **Gross and net both present.** ``gross_pnl = direction·(exit−entry)·size``;
  the cost model charges the round-trip friction; ``net_pnl = gross − cost``.
* **Distinct type.** The class carries the audited-simulator marker; it exposes
  ``simulate`` (not ``run``), so it can never be confused with the screener.

Determinism: the engine has no RNG — its trades are a pure function of bars,
events, execution and cost model. The ``seed`` (Blueprint §4.7 step 4) is threaded
through and recorded on the trade list as a provenance stamp and the anchor for
the battery's later stochastic steps; SAME INPUTS + SAME SEED → BYTE-IDENTICAL
trades, and the byte image is stable across a process restart (both tested).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import pandas as pd

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.record import canonical_bytes
from qrf.trading.simulator.fills import ExitFill, entry_bar_index, resolve_exit
from qrf.trading.utility.cost_models import CostModel

_REQUIRED_BAR_COLUMNS: tuple[str, ...] = ("ts", "open", "high", "low", "close")


@dataclass(frozen=True)
class ExecutionSpec:
    """The pre-declared execution of a hypothesis (Blueprint §2 hypothesis.execution).

    ``hold_bars`` is the time stop (bars held). ``strength_min`` filters weak
    events. ``stop_offset`` / ``target_offset`` are optional price distances for an
    intrabar stop-loss / take-profit; ``None`` means "no such level". ``size`` is
    the per-trade position size (positive; the traded direction comes from the
    event).
    """

    hold_bars: int
    strength_min: float = 0.0
    stop_offset: float | None = None
    target_offset: float | None = None
    size: float = 1.0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.hold_bars, int)
            or isinstance(self.hold_bars, bool)
            or self.hold_bars < 1
        ):
            raise SchemaViolation(
                f"execution.hold_bars must be an int >= 1, got {self.hold_bars!r}"
            )
        if self.size <= 0:
            raise SchemaViolation(f"execution.size must be > 0, got {self.size!r}")
        for name in ("stop_offset", "target_offset"):
            v = getattr(self, name)
            if v is not None and (not isinstance(v, (int, float)) or v <= 0):
                raise SchemaViolation(
                    f"execution.{name} must be a positive number or None, got {v!r}"
                )

    def as_dict(self) -> dict:
        return {
            "hold_bars": self.hold_bars,
            "strength_min": float(self.strength_min),
            "stop_offset": None if self.stop_offset is None else float(self.stop_offset),
            "target_offset": None if self.target_offset is None else float(self.target_offset),
            "size": float(self.size),
        }


@dataclass(frozen=True)
class Trade:
    """One closed round-trip trade, with gross and net both computed."""

    signal_ts: int      # the event that triggered the entry decision
    entry_ts: int       # ts of the bar the entry filled on (next open)
    exit_ts: int        # ts of the bar the exit filled on
    direction: int      # +1 long / -1 short
    size: float
    entry_price: float
    exit_price: float
    gross_pnl: float
    cost: float
    net_pnl: float
    exit_reason: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Trades:
    """The engine's output — the closed-trade list plus its provenance seed.

    Canonicalizes to bytes via the Blueprint §1.3 serialization, so determinism
    is tested as a byte-image compare, not a loose float compare.
    """

    seed: int
    trades: list[Trade] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.trades)

    def canonical_payload(self) -> dict:
        """A deterministic, JSON-safe image of the trade list (sorted for stability)."""
        rows = sorted(
            (t.as_dict() for t in self.trades),
            key=lambda r: (r["signal_ts"], r["entry_ts"], r["direction"]),
        )
        return {"seed": int(self.seed), "trades": rows}

    def canonical_bytes(self) -> bytes:
        return canonical_bytes(self.canonical_payload())

    def gross_total(self) -> float:
        return float(sum(t.gross_pnl for t in self.trades))

    def net_total(self) -> float:
        return float(sum(t.net_pnl for t in self.trades))


class EventEngine:
    """Audited, event-driven, no-look-ahead simulator (the ``Simulator`` type)."""

    # Marker read by qrf.kernel.battery.simulator.require_audited_simulator.
    is_audited_simulator: bool = True

    def simulate(
        self,
        bars: pd.DataFrame,
        events: pd.DataFrame,
        cost_model: CostModel,
        *,
        seed: int,
        execution: ExecutionSpec,
    ) -> Trades:
        """Simulate ``events`` over ``bars`` under ``execution``, charging ``cost_model``.

        ``bars`` needs columns ``ts, open, high, low, close`` (any ts-sortable
        order; it is sorted here). ``events`` needs ``ts, direction, strength``
        (an EventFrame's pandas view). Returns the closed :class:`Trades`; events
        that cannot open+close within the data (no next bar, or time-stop exit
        beyond the data) are silently skipped — never filled on absent bars.
        """
        if not isinstance(bars, pd.DataFrame):
            raise SchemaViolation(f"bars must be a pandas DataFrame, got {type(bars).__name__}")
        missing = [c for c in _REQUIRED_BAR_COLUMNS if c not in bars.columns]
        if missing:
            raise SchemaViolation(f"bars missing column(s) {missing}")
        for c in ("ts", "direction", "strength"):
            if c not in events.columns:
                raise SchemaViolation(f"events missing column {c!r}")

        b = bars.sort_values("ts").reset_index(drop=True)
        ts_sorted = [int(x) for x in b["ts"].tolist()]
        opens = [float(x) for x in b["open"].tolist()]
        highs = [float(x) for x in b["high"].tolist()]
        lows = [float(x) for x in b["low"].tolist()]

        cost_per_trade = cost_model.cost_for_size(execution.size)

        # Events processed in ascending ts, tie-broken by direction — deterministic.
        ev = events.sort_values(["ts", "direction"], kind="mergesort").reset_index(drop=True)

        trades: list[Trade] = []
        for signal_ts, direction, strength in zip(
            ev["ts"], ev["direction"], ev["strength"], strict=True
        ):
            direction = int(direction)
            if direction == 0:
                continue
            if float(strength) < execution.strength_min:
                continue

            entry_i = entry_bar_index(int(signal_ts), ts_sorted)
            if entry_i is None:
                continue
            entry_price = opens[entry_i]

            fill: ExitFill | None = resolve_exit(
                entry_index=entry_i,
                direction=direction,
                entry_price=entry_price,
                hold_bars=execution.hold_bars,
                opens=opens,
                highs=highs,
                lows=lows,
                stop_offset=execution.stop_offset,
                target_offset=execution.target_offset,
            )
            if fill is None:
                continue

            gross = direction * (fill.exit_price - entry_price) * execution.size
            trades.append(
                Trade(
                    signal_ts=int(signal_ts),
                    entry_ts=ts_sorted[entry_i],
                    exit_ts=ts_sorted[fill.exit_index],
                    direction=direction,
                    size=float(execution.size),
                    entry_price=float(entry_price),
                    exit_price=float(fill.exit_price),
                    gross_pnl=float(gross),
                    cost=float(cost_per_trade),
                    net_pnl=float(gross - cost_per_trade),
                    exit_reason=fill.reason,
                )
            )

        return Trades(seed=int(seed), trades=trades)
