"""The drill harness: no checker is trusted until shown able to FAIL.

Design after reference/NeelPrajnaPro_v1 @ 67b1d69 (control/tampered drill
pairs), re-implemented. Every drill runs a checker against a clean input
(must PASS) and a tampered input (must raise the SPECIFIC expected exception
type — never a bare Exception, since that is how a drill passes for the
wrong reason).
"""

from dataclasses import dataclass, field


@dataclass
class DrillResult:
    name: str
    control_passed: bool
    tampered_exception: type[BaseException]


@dataclass
class DrillLog:
    results: list[DrillResult] = field(default_factory=list)


def run_drill(name, checker, clean_input, tampered_input, expected_exception, log=None):
    """Run `checker(clean_input)` expecting no exception (the control), then
    `checker(tampered_input)` expecting `expected_exception` (the tampered
    case). Raises AssertionError if either half does not behave as a real
    drill requires. Returns the DrillResult on success.
    """
    try:
        checker(clean_input)
    except Exception as exc:
        raise AssertionError(
            f"drill {name!r}: control run raised {exc!r}, expected no exception"
        ) from exc

    try:
        checker(tampered_input)
    except expected_exception as exc:
        tampered_exception = type(exc)
    except Exception as exc:
        raise AssertionError(
            f"drill {name!r}: tampered run raised {type(exc).__name__}, "
            f"expected {expected_exception.__name__}"
        ) from exc
    else:
        raise AssertionError(
            f"drill {name!r}: tampered run did not raise, "
            f"expected {expected_exception.__name__}"
        )

    result = DrillResult(name=name, control_passed=True, tampered_exception=tampered_exception)
    if log is not None:
        log.results.append(result)
    return result
