#!/usr/bin/env python3
"""export_xauusd_m5.py -- WO-10 R6 acquisition tool (A-050/O-025).

Pulls XAUUSD M5 bars directly via the MetaTrader5 python API and emits
a rev-1-shaped provenance twin, mirroring QRF_Data_Export.mq5's own
output shape (ivf/mt5/QRF_Data_Export.mq5) but without needing the
terminal's interactive script dialog or a dedicated/closed terminal --
copy_rates_range works against an already-running, already-logged-in
terminal exactly as it is.

SCOPE (A-050 write grant, explicit and bounded): this file COLLECTS
inputs. It never judges, verifies, or re-derives a verdict -- that is
what the untouchable ivf/verify_* and IVF_*_HC_* scripts are for. If a
future change here starts asking "is this correct", it has crossed out
of this file's job.

VANTAGE ONLY, ALWAYS (A-039/A-040) and SYMBOL PIN (A-047/O-023): both
checks are re-implemented HERE, independently, rather than imported
from scripts/probe_mt5_terminal.py -- ivf/** stays independent of the
rest of the repo by design (IND-1), so this tool does not depend on
code outside ivf/ for its own safety gates. Small, deliberate
duplication; drilled RED exactly like the probe's originals.

Writes NO journal record and performs NO scope registration or OOS
designation -- those remain the Owner's two-key ceremony
(A-025/A-037). This tool's only writes are a CSV and a provenance
sidecar under data/incoming/.

Run:  .venv\\Scripts\\python.exe ivf\\mt5\\export_xauusd_m5.py \\
          <YYYY-MM-DD> <YYYY-MM-DD> [--tag TAG] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

TERMINAL_INSTALL_DIR = r"C:\Program Files\Vantage Markets MT5 Terminal"
TERMINAL_EXE = TERMINAL_INSTALL_DIR + r"\terminal64.exe"
VANTAGE_COMPANY_TOKEN = "vantage markets"
SYMBOL_PIN = "XAUUSD"
PERIOD_SECONDS = 300  # M5
INCOMPLETE_SLACK = timedelta(days=7)  # a request's start may legitimately
# land a few days late (weekend/holiday) without being a truncated pull


def _identity_matches_vantage(term_info):
    """A-039's identity check, re-implemented independently (IND-1) --
    see scripts/probe_mt5_terminal.py's own copy for the full rationale.
    Returns (ok, reason)."""
    if term_info is None:
        return False, "terminal_info() returned None -- cannot verify identity, refusing"
    path = getattr(term_info, "path", "") or ""
    company = getattr(term_info, "company", "") or ""
    path_ok = os.path.normcase(os.path.abspath(path)) == os.path.normcase(
        os.path.abspath(TERMINAL_INSTALL_DIR)
    )
    company_ok = VANTAGE_COMPANY_TOKEN in company.lower()
    if path_ok and company_ok:
        return True, f"path={path!r} company={company!r}"
    return False, (
        f"WRONG TERMINAL ATTACHED -- path={path!r} company={company!r}, "
        f"expected install {TERMINAL_INSTALL_DIR!r} "
        f"and company containing {VANTAGE_COMPANY_TOKEN!r}"
    )


def _symbol_is_pinned(symbol):
    """A-047's exact-match symbol pin, re-implemented independently."""
    return symbol == SYMBOL_PIN


class ExportRefused(Exception):
    """Raised for every refusal path -- caller prints str(exc) and exits
    non-zero. No file is ever written on this path."""


def _bar_time_to_server_str(epoch_seconds):
    """RAW server time, unconverted -- the epoch value copy_rates_range
    returns IS the server-labelled time already (the same numbers
    QRF_Data_Export.mq5's rates[i].time carries); this only formats it
    for the CSV/provenance, it does not shift the value."""
    dt = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    return dt.strftime("%Y.%m.%d %H:%M:%S")


def _dow_of(epoch_seconds):
    # server-labelled epoch interpreted as a plain calendar; 0=Sunday, matching
    # QRF_Data_Export.mq5's MqlDateTime.day_of_week convention exactly.
    dt = datetime.fromtimestamp(int(epoch_seconds), tz=timezone.utc)
    return (dt.weekday() + 1) % 7


def connect():
    """Refuses loudly (ExportRefused) on: package missing, terminal exe
    missing, initialize() failure, or wrong-terminal identity. Never
    reads a single bar before the identity check passes."""
    if mt5 is None:
        raise ExportRefused("MetaTrader5 package not installed (pip install .[mt5])")
    if not os.path.isfile(TERMINAL_EXE):
        raise ExportRefused(f"pinned terminal64.exe not found at {TERMINAL_EXE}")
    ok = mt5.initialize(path=TERMINAL_EXE)  # A-039 rule 2: path always supplied
    if not ok:
        raise ExportRefused(f"initialize() failed: {mt5.last_error()}")
    term_info = mt5.terminal_info()
    identity_ok, detail = _identity_matches_vantage(term_info)
    if not identity_ok:
        mt5.shutdown()
        raise ExportRefused(f"REFUSED: {detail}")
    return term_info


def export(symbol, date_from, date_to, tag, out_dir):
    """Pulls [date_from, date_to) M5 bars for `symbol`, writes CSV +
    provenance twin into out_dir. Refuses (ExportRefused, writes
    NOTHING) if symbol is not the exact pin. Returns the dict of
    provenance fields on success (even when history_complete_vs_request
    is "NO -- INCOMPLETE" -- that is reported, not hidden, exactly as
    QRF_Data_Export.mq5 does: the file is still written with a loud
    warning, not silently withheld, so the caller can decide)."""
    if not _symbol_is_pinned(symbol):
        raise ExportRefused(
            f"REFUSED: symbol={symbol!r} is not the pinned symbol {SYMBOL_PIN!r} -- no data read"
        )

    term_info = connect()
    try:
        acct_info = mt5.account_info()
        sym_info = mt5.symbol_info(symbol)
        if sym_info is None:
            raise ExportRefused(f"symbol_info({symbol!r}) returned None -- symbol not found")

        timeframe = mt5.TIMEFRAME_M5
        bars = mt5.copy_rates_range(symbol, timeframe, date_from, date_to)
        if bars is None or len(bars) == 0:
            raise ExportRefused(
                f"copy_rates_range returned no bars for {symbol} "
                f"{date_from.isoformat()}..{date_to.isoformat()} ({mt5.last_error()})"
            )

        n = len(bars)
        first_t, last_t = int(bars[0]["time"]), int(bars[-1]["time"])
        complete = datetime.fromtimestamp(first_t, tz=timezone.utc) <= date_from + INCOMPLETE_SLACK

        gaps = 0
        max_gap = 0
        max_gap_at = None
        for i in range(1, n):
            dt = int(bars[i]["time"]) - int(bars[i - 1]["time"])
            if dt > PERIOD_SECONDS:
                gaps += 1
                if dt > max_gap:
                    max_gap = dt
                    max_gap_at = int(bars[i - 1]["time"])

        os.makedirs(out_dir, exist_ok=True)
        from_s = date_from.strftime("%Y%m%d")
        to_s = date_to.strftime("%Y%m%d")
        tag_suffix = f"_{tag}" if tag else ""
        base = f"QRF_{symbol}_PERIOD_M5_{from_s}_{to_s}{tag_suffix}"
        csv_path = os.path.join(out_dir, base + ".csv")
        prov_path = os.path.join(out_dir, base + ".provenance.txt")

        with open(csv_path, "w", encoding="ascii", newline="") as f:
            f.write("time_open_sec,time_close_sec,open,high,low,close,"
                     "tick_volume,spread,real_volume,dow\n")
            for row in bars:
                t = int(row["time"])
                f.write(
                    f"{t},{t + PERIOD_SECONDS},"
                    f"{row['open']:.8f},{row['high']:.8f},{row['low']:.8f},{row['close']:.8f},"
                    f"{int(row['tick_volume'])},{int(row['spread'])},{int(row['real_volume'])},"
                    f"{_dow_of(t)}\n"
                )

        # symbol_info_tick's `time` is the LAST TICK, not a live clock -- when
        # the market is closed (weekend/holiday) that tick can be a day or
        # more stale, and naively subtracting wall-clock "now" from it then
        # produces a nonsense multi-hour "offset" (caught on a real Sunday
        # run: -130725s, i.e. -36h, physically impossible for a broker).
        # Only trust it as a NOW measurement when it is actually fresh.
        srv_now = mt5.symbol_info_tick(symbol)
        srv_vs_gmt_now = None
        srv_now_stale_reason = None
        if srv_now is not None:
            wall_now = int(datetime.now(timezone.utc).timestamp())
            tick_age = wall_now - int(srv_now.time)
            if abs(tick_age) <= 300:  # within 5 minutes: market is live, trust it
                srv_vs_gmt_now = int(srv_now.time) - wall_now
            else:
                srv_now_stale_reason = (
                    f"last tick is {tick_age}s old (market likely closed) -- "
                    f"NOW offset not computed from a stale tick"
                )

        provenance = {
            "format": "QRF data export provenance (rev 1, Python acquisition variant)",
            "exported_utc": datetime.now(timezone.utc).strftime("%Y.%m.%d %H:%M:%S"),
            "terminal_company": getattr(term_info, "company", None),
            "terminal_name": getattr(term_info, "name", None),
            "account_server": getattr(acct_info, "server", None) if acct_info else None,
            "account_company": getattr(acct_info, "company", None) if acct_info else None,
            "symbol": symbol,
            "symbol_description": getattr(sym_info, "description", None),
            "symbol_path": getattr(sym_info, "path", None),
            "digits": getattr(sym_info, "digits", None),
            "timeframe": f"PERIOD_M5 ({PERIOD_SECONDS} s)",
            "requested_range_server_time": (
                f"{date_from.strftime('%Y.%m.%d %H:%M')} .. {date_to.strftime('%Y.%m.%d %H:%M')}"
            ),
            "server_vs_gmt_offset_seconds_NOW": srv_vs_gmt_now,
            "server_vs_gmt_offset_NOW_unavailable_reason": srv_now_stale_reason,
            "note": "offset is measured NOW; DST-era offsets in history may differ",
            "bars_written": n,
            "first_bar_open_server": f"{_bar_time_to_server_str(first_t)} (epoch {first_t})",
            "last_bar_open_server": f"{_bar_time_to_server_str(last_t)} (epoch {last_t})",
            "gaps_gt_1_period": gaps,
            "max_gap_seconds": max_gap,
            "max_gap_after_server": _bar_time_to_server_str(max_gap_at) if max_gap_at else None,
            "history_complete_vs_request": "YES" if complete else "NO -- INCOMPLETE",
            "owner_provenance_statement": "(Owner fills: where does this feed's price come from?)",
            "declared_independence_tier": "(Owner fills: broker | lp | venue | unknown)",
        }
        with open(prov_path, "w", encoding="ascii", newline="\r\n") as f:
            for key, value in provenance.items():
                f.write(f"{key}: {value}\n")

        provenance["csv_path"] = csv_path
        provenance["provenance_path"] = prov_path
        return provenance
    finally:
        mt5.shutdown()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("date_from", help="YYYY-MM-DD, UTC, inclusive-ish (server time, raw)")
    parser.add_argument("date_to", help="YYYY-MM-DD, UTC, exclusive-ish (server time, raw)")
    parser.add_argument("--tag", default="r6", help="filename tag (default: r6)")
    parser.add_argument("--out-dir", default=os.path.join("data", "incoming"))
    args = parser.parse_args(argv)

    date_from = datetime.strptime(args.date_from, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    date_to = datetime.strptime(args.date_to, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    try:
        prov = export(SYMBOL_PIN, date_from, date_to, args.tag, args.out_dir)
    except ExportRefused as exc:
        print(f"EXPORT REFUSED: {exc}")
        return 1

    print(f"wrote {prov['csv_path']}")
    print(f"wrote {prov['provenance_path']}")
    for key in ("bars_written", "first_bar_open_server", "last_bar_open_server",
                "gaps_gt_1_period", "history_complete_vs_request"):
        print(f"{key}: {prov[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
