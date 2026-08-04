"""LS-01-R001's statistic (docs/measurements/LS-01-R001_filtered_sweep.md
§2-§4). S08 Phase 1 (A-032 §2.3): "the one genuinely new module in S08,
and it is pure: (ObservationSets + bars) -> a number."

DUCK-TYPED ON PURPOSE, NOT IMPORTED FROM qrf.trading: this module reads
`.kind`, `.sweep_bar`, `.direction`, `.shift_bar` off whatever
Observation instances it is given, rather than importing
`SweepObservation`/`StructureShiftObservation` from
qrf.trading.concepts.*.detector. That keeps it on the qrf/kernel/ side of
AM-02.3's inner wall (qrf/kernel/ must never import qrf.trading) while
still consuming detector output -- the same relationship the Battery
already has to an ObservationSet's *shape*, never its *source module*.

CAUSALITY, BY CONSTRUCTION (§2's "the context must be strictly BEFORE the
sweep bar", A-032 X5): `qualifying_events()` decides membership using
ONLY integer bar indices (`sweep.sweep_bar`, `shift.shift_bar`) -- it
never touches `bars` at all, so nothing about price action, let alone a
FUTURE close, can influence whether an event qualifies. Only
`signed_forward_return()`, called strictly AFTER qualification is
decided, ever reads `bars`, and it reads exactly two bars: the sweep bar
and the bar `horizon` bars later. There is no code path in this module
where a bar beyond `sweep_bar + horizon` is read for any event.

DESIGN DECISION -- THE EMPTY-POPULATION CASE (stated because A-032 asked
for design decisions with reasoning): if no event qualifies (or every
qualifying event's horizon runs past the end of the data), the statistic
is defined as 0.0. Reasoning: 0.0 is the value that asserts NOTHING about
direction -- a positive default would bias every population-starved
resample toward "significant", a negative one would bias the other way.
This matters most for the null model, where MANY resamples will
plausibly detect zero qualifying events; 0.0 keeps those resamples
neutral rather than silently favouring either verdict.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

CONTEXT_WINDOW = 10  # bars before the sweep, inclusive: [b-10, b-1] (spec §3)
HORIZON = 10  # bars after the sweep bar's close (spec §3)


class _HasClose(Protocol):
    close: float


def qualifying_events(sweep_observations, shift_observations, context_window: int = CONTEXT_WINDOW):
    """A sweep at bar b qualifies iff some structure-shift observation's
    `shift_bar` falls in [b - context_window, b - 1]. Reads ONLY bar
    indices -- see the module docstring's causality note. Returns the
    qualifying sweep observations, in the order given.
    """
    shift_bars = [s.shift_bar for s in shift_observations if s.kind == "STRUCTURE_SHIFT"]
    qualifying = []
    for sweep in sweep_observations:
        if sweep.kind != "SWEEP":
            continue
        b = sweep.sweep_bar
        window_start = b - context_window
        if any(window_start <= sb <= b - 1 for sb in shift_bars):
            qualifying.append(sweep)
    return tuple(qualifying)


def signed_forward_return(
    bars: Sequence[_HasClose], sweep_bar: int, direction: int, horizon: int = HORIZON
) -> float | None:
    """The forward return from `sweep_bar`'s close to the close `horizon`
    bars later, signed by `direction` so a reversal-consistent move is
    positive (spec §4). Returns None if `sweep_bar + horizon` is out of
    bounds for `bars` -- the caller decides how to treat that (this
    module's own `ls01_r001_statistic` excludes it from the mean, per
    the empty-population design decision above).
    """
    target = sweep_bar + horizon
    if target >= len(bars) or sweep_bar < 0 or sweep_bar >= len(bars):
        return None
    start_close = bars[sweep_bar].close
    end_close = bars[target].close
    raw_return = (end_close - start_close) / start_close
    return direction * raw_return


def ls01_r001_statistic(
    sweep_observations,
    shift_observations,
    bars: Sequence[_HasClose],
    context_window: int = CONTEXT_WINDOW,
    horizon: int = HORIZON,
) -> float:
    """Pure: (ObservationSets' observations + bars) -> a number. The mean
    signed forward return over qualifying events; 0.0 if none qualify or
    none has a computable forward return (see the module docstring).
    """
    qualifying = qualifying_events(sweep_observations, shift_observations, context_window)
    returns = []
    for sweep in qualifying:
        r = signed_forward_return(bars, sweep.sweep_bar, sweep.direction, horizon)
        if r is not None:
            returns.append(r)
    if not returns:
        return 0.0
    return sum(returns) / len(returns)
