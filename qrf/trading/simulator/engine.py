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

import math
from dataclasses import asdict, dataclass, field

import pandas as pd

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.record import canonical_bytes
from qrf.trading.simulator.fills import ExitFill, entry_bar_index, resolve_exit
from qrf.trading.utility.cost_models import CostModel

_REQUIRED_BAR_COLUMNS: tuple[str, ...] = ("ts", "open", "high", "low", "close")

# Exit rules (DEVQ-012 scope + ARCH-009 §4 calendar successor):
#   "time_stop"    — held exactly hold_bars bars, then exit at that bar's open.
#   "calendar_day" — held until the OPEN of the LAST bar sharing the entry bar's UTC
#                    calendar day (epoch-day), capped at hold_bars; the DEVQ-019
#                    successor exit for day-of-week claims (H-004). hold_bars stays
#                    the conservative MAX-hold bound, so embargo >= hold_bars + 1
#                    still clears any calendar exit (no boundary leak).
_EXIT_RULES: frozenset[str] = frozenset({"time_stop", "calendar_day"})

# ARCH-NP-004 §4.1: the EventFrame columns (kernel §4.3 spec, qrf/kernel/instruments/
# base.py) that may carry a per-trade stop PRICE (float64, so a level a detector can
# actually fix by signal_ts). Duplicated here rather than imported (the kernel/trading
# boundary already duplicates small closed sets this way, e.g. _EXIT_RULES above and
# in qrf/kernel/records/schemas.py) — trading may import kernel, but this keeps the
# engine's own contract self-contained and independently reimplementable (NP-D-012).
_EVENT_STOP_COLUMNS: frozenset[str] = frozenset({"level", "zone_hi", "zone_lo"})


@dataclass(frozen=True)
class ExecutionSpec:
    """The pre-declared execution of a hypothesis (Blueprint §2 hypothesis.execution).

    ``hold_bars`` is the time stop (bars held). ``strength_min`` filters weak
    events. ``size`` is the per-trade position size (positive; the traded direction
    comes from the event).

    Two independent stop mechanisms — declare AT MOST ONE:

    * ``stop_offset`` (legacy) — one constant price DISTANCE applied to every
      trade in the hypothesis: ``stop_price = entry_price -+ stop_offset``
      (adverse side; sign per direction, see ``fills._stop_price``).
    * ``event_stop_column`` (ARCH-NP-004 §4.1, new) — the name of an EventFrame
      column (must be one of ``level``, ``zone_hi``, ``zone_lo`` — the kernel
      §4.3 float64 columns; any other name means "the EventFrame cannot supply
      it" and is refused at registration) that carries an ABSOLUTE per-trade
      stop PRICE, fixed by data available at or before that event's own
      ``signal_ts`` (e.g. a sweep's penetration extreme). The engine reads this
      column's value for each event row and derives the trade's own risk
      distance as ``R = |entry_price - event_column_value|`` — i.e. the raw
      value is trusted as an already-adverse-side price; a caller that supplies
      a value on the wrong side of entry gets a degenerate (immediately-touched
      or unreachable) stop, which is a data-quality problem for the caller, not
      something the engine second-guesses. A missing/NaN value for a given event
      row degrades to "no stop for that one trade" (silent per-trade, not
      per-hypothesis — the hypothesis-level declaration is still honoured for
      every other row).

    Two independent target mechanisms — declare AT MOST ONE:

    * ``target_offset`` (legacy) — one constant price distance:
      ``target_price = entry_price +- target_offset``.
    * ``target_r_multiple`` (ARCH-NP-004 §4.2, new) — the target expressed as a
      multiple of the trade's own realized risk ``R`` (see above), computed at
      entry: ``target_price = entry_price +- target_r_multiple * R``. REQUIRES a
      stop declared via ``stop_offset`` or ``event_stop_column`` (an R-multiple
      target with no stop is meaningless) — refused at registration otherwise.

    Both stop and target, whichever mechanism supplies them, resolve through the
    SAME geometry as the legacy constant-offset path (``fills.resolve_exit``):
    intrabar, checked in bar order from the bar after entry through the exit bar,
    stop checked before target on any bar spanning both (the pessimistic tie,
    ARCH-NP-004 §4.3), each level filled with pessimistic gap-through. Per-trade
    values are resolved to a per-trade EFFECTIVE ``stop_offset``/``target_offset``
    once, at entry, inside :meth:`EventEngine.simulate`, then handed to the
    unmodified ``fills`` primitives — so when neither new field is set, the
    computed effective values ARE the legacy scalars with no arithmetic applied,
    and every already-sealed verdict reproduces byte-identically (AC-1).

    ``exit_rule`` picks the time-stop variant (``_EXIT_RULES``).
    """

    hold_bars: int
    strength_min: float = 0.0
    stop_offset: float | None = None
    target_offset: float | None = None
    size: float = 1.0
    exit_rule: str = "time_stop"
    event_stop_column: str | None = None
    target_r_multiple: float | None = None

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
            if v is not None and (
                not isinstance(v, (int, float))
                or isinstance(v, bool)
                or not math.isfinite(v)
                or v <= 0
            ):
                raise SchemaViolation(
                    f"execution.{name} must be a positive finite number or None, got {v!r}"
                )
        if self.exit_rule not in _EXIT_RULES:
            raise SchemaViolation(
                f"execution.exit_rule must be one of {sorted(_EXIT_RULES)}, got {self.exit_rule!r}"
            )
        if self.event_stop_column is not None:
            if not isinstance(self.event_stop_column, str) or not self.event_stop_column:
                raise SchemaViolation(
                    "execution.event_stop_column must be a non-empty string or None, "
                    f"got {self.event_stop_column!r}"
                )
            if self.event_stop_column not in _EVENT_STOP_COLUMNS:
                raise SchemaViolation(
                    f"execution.event_stop_column {self.event_stop_column!r} is not an "
                    f"EventFrame column that can carry a stop (must be one of "
                    f"{sorted(_EVENT_STOP_COLUMNS)}) — the EventFrame cannot supply it; "
                    "registration refused"
                )
            if self.stop_offset is not None:
                raise SchemaViolation(
                    "execution.stop_offset and execution.event_stop_column are mutually "
                    "exclusive — declare exactly one stop mechanism; registration refused"
                )
        if self.target_r_multiple is not None:
            if (
                not isinstance(self.target_r_multiple, (int, float))
                or isinstance(self.target_r_multiple, bool)
                or not math.isfinite(self.target_r_multiple)
                or self.target_r_multiple <= 0
            ):
                raise SchemaViolation(
                    "execution.target_r_multiple must be a positive finite number or "
                    f"None, got {self.target_r_multiple!r}"
                )
            if self.stop_offset is None and self.event_stop_column is None:
                raise SchemaViolation(
                    "execution.target_r_multiple requires a stop (execution.stop_offset "
                    "or execution.event_stop_column) — an R-multiple target without a "
                    "stop is meaningless; registration refused"
                )
            if self.target_offset is not None:
                raise SchemaViolation(
                    "execution.target_offset and execution.target_r_multiple are "
                    "mutually exclusive — declare exactly one target mechanism; "
                    "registration refused"
                )

    def as_dict(self) -> dict:
        return {
            "hold_bars": self.hold_bars,
            "strength_min": float(self.strength_min),
            "stop_offset": None if self.stop_offset is None else float(self.stop_offset),
            "target_offset": None if self.target_offset is None else float(self.target_offset),
            "size": float(self.size),
            "exit_rule": self.exit_rule,
            "event_stop_column": self.event_stop_column,
            "target_r_multiple": (
                None if self.target_r_multiple is None else float(self.target_r_multiple)
            ),
        }

    @classmethod
    def from_dict(cls, d: dict) -> ExecutionSpec:
        """Build an ExecutionSpec from a plain mapping (a hypothesis's execution).

        The kernel battery holds a hypothesis's ``execution`` as a domain-blind
        dict; this coerces it into the engine's spec at the trading boundary, so
        the kernel never imports the trading type. ``event_stop_column`` /
        ``target_r_multiple`` default to ``None`` when absent, so a dict recorded
        before ARCH-NP-004 (every hypothesis sealed under ``engine.s5.1``) coerces
        to the exact same spec it always did (AC-1).
        """
        return cls(
            hold_bars=d["hold_bars"],
            strength_min=float(d.get("strength_min", 0.0)),
            stop_offset=(None if d.get("stop_offset") is None else float(d["stop_offset"])),
            target_offset=(None if d.get("target_offset") is None else float(d["target_offset"])),
            size=float(d.get("size", 1.0)),
            exit_rule=str(d.get("exit_rule", "time_stop")),
            event_stop_column=(
                None if d.get("event_stop_column") is None else str(d["event_stop_column"])
            ),
            target_r_multiple=(
                None if d.get("target_r_multiple") is None else float(d["target_r_multiple"])
            ),
        )


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
    n_dropped_tail: int = 0  # eligible events the data tail could not open+close

    def __len__(self) -> int:
        return len(self.trades)

    def canonical_payload(self) -> dict:
        """A deterministic, JSON-safe image of the trade list (sorted for stability).

        ``n_dropped_tail`` is part of the image: the honest count of eligible events
        the engine could not turn into a closed trade because the required bars lie
        beyond the data's end (no next bar to enter on, or no exit bar within the
        window). Reporting it keeps the drop visible rather than silent — the same
        no-silent-truncation discipline the screener's trial_count enforces.
        """
        rows = sorted(
            (t.as_dict() for t in self.trades),
            key=lambda r: (r["signal_ts"], r["entry_ts"], r["direction"]),
        )
        return {"seed": int(self.seed), "n_dropped_tail": int(self.n_dropped_tail), "trades": rows}

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
    # Provenance stamp recorded in every verdict (Blueprint §2 verdict.engine_version).
    # Bumped s5.1 -> s5.2 for ARCH-NP-004 (per-trade stop + R-multiple target, §3):
    # every hypothesis sealed under s5.1 is proven byte-identical under s5.2 when its
    # execution does not use the new fields (AC-1) — the bump marks the capability
    # change for future verdicts, not a behavioural change to past ones.
    engine_version: str = "engine.s5.2"

    def simulate(
        self,
        bars: pd.DataFrame,
        events: pd.DataFrame,
        cost_model: CostModel,
        *,
        seed: int,
        execution: ExecutionSpec | dict,
    ) -> Trades:
        """Simulate ``events`` over ``bars`` under ``execution``, charging ``cost_model``.

        ``bars`` needs columns ``ts, open, high, low, close`` (any ts-sortable
        order; it is sorted here). ``events`` needs ``ts, direction, strength``
        (an EventFrame's pandas view); when ``execution.event_stop_column`` is set
        it additionally needs that column (``level`` / ``zone_hi`` / ``zone_lo``,
        ARCH-NP-004 §4.1 — a per-event absolute stop price). Returns the closed
        :class:`Trades`; events that cannot open+close within the data (no next
        bar, or time-stop exit beyond the data) are never filled on absent bars —
        they are dropped and counted in ``Trades.n_dropped_tail`` (visible, not
        silent).
        """
        if not isinstance(execution, ExecutionSpec):
            execution = ExecutionSpec.from_dict(execution)
        if not isinstance(bars, pd.DataFrame):
            raise SchemaViolation(f"bars must be a pandas DataFrame, got {type(bars).__name__}")
        missing = [c for c in _REQUIRED_BAR_COLUMNS if c not in bars.columns]
        if missing:
            raise SchemaViolation(f"bars missing column(s) {missing}")
        for c in ("ts", "direction", "strength"):
            if c not in events.columns:
                raise SchemaViolation(f"events missing column {c!r}")
        if execution.event_stop_column is not None and execution.event_stop_column not in events.columns:
            raise SchemaViolation(
                f"events missing column {execution.event_stop_column!r} required by "
                "execution.event_stop_column"
            )

        b = bars.sort_values("ts").reset_index(drop=True)
        ts_sorted = [int(x) for x in b["ts"].tolist()]
        opens = [float(x) for x in b["open"].tolist()]
        highs = [float(x) for x in b["high"].tolist()]
        lows = [float(x) for x in b["low"].tolist()]

        cost_per_trade = cost_model.cost_for_size(execution.size)

        # Events processed in ascending ts, tie-broken by direction — deterministic.
        ev = events.sort_values(["ts", "direction"], kind="mergesort").reset_index(drop=True)
        # Per-event absolute stop prices (ARCH-NP-004 §4.1), same order as `ev` —
        # None when the hypothesis does not use a per-trade stop (legacy path).
        event_stops = (
            ev[execution.event_stop_column].tolist()
            if execution.event_stop_column is not None
            else None
        )

        trades: list[Trade] = []
        n_dropped_tail = 0
        for i, (signal_ts, direction, strength) in enumerate(
            zip(ev["ts"], ev["direction"], ev["strength"], strict=True)
        ):
            direction = int(direction)
            if direction == 0:
                continue
            if float(strength) < execution.strength_min:
                continue

            # An eligible event that the data tail cannot open+close is dropped and
            # counted (n_dropped_tail) — never filled on absent bars, never silent.
            entry_i = entry_bar_index(int(signal_ts), ts_sorted)
            if entry_i is None:
                n_dropped_tail += 1  # no next bar to enter on (event past the data)
                continue
            entry_price = opens[entry_i]

            # Effective per-trade stop distance (ARCH-NP-004 §4.1). When
            # event_stops is None this IS execution.stop_offset — no arithmetic,
            # so the legacy path is byte-identical (AC-1). A missing/NaN per-event
            # value degrades to "no stop for this one trade" (see ExecutionSpec
            # docstring); it never raises mid-run.
            if event_stops is not None:
                raw_stop = event_stops[i]
                eff_stop_offset = (
                    None
                    if raw_stop is None or (isinstance(raw_stop, float) and math.isnan(raw_stop))
                    else abs(entry_price - float(raw_stop))
                )
            else:
                eff_stop_offset = execution.stop_offset

            # Effective per-trade target distance: an R-multiple of the stop
            # distance above (ARCH-NP-004 §4.2), or the legacy constant when
            # target_r_multiple is unset — again byte-identical with no arithmetic
            # on the legacy path.
            if execution.target_r_multiple is not None:
                eff_target_offset = (
                    None
                    if eff_stop_offset is None
                    else execution.target_r_multiple * eff_stop_offset
                )
            else:
                eff_target_offset = execution.target_offset

            fill: ExitFill | None = resolve_exit(
                entry_index=entry_i,
                direction=direction,
                entry_price=entry_price,
                hold_bars=execution.hold_bars,
                opens=opens,
                highs=highs,
                lows=lows,
                stop_offset=eff_stop_offset,
                target_offset=eff_target_offset,
                ts_sorted=ts_sorted,
                exit_rule=execution.exit_rule,
            )
            if fill is None:
                n_dropped_tail += 1  # time-stop exit bar lies beyond the data
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

        return Trades(seed=int(seed), trades=trades, n_dropped_tail=n_dropped_tail)
