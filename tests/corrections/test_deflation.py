"""Deflation — the Bonferroni multiple-testing penalty (ARCH-006 §2, Blueprint §4.8).

The correction must be EXACTLY ``base_alpha / max(1, N_trials)`` with ``N_trials``
read from the real trial ledger for a ``(scope, lineage)`` pair — pinned here
against hand numbers so a drift in the formula cannot pass unnoticed.
"""

from __future__ import annotations

import pytest

from qrf.kernel.corrections.deflation import METHOD, deflate, effective_alpha
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
