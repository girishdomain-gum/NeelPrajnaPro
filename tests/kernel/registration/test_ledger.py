"""R1-R3 (A-015 §5) for the trial ledger."""

from qrf.errors import BudgetExhausted, RegistrationMismatch
from qrf.kernel.registration.alpha import alpha_for_registration_index
from qrf.kernel.registration.ledger import TrialLedger
from tests.drills.harness import DrillLog, run_drill


def _register(ledger, hid, family="fam-a", thresholds_hash="t1", **overrides):
    kwargs = dict(
        hypothesis_id=hid,
        family_id=family,
        statement_hash="s1",
        detector_name="liquidity_sweep",
        detector_version="H-07-v1.1-appendixB",
        data_span_start_utc=0,
        data_span_end_utc=1000,
        window_id="W1",
        thresholds_hash=thresholds_hash,
        phrase_hash="0" * 64,
    )
    kwargs.update(overrides)
    return ledger.register(**kwargs)


def test_register_and_lookup_round_trip(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    reg = _register(ledger, "H1")
    assert reg.alpha == alpha_for_registration_index(1)
    assert reg.spent_count_at_registration == 1
    assert ledger.lookup("H1") == reg


def test_alpha_allocated_incrementally_per_family(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    r1 = _register(ledger, "H1")
    r2 = _register(ledger, "H2")
    assert r1.alpha == alpha_for_registration_index(1)
    assert r2.alpha == alpha_for_registration_index(2)
    assert r2.alpha < r1.alpha  # incremental, decaying -- never divided flat up front


# --- R1: post-registration threshold edit is detected and refused --------


def test_r1_post_registration_threshold_edit_refused_drill():
    log = DrillLog()

    def checker(path_and_change):
        path, change_threshold = path_and_change
        ledger = TrialLedger(path)
        _register(ledger, "H1", thresholds_hash="original")
        if change_threshold:
            _register(ledger, "H1", thresholds_hash="edited")  # same id, different frozen field
        else:
            ledger.lookup("H1")  # no-op control

    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        result = run_drill(
            name="R1-post-registration-threshold-edit",
            checker=checker,
            clean_input=(Path(d1) / "trials.jsonl", False),
            tampered_input=(Path(d2) / "trials.jsonl", True),
            expected_exception=RegistrationMismatch,
            log=log,
        )
    assert result.tampered_exception is RegistrationMismatch


# --- R2: a spent attempt cannot be un-spent -------------------------------


def test_r2_spent_registration_cannot_be_unspent(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    _register(ledger, "H1")
    assert ledger.family_count("fam-a") == 1
    try:
        _register(ledger, "H1")  # any re-attempt at the same id
    except RegistrationMismatch:
        pass
    # the family count must be UNCHANGED by the refused attempt -- nothing
    # was un-spent, and nothing extra was spent either
    assert ledger.family_count("fam-a") == 1


# --- R3: 101st registration in a family is refused ------------------------


def test_r3_101st_registration_refused_drill(tmp_path):
    log = DrillLog()
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    for i in range(100):
        _register(ledger, f"H{i}", capacity=100)
    assert ledger.family_count("fam-a") == 100

    def checker(attempt_101st: bool):
        if attempt_101st:
            _register(ledger, "H100", capacity=100)
        # control: no-op, family already at 100 but we don't touch it

    result = run_drill(
        name="R3-101st-registration-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=BudgetExhausted,
        log=log,
    )
    assert result.tampered_exception is BudgetExhausted
    assert ledger.family_count("fam-a") == 100  # unchanged by the refusal
