"""ARCH-003A — exercise the quarantine path in a SCRATCH datastore.

Closes the REV-S3 drill-2 SKIP: the real ``xauusd_h1_sample`` ingests with 0
flags, so the flagged path (and drill 2, which needs a quarantine dataset) was
never exercised end-to-end. This ingests a small synthetic CSV that plants at
least one row of EVERY anomaly class into a throwaway datastore (its own journal
+ BulkStore under a tmp dir) — **the real ledger is never touched** — and prints
the scratch paths + planted expectations so the Owner can run
``check_s3_dataplane.py --flagged`` (GREEN) and ``drill_s3.py`` (drill 2 CAUGHT,
not SKIPPED) against the output.

The synthetic open-time column is named ``time_open_sec`` so the IVF check/drill
read it with their default ``--time-col``.

Run:  uv run python scripts/exercise_quarantine_s3.py
"""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.mt5_csv import QUARANTINE_SUFFIX, ingest_mt5_csv

DATASET = "quarantine_demo"
TIMEFRAME_SECONDS = 3600
_BASE = 1_704_283_200  # 2024-01-03 12:00 UTC (a Wednesday — no weekend/holiday)
_H = 3600
_COLUMN_MAP = {"time": "time_open_sec"}

# (hour_offset, open, high, low, close, spread, planted_class or None).
# Prices are stored UNMODIFIED (flag-never-repair), so the check's price equality
# holds for flagged rows too; each anomaly's only deviation is the one it plants.
_SPEC: list[tuple[int, float, float, float, float, float, str | None]] = [
    (0, 100.0, 101.0, 99.0, 100.5, 2.0, None),               # clean
    (1, 100.0, 101.0, 99.0, 100.5, 2.0, None),               # clean
    (1, 100.0, 101.0, 99.0, 100.5, 2.0, "duplicate"),        # same time as prev
    (2, 100.0, 99.0, 101.0, 100.5, 2.0, "high_lt_low"),      # high < low
    (3, 100.0, 101.0, 99.0, -1.0, 2.0, "nonpositive_price"), # close <= 0
    (4, 100.0, 101.0, 99.0, 100.5, 9999.0, "spread_outlier"),# extreme spread
    (8, 100.0, 101.0, 99.0, 100.5, 2.0, "gap"),              # +4h hole (>1 bar)
    (9, 100.0, 101.0, 99.0, 100.5, 2.0, None),               # clean
    (5, 100.0, 101.0, 99.0, 100.5, 2.0, "non_monotonic"),    # time < previous
]
_FIELDS = ("time_open_sec", "open", "high", "low", "close", "spread")


def write_synthetic_csv(path: Path) -> list[dict]:
    """Write the planted CSV; return ``[{time, class}]`` for the flagged rows."""
    rows, planted = [], []
    for off, o, h, low, c, sp, cls in _SPEC:
        t = _BASE + off * _H
        rows.append({"time_open_sec": t, "open": o, "high": h, "low": low,
                     "close": c, "spread": sp})
        if cls:
            planted.append({"time": t, "class": cls})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, _FIELDS)
        w.writeheader()
        w.writerows(rows)
    return planted


def run_exercise(scratch_dir: str | Path) -> dict:
    """Ingest the synthetic CSV into a scratch datastore under ``scratch_dir``."""
    scratch = Path(scratch_dir)
    csv_path = scratch / "synthetic_quarantine.csv"
    planted = write_synthetic_csv(csv_path)

    store = RecordStore(scratch / "journal" / "journal.jsonl")
    bulk = BulkStore(store, scratch / "bulk")
    res = ingest_mt5_csv(
        csv_path, DATASET, timeframe_seconds=TIMEFRAME_SECONDS,
        store=store, bulk_store=bulk, column_map=_COLUMN_MAP,
    )
    return {
        "result": res,
        "planted": planted,
        "csv": csv_path,
        "clean": scratch / "bulk" / DATASET / "part-00000.parquet",
        "flagged": scratch / "bulk" / f"{DATASET}{QUARANTINE_SUFFIX}" / "part-00000.parquet",
        "scratch": scratch,
        "store": store,
    }


def main() -> None:
    scratch = Path(tempfile.mkdtemp(prefix="qrf_quarantine_s3_"))
    out = run_exercise(scratch)
    res = out["result"]

    print(f"scratch datastore: {scratch}  (the REAL ledger was NOT touched)")
    print(f"ingested {res.rows_total} rows: clean={res.rows_clean} flagged={res.rows_flagged}"
          f"  verdict={res.verdict}")
    print(f"ingest_report={res.report.record_id} (schema v{res.report.schema_version}) "
          f"anomaly_counts={res.anomaly_counts}")
    print(f"clean parquet   : {out['clean']}")
    print(f"flagged parquet : {out['flagged']}")
    print("planted (time -> class):")
    for p in out["planted"]:
        print(f"  {p['time']} -> {p['class']}")

    py = sys.executable
    print("\nOwner: run the IVF checks against the scratch output —")
    print(f"  {py} ivf/checks/check_s3_dataplane.py --mt5 {out['csv']} "
          f"--timeframe {TIMEFRAME_SECONDS} --clean {out['clean']} "
          f"--flagged {out['flagged']} --report {scratch / 's3_verify.json'}")
    print(f"  {py} ivf/checks/drill_s3.py --mt5 {out['csv']} "
          f"--timeframe {TIMEFRAME_SECONDS} --clean {out['clean']} "
          f"--flagged {out['flagged']} --workdir {scratch / 'drill_tmp'} "
          f"--report {scratch / 's3_drill.json'}")
    print("Expect: check GREEN (section B AUDITED, not vacuous); drill 2 CAUGHT.")


if __name__ == "__main__":
    main()
