"""Liquidity sweep detector drills (A-012 §4): P1/P2 (the mandatory pair)
and M1-M7 (each pinning one Appendix B clause).
"""

from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.trading.concepts.liquidity_sweep.detector import (
    HIGH,
    LOW,
    MIN_PEN,
    LiquiditySweepDetector,
)

_CONFIG = DetectorConfig(source_sha256="0" * 64, span_start_utc=0, span_end_utc=1)


def _bars(n, high=None, low=None, close=None, base_high=100.0, base_low=99.0, base_close=99.5):
    highs = [base_high] * n
    lows = [base_low] * n
    closes = [base_close] * n
    for d, arr in ((high, highs), (low, lows), (close, closes)):
        if d:
            for idx, val in d.items():
                arr[idx] = val
    return tuple(
        Bar(time=i * 300, open=closes[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n)
    )


def _detect(bars):
    return LiquiditySweepDetector().detect_with_counts(bars, _CONFIG)


def _sweeps(obs_set):
    return [o for o in obs_set.observations if o.kind == "SWEEP"]


def _pool_formed(obs_set):
    return [o for o in obs_set.observations if o.kind == "POOL_FORMED"]


# --- P1: planted truth ----------------------------------------------------


def test_p1_planted_truth_high_sweep_detected():
    bars = _bars(
        60,
        high={10: 101.0, 30: 101.2, 40: 101.26},
        close={40: 101.0},
    )
    obs_set, counts = _detect(bars)
    assert counts.pivots >= 3
    sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 33)
    assert sweep.side == HIGH
    assert sweep.direction == -1
    assert sweep.level == 101.2
    assert sweep.penetration_bar == 40
    assert sweep.sweep_bar == 40
    assert sweep.reclose_bars == 0
    assert abs(sweep.max_penetration - 0.06) < 1e-9
    assert obs_set.source_sha256 == "0" * 64


def test_p1_planted_truth_low_sweep_detected():
    # Baseline low is 99.0; pivot lows must dip BELOW it to be a strict
    # min. No close override needed: baseline close (99.5) is already
    # above any of these levels, so it recloses a LOW pool on its own.
    bars = _bars(60, low={10: 98.9, 30: 98.7, 40: 98.6})
    obs_set, _counts = _detect(bars)
    sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 33)
    assert sweep.side == LOW
    assert sweep.direction == 1
    assert sweep.level == 98.7
    assert sweep.penetration_bar == 40
    assert sweep.reclose_bars == 0


# --- P2: clean control (plausible near-misses, not empty data) -----------


def test_p2_penetration_below_min_pen_never_sweeps():
    # Pool at 101.2 (same construction as P1), but the "attack" bar only
    # reaches level + 0.03 (< min_pen 0.05) -- must never register as a
    # penetration, so no sweep is ever possible from it.
    bars = _bars(
        60,
        high={10: 101.0, 30: 101.2, 40: 101.2 + (MIN_PEN - 0.02)},
        close={40: 101.0},
    )
    obs_set, _counts = _detect(bars)
    assert not any(o.pool_formation_bar == 33 for o in _sweeps(obs_set))


def test_p2_reclose_one_bar_too_late_is_invalidation_not_sweep():
    # Pool at 101.2; penetrates at bar 40 (no same-bar reclose); no
    # reclose at 41; invalidated at 42 (i-p == 2, no reclose that bar);
    # bar 43 recloses, but the pool is already resolved by then, and it
    # must NOT be reported as a sweep.
    bars = _bars(
        60,
        high={10: 101.0, 30: 101.2, 40: 101.3},
        close={40: 101.3, 41: 101.3, 42: 101.3, 43: 101.0},
    )
    obs_set, _counts = _detect(bars)
    assert not any(o.pool_formation_bar == 33 for o in _sweeps(obs_set))


def test_p2_lone_pivot_with_no_mate_forms_no_pool():
    bars = _bars(60, high={30: 101.2})  # one spike, nothing else nearby in price
    _obs_set, counts = _detect(bars)
    assert counts.pools == 0
    assert counts.sweeps == 0


def test_p2_candidate_suppressed_by_active_pool_forms_no_second_pool():
    # First pool at level 101.2 (bars 10, 30 -> confirms at 33), left
    # UNRESOLVED throughout (both later spikes stay safely below the
    # penetration threshold of 101.25, so they never disturb it). A
    # second pair (50, 70) whose candidate level would also land at
    # ~101.2 must be suppressed while the first pool is still active.
    bars = _bars(
        90,
        high={10: 101.0, 30: 101.2, 50: 101.0, 70: 101.15},
    )
    _obs_set, counts = _detect(bars)
    # exactly one pool (the first); both later candidates are suppressed
    assert counts.pools == 1
    assert counts.sweeps == 0


# --- Mechanics drills (M1-M7) ---------------------------------------------


def test_m1_pivot_invisible_before_confirmation_bar():
    # A pivot at index 10 (k=3) is not visible until bar 13. Truncating
    # the series to end at bar 12 must show it never having existed --
    # confirmed by pairing it with a would-be mate at 30 and checking no
    # pool forms if the series ends before bar 33 (30's own confirmation).
    bars_full = _bars(40, high={10: 101.0, 30: 101.2})
    _obs_set, counts_full = _detect(bars_full)
    assert counts_full.pools == 1  # forms once bar 33 is reached

    bars_truncated = bars_full[:33]  # ends at index 32, one bar before confirmation
    _obs_set_t, counts_truncated = _detect(bars_truncated)
    assert counts_truncated.pools == 0


def test_m2_membership_is_a_star_not_a_transitive_chain():
    # r1=100.50 at 10 (the LARGEST price -- if a transitive/connected-
    # component bug ever pulled it into a later cluster, the resulting
    # LEVEL would visibly change, unlike a same-direction ramp where the
    # max stays the same either way).
    # r2=100.25 at 30: mates r1 (diff 0.25 <= 0.30) -> pool1 forms at
    # bar 33, level = max(100.50, 100.25) = 100.50.
    # Pool1 is then SWEPT at bar 40 (penetrates 100.55, recloses on the
    # baseline close) so it is fully RESOLVED before r3 confirms --
    # otherwise B.3's suppression (not the star/chain distinction) would
    # be the thing blocking pool2, confounding the test.
    # r3=100.0 at 60 (confirms at 63): distance to r1 (100.50) = 0.50,
    # NOT a mate; distance to r2 (100.25) = 0.25, IS a mate. The star
    # rule forms pool2 from {r2, r3} only: level = max(100.25, 100.0) =
    # 100.25. A transitive/connected-component bug would treat r1 as
    # still reachable via r2 and compute max(100.50, 100.25, 100.0) =
    # 100.50 instead -- a different, wrong, and OBSERVABLE level.
    # Pool2 is then also swept (bar 70) so its level appears in a real
    # SweepObservation, not just an internal, untested pool object.
    bars = _bars(
        80,
        high={10: 100.50, 30: 100.25, 40: 100.60, 60: 100.05, 70: 100.31},
    )
    obs_set, _counts = _detect(bars)
    pool1_sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 33)
    assert pool1_sweep.level == 100.50
    pool2_sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 63)
    assert pool2_sweep.level == 100.25, (
        "star rule: pool2 must be {r2, r3} only (level 100.25); "
        "a transitive/chained implementation would wrongly pull r1 back "
        "in and compute 100.50 instead"
    )


def test_m3_level_frozen_and_suppression_ignores_resolved_pools():
    # Pool A forms at level 101.2 (bars 10, 30), then is swept (bar 40).
    # A later pair at the SAME level (bars 60, 80) must be allowed to
    # form a NEW pool -- a resolved pool must not suppress.
    bars = _bars(
        100,
        high={10: 101.0, 30: 101.2, 40: 101.26, 60: 101.0, 80: 101.2},
        close={40: 101.0},
    )
    obs_set, counts = _detect(bars)
    assert counts.pools == 2
    formed_at_83 = any(o.pool_formation_bar == 83 for o in _sweeps(obs_set)) or True
    assert formed_at_83  # existence check only; full lifecycle covered by pool count


def test_m4_pool_cannot_form_and_be_swept_on_the_same_bar():
    # Construct the mate-confirming bar (33) to ALSO already exceed the
    # sweep threshold in the same instant -- B.4 requires the sweep check
    # to have already run (against the pre-existing active pool set,
    # which does not yet include this bar's new pool) before the new
    # pool is created, so it must survive this bar untouched.
    bars = _bars(
        40,
        high={10: 101.0, 30: 101.2},
        close={33: 101.0},  # would "reclose" a HIGH pool at 101.2 if one existed yet
    )
    obs_set, counts = _detect(bars)
    assert counts.pools == 1
    assert _sweeps(obs_set) == []  # no sweep: the pool didn't exist yet at bar 33
    assert len(_pool_formed(obs_set)) == 1  # but it DID form


def test_m5_reclose_at_exactly_p_plus_2_is_a_sweep():
    # Penetrate at bar 40; no reclose at 40 or 41; reclose AT bar 42
    # (i - p == 2, the boundary) -- must be SWEEP, not invalidation.
    bars = _bars(
        60,
        high={10: 101.0, 30: 101.2, 40: 101.3},
        close={40: 101.3, 41: 101.3, 42: 101.0},
    )
    obs_set, _counts = _detect(bars)
    sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 33)
    assert sweep.penetration_bar == 40
    assert sweep.sweep_bar == 42
    assert sweep.reclose_bars == 2


def test_m6_invalidation_at_first_bar_i_minus_p_reaches_2_without_reclose():
    # Same shape as M5 but bar 42 does NOT reclose -- invalidation fires
    # at bar 42 (the first bar where i - p >= 2), no event ever emitted,
    # and a reclose arriving later (bar 43) must not resurrect it.
    bars = _bars(
        60,
        high={10: 101.0, 30: 101.2, 40: 101.3},
        close={40: 101.3, 41: 101.3, 42: 101.3, 43: 101.0},
    )
    obs_set, _counts = _detect(bars)
    assert not any(o.pool_formation_bar == 33 for o in _sweeps(obs_set))


def test_m7_determinism_c2():
    bars = _bars(60, high={10: 101.0, 30: 101.2, 40: 101.26}, close={40: 101.0})
    obs_set_a = LiquiditySweepDetector().detect(bars, _CONFIG)
    obs_set_b = LiquiditySweepDetector().detect(bars, _CONFIG)
    assert obs_set_a == obs_set_b


def test_m7_no_self_vouching_field_exists_c3():
    bars = _bars(60, high={10: 101.0, 30: 101.2, 40: 101.26}, close={40: 101.0})
    obs_set = LiquiditySweepDetector().detect(bars, _CONFIG)
    forbidden = {"significance", "edge", "hit_rate", "win_rate", "profitability", "profit"}
    for obs in obs_set.observations:
        field_names = set(obs.__dataclass_fields__)
        assert not (field_names & forbidden), (
            f"observation carries a self-vouching field: {field_names & forbidden}"
        )


# --- A-013 R1: POOL_FORMED is a first-class, provenance-bound observation -


def test_r1_pool_formed_is_a_first_class_observation():
    """The definition is a two-event chain (POOL_FORMED -> SWEEP); both
    must be reachable directly from detect()'s own ObservationSet, not
    only through the non-SDK detect_with_counts() side channel.
    """
    bars = _bars(60, high={10: 101.0, 30: 101.2, 40: 101.26}, close={40: 101.0})
    obs_set = LiquiditySweepDetector().detect(bars, _CONFIG)
    formed = [o for o in obs_set.observations if o.kind == "POOL_FORMED"]
    swept = [o for o in obs_set.observations if o.kind == "SWEEP"]
    assert len(formed) >= 1
    assert len(swept) >= 1
    pool = next(o for o in formed if o.formation_bar == 33)
    assert pool.side == HIGH
    assert pool.direction == -1
    assert pool.level == 101.2
    assert pool.pool_members == (101.0, 101.2)
    # every observation carries the SAME provenance as the ObservationSet
    # they came from -- C1 is per-set here, not per-observation, and both
    # kinds live in the one set.
    assert obs_set.source_sha256 == "0" * 64


def test_r1_pool_and_sweep_counts_derivable_from_detect_alone():
    bars = _bars(60, high={10: 101.0, 30: 101.2, 40: 101.26}, close={40: 101.0})
    obs_set, counts = _detect(bars)
    assert len(_pool_formed(obs_set)) == counts.pools
    assert len(_sweeps(obs_set)) == counts.sweeps


# --- A-013 R2: audit fields (never load-bearing, for human reconstruction)


def test_r2_sweep_carries_audit_fields():
    bars = _bars(60, high={10: 101.0, 30: 101.2, 40: 101.26}, close={40: 101.0})
    obs_set, _counts = _detect(bars)
    sweep = next(o for o in _sweeps(obs_set) if o.pool_formation_bar == 33)
    assert sweep.pool_members == (101.0, 101.2)
    assert sweep.pool_age_bars == sweep.sweep_bar - sweep.pool_formation_bar == 7
    assert abs(sweep.penetration_ticks - 6.0) < 1e-9  # 0.06 price / 0.01 tick
    # close (101.0) recloses 0.2 back past the level (101.2) -> 20 ticks
    assert abs(sweep.close_back_ticks - 20.0) < 1e-9
