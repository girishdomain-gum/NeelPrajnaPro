"""Anchored walk-forward split tests (ARCH-005 §3, Blueprint §4.7 step 5).

Covers: exact geometry, the boundary matrix (first/last fold, embargo at edges),
the no-overlap property, in-window containment, anchoring, determinism, remainder
distribution, and validation.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.splits import (
    IndexRange,
    SplitSpec,
    walk_forward,
)


def _tuples(folds):
    return [(f.index, f.train.as_tuple(), f.test.as_tuple()) for f in folds]


# --- exact geometry ----------------------------------------------------------
def test_exact_geometry_no_embargo():
    folds = walk_forward(20, SplitSpec(n_folds=3, embargo_bars=0))
    # 4 blocks of 5: seed [0,5); tests [5,10),[10,15),[15,20); anchored trains.
    assert _tuples(folds) == [
        (1, (0, 5), (5, 10)),
        (2, (0, 10), (10, 15)),
        (3, (0, 15), (15, 20)),
    ]


def test_exact_geometry_with_embargo():
    folds = walk_forward(20, SplitSpec(n_folds=3, embargo_bars=2))
    assert _tuples(folds) == [
        (1, (0, 3), (5, 10)),
        (2, (0, 8), (10, 15)),
        (3, (0, 13), (15, 20)),
    ]


def test_remainder_goes_to_earliest_blocks():
    # 23 bars, 3 folds -> 4 blocks, base 5 rem 3 -> sizes 6,6,6,5.
    folds = walk_forward(23, SplitSpec(n_folds=3, embargo_bars=0))
    assert [f.test.as_tuple() for f in folds] == [(6, 12), (12, 18), (18, 23)]
    assert folds[0].train.as_tuple() == (0, 6)


# --- properties over a matrix ------------------------------------------------
_MATRIX = [
    (n, SplitSpec(n_folds=k, embargo_bars=e))
    for n in (12, 20, 23, 100, 251)
    for k in (1, 2, 3, 5)
    for e in (0, 1, 3, 7)
    if n >= k + 1
]


@pytest.mark.parametrize("n_bars,spec", _MATRIX)
def test_test_ranges_disjoint_and_ordered(n_bars, spec):
    folds = walk_forward(n_bars, spec)
    assert len(folds) == spec.n_folds
    prev_end = -1
    for f in folds:
        assert f.test.start >= prev_end  # ordered, non-overlapping
        assert f.test.start < f.test.end  # every test block is non-empty
        prev_end = f.test.end


@pytest.mark.parametrize("n_bars,spec", _MATRIX)
def test_all_ranges_inside_window(n_bars, spec):
    for f in walk_forward(n_bars, spec):
        assert 0 <= f.train.start <= f.train.end <= n_bars
        assert 0 <= f.test.start <= f.test.end <= n_bars


@pytest.mark.parametrize("n_bars,spec", _MATRIX)
def test_train_never_overlaps_its_test(n_bars, spec):
    for f in walk_forward(n_bars, spec):
        assert f.train.end <= f.test.start  # embargo gap keeps them apart


@pytest.mark.parametrize("n_bars,spec", _MATRIX)
def test_train_is_anchored_at_window_start(n_bars, spec):
    for f in walk_forward(n_bars, spec):
        assert f.train.start == 0


@pytest.mark.parametrize("n_bars,spec", _MATRIX)
def test_deterministic(n_bars, spec):
    assert _tuples(walk_forward(n_bars, spec)) == _tuples(walk_forward(n_bars, spec))


# --- embargo at the edges ----------------------------------------------------
def test_large_embargo_yields_empty_train():
    # embargo >= first test's start collapses the first fold's train to [0,0).
    folds = walk_forward(20, SplitSpec(n_folds=3, embargo_bars=100))
    assert folds[0].train.as_tuple() == (0, 0)
    assert folds[0].train.is_empty
    # later folds' trains are also clamped but still valid ranges.
    for f in folds:
        assert not f.train.start > f.train.end


def test_first_and_last_fold_indices():
    folds = walk_forward(50, SplitSpec(n_folds=5, embargo_bars=1))
    assert folds[0].index == 1
    assert folds[-1].index == 5
    assert folds[-1].test.end == 50  # last test reaches the window end


# --- validation --------------------------------------------------------------
@pytest.mark.parametrize("bad", [0, -1, 1.5, True])
def test_bad_n_folds_rejected(bad):
    with pytest.raises(SchemaViolation):
        SplitSpec(n_folds=bad)


@pytest.mark.parametrize("bad", [-1, 1.5, True])
def test_bad_embargo_rejected(bad):
    with pytest.raises(SchemaViolation):
        SplitSpec(n_folds=2, embargo_bars=bad)


def test_window_too_short_rejected():
    with pytest.raises(SchemaViolation):
        walk_forward(3, SplitSpec(n_folds=3))  # needs >= 4 bars for 3 folds + seed


def test_index_range_rejects_inverted():
    with pytest.raises(SchemaViolation):
        IndexRange(5, 3)
