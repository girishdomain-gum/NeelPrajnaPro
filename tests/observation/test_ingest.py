"""E4/E6: ingest cannot be bypassed, and the bulk binding it produces
survives S02's own D7/D8 checks on real (CSV-shaped) data.
"""

from qrf.errors import BulkMismatch, ProvenanceViolation
from qrf.kernel.observation.ingest import ingest_csv
from qrf.kernel.observation.provenance import write_twin
from qrf.kernel.records.bulk import BulkStore
from tests.drills.harness import DrillLog, run_drill


def _metadata(**overrides) -> dict:
    base = {
        "csv_filename": "xauusd_m1.csv",
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
        "row_count": 2,
        "export_timestamp_utc": 1_700_003_601,
        "clock_drift_probe_seconds": 7200.0,
    }
    base.update(overrides)
    return base


def test_ingest_round_trip(tmp_path):
    csv_path = tmp_path / "incoming" / "xauusd_m1.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("time,open,high,low,close\n1,1,1,1,1\n2,2,2,2,2\n", encoding="utf-8")
    twin_path = tmp_path / "provenance" / "xauusd_m1.provenance.json"
    write_twin(csv_path, _metadata(), twin_path)

    bulk_store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")
    payload = ingest_csv(csv_path, twin_path, bulk_store)
    assert payload["name"] == "xauusd_m1.csv"
    bulk_store.verify()  # must not raise


# --- E4: ingest attempted on unverified data is refused, unconditionally -


def test_e4_ingest_refuses_tampered_data_drill(tmp_path):
    log = DrillLog()
    csv_path = tmp_path / "incoming" / "xauusd_m1.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("time,open,high,low,close\n1,1,1,1,1\n2,2,2,2,2\n", encoding="utf-8")
    twin_path = tmp_path / "provenance" / "xauusd_m1.provenance.json"
    write_twin(csv_path, _metadata(), twin_path)
    bulk_store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")

    def checker(tamper: bool):
        if tamper:
            csv_path.write_text("time,open,high,low,close\n999,9,9,9,9\n", encoding="utf-8")
        ingest_csv(csv_path, twin_path, bulk_store)

    result = run_drill(
        name="E4-ingest-refuses-unverified",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=ProvenanceViolation,
        log=log,
    )
    assert result.tampered_exception is ProvenanceViolation
    # confirm nothing tampered was ever bound: the manifest holds only the
    # one clean ingest from the control run
    assert len(bulk_store.manifest.verify()) == 1


def test_e4_ingest_has_no_skip_verification_parameter():
    """There is structurally no way to bypass verification: ingest_csv's
    signature accepts only (csv_path, twin_path, bulk_store).
    """
    import inspect

    sig = inspect.signature(ingest_csv)
    assert list(sig.parameters) == ["csv_path", "twin_path", "bulk_store"]


# --- E6: the bulk binding survives S02's D7/D8 checks on real CSV data --


def test_e6_bound_csv_survives_d7_one_byte_alteration(tmp_path):
    log = DrillLog()
    csv_path = tmp_path / "incoming" / "xauusd_m1.csv"
    csv_path.parent.mkdir(parents=True)
    csv_path.write_text("time,open,high,low,close\n1,1,1,1,1\n2,2,2,2,2\n", encoding="utf-8")
    twin_path = tmp_path / "provenance" / "xauusd_m1.provenance.json"
    write_twin(csv_path, _metadata(), twin_path)
    bulk_store = BulkStore(tmp_path / "bulk", tmp_path / "manifest.jsonl")
    ingest_csv(csv_path, twin_path, bulk_store)
    bound_path = tmp_path / "bulk" / "xauusd_m1.csv"

    def checker(tamper: bool):
        if tamper:
            data = bytearray(bound_path.read_bytes())
            data[0] ^= 0xFF
            bound_path.write_bytes(bytes(data))
        bulk_store.verify()

    result = run_drill(
        name="E6-bound-csv-d7-survives",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=BulkMismatch,
        log=log,
    )
    assert result.tampered_exception is BulkMismatch
