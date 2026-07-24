# ARCH-003A · Sprint 3 Close-out · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL.md v1.2 (session log EVERY session — NOTE-011); ARCH-003 completion
report; DEVQ-006/007 CLOSED replies; REV-S3 (findings F-1, drill-2 SKIP);
NOTE-010 §3 (bulk data does not travel via git).

## Scope (small session — three deliverables)

### 1. `--rebuild-bulk` mode (REV-S3 F-1)
`scripts/ingest_xauusd_s3.py --rebuild-bulk`: when the journal already
holds the ingest (current no-op path), re-create the missing parquet
partition(s) from the source CSV using the SAME deterministic write, then
verify the rebuilt file's hash against the EXISTING manifest
(01KYAWHZ6A9X3YZQ2W0BDRFDS1). Match -> print ok. Mismatch -> raise
BulkIntegrityError; never write a new manifest, never append ANY journal
record in this mode. Test: delete the parquet in a tmp datastore copy,
rebuild, assert hash-verified read succeeds and journal byte-identical.

### 2. Quarantine exercise (closes the drill-2 SKIP, REV-S3)
`scripts/exercise_quarantine_s3.py`: in a SCRATCH datastore (tmp dir —
its own RecordStore journal + BulkStore; the real ledger is NEVER
touched), ingest a small synthetic CSV that plants at least one row of
EVERY anomaly class (non_monotonic, duplicate, gap [unexcused],
high_lt_low, nonpositive_price, spread_outlier). Print the scratch paths
of the clean + flagged parquet files and the planted expectations, so the
Owner can run check_s3_dataplane.py WITH --flagged and drill_s3.py
(drill 2 must then run, not SKIP) against them. Assert in a test:
ingest_report v2 params object present; every planted class appears in
anomaly_counts; flagged rows value-match the synthetic source.

### 3. VIRGIN declaration script (Owner's act — you build the tool only)
`scripts/declare_virgin_s3.py --csv <path> --holidays <d1,d2,...>`:
ingests the Owner's BIGGER XAUUSD H1 export as dataset `xauusd_h1_full`
(timeframe 3600, ingest_report v2), prints the report (verdict must be
PASS with 0 unexplained flags before proceeding — abort otherwise), then
asks for interactive confirmation by typing the exact phrase
`DECLARE VIRGIN` before designating a window over a TRAILING portion of
the span as VIRGIN (default: final 30% of rows; `--virgin-fraction` to
override; the leading portion is designated TRAINING). Print all record
ids. The script must REFUSE to run twice (journal check, like the S3
ingest). You implement; you do NOT run the declaration — the Owner runs
it and his console phrase + the printed ids go into GO-S3.md.

## Out of scope
Sprint 4 anything (screener/costs/SMC); ivf/** (Architect-owned); any
edit to existing journal records or manifests; architecture docs.

## Acceptance criteria
- Rebuild mode: hash-verified restore, zero journal writes, test green.
- Exercise: all 6 classes planted AND counted; check runs GREEN with
  --flagged on scratch output; drill 2 reports CAUGHT (not SKIPPED).
- declare_virgin_s3: refuses on non-PASS report; refuses re-run;
  interactive phrase gate; TRAINING + VIRGIN windows over disjoint spans
  (overlap guard must make contamination impossible by construction).

## Definition of Done
Session log (S3-3) pushed; tests green in CI; ruff clean; gen_state run;
completion report appended below; merged to main and pushed; DEVQs for
anything ambiguous (likely area: virgin-fraction boundary semantics —
the boundary bar belongs to TRAINING, VIRGIN starts at the next bar).
