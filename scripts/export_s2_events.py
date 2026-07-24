"""ARCH-002A T1 — export Sprint-2 detector events for the IVF S2 VC.

Runs both Sprint-2 detectors over the MT5 reference bars and writes
``s2_events.csv`` (header ``ts,event_type,direction``; ts int nanoseconds,
CLOSE-time basis per REV-S2 OBS-4). The IVF check then compares these events
against references it recomputes independently from the same MT5 CSV.

Contract notes:
* **ts basis = close time.** ``ts = time_close_sec * 1e9`` (OBS-4). For H1 bars
  (close = open + 3600) this lands every marker at the same absolute timestamp
  the check expects from open-time reasoning, because a bar's close time equals
  the next bar's open time.
* **Session params = the REGISTERED spec**, not the detector defaults. The
  seasonality instrument was registered/calibrated with london 28800-57600 and
  emit_dow=True (record 01KYAKYY1298M1N3JWAA8HBQ5P; the concrete window lives in
  the detector's construction params — the instrument_registered payload carries
  params_schema per Blueprint §2, not the values). The bare default would also
  emit a `newyork` session the check does not know about.

Run:  uv run python scripts/export_s2_events.py \
        --mt5 IVF_S2_XAUUSD_PERIOD_H1.csv --out s2_events.csv
"""

from __future__ import annotations

import argparse
import csv

import pyarrow as pa

from qrf.trading.concepts.classical.detector_rsi import RSIDetector
from qrf.trading.concepts.seasonality.detector import SeasonalityDetector

NS = 1_000_000_000

# Registered seasonality calibration config (record 01KYAKYY1298M1N3JWAA8HBQ5P).
REGISTERED_SESSIONS = {"london": [28800, 57600]}  # UTC seconds-of-day, [start,end)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mt5", default="IVF_S2_XAUUSD_PERIOD_H1.csv")
    ap.add_argument("--out", default="s2_events.csv")
    a = ap.parse_args()

    with open(a.mt5, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ts = [int(r["time_close_sec"]) * NS for r in rows]  # CLOSE-time basis (OBS-4)
    close = [float(r["close"]) for r in rows]
    bars = pa.table(
        {"ts": pa.array(ts, pa.int64()), "close": pa.array(close, pa.float64())}
    )

    seasonality = SeasonalityDetector(
        params={"sessions": REGISTERED_SESSIONS, "emit_dow": True}
    )
    rsi = RSIDetector()  # period 14, overbought 70, oversold 30 (check defaults)

    events: list[dict] = []
    counts: dict[str, int] = {}
    for det in (seasonality, rsi):
        frame = det.detect(bars)
        counts[det.instrument_id] = frame.num_rows
        et = frame.column("event_type").to_pylist()
        di = frame.column("direction").to_pylist()
        tsc = frame.column("ts").to_pylist()
        for i in range(frame.num_rows):
            events.append({"ts": int(tsc[i]), "event_type": et[i], "direction": int(di[i])})

    events.sort(key=lambda e: (e["ts"], e["event_type"], e["direction"]))
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, ["ts", "event_type", "direction"])
        w.writeheader()
        w.writerows(events)

    for iid, n in counts.items():
        print(f"{iid}: {n} events")
    print(f"wrote {len(events)} events -> {a.out}")


if __name__ == "__main__":
    main()
