"""The terminal launcher: the ONLY module in this project that touches a
live MT5 terminal (A-007 §3.1).

Design after F:\\Fable\\tools\\np_agent.py's launch/harvest mechanics (a
Script run via MT5's own `/config` `[StartUp]` file, never a live IPC
session) -- taken as a CODE QUARRY for the MECHANICS only (subprocess
launch, poll-with-timeout, `/config` ini shape, matching a running
process by exact executable path), re-implemented here from scratch for
this project's own pins. Nothing here reads or depends on Fable's
governance, whitelists, or job-bridge machinery -- none of that applies;
this is a single fixed, hard-coded export path.

WHY NOT THE LIVE `MetaTrader5` PYTHON PACKAGE: it was tried first, and
`mt5.initialize()` with no path attaches to WHATEVER terminal is already
running and exposing the IPC endpoint on this machine -- which silently
connected to a different broker's LIVE account (Winprofx-Live) mid-sprint
when that terminal happened to be the one open, despite the pinned facts
naming Vantage Markets Demo. That incident is why this module launches
the terminal by an explicit, hard-coded absolute path instead: there is
no "whichever terminal happens to be running" left to attach to. See
tests/observation/test_launcher.py and the sprint report for the full
account.

This module is deliberately thin, exactly like S03's original exporter.py
was: every decision (exact symbol, clock offset, provenance) is delegated
to pure, terminal-independent modules that are fully unit-tested without
a real terminal. `run_export()` itself cannot be exercised in CI
(ubuntu-latest has no MT5 terminal at all) -- it is exercised by hand
against the real terminal, and that real run's output is the evidence.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path

from qrf.errors import TerminalBusy, TerminalMismatch
from qrf.kernel.observation import provenance
from qrf.kernel.observation.clock import measure_offset
from qrf.kernel.observation.symbols import PINNED_SYMBOL, require_exact_symbol

# --- CONFIG: every path/pin lives HERE, never supplied by a caller -------

TERMINAL_EXE = r"C:\Program Files\Vantage Markets MT5 Terminal\terminal64.exe"
METAEDITOR_EXE = r"C:\Program Files\Vantage Markets MT5 Terminal\MetaEditor64.exe"
TERM_DATA_DIR = (
    r"C:\Users\giris\AppData\Roaming\MetaQuotes\Terminal"
    r"\725B72F25E46C780EF59F57016D58156"
)
TERM_FILES_DIR = TERM_DATA_DIR + r"\MQL5\Files\QRF"
SCRIPT_REL_PATH = "QRF\\ExportXAUUSD"  # relative to MQL5\Scripts, no extension

PINNED_SERVER = "VantageMarkets-Demo"
PINNED_ACCOUNT = 25867273
PINNED_BROKER = "Vantage Markets (Pty) Ltd"

CSV_FILENAME_IN_TERM = "xauusd_export.csv"
META_FILENAME_IN_TERM = "xauusd_export.meta.json"


def terminal_running() -> list[str]:
    """List any running process matching TERMINAL_EXE's exact path (via
    PowerShell CIM, matching Fable's approach). Other installs (a
    different broker's terminal, entirely) are not our concern and are
    never refused -- only a second instance of THIS install, which MT5
    would silently ignore (a launch that looks like success but does
    nothing).
    """
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='terminal64.exe'\" "
                '| ForEach-Object { "$($_.ProcessId)|$($_.ExecutablePath)" }',
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        return ["<could not query running processes -- erring strict>"]
    if result.returncode != 0:
        return ["<could not query running processes -- erring strict>"]
    target = TERMINAL_EXE.lower()
    hits = []
    for line in (result.stdout or "").splitlines():
        if "|" not in line:
            continue
        pid, _, path = line.strip().partition("|")
        if path and path.strip().lower() == target:
            hits.append(f"pid {pid} {path.strip()}")
    return hits


def build_startup_ini(ini_path: Path, symbol: str, period: str) -> None:
    """Write an MT5 `/config` `[StartUp]` file that runs SCRIPT_REL_PATH on
    `symbol`/`period` and self-closes the terminal afterward. UTF-16LE
    with a BOM, matching MT5's own ini encoding requirement.
    """
    lines = [
        "[StartUp]",
        f"Script={SCRIPT_REL_PATH}",
        f"Symbol={symbol}",
        f"Period={period}",
        "ShutdownTerminal=1",
    ]
    text = "\ufeff" + "\r\n".join(lines) + "\r\n"
    ini_path = Path(ini_path)
    ini_path.parent.mkdir(parents=True, exist_ok=True)
    ini_path.write_bytes(text.encode("utf-16-le"))


def _check_pinned_facts(meta: dict) -> None:
    """Defense in depth beyond the launch-by-path fix: even though we
    launched THIS exact terminal executable, confirm what it actually
    reported matches every pinned fact. Refuses loudly, naming exactly
    which field disagreed, rather than trusting the launch path alone.
    """
    checks = (
        ("symbol", PINNED_SYMBOL, meta.get("symbol")),
        ("server", PINNED_SERVER, meta.get("server")),
        ("account", PINNED_ACCOUNT, meta.get("account")),
        ("broker", PINNED_BROKER, meta.get("broker")),
    )
    for field, expected, actual in checks:
        if actual != expected:
            raise TerminalMismatch(field, expected, actual)


def run_export(
    period: str,
    out_dir: Path,
    twin_path: Path,
    csv_filename: str,
    ini_dir: Path | None = None,
    pinned_offset_seconds: float | None = None,
    timeout_s: int = 120,
) -> dict:
    """Launch the pinned Vantage terminal, run ExportXAUUSD.mq5 on
    (XAUUSD, `period`), wait for it to self-close, then harvest the CSV +
    metadata it wrote, check every pinned fact, measure the server clock
    offset (self-policing against `pinned_offset_seconds` if given, per
    A-007 §3.5c), copy the CSV to `out_dir` (never inside the repo), and
    write its provenance twin to `twin_path` (tracked in git). Returns the
    full provenance payload.
    """
    require_exact_symbol(PINNED_SYMBOL)

    busy = terminal_running()
    if busy:
        raise TerminalBusy(busy)

    ini_path = Path(ini_dir if ini_dir is not None else out_dir) / f"{csv_filename}.startup.ini"
    build_startup_ini(ini_path, PINNED_SYMBOL, period)

    csv_in_term = Path(TERM_FILES_DIR) / CSV_FILENAME_IN_TERM
    meta_in_term = Path(TERM_FILES_DIR) / META_FILENAME_IN_TERM
    csv_in_term.unlink(missing_ok=True)
    meta_in_term.unlink(missing_ok=True)

    t0 = time.time()
    proc = subprocess.Popen([TERMINAL_EXE, f"/config:{ini_path}"])
    while proc.poll() is None:
        time.sleep(1)
        if time.time() - t0 > timeout_s:
            proc.terminate()
            break
    proc.wait()
    wall_clock_after = time.time()

    if not csv_in_term.exists() or not meta_in_term.exists():
        raise RuntimeError(
            f"export produced no output within {timeout_s}s "
            f"(expected {csv_in_term} and {meta_in_term})"
        )

    meta = json.loads(meta_in_term.read_text(encoding="utf-8"))
    _check_pinned_facts(meta)

    measured_offset = measure_offset(meta["server_time_at_export"], wall_clock_after)
    if pinned_offset_seconds is not None:
        from qrf.kernel.observation.clock import check_clock_pin

        check_clock_pin(pinned_offset_seconds, measured_offset)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    dest_csv = out_dir / csv_filename
    shutil.copy2(csv_in_term, dest_csv)

    metadata = {
        "csv_filename": csv_filename,
        "symbol": meta["symbol"],
        "timeframe": meta["timeframe"],
        "broker": meta["broker"],
        "server": meta["server"],
        "account": meta["account"],
        "terminal_build": meta["terminal_build"],
        "digits": meta["digits"],
        "point": meta["point"],
        "trade_tick_size": meta["trade_tick_size"],
        "requested_start_utc": None,
        "requested_end_utc": None,
        "returned_start_utc": meta["returned_start_utc"],
        "returned_end_utc": meta["returned_end_utc"],
        "row_count": meta["row_count"],
        "export_timestamp_utc": int(wall_clock_after),
        "server_clock_offset_seconds": measured_offset,
        "requested_bar_count": meta["requested_bar_count"],
        "clock_measurement_note": (
            "server_time_at_export vs. Python wall-clock read immediately after "
            f"the terminal self-closed; bounded uncertainty <= the full launch-"
            f"run-close round trip ({wall_clock_after - t0:.1f}s this run)."
        ),
    }
    return provenance.write_twin(dest_csv, metadata, twin_path)
