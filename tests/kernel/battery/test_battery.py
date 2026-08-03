"""B1-B5, the honest atomicity drill, and the known-answer test in both
directions (A-015 §5).
"""

import os

import pytest

from qrf.errors import (
    HypothesisNotRegistered,
    UnverifiedObservations,
    WindowConflict,
    WriterLockHeld,
)
from qrf.kernel.battery.battery import Battery
from qrf.kernel.detection.types import ObservationSet
from qrf.kernel.registration.ceremony import complete_registration
from qrf.kernel.registration.ledger import TrialLedger
from qrf.kernel.windows.ledger import WindowLedger

PHRASE = "throwaway-s05-phrase"
import hashlib  # noqa: E402

PHRASE_HASH = hashlib.sha256(PHRASE.encode("utf-8")).hexdigest()


def _obs_set(sha256="a" * 64):
    return ObservationSet(
        detector_name="liquidity_sweep",
        detector_version="H-07-v1.1-appendixB",
        source_sha256=sha256,
        span_start_utc=0,
        span_end_utc=1000,
        observations=(),
    )


def _setup(tmp_path, family="fam-a", hid="H1", window_id="W1"):
    trials = TrialLedger(tmp_path / "trials.jsonl")
    windows = WindowLedger(tmp_path / "windows.jsonl")
    windows.reserve(window_id, 0, 1000, "VIRGIN")
    reg = complete_registration(
        trials,
        typed_phrase=PHRASE,
        expected_phrase_hash=PHRASE_HASH,
        hypothesis_id=hid,
        family_id=family,
        statement_hash="s1",
        detector_name="liquidity_sweep",
        detector_version="H-07-v1.1-appendixB",
        data_span_start_utc=0,
        data_span_end_utc=1000,
        window_id=window_id,
        thresholds_hash="t1",
    )
    battery = Battery(trials, windows)
    return battery, trials, windows, reg


def _no_effect_series():
    return [0.0] * 200


def _planted_effect_series():
    return [100.0, 100.0, 100.0] + [0.0] * 197


def _first_three_mean(series):
    return sum(series[:3]) / 3


# --- Known-answer test, BOTH directions -----------------------------------


def test_known_answer_planted_effect_is_detected(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path, hid="H-effect")
    series = _planted_effect_series()
    verdict = battery.judge(
        hypothesis_id="H-effect",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        series=series,
        statistic_fn=_first_three_mean,
        observed_statistic=_first_three_mean(series),
        block_length=10,
        n_resamples=2000,
        seed=1,
    )
    assert verdict.significant is True
    assert verdict.p_value < verdict.alpha


def test_known_answer_no_effect_is_not_significant(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path, hid="H-noeffect")
    series = _no_effect_series()
    verdict = battery.judge(
        hypothesis_id="H-noeffect",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        series=series,
        statistic_fn=_first_three_mean,
        observed_statistic=_first_three_mean(series),
        block_length=10,
        n_resamples=2000,
        seed=1,
    )
    assert verdict.significant is False
    assert verdict.p_value == 1.0  # every null draw ties the observed (all zeros)


# --- B3: judging on an already-burned window -> REFUSED ------------------


def test_b3_already_burned_window_refused_drill(tmp_path):
    battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")
    series = _planted_effect_series()
    battery.judge(
        hypothesis_id="H1",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        series=series,
        statistic_fn=_first_three_mean,
        observed_statistic=_first_three_mean(series),
        block_length=10,
        n_resamples=2000,
        seed=1,
    )
    assert windows.balances()["burned"] == 1
    with pytest.raises(WindowConflict):
        battery.judge(
            hypothesis_id="H1",
            observation_set=_obs_set(),
            verified_source_sha256="a" * 64,
            series=series,
            statistic_fn=_first_three_mean,
            observed_statistic=_first_three_mean(series),
            block_length=10,
            n_resamples=2000,
            seed=2,
        )


# --- B4: unregistered hypothesis -> REFUSED -------------------------------


def test_b4_unregistered_hypothesis_refused(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path)
    with pytest.raises(HypothesisNotRegistered):
        battery.judge(
            hypothesis_id="H-never-registered",
            observation_set=_obs_set(),
            verified_source_sha256="a" * 64,
            series=_no_effect_series(),
            statistic_fn=_first_three_mean,
            observed_statistic=0.0,
            block_length=10,
            n_resamples=2000,
            seed=1,
        )


# --- B5: unverified / non-provenance-bound observations -> REFUSED -------


def test_b5_unverified_observations_refused(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path, hid="H1")
    with pytest.raises(UnverifiedObservations):
        battery.judge(
            hypothesis_id="H1",
            observation_set=_obs_set(sha256="a" * 64),
            verified_source_sha256="b" * 64,  # does not match the ObservationSet's own hash
            series=_no_effect_series(),
            statistic_fn=_first_three_mean,
            observed_statistic=0.0,
            block_length=10,
            n_resamples=2000,
            seed=1,
        )


# --- B1: a second writer attempting a verdict -> REFUSED ------------------


def test_b1_second_writer_refused_drill(tmp_path):
    _battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")
    with windows._store:  # noqa: SLF001 -- simulate a concurrent writer holding the lock
        with pytest.raises(WriterLockHeld):
            windows.record_verdict("W1", "H1", {"p_value": 0.01})


# --- B2: verdict+burn atomicity, drilled HONESTLY (S02 F-02's lesson) ----


def test_b2_verdict_burn_atomicity_honest_crash_drill(tmp_path):
    """Leaves BOTH a torn tail AND the stale writer lock behind, exactly
    as a real crash mid-verdict-write would -- not just a torn tail in
    isolation (the mistake F-02 found and fixed in S02).
    """
    _battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")

    store = windows._store  # noqa: SLF001
    fd = os.open(store._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)  # noqa: SLF001
    os.write(fd, b"99999")
    os.close(fd)
    with open(store.path, "a", encoding="utf-8") as f:
        f.write('{"seq":1,"op":"verdict","truncatedgarbage')

    from qrf.errors import TornTail

    # verify()/balances() don't need the lock, so they see the torn tail
    # directly and refuse loudly, never silently guessing burned/unburned:
    with pytest.raises(TornTail):
        windows.balances()

    # recovery DOES need the lock, and must be BLOCKED by the stale one
    # first -- never silently bypassed:
    with pytest.raises(WriterLockHeld):
        store.recover_torn_tail()

    assert store.break_lock() is True
    assert store.recover_torn_tail() is True

    # window is exactly as if the crashed verdict attempt never happened:
    assert windows.balances()["virgin_unburned"] == 1
    assert windows.balances()["burned"] == 0

    # and a real verdict can still be written cleanly afterward:
    series = _planted_effect_series()
    verdict = Battery(_trials, windows).judge(
        hypothesis_id="H1",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        series=series,
        statistic_fn=_first_three_mean,
        observed_statistic=_first_three_mean(series),
        block_length=10,
        n_resamples=2000,
        seed=1,
    )
    assert verdict.significant is True
    assert windows.balances()["burned"] == 1
