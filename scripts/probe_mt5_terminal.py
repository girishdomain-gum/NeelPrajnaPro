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

Usage: python scripts/probe_mt5_terminal.py [SYMBOL_PREFIX]
  SYMBOL_PREFIX defaults to "XAUUSD".
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

TERMINAL_EXE = r"C:\Program Files\Vantage International MT5\terminal64.exe"
PROBE_TIMEFRAME = "M5"
PROBE_BAR_COUNT = 10  # depth-presence check only, never a real pull
LAUNCH_WAIT_SECONDS = 30
LAUNCH_POLL_SECONDS = 1


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
        "terminal_connected": None,
        "trade_allowed": None,
        "account_present": None,
        "matching_symbols": [],
        "depth_check": {},
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
        ok = mt5.initialize(path=TERMINAL_EXE)
        report["initialize_ok"] = bool(ok)
        if not ok:
            err = mt5.last_error()
            report["initialize_error"] = f"{err}"
            return report

        # Detect whether THIS call launched a new process, by polling for
        # a PID that was not present before initialize() was called.
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

        term_info = mt5.terminal_info()
        if term_info is not None:
            report["terminal_connected"] = bool(getattr(term_info, "connected", False))
            report["trade_allowed"] = bool(getattr(term_info, "trade_allowed", False))

        acct_info = mt5.account_info()
        report["account_present"] = acct_info is not None  # presence only, no fields

        all_symbols = mt5.symbols_get() or ()
        matches = sorted(s.name for s in all_symbols if s.name.upper().startswith(symbol_prefix.upper()))
        report["matching_symbols"] = matches

        timeframe = getattr(mt5, f"TIMEFRAME_{PROBE_TIMEFRAME}")
        for sym in matches:
            try:
                bars = mt5.copy_rates_from_pos(sym, timeframe, 0, PROBE_BAR_COUNT)
                report["depth_check"][sym] = 0 if bars is None else len(bars)
            except Exception as exc:  # noqa: BLE001 — report, don't crash the probe
                report["depth_check"][sym] = f"error: {exc}"

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
        "initialize_error", "terminal_connected", "trade_allowed",
        "account_present", "matching_symbols", "depth_check", "closed_by_probe",
    ):
        print(f"{key}: {report.get(key)}")
    green = (
        report["mt5_package_available"]
        and report["terminal_exe_exists"]
        and report["initialize_ok"]
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
