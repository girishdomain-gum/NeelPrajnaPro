"""The provenance twin: git holds the PROOF of what an export was, never
the export itself (A-007 §3.2).

A CSV lives outside the repo (F:\\NeelPrajnaProData\\incoming\\, per A-007
§3.1). Its provenance twin -- a small JSON file carrying the CSV's sha256
plus everything needed to know what the data IS -- is TRACKED IN GIT,
under `data/provenance/` in this repo. `verify()` is the only sanctioned
way past this file: it recomputes the CSV's hash, and refuses on any
mismatch, a missing twin, or a twin missing its own hash field.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qrf.errors import ProvenanceViolation, SchemaViolation

REQUIRED_FIELDS = {
    "csv_filename",
    "symbol",
    "timeframe",
    "broker",
    "server",
    "account",
    "terminal_build",
    "digits",
    "point",
    "trade_tick_size",
    "requested_start_utc",
    "requested_end_utc",
    "returned_start_utc",
    "returned_end_utc",
    "row_count",
    "export_timestamp_utc",
    "server_clock_offset_seconds",
    "sha256",
}


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_provenance(payload: dict) -> None:
    missing = REQUIRED_FIELDS - payload.keys()
    if missing:
        raise SchemaViolation("provenance twin missing required fields", sorted(missing))
    if not isinstance(payload["sha256"], str) or len(payload["sha256"]) != 64:
        raise SchemaViolation(
            "provenance twin sha256 must be a 64-char hex string", payload["sha256"]
        )
    if not isinstance(payload["row_count"], int) or payload["row_count"] < 0:
        raise SchemaViolation("provenance twin row_count must be a non-negative int", payload)


def write_twin(csv_path: Path, metadata: dict, twin_path: Path) -> dict:
    """Compute the CSV's hash, fold it into `metadata`, validate, and write
    the twin JSON. Returns the full payload written.
    """
    payload = dict(metadata)
    payload["sha256"] = _sha256_file(Path(csv_path))
    validate_provenance(payload)
    twin_path = Path(twin_path)
    twin_path.parent.mkdir(parents=True, exist_ok=True)
    twin_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def verify(csv_path: Path, twin_path: Path) -> dict:
    """Recompute csv_path's hash and check it against twin_path. Raises
    ProvenanceViolation naming exactly what failed: a missing twin, a twin
    that fails schema validation (e.g. no hash field), a missing CSV, or a
    hash mismatch. Returns the twin's payload on success.
    """
    csv_path = Path(csv_path)
    twin_path = Path(twin_path)
    if not twin_path.exists():
        raise ProvenanceViolation("missing-twin", f"no provenance twin at {twin_path}")
    try:
        payload = json.loads(twin_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProvenanceViolation("malformed-twin", f"{twin_path} is not valid JSON") from exc
    try:
        validate_provenance(payload)
    except SchemaViolation as exc:
        raise ProvenanceViolation("invalid-twin", str(exc)) from exc
    if not csv_path.exists():
        raise ProvenanceViolation(
            "missing-csv", f"twin names a CSV that does not exist: {csv_path}"
        )
    actual_hash = _sha256_file(csv_path)
    if actual_hash != payload["sha256"]:
        raise ProvenanceViolation(
            "hash-mismatch",
            f"expected {payload['sha256']}, got {actual_hash} for {csv_path}",
        )
    return payload
