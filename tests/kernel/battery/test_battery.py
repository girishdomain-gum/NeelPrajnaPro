"""B1-B5, the honest atomicity drill, the known-answer test in both
directions (A-015 §5), and F-11's pluggable-null drills (A-044).
"""

import os

import pytest

from qrf.errors import (
    CapabilityRequired,
    HypothesisNotRegistered,
    NullNotSpecified,
    UnverifiedObservations,
    WindowConflict,
    WriterLockHeld,
)
from qrf.kernel.battery.battery import Battery
from qrf.kernel.detection.types import ObservationSet
from qrf.kernel.measurement.circular_shift_null import circular_shift_null_runner
from qrf.kernel.null.resampling import block_resampling_null_runner
from qrf.kernel.registration.ceremony import complete_registration
from qrf.kernel.registration.ledger import TrialLedger
from qrf.kernel.windows.ledger import VerdictCapability, WindowLedger
from tests.drills.harness import DrillLog, run_drill

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


def _setup(tmp_path, family="fam-a", hid="H1", window_id="W1", start=0, end=1000):
    trials = TrialLedger(tmp_path / "trials.jsonl")
    windows = WindowLedger(tmp_path / "windows.jsonl")
    windows.reserve(window_id, start, end, "VIRGIN")
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


def _block_null(series, block_length=10, n_resamples=2000, seed=1):
    return block_resampling_null_runner(series, _first_three_mean, block_length, n_resamples, seed)


# --- Known-answer test, BOTH directions -----------------------------------


def test_known_answer_planted_effect_is_detected(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path, hid="H-effect")
    series = _planted_effect_series()
    verdict = battery.judge(
        hypothesis_id="H-effect",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        observed_statistic=_first_three_mean(series),
        null_runner=_block_null(series),
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
        observed_statistic=_first_three_mean(series),
        null_runner=_block_null(series),
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
        observed_statistic=_first_three_mean(series),
        null_runner=_block_null(series, seed=1),
    )
    assert windows.balances()["burned"] == 1
    with pytest.raises(WindowConflict):
        battery.judge(
            hypothesis_id="H1",
            observation_set=_obs_set(),
            verified_source_sha256="a" * 64,
            observed_statistic=_first_three_mean(series),
            null_runner=_block_null(series, seed=2),
        )


# --- B4: unregistered hypothesis -> REFUSED -------------------------------


def test_b4_unregistered_hypothesis_refused(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path)
    series = _no_effect_series()
    with pytest.raises(HypothesisNotRegistered):
        battery.judge(
            hypothesis_id="H-never-registered",
            observation_set=_obs_set(),
            verified_source_sha256="a" * 64,
            observed_statistic=0.0,
            null_runner=_block_null(series),
        )


# --- B5: unverified / non-provenance-bound observations -> REFUSED -------


def test_b5_unverified_observations_refused(tmp_path):
    battery, _trials, _windows, _reg = _setup(tmp_path, hid="H1")
    series = _no_effect_series()
    with pytest.raises(UnverifiedObservations):
        battery.judge(
            hypothesis_id="H1",
            observation_set=_obs_set(sha256="a" * 64),
            verified_source_sha256="b" * 64,  # does not match the ObservationSet's own hash
            observed_statistic=0.0,
            null_runner=_block_null(series),
        )


# --- B1: a second writer attempting a verdict -> REFUSED ------------------


def test_b1_second_writer_refused_drill(tmp_path):
    _battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")
    with windows._store:  # noqa: SLF001 -- simulate a concurrent writer holding the lock
        with pytest.raises(WriterLockHeld):
            windows.record_verdict("W1", "H1", {"p_value": 0.01}, VerdictCapability())


# --- A-016 R1: record_verdict() requires a VerdictCapability token --------


def test_r1_record_verdict_requires_capability_token_drill(tmp_path):
    log = DrillLog()
    _battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")

    def checker(supply_capability: bool):
        windows.record_verdict(
            "W1",
            "H1",
            {"p_value": 0.01},
            VerdictCapability() if supply_capability else object(),
        )

    result = run_drill(
        name="R1-record-verdict-requires-capability",
        checker=checker,
        clean_input=True,
        tampered_input=False,
        expected_exception=CapabilityRequired,
        log=log,
    )
    assert result.tampered_exception is CapabilityRequired


def test_r1_hand_built_verdict_without_capability_refused(tmp_path):
    _battery, _trials, windows, _reg = _setup(tmp_path, hid="H1")
    with pytest.raises(CapabilityRequired):
        windows.record_verdict("W1", "H1", {"p_value": 0.01}, None)
    # nothing was written: the window is still virgin, unburned
    assert windows.balances()["burned"] == 0


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
        observed_statistic=_first_three_mean(series),
        null_runner=_block_null(series),
    )
    assert verdict.significant is True
    assert windows.balances()["burned"] == 1


# --- F-11 (A-044): the pluggable null, drilled ----------------------------


def test_f11_judge_refuses_without_a_null_runner_drill(tmp_path):
    """A verdict computed under an unstated null is exactly the failure
    F-11 exists to close: `null_runner=None` must refuse, never silently
    fall back to any particular null. TWO hypotheses/windows, one per
    half, so both halves genuinely call `battery.judge()` -- a real
    control run (succeeds, burns its own window) and a real tampered run
    (refused, its window stays virgin), never a value substituted for
    the call itself.
    """
    log = DrillLog()
    trials = TrialLedger(tmp_path / "trials.jsonl")
    windows = WindowLedger(tmp_path / "windows.jsonl")
    battery = Battery(trials, windows)
    series = _no_effect_series()

    def checker(supply_null: bool):
        hid = "H-null-control" if supply_null else "H-null-tampered"
        start, end = (0, 1000) if supply_null else (5000, 6000)
        windows.reserve(hid, start, end, "VIRGIN")
        complete_registration(
            trials,
            typed_phrase=PHRASE,
            expected_phrase_hash=PHRASE_HASH,
            hypothesis_id=hid,
            family_id="fam-null-drill",
            statement_hash="s1",
            detector_name="liquidity_sweep",
            detector_version="H-07-v1.1-appendixB",
            data_span_start_utc=start,
            data_span_end_utc=end,
            window_id=hid,
            thresholds_hash="t1",
        )
        battery.judge(
            hypothesis_id=hid,
            observation_set=_obs_set(),
            verified_source_sha256="a" * 64,
            observed_statistic=_first_three_mean(series),
            null_runner=_block_null(series) if supply_null else None,
        )

    result = run_drill(
        name="F11-judge-refuses-without-null-runner",
        checker=checker,
        clean_input=True,
        tampered_input=False,
        expected_exception=NullNotSpecified,
        log=log,
    )
    assert result.tampered_exception is NullNotSpecified
    assert windows.balances()["burned"] == 1  # only the control's window was burned
    assert windows.balances()["virgin_unburned"] == 1  # the tampered window untouched


def test_f11_block_resampling_and_circular_shift_verdicts_are_distinguishable(tmp_path):
    """The requirement this drill proves: two verdicts produced by
    DIFFERENT nulls must be tellable apart from the written record alone
    -- never inferred, never assumed to be "whichever one Battery always
    used".
    """
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class _FakeEvent:
        sweep_bar: int
        direction: int

    @dataclass(frozen=True)
    class _FakeBar:
        close: float

    battery_a, _t1, windows_a, _r1 = _setup(tmp_path, hid="H-block", window_id="W-block")
    series = _planted_effect_series()
    verdict_block = battery_a.judge(
        hypothesis_id="H-block",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        observed_statistic=_first_three_mean(series),
        null_runner=_block_null(series),
    )

    bars = tuple(_FakeBar(close=100.0 + (i % 7) * 0.05) for i in range(2000))
    events = [_FakeEvent(sweep_bar=500, direction=1), _FakeEvent(sweep_bar=700, direction=-1)]
    cs_runner = circular_shift_null_runner(
        events, bars, min_offset=200, n_resamples=50, seed=3, excluded_count=0, horizon=10
    )
    battery_b, _t2, windows_b, _r2 = _setup(
        tmp_path, family="fam-cs", hid="H-cs", window_id="W-cs", start=2000, end=3000
    )
    verdict_cs = battery_b.judge(
        hypothesis_id="H-cs",
        observation_set=_obs_set(),
        verified_source_sha256="a" * 64,
        observed_statistic=0.01,
        null_runner=cs_runner,
    )

    assert verdict_block.null_name == "block_resampling_v1"
    assert "block_length" in verdict_block.null_parameters
    assert verdict_cs.null_name == "circular_shift_v1"
    assert "min_offset" in verdict_cs.null_parameters
    assert verdict_block.null_name != verdict_cs.null_name

    # and the DISTINCTION SURVIVES THE WRITTEN RECORD, not just the return
    # value -- read it back from the window ledger, not from `verdict_*`:
    stored_block = windows_a.get_verdict("W-block")
    stored_cs = windows_b.get_verdict("W-cs")
    assert stored_block["null_name"] == "block_resampling_v1"
    assert stored_cs["null_name"] == "circular_shift_v1"
