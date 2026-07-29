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

---
## COMPLETION REPORT (developer)
Author: developer (claude-code) · 2026-07-25 · Session S3-3 · Status: **COMPLETE**
— three deliverables built + tested end-to-end, merged, pushed. No DEVQ needed:
the one flagged-ambiguous area (virgin-fraction boundary) was resolved in the
instruction itself (boundary bar → TRAINING) and implemented exactly.

### 1. `--rebuild-bulk` (REV-S3 F-1) — `scripts/ingest_xauusd_s3.py`
`rebuild_bulk()` reproduces the adapter's deterministic transform + write for the
dataset's partition(s) and hash-verifies each rebuilt file against its EXISTING
manifest via `BulkStore.read` (raises `BulkIntegrityError` on mismatch). Appends
**nothing** to the journal, mints no manifest (asserted: `len(store)` unchanged).
Verified live: deleted the real `xauusd_h1_sample` parquet, rebuilt, hash-verified
read of manifest 01KYAWHZ6A9X3YZQ2W0BDRFDS1 succeeded, journal byte-identical
(12785 bytes, 12 records). Test: ingest→snapshot→delete→rebuild→read-ok +
journal-byte-identical.

### 2. Quarantine exercise (closes drill-2 SKIP) — `scripts/exercise_quarantine_s3.py`
Ingests a 9-row synthetic CSV into a **scratch** datastore (tmp dir; the real
ledger is never touched) planting one row of every anomaly class
(non_monotonic, duplicate, gap, high_lt_low, nonpositive_price, spread_outlier);
prints scratch clean/flagged parquet paths, planted expectations, and the exact
`check_s3_dataplane.py --flagged` / `drill_s3.py` commands. Verified against the
real IVF tools on the scratch output: **check GREEN** (section B AUDITED, not
vacuous; source=9 clean=3 flagged=6) and **drill 2 CAUGHT** (no longer SKIPPED).
Test: ingest_report v2 `params` present; all 6 classes in `anomaly_counts`;
flagged rows value-match the synthetic source.

### 3. VIRGIN declaration tool — `scripts/declare_virgin_s3.py` (Owner runs it)
Ingests the Owner's bigger export as `xauusd_h1_full` (ingest_report v2). Guards,
in order: refuse if a `xauusd_h1_full` window already exists (re-run guard); a
**dry pass** aborts with nothing written unless the export ingests with 0
unexplained flags; verdict must be PASS. Then the interactive gate requires the
exact phrase `DECLARE VIRGIN` before designating a TRAILING VIRGIN window
(default final 30%, `--virgin-fraction`) and a leading TRAINING window over
**disjoint half-open intervals** — TRAINING `[first, boundary)`, VIRGIN
`[boundary, last+1)` — so contamination is impossible by construction (boundary
bar is the last TRAINING bar; VIRGIN starts at the next). Prints all record ids.
**Not run by the Developer** — the Owner runs it; the console phrase + printed ids
go into GO-S3.md. Tests: exact-phrase gate; split semantics; clean-vs-dirty dry
pass; disjoint TRAINING/VIRGIN + re-run guard trips.

### Verification
133 tests pass (+6 script tests), firewall GREEN, ruff clean, gen_state run
(hand sections byte-for-byte intact), journal 12 records chain GREEN (this session
appended **no** journal records — rebuild writes none, exercise uses a scratch
store, and the VIRGIN declaration is the Owner's act). IVF check GREEN + drill 2
CAUGHT confirmed on scratch output.
