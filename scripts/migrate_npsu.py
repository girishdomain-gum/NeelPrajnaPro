"""WO-07 stage B (S5, refs A-020, ratifies D-019's draft) + addendum (A-028)
— idempotent, per-file-batch migration of the retired NPSU CSV estate into
the journal, with a real --dry-run mode ahead of the two-key real run.

Estate (D-019's inventory, Owner-confirmed complete, O-016): 22 files under
F:\\NeelPrajna (bridge\\results\\ and runs\\*\\csv\\, same bytes, two
locations) — 11 ``NP_Trades_*`` (the real EA's own per-trade log) and 11
``NPSU_Trades_*`` (the shadow-universe parallel exploration), auto-detected
by column shape (``position_id`` vs ``universe_id``), never by filename
alone (a filename is not evidence).

Per file (real run): appends ONE ``npsu_legacy_import_trade`` or
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

DRY-RUN (A-028): discovers and classifies EXACTLY as the real path
(``_plan_one`` is the single source both the report and the real migration
share — a dry-run that used separate logic could drift from what the real
run actually does), reports per file, prints reconciliation totals, and
WRITES NOTHING — no journal append, no Parquet, no manifest. This is proven
by a test asserting the journal length and the bulk root's file count are
both unchanged (A-028 item 2), not merely claimed by the flag's name.

Run:
  .venv/Scripts/python.exe scripts/migrate_npsu.py <csv_path> [--dry-run]
  .venv/Scripts/python.exe scripts/migrate_npsu.py --all [--dry-run]
  .venv/Scripts/python.exe scripts/migrate_npsu.py --help | -h
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
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

USAGE = (
    "Usage: migrate_npsu.py <csv_path> [--dry-run]\n"
    "       migrate_npsu.py --all [--dry-run]\n"
    "       migrate_npsu.py --help | -h"
)


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


@dataclass(frozen=True)
class MigrationPlan:
    """Everything about one file the real path needs, computed once and
    shared by both the real migration and --dry-run's report — the ONLY way
    a dry-run can honestly promise "this is what the real run would do"."""

    csv_path: Path
    file_sha256: str
    record_type: str
    row_count: int
    already_migrated: bool


def _plan_one(store: RecordStore, csv_path: Path) -> MigrationPlan:
    """Read-only: hashes and classifies one file. Never writes anything —
    safe to call from both the dry-run report and as the real path's own
    first step."""
    file_sha256 = _sha256(csv_path)
    already = _already_migrated(store, file_sha256)
    df = pd.read_csv(csv_path)
    record_type = _detect_record_type(list(df.columns))
    return MigrationPlan(
        csv_path=csv_path, file_sha256=file_sha256, record_type=record_type,
        row_count=len(df), already_migrated=already,
    )


def migrate_one(store: RecordStore, bulk: BulkStore, csv_path: Path):
    """Migrate one CSV file. Returns the appended journal record, or None if
    it was already migrated (idempotent no-op, nothing written)."""
    plan = _plan_one(store, csv_path)
    if plan.already_migrated:
        print(f"already migrated (sha256={plan.file_sha256[:12]}...): {csv_path}")
        return None

    df = pd.read_csv(csv_path)
    # BulkStore.write requires an int64 `ts` column (its structural timeline
    # contract) — this data carries ZERO epistemic weight (Architecture B.1)
    # and this migration makes no temporal claim about it, so `ts` here is a
    # SYNTHETIC ROW-ORDINAL placeholder (0..n-1), never a real UTC timeline.
    # The source's own `open_time`/`close_time` strings survive verbatim as
    # ordinary payload columns, unparsed and unclaimed.
    out = df.copy()
    out.insert(0, "ts", range(len(out)))
    table = pa.Table.from_pandas(out, preserve_index=False)

    dataset = f"npsu_legacy.{plan.record_type}"
    manifest = bulk.write(
        dataset, table, producer="script:migrate_npsu", parents=[],
    )

    payload = {
        "source": str(csv_path),
        "file_sha256": plan.file_sha256,
        "row_count": plan.row_count,
        "bulk_manifest_ref": manifest.record_id,
        "epistemic_weight": "zero",
    }
    rec = store.append(
        plan.record_type, payload, producer="script:migrate_npsu", event_ts=now_ns(),
        parents=[manifest.record_id],
    )
    print(
        f"migrated {csv_path} -> {plan.record_type} {rec.record_id} "
        f"(rows={plan.row_count}, manifest={manifest.record_id})"
    )
    return rec


def dry_run(store: RecordStore, csv_paths: list[Path]) -> list[MigrationPlan]:
    """Report-only pass over ``csv_paths``: writes NOTHING (no store.append,
    no BulkStore.write — those calls simply never happen on this path).
    Returns the plans so a caller (or a test) can assert the totals."""
    plans = [_plan_one(store, p) for p in csv_paths]
    for plan in plans:
        status = "ALREADY MIGRATED" if plan.already_migrated else "would migrate"
        print(
            f"[DRY-RUN] {plan.csv_path} -> {plan.record_type} "
            f"rows={plan.row_count} sha256={plan.file_sha256[:12]}... ({status})"
        )
    by_type: dict[str, int] = {}
    new_files = 0
    for plan in plans:
        if plan.already_migrated:
            continue
        new_files += 1
        by_type[plan.record_type] = by_type.get(plan.record_type, 0) + plan.row_count
    print(
        f"[DRY-RUN] totals: {len(plans)} files discovered, {new_files} would be "
        f"newly migrated, rows by type: {by_type} — NOTHING WRITTEN"
    )
    return plans


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
    args = sys.argv[1:]
    if not args or "--help" in args or "-h" in args:
        print(USAGE)
        return
    dry = "--dry-run" in args
    positional = [a for a in args if a not in ("--dry-run",)]
    if len(positional) != 1:
        raise SystemExit(USAGE)
    target = positional[0]

    store = RecordStore(JOURNAL)  # verifies chain on open
    bulk = BulkStore(store, BULK_ROOT)

    if target == "--all":
        files = _discover_estate_files()
        print(f"discovered {len(files)} distinct files under the estate roots")
        if dry:
            dry_run(store, files)
            return
        migrated = 0
        for f in files:
            if migrate_one(store, bulk, f) is not None:
                migrated += 1
        print(f"done: {migrated} newly migrated, {len(files) - migrated} already present")
    else:
        csv_path = Path(target)
        if dry:
            dry_run(store, [csv_path])
        else:
            migrate_one(store, bulk, csv_path)


if __name__ == "__main__":
    main()
