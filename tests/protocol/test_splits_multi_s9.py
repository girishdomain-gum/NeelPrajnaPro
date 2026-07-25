"""Multi-window walk-forward splits (ARCH-009 §4, DEVQ-022 Option A).

The seam between concatenated windows is a HARD fold boundary: no test block
straddles it, and no window's train reaches into another window. These are the
properties DEVQ-022 ratified ("splits deterministic and property-tested, with the
exact seam-snapping convention"). Verified as exact geometry AND as invariants
over a matrix of shapes.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.protocol.splits import SplitSpec, walk_forward, walk_forward_multi


def _tuples(folds):
    return [(f.index, f.train.as_tuple(), f.test.as_tuple()) for f in folds]


def test_single_element_reduces_to_walk_forward():
    spec = SplitSpec(n_folds=3, embargo_bars=2)
    assert _tuples(walk_forward_multi([20], spec)) == _tuples(walk_forward(20, spec))


def test_exact_geometry_two_windows():
    # window A: 20 bars, window B: 20 bars (offset 20). Each 3 folds, embargo 0.
    folds = walk_forward_multi([20, 20], SplitSpec(n_folds=3, embargo_bars=0))
    assert _tuples(folds) == [
        (1, (0, 5), (5, 10)),
        (2, (0, 10), (10, 15)),
        (3, (0, 15), (15, 20)),
        # window B, offset +20, train anchored at the WINDOW start (20), not 0.
        (4, (20, 25), (25, 30)),
        (5, (20, 30), (30, 35)),
        (6, (20, 35), (35, 40)),
    ]


def test_index_is_globally_sequential():
    folds = walk_forward_multi([20, 20, 20], SplitSpec(n_folds=2, embargo_bars=0))
    assert [f.index for f in folds] == [1, 2, 3, 4, 5, 6]


@pytest.mark.parametrize(
    "lengths,n_folds,embargo",
    [
        ([20, 20], 3, 0),
        ([20, 20], 3, 2),
        ([30, 15], 4, 5),
        ([50, 50, 50], 5, 7),
        ([100, 37], 4, 23),
        ([12, 12], 1, 0),
    ],
)
def test_invariants(lengths, n_folds, embargo):
    spec = SplitSpec(n_folds=n_folds, embargo_bars=embargo)
    folds = walk_forward_multi(lengths, spec)
    total = sum(lengths)
    # seam boundaries in the concatenated index space.
    seams = []
    acc = 0
    for length in lengths:
        seams.append((acc, acc + length))
        acc += length

    def window_of(idx):
        for lo, hi in seams:
            if lo <= idx < hi:
                return (lo, hi)
        raise AssertionError(f"index {idx} outside all windows")

    tests = [f.test.as_tuple() for f in folds]
    # 1. every test range lies strictly inside [0, total) and is non-empty.
    for a, b in tests:
        assert 0 <= a < b <= total
    # 2. test ranges disjoint and ordered.
    for (_a0, a1), (b0, _b1) in zip(tests, tests[1:], strict=False):
        assert a1 <= b0
    # 3. no test range straddles a seam — it lies within one window.
    for a, b in tests:
        lo, hi = window_of(a)
        assert lo <= a < b <= hi, f"test [{a},{b}) straddles seam of window [{lo},{hi})"
    # 4. no train range crosses into another window (train within its window).
    for f in folds:
        lo, hi = window_of(f.test.start)
        assert f.train.start >= lo, "train reaches before its window (into an earlier window)"
        assert f.train.end <= f.test.start
        assert f.train.end <= hi


def test_deterministic():
    spec = SplitSpec(n_folds=4, embargo_bars=3)
    assert _tuples(walk_forward_multi([40, 30], spec)) == _tuples(
        walk_forward_multi([40, 30], spec)
    )


def test_empty_window_lengths_refused():
    with pytest.raises(SchemaViolation, match="non-empty list"):
        walk_forward_multi([], SplitSpec(n_folds=2))


def test_window_too_short_refused():
    # window of 2 bars cannot form 3 folds + seed (needs >= 4).
    with pytest.raises(SchemaViolation, match="too short"):
        walk_forward_multi([20, 2], SplitSpec(n_folds=3, embargo_bars=0))
