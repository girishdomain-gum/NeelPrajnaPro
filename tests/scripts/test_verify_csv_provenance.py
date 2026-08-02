"""Tests for scripts/verify_csv_provenance.py (AM-07 item 7, O-049).

Drill law: a hash-binding check is not evidence until shown able to
REFUSE a genuinely mismatched file, not merely accept a matching one.
"""

import hashlib

import pytest

from qrf.kernel.errors import SchemaViolation
from scripts.verify_csv_provenance import (
    default_provenance_path,
    read_provenance,
    verify_csv_provenance,
)


def _write_pair(tmp_path, csv_bytes: bytes, *, sha256: str | None = "__AUTO__"):
    csv_path = tmp_path / "sample.csv"
    csv_path.write_bytes(csv_bytes)
    if sha256 == "__AUTO__":
        sha256 = hashlib.sha256(csv_bytes).hexdigest()
    prov_path = tmp_path / "sample.provenance.txt"
    lines = ["format: QRF data export provenance (rev 1, Python acquisition variant)"]
    if sha256 is not None:
        lines.append(f"csv_sha256: {sha256}")
    prov_path.write_text("\n".join(lines) + "\n", encoding="ascii")
    return csv_path, prov_path


def test_matching_hash_passes(tmp_path):
    csv_path, prov_path = _write_pair(tmp_path, b"time,close\n1,2\n")
    digest = verify_csv_provenance(csv_path, prov_path)
    assert digest == hashlib.sha256(b"time,close\n1,2\n").hexdigest()


def test_default_provenance_path_matches_export_naming_convention(tmp_path):
    csv_path = tmp_path / "QRF_XAUUSD_PERIOD_M5_20251001_20251130_r6_wo10.csv"
    csv_path.write_bytes(b"x")
    expected = tmp_path / "QRF_XAUUSD_PERIOD_M5_20251001_20251130_r6_wo10.provenance.txt"
    assert default_provenance_path(csv_path) == expected


def test_default_provenance_path_used_when_not_given(tmp_path):
    csv_path, _ = _write_pair(tmp_path, b"abc")
    digest = verify_csv_provenance(csv_path)  # no provenance_path arg
    assert digest == hashlib.sha256(b"abc").hexdigest()


# --- DRILL: a one-byte-altered copy must be REFUSED, not silently passed --
def test_one_byte_altered_csv_is_refused(tmp_path):
    csv_path, prov_path = _write_pair(tmp_path, b"time,close\n1,2\n")
    csv_path.write_bytes(b"time,close\n1,3\n")  # one byte different, same length
    with pytest.raises(SchemaViolation, match="sha256"):
        verify_csv_provenance(csv_path, prov_path)


def test_missing_csv_sha256_field_is_refused(tmp_path):
    csv_path, prov_path = _write_pair(tmp_path, b"x", sha256=None)
    with pytest.raises(SchemaViolation, match="csv_sha256"):
        verify_csv_provenance(csv_path, prov_path)


def test_missing_csv_file_is_refused(tmp_path):
    _, prov_path = _write_pair(tmp_path, b"x")
    with pytest.raises(SchemaViolation, match="not found"):
        verify_csv_provenance(tmp_path / "does_not_exist.csv", prov_path)


def test_missing_provenance_file_is_refused(tmp_path):
    csv_path = tmp_path / "lonely.csv"
    csv_path.write_bytes(b"x")
    with pytest.raises(SchemaViolation, match="not found"):
        verify_csv_provenance(csv_path, tmp_path / "lonely.provenance.txt")


def test_read_provenance_parses_key_value_lines(tmp_path):
    p = tmp_path / "p.txt"
    p.write_text("symbol: XAUUSD\ncsv_sha256: deadbeef\n\n", encoding="ascii")
    parsed = read_provenance(p)
    assert parsed == {"symbol": "XAUUSD", "csv_sha256": "deadbeef"}


# --- integration: the two REAL WO-10 exports, once their twins carry the hash --
def test_real_wo10_exports_verify_against_their_provenance_twins():
    """Non-vacuous: uses the actual on-disk CSVs this sprint's AM-07 work
    is moving house, proving the recorded hash really is theirs."""
    from pathlib import Path

    base = Path("data/incoming")
    pairs = [
        base / "QRF_XAUUSD_PERIOD_M5_20251001_20251130_r6_wo10.csv",
        base / "QRF_XAUUSD_PERIOD_M5_20260215_20260415_r6_wo10_2026q1.csv",
    ]
    checked = 0
    for csv_path in pairs:
        if not csv_path.exists():
            continue
        verify_csv_provenance(csv_path)  # raises loudly if it fails
        checked += 1
    assert checked == 2, "expected both real WO-10 exports to be present and verified"
