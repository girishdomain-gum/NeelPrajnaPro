"""BulkStore tests (Blueprint §4.2): hash verification, schema round-trip,
scan ranges, corrupt-file detection, write-once."""

from __future__ import annotations

import pyarrow as pa
import pytest

from qrf.kernel.errors import BulkIntegrityError, SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore


@pytest.fixture
def env(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    bulk = BulkStore(store, tmp_path / "bulk")
    return store, bulk


def _table(ts, price=None):
    price = price if price is not None else [float(x) for x in ts]
    return pa.table(
        {"ts": pa.array(ts, pa.int64()), "open": pa.array(price, pa.float64())}
    )


def test_roundtrip_and_manifest_fields(env):
    store, bulk = env
    t = _table([10, 20, 30])
    m = bulk.write("ds", t, producer="adapter:x", parents=[])

    assert m.record_type == "bulk_manifest"
    p = m.payload
    assert p["dataset"] == "ds"
    assert p["row_count"] == 3
    assert p["ts_min"] == 10 and p["ts_max"] == 30
    assert p["byte_size"] > 0 and len(p["file_sha256"]) == 64
    # Schema recorded == schema read back.
    assert p["columns"] == [{"name": "ts", "dtype": "int64"}, {"name": "open", "dtype": "double"}]

    back = bulk.read(m.record_id)
    assert back.schema.names == ["ts", "open"]
    assert back.column("ts").to_pylist() == [10, 20, 30]
    assert store.verify().ok


def test_scan_range_correctness(env):
    _, bulk = env
    bulk.write("ds", _table([10, 20, 30, 40, 50]), producer="p", parents=[])
    rel = bulk.scan("ds", (20, 40))
    got = sorted(r[0] for r in rel.fetchall())
    assert got == [20, 30, 40]
    # No range -> everything.
    assert bulk.scan("ds").count("ts").fetchone()[0] == 5
    # Empty dataset -> empty relation, not an error.
    assert bulk.scan("nope").fetchall() == []


def test_scan_spans_multiple_write_once_files(env):
    _, bulk = env
    m0 = bulk.write("ds", _table([10, 20]), producer="p", parents=[])
    m1 = bulk.write("ds", _table([30, 40]), producer="p", parents=[])
    # Write-once: two distinct part files, both anchored.
    assert m0.payload["path"] != m1.payload["path"]
    assert m0.payload["path"].endswith("part-00000.parquet")
    assert m1.payload["path"].endswith("part-00001.parquet")
    got = sorted(r[0] for r in bulk.scan("ds").fetchall())
    assert got == [10, 20, 30, 40]


def test_corrupt_byte_detected_and_names_manifest(env):
    _, bulk = env
    m = bulk.write("ds", _table([10, 20, 30]), producer="p", parents=[])
    path = bulk.path_for(m.record_id)

    raw = bytearray(path.read_bytes())
    raw[len(raw) // 2] ^= 0xFF  # flip a byte mid-file
    path.write_bytes(raw)

    with pytest.raises(BulkIntegrityError) as ei:
        bulk.read(m.record_id)
    assert m.record_id in str(ei.value)


def test_missing_file_is_integrity_error(env):
    _, bulk = env
    m = bulk.write("ds", _table([1, 2]), producer="p", parents=[])
    bulk.path_for(m.record_id).unlink()
    with pytest.raises(BulkIntegrityError):
        bulk.read(m.record_id)


def test_write_rejects_empty_and_bad_ts(env):
    _, bulk = env
    with pytest.raises(SchemaViolation):  # empty
        bulk.write("ds", pa.table({"ts": pa.array([], pa.int64())}), producer="p", parents=[])
    with pytest.raises(SchemaViolation):  # no ts column
        bulk.write("ds", pa.table({"x": pa.array([1], pa.int64())}), producer="p", parents=[])
    with pytest.raises(SchemaViolation):  # ts not int64
        bulk.write("ds", pa.table({"ts": pa.array([1.0], pa.float64())}), producer="p", parents=[])


def test_read_non_manifest_rejected(env):
    store, bulk = env
    note = store.append("note", {"text": "hi"}, producer="p", event_ts=1)
    with pytest.raises(SchemaViolation):
        bulk.read(note.record_id)
