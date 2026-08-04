"""F-09/A-035: drills for the circular-shift null."""

from dataclasses import dataclass

import pytest

from qrf.errors import InsufficientResamples
from qrf.kernel.measurement.circular_shift_null import (
    circular_shift_offsets,
    circular_shift_statistic,
    run_circular_shift_null_test,
)


@dataclass(frozen=True)
class _FakeEvent:
    sweep_bar: int
    direction: int


@dataclass(frozen=True)
class _FakeBar:
    close: float


def _bars(closes):
    return tuple(_FakeBar(close=c) for c in closes)


# --- offsets: determinism, minimum magnitude, wrap complement -------------


def test_offsets_are_deterministic():
    a = circular_shift_offsets(n_bars=1000, n_resamples=50, seed=7, min_offset=200)
    b = circular_shift_offsets(n_bars=1000, n_resamples=50, seed=7, min_offset=200)
    assert a == b


def test_offsets_respect_min_offset_both_sides():
    offsets = circular_shift_offsets(n_bars=1000, n_resamples=200, seed=7, min_offset=200)
    for s in offsets:
        assert 200 <= s <= 800  # s and its wrapped complement (n_bars - s) both >= min_offset


def test_offsets_refuses_when_n_bars_too_small_for_min_offset():
    with pytest.raises(ValueError):
        circular_shift_offsets(n_bars=300, n_resamples=10, seed=1, min_offset=200)


# --- circular_shift_statistic: wrapping and empty population --------------


def test_circular_shift_wraps_around_the_end():
    # 10 bars, sweep at bar 8, horizon 5: (8+shift)%10 and (+5)%10 must wrap.
    events = [_FakeEvent(sweep_bar=8, direction=1)]
    bars = _bars([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0])
    # shift=0 (not realistic given min_offset, but isolates the wrap math):
    # start_idx = 8, end_idx = (8+5)%10 = 3 -> closes[3]=103.0
    stat = circular_shift_statistic(events, bars, shift=0, horizon=5)
    expected = (103.0 - 108.0) / 108.0
    assert abs(stat - expected) < 1e-9


def test_circular_shift_empty_population_returns_zero():
    assert circular_shift_statistic([], _bars([100.0] * 20), shift=5, horizon=5) == 0.0


def test_circular_shift_one_offset_applies_to_every_event_identically():
    """A-035: ONE offset per resample for ALL events, not independent
    per-event shifts -- proven by checking two events at different bars
    both get the SAME shift applied.
    """
    bars = _bars([100.0 + i * 0.1 for i in range(50)])
    events = [_FakeEvent(sweep_bar=5, direction=1), _FakeEvent(sweep_bar=20, direction=1)]
    shift = 3
    stat = circular_shift_statistic(events, bars, shift=shift, horizon=2)

    def expected_return(sweep_bar):
        start = bars[(sweep_bar + shift) % 50].close
        end = bars[(sweep_bar + shift + 2) % 50].close
        return (end - start) / start

    r1 = expected_return(5)
    r2 = expected_return(20)
    assert abs(stat - (r1 + r2) / 2) < 1e-9


# --- run_circular_shift_null_test: alpha achievability, determinism -------


def test_insufficient_resamples_refused_before_anything_runs():
    events = [_FakeEvent(sweep_bar=500, direction=1)]
    bars = _bars([100.0] * 1000)
    with pytest.raises(InsufficientResamples):
        run_circular_shift_null_test(
            events, bars, observed_statistic=0.01, min_offset=200,
            n_resamples=10, seed=1, alpha=0.025, excluded_count=0, horizon=10,
        )


def test_null_test_is_deterministic():
    events = [_FakeEvent(sweep_bar=500, direction=1), _FakeEvent(sweep_bar=700, direction=-1)]
    bars = _bars([100.0 + (i % 7) * 0.05 for i in range(2000)])
    r1 = run_circular_shift_null_test(
        events, bars, observed_statistic=0.01, min_offset=200,
        n_resamples=50, seed=3, alpha=0.025, excluded_count=0, horizon=10,
    )
    r2 = run_circular_shift_null_test(
        events, bars, observed_statistic=0.01, min_offset=200,
        n_resamples=50, seed=3, alpha=0.025, excluded_count=0, horizon=10,
    )
    assert r1.null_statistics == r2.null_statistics
    assert r1.p_value == r2.p_value


# --- the sanity property this null was built to have: shifting AWAY from
# a real local move must be able to disagree with the real, unshifted stat


def test_shifted_statistic_differs_from_a_strong_local_planted_move():
    """Not a full power check (see tests/kernel/test_s08_power_check.py
    for that) -- a small, direct proof that circularly shifting a real
    event's window OUT of a strong local move changes the computed
    return, which the OLD block-resampling null could never show because
    it re-detected the same welded event inside every resample.
    """
    n = 2000
    closes = [100.0] * n
    # a strong local decline right after bar 1000 (the "real event")
    for i in range(1001, 1011):
        closes[i] = 100.0 - (i - 1000) * 1.0
    bars = _bars(closes)
    event = _FakeEvent(sweep_bar=1000, direction=-1)  # expects a decline
    real = circular_shift_statistic([event], bars, shift=0, horizon=10)
    shifted_far = circular_shift_statistic([event], bars, shift=500, horizon=10)
    assert real > 0  # the real event's own window IS the strong decline
    assert abs(shifted_far) < abs(real)  # shifted away, it lands in flat bars
