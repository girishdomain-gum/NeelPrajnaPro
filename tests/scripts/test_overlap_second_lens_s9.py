"""ARCH-009 S4.1 (DEVQ-023) -- overlap engine unit tests.

Fully synthetic (no journal, no parquet): they pin the DEVQ-023 machinery -- empirical
weekly segmentation, the agreement-RATE discriminator, the shared-count sanity floor,
the two-part guard (>=3x runner-up AND >=0.80), the winter prediction guard (<0.90 STOP),
and the noise-absorption rule (a run < K=2 windows never opens an era). scripts/ is not a
package, so the tool logic is loaded from file -- the single source of truth for the CLI
and these tests alike.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def eng():
    return _load("overlap_second_lens_s9")


def _bar(ts, price):
    # a bar whose OHLC are all `price`; distinct hours differ by >> tolerance, so a
    # wrong-hour pairing always disagrees.
    return {"ts": int(ts), "open": price, "high": price, "low": price, "close": price}


def _feed(eng, n_hours, boundary_hour, shift_a=-2, shift_b=-3, price_step=10.0,
          corrupt=(), start_price=1000.0):
    """A primary bar list + a second-feed dict with a clean shift flip at
    ``boundary_hour``. Bars before the boundary truly align at ``shift_a``, after at
    ``shift_b``. ``corrupt`` is a set of hour-indices whose second-feed OHLC are pushed
    out of tolerance (to depress an era's agreement rate)."""
    hr = eng.HR_NS
    anchor = 1_700_000_000_000_000_000  # arbitrary; well clear of any reserve range
    bars, sec = [], {}
    for i in range(n_hours):
        ts = anchor + i * hr
        price = start_price + i * price_step
        bars.append(_bar(ts, price))
        s_true = shift_a if i < boundary_hour else shift_b
        val = price + 5.0 if i in corrupt else price   # +5 > tol(0.75) => disagree
        sec[ts + s_true * hr] = {"open": val, "high": val, "low": val, "close": val}
    return bars, sec, anchor


# --------------------------------------------------------------------------- agreement
def test_agrees_tolerance_edges(eng):
    base = _bar(0, 2000.0)
    assert eng._agrees(base, {"open": 2000.5, "high": 2000.75, "low": 1999.25, "close": 1999.5})
    # open just over 0.50 -> disagree
    assert not eng._agrees(base, {"open": 2000.51, "high": 2000.0, "low": 2000.0, "close": 2000.0})
    # high just over 0.75 -> disagree
    assert not eng._agrees(base, {"open": 2000.0, "high": 2000.76, "low": 2000.0, "close": 2000.0})


def test_shift_table_counts(eng):
    bars, sec, _ = _feed(eng, n_hours=200, boundary_hour=200)  # single era, all shift -2
    table = {t["shift_h"]: t for t in eng._shift_table(bars, sec)}
    assert table[-2]["agreement_rate"] > 0.95           # the true shift agrees
    assert table[-2]["agree"] == table[-2]["shared"]
    assert table[-3]["agreement_rate"] < 0.05           # wrong shift pairs neighbours


# ------------------------------------------------------------------- segmentation
def test_detects_two_eras_and_boundary(eng):
    # 12 weeks; boundary at exactly week 6 start (hour = 6*7*24).
    hpw = eng.WEEK_NS // eng.HR_NS
    boundary_hour = 6 * hpw
    bars, sec, anchor = _feed(eng, n_hours=12 * hpw, boundary_hour=boundary_hour)
    eras, boundaries = eng.detect_eras(bars, sec)
    assert len(eras) == 2
    assert len(boundaries) == 1
    # refined to the hour; a 1-bar tie is inherent at a clock flip (the last winter bar's
    # -2 key and the first summer bar's -3 key collide), and ties resolve to the earlier cut.
    assert abs(boundaries[0] - (anchor + boundary_hour * eng.HR_NS)) <= eng.HR_NS
    post = eng.evaluate_eras(bars, sec, eras)
    assert [e["winner"]["shift_h"] for e in post] == [-2, -3]
    assert all(e["passes"] for e in post)


def test_single_week_noise_is_absorbed(eng):
    # one anomalous week (winner -3) inside an otherwise -2 span must NOT open an era.
    hpw = eng.WEEK_NS // eng.HR_NS
    bars, sec, anchor = _feed(eng, n_hours=8 * hpw, boundary_hour=8 * hpw)  # all -2
    hr = eng.HR_NS
    # re-key week 3's bars to align at -3 instead of -2 (a lone flipped window)
    for i in range(3 * hpw, 4 * hpw):
        ts = anchor + i * hr
        price = 1000.0 + i * 10.0
        del sec[ts - 2 * hr]
        sec[ts - 3 * hr] = {"open": price, "high": price, "low": price, "close": price}
    eras, boundaries = eng.detect_eras(bars, sec)
    assert len(eras) == 1                # the K=2 rule absorbs the single-week run
    assert boundaries == []


# ------------------------------------------------------------------------ guards
def test_guard_fires_below_absolute(eng):
    # corrupt ~40% of a single winter era's second feed -> rate ~0.6 < 0.80 -> STOP.
    n = 300
    corrupt = set(range(0, n, 5)) | set(range(1, n, 5))    # 2 of every 5 -> ~0.6 rate
    bars, sec, _ = _feed(eng, n_hours=n, boundary_hour=n, corrupt=corrupt)
    eras, _ = eng.detect_eras(bars, sec)
    post = eng.evaluate_eras(bars, sec, eras)
    assert 0.55 < post[0]["winner"]["agreement_rate"] < 0.65
    assert post[0]["abs_ok"] is False and post[0]["passes"] is False
    v = eng.guards_verdict(post)
    assert v["ok"] is False and v["failed"]


def test_prediction_guard_winter_below_0_90(eng):
    # a winter era at ~0.86: clears the two-part guard but fails the <0.90 prediction guard.
    n = 300
    corrupt = set(range(0, n, 7))          # ~1/7 corrupted -> ~0.857 rate
    bars, sec, _ = _feed(eng, n_hours=n, boundary_hour=n, corrupt=corrupt)
    eras, _ = eng.detect_eras(bars, sec)
    post = eng.evaluate_eras(bars, sec, eras)
    r = post[0]["winner"]["agreement_rate"]
    assert 0.80 <= r < 0.90 and post[0]["is_winter"]
    assert post[0]["passes"] is True                       # two-part guard satisfied
    v = eng.guards_verdict(post)
    assert v["prediction_ok"] is False and v["ok"] is False  # prediction guard STOPs


def test_clean_two_era_passes_all_guards(eng):
    hpw = eng.WEEK_NS // eng.HR_NS
    bars, sec, _ = _feed(eng, n_hours=12 * hpw, boundary_hour=6 * hpw)
    eras, _ = eng.detect_eras(bars, sec)
    post = eng.evaluate_eras(bars, sec, eras)
    v = eng.guards_verdict(post)
    assert v["ok"] is True and not v["failed"] and v["prediction_ok"] is True
    assert v["winter_min"] > 0.95


def test_sanity_floor_uses_shared_count(eng):
    # the discriminator's winner must also clear the shared-count floor; on this dense
    # synthetic grid all shifts are near-equally shared, so the floor holds for the winner.
    bars, sec, _ = _feed(eng, n_hours=250, boundary_hour=250)
    eras, _ = eng.detect_eras(bars, sec)
    post = eng.evaluate_eras(bars, sec, eras)
    e = post[0]
    assert e["winner"]["shared"] >= eng.FLOOR_FRAC * e["max_shared"]
    assert e["floor_ok"] is True


def test_rebuild_bulk_sha_matches_manifest(eng):
    """Integration (ARCH-009 S1 discipline): the gitignored overlap parquet regenerates
    byte-identically from journal + feeds, or rebuild() raises. Skips on a checkout where
    the second_lens has not yet been appended (no overlap manifest to verify against)."""
    from qrf.kernel.records.store import RecordStore

    store = RecordStore(eng.JOURNAL)
    have = [m for m in store.query(record_type="bulk_manifest")
            if m.payload["dataset"] == eng.OVERLAP_DATASET]
    if not have:
        pytest.skip("overlap manifest not yet in journal (engine has not run here)")
    eng.rebuild()   # writes the parquet + asserts sha == recorded; SystemExit on drift
