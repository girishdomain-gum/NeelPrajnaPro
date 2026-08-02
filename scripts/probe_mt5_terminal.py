#!/usr/bin/env python3
"""probe_mt5_terminal.py — WO-10 STEP 1 (A-038): read-only MT5 terminal
capability probe. Answers "does live-session automation work on this
terminal today?" by measuring, not assuming. Writes NO file, touches no
journal, pulls no bars beyond a small depth check.

Launch/detect/close mechanics quarried (mechanics only, per A-038/O-020)
from F:\\Fable\\tools\\np_agent.py's _terminal_running(): match the pinned
executable by PATH via Get-CimInstance, tasklist as a strict fallback.
NOT a port — that source launches in strategy-tester /config mode; this
probe uses MetaTrader5.initialize() live-session mode (A-038's own
distinction). The job system, bridge, and tester-config mode are
deliberately NOT reused.

SECURITY: never prints an account number, login, server, or balance —
presence/connection-state only. HUMAN-ONLY lines (chart attach, arming,
order/position/account action) are never called, not even unreachable.
Leave-as-found: closes the terminal only if THIS run launched it.

VANTAGE ONLY, ALWAYS (A-039/A-040, O-009/O-021): MetaTrader5.initialize()
attaches to WHATEVER terminal is already running if one is, regardless
of the `path` argument — so a probe/export started while a DIFFERENT
broker's terminal (the Owner runs another one for a separate, unrelated
project) is open can silently read and label THAT broker's data as
Vantage. This is treated as evidence contamination, not a config error.
The identity check below runs BEFORE any data read (symbols, bars,
account) and REFUSES LOUDLY — reads nothing, writes nothing, shuts down
per leave-as-found — the moment the connected terminal's own
terminal_info() does not match the pinned Vantage install. Per A-039
rule 4, no other broker's name, path, symbol suffix, server name, or
credential is ever referenced anywhere in this repo, including here.

Usage: python scripts/probe_mt5_terminal.py [SYMBOL_PREFIX]
  SYMBOL_PREFIX defaults to "XAUUSD".

PIN HISTORY (A-044/O-022): the Owner reinstalled the Vantage terminal
under a new build; the install path changed and the old one is now a
DIFFERENT, unpinned installation that happens to still say "Vantage" —
exactly the plausible-but-wrong neighbour an identity check exists to
catch, not a broker mismatch. Both constants below are read off the
Owner's own screenshots (ADOPTION_ADAPTATIONS.md's "EA folder / MT5
terminal / TERMID" row is the single recorded source — test_probe_
mt5_terminal.py's drift guard fails if this file and that doc ever
disagree again).
  CURRENT (pinned):  C:\\Program Files\\Vantage Markets MT5 Terminal\\
  SUPERSEDED (must now REFUSE): C:\\Program Files\\Vantage International MT5\\

SYMBOL PIN (A-047/O-023): the Owner ruled directly, before any property
comparison was run — XAUUSD only, XAUUSD.crp NEVER. Exact-match, not a
prefix: `XAUUSD*` is fine for DISCOVERY (this probe still enumerates
every matching symbol so the Owner can see what exists), but reading,
exporting, or ingesting bars for anything other than the exact pinned
string is refused before any data is read for it — same hard-stop shape
as the Vantage identity check.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import UTC, datetime

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

TERMINAL_INSTALL_DIR = r"C:\Program Files\Vantage Markets MT5 Terminal"
TERMINAL_EXE = TERMINAL_INSTALL_DIR + r"\terminal64.exe"
VANTAGE_COMPANY_TOKEN = "vantage markets"  # case-insensitive substring of terminal_info().company
# Superseded install (O-010's original pin) — kept ONLY so the identity
# check's "plausible-but-unpinned neighbour" drill has a real, project-
# owned path to test against. Not a competitor's name (A-039 rule 4
# concerns OTHER brokers; this is this project's own retired pin).
SUPERSEDED_TERMINAL_INSTALL_DIR = r"C:\Program Files\Vantage International MT5"
SYMBOL_PIN = "XAUUSD"  # O-023, EXACT string — never a prefix, never .crp
PROBE_TIMEFRAME = "M5"
PROBE_BAR_COUNT = 10  # depth-presence check only, never a real pull
LAUNCH_WAIT_SECONDS = 30
LAUNCH_POLL_SECONDS = 1
MAX_HISTORY_PROBE_BARS = 200_000  # generous cap for an "earliest available" walk-back
# The DST-pin candidate span (A-035/A-047) — bracketed with margin either
# side of the 2025-10-26 EU and 2025-11-02 US transitions. UTC boundaries
# here are ONLY a coarse coverage probe (does data exist in this window
# at all) — they make no zone claim; that determination is a later,
# separate step once real data is in hand.
TARGET_SPAN_START_UTC = datetime(2025, 10, 15, tzinfo=UTC)
TARGET_SPAN_END_UTC = datetime(2025, 11, 15, tzinfo=UTC)


def _identity_matches_vantage(term_info):
    """A-039's binding identity check: the CONNECTED terminal's own
    reported path and company must match the pinned Vantage install.
    Returns (ok, reason). initialize()'s `path` argument only requests a
    terminal — MT5 attaches to whatever is already running if one is —
    so this is the only real proof of whose data is about to be read."""
    if term_info is None:
        return False, "terminal_info() returned None — cannot verify identity, refusing"
    path = getattr(term_info, "path", "") or ""
    company = getattr(term_info, "company", "") or ""
    path_ok = os.path.normcase(os.path.abspath(path)) == os.path.normcase(
        os.path.abspath(TERMINAL_INSTALL_DIR)
    )
    company_ok = VANTAGE_COMPANY_TOKEN in company.lower()
    if path_ok and company_ok:
        return True, f"path={path!r} company={company!r}"
    return False, (
        f"WRONG TERMINAL ATTACHED — path={path!r} company={company!r}, "
        f"expected install {TERMINAL_INSTALL_DIR!r} "
        f"and company containing {VANTAGE_COMPANY_TOKEN!r}"
    )


def _symbol_matches_pin(symbol):
    """A-047's binding symbol pin: EXACT match only, never a prefix and
    never a near-miss/case-variant. A `XAUUSD*` scan is fine for
    discovery (matching_symbols below still lists everything found —
    that is inventory, not use); this gate is what stands between
    discovery and actually reading a symbol's bars. Returns (ok, reason)
    in the same shape as _identity_matches_vantage, for the same reason:
    refuse loudly, name what was found, read nothing."""
    if symbol == SYMBOL_PIN:
        return True, f"symbol={symbol!r} matches the pin"
    return False, (
        f"REFUSED: symbol={symbol!r} is not the pinned symbol {SYMBOL_PIN!r} — no data read"
    )


def _measure_m5_extent(symbol):
    """Read-only M5 history extent measurement for the PINNED symbol
    only — the caller is responsible for gating via _symbol_matches_pin
    before ever calling this. No file written, no journal touch; this
    is a depth/coverage measurement, not the STEP 2 export. Reports raw
    facts (earliest/latest bar, target-span bar count) rather than a
    judged "covered" verdict — A-047: 'report the numbers and I will
    rule on whether the span stands or must move'."""
    extent = {
        "symbol": symbol,
        "earliest_bar_utc": None,
        "latest_bar_utc": None,
        "target_span_start_utc": TARGET_SPAN_START_UTC.isoformat(),
        "target_span_end_utc": TARGET_SPAN_END_UTC.isoformat(),
        "target_span_bar_count": None,
        "target_span_first_bar_utc": None,
        "target_span_last_bar_utc": None,
        "error": None,
    }
    timeframe = getattr(mt5, f"TIMEFRAME_{PROBE_TIMEFRAME}")
    try:
        walk = mt5.copy_rates_from_pos(symbol, timeframe, 0, MAX_HISTORY_PROBE_BARS)
        if walk is not None and len(walk) > 0:
            extent["earliest_bar_utc"] = _bar_time_to_iso(walk[0])
            extent["latest_bar_utc"] = _bar_time_to_iso(walk[-1])
    except Exception as exc:  # noqa: BLE001 — report, don't crash the probe
        extent["error"] = f"extent walk-back failed: {exc}"
        return extent

    try:
        span_bars = mt5.copy_rates_range(
            symbol, timeframe, TARGET_SPAN_START_UTC, TARGET_SPAN_END_UTC,
        )
        extent["target_span_bar_count"] = 0 if span_bars is None else len(span_bars)
        if span_bars is not None and len(span_bars) > 0:
            extent["target_span_first_bar_utc"] = _bar_time_to_iso(span_bars[0])
            extent["target_span_last_bar_utc"] = _bar_time_to_iso(span_bars[-1])
    except Exception as exc:  # noqa: BLE001
        extent["error"] = f"target-span range failed: {exc}"

    return extent


def _bar_time_to_iso(bar):
    return datetime.fromtimestamp(int(bar["time"]), tz=UTC).isoformat()


def _running_pids_by_path(target_exe):
    """Return the set of PIDs whose executable path matches target_exe
    exactly, matched via Get-CimInstance; falls back to a strict
    tasklist-by-name scan (path unverified) if the CIM query fails —
    erring toward "assume running" rather than "assume free"."""
    target = os.path.normcase(os.path.abspath(target_exe))
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\""
             " | ForEach-Object { \"$($_.ProcessId)|$($_.ExecutablePath)\" }"],
            capture_output=True, text=True, timeout=60,
        )
        if r.returncode == 0:
            pids = set()
            for line in (r.stdout or "").splitlines():
                if "|" not in line:
                    continue
                pid, _, path = line.strip().partition("|")
                if path and os.path.normcase(os.path.abspath(path)) == target and pid.isdigit():
                    pids.add(int(pid))
            return pids
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq terminal64.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=30,
        )
        pids = set()
        for line in (r.stdout or "").splitlines():
            if "terminal64" not in line.lower():
                continue
            parts = [p.strip('"') for p in line.strip().split('","')]
            if len(parts) >= 2 and parts[1].isdigit():
                pids.add(int(parts[1]))
        return pids
    except Exception:
        return set()


def _kill_pids(pids):
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                            capture_output=True, text=True, timeout=30)
        except Exception:
            pass


def probe(symbol_prefix="XAUUSD"):
    """Returns a plain-dict report. Never raises for expected real-world
    conditions (package missing, terminal missing, init failure, symbol
    absent) — those are reported fields, not exceptions."""
    report = {
        "mt5_package_available": mt5 is not None,
        "terminal_exe": TERMINAL_EXE,
        "terminal_exe_exists": os.path.isfile(TERMINAL_EXE),
        "pre_launch_running_pids": [],
        "we_launched_it": False,
        "initialize_ok": False,
        "initialize_error": None,
        "vantage_identity_ok": None,
        "vantage_identity_detail": None,
        "terminal_connected": None,
        "trade_allowed": None,
        "account_present": None,
        "matching_symbols": [],
        "symbol_pin": SYMBOL_PIN,
        "depth_check": {},
        "m5_extent": None,
        "closed_by_probe": False,
    }

    if mt5 is None:
        report["initialize_error"] = "MetaTrader5 package not installed (pip install .[mt5])"
        return report
    if not report["terminal_exe_exists"]:
        report["initialize_error"] = f"pinned terminal64.exe not found at {TERMINAL_EXE}"
        return report

    pre_pids = _running_pids_by_path(TERMINAL_EXE)
    report["pre_launch_running_pids"] = sorted(pre_pids)

    try:
        # A-039, rule 2: NEVER call initialize() without the pinned path —
        # a bare initialize() attaches to whatever is running.
        ok = mt5.initialize(path=TERMINAL_EXE)
        report["initialize_ok"] = bool(ok)

        # F-PROBE-1 (A-043): initialize() can START the terminal process
        # and THEN fail (e.g. no stored auto-login) — the launch already
        # happened regardless of ok/not-ok, so this re-scan must run on
        # EVERY exit from initialize(), not only the success path, or a
        # failed run leaves an undetected, unclosed orphan.
        new_pids = set()
        deadline = time.time() + LAUNCH_WAIT_SECONDS
        while time.time() < deadline:
            now_pids = _running_pids_by_path(TERMINAL_EXE)
            new_pids = now_pids - pre_pids
            if new_pids or now_pids:
                break
            time.sleep(LAUNCH_POLL_SECONDS)
        report["we_launched_it"] = bool(new_pids) and not pre_pids
        report["_new_pids_for_shutdown"] = sorted(new_pids) if report["we_launched_it"] else []

        if not ok:
            err = mt5.last_error()
            report["initialize_error"] = f"{err}"
            return report

        # A-039, rule 1: IDENTITY CHECK BEFORE ANY DATA READ. initialize()
        # succeeding proves SOME terminal answered — not that it is
        # Vantage. Refuse loudly and read nothing further if it is not.
        term_info = mt5.terminal_info()
        identity_ok, identity_detail = _identity_matches_vantage(term_info)
        report["vantage_identity_ok"] = identity_ok
        report["vantage_identity_detail"] = identity_detail
        if not identity_ok:
            report["initialize_error"] = f"REFUSED: {identity_detail}"
            return report

        report["terminal_connected"] = bool(getattr(term_info, "connected", False))
        report["trade_allowed"] = bool(getattr(term_info, "trade_allowed", False))

        acct_info = mt5.account_info()
        report["account_present"] = acct_info is not None  # presence only, no fields

        all_symbols = mt5.symbols_get() or ()
        prefix = symbol_prefix.upper()
        matches = sorted(s.name for s in all_symbols if s.name.upper().startswith(prefix))
        report["matching_symbols"] = matches

        timeframe = getattr(mt5, f"TIMEFRAME_{PROBE_TIMEFRAME}")
        for sym in matches:
            # A-047: exact-match refusal BEFORE any bar read. The prefix
            # scan above is discovery only — XAUUSD.crp is listed in
            # matching_symbols (inventory) but its bars are never read.
            pin_ok, pin_detail = _symbol_matches_pin(sym)
            if not pin_ok:
                report["depth_check"][sym] = pin_detail
                continue
            try:
                bars = mt5.copy_rates_from_pos(sym, timeframe, 0, PROBE_BAR_COUNT)
                report["depth_check"][sym] = 0 if bars is None else len(bars)
            except Exception as exc:  # noqa: BLE001 — report, don't crash the probe
                report["depth_check"][sym] = f"error: {exc}"

        if SYMBOL_PIN in matches:
            report["m5_extent"] = _measure_m5_extent(SYMBOL_PIN)

    finally:
        if mt5 is not None:
            mt5.shutdown()
        new_pids_to_close = report.pop("_new_pids_for_shutdown", [])
        if report["we_launched_it"] and new_pids_to_close:
            _kill_pids(new_pids_to_close)
            report["closed_by_probe"] = True

    return report


def _print_report(report):
    print("=== WO-10 STEP 1 PROBE (A-038) — presence/connection-state only, no credentials ===")
    for key in (
        "mt5_package_available", "terminal_exe", "terminal_exe_exists",
        "pre_launch_running_pids", "we_launched_it", "initialize_ok",
        "initialize_error", "vantage_identity_ok", "vantage_identity_detail",
        "terminal_connected", "trade_allowed",
        "account_present", "matching_symbols", "symbol_pin", "depth_check",
        "m5_extent", "closed_by_probe",
    ):
        print(f"{key}: {report.get(key)}")
    green = (
        report["mt5_package_available"]
        and report["terminal_exe_exists"]
        and report["initialize_ok"]
        and report["vantage_identity_ok"] is True
        and bool(report["matching_symbols"])
        and any(isinstance(v, int) and v > 0 for v in report["depth_check"].values())
    )
    print(f"VERDICT: {'GREEN' if green else 'RED — see fields above for the blocking reason'}")
    return green


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    symbol_prefix = argv[0] if argv else "XAUUSD"
    report = probe(symbol_prefix)
    green = _print_report(report)
    return 0 if green else 1


if __name__ == "__main__":
    raise SystemExit(main())
