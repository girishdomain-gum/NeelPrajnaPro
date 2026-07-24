"""The Record — wire-level schema, canonical serialization, hashing, ids.

Implementation Blueprint v1.0 §1. This module is the leaf of the kernel: it
imports only the stdlib, ``python-ulid``, and the shared error taxonomy.

Normative contracts inlined from the Blueprint (do not drift — the IVF
re-implements canonical serialization independently from the spec text):

* ``canonical_bytes`` (§1.3): sorted keys, no whitespace, UTF-8, floats via the
  JSON default (Python ``repr``), NaN/Inf forbidden.
* ``content_hash`` (§1.1): SHA-256 of ``canonical_bytes`` of the six semantic
  fields ``{record_type, schema_version, producer, event_ts, parents, payload}``.
  It deliberately excludes ``record_id`` (assigned at append), ``recorded_ts``,
  ``meta`` (never load-bearing), ``content_hash`` and ``prev_hash``.
* ``prev_hash``: the previous record's ``content_hash``; genesis is 64 zeros.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from ulid import ULID

# 64 hex zeros — the prev_hash of the genesis record (Blueprint §1.1).
GENESIS_HASH = "0" * 64

# Fields covered by content_hash, in the order the Blueprint lists them. Order
# is irrelevant to the digest (canonical_bytes sorts keys) but kept for clarity.
HASHED_FIELDS = (
    "record_type",
    "schema_version",
    "producer",
    "event_ts",
    "parents",
    "payload",
)


def canonical_bytes(d: dict) -> bytes:
    """Canonical JSON serialization (Blueprint §1.3, normative — copy exactly).

    Floats use the JSON default (Python ``repr``); ``NaN``/``Inf`` are forbidden
    (``allow_nan=False`` raises ``ValueError``) — use ``null`` and an explicit
    flag field instead.
    """
    return json.dumps(
        d,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def compute_content_hash(
    *,
    record_type: str,
    schema_version: int,
    producer: str,
    event_ts: int,
    parents: list[str] | tuple[str, ...],
    payload: dict,
) -> str:
    """SHA-256 hex digest over the canonical bytes of the six semantic fields."""
    body = {
        "record_type": record_type,
        "schema_version": schema_version,
        "producer": producer,
        "event_ts": event_ts,
        "parents": list(parents),
        "payload": payload,
    }
    return hashlib.sha256(canonical_bytes(body)).hexdigest()


def new_ulid(after: str | None = None) -> str:
    """A ULID string, strictly greater than ``after`` when supplied.

    ULIDs are time-sortable to the millisecond; within one millisecond the
    random component can regress. To guarantee the strict monotonicity the
    store relies on (I: ULIDs increasing within a session), when a freshly
    minted ULID would not exceed ``after`` we take ``after + 1`` on the 128-bit
    integer instead.
    """
    u = ULID()
    if after is not None and str(u) <= after:
        u = ULID.from_int(int(ULID.from_str(after)) + 1)
    return str(u)


@dataclass(frozen=True, slots=True)
class Record:
    """An immutable ledger record (Blueprint §1.1).

    Instances are treated as immutable; ``parents`` is stored as a tuple so the
    lineage cannot be mutated in place. ``payload`` and ``meta`` are dicts by
    contract and must not be mutated after construction.
    """

    record_id: str
    record_type: str
    schema_version: int
    producer: str
    event_ts: int
    recorded_ts: int
    parents: tuple[str, ...]
    payload: dict[str, Any]
    content_hash: str
    prev_hash: str
    meta: dict[str, Any] = field(default_factory=dict)

    # -- construction ---------------------------------------------------------
    @classmethod
    def create(
        cls,
        *,
        record_id: str,
        record_type: str,
        schema_version: int,
        producer: str,
        event_ts: int,
        recorded_ts: int,
        parents: list[str] | tuple[str, ...],
        payload: dict,
        prev_hash: str,
        meta: dict | None = None,
    ) -> Record:
        """Build a record, computing its ``content_hash`` from the six fields."""
        parents_t = tuple(parents)
        content_hash = compute_content_hash(
            record_type=record_type,
            schema_version=schema_version,
            producer=producer,
            event_ts=event_ts,
            parents=parents_t,
            payload=payload,
        )
        return cls(
            record_id=record_id,
            record_type=record_type,
            schema_version=schema_version,
            producer=producer,
            event_ts=event_ts,
            recorded_ts=recorded_ts,
            parents=parents_t,
            payload=payload,
            content_hash=content_hash,
            prev_hash=prev_hash,
            meta=meta or {},
        )

    # -- integrity ------------------------------------------------------------
    def recompute_content_hash(self) -> str:
        """Recompute this record's content hash from its stored fields."""
        return compute_content_hash(
            record_type=self.record_type,
            schema_version=self.schema_version,
            producer=self.producer,
            event_ts=self.event_ts,
            parents=self.parents,
            payload=self.payload,
        )

    # -- wire form ------------------------------------------------------------
    def to_wire(self) -> dict[str, Any]:
        """The full 11-field dict written to the journal (one line = one dict)."""
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "schema_version": self.schema_version,
            "producer": self.producer,
            "event_ts": self.event_ts,
            "recorded_ts": self.recorded_ts,
            "parents": list(self.parents),
            "payload": self.payload,
            "meta": self.meta,
            "content_hash": self.content_hash,
            "prev_hash": self.prev_hash,
        }

    def to_json_line(self) -> bytes:
        """Canonical single-line JSON (no trailing newline) for the journal."""
        return canonical_bytes(self.to_wire())

    @classmethod
    def from_wire(cls, d: dict) -> Record:
        """Reconstruct a record from a parsed journal line."""
        return cls(
            record_id=d["record_id"],
            record_type=d["record_type"],
            schema_version=d["schema_version"],
            producer=d["producer"],
            event_ts=d["event_ts"],
            recorded_ts=d["recorded_ts"],
            parents=tuple(d["parents"]),
            payload=d["payload"],
            content_hash=d["content_hash"],
            prev_hash=d["prev_hash"],
            meta=d.get("meta", {}),
        )


def now_ns() -> int:
    """Current UTC time in integer nanoseconds since the epoch."""
    return time.time_ns()
