"""N1-N4 (A-015 §5)."""

import statistics

from qrf.errors import InsufficientResamples
from qrf.kernel.null.resampling import (
    add_one_pvalue,
    block_resample_indices,
    check_alpha_achievable,
    min_achievable_pvalue,
    run_null_test,
)
from tests.drills.harness import DrillLog, run_drill

# --- N1: add-one estimator cannot return 0.0, even at maximal extremity --


def test_n1_add_one_pvalue_never_zero_at_maximal_extremity():
    # observed is more extreme than EVERY null draw -- count=0, yet p must
    # still be strictly positive.
    null_stats = [1.0] * 1000
    p = add_one_pvalue(observed_statistic=1000.0, null_statistics=null_stats)
    assert p > 0.0
    assert p == 1 / 1001


def test_n1_add_one_pvalue_never_zero_even_with_zero_resamples():
    p = add_one_pvalue(observed_statistic=5.0, null_statistics=[])
    assert p > 0.0
    assert p == 1.0


# --- N2: same seed + inputs reproduce the null distribution exactly ------


def test_n2_same_seed_reproduces_exactly():
    a = block_resample_indices(n_bars=50, block_length=10, n_resamples=20, seed=42)
    b = block_resample_indices(n_bars=50, block_length=10, n_resamples=20, seed=42)
    assert a == b


def test_n2_different_seed_drill():
    log = DrillLog()

    def checker(seed):
        return block_resample_indices(n_bars=50, block_length=10, n_resamples=20, seed=seed)

    # "control": same seed twice must match (not a drill exception, just a
    # direct equality check, done above). Here we drill that a DIFFERENT
    # seed is REQUIRED to (almost certainly) differ -- the harness wants
    # an exception-shaped drill, so we phrase it as: reusing the wrong
    # seed's result and asserting equality raises AssertionError.
    a = checker(1)

    def compare(same: bool):
        other = checker(1) if same else checker(2)
        assert a == other

    result = run_drill(
        name="N2-seed-changes-resample",
        checker=compare,
        clean_input=True,
        tampered_input=False,
        expected_exception=AssertionError,
        log=log,
    )
    assert result.tampered_exception is AssertionError


# --- N3: block structure preserved (a shuffle destroying it is distinguishable)


def test_n3_block_resample_preserves_contiguity():
    # every resample must be built from CONTIGUOUS runs of `block_length`
    # (mod n_bars) -- a plain independent shuffle would not have this
    # property. Check: within each block-sized chunk of the output, the
    # indices increase by exactly 1 (mod n_bars).
    n_bars, block_length = 30, 6
    resamples = block_resample_indices(n_bars, block_length, n_resamples=5, seed=7)
    for resample in resamples:
        for chunk_start in range(0, len(resample) - block_length + 1, block_length):
            chunk = resample[chunk_start : chunk_start + block_length]
            for a, b in zip(chunk, chunk[1:]):
                assert b == (a + 1) % n_bars, "block resampling must preserve contiguity"


def test_n3_block_resample_distinguishable_from_iid_shuffle():
    # A block resample of a strongly-trended series preserves local runs;
    # an i.i.d. shuffle of the same series destroys them. Use variance of
    # first differences as the discriminating statistic: shuffled data has
    # much higher first-difference variance than block-resampled data,
    # because shuffling breaks the smooth local trend into noise.
    series = list(range(100))  # a perfectly smooth trend
    resamples = block_resample_indices(100, block_length=20, n_resamples=1, seed=3)
    block_resampled = [series[i] for i in resamples[0]]
    block_diffs = [b - a for a, b in zip(block_resampled, block_resampled[1:])]
    block_variance = statistics.pvariance(block_diffs)

    import random

    shuffled = series[:]
    random.Random(3).shuffle(shuffled)
    shuffled_diffs = [b - a for a, b in zip(shuffled, shuffled[1:])]
    shuffled_variance = statistics.pvariance(shuffled_diffs)

    assert block_variance < shuffled_variance, (
        "block resampling must preserve local structure better than an "
        "i.i.d. shuffle of the same series"
    )


# --- N4: N too small for the allocated alpha -> REFUSED ------------------


def test_n4_insufficient_resamples_refused_drill():
    log = DrillLog()

    def checker(n_resamples):
        check_alpha_achievable(n_resamples, alpha=0.01)

    result = run_drill(
        name="N4-insufficient-resamples-refused",
        checker=checker,
        clean_input=200,  # min p = 1/201 ~ 0.005 < 0.01: achievable
        tampered_input=50,  # min p = 1/51 ~ 0.0196 > 0.01: NOT achievable
        expected_exception=InsufficientResamples,
        log=log,
    )
    assert result.tampered_exception is InsufficientResamples


def test_n4_run_null_test_refuses_before_resampling():
    """The refusal must happen BEFORE any resampling work, never as a
    "ran it anyway and reported not-significant" outcome.
    """
    try:
        run_null_test(
            series=list(range(50)),
            statistic_fn=statistics.mean,
            observed_statistic=100.0,
            block_length=5,
            n_resamples=10,  # min p = 1/11 ~ 0.09
            seed=1,
            alpha=0.01,  # unreachable at N=10
        )
    except InsufficientResamples as exc:
        assert exc.n_resamples == 10
        assert exc.alpha == 0.01
    else:
        raise AssertionError("expected InsufficientResamples")


def test_min_achievable_pvalue():
    assert min_achievable_pvalue(0) == 1.0
    assert min_achievable_pvalue(999) == 0.001
