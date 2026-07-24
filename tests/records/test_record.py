"""Unit tests for canonical serialization, hashing and ids (Blueprint §1)."""

from __future__ import annotations

import hashlib
import json

import pytest

from qrf.kernel.records.record import (
    GENESIS_HASH,
    Record,
    canonical_bytes,
    compute_content_hash,
    new_ulid,
)


# --- canonical_bytes ---------------------------------------------------------
def test_canonical_bytes_stable_under_key_order():
    a = canonical_bytes({"b": 2, "a": 1, "c": 3})
    b = canonical_bytes({"c": 3, "a": 1, "b": 2})
    assert a == b == b'{"a":1,"b":2,"c":3}'


def test_canonical_bytes_no_whitespace():
    assert canonical_bytes({"a": 1, "nested": {"y": 2, "x": 1}}) == (
        b'{"a":1,"nested":{"x":1,"y":2}}'
    )


def test_canonical_bytes_utf8_not_escaped():
    # ensure_ascii=False: non-ASCII stays as UTF-8 bytes, not \uXXXX.
    assert canonical_bytes({"t": "é"}) == b'{"t":"\xc3\xa9"}'


def test_float_repr_cases():
    assert canonical_bytes({"x": 1.0}) == b'{"x":1.0}'
    assert canonical_bytes({"x": 0.1}) == b'{"x":0.1}'
    # Full repr fidelity — the classic 0.1+0.2 case.
    assert canonical_bytes({"x": 0.1 + 0.2}) == b'{"x":0.30000000000000004}'


def test_nan_and_inf_rejected():
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("nan")})
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("inf")})
    with pytest.raises(ValueError):
        canonical_bytes({"x": float("-inf")})


# --- content_hash ------------------------------------------------------------
# Hand-computed vector (Blueprint §1.1). Recompute independently from the spec
# formula if this ever needs regenerating; a change here means the wire
# contract changed and the IVF must be updated in lockstep.
_VECTOR_HASH = "9ff662316bf89dc9c20cecc15107f8df55beb8f981995c85e5c3a23e74e4e905"


def test_content_hash_matches_hand_computed_vector():
    got = compute_content_hash(
        record_type="note",
        schema_version=1,
        producer="human:tester",
        event_ts=1700000000000000000,
        parents=[],
        payload={"text": "hello"},
    )
    assert got == _VECTOR_HASH

    # Independently reproduce the digest straight from the §1.3 spec text.
    body = {
        "record_type": "note",
        "schema_version": 1,
        "producer": "human:tester",
        "event_ts": 1700000000000000000,
        "parents": [],
        "payload": {"text": "hello"},
    }
    spec_bytes = json.dumps(
        body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    assert got == hashlib.sha256(spec_bytes).hexdigest()


def test_content_hash_excludes_meta_and_recorded_ts():
    common = dict(
        record_type="note",
        schema_version=1,
        producer="p",
        event_ts=1,
        parents=[],
        payload={"text": "x"},
        prev_hash=GENESIS_HASH,
    )
    r1 = Record.create(record_id="A", recorded_ts=10, meta={"tag": "a"}, **common)
    r2 = Record.create(record_id="B", recorded_ts=999, meta={"tag": "different"}, **common)
    assert r1.content_hash == r2.content_hash


def test_content_hash_changes_with_payload():
    base = dict(
        record_type="note",
        schema_version=1,
        producer="p",
        event_ts=1,
        parents=[],
        prev_hash=GENESIS_HASH,
        record_id="A",
        recorded_ts=1,
    )
    h1 = Record.create(payload={"text": "x"}, **base).content_hash
    h2 = Record.create(payload={"text": "y"}, **base).content_hash
    assert h1 != h2


# --- ULIDs -------------------------------------------------------------------
def test_new_ulid_strictly_increasing_and_26_chars():
    prev = None
    ids = []
    for _ in range(1000):
        u = new_ulid(prev)
        ids.append(u)
        prev = u
    assert ids == sorted(ids)  # strictly increasing
    assert len(set(ids)) == len(ids)  # unique
    assert all(len(u) == 26 for u in ids)


# --- wire round-trip ---------------------------------------------------------
def test_wire_roundtrip_and_recompute():
    r = Record.create(
        record_id="01ABCDEF",
        record_type="note",
        schema_version=1,
        producer="p",
        event_ts=5,
        recorded_ts=6,
        parents=["x"],
        payload={"text": "y"},
        prev_hash=GENESIS_HASH,
    )
    r2 = Record.from_wire(r.to_wire())
    assert r2 == r
    assert r2.recompute_content_hash() == r.content_hash
