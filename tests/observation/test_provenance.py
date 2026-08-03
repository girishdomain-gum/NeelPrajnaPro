"""E2/E3/E7: the provenance twin drills (A-007 §3.2, §3.1)."""

import json

from qrf.errors import ProvenanceViolation
from qrf.kernel.observation.provenance import verify, write_twin
from tests.drills.harness import DrillLog, run_drill


def _metadata(**overrides) -> dict:
    base = {
        "csv_filename": "xauusd_m1_2026.csv",
        "symbol": "XAUUSD",
        "timeframe": "M1",
        "broker": "Vantage Markets (Pty) Ltd",
        "server": "VantageMarkets-Demo",
        "account": 25867273,
        "terminal_build": 6090,
        "digits": 2,
        "point": 0.01,
        "trade_tick_size": 0.01,
        "requested_start_utc": 1_700_000_000,
        "requested_end_utc": 1_700_003_600,
        "returned_start_utc": 1_700_000_060,
        "returned_end_utc": 1_700_003_540,
        "row_count": 59,
        "export_timestamp_utc": 1_700_003_601,
        "server_clock_offset_seconds": 7200.0,
    }
    base.update(overrides)
    return base


def test_write_and_verify_round_trip(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"time,open,high,low,close\n1,1,1,1,1\n")
    twin_path = tmp_path / "data.provenance.json"
    payload = write_twin(csv_path, _metadata(), twin_path)
    assert payload["sha256"]
    verified = verify(csv_path, twin_path)
    assert verified["sha256"] == payload["sha256"]


# --- E2: CSV altered by one byte, twin unchanged -------------------------


def test_e2_csv_altered_one_byte_drill(tmp_path):
    log = DrillLog()
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"time,open,high,low,close\n1,1,1,1,1\n")
    twin_path = tmp_path / "data.provenance.json"
    write_twin(csv_path, _metadata(), twin_path)

    def checker(tamper: bool):
        if tamper:
            data = bytearray(csv_path.read_bytes())
            data[0] ^= 0xFF
            csv_path.write_bytes(bytes(data))
        verify(csv_path, twin_path)

    try:
        result = run_drill(
            name="E2-csv-altered-one-byte",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=ProvenanceViolation,
            log=log,
        )
    finally:
        csv_path.write_bytes(b"time,open,high,low,close\n1,1,1,1,1\n")

    assert result.tampered_exception is ProvenanceViolation


# --- E3: twin missing / missing its hash field ---------------------------


def test_e3_missing_twin_drill(tmp_path):
    log = DrillLog()
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"payload")
    present_twin = tmp_path / "present.json"
    write_twin(csv_path, _metadata(), present_twin)
    absent_twin = tmp_path / "absent.json"

    def checker(use_absent: bool):
        verify(csv_path, absent_twin if use_absent else present_twin)

    result = run_drill(
        name="E3-missing-twin",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ProvenanceViolation,
        log=log,
    )
    assert result.tampered_exception is ProvenanceViolation


def test_e3_twin_missing_hash_field_drill(tmp_path):
    log = DrillLog()
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"payload")
    twin_path = tmp_path / "data.provenance.json"
    payload = write_twin(csv_path, _metadata(), twin_path)

    def checker(strip_hash: bool):
        if strip_hash:
            broken = dict(payload)
            del broken["sha256"]
            twin_path.write_text(json.dumps(broken), encoding="utf-8")
        else:
            twin_path.write_text(json.dumps(payload), encoding="utf-8")
        verify(csv_path, twin_path)

    result = run_drill(
        name="E3-twin-missing-hash-field",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ProvenanceViolation,
        log=log,
    )
    assert result.tampered_exception is ProvenanceViolation


# --- E7: returned span differing from requested is recorded honestly ----


def test_e7_returned_span_recorded_even_when_different_from_requested(tmp_path):
    """The twin schema has separate requested_*/returned_* fields, and
    writing one never derives or overwrites the other -- a short-returned
    export is visible in the twin, never silently presented as complete.
    """
    csv_path = tmp_path / "data.csv"
    csv_path.write_bytes(b"payload")
    twin_path = tmp_path / "data.provenance.json"
    metadata = _metadata(
        requested_start_utc=1_700_000_000,
        requested_end_utc=1_700_100_000,  # requested a huge span
        returned_start_utc=1_700_000_060,
        returned_end_utc=1_700_003_540,  # terminal only had a little history
    )
    payload = write_twin(csv_path, metadata, twin_path)
    assert payload["requested_end_utc"] == 1_700_100_000
    assert payload["returned_end_utc"] == 1_700_003_540
    assert payload["returned_end_utc"] != payload["requested_end_utc"]
