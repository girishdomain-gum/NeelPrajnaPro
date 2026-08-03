"""Tests for ivf/mt5/export_xauusd_m5.py (WO-10 STEP 2, A-050/O-025).

Same testing shape as tests/scripts/test_probe_mt5_terminal.py: this
sandbox has the MetaTrader5 package (installed per O-024/D-034) but
tests never touch the real terminal -- every probe()-style call is
exercised against a fake mt5 module. What's proven here: the identity
and symbol-pin refusals are re-derived correctly (IND-1 -- this file
duplicates rather than imports scripts/probe_mt5_terminal.py's logic,
so it needs its own drill, not a shared one), that a refusal writes
NOTHING to disk, and that the CSV/provenance shape matches what the
real run needs.
"""

import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ivf" / "mt5"))
import export_xauusd_m5 as export_mod  # noqa: E402


class _FakeTerminalInfo:
    def __init__(self, path, company, name="Vantage Markets MT5"):
        self.path = path
        self.company = company
        self.name = name


class _FakeAccountInfo:
    server = "VantageMarkets-Demo"
    company = "Vantage Markets (Pty) Ltd"


class _FakeSymbolInfo:
    description = "Gold vs US Dollar"
    path = "Metals\\XAUUSD"
    digits = 2


class _FakeTick:
    def __init__(self, t):
        self.time = t


VANTAGE_INFO = _FakeTerminalInfo(
    path=export_mod.TERMINAL_INSTALL_DIR, company="Vantage Markets (Pty) Ltd",
)
OTHER_INFO = _FakeTerminalInfo(
    path=r"C:\Program Files\Some Other Broker MT5", company="Some Other Broker Ltd",
)


def test_identity_matches_vantage_accepts_pinned_install():
    ok, detail = export_mod._identity_matches_vantage(VANTAGE_INFO)
    assert ok is True
    assert "Vantage" in detail


def test_identity_matches_vantage_rejects_mismatch():
    ok, detail = export_mod._identity_matches_vantage(OTHER_INFO)
    assert ok is False
    assert "WRONG TERMINAL ATTACHED" in detail


def test_identity_matches_vantage_rejects_none():
    ok, detail = export_mod._identity_matches_vantage(None)
    assert ok is False
    assert "None" in detail


def test_symbol_is_pinned_accepts_exact():
    assert export_mod._symbol_is_pinned("XAUUSD") is True


def test_symbol_is_pinned_rejects_crp():
    assert export_mod._symbol_is_pinned("XAUUSD.crp") is False


def test_symbol_is_pinned_rejects_case_variant():
    assert export_mod._symbol_is_pinned("xauusd") is False


def test_symbol_is_pinned_rejects_near_miss():
    assert export_mod._symbol_is_pinned("XAUUSDm") is False


def test_export_refuses_non_pinned_symbol_before_connecting(monkeypatch, tmp_path):
    """The symbol-pin refusal must fire BEFORE connect() is ever called
    -- a caller must not be able to reach a real terminal handshake for
    an excluded symbol."""
    calls = []
    monkeypatch.setattr(export_mod, "connect", lambda: calls.append("connect"))
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 11, 1, tzinfo=UTC)
    try:
        export_mod.export("XAUUSD.crp", from_dt, to_dt, "test", str(tmp_path))
        raised = False
    except export_mod.ExportRefused as exc:
        raised = True
        assert "REFUSED" in str(exc)
        assert "XAUUSD.crp" in str(exc)
    assert raised
    assert calls == []  # connect() never reached
    assert list(tmp_path.iterdir()) == []  # nothing written


def test_connect_refuses_when_package_missing(monkeypatch):
    monkeypatch.setattr(export_mod, "mt5", None)
    try:
        export_mod.connect()
        raised = False
    except export_mod.ExportRefused as exc:
        raised = True
        assert "not installed" in str(exc)
    assert raised


def test_connect_refuses_when_terminal_exe_missing(monkeypatch):
    monkeypatch.setattr(export_mod, "mt5", object())
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", r"C:\nowhere\terminal64.exe")
    try:
        export_mod.connect()
        raised = False
    except export_mod.ExportRefused as exc:
        raised = True
        assert "not found" in str(exc)
    assert raised


class _FakeMT5:
    TIMEFRAME_M5 = 5

    def __init__(self, term_info, bars):
        self._term_info = term_info
        self._bars = bars
        self.shutdown_called = False

    def initialize(self, path=None):
        assert path == export_mod.TERMINAL_EXE
        return True

    def last_error(self):
        return (0, "no error")

    def terminal_info(self):
        return self._term_info

    def account_info(self):
        return _FakeAccountInfo()

    def symbol_info(self, symbol):
        return _FakeSymbolInfo()

    def symbol_info_tick(self, symbol):
        return _FakeTick(int(datetime.now(UTC).timestamp()))

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        return self._bars

    def shutdown(self):
        self.shutdown_called = True


def _fake_bar(t, o=4000.0, h=4001.0, low=3999.0, c=4000.5, tv=100, sp=20, rv=0):
    return {"time": t, "open": o, "high": h, "low": low, "close": c,
            "tick_volume": tv, "spread": sp, "real_volume": rv}


def test_export_refuses_when_wrong_terminal_attached(monkeypatch, tmp_path):
    fake = _FakeMT5(OTHER_INFO, bars=[_fake_bar(1_760_000_000)])
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 11, 1, tzinfo=UTC)
    try:
        export_mod.export("XAUUSD", from_dt, to_dt, "test", str(tmp_path))
        raised = False
    except export_mod.ExportRefused as exc:
        raised = True
        assert "WRONG TERMINAL ATTACHED" in str(exc)
    assert raised
    assert list(tmp_path.iterdir()) == []  # nothing written on refusal
    assert fake.shutdown_called is True  # still cleaned up


def test_export_refuses_when_no_bars_returned(monkeypatch, tmp_path):
    fake = _FakeMT5(VANTAGE_INFO, bars=[])
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 11, 1, tzinfo=UTC)
    try:
        export_mod.export("XAUUSD", from_dt, to_dt, "test", str(tmp_path))
        raised = False
    except export_mod.ExportRefused as exc:
        raised = True
        assert "no bars" in str(exc)
    assert raised
    assert list(tmp_path.iterdir()) == []


def test_export_writes_csv_and_provenance_on_success(monkeypatch, tmp_path):
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 10, 1, 1, tzinfo=UTC)
    t0 = int(from_dt.timestamp())
    bars = [_fake_bar(t0 + i * 300) for i in range(12)]  # 1 hour of M5 bars
    fake = _FakeMT5(VANTAGE_INFO, bars=bars)
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)

    prov = export_mod.export("XAUUSD", from_dt, to_dt, "unittest", str(tmp_path))

    assert prov["bars_written"] == 12
    assert prov["history_complete_vs_request"] == "YES"
    assert prov["gaps_gt_1_period"] == 0
    assert prov["symbol"] == "XAUUSD"
    assert prov["terminal_company"] == "Vantage Markets (Pty) Ltd"
    assert prov["account_server"] == "VantageMarkets-Demo"
    assert fake.shutdown_called is True

    csv_path = Path(prov["csv_path"])
    prov_path = Path(prov["provenance_path"])
    assert csv_path.exists()
    assert prov_path.exists()

    csv_lines = csv_path.read_text(encoding="ascii").splitlines()
    assert csv_lines[0] == (
        "time_open_sec,time_close_sec,open,high,low,close,"
        "tick_volume,spread,real_volume,dow"
    )
    assert len(csv_lines) == 13  # header + 12 bars
    first_row = csv_lines[1].split(",")
    assert int(first_row[0]) == t0
    assert int(first_row[1]) == t0 + 300  # close = open + period

    prov_text = prov_path.read_text(encoding="ascii")
    assert "QRF data export provenance (rev 1" in prov_text
    assert "symbol: XAUUSD" in prov_text
    assert "history_complete_vs_request: YES" in prov_text
    # fake tick is "now" (fresh) -> a real offset was computed, not nulled
    assert prov["server_vs_gmt_offset_seconds_NOW"] is not None
    assert prov["server_vs_gmt_offset_NOW_unavailable_reason"] is None

    # AM-07 item 3: the provenance twin carries the CSV's own sha256.
    assert prov["csv_sha256"] == export_mod._sha256_file(csv_path)
    assert f"csv_sha256: {prov['csv_sha256']}" in prov_text


def test_sha256_file_matches_hashlib_directly(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_bytes(b"time_open_sec,close\n1,2\n")
    import hashlib
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    assert export_mod._sha256_file(p) == expected


def test_sha256_file_detects_a_single_byte_change(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_bytes(b"time_open_sec,close\n1,2\n")
    original = export_mod._sha256_file(p)
    p.write_bytes(b"time_open_sec,close\n1,3\n")  # one byte different
    assert export_mod._sha256_file(p) != original


def test_out_dir_defaults_to_the_external_evidence_store(monkeypatch):
    """AM-07 item 2/6: the store is a single named constant, not a string
    repeated in two files -- main()'s CLI default must read FROM it."""
    captured = {}

    def _fake_export(symbol, date_from, date_to, tag, out_dir):
        captured["out_dir"] = out_dir
        return {"csv_path": "x", "provenance_path": "y", "bars_written": 0,
                 "first_bar_open_server": "", "last_bar_open_server": "",
                 "gaps_gt_1_period": 0, "history_complete_vs_request": "YES"}

    monkeypatch.setattr(export_mod, "export", _fake_export)
    export_mod.main(["2025-10-01", "2025-11-01"])  # no --out-dir given
    assert captured["out_dir"] == export_mod.EXTERNAL_EVIDENCE_STORE
    assert export_mod.EXTERNAL_EVIDENCE_STORE == r"F:\NeelPrajnaProData\incoming"


def test_export_does_not_report_nonsense_offset_from_a_stale_tick(monkeypatch, tmp_path):
    """F-EXPORT-1 (self-caught, real run, Sunday 2026-08-02): the market
    was closed, symbol_info_tick's last tick was from Friday's close, and
    naively subtracting wall-clock now from that stale tick produced
    server_vs_gmt_offset_seconds_NOW = -130725 (~-36h) -- physically
    impossible for a real broker. Fixed: a tick older than 5 minutes is
    treated as stale and the offset is NOT computed from it."""
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 10, 1, 1, tzinfo=UTC)
    t0 = int(from_dt.timestamp())
    bars = [_fake_bar(t0 + i * 300) for i in range(12)]

    class _StaleTickMT5(_FakeMT5):
        def symbol_info_tick(self, symbol):
            # a tick 2 days old -- simulates the real Sunday-market-closed case
            stale = int(datetime.now(UTC).timestamp()) - 2 * 86400
            return _FakeTick(stale)

    fake = _StaleTickMT5(VANTAGE_INFO, bars=bars)
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)

    prov = export_mod.export("XAUUSD", from_dt, to_dt, "unittest", str(tmp_path))

    assert prov["server_vs_gmt_offset_seconds_NOW"] is None
    assert "stale" in prov["server_vs_gmt_offset_NOW_unavailable_reason"].lower()
    # sanity: no wildly-implausible multi-hour value leaked through anywhere
    assert prov["server_vs_gmt_offset_seconds_NOW"] != -130725


def test_export_flags_incomplete_history_but_still_writes(monkeypatch, tmp_path):
    """QRF_Data_Export.mq5's own behaviour, mirrored: an incomplete pull
    is reported LOUDLY, not silently withheld -- the file still lands so
    a human can see exactly what was and wasn't covered."""
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 10, 20, tzinfo=UTC)
    # bars start 10 days after the requested start -- well past the 7-day slack
    late_start = int(datetime(2025, 10, 11, tzinfo=UTC).timestamp())
    bars = [_fake_bar(late_start + i * 300) for i in range(5)]
    fake = _FakeMT5(VANTAGE_INFO, bars=bars)
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)

    prov = export_mod.export("XAUUSD", from_dt, to_dt, "unittest", str(tmp_path))

    assert prov["history_complete_vs_request"] == "NO -- INCOMPLETE"
    assert Path(prov["csv_path"]).exists()  # still written, per QRF_Data_Export.mq5's own model


def test_export_reports_gap_census(monkeypatch, tmp_path):
    from_dt = datetime(2025, 10, 1, tzinfo=UTC)
    to_dt = datetime(2025, 10, 1, 1, tzinfo=UTC)
    t0 = int(from_dt.timestamp())
    bars = [_fake_bar(t0), _fake_bar(t0 + 300), _fake_bar(t0 + 300 + 3600)]  # one 1h gap
    fake = _FakeMT5(VANTAGE_INFO, bars=bars)
    monkeypatch.setattr(export_mod, "mt5", fake)
    monkeypatch.setattr(export_mod, "TERMINAL_EXE", __file__)

    prov = export_mod.export("XAUUSD", from_dt, to_dt, "unittest", str(tmp_path))
    assert prov["gaps_gt_1_period"] == 1
    assert prov["max_gap_seconds"] == 3600


def test_dow_of_matches_expected_convention():
    # 2025-10-01 is a Wednesday -> weekday()=2 -> (2+1)%7 = 3
    t = int(datetime(2025, 10, 1, tzinfo=UTC).timestamp())
    assert export_mod._dow_of(t) == 3
    # 2025-10-05 is a Sunday -> weekday()=6 -> (6+1)%7 = 0
    t_sun = int(datetime(2025, 10, 5, tzinfo=UTC).timestamp())
    assert export_mod._dow_of(t_sun) == 0


def test_main_returns_nonzero_and_prints_reason_on_refusal(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(export_mod, "mt5", None)
    code = export_mod.main(["2025-10-01", "2025-11-01", "--out-dir", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "EXPORT REFUSED" in out
    assert list(tmp_path.iterdir()) == []


def test_module_importable_standalone():
    importlib.reload(export_mod)
    assert hasattr(export_mod, "export")
    assert hasattr(export_mod, "main")
