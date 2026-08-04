"""S08 Phase 1 X3/X4/X5: LS-01-R001's statistic module drills. Uses
lightweight fakes for sweep/shift observations -- this module is
duck-typed on purpose (see its own docstring), so a fake with the right
attributes IS a valid input, not a workaround.
"""

from dataclasses import dataclass

from qrf.kernel.measurement.ls01_r001 import (
    ls01_r001_statistic,
    qualifying_events,
    qualifying_events_with_valid_horizon,
    signed_forward_return,
)


@dataclass(frozen=True)
class _FakeSweep:
    kind: str
    sweep_bar: int
    direction: int


@dataclass(frozen=True)
class _FakeShift:
    kind: str
    shift_bar: int


@dataclass(frozen=True)
class _FakeBar:
    close: float


def _bars(closes):
    return tuple(_FakeBar(close=c) for c in closes)


# --- X4: the [b-10, b-1] window boundary -----------------------------


def test_x4_shift_at_b_minus_11_does_not_qualify():
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=50, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=39)  # 50-11
    assert qualifying_events([sweep], [shift]) == ()


def test_x4_shift_at_b_minus_1_qualifies():
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=50, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=49)  # 50-1
    assert qualifying_events([sweep], [shift]) == (sweep,)


def test_x4_shift_at_b_minus_10_qualifies_inclusive_boundary():
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=50, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=40)  # 50-10
    assert qualifying_events([sweep], [shift]) == (sweep,)


def test_x4_shift_at_b_itself_does_not_qualify():
    """The shift must be strictly BEFORE the sweep bar (spec §2's
    causality requirement) -- a shift AT the sweep bar is not "before".
    """
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=50, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=50)
    assert qualifying_events([sweep], [shift]) == ()


# --- X5: causality -- no future bar can influence qualification or leak ---


def test_x5_qualification_never_reads_bars():
    """qualifying_events() takes no `bars` argument at all -- a future
    close cannot influence membership because the function has no way to
    see one. This test exists to keep that signature honest: if a future
    change added a `bars` parameter, this call would break loudly.
    """
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=5, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=1)
    assert qualifying_events([sweep], [shift]) == (sweep,)


def test_x5_forward_return_unaffected_by_bars_beyond_horizon():
    # sweep_bar=5, horizon=1 -> target bar is index 6 (110.0 in both). Only
    # bars[7:] differ between the two series -- must not change the result.
    bars_a = _bars([100.0] * 5 + [110.0] + [110.0] + [999.0] * 20)
    bars_b = _bars([100.0] * 5 + [110.0] + [110.0] + [1.0] * 20)
    ra = signed_forward_return(bars_a, sweep_bar=5, direction=1, horizon=1)
    rb = signed_forward_return(bars_b, sweep_bar=5, direction=1, horizon=1)
    assert ra == rb  # only bars[5] and bars[6] matter; bars[7:] never read


def test_x5_forward_return_reflects_exactly_the_horizon_bar():
    bars = _bars([100.0, 100.0, 100.0, 100.0, 100.0, 105.0, 200.0])
    r_h1 = signed_forward_return(bars, sweep_bar=4, direction=1, horizon=1)  # -> bar 5 (105.0)
    r_h2 = signed_forward_return(bars, sweep_bar=4, direction=1, horizon=2)  # -> bar 6 (200.0)
    assert abs(r_h1 - 0.05) < 1e-9
    assert r_h2 > r_h1  # different horizon bar, different (much larger) result


def test_out_of_bounds_horizon_returns_none():
    bars = _bars([100.0, 101.0])
    assert signed_forward_return(bars, sweep_bar=1, direction=1, horizon=5) is None


# --- X3: purity / determinism ------------------------------------------


def test_x3_statistic_is_pure_and_deterministic():
    sweeps = [
        _FakeSweep(kind="SWEEP", sweep_bar=20, direction=1),
        _FakeSweep(kind="SWEEP", sweep_bar=50, direction=-1),
    ]
    shifts = [
        _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=15),
        _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=45),
    ]
    bars = _bars([100.0 + i * 0.1 for i in range(70)])
    r1 = ls01_r001_statistic(sweeps, shifts, bars)
    r2 = ls01_r001_statistic(sweeps, shifts, bars)
    assert r1 == r2
    # inputs untouched (no mutation -- part of purity)
    assert sweeps[0].sweep_bar == 20
    assert len(bars) == 70


def test_empty_population_returns_zero():
    assert ls01_r001_statistic([], [], _bars([100.0] * 20)) == 0.0


def test_statistic_sign_matches_direction():
    """A HIGH-side sweep (direction=-1, expects a decline) that IS
    followed by a decline must produce a POSITIVE signed statistic
    (spec §4: reversal-consistent move is positive).
    """
    sweep = _FakeSweep(kind="SWEEP", sweep_bar=5, direction=-1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=1)
    bars = _bars([100.0] * 5 + [100.0] + [90.0] * 10)  # decline after the sweep bar
    stat = ls01_r001_statistic([sweep], [shift], bars, horizon=1)
    assert stat > 0


# --- A-035 R2: one shared qualifying-set definition, horizon-bounded ------


def test_valid_horizon_excludes_events_running_past_the_end():
    """A sweep at bar 8 with horizon=5 in a 10-bar series needs bar 13,
    which does not exist -- excluded from the valid set, and the
    exclusion is counted.
    """
    sweep_near_end = _FakeSweep(kind="SWEEP", sweep_bar=8, direction=1)
    sweep_with_room = _FakeSweep(kind="SWEEP", sweep_bar=2, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=1)
    bars = _bars([100.0] * 10)
    valid, excluded = qualifying_events_with_valid_horizon(
        [sweep_near_end, sweep_with_room], [shift], bars, context_window=10, horizon=5
    )
    assert sweep_with_room in valid
    assert sweep_near_end not in valid
    assert excluded == 1


def test_statistic_uses_only_the_valid_set():
    """ls01_r001_statistic must average over exactly the same set
    qualifying_events_with_valid_horizon() would return -- not a
    superset that happens to skip None results some other way.
    """
    sweep_near_end = _FakeSweep(kind="SWEEP", sweep_bar=8, direction=1)
    shift = _FakeShift(kind="STRUCTURE_SHIFT", shift_bar=1)
    bars = _bars([100.0] * 10)
    # the only qualifying sweep has no valid horizon -> empty population -> 0.0
    assert ls01_r001_statistic([sweep_near_end], [shift], bars, horizon=5) == 0.0
