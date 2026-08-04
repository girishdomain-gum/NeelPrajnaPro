"""CSV-to-Bar loader (AM-07 Stage A, P1; A-037/A-038).

Design after reference/NeelPrajnaPro_v1 @ 67b1d69 (bar-loading exists
there in a different shape), re-implemented from scratch against THIS
project's own `Bar` type and THIS project's own real export format.

FRICTION #1 (named in A-032 §3, closed here): no canonical CSV<->Bar
loader existed anywhere in qrf/. Every place bars were previously needed
(tests/kernel/test_s08_rehearsal.py) hand-built synthetic `Bar` objects or
round-tripped through a test-only CSV shape that was never the real
export's columns. This module is the first thing that turns a real S03
-exported CSV into `Bar` objects the detector SDK can consume.

THE HEADER IS A CODE FACT, NOT A DATA FACT (A-038 Ruling 1): the expected
column order below is copied from the literal string the exporter itself
writes -- `mql5/Scripts/QRF/ExportXAUUSD.mq5`'s
`FileWrite(csv_handle, "time,open,high,low,close,tick_volume,spread,
real_volume")` line -- never read from any live CSV, VIRGIN or otherwise.
A loader that refuses loudly on an unexpected header needs to know the
right header only from the code that writes it.

WHY REFUSE RATHER THAN ADAPT: A-038 Ruling 1 is explicit that this loader
must not need to peek at a live batch to know its own contract. If the
real export format ever changes, this loader stops with a named exception
at Stage B ingest time -- caught by the machine, costing nothing -- rather
than silently reading columns it was never proven to understand.

WHAT THIS MODULE DOES NOT DO: it does not verify provenance (that is
`qrf.kernel.observation.provenance` / `ingest_csv`, called first, always).
It does not interpret `time` (server-time epoch seconds, uncorrected --
same convention as `Bar.time` itself). It drops `tick_volume`, `spread`
and `real_volume` -- present in the real export, not part of the `Bar`
SDK type (AM-01: detectors see OHLC + time only).
"""

from __future__ import annotations

import csv
from pathlib import Path

from qrf.errors import SchemaViolation
from qrf.kernel.detection.types import Bar

EXPECTED_HEADER = (
    "time",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "spread",
    "real_volume",
)


def load_bars_csv(csv_path: Path) -> tuple[Bar, ...]:
    """Parse a real-format XAUUSD M5 export into `Bar` objects, in file
    order. Refuses (SchemaViolation) on any header that is not EXACTLY
    `EXPECTED_HEADER`, in that order -- no partial match, no reordering,
    no "close enough". Refuses on any row that cannot be parsed as the
    numeric OHLC + integer time shape `Bar` requires.
    """
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = tuple(next(reader))
        except StopIteration:
            raise SchemaViolation("bars csv has no header row", csv_path) from None
        if header != EXPECTED_HEADER:
            raise SchemaViolation(
                f"bars csv header does not match the exporter's real format "
                f"{EXPECTED_HEADER}",
                header,
            )

        bars = []
        for row_index, row in enumerate(reader):
            if len(row) != len(EXPECTED_HEADER):
                raise SchemaViolation(
                    f"bars csv row {row_index} has {len(row)} fields, "
                    f"expected {len(EXPECTED_HEADER)}",
                    row,
                )
            try:
                bars.append(
                    Bar(
                        time=int(row[0]),
                        open=float(row[1]),
                        high=float(row[2]),
                        low=float(row[3]),
                        close=float(row[4]),
                    )
                )
            except ValueError as exc:
                raise SchemaViolation(
                    f"bars csv row {row_index} is not parseable as a Bar", row
                ) from exc
        return tuple(bars)
