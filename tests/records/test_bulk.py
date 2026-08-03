"""Drills for the bulk store's hash-binding manifest (A-004 §3.2, §5 D7-D8)."""

from qrf.errors import BulkMismatch
from qrf.kernel.records.bulk import BulkStore
from tests.drills.harness import DrillLog, run_drill


def test_bind_and_verify_round_trip(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"some bulk evidence bytes")
    store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")
    payload = store.bind("dataset_a", source)
    assert payload["name"] == "dataset_a"
    assert payload["size"] == len(b"some bulk evidence bytes")
    store.verify()  # must not raise


def test_d7_bulk_file_altered_one_byte_drill(tmp_path):
    log = DrillLog()
    source = tmp_path / "source.bin"
    source.write_bytes(b"0123456789")
    store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")
    store.bind("dataset_a", source)
    bound_path = tmp_path / "bulk" / "dataset_a"

    def checker(tamper: bool):
        if tamper:
            data = bytearray(bound_path.read_bytes())
            data[0] ^= 0xFF  # flip one byte; size is unchanged
            bound_path.write_bytes(bytes(data))
        store.verify()

    try:
        result = run_drill(
            name="D7-bulk-one-byte-altered",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=BulkMismatch,
            log=log,
        )
    finally:
        bound_path.write_bytes(b"0123456789")  # restore for a clean fixture teardown

    assert result.tampered_exception is BulkMismatch


def test_d8_manifest_names_missing_file_drill(tmp_path):
    log = DrillLog()
    source = tmp_path / "source.bin"
    source.write_bytes(b"abcdef")
    store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")
    store.bind("dataset_b", source)
    bound_path = tmp_path / "bulk" / "dataset_b"
    original = bound_path.read_bytes()

    def checker(tamper: bool):
        if tamper:
            bound_path.unlink()
        store.verify()

    try:
        result = run_drill(
            name="D8-manifest-names-missing-file",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=BulkMismatch,
            log=log,
        )
    finally:
        if not bound_path.exists():
            bound_path.write_bytes(original)

    assert result.tampered_exception is BulkMismatch
