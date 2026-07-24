# ARCH-003 · Sprint 3 — Data Plane · 2026-07-24
Author: architect (fable) · Level: INSTRUCTION · Status: OPEN

## Read first (in this order)
1. `docs/coordination/reviews/GO-S2.md` — Sprint 2 closed; carried
   items below are yours this sprint.
2. Blueprint §4.2 (BulkStore), §4.6 (WindowLedger), §2 rows
   `bulk_manifest`, `ingest_report`, `window`, §5 arrows (1)–(4),
   §7 Sprint 3.
3. `docs/coordination/reviews/REV-S2.md` OBS-4 — the close-time
   contract this sprint makes real.
4. ADR-003 (manifest pattern — the why).

## T0 — Ledger note for GO-S2 (do first)
Append one `note` record, producer `human:girish`, parents =
[GO-S1 note record 01KYAJA3TMM03K1MYMCTRE9033]:
"Sprint 2 signed off by Owner: 'S2 VC GREEN, drill RED caught, HC done
— sign off Sprint 2'. GO-S2: VC rev3 GREEN on real XAUUSD (red=0
amber=0), drill S2 caught (144), HC on real sampled events. DEVQ-005
DOW contract ratified."
Commit: `ARCH-003: T0 GO-S2 ledger note`.

## Scope (build exactly this)
Sprint 3 per Blueprint §7: the data plane.

### Kernel
- `qrf/kernel/records/bulk.py` — BulkStore per §4.2: `write(dataset,
  table, producer, parents) -> bulk_manifest record`; `read(manifest_ref)`
  verifying file sha256 first (BulkIntegrityError on mismatch);
  `scan(dataset, ts_range)` via DuckDB over the dataset's parquet files.
  Files write-once under `datastore/bulk/{dataset}/`; re-ingest = new
  file + new manifest, never overwrite.
- `qrf/kernel/records/schemas.py` — add v1 payload schemas:
  `bulk_manifest`, `ingest_report`, `window` (fields per Blueprint §2).
- `qrf/kernel/protocol/windows.py` — WindowLedger per §4.6:
  `designate(dataset, ts_start, ts_end, designation)` →
  window record (TRAINING/EXPLORATION/VIRGIN);
  `check_available(window_ref, lineage)` — WindowBurnedError on overlap
  with a prior burn for that lineage (interval intersection on the same
  dataset; lineage = plain string this sprint);
  `guard_observatory(window_ref)` — ContaminationError if VIRGIN.
  `burn()` exists but is exercised only by tests this sprint (the
  battery arrives in Sprint 5/6); include the §4.6 overlap-matrix tests
  now so the semantics are locked before anything depends on them.

### Trading plug-in
- `qrf/trading/adapters/schemas.py` — pandera schema for MT5-format bar
  CSV (time,open,high,low,close,tick_volume[,spread,real_volume];
  configurable column mapping).
- `qrf/trading/adapters/mt5_csv.py` — the adapter. Contract:
  (a) OBS-4 NORMATIVE: input MT5 bar `time` is the OPEN time; the
      adapter emits `ts` = close time = open + timeframe_seconds, as
      int64 ns UTC-timeline. The timeframe is an explicit required
      parameter — never inferred silently.
  (b) Validation at the door: schema check; anomaly FLAGS (never
      repair, never drop): non-monotonic time, duplicate bar, gap
      larger than K×timeframe outside weekends, high<low, zero/negative
      prices, spread outliers when spread present. Flagged rows go to a
      quarantine parquet (`{dataset}__flagged`), clean rows to the main
      dataset — both via BulkStore with manifests.
  (c) Emits an `ingest_report` record per Blueprint §2 (parents = the
      manifests), verdict PASS unless the flagged share exceeds a
      declared threshold parameter (then FAIL — data still stored,
      nothing deleted).
- Ingest the real Sprint-2 export (`IVF_S2_XAUUSD_PERIOD_H1.csv` — it
  is MT5-format plus extra columns; the mapping handles it) as dataset
  `xauusd_h1_sample`, then `designate` it TRAINING. Do NOT declare a
  VIRGIN reserve yet — that is the Owner's act, over a bigger export,
  at close-out (ARCH-003A will script it).

### Carried items from GO-S2
- Seasonality calibration suite: ADD a gapped-feed planted case (first
  bar of day at 01:00, no midnight bar, post-weekend Monday included)
  asserting markers per the ratified DEVQ-005 contract. Recalibrate;
  new calibration record in the journal.
- Rename `scripts/hand_audit_s2.py` → `scripts/calibration_audit_s2.py`
  with a docstring stating it inspects the SYNTHETIC calibration suite
  (HC uses `ivf/human/sample_s2_events.py` against real evidence).

## Out of scope
Screener, cost models, SMC (Sprint 4); battery; observatory; any ivf/**
edit; live broker connections (CSV files only this sprint).

## Acceptance criteria
- Round-trip: ingest → manifests in journal → `read` verifies hashes →
  `scan` returns correct ranges; corrupting one byte of a parquet file
  makes `read` raise BulkIntegrityError naming the manifest.
- Flagged rows are present, unmodified, in the quarantine dataset;
  clean+flagged row counts sum to input rows; ingest_report matches by
  independent count.
- Overlap matrix green: touching/containing/contained/disjoint windows
  per lineage; VIRGIN guard raises ContaminationError.
- OBS-4 test: adapter output ts == input open + timeframe for every row.
- Gapped-feed seasonality calibration passes; journal chain GREEN.
- The `xauusd_h1_sample` dataset ingested with 0 unexplained flags
  (weekend gaps must NOT flag; Jan-1-holiday gap must NOT flag — the
  gap rule needs a calendar-aware allowance or a documented parameter).

## Required tests (minimum)
§4.2 list (hash verification, schema round-trip, scan ranges, corrupt
detection) · §4.6 list (overlap matrix, lineage isolation, guard) ·
adapter: OBS-4 property, each anomaly class planted and flagged,
quarantine integrity, threshold FAIL path, column-mapping variants ·
carried items' tests.

## Definition of Done
T0 + all above; tests green in CI; ruff clean; gen_state run;
completion report appended below; branch merged to main and pushed
(NOTE-005); DEVQs filed for anything ambiguous. Expected DEVQ areas:
the weekend/holiday gap allowance design, and quarantine dataset
naming. Sprint close (after you): Architect IVF S3 checks
(TickExporter row/price comparison, flagged-row audit, drill S3 silent
repair), Owner HC + VIRGIN declaration + Go/No-Go.
