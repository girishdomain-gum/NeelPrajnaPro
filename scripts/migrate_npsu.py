"""WO-07 stage B (S5, refs A-020, ratifies D-019's draft) + addenda (A-028,
A-030 / F-MIG-1) — idempotent, per-file-batch migration of the retired NPSU
CSV estate into the journal, with a --dry-run mode that models its own
cumulative effect ahead of the two-key real run.

Estate (D-019's inventory, Owner-confirmed complete, O-016): 22 files under
F:\\NeelPrajna (bridge\\results\\ and runs\\*\\csv\\, same bytes, two
locations) — 11 ``NP_Trades_*`` (the real EA's own per-trade log) and 11
``NPSU_Trades_*`` (the shadow-universe parallel exploration), auto-detected
by column shape (``position_id`` vs ``universe_id``), never by filename
alone (a filename is not evidence).

CONTENT DUPLICATES (F-MIG-1, A-030): the real estate contains file PAIRS
that are byte-identical under DIFFERENT basenames (not the known bridge\\
results\\ / runs\\*\\csv\\ mirror — a second, distinct duplication). Content
migrates ONCE per sha256; every other path it was ever known under survives
in that one record's ``duplicate_source_paths`` (never silently dropped —
A-030's provenance ruling, see the module's own decision note below).

Per file-group (real run): appends ONE ``npsu_legacy_import_trade`` or
``npsu_legacy_import_shadow`` record (schemas.py) carrying the PRIMARY
source path, its sha256, the row count, a reference to the rows' own
BulkStore/Parquet manifest (D-019 decision (b)/A-020), the full list of any
OTHER paths sharing that sha256 (``duplicate_source_paths``), and
``epistemic_weight: "zero"`` — the structural marker
``qrf.kernel.records.epistemic`` keys its refusal on (Architecture B.1).

PROVENANCE DECISION (A-030's question, answered here — option (b)):
duplicate paths are NOT recorded by mutating an earlier record after the
fact (P5 forbids rewriting; corrections are new records pointing at old
ones) — they are decided and written ONCE, at the primary record's own
creation, using the full file listing already known at that moment
(``_group_by_sha256`` runs before any write). This is why grouping happens
BEFORE the migration loop, not incrementally inside it: the append-only law
is respected by construction, not by exception.

DRY-RUN (A-028, corrected by A-030/F-MIG-1): groups the SAME way the real
path does (``_group_by_sha256`` -> ``_plan_group``, the single source both
share), so a within-batch duplicate is reported as "would SKIP (duplicate
of <primary path>)" — not "would migrate" — making the dry-run's predicted
counts equal to what the real run will actually do, not merely equal to
what it does per-file-in-isolation (F-MIG-1's exact gap). Proven by a test
with two identical-content, different-named fixture files asserting
predicted == actual (A-030 item: "add a test... asserting predicted ==
actual"). Writes NOTHING on the dry-run path — no journal append, no
Parquet, no manifest — proven against both the journal length and the bulk
root's file count (A-028 item 2, unchanged).

Idempotent across separate RUNS too: refuses (writes nothing) a group whose
sha256 already has a migrated record from an earlier invocation.

Run:
  .venv/Scripts/python.exe scripts/migrate_npsu.py <csv_path> [--dry-run]
  .venv/Scripts/python.exe scripts/migrate_npsu.py --all [--dry-run]
  .venv/Scripts/python.exe scripts/migrate_npsu.py --help | -h
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass, field
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
class FileGroup:
    """All known paths sharing one sha256 (byte-identical content), computed
    ONCE over the whole batch before any write — the only way a content
    duplicate spanning two unrelated basenames (F-MIG-1) is ever seen,
    since checking one file at a time never looks sideways at its siblings.
    ``paths[0]`` (path-sorted) is the PRIMARY; the rest are duplicates."""

    file_sha256: str
    paths: list[Path]

    @property
    def primary(self) -> Path:
        return self.paths[0]

    @property
    def duplicates(self) -> list[Path]:
        return self.paths[1:]


def _group_by_sha256(csv_paths: list[Path]) -> list[FileGroup]:
    by_hash: dict[str, list[Path]] = {}
    for p in csv_paths:
        by_hash.setdefault(_sha256(p), []).append(p)
    groups = [
        FileGroup(file_sha256=h, paths=sorted(ps, key=str)) for h, ps in by_hash.items()
    ]
    return sorted(groups, key=lambda g: str(g.primary))


@dataclass(frozen=True)
class MigrationPlan:
    """Everything about one file GROUP the real path needs, computed once
    and shared by both the real migration and --dry-run's report — the only
    way a dry-run can honestly promise "this is what the real run would
    do", including its within-batch cumulative effect (F-MIG-1)."""

    primary_path: Path
    duplicate_paths: list[Path] = field(default_factory=list)
    file_sha256: str = ""
    record_type: str = ""
    row_count: int = 0
    already_migrated: bool = False


def _plan_group(store: RecordStore, group: FileGroup) -> MigrationPlan:
    """Read-only: hashes and classifies one file GROUP. Never writes
    anything — safe to call from both the dry-run report and as the real
    path's own first step. ``group.file_sha256`` is already known (computed
    by :func:`_group_by_sha256`), so no re-hashing here."""
    already = _already_migrated(store, group.file_sha256)
    df = pd.read_csv(group.primary)
    record_type = _detect_record_type(list(df.columns))
    return MigrationPlan(
        primary_path=group.primary, duplicate_paths=group.duplicates,
        file_sha256=group.file_sha256, record_type=record_type,
        row_count=len(df), already_migrated=already,
    )


def migrate_group(store: RecordStore, bulk: BulkStore, group: FileGroup):
    """Migrate one file GROUP (primary + any known content-duplicates).
    Returns the appended journal record, or None if the group's content was
    already migrated (idempotent no-op, nothing written)."""
    plan = _plan_group(store, group)
    if plan.already_migrated:
        print(
            f"already migrated (sha256={plan.file_sha256[:12]}...): {plan.primary_path}"
        )
        return None

    df = pd.read_csv(plan.primary_path)
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
        "source": str(plan.primary_path),
        "file_sha256": plan.file_sha256,
        "row_count": plan.row_count,
        "bulk_manifest_ref": manifest.record_id,
        "epistemic_weight": "zero",
        "duplicate_source_paths": [str(p) for p in plan.duplicate_paths],
    }
    rec = store.append(
        plan.record_type, payload, producer="script:migrate_npsu", event_ts=now_ns(),
        parents=[manifest.record_id],
    )
    dup_note = f", {len(plan.duplicate_paths)} duplicate path(s)" if plan.duplicate_paths else ""
    print(
        f"migrated {plan.primary_path} -> {plan.record_type} {rec.record_id} "
        f"(rows={plan.row_count}, manifest={manifest.record_id}{dup_note})"
    )
    return rec


def migrate_one(store: RecordStore, bulk: BulkStore, csv_path: Path):
    """Single-file convenience wrapper (no sibling grouping — used for the
    CLI's <csv_path> form and by tests that don't need the batch-duplicate
    behavior). Equivalent to migrating a group of exactly one path."""
    return migrate_group(store, bulk, FileGroup(file_sha256=_sha256(csv_path), paths=[csv_path]))


def dry_run(store: RecordStore, csv_paths: list[Path]) -> list[MigrationPlan]:
    """Report-only pass over ``csv_paths``: writes NOTHING (no store.append,
    no BulkStore.write — those calls simply never happen on this path).
    Groups by content FIRST (F-MIG-1) so a within-batch duplicate is
    reported as a skip, not a migrate. Returns the plans so a caller (or a
    test) can assert the totals."""
    groups = _group_by_sha256(csv_paths)
    plans = [_plan_group(store, g) for g in groups]
    for plan in plans:
        if plan.already_migrated:
            status = "ALREADY MIGRATED"
        elif plan.duplicate_paths:
            status = f"would migrate ({len(plan.duplicate_paths)} duplicate path(s) noted)"
        else:
            status = "would migrate"
        print(
            f"[DRY-RUN] {plan.primary_path} -> {plan.record_type} "
            f"rows={plan.row_count} sha256={plan.file_sha256[:12]}... ({status})"
        )
        for dup in plan.duplicate_paths:
            print(f"[DRY-RUN]   would SKIP (duplicate of {plan.primary_path}): {dup}")

    n_discovered = len(csv_paths)
    n_would_migrate = sum(1 for p in plans if not p.already_migrated)
    n_would_skip_duplicate = sum(len(p.duplicate_paths) for p in plans if not p.already_migrated)
    n_already_migrated_groups = sum(1 for p in plans if p.already_migrated)
    by_type: dict[str, int] = {}
    for plan in plans:
        if plan.already_migrated:
            continue
        by_type[plan.record_type] = by_type.get(plan.record_type, 0) + plan.row_count
    print(
        f"[DRY-RUN] totals: {n_discovered} files discovered, {n_would_migrate} would be "
        f"newly migrated, {n_would_skip_duplicate} would SKIP as within-batch duplicates, "
        f"{n_already_migrated_groups} group(s) already migrated in an earlier run, "
        f"rows by type (what would ACTUALLY be written): {by_type} — NOTHING WRITTEN"
    )
    return plans


def _discover_estate_files() -> list[Path]:
    """Every NPSU/NP_Trades CSV under the estate roots, de-duplicated by
    basename (bridge\\results\\ and runs\\*\\csv\\ hold the same bytes
    twice under the SAME name, per D-019's inventory — that mirror is
    collapsed here). Cross-basename content duplicates (F-MIG-1) are a
    SEPARATE concern, handled downstream by :func:`_group_by_sha256` over
    the list this returns — basename-dedup alone cannot see them."""
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
        print(f"discovered {len(files)} distinct-basename files under the estate roots")
        if dry:
            dry_run(store, files)
            return
        groups = _group_by_sha256(files)
        migrated = 0
        for g in groups:
            if migrate_group(store, bulk, g) is not None:
                migrated += 1
        print(f"done: {migrated} newly migrated, {len(groups) - migrated} already present")
    else:
        csv_path = Path(target)
        if dry:
            dry_run(store, [csv_path])
        else:
            migrate_one(store, bulk, csv_path)


if __name__ == "__main__":
    main()
