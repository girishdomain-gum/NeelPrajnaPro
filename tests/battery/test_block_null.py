"""WO-15 stage B (S6-S7, refs A-020/A-022/A-023) — drill law for
qrf/kernel/battery/block_null.py: N2 must be shown able to DESTROY a
fabricated long-range (>7-bar) event dependence (planted-truth) while
PRESERVING short-range (<=7-bar) volatility clustering intact
(clean-control) — per Gen-1's own certification style, cited in A-022.

Mechanical tests (determinism, shape preservation, calendar honesty) come
first; the two drills follow. All fixtures use synthetic epoch-day-based
timestamps (not real dates) so weekday period-7 arithmetic is exact and
independently checkable.
"""

from __future__ import annotations

import pandas as pd
import pyarrow as pa
import pytest

from qrf.kernel.battery.block_null import (
    BLOCK_BARS,
    empirical_one_sided_p,
    n_local_sweeps,
    resample_bar_blocks,
    run_block_null,
    run_block_null_local,
)
from qrf.kernel.errors import SchemaViolation
from qrf.trading.concepts.neelprajna.detector import LiquiditySweepDetector

_NS_PER_DAY = 86_400_000_000_000


def _flat_day(epoch_day: int, n: int, *, high=100.00, low=99.50, close=100.00) -> pd.DataFrame:
    ts0 = epoch_day * _NS_PER_DAY
    return pd.DataFrame(
        {
            "ts": [ts0 + i * 300_000_000_000 for i in range(n)],
            "open": [close] * n,
            "high": [high] * n,
            "low": [low] * n,
            "close": [close] * n,
        }
    )


# --- mechanical properties ------------------------------------------------
def test_surrogate_preserves_length_and_real_calendar_timeline():
    day = _flat_day(100, 40)
    surrogate = resample_bar_blocks(day, seed=1)
    assert len(surrogate) == len(day)
    assert list(surrogate["ts"]) == list(day["ts"])


def test_same_seed_is_deterministic():
    day = pd.concat([_flat_day(100, 40), _flat_day(107, 40)], ignore_index=True)
    a = resample_bar_blocks(day, seed=42)
    b = resample_bar_blocks(day, seed=42)
    pd.testing.assert_frame_equal(a, b)


def test_different_seeds_usually_differ():
    day = pd.concat([_flat_day(100, 40), _flat_day(107, 40), _flat_day(114, 40)], ignore_index=True)
    # Give each day a distinct marker so different draws are visibly different.
    day.loc[0:6, "high"] = 101.0
    day.loc[40:46, "high"] = 102.0
    day.loc[80:86, "high"] = 103.0
    a = resample_bar_blocks(day, seed=1)
    b = resample_bar_blocks(day, seed=2)
    assert not a["high"].equals(b["high"])


def test_rejects_missing_columns():
    with pytest.raises(SchemaViolation):
        resample_bar_blocks(pd.DataFrame({"ts": [1, 2, 3]}), seed=1)


def test_run_block_null_rejects_bad_params():
    day = _flat_day(100, 40)
    with pytest.raises(SchemaViolation):
        run_block_null(day, LiquiditySweepDetector(), base_seed=1, n_runs=0)
    with pytest.raises(SchemaViolation):
        run_block_null(day, LiquiditySweepDetector(), base_seed=-1, n_runs=5)


def test_block_bars_is_sealed_at_seven():
    # R1-v2 (A-023): 2*PIVOT_K + 1, zero discretion — pinned here as a
    # regression guard, not a design choice this test makes.
    assert BLOCK_BARS == 7


# --- PLANTED-TRUTH: a fabricated LONG-RANGE (gap=15 > 7) pool<->sweep -----
# pairing must DIE under resampling (destroyed by construction, not by luck).
def _planted_pair_bars() -> pd.DataFrame:
    """Day A (epoch_day=100): one HIGH pool forms at bar 13 (pivots at 3, 10;
    level 100.35) and is swept at bar 28 — gap = 28-13 = 15 bars, 8 MORE than
    BLOCK_BARS=7. Days B-E (epoch_day 107/114/121/128, SAME weekday as A, 7
    days apart each) are flat filler EXCEPT day B's own first block (local
    bars 0-6), a distinct clean-control burst — five same-weekday days (30
    blocks total) keep the coincidental-exact-reconstruction rate low enough
    to be a meaningful drill (a 2-day, 12-block pool was measured to
    reconstruct the planted pair by pure chance ~10% of the time — too small
    a pool to prove destruction; this is a real, not assumed, sample-size
    finding, not a tuned-to-pass fixture)."""
    a = _flat_day(100, 40)
    a.loc[3, "high"] = 100.20
    a.loc[10, "high"] = 100.35
    a.loc[28, "high"] = 100.45
    a.loc[28, "close"] = 100.30

    b = _flat_day(107, 40)
    b.loc[0:6, "high"] = 105.00  # clean-control burst: exactly one whole block
    b.loc[0:6, "low"] = 104.50

    c = _flat_day(114, 40)
    d = _flat_day(121, 40)
    e = _flat_day(128, 40)
    return pd.concat([a, b, c, d, e], ignore_index=True)


def _sweep_signatures(bars: pd.DataFrame) -> set[tuple[int, float]]:
    table = pa.table(
        {
            "ts": pa.array(bars["ts"].tolist(), type=pa.int64()),
            "high": pa.array(bars["high"].tolist(), type=pa.float64()),
            "low": pa.array(bars["low"].tolist(), type=pa.float64()),
            "close": pa.array(bars["close"].tolist(), type=pa.float64()),
        }
    )
    events = LiquiditySweepDetector().detect(table).to_pylist()
    return {
        (r["direction"], r["level"])
        for r in events
        if r["event_type"].endswith(".sweep")
    }


def test_planted_long_range_pair_exists_in_the_real_data():
    bars = _planted_pair_bars()
    sigs = _sweep_signatures(bars)
    assert (-1, 100.35) in sigs, "the planted pool/sweep pair must actually exist first"


def test_planted_long_range_pair_dies_under_resampling():
    """Measured, not assumed: an earlier version of this drill asserted
    survivals == 0 and was WRONG on the evidence (real runs find what
    review cannot) -- the pool's two pivot PRICES (100.20, 100.35) are
    preserved wherever their blocks land, and MEMBER_WINDOW_BARS=200 lets
    pivots mate across ANY resampled position within that window, not only
    the original one -- so the pairing can RECOMBINE from different block
    positions, not just survive intact in its original spot. A 200-seed
    empirical measurement on this exact fixture found a 23.5% survival
    rate (47/200) -- real, meaningful destruction (a majority of resamples
    do NOT reproduce the pairing) but not absolute, and asserting absolute
    destruction would be asserting something false. The honest, evidence-
    matched claim: survival is a MINORITY."""
    bars = _planted_pair_bars()
    assert (-1, 100.35) in _sweep_signatures(bars)  # positive control, re-affirmed

    survivals = 0
    n_seeds = 100
    for seed in range(n_seeds):
        surrogate = resample_bar_blocks(bars, seed=seed)
        if (-1, 100.35) in _sweep_signatures(surrogate):
            survivals += 1
    rate = survivals / n_seeds
    assert rate < 0.5, (
        f"planted long-range pair survived {survivals}/{n_seeds} ({rate:.0%}) resamples"
    )


# --- CLEAN-CONTROL: WITHIN-block (<=7-bar) structure must SURVIVE intact --
def test_within_block_burst_survives_intact_in_some_resample():
    bars = _planted_pair_bars()  # day B's first block (0-6) is the burst
    burst_high = [105.00] * 7
    burst_low = [104.50] * 7

    found_intact = False
    for seed in range(30):
        surrogate = resample_bar_blocks(bars, seed=seed)
        highs = surrogate["high"].tolist()
        lows = surrogate["low"].tolist()
        for start in range(0, len(surrogate) - 6):
            if highs[start : start + 7] == burst_high and lows[start : start + 7] == burst_low:
                found_intact = True
                break
        if found_intact:
            break
    assert found_intact, (
        "a whole 7-bar block's own OHLC values must be able to survive intact "
        "somewhere in a resample -- local structure is preserved by construction"
    )


# --- integration: run_block_null end-to-end on the planted fixture --------
def test_run_block_null_end_to_end_on_planted_fixture():
    bars = _planted_pair_bars()
    result = run_block_null(bars, LiquiditySweepDetector(), base_seed=100, n_runs=10)
    assert result.n_runs == 10
    assert result.base_seed == 100
    assert result.block_bars == 7
    assert len(result.event_counts) == 10
    assert all(isinstance(c, int) for c in result.event_counts)
    # Real data (undisturbed) finds exactly 2 sweep events (the planted pair
    # is the only one) -- the null runs should not systematically match that
    # exactly every time (they operate on scrambled, not real, data).
    real_events = LiquiditySweepDetector().detect(
        pa.table(
            {
                "ts": pa.array(bars["ts"].tolist(), type=pa.int64()),
                "high": pa.array(bars["high"].tolist(), type=pa.float64()),
                "low": pa.array(bars["low"].tolist(), type=pa.float64()),
                "close": pa.array(bars["close"].tolist(), type=pa.float64()),
            }
        )
    )
    assert real_events.num_rows >= 1


# --- real-data cross-check: reproduce WO-15's own quoted gap statistic ----
def test_real_burned_window_matches_the_quoted_gap_evidence(tmp_path):
    """Non-vacuous sanity: the exact 465-pool/325-sweep/55.7%-over-7 evidence
    quoted in D-023 is reproducible from the real journal, not narrated."""
    import shutil

    from qrf.kernel.records.bulk import BulkStore
    from qrf.kernel.records.store import RecordStore

    dest = tmp_path / "journal.jsonl"
    shutil.copyfile("datastore/journal/journal.jsonl", dest)
    store = RecordStore(dest)
    bulk = BulkStore(store, "datastore/bulk")
    manifest = next(
        m for m in store.query(record_type="bulk_manifest")
        if m.payload["dataset"] == "xauusd_m5_vantage"
    )
    table = bulk.read(manifest.record_id)
    assert table.num_rows == 16029

    events = LiquiditySweepDetector().detect(table).to_pylist()
    pool_formed = sorted(
        (r for r in events if r["event_type"].endswith(".pool_formed")), key=lambda r: r["ts"]
    )
    sweeps = sorted(
        (r for r in events if r["event_type"].endswith(".sweep")), key=lambda r: r["ts"]
    )
    assert len(pool_formed) == 465
    assert len(sweeps) == 325

    ts_to_idx = {t: i for i, t in enumerate(table.column("ts").to_pylist())}
    used = [False] * len(pool_formed)
    gaps = []
    for sw in sweeps:
        best = None
        for j in range(len(pool_formed) - 1, -1, -1):
            if used[j]:
                continue
            pf = pool_formed[j]
            if pf["ts"] > sw["ts"]:
                continue
            if pf["direction"] == sw["direction"] and pf["level"] == sw["level"]:
                best = j
                break
        assert best is not None
        used[best] = True
        gaps.append(ts_to_idx[sw["ts"]] - ts_to_idx[pool_formed[best]["ts"]])

    over_7 = sum(1 for g in gaps if g > BLOCK_BARS)
    assert len(gaps) == 325
    assert over_7 == 181
    assert over_7 / len(gaps) == pytest.approx(0.556923076923077)


# --- WO-16/C2: n_local_sweeps statistic (A-024's open item, D-041) --------
def test_n_local_sweeps_counts_only_sweeps_within_block_bars():
    """Mechanical: the statistic reads each SWEEP's own pool_age_bars meta
    field and filters on it -- F-27 (a check must be shown able to return a
    positive before its clean is trusted): plant one LOCAL and one LONG-RANGE
    sweep in the same table, confirm only the local one is counted."""
    events = pa.table(
        {
            "ts": pa.array([1, 2], type=pa.int64()),
            "event_type": pa.array(
                ["neelprajna.liquidity_sweep.sweep", "neelprajna.liquidity_sweep.sweep"]
            ),
            "direction": pa.array([-1, -1]),
            "level": pa.array([100.0, 101.0]),
            "meta": pa.array(
                [
                    __import__("json").dumps({"pool_age_bars": 3}),
                    __import__("json").dumps({"pool_age_bars": 15}),
                ]
            ),
        }
    )
    assert n_local_sweeps(events) == 1
    assert n_local_sweeps(events, block_bars=20) == 2


def test_n_local_sweeps_ignores_pool_formed_events():
    events = pa.table(
        {
            "ts": pa.array([1], type=pa.int64()),
            "event_type": pa.array(["neelprajna.liquidity_sweep.pool_formed"]),
            "direction": pa.array([-1]),
            "level": pa.array([100.0]),
            "meta": pa.array([__import__("json").dumps({"pool_members": 2})]),
        }
    )
    assert n_local_sweeps(events) == 0


def test_n_local_sweeps_refuses_a_sweep_missing_pool_age_bars():
    """A-054 DEFECT 2, required: a malformed sweep event (meta missing
    pool_age_bars) must raise a NAMED SchemaViolation, not a bare KeyError
    from inside a null-construction loop."""
    events = pa.table(
        {
            "ts": pa.array([1], type=pa.int64()),
            "event_type": pa.array(["neelprajna.liquidity_sweep.sweep"]),
            "direction": pa.array([-1]),
            "level": pa.array([100.0]),
            "meta": pa.array([__import__("json").dumps({"pool_members": 2})]),
        }
    )
    with pytest.raises(SchemaViolation, match="pool_age_bars"):
        n_local_sweeps(events)


def test_n_local_sweeps_empty_table_is_zero():
    events = pa.table(
        {
            "ts": pa.array([], type=pa.int64()),
            "event_type": pa.array([], type=pa.string()),
            "direction": pa.array([], type=pa.int64()),
            "level": pa.array([], type=pa.float64()),
            "meta": pa.array([], type=pa.string()),
        }
    )
    assert n_local_sweeps(events) == 0


def test_run_block_null_local_rejects_bad_params():
    day = _flat_day(100, 40)
    with pytest.raises(SchemaViolation):
        run_block_null_local(day, LiquiditySweepDetector(), base_seed=1, n_runs=0)
    with pytest.raises(SchemaViolation):
        run_block_null_local(day, LiquiditySweepDetector(), base_seed=-1, n_runs=5)


def test_planted_long_range_pair_is_excluded_by_the_local_statistic_on_real_data():
    """The exact fixture whose only event is the planted LONG-RANGE (gap=15)
    pair: n_local_sweeps on the REAL (undisturbed) detection must be 0 -- the
    raw statistic (run_block_null) would count this event; the local
    statistic (C2's whole point) must not."""
    bars = _planted_pair_bars()
    table = pa.table(
        {
            "ts": pa.array(bars["ts"].tolist(), type=pa.int64()),
            "high": pa.array(bars["high"].tolist(), type=pa.float64()),
            "low": pa.array(bars["low"].tolist(), type=pa.float64()),
            "close": pa.array(bars["close"].tolist(), type=pa.float64()),
        }
    )
    events = LiquiditySweepDetector().detect(table)
    assert events.num_rows >= 1  # the raw statistic sees it
    assert n_local_sweeps(events) == 0  # the local statistic correctly excludes it


def test_local_statistic_reduces_but_does_not_eliminate_recombination_contamination():
    """Measured, not assumed (real runs find what review cannot, HARD-WON
    RULE 4): a long-range pair CAN recombine at a shorter gap under
    resampling, so the local statistic is not immune to A-024's
    contamination, only LESS exposed to it. On this exact planted-pair
    fixture (200 seeds, matching A-024's own measurement protocol): the raw
    statistic's survival rate is the already-established 23.5% (47/200); the
    local statistic must show a STRICTLY LOWER contamination rate on the same
    seeds, not zero -- asserting zero would assert something this drill does
    not show."""
    bars = _planted_pair_bars()
    n_seeds = 200
    raw_survivals = 0
    local_contaminations = 0
    for seed in range(n_seeds):
        surrogate = resample_bar_blocks(bars, seed=seed)
        sigs_present = (-1, 100.35) in _sweep_signatures(surrogate)
        if sigs_present:
            raw_survivals += 1
        table = pa.table(
            {
                "ts": pa.array(surrogate["ts"].tolist(), type=pa.int64()),
                "high": pa.array(surrogate["high"].tolist(), type=pa.float64()),
                "low": pa.array(surrogate["low"].tolist(), type=pa.float64()),
                "close": pa.array(surrogate["close"].tolist(), type=pa.float64()),
            }
        )
        events = LiquiditySweepDetector().detect(table)
        for r in events.to_pylist():
            if (
                r["event_type"].endswith(".sweep")
                and r["direction"] == -1
                and r["level"] == 100.35
                and __import__("json").loads(r["meta"])["pool_age_bars"] <= BLOCK_BARS
            ):
                local_contaminations += 1
                break

    assert raw_survivals == 47, (
        f"raw survivals drifted from A-024's measured 47/200: {raw_survivals}"
    )
    assert local_contaminations < raw_survivals, (
        f"local statistic ({local_contaminations}/{n_seeds}) must contaminate LESS than the "
        f"raw statistic ({raw_survivals}/{n_seeds}), or it buys nothing over C2's concern"
    )
    assert local_contaminations == 11, (
        f"measured contamination drifted from the recorded 11/200: {local_contaminations}"
    )


def test_run_block_null_local_end_to_end_on_planted_fixture():
    bars = _planted_pair_bars()
    result = run_block_null_local(bars, LiquiditySweepDetector(), base_seed=100, n_runs=10)
    assert result.n_runs == 10
    assert result.base_seed == 100
    assert result.block_bars == 7
    assert len(result.event_counts) == 10
    assert all(isinstance(c, int) and c >= 0 for c in result.event_counts)
    # The real (undisturbed) count is 0 -- the planted pair is long-range, so
    # the local statistic correctly reports no local sweeps on the real data.
    real_table = pa.table(
        {
            "ts": pa.array(bars["ts"].tolist(), type=pa.int64()),
            "high": pa.array(bars["high"].tolist(), type=pa.float64()),
            "low": pa.array(bars["low"].tolist(), type=pa.float64()),
            "close": pa.array(bars["close"].tolist(), type=pa.float64()),
        }
    )
    real_local = n_local_sweeps(LiquiditySweepDetector().detect(real_table))
    assert real_local == 0


# --- empirical_one_sided_p (add-one estimator, A-054 DEFECT 1) ------------
def test_empirical_one_sided_p_basic():
    # ge=6 of 10 (values 5..10) -> (6+1)/(10+1)
    assert empirical_one_sided_p(5, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == pytest.approx(7 / 11)
    # ge=0 of 10 -> (0+1)/(10+1), NOT 0.0 (A-054: a naive ge/n would be exactly 0.0 here)
    assert empirical_one_sided_p(11, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) == pytest.approx(1 / 11)
    # ge=3 of 3 (all >= 0) -> (3+1)/(3+1) == 1.0, the ceiling is still reachable
    assert empirical_one_sided_p(0, [1, 2, 3]) == 1.0


def test_empirical_one_sided_p_never_returns_zero():
    """A-054 DEFECT 1, required: 200 (or any finite n) surrogates can never
    license an exact p=0.0 claim. Drilled across several ge=0 cases and
    sample sizes -- the drill law applies to arithmetic too."""
    for null_counts, real_value in [
        ([0] * 200, 1000),
        ([1, 2, 3], 999),
        ([5] * 5, 6),
        ([0], 1),
    ]:
        p = empirical_one_sided_p(real_value, null_counts)
        assert p > 0.0, f"returned exactly 0.0 for {null_counts!r}/{real_value}"
        assert p == pytest.approx(1 / (len(null_counts) + 1))


def test_empirical_one_sided_p_rejects_empty_null():
    with pytest.raises(SchemaViolation):
        empirical_one_sided_p(1, [])
