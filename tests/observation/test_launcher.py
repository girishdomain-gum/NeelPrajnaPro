"""Tests for the launcher's pure, terminal-independent parts.

`run_export()` itself talks to a live Vantage terminal and cannot be
exercised in CI (no terminal exists there, and this module intentionally
has no Python MT5-package dependency to even mock) -- it is exercised by
hand; see the sprint report for that real run's evidence. Everything
tested here is the part that decides correctness, not the part that
merely talks to Windows.
"""

from qrf.errors import TerminalMismatch
from qrf.kernel.observation import launcher


def test_build_startup_ini_is_utf16le_with_bom(tmp_path):
    ini_path = tmp_path / "run.ini"
    launcher.build_startup_ini(ini_path, "XAUUSD", "M5")
    raw = ini_path.read_bytes()
    assert raw.startswith(b"\xff\xfe")  # UTF-16LE BOM
    text = raw.decode("utf-16-le")
    assert "[StartUp]" in text
    assert f"Script={launcher.SCRIPT_REL_PATH}" in text
    assert "Symbol=XAUUSD" in text
    assert "Period=M5" in text
    assert "ShutdownTerminal=1" in text


def test_terminal_running_returns_a_result_without_raising():
    # Cross-platform smoke test: on a machine/CI runner with no
    # `powershell` at all, the broad except still returns a safe,
    # erring-strict fallback rather than crashing.
    result = launcher.terminal_running()
    assert result.path in ("cim", "fallback")
    assert isinstance(result.hits, tuple)


def test_terminal_running_exercises_the_real_cim_path_on_windows():
    """A-011: proof, not an argument from the mechanism. CI now runs on
    windows-latest (A-010), where PowerShell/CIM is genuinely present --
    this asserts the primary path actually ran, rather than "arguing
    strongly" that it must have.
    """
    import sys

    if sys.platform != "win32":
        import pytest as _pytest

        _pytest.skip("this proof only applies where PowerShell/CIM can run at all")
    result = launcher.terminal_running()
    assert result.path == "cim", (
        "expected the real PowerShell/CIM path to run on Windows; got the "
        "erring-strict fallback instead -- that is a FINDING (A-011), not "
        "a passing test"
    )


def _base_meta(**overrides) -> dict:
    base = {
        "symbol": "XAUUSD",
        "server": launcher.PINNED_SERVER,
        "account": launcher.PINNED_ACCOUNT,
        "broker": launcher.PINNED_BROKER,
    }
    base.update(overrides)
    return base


def test_check_pinned_facts_passes_on_exact_match():
    launcher._check_pinned_facts(_base_meta())  # noqa: SLF001 -- deliberate


def test_check_pinned_facts_refuses_wrong_server():
    """This is the exact failure mode that occurred mid-sprint: a
    different broker's terminal (Winprofx-Live) answering in place of the
    pinned Vantage Markets Demo. Proven here as a drill, not just fixed.
    """
    try:
        launcher._check_pinned_facts(  # noqa: SLF001 -- deliberate
            _base_meta(
                server="Winprofx-Live",
                account=183992,
                broker="Winprofx Limited",
            )
        )
    except TerminalMismatch as exc:
        assert exc.field == "server"
        assert exc.expected == launcher.PINNED_SERVER
        assert exc.actual == "Winprofx-Live"
    else:
        raise AssertionError("expected TerminalMismatch")


def test_check_pinned_facts_refuses_wrong_symbol():
    try:
        launcher._check_pinned_facts(_base_meta(symbol="XAUUSD.crp"))  # noqa: SLF001
    except TerminalMismatch as exc:
        assert exc.field == "symbol"
    else:
        raise AssertionError("expected TerminalMismatch")
