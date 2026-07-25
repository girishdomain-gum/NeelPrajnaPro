"""PlaceboBattery — the G-3 placebo run (ARCH-008 §1).

Acceptance: on a real edge, >=20 seeded null runs PASS at most ~alpha (here 0,
deterministically); the placebo writes NO verdict and burns NO window (the window
is still judgeable afterwards); the placebo_run record is shape- and
count-consistent and reproducible from its seed. The null makers are unit-tested
for what they preserve vs destroy. All in a scratch datastore.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from qrf.kernel.battery.battery import EvidenceBattery
from qrf.kernel.battery.placebo import (
    DIRECTION_PERMUTATION,
    PlaceboBattery,
    _direction_permutation,
    _entry_time_shuffle,
)
from qrf.kernel.errors import SchemaViolation
from qrf.trading.simulator.engine import EventEngine
from tests.battery.test_battery import (
    _BASE_TS,
    ZERO_COST,
    _designate,
    _hypothesis,
    _scratch,
)


def _planted_directional(*, n_events: int, drift: float, hold: int = 1):
    """Episodic bars whose move ALIGNS with each event's direction.

    Directions are balanced +/-1. For event k the exit move is ``direction[k] *
    drift``, so a trade in the event's own direction realises ``+drift`` every time
    (real edge). Permuting the directions breaks that alignment: a mismatched
    direction realises ``-drift``, so a balanced permutation drives the mean to ~0.
    """
    L = hold + 2
    n_bars = n_events * L
    ts = _BASE_TS + np.arange(n_bars, dtype=np.int64)
    opens = np.full(n_bars, 100.0, dtype=np.float64)
    directions = np.where(np.arange(n_events) % 2 == 0, 1, -1).astype(np.int64)
    ev_ts = []
    for k in range(n_events):
        e0 = k * L
        opens[e0 + 1 + hold] = 100.0 + directions[k] * drift  # move aligns with direction
        ev_ts.append(int(ts[e0]))
    bars = pd.DataFrame({"ts": ts, "open": opens, "high": opens, "low": opens, "close": opens})
    events = pd.DataFrame(
        {
            "ts": np.array(ev_ts, dtype=np.int64),
            "direction": directions,
            "strength": np.ones(n_events, dtype=np.float64),
        }
    )
    return bars, events


# --- null makers (unit) ------------------------------------------------------

def test_direction_permutation_preserves_all_but_direction():
    bars, events = _planted_directional(n_events=50, drift=5.0)
    out = _direction_permutation(events, bars, seed=1)
    assert list(out["ts"]) == list(events["ts"])  # timing untouched
    assert sorted(out["direction"]) == sorted(events["direction"])  # a permutation
    assert out["direction"].sum() == events["direction"].sum()  # marginal mix preserved
    # Reproducible by seed; different seed generally differs.
    assert list(_direction_permutation(events, bars, seed=1)["direction"]) == list(out["direction"])


def test_entry_time_shuffle_preserves_direction_moves_ts_within_bars():
    bars, events = _planted_directional(n_events=50, drift=5.0)
    out = _entry_time_shuffle(events, bars, seed=3)
    assert len(out) == len(events)
    assert list(out["direction"]) == list(events["direction"])  # direction untouched
    bar_ts = set(bars["ts"].tolist())
    assert set(out["ts"]).issubset(bar_ts)  # entries land on real bars
    assert out["ts"].is_unique  # distinct bars
    # Reproducible by seed.
    assert list(_entry_time_shuffle(events, bars, seed=3)["ts"]) == list(out["ts"])


# --- placebo integration -----------------------------------------------------

def test_placebo_zero_passes_on_real_edge_under_deflation(tmp_path):
    """AC: a strong real edge under a deflated alpha (H-001's condition — its 502-trial
    family drives effective alpha ~1e-4); >=20 direction-null runs PASS ~0 times."""
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=240, drift=10.0)
    window = _designate(store, bars)
    # A large family burden deflates alpha to ~1e-4, mirroring the FVG family's 502
    # trials — so a null twin PASSes essentially never (a healthy judge).
    from qrf.kernel.corrections.trials import TrialCountLedger
    TrialCountLedger(store).bump(
        "synthetic", "synthetic.planted", 500, "screener", family="synthetic/planted"
    )
    hyp = _hypothesis(store, window, min_n=100, family="synthetic/planted")

    # Sanity: the real setup still PASSes (a zero-variance +10 edge; p=0 < any alpha).
    real = EvidenceBattery(store, bulk).evaluate(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert real.verdict == "PASS"

    rec = PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=DIRECTION_PERMUTATION, base_seed=20260725, n_runs=20,
    )
    p = rec.payload
    assert p["n_runs"] == 20 and len(p["outcomes"]) == 20
    assert p["n_pass"] == 0  # under 1e-4 alpha, the null PASSes ~0 times (report exact)
    assert p["method"] == DIRECTION_PERMUTATION
    assert rec.parents == (hyp,)


def test_placebo_null_pass_rate_near_alpha_without_deflation(tmp_path):
    """Without deflation (alpha=0.05), a TRUE null PASSes at ~alpha — the placebo's
    calibration: a healthy judge's null pass rate is alpha, not zero. Here ~1/20."""
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family="synthetic/planted")
    rec = PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=DIRECTION_PERMUTATION, base_seed=20260725, n_runs=20,
    )
    # At alpha=0.05 the expected null passes is ~1; assert it is small (<= 3), not that
    # it is zero — a zero would suggest the null is not a true null.
    assert rec.payload["n_pass"] <= 3


def test_placebo_writes_no_verdict_and_leaves_window_judgeable(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family="synthetic/planted")

    PlaceboBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
        method=DIRECTION_PERMUTATION, base_seed=1, n_runs=20,
    )
    # No verdict, no burn — the placebo consumed nothing.
    assert not list(store.query(record_type="verdict"))
    assert not list(store.query(record_type="window_burn"))
    # The window is still judgeable: a real verdict now succeeds and burns it.
    verdict = EvidenceBattery(store, bulk).run(
        hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events
    )
    assert verdict.payload["verdict"] == "PASS"
    assert len(list(store.query(record_type="window_burn"))) == 1


def test_placebo_reproducible_from_seed(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=240, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family="synthetic/planted")
    pb = PlaceboBattery(store, bulk)
    a = pb.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
               method=DIRECTION_PERMUTATION, base_seed=99, n_runs=20)
    b = pb.run(hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
               method=DIRECTION_PERMUTATION, base_seed=99, n_runs=20)
    assert a.payload["outcomes"] == b.payload["outcomes"]  # same seed -> same null draw


def test_placebo_rejects_unknown_method(tmp_path):
    store, bulk = _scratch(tmp_path)
    bars, events = _planted_directional(n_events=20, drift=10.0)
    window = _designate(store, bars)
    hyp = _hypothesis(store, window, min_n=100, family="synthetic/planted")
    with pytest.raises(SchemaViolation):
        PlaceboBattery(store, bulk).run(
            hyp, simulator=EventEngine(), cost_model=ZERO_COST, bars=bars, events=events,
            method="coin_flip", base_seed=1, n_runs=5,
        )
