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


def test_pinned_identity_constants_match_adoption_adaptations_doc():
    """A-044 point 3: the pin must not drift from ADOPTION_ADAPTATIONS.md
    again. Rather than parsing that doc's free-text table cell into
    structured config (fragile against innocuous wording edits), this
    pins the relationship the other way: the doc's recorded row must
    still CONTAIN the exact strings this file hardcodes as constants —
    if a future repin edits one and not the other, this fails loudly."""
    doc_path = Path(__file__).resolve().parents[2] / "ADOPTION_ADAPTATIONS.md"
    text = doc_path.read_text(encoding="utf-8")
    assert probe_mod.TERMINAL_INSTALL_DIR in text
    assert probe_mod.SUPERSEDED_TERMINAL_INSTALL_DIR in text
    # the doc records the company with its full legal suffix; the code's
    # token is a deliberately shorter case-insensitive substring of it
    assert probe_mod.VANTAGE_COMPANY_TOKEN in text.lower()


# --- A-039 VANTAGE-ONLY identity check: drilled RED before trusted GREEN ---

class _FakeTerminalInfo:
    def __init__(self, path, company, connected=True, trade_allowed=False):
        self.path = path
        self.company = company
        self.connected = connected
        self.trade_allowed = trade_allowed


VANTAGE_INFO = _FakeTerminalInfo(
    path=probe_mod.TERMINAL_INSTALL_DIR, company="Vantage Markets (Pty) Ltd",
)
# A-039 rule 4: no OTHER broker's real name/path/server ever appears in
# this repo, including in a drill fixture — a generic placeholder proves
# the refusal on ANY mismatch just as well as a real name would.
OTHER_BROKER_INFO = _FakeTerminalInfo(
    path=r"C:\Program Files\Some Other Broker MT5", company="Some Other Broker Ltd",
)
# A-044: the OLD Vantage install is now a plausible-but-unpinned
# neighbour, not a competitor — same brand family, wrong build, wrong
# path. This is exactly the case an identity check exists to catch, so
# it gets its own drill distinct from OTHER_BROKER_INFO above.
SUPERSEDED_VANTAGE_INFO = _FakeTerminalInfo(
    path=probe_mod.SUPERSEDED_TERMINAL_INSTALL_DIR, company="Vantage International Group Limited",
)


def test_identity_matches_vantage_accepts_pinned_install():
    ok, detail = probe_mod._identity_matches_vantage(VANTAGE_INFO)
    assert ok is True
    assert "Vantage" in detail


def test_identity_matches_vantage_rejects_wrong_path_and_company():
    ok, detail = probe_mod._identity_matches_vantage(OTHER_BROKER_INFO)
    assert ok is False
    assert "WRONG TERMINAL ATTACHED" in detail
    assert "Some Other Broker" in detail


def test_identity_matches_vantage_rejects_right_path_wrong_company():
    mismatched = _FakeTerminalInfo(
        path=probe_mod.TERMINAL_INSTALL_DIR, company="Some Other Broker Ltd",
    )
    ok, _ = probe_mod._identity_matches_vantage(mismatched)
    assert ok is False


def test_identity_matches_vantage_rejects_right_company_wrong_path():
    mismatched = _FakeTerminalInfo(
        path=r"C:\Somewhere\Else", company="Vantage Markets (Pty) Ltd",
    )
    ok, _ = probe_mod._identity_matches_vantage(mismatched)
    assert ok is False


def test_identity_matches_vantage_rejects_none():
    ok, detail = probe_mod._identity_matches_vantage(None)
    assert ok is False
    assert "None" in detail


def test_identity_matches_vantage_rejects_superseded_install(monkeypatch):
    """A-044 drill: the OLD Vantage install must now be treated as a
    refusal like any other mismatch, even though it still says
    'Vantage' — the pin decides which install is THIS project's, not
    the brand name alone."""
    ok, detail = probe_mod._identity_matches_vantage(SUPERSEDED_VANTAGE_INFO)
    assert ok is False
    assert "WRONG TERMINAL ATTACHED" in detail


def test_pin_and_superseded_pin_are_distinct_paths():
    assert probe_mod.TERMINAL_INSTALL_DIR != probe_mod.SUPERSEDED_TERMINAL_INSTALL_DIR


class _FakeMT5:
    """Simulates the MetaTrader5 module surface probe() touches. Tracks
    which data-reading calls actually happened, so the drill can prove
    the identity refusal reads NOTHING beyond terminal_info()."""

    def __init__(self, term_info, init_ok=True, init_error=(0, "no error")):
        self._term_info = term_info
        self._init_ok = init_ok
        self._init_error = init_error
        self.symbols_get_called = False
        self.account_info_called = False
        self.copy_rates_called = False
        self.shutdown_called = False
        self.TIMEFRAME_M5 = 5

    def initialize(self, path=None):
        assert path == probe_mod.TERMINAL_EXE  # A-039 rule 2: path always supplied
        return self._init_ok

    def last_error(self):
        return self._init_error

    def terminal_info(self):
        return self._term_info

    def account_info(self):
        self.account_info_called = True
        return object()

    def symbols_get(self):
        self.symbols_get_called = True

        class Sym:
            name = "XAUUSDm"
        return [Sym()]

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        self.copy_rates_called = True
        return [object()] * count

    def shutdown(self):
        self.shutdown_called = True


def test_probe_refuses_and_reads_nothing_when_wrong_terminal_attached(monkeypatch):
    fake = _FakeMT5(OTHER_BROKER_INFO)
    monkeypatch.setattr(probe_mod, "mt5", fake)
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", __file__)  # any real file, exists-check passes
    monkeypatch.setattr(probe_mod, "_running_pids_by_path", lambda exe: set())
    monkeypatch.setattr(probe_mod, "LAUNCH_WAIT_SECONDS", 0)  # skip the poll wait in tests

    report = probe_mod.probe("XAUUSD")

    assert report["vantage_identity_ok"] is False
    assert "WRONG TERMINAL ATTACHED" in report["vantage_identity_detail"]
    assert "REFUSED" in report["initialize_error"]
    # the drill's whole point: nothing downstream of the identity check ran
    assert fake.account_info_called is False
    assert fake.symbols_get_called is False
    assert fake.copy_rates_called is False
    assert report["account_present"] is None
    assert report["matching_symbols"] == []
    assert report["depth_check"] == {}
    # leave-as-found / shutdown discipline still runs on the refusal path
    assert fake.shutdown_called is True


def test_probe_green_control_reads_data_when_vantage_identity_matches(monkeypatch):
    fake = _FakeMT5(VANTAGE_INFO)
    monkeypatch.setattr(probe_mod, "mt5", fake)
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", __file__)
    monkeypatch.setattr(probe_mod, "_running_pids_by_path", lambda exe: set())
    monkeypatch.setattr(probe_mod, "LAUNCH_WAIT_SECONDS", 0)

    report = probe_mod.probe("XAUUSD")

    assert report["vantage_identity_ok"] is True
    assert report["initialize_error"] is None
    assert fake.account_info_called is True
    assert fake.symbols_get_called is True
    assert fake.copy_rates_called is True
    assert report["matching_symbols"] == ["XAUUSDm"]
    assert report["depth_check"] == {"XAUUSDm": 10}
    assert fake.shutdown_called is True


def test_probe_refuses_superseded_vantage_install(monkeypatch):
    """A-044 end-to-end drill: a terminal at the OLD pinned path answers
    (plausible — it still says 'Vantage') and the probe must refuse it
    exactly like any other mismatch, reading nothing further."""
    fake = _FakeMT5(SUPERSEDED_VANTAGE_INFO)
    monkeypatch.setattr(probe_mod, "mt5", fake)
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", __file__)
    monkeypatch.setattr(probe_mod, "_running_pids_by_path", lambda exe: set())
    monkeypatch.setattr(probe_mod, "LAUNCH_WAIT_SECONDS", 0)

    report = probe_mod.probe("XAUUSD")

    assert report["vantage_identity_ok"] is False
    assert "WRONG TERMINAL ATTACHED" in report["vantage_identity_detail"]
    assert fake.account_info_called is False
    assert fake.symbols_get_called is False
    assert fake.copy_rates_called is False


def test_fprobe1_orphan_detected_and_closed_when_initialize_fails_after_launch(monkeypatch):
    """F-PROBE-1 (A-043) drill: initialize() STARTS the terminal and THEN
    fails (e.g. no stored auto-login — exactly JOB-018's real finding).
    Before the fix, the launch-detection re-scan only ran on the success
    path, so we_launched_it/closed_by_probe stayed False even though a
    real orphaned process was left running. This proves the fix: the
    re-scan (and therefore the leave-as-found close) runs on the FAILURE
    path too."""
    fake = _FakeMT5(VANTAGE_INFO, init_ok=False, init_error=(-6, "Terminal: Authorization failed"))
    monkeypatch.setattr(probe_mod, "mt5", fake)
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", __file__)
    monkeypatch.setattr(probe_mod, "LAUNCH_WAIT_SECONDS", 5)
    monkeypatch.setattr(probe_mod, "LAUNCH_POLL_SECONDS", 0)

    calls = {"n": 0}
    launched_pid = 424242

    def fake_pid_scan(exe):
        calls["n"] += 1
        # 1st call = pre-launch scan (before initialize): nothing running.
        # every call after = the terminal initialize() itself started.
        return set() if calls["n"] == 1 else {launched_pid}

    monkeypatch.setattr(probe_mod, "_running_pids_by_path", fake_pid_scan)
    killed = []
    monkeypatch.setattr(probe_mod, "_kill_pids", lambda pids: killed.extend(pids))

    report = probe_mod.probe("XAUUSD")

    assert report["initialize_ok"] is False
    assert "Authorization failed" in report["initialize_error"]
    # the fix: launch was detected DESPITE the auth failure...
    assert report["we_launched_it"] is True
    # ...and leave-as-found closed the orphan rather than abandoning it
    assert report["closed_by_probe"] is True
    assert killed == [launched_pid]
    # identity check never runs — initialize() itself failed first
    assert report["vantage_identity_ok"] is None


def test_print_report_red_and_refused_detail_shown_on_wrong_terminal(monkeypatch):
    fake = _FakeMT5(OTHER_BROKER_INFO)
    monkeypatch.setattr(probe_mod, "mt5", fake)
    monkeypatch.setattr(probe_mod, "TERMINAL_EXE", __file__)
    monkeypatch.setattr(probe_mod, "_running_pids_by_path", lambda exe: set())
    monkeypatch.setattr(probe_mod, "LAUNCH_WAIT_SECONDS", 0)
    report = probe_mod.probe("XAUUSD")

    buf = io.StringIO()
    with redirect_stdout(buf):
        green = probe_mod._print_report(report)
    assert green is False
    out = buf.getvalue()
    assert "RED" in out
    assert "WRONG TERMINAL ATTACHED" in out
    # still no credential-shaped terms leak through the refusal path
    for term in ("login", "password", "balance", "server="):
        assert term not in out.lower()
