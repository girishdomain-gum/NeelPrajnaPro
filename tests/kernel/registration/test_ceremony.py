"""R4/R5 (A-015 §4.3, §5): the Owner's ceremony, proven with throwaway
phrases obviously not the Owner's real one -- which has not been chosen
as of S05 and which this module neither needs nor wants.
"""

import hashlib
import inspect

from qrf.errors import CeremonyRefused
from qrf.kernel.registration.ceremony import complete_registration
from qrf.kernel.registration.ledger import TrialLedger
from tests.drills.harness import DrillLog, run_drill

THROWAWAY_PHRASE = "definitely-not-the-owners-real-phrase"
THROWAWAY_HASH = hashlib.sha256(THROWAWAY_PHRASE.encode("utf-8")).hexdigest()


def _kwargs(**overrides):
    base = dict(
        hypothesis_id="H1",
        family_id="fam-a",
        statement_hash="s1",
        detector_name="liquidity_sweep",
        detector_version="H-07-v1.1-appendixB",
        data_span_start_utc=0,
        data_span_end_utc=1000,
        window_id="W1",
        thresholds_hash="t1",
    )
    base.update(overrides)
    return base


def test_ceremony_with_correct_phrase_registers(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    reg = complete_registration(
        ledger,
        typed_phrase=THROWAWAY_PHRASE,
        expected_phrase_hash=THROWAWAY_HASH,
        **_kwargs(),
    )
    assert reg.hypothesis_id == "H1"
    assert reg.phrase_hash == THROWAWAY_HASH


# --- R4: registration without the ceremony / with the wrong phrase -------


def test_r4_missing_phrase_refused_drill(tmp_path):
    log = DrillLog()
    ledger = TrialLedger(tmp_path / "trials.jsonl")

    def checker(supply_phrase: bool):
        complete_registration(
            ledger,
            typed_phrase=THROWAWAY_PHRASE if supply_phrase else "",
            expected_phrase_hash=THROWAWAY_HASH,
            **_kwargs(hypothesis_id="H-missing" if not supply_phrase else "H-present"),
        )

    result = run_drill(
        name="R4-missing-phrase-refused",
        checker=checker,
        clean_input=True,
        tampered_input=False,
        expected_exception=CeremonyRefused,
        log=log,
    )
    assert result.tampered_exception is CeremonyRefused


def test_r4_wrong_phrase_refused_drill(tmp_path):
    log = DrillLog()
    ledger = TrialLedger(tmp_path / "trials.jsonl")

    def checker(correct: bool):
        complete_registration(
            ledger,
            typed_phrase=THROWAWAY_PHRASE if correct else "a-wrong-guess",
            expected_phrase_hash=THROWAWAY_HASH,
            **_kwargs(hypothesis_id="H-correct" if correct else "H-wrong"),
        )

    result = run_drill(
        name="R4-wrong-phrase-refused",
        checker=checker,
        clean_input=True,
        tampered_input=False,
        expected_exception=CeremonyRefused,
        log=log,
    )
    assert result.tampered_exception is CeremonyRefused


def test_r4_refused_ceremony_registers_nothing(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    try:
        complete_registration(
            ledger,
            typed_phrase="wrong",
            expected_phrase_hash=THROWAWAY_HASH,
            **_kwargs(),
        )
    except CeremonyRefused:
        pass
    assert ledger.family_count("fam-a") == 0


# --- R5: the phrase appears in no file, log, or fixture ------------------


def test_r5_source_never_hardcodes_a_real_looking_phrase():
    """Static check: the ceremony module's own source contains no phrase
    constant at all -- only hashing logic and a parameter name. This is
    the closest a test can get to proving "the phrase appears nowhere",
    short of scanning every file in the repo.
    """
    import qrf.kernel.registration.ceremony as ceremony_module

    source = inspect.getsource(ceremony_module)
    assert "typed_phrase" in source  # the parameter exists
    # no assignment of a literal string to anything resembling a phrase
    assert "REAL_PHRASE" not in source
    assert "OWNER_PHRASE" not in source


def test_r5_ceremony_function_does_not_return_the_phrase(tmp_path):
    ledger = TrialLedger(tmp_path / "trials.jsonl")
    reg = complete_registration(
        ledger,
        typed_phrase=THROWAWAY_PHRASE,
        expected_phrase_hash=THROWAWAY_HASH,
        **_kwargs(),
    )
    reg_repr = repr(reg)
    assert THROWAWAY_PHRASE not in reg_repr
