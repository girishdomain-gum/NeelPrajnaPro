"""The circular-shift null (F-09, A-034/A-035): the correct null for
LS-01-R001's statistic, replacing the block-resampling null that S08
Phase 1's rehearsal proved BLIND to a real, population-wide effect at
the real block_length (D-024: not significant across three independent
constructions; a 10x larger effect made p WORSE, not better -- ruling
out an ordinary power problem).

THE DIAGNOSIS (A-034), restated here because it is what this module
exists to fix: a null must destroy the thing being tested. Block-
resampling the raw bar series and RE-DETECTING on every resample welds
each event back to its own outcome inside every resample -- the
association survives resampling intact, so the test correctly (but
uselessly) finds "no difference" between the effect and the effect,
reshuffled.

**DETECTION RUNS EXACTLY ONCE, ON THE REAL DATA, AND IS NEVER RE-RUN FOR
THE NULL.** That is the actual fix (A-035's own words, kept verbatim
because they are exactly right): the real events -- their bar positions,
directions, and count -- never change. The null asks a different
question of those SAME events: would this event's outcome look unusual
paired with a different moment's return instead of its own? Nothing is
synthesized, so nothing can smuggle the association back in.

MECHANISM: for resample `r`, draw ONE integer offset `s_r` (never an
independent shift per event -- A-035: "isolates exactly one
relationship" and preserves the events' own mutual clustering) and pair
every real qualifying event's bar with the close-price series read from
`(sweep_bar + s_r) % n_bars` instead of its own real position. This
preserves the real events' timing/clustering AND the real price series'
own autocorrelation/volatility structure; it destroys only the specific
correspondence between a given event and the return that actually
followed it.

MINIMUM OFFSET MAGNITUDE (A-035 R1, zero discretion, same derivation
S05 already used for block length): an offset smaller than
`min_offset` (the detector's own dependence length -- pass
`block_length_from_detector(MEMBER_WINDOW)` from the caller, this
module stays duck-typed/detector-agnostic like the rest of
`qrf/kernel/measurement/`) lands the "null" window inside the SAME
local price move the real event was part of, diluting rather than
destroying the link. Offsets are drawn from `{min_offset, ...,
n_bars - min_offset}` so both the offset and its wrapped complement
clear the dependence length.

SAME QUALIFYING SET FOR BOTH SIDES (A-035 R2): the real observed
statistic and every null resample use the IDENTICAL event set --
`ls01_r001.qualifying_events_with_valid_horizon()`'s output -- so a
difference between them is never partly an artefact of which events
each one happened to include. The real statistic never wraps (it never
invents data past the end of what was actually collected); the null
always wraps (a circular test must). Both true only because both start
from the same fixed set.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from qrf.kernel.null.resampling import add_one_pvalue, check_alpha_achievable


class _HasClose(Protocol):
    close: float


@dataclass(frozen=True)
class CircularShiftNullResult:
    """Everything needed to reproduce and audit one circular-shift null
    test -- mirrors qrf.kernel.null.resampling.NullResult's shape, with
    `min_offset` in place of `block_length` and `excluded_count` for the
    A-035 R2 requirement that a reader know how many events the horizon
    cost at the tail.
    """

    p_value: float
    n_resamples: int
    seed: int
    min_offset: int
    excluded_count: int
    null_statistics: tuple[float, ...]


def circular_shift_offsets(
    n_bars: int, n_resamples: int, seed: int, min_offset: int
) -> tuple[int, ...]:
    """`n_resamples` offsets, each drawn uniformly from
    `{min_offset, ..., n_bars - min_offset}`, deterministic given
    (n_bars, n_resamples, seed, min_offset) -- same reproducibility
    guarantee as `block_resample_indices`.
    """
    if n_bars < 2 * min_offset:
        raise ValueError(
            f"n_bars ({n_bars}) must be at least 2*min_offset ({2 * min_offset}) "
            "for any offset to clear the dependence length on both sides"
        )
    rng = random.Random(seed)
    lo, hi = min_offset, n_bars - min_offset
    return tuple(rng.randint(lo, hi) for _ in range(n_resamples))


def circular_shift_statistic(
    qualifying_events, bars: Sequence[_HasClose], shift: int, horizon: int
) -> float:
    """The mean signed forward return over `qualifying_events` (already
    filtered to a valid horizon -- see
    `ls01_r001.qualifying_events_with_valid_horizon`), each event's
    close-price window shifted circularly by `shift` bars. 0.0 if
    `qualifying_events` is empty (same empty-population convention as
    `ls01_r001_statistic`).
    """
    n = len(bars)
    returns = []
    for event in qualifying_events:
        start_idx = (event.sweep_bar + shift) % n
        end_idx = (start_idx + horizon) % n
        start_close = bars[start_idx].close
        end_close = bars[end_idx].close
        returns.append(event.direction * (end_close - start_close) / start_close)
    if not returns:
        return 0.0
    return sum(returns) / len(returns)


def run_circular_shift_null_test(
    qualifying_events,
    bars: Sequence[_HasClose],
    observed_statistic: float,
    min_offset: int,
    n_resamples: int,
    seed: int,
    alpha: float,
    excluded_count: int,
    horizon: int,
) -> CircularShiftNullResult:
    """Refuses (InsufficientResamples) before running anything if `alpha`
    is not achievable at `n_resamples` -- reuses S05's own check
    unchanged. Otherwise draws `n_resamples` circular-shift offsets and
    computes the add-one p-value against `observed_statistic`, exactly
    like the block-resampling null does, over the SAME event population.
    """
    check_alpha_achievable(n_resamples, alpha)
    offsets = circular_shift_offsets(len(bars), n_resamples, seed, min_offset)
    null_statistics = tuple(
        circular_shift_statistic(qualifying_events, bars, s, horizon) for s in offsets
    )
    p_value = add_one_pvalue(observed_statistic, null_statistics)
    return CircularShiftNullResult(
        p_value=p_value,
        n_resamples=n_resamples,
        seed=seed,
        min_offset=min_offset,
        excluded_count=excluded_count,
        null_statistics=null_statistics,
    )
