"""BulkStore — Parquet series with a hash-verified manifest in the ledger.

Implementation Blueprint v1.0 §4.2 and the manifest pattern (§1.4, ADR-003).
Heavy series (millions of rows) live as Parquet files under
``datastore/bulk/{dataset}/``; the journal stays small by holding one
``bulk_manifest`` record per file — path, row count, byte size, sha256 of the
file bytes, column schema, and the min/max of the timeline column. The ledger
is therefore the root of trust for gigabytes of data: verifying a manifest
verifies its file.

Contracts (normative):

* **Write-once.** Files are never overwritten. Each :meth:`write` mints a new
  ``part-NNNNN.parquet`` in the dataset directory; a re-ingest of the same
  dataset is a *new file plus a new manifest*, never a mutation of an old one.
* **Hash is truth.** :meth:`read` recomputes the file sha256 and refuses a
  mismatch with :class:`BulkIntegrityError`, naming the manifest record.
* **A timeline column named ``ts``** (int64) is required: it drives the
  manifest ``ts_min``/``ts_max`` and :meth:`scan` range filtering. ``ts`` is
  kernel vocabulary (the EventFrame knowability moment, §4.3) — domain-blind.

This module is kernel: it imports only the records layer, the error taxonomy,
stdlib and the pyarrow/duckdb data libraries (Blueprint §3 import rules).
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

from qrf.kernel.errors import BulkIntegrityError, SchemaViolation
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore

_PART_RE = re.compile(r"^part-(\d{5})\.parquet$")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _columns_schema(table: pa.Table) -> list[dict[str, str]]:
    """The manifest ``columns`` list: ``[{name, dtype}]`` in table order."""
    return [
        {"name": name, "dtype": str(table.schema.field(name).type)}
        for name in table.column_names
    ]


class BulkStore:
    """Parquet writer/reader whose files are anchored by ledger manifests."""

    def __init__(self, store: RecordStore, bulk_root: str | os.PathLike) -> None:
        self._store = store
        self._root = Path(bulk_root)

    # -- write ----------------------------------------------------------------
    def _next_part_path(self, dataset_dir: Path) -> Path:
        """The next unused ``part-NNNNN.parquet`` in ``dataset_dir`` (write-once)."""
        highest = -1
        if dataset_dir.exists():
            for p in dataset_dir.iterdir():
                m = _PART_RE.match(p.name)
                if m:
                    highest = max(highest, int(m.group(1)))
        n = highest + 1
        while True:
            candidate = dataset_dir / f"part-{n:05d}.parquet"
            if not candidate.exists():
                return candidate
            n += 1

    def write(
        self,
        dataset: str,
        table: pa.Table,
        *,
        producer: str,
        parents: list[str] | tuple[str, ...],
    ) -> Record:
        """Write ``table`` to a new Parquet file and append its ``bulk_manifest``.

        The table must be non-empty and carry an int64 ``ts`` column (the
        timeline). Returns the ``bulk_manifest`` record; its id is the
        ``manifest_ref`` used by :meth:`read`.
        """
        if not isinstance(table, pa.Table):
            raise SchemaViolation(
                f"BulkStore.write expects a pyarrow.Table, got {type(table).__name__}"
            )
        if table.num_rows == 0:
            raise SchemaViolation("BulkStore.write refuses an empty table (nothing to anchor)")
        if "ts" not in table.column_names:
            raise SchemaViolation("BulkStore.write requires a 'ts' column (int64 timeline)")
        if not table.schema.field("ts").type.equals(pa.int64()):
            raise SchemaViolation(
                f"BulkStore 'ts' column must be int64, got {table.schema.field('ts').type}"
            )

        dataset_dir = self._root / dataset
        dataset_dir.mkdir(parents=True, exist_ok=True)
        path = self._next_part_path(dataset_dir)

        # Write the file first so the manifest can hash real bytes, then fsync
        # the directory entry (durability before the ledger points at it).
        pq.write_table(table, path)
        file_sha256 = _sha256_file(path)
        byte_size = path.stat().st_size

        ts_col = table.column("ts")
        ts_min = int(pc.min(ts_col).as_py())
        ts_max = int(pc.max(ts_col).as_py())

        # Store the path relative to the bulk root (portable across clones).
        rel_path = path.relative_to(self._root).as_posix()
        payload = {
            "path": rel_path,
            "dataset": dataset,
            "row_count": table.num_rows,
            "byte_size": byte_size,
            "file_sha256": file_sha256,
            "columns": _columns_schema(table),
            "ts_min": ts_min,
            "ts_max": ts_max,
        }
        return self._store.append(
            "bulk_manifest",
            payload,
            producer=producer,
            event_ts=ts_max,
            parents=list(parents),
        )

    # -- read -----------------------------------------------------------------
    def _manifest(self, manifest_ref: str) -> Record:
        rec = self._store.get(manifest_ref)
        if rec.record_type != "bulk_manifest":
            raise SchemaViolation(
                f"record {manifest_ref} is a {rec.record_type!r}, not a bulk_manifest"
            )
        return rec

    def path_for(self, manifest_ref: str) -> Path:
        """Absolute filesystem path of the file a manifest anchors."""
        return self._root / self._manifest(manifest_ref).payload["path"]

    def read(self, manifest_ref: str) -> pa.Table:
        """Read the file a manifest anchors, verifying its sha256 first.

        Raises :class:`BulkIntegrityError` (naming the manifest and path) if the
        file's bytes no longer match the manifest's ``file_sha256``.
        """
        rec = self._manifest(manifest_ref)
        path = self._root / rec.payload["path"]
        if not path.exists():
            raise BulkIntegrityError(
                f"manifest {manifest_ref}: file {path} is missing"
            )
        actual = _sha256_file(path)
        if actual != rec.payload["file_sha256"]:
            raise BulkIntegrityError(
                f"manifest {manifest_ref}: file {rec.payload['path']} sha256 "
                f"{actual} != recorded {rec.payload['file_sha256']} — the file "
                "was modified after ingest (fatal for this file)"
            )
        return pq.read_table(path)

    # -- scan -----------------------------------------------------------------
    def scan(
        self, dataset: str, ts_range: tuple[int, int] | None = None
    ) -> duckdb.DuckDBPyRelation:
        """A DuckDB relation over every Parquet file in ``dataset``.

        ``ts_range`` is an inclusive ``(lo, hi)`` filter on the ``ts`` column.
        Returns an empty relation (correct schema) when the dataset has no files.
        """
        dataset_dir = self._root / dataset
        files = (
            sorted(str(p) for p in dataset_dir.glob("part-*.parquet"))
            if dataset_dir.exists()
            else []
        )
        con = duckdb.connect()
        if not files:
            return con.sql("SELECT NULL AS ts WHERE 1=0")
        rel = con.read_parquet(files)
        if ts_range is not None:
            lo, hi = int(ts_range[0]), int(ts_range[1])
            rel = rel.filter(f"ts >= {lo} AND ts <= {hi}")
        return rel
