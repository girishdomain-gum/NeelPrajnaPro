"""Behaviour tests for RecordStore (Blueprint §4.1, ARCH-001 acceptance)."""

from __future__ import annotations

import pytest

from qrf.kernel.errors import (
    LedgerIntegrityError,
    SchemaViolation,
    UnknownParentError,
    UnknownRecordError,
)
from qrf.kernel.records.record import GENESIS_HASH
from qrf.kernel.records.store import RecordStore

_INSTRUMENT = {
    "instrument_id": "smc.order_block",
    "kind": "detector",
    "version": "0.0.26",
    "params_schema": {"lookback": "int"},
    "code_ref": "qrf.trading.concepts.smc:OrderBlock",
}


@pytest.fixture
def store(tmp_path):
    return RecordStore(tmp_path / "journal.jsonl")


# --- round-trip & chain ------------------------------------------------------
def test_append_get_roundtrip(store):
    r = store.append("note", {"text": "hi"}, producer="human:t", event_ts=1)
    assert store.get(r.record_id) == r
    assert r.prev_hash == GENESIS_HASH
    assert len(r.record_id) == 26
    assert store.verify().ok


def test_chain_links_prev_hash(store):
    a = store.append("note", {"text": "a"}, producer="p", event_ts=1)
    b = store.append("note", {"text": "b"}, producer="p", event_ts=2)
    assert b.prev_hash == a.content_hash
    report = store.verify()
    assert report.n_records == 2
    assert report.head_hash == b.content_hash


def test_get_unknown_raises(store):
    with pytest.raises(UnknownRecordError):
        store.get("01NOPE")


def test_reopen_reproduces_journal(tmp_path):
    p = tmp_path / "journal.jsonl"
    s = RecordStore(p)
    r1 = s.append("note", {"text": "one"}, producer="p", event_ts=1)
    r2 = s.append("note", {"text": "two"}, producer="p", event_ts=2)
    first_bytes = p.read_bytes()

    s2 = RecordStore(p)  # re-open: loads + verifies on startup
    assert len(s2) == 2
    assert s2.get(r1.record_id).content_hash == r1.content_hash
    assert s2.get(r2.record_id).content_hash == r2.content_hash
    # Re-opening does not rewrite the journal.
    assert p.read_bytes() == first_bytes


# --- tamper detection --------------------------------------------------------
def test_tamper_byte_flip_names_record(tmp_path):
    p = tmp_path / "journal.jsonl"
    s = RecordStore(p)
    r1 = s.append("note", {"text": "alpha"}, producer="p", event_ts=1)
    s.append("note", {"text": "bravo"}, producer="p", event_ts=2)

    lines = p.read_bytes().split(b"\n")
    lines[0] = lines[0].replace(b"alpha", b"alphb")  # flip a byte in r1's payload
    p.write_bytes(b"\n".join(lines))

    # verify() re-reads disk and names the first bad record.
    with pytest.raises(LedgerIntegrityError) as ei:
        s.verify()
    assert r1.record_id in str(ei.value)

    # Re-opening the tampered journal also refuses (verify-on-startup).
    with pytest.raises(LedgerIntegrityError):
        RecordStore(p)


def test_tamper_broken_chain_link_detected(tmp_path):
    p = tmp_path / "journal.jsonl"
    s = RecordStore(p)
    s.append("note", {"text": "a"}, producer="p", event_ts=1)
    r2 = s.append("note", {"text": "b"}, producer="p", event_ts=2)

    # Delete the first line entirely -> r2.prev_hash no longer matches genesis.
    lines = [ln for ln in p.read_bytes().split(b"\n") if ln]
    p.write_bytes(lines[1] + b"\n")
    with pytest.raises(LedgerIntegrityError) as ei:
        RecordStore(p)
    assert r2.record_id in str(ei.value)


# --- parent enforcement (I-3) ------------------------------------------------
def test_unknown_parent_rejected(store):
    with pytest.raises(UnknownParentError):
        store.append("note", {"text": "x"}, producer="p", event_ts=1, parents=["01MISSING"])


def test_valid_parent_accepted(store):
    inst = store.append("instrument_registered", _INSTRUMENT, producer="human:boot", event_ts=1)
    child = store.append(
        "note", {"text": "child"}, producer="p", event_ts=2, parents=[inst.record_id]
    )
    assert inst.record_id in child.parents


# --- schema rejection (I-4), all three v1 types ------------------------------
def test_schema_rejection_note(store):
    with pytest.raises(SchemaViolation):
        store.append("note", {"text": 123}, producer="p", event_ts=1)  # wrong type
    with pytest.raises(SchemaViolation):
        store.append("note", {"body": "x"}, producer="p", event_ts=1)  # unknown key


def test_schema_rejection_amendment(store):
    base = store.append("note", {"text": "orig"}, producer="p", event_ts=1)
    with pytest.raises(SchemaViolation):
        store.append(
            "amendment",
            {"target_ref": base.record_id},  # missing 'correction'
            producer="p",
            event_ts=2,
            parents=[base.record_id],
        )


def test_schema_rejection_instrument(store):
    store.append("instrument_registered", _INSTRUMENT, producer="human:boot", event_ts=1)
    bad_kind = dict(_INSTRUMENT, kind="oracle")
    with pytest.raises(SchemaViolation):
        store.append("instrument_registered", bad_kind, producer="human:boot", event_ts=2)
    missing = {"instrument_id": "x", "kind": "data", "version": "1"}
    with pytest.raises(SchemaViolation):
        store.append("instrument_registered", missing, producer="human:boot", event_ts=3)


def test_unregistered_record_type_rejected(store):
    with pytest.raises(SchemaViolation):
        store.append("verdict", {"anything": 1}, producer="p", event_ts=1)


def test_bad_core_fields_rejected(store):
    with pytest.raises(SchemaViolation):
        store.append("note", {"text": "x"}, producer="", event_ts=1)
    with pytest.raises(SchemaViolation):
        store.append("note", {"text": "x"}, producer="p", event_ts=1.5)  # not int


# --- amendment resolution (I-5) ----------------------------------------------
def test_amendment_resolution(store):
    base = store.append("note", {"text": "original"}, producer="p", event_ts=1)
    amd = store.append(
        "amendment",
        {"target_ref": base.record_id, "correction": {"text": "corrected"}},
        producer="human:fix",
        event_ts=2,
        parents=[base.record_id],
    )
    resolved = store.resolve(base.record_id)
    assert resolved.payload["text"] == "corrected"
    # Original is untouched in the journal.
    assert store.get(base.record_id).payload["text"] == "original"
    # A record with no amendments resolves to itself.
    assert store.resolve(amd.record_id).record_id == amd.record_id


def test_amendments_apply_in_ulid_order(store):
    base = store.append("note", {"text": "v0"}, producer="p", event_ts=1)
    store.append(
        "amendment",
        {"target_ref": base.record_id, "correction": {"text": "v1"}},
        producer="p",
        event_ts=2,
        parents=[base.record_id],
    )
    store.append(
        "amendment",
        {"target_ref": base.record_id, "correction": {"text": "v2"}},
        producer="p",
        event_ts=3,
        parents=[base.record_id],
    )
    assert store.resolve(base.record_id).payload["text"] == "v2"  # last wins


# --- crash-mid-append --------------------------------------------------------
def test_truncated_final_line_detected_and_healed(tmp_path):
    p = tmp_path / "journal.jsonl"
    s = RecordStore(p)
    s.append("note", {"text": "one"}, producer="p", event_ts=1)
    r2 = s.append("note", {"text": "two"}, producer="p", event_ts=2)

    # Simulate a crash mid-append: a partial line with no trailing newline.
    with open(p, "ab") as f:
        f.write(b'{"record_id":"01PARTIAL","record_type":"no')

    # Without the heal flag, opening refuses.
    with pytest.raises(LedgerIntegrityError):
        RecordStore(p)

    # With explicit operator confirmation, the torn tail is dropped.
    healed = RecordStore(p, heal_truncated=True)
    assert len(healed) == 2
    assert healed.verify().ok
    assert healed.get(r2.record_id).payload["text"] == "two"
    assert p.read_bytes().endswith(b"\n")

    # Appends continue cleanly after healing.
    r3 = healed.append("note", {"text": "three"}, producer="p", event_ts=3)
    assert r3.prev_hash == r2.content_hash


def test_mid_chain_corruption_never_auto_healed(tmp_path):
    # A complete but non-JSON line is corruption, not a torn tail: heal must not
    # silently swallow it.
    p = tmp_path / "journal.jsonl"
    s = RecordStore(p)
    s.append("note", {"text": "a"}, producer="p", event_ts=1)
    raw = p.read_bytes()
    p.write_bytes(b"this is not json\n" + raw)
    with pytest.raises(LedgerIntegrityError):
        RecordStore(p, heal_truncated=True)


# --- query filters -----------------------------------------------------------
def test_query_filters(store):
    inst = store.append("instrument_registered", _INSTRUMENT, producer="human:boot", event_ts=100)
    n1 = store.append(
        "note", {"text": "a"}, producer="human:alice", event_ts=200, parents=[inst.record_id]
    )
    n2 = store.append("note", {"text": "b"}, producer="bot:x", event_ts=300)

    by_type = {r.record_id for r in store.query(record_type="note")}
    assert by_type == {n1.record_id, n2.record_id}

    by_producer = {r.record_id for r in store.query(producer_prefix="human:")}
    assert by_producer == {inst.record_id, n1.record_id}

    by_parent = [r.record_id for r in store.query(parent=inst.record_id)]
    assert by_parent == [n1.record_id]

    in_range = {r.record_id for r in store.query(ts_range=(200, 300))}
    assert in_range == {n1.record_id, n2.record_id}

    narrow = {r.record_id for r in store.query(ts_range=(150, 250))}
    assert narrow == {n1.record_id}


def test_ulids_strictly_increasing_within_session(store):
    ids = [
        store.append("note", {"text": str(i)}, producer="p", event_ts=i).record_id
        for i in range(200)
    ]
    assert ids == sorted(ids)
    assert len(set(ids)) == len(ids)
