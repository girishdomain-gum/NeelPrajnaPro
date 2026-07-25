"""Anchored walk-forward splits with embargo (Blueprint §4.7 step 5, §4 tree).

The battery simulates a hypothesis over a window by walking forward: train on an
anchored, expanding prefix; test on the block that immediately follows; step the
test block forward; repeat. An *embargo* gap of ``embargo_bars`` separates each
train from its test so serial correlation cannot leak backward across the
boundary. This module turns a ``split_spec {n_folds, embargo_bars}`` and a window
length into the ordered ``(train, test)`` index ranges — nothing more; it reads no
bars and knows no prices, so it is kernel and domain-blind.

Geometry (normative — the convention recorded for ratification in DEVQ-011):

* The window is the half-open index range ``[0, n_bars)``. It is partitioned into
  ``n_folds + 1`` contiguous, near-equal blocks ``B0, B1, …, B_{n_folds}``; any
  remainder bars are handed to the earliest blocks (deterministic). ``B0`` is the
  initial anchored training seed; ``B1 … B_{n_folds}`` are the test blocks.
* Fold ``i`` (1-based, ``i = 1 … n_folds``):
    - ``test_i  = B_i = [t0_i, t1_i)``
    - ``train_i = [0, max(0, t0_i - embargo_bars))`` — anchored at the window
      start, expanding each fold, with the ``embargo_bars`` immediately before the
      test block withheld (the leakage gap at the train→test boundary).

Properties guaranteed (and tested):
    * test ranges are disjoint and strictly ordered (contiguous blocks);
    * no train range overlaps its own test range (the embargo gap ≥ 0 ensures
      ``train_i.end ≤ test_i.start``);
    * every range lies strictly inside ``[0, n_bars)``;
    * the function is a pure, deterministic function of ``(n_bars, spec)``.

An embargo large enough to erase a fold's train yields an empty ``train`` range
``[0, 0)`` — a legitimate, explicit boundary case (see :meth:`IndexRange.is_empty`),
never a silent error.
"""

from __future__ import annotations

from dataclasses import dataclass

from qrf.kernel.errors import SchemaViolation


@dataclass(frozen=True, slots=True)
class IndexRange:
    """A half-open index range ``[start, end)`` inside a window."""

    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end < 0:
            raise SchemaViolation(f"IndexRange bounds must be >= 0, got [{self.start},{self.end})")
        if self.end < self.start:
            raise SchemaViolation(f"IndexRange end < start: [{self.start},{self.end})")

    def __len__(self) -> int:
        return self.end - self.start

    @property
    def is_empty(self) -> bool:
        return self.end == self.start

    def as_tuple(self) -> tuple[int, int]:
        return (self.start, self.end)


@dataclass(frozen=True, slots=True)
class Fold:
    """One walk-forward fold: an anchored ``train`` range and its ``test`` block."""

    index: int  # 1-based fold number
    train: IndexRange
    test: IndexRange


@dataclass(frozen=True, slots=True)
class SplitSpec:
    """A hypothesis's ``split_spec`` (Blueprint §2 hypothesis payload)."""

    n_folds: int
    embargo_bars: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.n_folds, int) or isinstance(self.n_folds, bool) or self.n_folds < 1:
            raise SchemaViolation(f"split_spec.n_folds must be an int >= 1, got {self.n_folds!r}")
        if (
            not isinstance(self.embargo_bars, int)
            or isinstance(self.embargo_bars, bool)
            or self.embargo_bars < 0
        ):
            raise SchemaViolation(
                f"split_spec.embargo_bars must be an int >= 0, got {self.embargo_bars!r}"
            )

    def as_dict(self) -> dict[str, int]:
        return {"n_folds": self.n_folds, "embargo_bars": self.embargo_bars}


def _block_bounds(n_bars: int, n_blocks: int) -> list[int]:
    """Cumulative boundaries of ``n_blocks`` near-equal contiguous blocks over ``[0, n_bars)``.

    Returns ``n_blocks + 1`` boundary indices ``[0, …, n_bars]``. Remainder bars go
    to the earliest blocks, so the split is deterministic and boundary indices are
    non-decreasing.
    """
    base, rem = divmod(n_bars, n_blocks)
    bounds = [0]
    for b in range(n_blocks):
        size = base + (1 if b < rem else 0)
        bounds.append(bounds[-1] + size)
    return bounds


def walk_forward(n_bars: int, spec: SplitSpec) -> list[Fold]:
    """Build the ordered anchored walk-forward folds for a window of ``n_bars``.

    Raises :class:`SchemaViolation` if the window is too short to carry one
    training seed block plus ``n_folds`` test blocks (``n_bars >= n_folds + 1``).
    """
    if not isinstance(n_bars, int) or isinstance(n_bars, bool) or n_bars < 1:
        raise SchemaViolation(f"n_bars must be an int >= 1, got {n_bars!r}")
    n_blocks = spec.n_folds + 1
    if n_bars < n_blocks:
        raise SchemaViolation(
            f"window too short: {n_bars} bars cannot form {n_blocks} blocks "
            f"(need >= {n_blocks} for {spec.n_folds} folds + 1 anchored seed)"
        )

    bounds = _block_bounds(n_bars, n_blocks)
    folds: list[Fold] = []
    for i in range(1, spec.n_folds + 1):
        t0, t1 = bounds[i], bounds[i + 1]
        train_end = max(0, t0 - spec.embargo_bars)
        folds.append(
            Fold(index=i, train=IndexRange(0, train_end), test=IndexRange(t0, t1))
        )
    return folds
