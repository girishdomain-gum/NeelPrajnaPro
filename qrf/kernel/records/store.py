"""Append-only, hash-chained record store.

Design after reference/NeelPrajnaPro_v1 @ 67b1d69 (the ledger-as-proof
concept: the store holds the PROOF of what evidence was, not just the
evidence), re-implemented from the plan doc (A-004), not the old code.
Per O-005 this store is independent of the previous era's sealed journal —
it is not read, imported, or migrated from it.

Guarantees:
  - APPEND-ONLY: records are added; nothing is ever edited or removed.
  - HASH-CHAINED: each record's hash covers its own payload AND the
    previous record's hash, so altering, deleting, or reordering any
    record invalidates the chain from that point on.
  - SINGLE-WRITER: a second writer while one append is in flight is
    refused by name, never silently interleaved.
  - TORN-TAIL DETECTION: an incomplete final line (a crash mid-write) is
    detected and reported as TornTail, distinct from ChainCorruption (a
    complete but altered/reordered/deleted record).
  - SCHEMA VALIDATION on write: the caller-supplied validator runs before
    anything is written; a bad payload is refused, never coerced.
  - VERIFICATION as a first-class operation: `verify()` walks the whole
    chain and returns it, or raises naming the exact failing index.

CRASH RECOVERY (A-005 R1): a process that dies mid-`append()` never runs
`__exit__`, so the writer `.lock` file survives the crash alongside the
torn tail it left. `recover_torn_tail()` itself needs the lock (it is a
write), so it is correctly BLOCKED by that stale lock, not bricked by it:
the lock is never broken automatically (an auto-timeout could break a lock
held by a writer that is merely slow, not dead, which is worse than a
deadlock). Recovery from a genuine crash is a deliberate two-step
operator action: call `break_lock()` — an explicit admission "I have
confirmed out of band that the previous writer is dead, not slow" — and
only then does `recover_torn_tail()` become reachable. Exercised
end-to-end (lock and torn tail both left behind, exactly as a real death
would) in tests/records/test_store.py::test_d14_crash_recovery_with_lock_held
and, at the window-ledger level, tests/windows/test_ledger.py's D14 drill.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from qrf.errors import ChainCorruption, TornTail, WriterLockHeld

GENESIS_HASH = "0" * 64


def _canonical_bytes(obj: object) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _record_hash(seq: int, prev_hash: str, payload: dict) -> str:
    body = {"seq": seq, "prev_hash": prev_hash, "payload": payload}
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


@dataclass(frozen=True)
class Record:
    seq: int
    prev_hash: str
    hash: str
    payload: dict


class RecordStore:
    """An append-only, hash-chained ledger of JSON records at `path` (one
    file, one JSON object per line). `validator(payload)` runs on every
    `append()` and must raise SchemaViolation (or a subclass) on a bad
    payload.
    """

    def __init__(self, path: Path, validator: Callable[[dict], None]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._validator = validator
        self._lock_path = self.path.with_name(self.path.name + ".lock")

    def __enter__(self) -> RecordStore:
        try:
            fd = os.open(self._lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise WriterLockHeld(self._lock_path) from exc
        os.write(fd, str(os.getpid()).encode("ascii"))
        os.close(fd)
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._lock_path.unlink(missing_ok=True)
        return False

    def _tail_state(self) -> tuple[list[dict], str | None, int]:
        """Return (parsed complete records, torn tail text or None, byte
        length of the confirmed-good prefix). Only the LAST line is ever a
        candidate torn tail; every earlier line that fails to parse is
        corruption, not a crash artifact, and is left for `verify()` to
        report precisely. The byte length lets `recover_torn_tail()`
        truncate the file exactly, rather than re-emit its content.
        """
        if not self.path.exists():
            return [], None, 0
        raw = self.path.read_bytes()
        lines = raw.split(b"\n")
        if lines and lines[-1] == b"":
            lines = lines[:-1]
        if not lines:
            return [], None, 0
        try:
            json.loads(lines[-1])
        except json.JSONDecodeError:
            good = lines[:-1]
            good_len = sum(len(line) + 1 for line in good)
            torn_text = lines[-1].decode("utf-8", "replace")
            return [json.loads(line) for line in good], torn_text, good_len
        good_len = sum(len(line) + 1 for line in lines)
        return [json.loads(line) for line in lines], None, good_len

    def append(self, payload: dict) -> Record:
        self._validator(payload)
        with self:
            records, torn, _ = self._tail_state()
            if torn is not None:
                raise TornTail(
                    len(records), "refusing to append: an unrecovered torn tail exists"
                )
            prev_hash = records[-1]["hash"] if records else GENESIS_HASH
            seq = len(records)
            h = _record_hash(seq, prev_hash, payload)
            record = {"seq": seq, "prev_hash": prev_hash, "hash": h, "payload": payload}
            with open(self.path, "a", encoding="utf-8", newline="\n") as f:
                f.write(_canonical_bytes(record).decode("utf-8") + "\n")
                f.flush()
                os.fsync(f.fileno())
        return Record(**record)

    def verify(self) -> list[Record]:
        """Walk the chain and return every valid Record in order. Raises
        ChainCorruption naming the exact index if a seq, prev_hash, or hash
        does not match what the chain requires. Raises TornTail (after
        confirming every earlier record is sound) if the final line is
        incomplete.
        """
        records, torn, _ = self._tail_state()
        prev_hash = GENESIS_HASH
        out = []
        for i, rec in enumerate(records):
            if not isinstance(rec, dict) or rec.get("seq") != i:
                raise ChainCorruption(i, f"expected seq {i}, found {rec.get('seq')!r}")
            if rec.get("prev_hash") != prev_hash:
                raise ChainCorruption(i, "prev_hash does not match the preceding record")
            expected_hash = _record_hash(i, prev_hash, rec["payload"])
            if rec.get("hash") != expected_hash:
                raise ChainCorruption(i, "stored hash does not match the recomputed hash")
            out.append(
                Record(seq=i, prev_hash=rec["prev_hash"], hash=rec["hash"], payload=rec["payload"])
            )
            prev_hash = rec["hash"]
        if torn is not None:
            raise TornTail(len(records), "the final line is incomplete or not valid JSON")
        return out

    def recover_torn_tail(self) -> bool:
        """If the final line is an incomplete torn tail, TRUNCATE the file
        at the byte offset where the last complete record ends and return
        True — the aborted write leaves no trace, as if it had never been
        attempted. If the chain is already clean, return False. This only
        ever removes bytes; it never re-emits or rewrites a complete
        record, so nothing that hashes the ledger FILE itself (as opposed
        to its parsed content) can be invalidated by recovery.

        Requires the writer lock, exactly like `append()` — if a genuine
        crash left the lock held, call `break_lock()` first (a deliberate,
        separate admission that the previous writer is dead, not slow).
        """
        _records, torn, good_len = self._tail_state()
        if torn is None:
            return False
        with self:
            with open(self.path, "r+b") as f:
                f.truncate(good_len)
        return True

    def break_lock(self) -> bool:
        """Deliberately remove the writer lock, e.g. after confirming out
        of band that the process which held it has died. This bypasses
        single-writer protection: never call it while another writer might
        genuinely still be active. Returns True if a lock was removed,
        False if none existed.
        """
        if self._lock_path.exists():
            self._lock_path.unlink()
            return True
        return False
