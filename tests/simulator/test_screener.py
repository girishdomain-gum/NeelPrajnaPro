"""Screener tests (ARCH-004 §1/§2, Blueprint §5 arrow 8).

Covers: exact grid-size == trial_count bump; the type-level no-verdict/no-burn
audit (the screener module cannot append a verdict or a window_burn, nor call
burn); the TRAINING/EXPLORATION-only guard (VIRGIN refused); seeded determinism;
gross-vs-net divergence; and a random-signal grid yielding an empty shortlist.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest

from qrf.kernel.corrections.trials import TrialCountLedger
from qrf.kernel.errors import ContaminationError, SchemaViolation
from qrf.kernel.instruments.base import build_event_frame
from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.simulator import screener_vbt
from qrf.trading.simulator.screener_vbt import Screener, ScreenThresholds, grid_variants

STEP = 3600 * 10**9
TS0 = 1704160800000000000


def _grid_500() -> dict:
    return {
        "hold_bars": list(range(1, 26)),                 # 25
        "strength_min": [round(0.1 * k, 1) for k in range(10)],  # 10
        "side": ["long", "short"],                       # 2  -> 500
    }


def _make_bars(bulk, close: np.ndarray, dataset="bars"):
    n = len(close)
    ts = np.array([TS0 + i * STEP for i in range(n)], dtype=np.int64)
    tbl = pa.table(
        {"ts": ts, "open": close, "high": close + 1.0, "low": close - 1.0, "close": close}
    )
    return bulk.write(dataset, tbl, producer="t", parents=[]), ts


def _make_events(bulk, ts, idxs, direction=1, strength=1.0):
    rows = [
        {
            "ts": int(ts[i]),
            "event_type": "x.y.sig",
            "direction": int(direction),
            "level": 0.0,
            "zone_hi": float("nan"),
            "zone_lo": float("nan"),
            "strength": float(strength),
            "meta": "{}",
        }
        for i in idxs
    ]
    return bulk.write("events", build_event_frame(rows), producer="t", parents=[])


@pytest.fixture
def env(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    return store, bulk


def _uptrend_setup(store, bulk, designation="TRAINING", n=300):
    close = 100.0 + np.cumsum(np.full(n, 0.5))
    bm, ts = _make_bars(bulk, close)
    em = _make_events(bulk, ts, range(0, n, 5), direction=1)
    w = WindowLedger(store).designate(
        "bars", int(ts[0]), int(ts[-1]) + 1, designation, parents=[bm.record_id]
    )
    return bm, em, w, ts


# --- grid expansion + exact trial_count --------------------------------------
def test_grid_variants_exact_product():
    assert len(grid_variants(_grid_500())) == 500


def test_grid_keys_must_match():
    with pytest.raises(SchemaViolation):
        grid_variants({"hold_bars": [1], "strength_min": [0.0]})  # missing 'side'


def test_grid_size_equals_trial_count_bump(env):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk)
    sc = Screener(store, bulk)
    note = sc.run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
    )
    decl = json.loads(note.payload["text"])
    assert decl["grid_size"] == 500
    assert decl["trial_count_n"] == 500
    # The ledger reflects exactly the grid size — one bump, no netting.
    assert TrialCountLedger(store).total(w.record_id, "fam.test") == 500
    counts = list(store.query(record_type="trial_count"))
    assert len(counts) == 1 and counts[0].payload["n_attempts"] == 500


def test_shortlist_impossible_without_trial_count(env):
    # There is exactly one shortlist note and exactly one trial_count, both from
    # the single run() code path — a shortlist can never exist without its bump.
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk)
    Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
    )
    notes = [
        n for n in store.query(record_type="note")
        if json.loads(n.payload["text"]).get("kind") == "screener_shortlist"
    ]
    assert len(notes) == len(list(store.query(record_type="trial_count"))) == 1


# --- TRAINING/EXPLORATION-only guard -----------------------------------------
def test_virgin_window_refused(env):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk, designation="VIRGIN")
    with pytest.raises(ContaminationError):
        Screener(store, bulk).run(
            dataset_manifest_refs=[bm.record_id],
            eventframe_manifest_ref=em.record_id,
            grid=_grid_500(),
            cost_model_name="xauusd_retail_median",
            window_ref=w.record_id,
            lineage="fam.test",
        )
    # Refusal is total: no shortlist, no trial_count leaked before the guard.
    assert list(store.query(record_type="trial_count")) == []
    assert not [
        n for n in store.query(record_type="note")
        if json.loads(n.payload["text"]).get("kind") == "screener_shortlist"
    ]


def test_exploration_window_allowed(env):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk, designation="EXPLORATION")
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
    )
    assert json.loads(note.payload["text"])["window_designation"] == "EXPLORATION"


# --- seeded determinism ------------------------------------------------------
def test_determinism_same_inputs_same_ranking(env, tmp_path):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk)
    sc = Screener(store, bulk)
    kw = dict(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
        seed=7,
    )
    n1 = sc.run(**kw)
    n2 = sc.run(**kw)
    d1, d2 = json.loads(n1.payload["text"]), json.loads(n2.payload["text"])
    # The ranked artifact content is identical across runs (order + metrics).
    m1 = bulk.read(d1["shortlist_manifest_ref"]).to_pandas().drop(columns=["ts"])
    m2 = bulk.read(d2["shortlist_manifest_ref"]).to_pandas().drop(columns=["ts"])
    assert m1.equals(m2)
    assert d1["top"] == d2["top"]


# --- gross vs net differ (AC) ------------------------------------------------
def test_gross_and_net_metrics_differ(env):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk)
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
    )
    decl = json.loads(note.payload["text"])
    ranking = bulk.read(decl["shortlist_manifest_ref"]).to_pandas()
    traded = ranking[ranking["n_trades"] > 0]
    assert len(traded) > 0
    # Costs are a strict drag: net_total < gross_total wherever trades happened.
    assert (traded["net_total"] < traded["gross_total"]).all()


# --- random-signal grid -> empty shortlist (AC) ------------------------------
def test_random_signal_grid_yields_empty_shortlist(env):
    store, bulk = env
    rng = np.random.default_rng(20260725)
    n = 600
    # A driftless random walk — no edge.
    close = 2000.0 + np.cumsum(rng.normal(0.0, 1.0, n))
    bm, ts = _make_bars(bulk, close)
    # Random long signals scattered through the series.
    sig_idx = np.flatnonzero(rng.random(n) < 0.15)
    em = _make_events(bulk, ts, sig_idx, direction=1)
    w = WindowLedger(store).designate(
        "bars", int(ts[0]), int(ts[-1]) + 1, "TRAINING", parents=[bm.record_id]
    )
    note = Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.random",
        thresholds=ScreenThresholds(min_trades=30, min_sharpe=0.10),
    )
    decl = json.loads(note.payload["text"])
    assert decl["n_admitted"] == 0  # no-edge signals, after costs, admit nothing


# --- the type-level no-verdict / no-burn audit -------------------------------
def _screener_source() -> str:
    return Path(screener_vbt.__file__).read_text(encoding="utf-8")


def _forbidden_calls(source: str) -> list[str]:
    """Scan the screener AST for any append('verdict'|'window_burn') or .burn()."""
    tree = ast.parse(source)
    bad: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Attribute):
            if func.attr == "append" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and first.value in ("verdict", "window_burn"):
                    bad.append(f"append({first.value!r}) at line {node.lineno}")
            if func.attr == "burn":
                bad.append(f".burn() at line {node.lineno}")
    return bad


def test_screener_module_cannot_write_verdict_or_burn():
    assert _forbidden_calls(_screener_source()) == []


def test_audit_scanner_catches_planted_violations():
    planted = (
        "def f(store, wl):\n"
        "    store.append('verdict', {})\n"
        "    store.append('window_burn', {})\n"
        "    wl.burn('w', 'l', 'v')\n"
    )
    found = _forbidden_calls(planted)
    assert any("verdict" in v for v in found)
    assert any("window_burn" in v for v in found)
    assert any("burn()" in v for v in found)


def test_no_verdict_or_burn_records_after_run(env):
    store, bulk = env
    bm, em, w, _ = _uptrend_setup(store, bulk)
    Screener(store, bulk).run(
        dataset_manifest_refs=[bm.record_id],
        eventframe_manifest_ref=em.record_id,
        grid=_grid_500(),
        cost_model_name="xauusd_retail_median",
        window_ref=w.record_id,
        lineage="fam.test",
    )
    assert list(store.query(record_type="verdict")) == []
    assert list(store.query(record_type="window_burn")) == []
