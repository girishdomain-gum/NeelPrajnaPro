"""verify_csv_provenance.py -- AM-07 item 7: ingest BINDS the hash (O-049).

A provenance twin is not a control until something actually checks a CSV
against it. This is that check: recompute the CSV's own sha256 and REFUSE
LOUDLY (SchemaViolation) if it disagrees with the ``csv_sha256`` field
recorded in its provenance twin at export time
(ivf/mt5/export_xauusd_m5.py) -- or if the twin doesn't carry that field
at all (an older or hand-edited twin is not evidence either).

SCOPE NOTE (flagged, not silently assumed): AM-07 names
``scripts/ingest_r6.py`` as a reader of the external evidence store, but
that script ingests a DIFFERENT dataset (tick-level ``local_time,bid,ask``
rows for ``xauusd_ticks_vantage_r6``) with no hardcoded path into
``data/incoming/`` or the new store -- it takes an explicit ``csv_path``
argument today, and nothing in this repo currently reads the M5-bar CSVs
this hash-binding was written for via that script. This module is
therefore a STANDALONE verifier, usable both as a one-off check (this
file's CLI) and, later, as an importable step for whatever script actually
reads a given CSV -- rather than force a wrong wire-up into ingest_r6.py
to satisfy the letter of AM-07 over its substance (drill law: a checker is
not evidence until it can be run, and running it here does not require
guessing at a connection that does not exist yet).

Run:  .venv\\Scripts\\python.exe scripts\\verify_csv_provenance.py <csv_path> [<provenance_path>]
(``provenance_path`` defaults to ``<csv_path stem>.provenance.txt`` beside it,
the exact shape ivf/mt5/export_xauusd_m5.py writes.)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ivf" / "mt5"))
from export_xauusd_m5 import _sha256_file  # noqa: E402

from qrf.kernel.errors import SchemaViolation


def read_provenance(path: Path) -> dict[str, str]:
    """Parses the ``key: value`` provenance twin format (rev 1) back into a
    dict of strings -- the exact shape export_xauusd_m5.py writes."""
    out: dict[str, str] = {}
    text = Path(path).read_text(encoding="ascii")
    for line in text.splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def default_provenance_path(csv_path: Path) -> Path:
    csv_path = Path(csv_path)
    return csv_path.with_suffix("").with_suffix(".provenance.txt")


def verify_csv_provenance(csv_path: Path, provenance_path: Path | None = None) -> str:
    """Recomputes ``csv_path``'s sha256 and compares it to the ``csv_sha256``
    field in its provenance twin. Returns the verified hash on success;
    raises :class:`SchemaViolation`, naming both paths and both hashes, on
    any mismatch or a twin missing the field. Never silently passes."""
    csv_path = Path(csv_path)
    if provenance_path is None:
        provenance_path = default_provenance_path(csv_path)
    else:
        provenance_path = Path(provenance_path)

    if not csv_path.is_file():
        raise SchemaViolation(f"verify_csv_provenance: CSV not found: {csv_path}")
    if not provenance_path.is_file():
        raise SchemaViolation(
            f"verify_csv_provenance: provenance twin not found: {provenance_path}"
        )

    provenance = read_provenance(provenance_path)
    expected = provenance.get("csv_sha256")
    if not expected or expected == "None":
        raise SchemaViolation(
            f"verify_csv_provenance: {provenance_path} carries no csv_sha256 field "
            "-- an untethered CSV is not evidence, refusing"
        )

    actual = _sha256_file(csv_path)
    if actual != expected:
        raise SchemaViolation(
            f"verify_csv_provenance: {csv_path} sha256 {actual} != provenance's "
            f"recorded {expected} ({provenance_path}) -- the file is not the one "
            "the provenance twin describes, refusing"
        )
    return actual


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or len(argv) > 2:
        print("Usage: verify_csv_provenance.py <csv_path> [<provenance_path>]")
        return 2
    csv_path = Path(argv[0])
    provenance_path = Path(argv[1]) if len(argv) == 2 else None
    try:
        digest = verify_csv_provenance(csv_path, provenance_path)
    except SchemaViolation as exc:
        print(f"VERIFY REFUSED: {exc}")
        return 1
    print(f"OK sha256={digest} matches provenance for {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
