"""Tests for scripts/probe_mt5_terminal.py (WO-10 STEP 1, A-038).

This sandbox has no MetaTrader5 package and no live terminal, so the
real GREEN path cannot be exercised here — that only happens in the
Owner's job run against the real terminal. What IS testable, and what
these tests hold to: the probe never crashes when the package is
missing or the terminal is absent (it reports, per the design contract
that account fields are never printed, and that the PID-matching parser
handles CIM/tasklist output correctly, which is real, exercisable logic
independent of a live terminal.
"""

import importlib
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import probe_mt5_terminal as probe_mod  # noqa: E402


def test_no_mt5_package_reports_blocker_not_crash(monkeypatch):
    monkeypatch.setattr(probe_mod, "mt5", None)
    report = probe_mod.probe("XAUUSD")
    assert report["mt5_package_available"] is False
    assert report["initialize_ok"] is False
    assert "not installed" in report["initialize_error"]
    assert report["account_present"] is None
    assert report["matching_symbols"] == []


def test_terminal_exe_missing_reports_blocker(monkeypatch):
    monkeypatch.setattr(probe_mod, "mt5", object())  # package "present"
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", r"C:\definitely\not\here\terminal64.exe")
    report = probe_mod.probe("XAUUSD")
    assert report["terminal_exe_exists"] is False
    assert "not found" in report["initialize_error"]


def test_real_sandbox_has_no_mt5_package():
    """Ground truth for this venv, asserted so a future dependency
    change is caught rather than silently changing what this suite
    covers."""
    assert probe_mod.mt5 is None


def test_report_never_contains_account_login_or_server_strings(monkeypatch):
    """The report dict's OWN keys are the security contract: only
    presence/connection-state fields exist, never raw account/login/
    server/balance fields — this holds regardless of mock realism."""
    monkeypatch.setattr(probe_mod, "mt5", None)
    report = probe_mod.probe("XAUUSD")
    forbidden = {"login", "server", "balance", "password", "account_number"}
    assert forbidden.isdisjoint(report.keys())


def test_print_report_output_excludes_forbidden_terms(monkeypatch):
    monkeypatch.setattr(probe_mod, "mt5", None)
    report = probe_mod.probe("XAUUSD")
    buf = io.StringIO()
    with redirect_stdout(buf):
        probe_mod._print_report(report)
    out = buf.getvalue().lower()
    for term in ("login", "password", "balance", "server="):
        assert term not in out


def test_print_report_red_when_package_missing(monkeypatch):
    monkeypatch.setattr(probe_mod, "mt5", None)
    report = probe_mod.probe("XAUUSD")
    buf = io.StringIO()
    with redirect_stdout(buf):
        green = probe_mod._print_report(report)
    assert green is False
    assert "RED" in buf.getvalue()


def test_main_exits_nonzero_when_probe_red(monkeypatch, capsys):
    monkeypatch.setattr(probe_mod, "mt5", None)
    code = probe_mod.main([])
    assert code == 1


def test_running_pids_by_path_parses_cim_output(monkeypatch, tmp_path):
    target = tmp_path / "terminal64.exe"
    target.write_bytes(b"")

    class FakeResult:
        returncode = 0
        stdout = f"1234|{target}\n5678|C:\\Other\\terminal64.exe\n"

    def fake_run(cmd, **kwargs):
        assert cmd[0] == "powershell"
        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    pids = probe_mod._running_pids_by_path(str(target))
    assert pids == {1234}


def test_running_pids_by_path_falls_back_to_tasklist_on_cim_failure(monkeypatch, tmp_path):
    target = tmp_path / "terminal64.exe"
    target.write_bytes(b"")
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd[0])
        if cmd[0] == "powershell":
            raise OSError("powershell not available")
        assert cmd[0] == "tasklist"

        class FakeResult:
            returncode = 0
            stdout = '"terminal64.exe","9999","Console","1","50,000 K"\n'

        return FakeResult()

    monkeypatch.setattr(subprocess, "run", fake_run)
    pids = probe_mod._running_pids_by_path(str(target))
    assert pids == {9999}
    assert calls == ["powershell", "tasklist"]


def test_running_pids_by_path_returns_empty_set_when_both_fail(monkeypatch, tmp_path):
    target = tmp_path / "terminal64.exe"

    def fake_run(cmd, **kwargs):
        raise OSError("no shell available")

    monkeypatch.setattr(subprocess, "run", fake_run)
    pids = probe_mod._running_pids_by_path(str(target))
    assert pids == set()


def test_kill_pids_swallows_exceptions(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise OSError("taskkill missing")

    monkeypatch.setattr(subprocess, "run", fake_run)
    probe_mod._kill_pids({111, 222})  # must not raise


def test_module_importable_standalone():
    importlib.reload(probe_mod)
    assert hasattr(probe_mod, "probe")
    assert hasattr(probe_mod, "main")
