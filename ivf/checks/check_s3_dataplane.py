#!/usr/bin/env python3
"""IVF Sprint-3 check: data plane — rows, prices, and quarantine integrity. (rev 1)

Two checks in one tool (ARCH handover §7 / Verification_Framework per-sprint VC):

  A) ROW + PRICE COMPARISON. A fresh MT5 export CSV (same instrument/period,
     exported independently of the ingested file) vs the BulkStore-persisted
     dataset. EXACT row accounting: clean + flagged == input, every source
     open-time present exactly once across the two partitions, none invented.
     NUMERIC price equality per row (open/high/low/close), and the OBS-4
     property ts == (open_time + timeframe) * 1e9 for every stored row.
  B) FLAGGED-ROW AUDIT. Every quarantined row's values match its source row
     exactly (proving quarantine = set aside, never repair), its `flags`
     column is non-empty, and every flag label is from the ratified class set
     (DEVQ-007). If there are no flagged rows, section B reports VACUOUS —
     visibly, never as a silent pass (S2 lesson: no soft-pass).

INDEPENDENCE (IND): imports NOTHING from qrf. Parquet is read via pyarrow —
a neutral third-party reader, not project code; the OBS-4 shift and all
comparisons are re-implemented here from the spec text (Blueprint §4.2/§5,
REV-S2 OBS-4, DEVQ-006/007 CLOSED threads). Prices are compared as float64
parsed directly from the CSV text, matching the adapter's declared storage
type — equality is exact, no tolerance.

Usage (S3 close):
  uv run python ivf/checks/check_s3_dataplane.py \
      --mt5 ivf/mt5/IVF_S3_FRESH_XAUUSD_H1.csv --timeframe 3600 \
      --clean datastore/bulk/xauusd_h1_sample/part-00000.parquet \
      [--flagged datastore/bulk/xauusd_h1_sample__flagged/part-00000.parquet] \
      --report ivf/reports/s3_verify.json

CSV columns: time_open_sec,open,high,low,close (extra columns ignored;
override the open-time column with --time-col). Exit 0 GREEN, 1 RED.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

FLAG_CLASSES = {
    "non_monotonic", "duplicate", "gap",
    "high_lt_low", "nonpositive_price", "spread_outlier",
}
NS = 1_000_000_000
PRICES = ("open", "high", "low", "close")


def load_csv(path: str, time_col: str) -> dict[int, dict[str, float]]:
    import csv

    rows: dict[int, dict[str, float]] = {}
    order: list[int] = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            t = int(r[time_col])
            order.append(t)
            rows[t] = {p: float(r[p]) for p in PRICES}
    if len(order) != len(rows):
        # duplicates in the SOURCE are legal (they get flagged); keep count
        rows["__dup_source_rows__"] = len(order) - len(rows)  # type: ignore
    rows["__n__"] = len(order)  # type: ignore
    return rows


def load_parquet(path: str) -> list[dict]:
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    return table.to_pylist()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mt5", required=True)
    ap.add_argument("--timeframe", required=True, type=int)
    ap.add_argument("--clean", required=True)
    ap.add_argument("--flagged", default=None)
    ap.add_argument("--time-col", default="time_open_sec")
    ap.add_argument("--report", default=None)
    a = ap.parse_args()

    red: list[str] = []
    src = load_csv(a.mt5, a.time_col)
    n_src = src.pop("__n__")
    n_dup = src.pop("__dup_source_rows__", 0)
    clean = load_parquet(a.clean)
    flagged = load_parquet(a.flagged) if a.flagged else []

    # --- A: row accounting -------------------------------------------------
    if len(clean) + len(flagged) != n_src:
        red.append(
            f"A.count: clean({len(clean)}) + flagged({len(flagged)}) "
            f"!= source rows({n_src})"
        )
    seen: dict[int, int] = {}
    for part, rows in (("clean", clean), ("flagged", flagged)):
        for row in rows:
            t = int(row["time"])
            seen[t] = seen.get(t, 0) + 1
            if t not in src:
                red.append(f"A.invented: {part} row time={t} absent from source")
                continue
            # OBS-4 property, re-derived from spec text
            want_ts = (t + a.timeframe) * NS
            if int(row["ts"]) != want_ts:
                red.append(
                    f"A.obs4: time={t} stored ts={row['ts']} != {want_ts}"
                )
            for p in PRICES:
                if float(row[p]) != src[t][p]:
                    red.append(
                        f"{'B' if part == 'flagged' else 'A'}.price: time={t} "
                        f"{part}.{p}={row[p]!r} != source {src[t][p]!r}"
                    )
    missing = [t for t in src if seen.get(t, 0) == 0]
    if missing:
        red.append(f"A.missing: {len(missing)} source rows absent, first={missing[0]}")
    multi = {t: c for t, c in seen.items() if c > 1 and n_dup == 0}
    if multi:
        t0 = next(iter(multi))
        red.append(f"A.duplicated: {len(multi)} times stored >once, first={t0}")

    # --- B: quarantine audit ----------------------------------------------
    b_status = "VACUOUS (0 flagged rows — audited nothing; drill covers B)"
    if flagged:
        b_status = "AUDITED"
        for row in flagged:
            fl = [s for s in str(row.get("flags", "")).split(",") if s]
            if not fl:
                red.append(f"B.flags: quarantined time={row['time']} has empty flags")
            for s in fl:
                if s not in FLAG_CLASSES:
                    red.append(f"B.flags: unknown class {s!r} at time={row['time']}")

    verdict = "RED" if red else "GREEN"
    report = {
        "check": "s3_dataplane", "rev": 1, "run_utc": int(time.time()),
        "inputs": {"mt5": a.mt5, "clean": a.clean, "flagged": a.flagged,
                   "timeframe": a.timeframe},
        "counts": {"source": n_src, "source_dup_times": n_dup,
                   "clean": len(clean), "flagged": len(flagged)},
        "section_b": b_status, "red": red, "verdict": verdict,
    }
    out = json.dumps(report, indent=2)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out + "\n")
    print(out)
    return 0 if verdict == "GREEN" else 1


if __name__ == "__main__":
    sys.exit(main())
