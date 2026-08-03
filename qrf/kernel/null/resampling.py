"""The null model: block resampling + the add-one p-value estimator
(A-015 §2).

THE QUESTION: how often would a result this strong appear by chance in
data with the SAME STRUCTURE but no real effect? Market data has
autocorrelation, volatility clustering and session structure; resampling
single bars independently would destroy that structure and call noise
significant. Resampling in contiguous BLOCKS preserves local structure.

BLOCK LENGTH DERIVATION (A-015 §2.2: stated, zero-discretion, from the
hypothesis's OWN constants -- never a number chosen because it "looks
right"): `block_length_from_detector()` takes a detector's own
MEMBER_WINDOW constant and uses it directly. Reasoning: MEMBER_WINDOW is
the longest span over which THAT detector's own mechanics can create a
dependency between two bars (pool membership looks back up to this many
bars, per Appendix B.2) -- so a block shorter than this could sample two
bars the detector treats as related while breaking whatever local
structure created that relation. For the liquidity sweep detector (H-07),
MEMBER_WINDOW = 200 bars, so block_length = 200. A hypothesis using a
different detector derives its own block length the same way, from that
detector's own constant -- never a shared default.

THE P-VALUE (A-015 §2.3): the add-one estimator, p = (1 + #{null >=
observed}) / (1 + N). Structurally incapable of returning 0.0 for any N
and any inputs -- an unattainable p is a lie about certainty.

REPRODUCIBILITY (A-015 §2.5): `block_resample_indices` is a pure function
of (n_bars, block_length, n_resamples, seed) using Python's stdlib
`random.Random(seed)`, which is itself deterministic given a seed -- the
same four inputs always produce the same resample indices.
"""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass

from qrf.errors import InsufficientResamples


def block_length_from_detector(member_window: int) -> int:
    """Derive the block length from a detector's own MEMBER_WINDOW
    constant. See the module docstring for the reasoning. Zero discretion:
    this is the identity function on purpose, so the derivation rule is
    the whole of what a reader needs to check, not a hidden multiplier.
    """
    return member_window


def min_achievable_pvalue(n_resamples: int) -> float:
    return 1 / (1 + n_resamples)


def check_alpha_achievable(n_resamples: int, alpha: float) -> None:
    """Refuse if the allocated alpha is smaller than what N resamples can
    ever achieve -- the battery must not run a test that cannot possibly
    reject, then report a foregone "not significant" (A-015 §2.4).
    """
    if min_achievable_pvalue(n_resamples) > alpha:
        raise InsufficientResamples(n_resamples, alpha)


def add_one_pvalue(observed_statistic: float, null_statistics: Sequence[float]) -> float:
    """p = (1 + #{null >= observed}) / (1 + N). Always > 0, for any N
    (including N=0) and any inputs -- there is no code path that can
    divide by zero or return exactly 0.0.
    """
    n = len(null_statistics)
    count = sum(1 for x in null_statistics if x >= observed_statistic)
    return (1 + count) / (1 + n)


def block_resample_indices(
    n_bars: int, block_length: int, n_resamples: int, seed: int
) -> tuple[tuple[int, ...], ...]:
    """Return `n_resamples` index tuples, each of length `n_bars`, built
    by drawing contiguous (circularly-wrapped) blocks of `block_length`
    with replacement until `n_bars` indices are filled, then truncating
    to exactly `n_bars`. Deterministic: the same (n_bars, block_length,
    n_resamples, seed) always produces the same output.
    """
    rng = random.Random(seed)
    n_blocks_needed = -(-n_bars // block_length)  # ceil division
    resamples = []
    for _ in range(n_resamples):
        idx: list[int] = []
        for _b in range(n_blocks_needed):
            start = rng.randrange(n_bars)
            idx.extend((start + offset) % n_bars for offset in range(block_length))
        resamples.append(tuple(idx[:n_bars]))
    return tuple(resamples)


@dataclass(frozen=True)
class NullResult:
    """Everything needed to reproduce and audit one null test."""

    p_value: float
    n_resamples: int
    seed: int
    block_length: int
    null_statistics: tuple[float, ...]


def run_null_test(
    series: Sequence[float],
    statistic_fn,
    observed_statistic: float,
    block_length: int,
    n_resamples: int,
    seed: int,
    alpha: float,
) -> NullResult:
    """Refuses (InsufficientResamples) before running anything if `alpha`
    is not achievable at this `n_resamples`. Otherwise resamples `series`
    in blocks, computes `statistic_fn` on each resample, and returns the
    add-one p-value against `observed_statistic`.
    """
    check_alpha_achievable(n_resamples, alpha)
    resample_idx = block_resample_indices(len(series), block_length, n_resamples, seed)
    null_statistics = tuple(statistic_fn([series[i] for i in idx]) for idx in resample_idx)
    p_value = add_one_pvalue(observed_statistic, null_statistics)
    return NullResult(
        p_value=p_value,
        n_resamples=n_resamples,
        seed=seed,
        block_length=block_length,
        null_statistics=null_statistics,
    )
