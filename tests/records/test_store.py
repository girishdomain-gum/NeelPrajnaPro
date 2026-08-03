"""Drills for the record store's guarantees (A-004 §3, §5 D1-D6)."""

import json

import pytest

from qrf.errors import ChainCorruption, SchemaViolation, TornTail, WriterLockHeld
from qrf.kernel.records.store import GENESIS_HASH, RecordStore
from tests.drills.harness import DrillLog, run_drill


def _validator(payload: dict) -> None:
    if not isinstance(payload.get("n"), int):
        raise SchemaViolation("payload.n must be an int", payload.get("n"))


def test_append_and_verify_round_trip(tmp_path):
    store = RecordStore(tmp_path / "ledger.jsonl", _validator)
    r0 = store.append({"n": 1})
    r1 = store.append({"n": 2})
    assert r0.seq == 0 and r0.prev_hash == GENESIS_HASH
    assert r1.seq == 1 and r1.prev_hash == r0.hash
    records = store.verify()
    assert [r.payload for r in records] == [{"n": 1}, {"n": 2}]


# --- D6: schema validation on write ------------------------------------


def test_d6_schema_violation_on_write_drill(tmp_path):
    log = DrillLog()
    store = RecordStore(tmp_path / "ledger.jsonl", _validator)

    def checker(payload):
        store.append(payload)

    result = run_drill(
        name="D6-schema-violation-on-write",
        checker=checker,
        clean_input={"n": 1},
        tampered_input={"n": "not-an-int"},
        expected_exception=SchemaViolation,
        log=log,
    )
    assert result.tampered_exception is SchemaViolation
    assert [r.payload for r in store.verify()] == [{"n": 1}]


# --- D1/D2/D3: chain corruption (altered / deleted / reordered) --------


def _make_three_record_chain(path):
    store = RecordStore(path, _validator)
    store.append({"n": 1})
    store.append({"n": 2})
    store.append({"n": 3})
    return store


def test_d1_altered_middle_record_drill(tmp_path):
    log = DrillLog()
    path = tmp_path / "ledger.jsonl"

    def checker(tamper: bool):
        _make_three_record_chain(path)
        if tamper:
            lines = path.read_text(encoding="utf-8").splitlines()
            rec = json.loads(lines[1])
            rec["payload"]["n"] = 999  # altered content, hash now stale
            lines[1] = json.dumps(rec)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        RecordStore(path, _validator).verify()

    try:
        result = run_drill(
            name="D1-altered-middle-record",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=ChainCorruption,
            log=log,
        )
    finally:
        path.unlink(missing_ok=True)

    assert result.tampered_exception is ChainCorruption


def test_d2_deleted_record_drill(tmp_path):
    log = DrillLog()
    path = tmp_path / "ledger.jsonl"

    def checker(tamper: bool):
        _make_three_record_chain(path)
        if tamper:
            lines = path.read_text(encoding="utf-8").splitlines()
            del lines[1]  # remove the middle record entirely
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        RecordStore(path, _validator).verify()

    try:
        result = run_drill(
            name="D2-deleted-record",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=ChainCorruption,
            log=log,
        )
    finally:
        path.unlink(missing_ok=True)

    assert result.tampered_exception is ChainCorruption


def test_d3_reordered_records_drill(tmp_path):
    log = DrillLog()
    path = tmp_path / "ledger.jsonl"

    def checker(tamper: bool):
        _make_three_record_chain(path)
        if tamper:
            lines = path.read_text(encoding="utf-8").splitlines()
            lines[0], lines[1] = lines[1], lines[0]  # swap two records
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        RecordStore(path, _validator).verify()

    try:
        result = run_drill(
            name="D3-reordered-records",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=ChainCorruption,
            log=log,
        )
    finally:
        path.unlink(missing_ok=True)

    assert result.tampered_exception is ChainCorruption


# --- D4: torn tail, distinguished from chain corruption ------------------


def test_d4_torn_tail_drill(tmp_path):
    log = DrillLog()
    path = tmp_path / "ledger.jsonl"

    def checker(tamper: bool):
        _make_three_record_chain(path)
        if tamper:
            with open(path, "a", encoding="utf-8") as f:
                f.write('{"seq":3,"prev_hash":"deadbeef","hash":"incomplete')  # no closing, no \n
        RecordStore(path, _validator).verify()

    try:
        result = run_drill(
            name="D4-torn-tail",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=TornTail,
            log=log,
        )
    finally:
        path.unlink(missing_ok=True)

    assert result.tampered_exception is TornTail


def test_d4_torn_tail_is_not_reported_as_chain_corruption(tmp_path):
    """The two failures must never be conflated: a torn tail is
    recoverable and expected; mid-chain corruption never is.
    """
    path = tmp_path / "ledger.jsonl"
    store = _make_three_record_chain(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"seq":3,"broken')
    with pytest.raises(TornTail) as exc_info:
        store.verify()
    assert not isinstance(exc_info.value, ChainCorruption)


def test_recover_torn_tail_leaves_no_trace(tmp_path):
    path = tmp_path / "ledger.jsonl"
    store = _make_three_record_chain(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"seq":3,"broken')
    assert store.recover_torn_tail() is True
    assert [r.payload for r in store.verify()] == [{"n": 1}, {"n": 2}, {"n": 3}]
    # a clean chain has nothing to recover
    assert store.recover_torn_tail() is False


# --- D5: single-writer refusal ------------------------------------------


def test_d5_second_concurrent_writer_refused_drill(tmp_path):
    log = DrillLog()
    store = RecordStore(tmp_path / "ledger.jsonl", _validator)

    def checker(hold_lock: bool):
        if hold_lock:
            # Simulate a second writer: the outer `with store` holds the
            # lock exactly as a concurrent process would; the nested
            # append() is the second writer arriving while it is held.
            with store:
                store.append({"n": 999})
        else:
            store.append({"n": 1})

    result = run_drill(
        name="D5-second-writer-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=WriterLockHeld,
        log=log,
    )
    assert result.tampered_exception is WriterLockHeld
    # the refusal must not have written anything under the held lock
    assert [r.payload for r in store.verify()] == [{"n": 1}]


def test_d5_writer_lock_released_after_append(tmp_path):
    """Confirms the lock is a per-call guard, not a permanent hold: two
    sequential appends (not concurrent) must both succeed.
    """
    store = RecordStore(tmp_path / "ledger.jsonl", _validator)
    store.append({"n": 1})
    store.append({"n": 2})
    assert len(store.verify()) == 2
