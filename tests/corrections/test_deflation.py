"""Deflation — the Bonferroni multiple-testing penalty (ARCH-006 §2, Blueprint §4.8).

The correction must be EXACTLY ``base_alpha / max(1, N_trials)`` with ``N_trials``
read from the real trial ledger for a ``(scope, lineage)`` pair — pinned here
against hand numbers so a drift in the formula cannot pass unnoticed.
"""

from __future__ import annotations

import pytest

from qrf.kernel.corrections.deflation import (
    METHOD,
    _is_prefix_segment,
    deflate,
    deflate_family,
    effective_alpha,
    family_trials,
)
from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.store import RecordStore


def _store(tmp_path) -> RecordStore:
    return RecordStore(tmp_path / "journal.jsonl")


def test_zero_trials_keeps_face_alpha(tmp_path):
    store = _store(tmp_path)
    # No trials recorded for this pair: max(1, 0) = 1, so alpha is unchanged.
    assert effective_alpha(0.05, "xauusd_h1", "h001", store) == pytest.approx(0.05)
    d = deflate(0.05, "xauusd_h1", "h001", store)
    assert (d.base_alpha, d.n_trials, d.method) == (0.05, 0, METHOD)
    assert d.effective_alpha == pytest.approx(0.05)


def test_bonferroni_divides_by_total(tmp_path):
    store = _store(tmp_path)
    ledger = TrialCountLedger(store)
    ledger.bump("xauusd_h1", "h001", 500, "screener")
    # 0.05 / 500 = 1e-4 exactly.
    assert effective_alpha(0.05, "xauusd_h1", "h001", store) == pytest.approx(1e-4)
    assert deflate(0.05, "xauusd_h1", "h001", store).n_trials == 500


def test_totals_accumulate_and_isolate_by_key(tmp_path):
    store = _store(tmp_path)
    ledger = TrialCountLedger(store)
    ledger.bump("xauusd_h1", "h001", 3, "human")
    ledger.bump("xauusd_h1", "h001", 7, "screener")     # same key -> 10 total
    ledger.bump("xauusd_h1", "other", 99, "screener")   # different lineage -> ignored
    ledger.bump("eurusd_h1", "h001", 99, "screener")    # different scope -> ignored
    assert deflate(0.05, "xauusd_h1", "h001", store).n_trials == 10
    assert effective_alpha(0.05, "xauusd_h1", "h001", store) == pytest.approx(0.05 / 10)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 2.0])
def test_bad_base_alpha_refused(tmp_path, bad):
    with pytest.raises(SchemaViolation):
        deflate(bad, "s", "l", _store(tmp_path))


# --- family-prefix deflation (DEVQ-015 governing rule) ----------------------

@pytest.mark.parametrize(
    "prefix,full,expected",
    [
        ("smc.fvg", "smc.fvg.screen.s4", True),   # dotted segment
        ("smc.fvg", "smc.fvg", True),             # exact
        ("smc.fvg", "smc.fvg/anything", True),    # slashed segment
        ("smc.fvg", "smc.fvghost", False),        # not on a separator boundary
        ("smc.order_block", "smc.fvg.screen.s4", False),  # different family
    ],
)
def test_prefix_segment_boundary(prefix, full, expected):
    assert _is_prefix_segment(prefix, full) is expected


def test_family_captures_legacy_lineage_without_rekeying(tmp_path):
    """The existing v1 record (lineage=smc.fvg.screen.s4, no family) is captured."""
    store = _store(tmp_path)
    # Legacy record: lineage-keyed, no family field (v1), scoped to a window id.
    TrialCountLedger(store).bump("some_window_id", "smc.fvg.screen.s4", 500, "screener")
    assert family_trials("xauusd_h1/smc.fvg", store) == 500
    d = deflate_family(0.05, "xauusd_h1/smc.fvg", store)
    assert d.effective_alpha == pytest.approx(1e-4)  # 0.05 / 500
    assert d.family == "xauusd_h1/smc.fvg" and d.method == METHOD


def test_family_matches_declared_family_and_isolates(tmp_path):
    store = _store(tmp_path)
    ledger = TrialCountLedger(store)
    ledger.bump("w", "smc.fvg.screen.s5", 10, "screener", family="xauusd_h1/smc.fvg")
    ledger.bump("w", "smc.order_block.s5", 7, "screener", family="xauusd_h1/smc.order_block")
    ledger.bump("w", "smc.fvg.legacy", 3, "screener")  # legacy, no family -> prefix
    # FVG family totals its declared bump + the legacy prefix match, NOT the OB one.
    assert family_trials("xauusd_h1/smc.fvg", store) == 13
    assert family_trials("xauusd_h1/smc.order_block", store) == 7


def test_family_empty_refused(tmp_path):
    with pytest.raises(SchemaViolation):
        deflate_family(0.05, "  ", _store(tmp_path))
