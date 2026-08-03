"""Ingest: unverified data must be structurally unable to enter the store
(A-007 §3.4).

`ingest_csv` always calls `provenance.verify()` itself, first, with no
parameter to skip it -- there is no bypass path to prove wrong, because
there is no path at all. Only after verification passes does the CSV's
bytes get bound into the S02 BulkStore, so the window/record ledger holds
the proof of exactly what was ingested.

BULK FORMAT CHOICE: the verified CSV's raw bytes are bound as-is, unlike
converting to parquet or another columnar format first. Reasoning kept
here, not just in the sprint report: S02's BulkStore is deliberately
format-agnostic (any bytes, proven unaltered by hash), and CSV is the
format the exporter and the terminal naturally produce -- converting adds
a dependency and a conversion step with no reader yet that needs columnar
access. That choice belongs to whichever later sprint first computes
statistics over this data at a scale where row-by-row CSV parsing is
actually the bottleneck.
"""

from __future__ import annotations

from pathlib import Path

from qrf.kernel.observation import provenance
from qrf.kernel.records.bulk import BulkStore


def ingest_csv(csv_path: Path, twin_path: Path, bulk_store: BulkStore) -> dict:
    """Verify `csv_path` against `twin_path`, then bind it into
    `bulk_store` under its provenance-recorded filename. Returns the
    manifest payload BulkStore.bind() produced. Raises whatever
    `provenance.verify()` raises (ProvenanceViolation) if verification
    fails -- nothing is bound in that case.
    """
    twin_payload = provenance.verify(csv_path, twin_path)
    return bulk_store.bind(twin_payload["csv_filename"], csv_path)
