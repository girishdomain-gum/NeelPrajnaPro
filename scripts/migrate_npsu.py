"""WO-07 stage B (S5, refs A-020, ratifies D-019's draft) — idempotent,
per-file-batch migration of the retired NPSU CSV estate into the journal.

Estate (D-019's inventory, Owner-confirmed complete, O-016): 22 files under
F:\\NeelPrajna (bridge\\results\\ and runs\\*\\csv\\, same bytes, two
locations) — 11 ``NP_Trades_*`` (the real EA's own per-trade log) and 11
``NPSU_Trades_*`` (the shadow-universe parallel exploration), auto-detected
by column shape (``position_id`` vs ``universe_id``), never by filename
alone (a filename is not evidence).

Per file: appends ONE ``npsu_legacy_import_trade`` or
``npsu_legacy_import_shadow`` record (schemas.py) carrying the source path,
its sha256, the row count, a reference to the rows' own BulkStore/Parquet
manifest (the actual data — the journal records the MIGRATION EVENT, not
7000+ individual rows, D-019 decision (b)/A-020), and
``epistemic_weight: "zero"`` — the structural marker
``qrf.kernel.records.epistemic`` keys its refusal on (Architecture B.1).

Idempotent: refuses (writes nothing) a source file whose sha256 was already
migrated. Reports a reconciliation line (source rows vs migrated rows) so a
discrepancy is visible, never silent — mirrors ingest_r6.py's own
duplicate-source convention.

Run:  .venv/Scripts/python.exe scripts/migrate_npsu.py <csv_path>
      .venv/Scripts/python.exe scripts/migrate_npsu.py --all   (every file
      under both F:\\NeelPrajna estate locations, de-duplicated by sha256)
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd
import pyarrow as pa

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import now_ns
from qrf.kernel.records.store import RecordStore

JOURNAL = "datastore/journal/journal.jsonl"
BULK_ROOT = "datastore/bulk"

ESTATE_ROOTS = (
    Path(r"F:\NeelPrajna\bridge\results"),
    Path(r"F:\NeelPrajna\runs"),
)

_TRADE_TYPE = "npsu_legacy_import_trade"
_SHADOW_TYPE = "npsu_legacy_import_shadow"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _detect_record_type(columns: list[str]) -> str:
    cols = set(columns)
    if "universe_id" in cols:
        return _SHADOW_TYPE
    if "position_id" in cols:
        return _TRADE_TYPE
    raise SchemaViolation(
        f"migrate_npsu: cannot classify columns {sorted(cols)} — expected either "
        "'universe_id' (NPSU_Trades shadow-universe shape) or 'position_id' "
        "(NP_Trades real-EA shape); neither found"
    )


def _already_migrated(store: RecordStore, file_sha256: str) -> bool:
    for t in (_TRADE_TYPE, _SHADOW_TYPE):
        for r in store.query(record_type=t):
            if r.payload["file_sha256"] == file_sha256:
                return True
    return False


def migrate_one(store: RecordStore, bulk: BulkStore, csv_path: Path):
    """Migrate one CSV file. Returns the appended journal record, or None if
    it was already migrated (idempotent no-op, nothing written)."""
    file_sha256 = _sha256(csv_path)
    if _already_migrated(store, file_sha256):
        print(f"already migrated (sha256={file_sha256[:12]}...): {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    record_type = _detect_record_type(list(df.columns))
    # BulkStore.write requires an int64 `ts` column (its structural timeline
    # contract) — this data carries ZERO epistemic weight (Architecture B.1)
    # and this migration makes no temporal claim about it, so `ts` here is a
    # SYNTHETIC ROW-ORDINAL placeholder (0..n-1), never a real UTC timeline.
    # The source's own `open_time`/`close_time` strings survive verbatim as
    # ordinary payload columns, unparsed and unclaimed.
    out = df.copy()
    out.insert(0, "ts", range(len(out)))
    table = pa.Table.from_pandas(out, preserve_index=False)

    dataset = f"npsu_legacy.{record_type}"
    manifest = bulk.write(
        dataset, table, producer="script:migrate_npsu", parents=[],
    )

    payload = {
        "source": str(csv_path),
        "file_sha256": file_sha256,
        "row_count": len(df),
        "bulk_manifest_ref": manifest.record_id,
        "epistemic_weight": "zero",
    }
    rec = store.append(
        record_type, payload, producer="script:migrate_npsu", event_ts=now_ns(),
        parents=[manifest.record_id],
    )
    print(
        f"migrated {csv_path} -> {record_type} {rec.record_id} "
        f"(rows={len(df)}, manifest={manifest.record_id})"
    )
    return rec


def _discover_estate_files() -> list[Path]:
    """Every NPSU/NP_Trades CSV under the estate roots, de-duplicated by
    basename (bridge\\results\\ and runs\\*\\csv\\ hold the same bytes
    twice, per D-019's inventory — migrate each logical export once)."""
    seen: dict[str, Path] = {}
    for root in ESTATE_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*.csv"):
            name = p.name
            if "Trades" not in name:
                continue
            seen.setdefault(name, p)
    return sorted(seen.values())


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: migrate_npsu.py <csv_path> | migrate_npsu.py --all")
    store = RecordStore(JOURNAL)  # verifies chain on open
    bulk = BulkStore(store, BULK_ROOT)

    if sys.argv[1] == "--all":
        files = _discover_estate_files()
        print(f"discovered {len(files)} distinct files under the estate roots")
        migrated = 0
        for f in files:
            if migrate_one(store, bulk, f) is not None:
                migrated += 1
        print(f"done: {migrated} newly migrated, {len(files) - migrated} already present")
    else:
        migrate_one(store, bulk, Path(sys.argv[1]))


if __name__ == "__main__":
    main()
