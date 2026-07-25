"""Battery selftest tests (ARCH-005 §4, Blueprint §4.7 step 3).

Covers: the tri-state correct on all three synthetic suites when wired to the REAL
engine (PASS / FAIL / INSUFFICIENT), determinism (same seed → same data and same
report), the classifier unit behaviour, the no-verdict AST audit (the module
cannot write a verdict, mirroring the screener), and the VIRGIN guard.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

from qrf.kernel.battery import selftest as selftest_mod
from qrf.kernel.battery.selftest import (
    FAIL,
    INSUFFICIENT,
    PASS,
    build_suites,
    classify,
    run_selftest,
)
from qrf.trading.simulator.engine import EventEngine, ExecutionSpec
from qrf.trading.utility.cost_models import CostModel

# A near-zero cost model so the planted edge (drift 1.0) reads cleanly; costs are
# exercised to the cent elsewhere (test_engine micro-scenario).
_TINY_COST = CostModel(
    name="selftest_tiny", spread=0.001, slippage_per_side=0.0, commission_per_side=0.0
)


def _engine_runner(bars: pd.DataFrame, events: pd.DataFrame, hold_bars: int):
    """Wire the real audited engine as the injected selftest runner → net outcomes."""
    trades = EventEngine().simulate(
        bars, events, _TINY_COST, seed=1, execution=ExecutionSpec(hold_bars=hold_bars)
    )
    return [t.net_pnl for t in trades.trades]


# --- tri-state on all three suites, wired to the real engine -----------------
def test_tri_state_correct_on_all_suites():
    report = run_selftest(_engine_runner, seed=2026)
    by_name = {r.name: r for r in report.results}
    assert by_name["planted_edge"].classification == PASS
    assert by_name["pure_noise"].classification == FAIL
    assert by_name["small_n"].classification == INSUFFICIENT
    assert report.passed


def test_planted_edge_is_decisive():
    report = run_selftest(_engine_runner, seed=99)
    edge = next(r for r in report.results if r.name == "planted_edge")
    assert edge.mean > 0.5  # drift 1.0 minus a whisker of cost
    assert edge.p_value < 1e-3  # comfortably significant
    assert edge.n_trades == 60


def test_small_n_is_insufficient_regardless_of_edge():
    report = run_selftest(_engine_runner, seed=99)
    small = next(r for r in report.results if r.name == "small_n")
    assert small.n_trades == 8
    assert small.classification == INSUFFICIENT


# --- determinism -------------------------------------------------------------
def test_same_seed_same_data():
    a = build_suites(1234)
    b = build_suites(1234)
    for sa, sb in zip(a, b, strict=True):
        pd.testing.assert_frame_equal(sa.bars, sb.bars)
        pd.testing.assert_frame_equal(sa.events, sb.events)


def test_different_seed_different_data():
    a = build_suites(1)[0].bars["open"].to_numpy()
    b = build_suites(2)[0].bars["open"].to_numpy()
    assert not np.array_equal(a, b)


def test_same_seed_same_report():
    r1 = run_selftest(_engine_runner, seed=7)
    r2 = run_selftest(_engine_runner, seed=7)
    assert [(x.name, x.classification, round(x.mean, 9)) for x in r1.results] == [
        (x.name, x.classification, round(x.mean, 9)) for x in r2.results
    ]


# --- classifier unit ---------------------------------------------------------
def test_classify_insufficient_below_min_n():
    assert classify([1.0] * 29, seed=0).classification == INSUFFICIENT


def test_classify_pass_on_strong_positive():
    rng = np.random.default_rng(0)
    x = 1.0 + rng.normal(0, 1, 100)
    assert classify(x, seed=0).classification == PASS


def test_classify_fail_on_noise():
    rng = np.random.default_rng(0)
    x = rng.normal(0, 1, 100)  # zero-mean
    assert classify(x, seed=0).classification == FAIL


def test_classify_fail_on_negative():
    assert classify([-1.0] * 60, seed=0).classification == FAIL


# --- the no-verdict AST audit (mirrors the screener) -------------------------
def _forbidden_calls(source: str) -> list[str]:
    tree = ast.parse(source)
    bad: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr == "append" and node.args:
                first = node.args[0]
                forbidden = ("verdict", "window_burn", "belief_update")
                if isinstance(first, ast.Constant) and first.value in forbidden:
                    bad.append(f"append({first.value!r}) at line {node.lineno}")
            if func.attr == "burn":
                bad.append(f".burn() at line {node.lineno}")
    return bad


def test_selftest_module_cannot_write_verdict_or_burn():
    src = Path(selftest_mod.__file__).read_text(encoding="utf-8")
    assert _forbidden_calls(src) == []


def test_audit_scanner_catches_planted_violations():
    planted = "def f(s):\n    s.append('verdict', {})\n    s.burn('w','l','v')\n"
    found = _forbidden_calls(planted)
    assert any("verdict" in v for v in found) and any("burn()" in v for v in found)


# --- VIRGIN / journal reachability guard -------------------------------------
def test_selftest_touches_no_journal_or_virgin():
    src = Path(selftest_mod.__file__).read_text(encoding="utf-8")
    assert "VIRGIN" not in src
    assert "RecordStore" not in src and "WindowLedger" not in src
    # run_selftest takes only a runner + seed — no store, no window ref.
    import inspect

    params = set(inspect.signature(run_selftest).parameters)
    assert {"store", "window", "window_ref"}.isdisjoint(params)
