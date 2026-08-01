"""Dataset scope registration — WO-03 (S3, refs A-007 ruling (d)(1)).

A ``dataset_scope`` record is the one place a data-collection scope's static
facts live together: the dataset name, its pinned IANA timezone plus the
evidence it was determined from, its pinned ingest path, the batch-forward
collection protocol in one paragraph, and its OOS designation. Registering
one is a ceremony, not a form fill: every field is required (the
``dataset_scope`` schema, ``qrf.kernel.records.schemas``, rejects any missing
or empty one) — there is no silent-default path. The caller must have
already resolved and reviewed the span/evidence/protocol with the Owner
BEFORE calling ``register``, since calling it seals the record (mirrors the
J-029/030 designation ceremony: typed, not assumed).

This module is kernel: records layer + error taxonomy only.
"""

from __future__ import annotations

from qrf.kernel.records.record import Record, now_ns
from qrf.kernel.records.store import RecordStore


def register(
    store: RecordStore,
    *,
    dataset: str,
    iana_zone: str,
    zone_evidence: str,
    ingest_path: str,
    batch_forward_protocol: str,
    oos_designation: str,
    anchor_ts: int,
    producer: str = "human:girish",
    event_ts: int | None = None,
) -> Record:
    """Append a ``dataset_scope`` record. Writes exactly one record — nothing
    else — to ``store`` (WO-03 AT-4: registering a scope must never touch the
    journal beyond this single record).
    """
    payload = {
        "dataset": dataset,
        "iana_zone": iana_zone,
        "zone_evidence": zone_evidence,
        "ingest_path": ingest_path,
        "batch_forward_protocol": batch_forward_protocol,
        "oos_designation": oos_designation,
        "anchor_ts": int(anchor_ts),
    }
    return store.append(
        "dataset_scope",
        payload,
        producer=producer,
        event_ts=event_ts if event_ts is not None else now_ns(),
    )
