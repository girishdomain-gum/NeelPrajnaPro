# ADR-003 — Manifest Pattern for Bulk Data

**Status:** Accepted · 2026-07-24 · Owner: Implementation

## Decision
Heavy series (ticks, bars, events, trades) live in write-once Parquet
files. The journal stores a `bulk_manifest` record per file: path, row
count, byte size, sha256 of file bytes, column schema, ts range.
Reading a file verifies its hash against the manifest first.

## Reason
Keeps the ledger small (thousands of lines) while remaining the root of
trust for gigabytes: verifying a manifest verifies its file. Journal
stays human-readable and fast to chain-verify.

## Alternatives rejected
- Rows-in-journal: journal balloons to GB; chain verification becomes
  hours.
- External data without manifests: silent file corruption or
  substitution becomes undetectable.

## Consequences
Re-ingest = new file + new manifest (never overwrite). BulkStore.read
refuses hash mismatch (BulkIntegrityError).
