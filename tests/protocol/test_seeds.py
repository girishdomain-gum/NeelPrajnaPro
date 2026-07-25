"""Seed-derivation tests (ARCH-005 §2, Blueprint §4.7 step 4).

Covers: determinism, input sensitivity, range, exact-recipe reproducibility, and
input validation.
"""

from __future__ import annotations

import hashlib

import pytest

from qrf.kernel.protocol import seeds
from qrf.kernel.records.record import canonical_bytes

H = "01KYBHYPOTHESIS00000000000"
W = "01KYB4SSC96SSS8RA7D1NMTPEX"


def test_deterministic_same_inputs():
    assert seeds.for_run(H, W) == seeds.for_run(H, W)


def test_input_sensitive_both_anchors():
    base = seeds.for_run(H, W)
    assert seeds.for_run(H + "X", W) != base
    assert seeds.for_run(H, W + "X") != base


def test_seed_is_nonnegative_63_bit():
    s = seeds.for_run(H, W)
    assert 0 <= s < (1 << 63)


def test_recipe_reproducible_by_hand():
    body = canonical_bytes({"hypothesis_ref": H, "window_ref": W})
    expected = int.from_bytes(hashlib.sha256(body).digest()[:8], "big") & ((1 << 63) - 1)
    assert seeds.for_run(H, W) == expected


def test_anchor_order_matters():
    # The two anchors are keyed, not concatenated, so swapping them changes the seed.
    assert seeds.for_run(H, W) != seeds.for_run(W, H)


@pytest.mark.parametrize("bad", ["", None, 123])
def test_rejects_bad_hypothesis_ref(bad):
    with pytest.raises(ValueError):
        seeds.for_run(bad, W)


@pytest.mark.parametrize("bad", ["", None, 123])
def test_rejects_bad_window_ref(bad):
    with pytest.raises(ValueError):
        seeds.for_run(H, bad)
