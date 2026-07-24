"""RecordStore — the append-only, hash-chained ledger (Blueprint §4.1).

The journal is ``journal.jsonl``: one canonical-JSON record per line, appended
under a single-writer file lock, fsync'd per line. The store is the sole write
path (I-1: no update/delete surface). On construction and on demand it verifies
the hash chain end-to-end (I-2), raising :class:`LedgerIntegrityError` naming
the first bad record. Parents must exist at append time (I-3); payloads must
validate (I-4); corrections are new ``amendment`` records resolved by readers
(I-5).

A crash mid-append leaves a torn final line (bytes after the last newline).
Opening detects it and refuses unless ``heal_truncated=True`` is passed, which
drops the torn tail — healing requires explicit operator confirmation.
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from qrf.kernel.errors import (
    LedgerIntegrityError,
    SchemaViolation,
    UnknownParentError,
    UnknownRecordError,
)
from qrf.kernel.records import schemas
from qrf.kernel.records.record import (
    GENESIS_HASH,
    Record,
    new_ulid,
    now_ns,
)

# --- cross-platform single-writer file lock ----------------------------------
if sys.platform == "win32":
    import msvcrt

    def _lock_fh(fh) -> None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock_fh(fh) -> None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock_fh(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)

    def _unlock_fh(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


@dataclass(frozen=True, slots=True)
class VerifyReport:
    """Result of a chain verification pass."""

    ok: bool
    n_records: int
    head_hash: str


def _read_records_from_disk(path: Path) -> tuple[list[Record], bytes | None]:
    """Parse the journal file. Returns (records, torn_tail_bytes | None).

    A torn tail is bytes following the final newline (an interrupted append).
    A complete line that fails to parse is *not* a torn tail — it is on-disk
    corruption and raises :class:`LedgerIntegrityError`.
    """
    if not path.exists():
        return [], None
    raw = path.read_bytes()
    if not raw:
        return [], None

    torn_tail: bytes | None = None
    if raw.endswith(b"\n"):
        body = raw
    else:
        idx = raw.rfind(b"\n")
        torn_tail = raw[idx + 1 :]
        body = raw[: idx + 1]

    records: list[Record] = []
    for lineno, ln in enumerate(body.split(b"\n")):
        if not ln:
            continue
        try:
            d = json.loads(ln.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            raise LedgerIntegrityError(
                f"journal line {lineno} is not valid JSON: {e}"
            ) from e
        records.append(Record.from_wire(d))
    return records, torn_tail


class RecordStore:
    """Append-only, hash-chained record store."""

    def __init__(self, path: str | os.PathLike, *, heal_truncated: bool = False) -> None:
        self._path = Path(path)
        self._lock_path = Path(str(self._path) + ".lock")
        self._path.parent.mkdir(parents=True, exist_ok=True)

        records, torn_tail = _read_records_from_disk(self._path)
        if torn_tail is not None:
            if not heal_truncated:
                raise LedgerIntegrityError(
                    f"journal {self._path} has a truncated final line "
                    f"({len(torn_tail)} bytes after the last newline); reopen with "
                    "heal_truncated=True to drop it (operator confirmation required)"
                )
            # Heal: physically drop the torn tail, then re-read the clean file.
            with open(self._path, "rb") as f:
                clean = f.read()
            clean = clean[: len(clean) - len(torn_tail)]
            with open(self._path, "wb") as f:
                f.write(clean)
                f.flush()
                os.fsync(f.fileno())
            records, torn_tail = _read_records_from_disk(self._path)

        self._records: list[Record] = records
        self._by_id: dict[str, Record] = {r.record_id: r for r in records}
        self._last_hash: str = records[-1].content_hash if records else GENESIS_HASH
        self._last_ulid: str | None = records[-1].record_id if records else None

        # I-2: verify the chain on startup.
        self.verify()

    # -- write path -----------------------------------------------------------
    @contextmanager
    def _locked(self):
        # Ensure the lock file exists and has a byte to lock (msvcrt needs one).
        if not self._lock_path.exists():
            self._lock_path.write_bytes(b"\0")
        fh = open(self._lock_path, "r+b")
        try:
            _lock_fh(fh)
            yield
        finally:
            try:
                _unlock_fh(fh)
            finally:
                fh.close()

    def append(
        self,
        record_type: str,
        payload: dict,
        *,
        producer: str,
        event_ts: int,
        parents: list[str] | tuple[str, ...] = (),
        meta: dict | None = None,
        schema_version: int = 1,
    ) -> Record:
        """Validate, hash-chain and durably append one record. The only write path."""
        if not isinstance(producer, str) or not producer:
            raise SchemaViolation("producer must be a non-empty string")
        if not isinstance(event_ts, int) or isinstance(event_ts, bool):
            raise SchemaViolation("event_ts must be an int (nanoseconds since epoch)")

        # I-4: payload must validate against the registered schema.
        schemas.validate(record_type, payload, schema_version)

        parents_t = tuple(parents)
        # I-3: parents must exist at append time.
        for parent in parents_t:
            if parent not in self._by_id:
                raise UnknownParentError(f"parent record {parent!r} does not exist")

        payload_copy = dict(payload)
        meta_copy = dict(meta) if meta else {}

        with self._locked():
            record_id = new_ulid(self._last_ulid)
            rec = Record.create(
                record_id=record_id,
                record_type=record_type,
                schema_version=schema_version,
                producer=producer,
                event_ts=event_ts,
                recorded_ts=now_ns(),
                parents=parents_t,
                payload=payload_copy,
                prev_hash=self._last_hash,
                meta=meta_copy,
            )
            line = rec.to_json_line() + b"\n"
            with open(self._path, "ab") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())

            self._records.append(rec)
            self._by_id[record_id] = rec
            self._last_hash = rec.content_hash
            self._last_ulid = record_id

        return rec

    # -- read path ------------------------------------------------------------
    def get(self, record_id: str) -> Record:
        """Return the record with ``record_id`` (raw, un-resolved)."""
        try:
            return self._by_id[record_id]
        except KeyError as e:
            raise UnknownRecordError(f"no record with id {record_id!r}") from e

    def query(
        self,
        *,
        record_type: str | None = None,
        producer_prefix: str | None = None,
        parent: str | None = None,
        ts_range: tuple[int, int] | None = None,
    ) -> Iterator[Record]:
        """Yield records in journal order matching every supplied filter.

        ``ts_range`` is an inclusive ``(lo, hi)`` bound on ``event_ts``.
        ``parent`` matches records that name ``parent`` in their lineage.
        """
        for rec in self._records:
            if record_type is not None and rec.record_type != record_type:
                continue
            if producer_prefix is not None and not rec.producer.startswith(producer_prefix):
                continue
            if parent is not None and parent not in rec.parents:
                continue
            if ts_range is not None:
                lo, hi = ts_range
                if rec.event_ts < lo or rec.event_ts > hi:
                    continue
            yield rec

    def verify(self, full: bool = True) -> VerifyReport:
        """Re-read the journal from disk and verify the hash chain end-to-end.

        Raises :class:`LedgerIntegrityError` naming the first bad record on a
        content-hash mismatch, a broken chain link, or a torn final line.
        """
        records, torn_tail = _read_records_from_disk(self._path)
        if torn_tail is not None:
            raise LedgerIntegrityError(
                f"journal {self._path} has a truncated final line "
                f"({len(torn_tail)} bytes); the last append did not complete"
            )
        prev = GENESIS_HASH
        for rec in records:
            if rec.recompute_content_hash() != rec.content_hash:
                raise LedgerIntegrityError(
                    f"content hash mismatch at record {rec.record_id} — "
                    "a stored field was tampered with"
                )
            if rec.prev_hash != prev:
                raise LedgerIntegrityError(
                    f"broken chain link at record {rec.record_id}: "
                    f"prev_hash {rec.prev_hash} != expected {prev}"
                )
            prev = rec.content_hash
        return VerifyReport(ok=True, n_records=len(records), head_hash=prev)

    def resolve(self, record_id: str) -> Record:
        """Return the amendment-resolved view of ``record_id`` (I-5).

        Amendments targeting the record (``payload.target_ref == record_id``)
        are applied in ULID order as shallow overrides onto the base payload.
        The original record in the journal is never modified.
        """
        base = self.get(record_id)
        amendments = [
            r
            for r in self._records
            if r.record_type == "amendment" and r.payload.get("target_ref") == record_id
        ]
        if not amendments:
            return base
        amendments.sort(key=lambda r: r.record_id)
        corrected = dict(base.payload)
        for am in amendments:
            corrected.update(am.payload.get("correction", {}))
        return Record.create(
            record_id=base.record_id,
            record_type=base.record_type,
            schema_version=base.schema_version,
            producer=base.producer,
            event_ts=base.event_ts,
            recorded_ts=base.recorded_ts,
            parents=base.parents,
            payload=corrected,
            prev_hash=base.prev_hash,
            meta=base.meta,
        )

    # -- convenience ----------------------------------------------------------
    def __len__(self) -> int:
        return len(self._records)

    @property
    def head_hash(self) -> str:
        """Content hash of the most recent record (``GENESIS_HASH`` if empty)."""
        return self._last_hash
