"""Provenance / integrity gate for the vendored ``smc_toolkit`` source (DEVQ-021).

The Architect ruling (inbox/CLOSED/DEVQ-021) vendors two files from
``github.com/Louisjzhao/smc-toolkit`` at commit
``812de852f0e0a6bf454720d0ea11ad5c7c64b4ef`` as an offline, drift-proof test
fixture (the PyPI package is an empty publish — FINDING F-021-1). Each vendored
file carries a provenance header recording the upstream sha256 of the bytes BELOW a
sentinel line. This test re-computes those hashes so any silent edit to the pristine
upstream code (or a bad re-vendor) fails loudly, exactly as a pinned dependency
would.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / "smc_toolkit_vendored"
UPSTREAM_COMMIT = "812de852f0e0a6bf454720d0ea11ad5c7c64b4ef"
_SENTINEL = b"=== VENDORED UPSTREAM BEGINS"

# The upstream sha256s the Architect recorded in the DEVQ-021 ruling.
EXPECTED_SHA256 = {
    "core.py": "056a9fdbb20a8e4e26141f41c5b8d5540a2f40f9313e2bd2289c282f7b92288f",
    "__init__.py": "82267473162398aef8e858a4f8fa20c7541ed3fea80d40c44f3dc7a2e8acf449",
}


def _upstream_bytes(path: Path) -> bytes:
    """Return the pristine upstream bytes — everything after the sentinel line."""
    data = path.read_bytes()
    i = data.find(_SENTINEL)
    assert i != -1, f"{path.name}: provenance sentinel missing"
    return data[data.find(b"\n", i) + 1:]


def test_license_present_and_mit():
    text = (VENDOR_DIR / "LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in text


def test_vendored_files_match_recorded_upstream_sha256():
    for name, expected in EXPECTED_SHA256.items():
        got = hashlib.sha256(_upstream_bytes(VENDOR_DIR / name)).hexdigest()
        assert got == expected, (
            f"{name}: upstream bytes hash {got} != recorded {expected} — the vendored "
            "copy has drifted from the pinned commit"
        )


def test_provenance_headers_record_commit_and_hash():
    for name, expected in EXPECTED_SHA256.items():
        header = (VENDOR_DIR / name).read_text(encoding="utf-8").split("\n")
        header_text = "\n".join(header)
        assert UPSTREAM_COMMIT in header_text, f"{name}: commit SHA not in provenance header"
        assert expected in header_text, f"{name}: upstream sha256 not in provenance header"
        assert "github.com/Louisjzhao/smc-toolkit" in header_text
