"""Schema tests for the Sprint-6 record types: hypothesis / verdict (ARCH-006).

Accept a valid payload; reject missing/unknown fields, bad enums and wrong types.
These validate through the same ``schemas.validate`` path production appends use.
"""

from __future__ import annotations

import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records import schemas


def _ok(rt, payload):
    schemas.validate(rt, payload, 1)


_HYP = {
    "lineage": "h001",
    "scope": "xauusd_h1",
    "instrument_refs": ["01ABC"],
    "setup_dsl": {"event": "smc.fvg"},
    "execution": {
        "hold_bars": 4, "size": 1.0, "strength_min": 0.0,
        "stop_offset": None, "target_offset": None,
    },
    "cost_model_ref": "xauusd_retail_median",
    "split_spec": {"n_folds": 4, "embargo_bars": 8},
    "thresholds": {"min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
}


def test_hypothesis_valid_and_rejections():
    _ok("hypothesis", _HYP)
    with pytest.raises(SchemaViolation):  # empty instrument_refs
        _ok("hypothesis", {**_HYP, "instrument_refs": []})
    with pytest.raises(SchemaViolation):  # unknown field
        _ok("hypothesis", {**_HYP, "extra": 1})
    with pytest.raises(SchemaViolation):  # hold_bars < 1
        _ok("hypothesis", {**_HYP, "execution": {**_HYP["execution"], "hold_bars": 0}})
    with pytest.raises(SchemaViolation):  # base_alpha out of range
        _ok("hypothesis", {**_HYP, "thresholds": {**_HYP["thresholds"], "base_alpha": 1.5}})
    with pytest.raises(SchemaViolation):  # correction missing method
        bad = {"min_n": 100, "base_alpha": 0.05, "correction": {}}
        _ok("hypothesis", {**_HYP, "thresholds": bad})
    with pytest.raises(SchemaViolation):  # size <= 0
        _ok("hypothesis", {**_HYP, "execution": {**_HYP["execution"], "size": 0.0}})


_VERDICT = {
    "hypothesis_ref": "01H",
    "window_ref": "01W",
    "verdict": "FAIL",
    "n_trades": 120,
    "n_dropped_tail": 3,
    "gross": {"total": 1.0, "mean": 0.01},
    "net": {"total": -0.5, "mean": -0.004},
    "statistics": {"t_one_sided": {"stat": -0.4, "p": 0.66, "ci_low": -0.1, "ci_high": 0.05}},
    "folds": [
        {"index": 1, "n_trades": 60, "mean_net": -0.004, "test_start": 0, "test_end": 100},
        {"index": 2, "n_trades": 60, "mean_net": None, "test_start": 100, "test_end": 200},
    ],
    "corrections": {
        "family_m": 500, "method": "bonferroni", "base_alpha": 0.05, "effective_alpha": 1e-4,
    },
    "thresholds": {"min_n": 100, "base_alpha": 0.05, "correction": {"method": "bonferroni"}},
    "seed": 12345,
    "selftest_seed": 20260725,
    "engine_version": "engine.s5.1",
    "trades_manifest": "01T",
}


def test_verdict_valid_and_rejections():
    _ok("verdict", _VERDICT)
    # null stats allowed (INSUFFICIENT with too few trades to test).
    null_stat = {"t_one_sided": {"stat": None, "p": None, "ci_low": None, "ci_high": None}}
    _ok("verdict", {**_VERDICT, "statistics": null_stat})
    with pytest.raises(SchemaViolation):  # bad verdict enum
        _ok("verdict", {**_VERDICT, "verdict": "MAYBE"})
    with pytest.raises(SchemaViolation):  # unknown field
        _ok("verdict", {**_VERDICT, "extra": 1})
    with pytest.raises(SchemaViolation):  # missing correction field
        _ok("verdict", {**_VERDICT, "corrections": {"family_m": 1, "method": "bonferroni"}})
    with pytest.raises(SchemaViolation):  # negative n_trades
        _ok("verdict", {**_VERDICT, "n_trades": -1})
    with pytest.raises(SchemaViolation):  # thresholds not as-registered shape
        _ok("verdict", {**_VERDICT, "thresholds": {"min_n": 100}})
