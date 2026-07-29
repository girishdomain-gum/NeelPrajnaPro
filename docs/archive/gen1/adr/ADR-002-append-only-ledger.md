# ADR-002 — Append-Only Hash-Chained Ledger as the Sole Store of Truth

**Status:** Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)

## Decision
All knowledge is immutable Records in an append-only JSONL journal,
hash-chained (each record carries the previous record's content hash).
Corrections are new `amendment` records. Derived indexes (DuckDB) are
rebuildable and never authoritative.

## Reason
Knowledge that can be quietly revised is not knowledge. The hash chain
makes any tampering break every subsequent record — auditability by
construction, not policy.

## Alternatives rejected
- Mutable database (SQLite/Postgres): update paths invite silent
  revision; server adds operational weight (violates boring-technology).
- Git-as-ledger: good immutability, poor queryability for records;
  retained for code, not for records.

## Consequences
Bulk data cannot live in the journal → ADR-003 (manifest pattern).
Single-writer file lock; `verify()` on startup. Blueprint §1 defines
the wire schema.
