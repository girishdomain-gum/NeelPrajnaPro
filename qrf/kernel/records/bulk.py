"""Bulk evidence store: binds arbitrary bulk files to a RecordStore
manifest by content hash, so a small ledger holds the PROOF of what a large
bulk file was, rather than the bulk data itself — the load-bearing idea is
that the ledger stops holding the data and starts holding the proof of what
the data was.

FORMAT CHOICE: raw bytes on disk (one file per bulk artifact, physically
owned by the store under `root/<name>`) plus a JSON-per-line manifest
binding each name to its sha256 and size. A fixed serialization such as
parquet is deliberately NOT chosen here: S02 has no real market data to
serialize (A-004 §7 — no market data ingest this sprint) and building the
proof mechanism does not require picking that format in advance. The
on-disk representation for real bulk data is a decision for S03, when real
data first exists; this store only needs to prove that ANY bytes, once
bound, cannot silently change without detection.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from qrf.errors import BulkMismatch, SchemaViolation
from qrf.kernel.records.store import RecordStore


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_manifest_entry(payload: dict) -> None:
    required = {"name", "sha256", "size"}
    if not required.issubset(payload):
        raise SchemaViolation("manifest entry missing required fields", payload)
    if not isinstance(payload["name"], str) or not payload["name"]:
        raise SchemaViolation("manifest entry name must be a non-empty string", payload["name"])
    if not isinstance(payload["sha256"], str) or len(payload["sha256"]) != 64:
        raise SchemaViolation(
            "manifest entry sha256 must be a 64-char hex string", payload["sha256"]
        )
    if not isinstance(payload["size"], int) or payload["size"] < 0:
        raise SchemaViolation("manifest entry size must be a non-negative int", payload["size"])


class BulkStore:
    """`root` holds the bulk files this store owns; `manifest_path` is the
    binding RecordStore's file. `bind()` copies the source bytes in under
    the store's control and appends a manifest record. `verify()` re-hashes
    every bulk file the manifest names and raises BulkMismatch naming the
    first file that does not match (altered content, wrong size, or
    missing entirely).
    """

    def __init__(self, root: Path, manifest_path: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest = RecordStore(manifest_path, validate_manifest_entry)

    def bind(self, name: str, source_path: Path) -> dict:
        source_path = Path(source_path)
        if not source_path.exists():
            raise BulkMismatch(name, f"source file does not exist: {source_path}")
        data = source_path.read_bytes()
        dest = self.root / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        payload = {"name": name, "sha256": _sha256_bytes(data), "size": len(data)}
        record = self.manifest.append(payload)
        return record.payload

    def verify(self) -> None:
        for record in self.manifest.verify():
            name = record.payload["name"]
            expected_hash = record.payload["sha256"]
            expected_size = record.payload["size"]
            path = self.root / name
            if not path.exists():
                raise BulkMismatch(name, f"manifest names a file that does not exist: {path}")
            data = path.read_bytes()
            if len(data) != expected_size:
                raise BulkMismatch(
                    name, f"size mismatch: manifest says {expected_size}, found {len(data)}"
                )
            actual_hash = _sha256_bytes(data)
            if actual_hash != expected_hash:
                raise BulkMismatch(
                    name, f"content hash mismatch: expected {expected_hash}, got {actual_hash}"
                )
