"""The harness must drill itself: a checker that never raises must FAIL the
drill, not pass it. A drill harness that always reports success is worse
than none — it launders every later claim.
"""

import pytest

from tests.drills.harness import DrillLog, run_drill


def test_harness_fails_a_checker_that_can_never_raise():
    def never_raises(_value):
        pass

    log = DrillLog()
    with pytest.raises(AssertionError, match="did not raise"):
        run_drill(
            name="always-passes-checker",
            checker=never_raises,
            clean_input="clean",
            tampered_input="tampered",
            expected_exception=ValueError,
            log=log,
        )
    assert log.results == []


def test_harness_fails_when_the_control_run_raises():
    def always_raises(_value):
        raise ValueError("boom")

    log = DrillLog()
    with pytest.raises(AssertionError, match="control run raised"):
        run_drill(
            name="broken-checker",
            checker=always_raises,
            clean_input="clean",
            tampered_input="tampered",
            expected_exception=ValueError,
            log=log,
        )
    assert log.results == []


def test_harness_fails_when_tampered_raises_the_wrong_type():
    def wrong_type(value):
        if value == "tampered":
            raise TypeError("wrong kind of failure")

    log = DrillLog()
    with pytest.raises(AssertionError, match="expected ValueError"):
        run_drill(
            name="wrong-exception-checker",
            checker=wrong_type,
            clean_input="clean",
            tampered_input="tampered",
            expected_exception=ValueError,
            log=log,
        )
    assert log.results == []


def test_harness_passes_a_real_checker():
    def real_checker(value):
        if value == "tampered":
            raise ValueError("bad value")

    log = DrillLog()
    result = run_drill(
        name="real-checker",
        checker=real_checker,
        clean_input="clean",
        tampered_input="tampered",
        expected_exception=ValueError,
        log=log,
    )
    assert result.control_passed
    assert result.tampered_exception is ValueError
    assert log.results == [result]
