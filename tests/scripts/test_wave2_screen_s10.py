"""ARCH-010 §3 — Exploration Wave 2 reserve-safety (the slice that never leaks).

The screener does NOT slice bars to a window; this wave slices to the
2025-TRAINING interval FIRST so a near-boundary exit can never read a reserve
bar. These tests pin that property on a SYNTHETIC feed (own tmp journal + bulk):
the training slice is exactly ``ts_start <= ts < ts_end``, ends strictly before
the VIRGIN start, and the guard raises if a (mis-designated) training window
overlaps the reserve. scripts/ is not a package, so the tool logic is loaded from
file — the single source of truth for the CLI and these tests alike.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pyarrow as pa
import pytest

from qrf.kernel.protocol.windows import WindowLedger
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def wave():
    return _load("wave2_screen_s10")


def _feed_table(ts_start=0, n=100, step=3600 * 10**9):
    ts = np.array([ts_start + i * step for i in range(n)], dtype=np.int64)
    close = 2000.0 + np.arange(n, dtype=float)
    return pa.table(
        {"ts": ts, "open": close, "high": close + 1.0, "low": close - 1.0, "close": close}
    ), ts, step


def _setup(tmp_path, *, train_end_step, virgin_start_step):
    """A synthetic primary feed with a TRAINING and a VIRGIN window designated."""
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    table, ts, step = _feed_table()
    m = bulk.write("primary", table, producer="synthetic", parents=[])
    tr = WindowLedger(store).designate(
        "primary", int(ts[0]), int(ts[train_end_step]), "TRAINING", parents=[m.record_id]
    )
    vg = WindowLedger(store).designate(
        "primary", int(ts[virgin_start_step]), int(ts[-1]) + 1, "VIRGIN", parents=[m.record_id]
    )
    return store, bulk, m.record_id, tr.record_id, vg.record_id, ts


def test_training_slice_excludes_reserve(wave, tmp_path):
    # TRAINING = bars[0:50); VIRGIN = bars[50:100). The slice must be exactly [0,50).
    store, bulk, pm, tw, vw, ts = _setup(tmp_path, train_end_step=50, virgin_start_step=50)
    sl = wave._training_slice(
        store, bulk, primary_manifest=pm, train_window=tw, virgin_window=vw
    ).to_pandas()
    assert len(sl) == 50
    virgin_start = int(ts[50])
    assert sl["ts"].max() < virgin_start          # ends before the reserve
    assert (sl["ts"] < virgin_start).all()        # no reserve bar leaked in
    assert sl["ts"].min() == int(ts[0])


def test_training_slice_guard_refuses_overlap_into_reserve(wave, tmp_path):
    # A mis-designated TRAINING window whose ts_end runs PAST the VIRGIN start must
    # trip the reserve guard rather than silently screen reserve bars.
    store, bulk, pm, tw, vw, ts = _setup(tmp_path, train_end_step=70, virgin_start_step=50)
    with pytest.raises(AssertionError):
        wave._training_slice(
            store, bulk, primary_manifest=pm, train_window=tw, virgin_window=vw
        )


def test_grid_is_the_unchanged_500_variant_s4_suite(wave):
    from qrf.trading.simulator.screener_vbt import grid_variants

    assert len(grid_variants(wave.GRID)) == 500
    assert wave.FAMILY == "xauusd_h1/smc.fvg"
    assert wave.LINEAGE == "smc.fvg.screen.s10.wave2"
