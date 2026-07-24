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

---
## COMPLETION REPORT (developer)
Author: developer (claude-code) · 2026-07-25 · Status: **COMPLETE** — all AC
met, tests green, ruff clean, gen_state run, branch ready to merge. Two
QUESTION-level DEVQs filed (non-blocking, in the areas the DoD anticipated).

### T0 — done first
GO-S2 sign-off appended as a `note` record, producer `human:girish`, parent =
GO-S1 note `01KYAJA3TMM03K1MYMCTRE9033`. Record id
**01KYAVQFR4F94XPMT3C52TFFW0**. Chain re-verified GREEN. Commit
`ARCH-003: T0 GO-S2 ledger note` (`scripts/note_go_s2.py`, idempotent).

### Built — Kernel (`qrf/kernel/`, domain-blind; firewall GREEN)
- `records/bulk.py` — **BulkStore** (§4.2). `write` is write-once
  (`part-NNNNN.parquet` per dataset, never overwritten) and returns a
  `bulk_manifest` (path, row_count, byte_size, file sha256, column schema,
  ts_min/ts_max). `read` recomputes the file sha256 and raises
  `BulkIntegrityError` (naming the manifest) on any mismatch or missing file.
  `scan(dataset, ts_range)` is a DuckDB relation over the dataset's parquet,
  filtered on the int64 `ts` timeline (empty relation for an empty dataset).
- `protocol/windows.py` — **WindowLedger** (§4.6). `designate` →
  `window` (TRAINING/EXPLORATION/VIRGIN); `check_available` refuses reuse
  (`WindowBurnedError`) on half-open interval intersection with a prior burn
  for the *same lineage and dataset* (touching endpoints do not conflict);
  `burn` → `window_burn` (battery-only in production; unit-tested here);
  `guard_observatory` → `ContaminationError` on VIRGIN.
- `records/schemas.py` — v1 payload schemas `bulk_manifest`, `ingest_report`,
  `window`, **and `window_burn`** (needed by `burn`; see NOTE-009).

### Built — Trading plug-in (`qrf/trading/adapters/`)
- `schemas.py` — pandera bar schema (the structural *door*): canonical
  `time,open,high,low,close` required, `tick_volume/spread/real_volume`
  optional; configurable `column_map` (identity default; `IVF_S2_COLUMN_MAP`
  maps `time→time_open_sec`). Only structural faults reject here.
- `mt5_csv.py` — the adapter. **OBS-4 normative**: `ts` = close =
  `open + timeframe_seconds` (int64 ns); timeframe is an explicit **required**
  param, never inferred. Anomalies are **flagged, never repaired/dropped**:
  `non_monotonic`, `duplicate`, `gap` (calendar-aware, DEVQ-006),
  `high_lt_low`, `nonpositive_price`, `spread_outlier` (robust MAD w/
  mean-AD fallback). Flagged rows → `{dataset}__flagged` quarantine (unmodified,
  + a `flags` column); clean rows → `{dataset}`; both via BulkStore manifests.
  Emits an `ingest_report` (parents = manifests) with verdict FAIL only when the
  flagged share exceeds `flagged_threshold` — data always stored in full.

### Carried items (GO-S2)
- Seasonality **gapped-feed** planted-truth case added
  (`fixtures/_gapped_feed_case`, `gapped_feed_first_bar_0100`): first bar of each
  day at 01:00, no midnight bar, post-weekend Monday — asserts dow markers at the
  day's first bar per the ratified DEVQ-005 contract (post-weekend `dow.mon` at
  Mon 01:00, never a back-stamped midnight). Recalibrated in the **real journal**
  (`scripts/recalibrate_seasonality_s3.py`): new `calibration`
  **01KYAWJ0REJ7TSM4PRRT18DXD3** over the 4-case suite (truth=2), parented to the
  existing S2 registration `01KYAKYY1298M1N3JWAA8HBQ5P` — same instrument, no new
  registration minted.
- Renamed `scripts/hand_audit_s2.py` → `scripts/calibration_audit_s2.py`; its
  docstring now states it inspects the SYNTHETIC calibration suite, and that the
  real-evidence HC is `ivf/human/sample_s2_events.py`.

### Real ingest (`scripts/ingest_xauusd_s3.py`, idempotent)
`IVF_S2_XAUUSD_PERIOD_H1.csv` → dataset `xauusd_h1_sample`: **504 rows, 0
flagged, verdict PASS** (weekend holes weekend-excused; the 2024-01-15 MLK holiday
hole passed as a declared holiday → 0 unexplained flags). ingest_report
**01KYAWHZ77SYPEMPYDY25X8CC1**, manifest **01KYAWHZ6A9X3YZQ2W0BDRFDS1**, then
designated **TRAINING** window **01KYAWHZ86ZNDGY4NZNCF4XFY0** over the full span.
No VIRGIN declaration (Owner's act at close-out, per instruction). Journal now
**12 records, chain GREEN**.

### Acceptance criteria — all met
- Round-trip: ingest → manifest in journal → `read` verifies hash → `scan`
  returns correct ranges; a flipped byte makes `read` raise `BulkIntegrityError`
  naming the manifest. ✔ (`tests/records/test_bulk.py`; verified on the real
  dataset too — the parquet write is byte-deterministic, so the manifest hash
  reproduces exactly.)
- Flagged rows present unmodified in quarantine; clean+flagged = input;
  ingest_report matches by independent count. ✔
- Overlap matrix (touching/containing/contained/disjoint), lineage + dataset
  isolation, VIRGIN guard. ✔ (`tests/protocol/test_windows.py`)
- OBS-4: `ts == open + timeframe` for every row. ✔
- Gapped-feed seasonality calibration passes; journal chain GREEN. ✔
- `xauusd_h1_sample` ingested with 0 unexplained flags. ✔

### Tests / tooling
124 passed (was 87; +37: bulk, windows, data-plane schemas, adapter OBS-4 /
each anomaly class / quarantine integrity / threshold-FAIL / column-mapping /
door rejection / real-export-zero-flags, gapped-feed dow). Firewall GREEN.
`ruff check .` clean. `gen_state.py` run — DERIVED rows recomputed, both
hand-maintained sections byte-for-byte intact.

### Open DEVQs (QUESTION, non-blocking)
- **DEVQ-006** — weekend/holiday gap allowance design (recommend ratify the
  parameterized rule; defer a trading-calendar module).
- **DEVQ-007** — quarantine dataset naming (recommend ratify `{dataset}__flagged`
  + `flags` column).
- **NOTE-009** (FYI) — `window_burn` schema added (4 schemas, not the 3 listed);
  required for `burn()` to function; type already in Blueprint §2.
