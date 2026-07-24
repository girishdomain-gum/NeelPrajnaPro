# NOTE-009 · FYI · Sprint 3 · 2026-07-25
Author: developer (claude-code)
Note: allocated NOTE-008 first, renamed to NOTE-009 on merge — main already held
NOTE-008 (reducing_owner_mediation); per NOTE-005 the later allocation renames.
Refs: ARCH-003 §Kernel (schemas.py list; WindowLedger.burn); Blueprint §2
`window_burn`, §4.6

## Discovery (no reply needed)
ARCH-003's schemas.py deliverable lists three payload schemas to add:
`bulk_manifest`, `ingest_report`, `window`. But WindowLedger's `burn()` — which
the instruction requires to exist and to be exercised by the §4.6 tests this
sprint — appends a `window_burn` record, and `RecordStore.append` validates every
payload against a registered schema (I-4). So `burn()` cannot run without a
`window_burn` schema.

I therefore also registered `("window_burn", 1)` per Blueprint §2 (fields
`window_ref`, `lineage`, `consumed_by`). This is not an architecture change: the
type and its fields are already defined in Blueprint §2; I only made the schema
table match what §4.6 needs to function. The overlap-matrix / burn-round-trip
tests in `tests/protocol/test_windows.py` exercise it.

No reply needed — recording the four-not-three schema count so the ledger schema
registry and the ARCH-003 text are reconciled in the record.
