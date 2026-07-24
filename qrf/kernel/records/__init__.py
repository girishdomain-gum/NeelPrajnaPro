"""Kernel records: the Record schema, payload schemas, and the RecordStore.

This subpackage is the foundational data layer. It imports only the stdlib,
``python-ulid`` and the shared error taxonomy (``qrf.kernel.errors``); it does
not depend on any other kernel subsystem.
"""

from qrf.kernel.records.record import (
    GENESIS_HASH,
    Record,
    canonical_bytes,
    compute_content_hash,
    new_ulid,
    now_ns,
)
from qrf.kernel.records.store import RecordStore, VerifyReport

__all__ = [
    "GENESIS_HASH",
    "Record",
    "RecordStore",
    "VerifyReport",
    "canonical_bytes",
    "compute_content_hash",
    "new_ulid",
    "now_ns",
]
