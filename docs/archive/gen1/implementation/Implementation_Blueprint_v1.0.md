# QRF Implementation Blueprint v1.0

**Status:** PROPOSED · 24 July 2026
**Governs:** transformation of QRF Architecture v1.1 (frozen) into code
**Mode:** Engineer — concrete interfaces over discussion
**Rule of this document:** every section must reduce implementation
uncertainty. If a section doesn't tell you what to type, it doesn't belong.

---

## 0. Ground Rules

1. **The architecture is frozen.** This document implements v1.1; it does
   not redesign it. If implementation reveals a genuine contradiction,
   the finding is recorded as a `note` record and raised — never patched
   silently.
2. **Kernel purity is mechanical.** `qrf/kernel/**` must not import
   `qrf/trading/**` and must not contain the tokens `price`, `bid`,
   `ask`, `spread`, `pip`, `lot`, `venue` in identifiers. Enforced by
   `tests/test_kernel_firewall.py` (AST + token scan) in CI.
3. **Python 3.13, uv-locked.** All deps pinned in `uv.lock`. New deps
   enter only with the sprint that needs them.
4. **Everything below is testable.** Each interface section ends with
   its required tests. A module without its tests is not done.

---

## 1. The Record — Wire-Level Schema

### 1.1 Field table

| Field | Type | Req | Immutable | Description |
|---|---|---|---|---|
| `record_id` | str (ULID, 26 chars) | ✔ | ✔ | Globally unique, lexically time-sortable. Generated at append time by the store, never by producers. |
| `record_type` | str enum (§2) | ✔ | ✔ | Discriminator for payload schema. |
| `schema_version` | int | ✔ | ✔ | Version of this record_type's payload schema. Starts at 1. |
| `producer` | str | ✔ | ✔ | Instrument identity: `"{instrument_id}@{instrument_version}"`, e.g. `smc.order_block@0.0.26+qrf.2`. Human producers: `human:{name}`. |
| `event_ts` | int64 (ns, UTC epoch) | ✔ | ✔ | When the asserted thing became true/knowable in the world. |
| `recorded_ts` | int64 (ns, UTC epoch) | ✔ | ✔ | When the store appended it. Always ≥ event_ts is NOT required (backfills exist); both always stored. |
| `parents` | list[str] (record_ids) | ✔ (may be `[]`) | ✔ | Lineage. A verdict's parents: hypothesis, window, calibration, manifest(s). |
| `payload` | object (per-type schema) | ✔ | ✔ | The assertion content. Validated against §2 schema before append. |
| `meta` | object | ○ | ✔ | Free-form annotations (tags, notes). Never load-bearing: no code may branch on `meta`. |
| `content_hash` | str (sha256 hex) | ✔ | ✔ | SHA-256 of canonical JSON of `{record_type, schema_version, producer, event_ts, parents, payload}` — sorted keys, UTF-8, no whitespace, floats via `repr`. |
| `prev_hash` | str (sha256 hex) | ✔ | ✔ | `content_hash` of the previous journal record (`"0"*64` for genesis). Makes the journal a hash chain: any edit breaks every later record. |

**Not present by design:** `signature` (cryptographic signing is a
Generation-2 extension; the hash chain covers tamper-evidence for a
solo operator), `updated_at` (nothing updates), `status` on the record
itself (status lives in *later* records that reference this one).

### 1.2 Hard invariants (enforced in `record.py`, tested)

- I-1 Append-only: the store exposes no update/delete surface at all.
- I-2 Hash chain verifies end-to-end on demand and on startup
  (`store.verify()` → raises `LedgerIntegrityError` with first bad id).
- I-3 Parents must exist at append time (`UnknownParentError`).
- I-4 Payload must validate against the registered schema for
  `(record_type, schema_version)` (`SchemaViolation`).
- I-5 Corrections are new records: `record_type="amendment"` with the
  corrected record in `parents` and the correction in payload. Readers
  resolve amendments; the original remains.

### 1.3 Canonical serialization (normative)

```python
def canonical_bytes(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
# floats: json default repr; NaN/Inf forbidden (allow_nan=False) —
# use null and an explicit flag field instead.
```

### 1.4 Storage layout

```
datastore/
├─ journal/journal.jsonl          # THE ledger. One record per line. Append-only.
├─ bulk/                          # heavy series live here, not in the journal
│   └─ {dataset}/{partition}.parquet
└─ index/qrf.duckdb               # DERIVED. Rebuildable from journal+bulk. Never authoritative.
```

**The manifest pattern (key decision):** bulk series (millions of
observation/event rows) are Parquet files; the journal stores a
`bulk_manifest` record per file: path, row count, byte size, sha256 of
file bytes, column schema, min/max event_ts. The ledger therefore stays
small (thousands of lines) while remaining the root of trust for
gigabytes of data — verifying a manifest verifies its file.

---

## 2. Typed Record Catalog (payload schemas, v1)

All payloads are given as field → type. `(○)` = optional.

| record_type | Payload fields | Producer | Typical parents |
|---|---|---|---|
| `instrument_registered` | instrument_id str · kind enum(data/detector/judge) · version str · params_schema obj · code_ref str (module:path or pip pin) | human/bootstrap | [] |
| `calibration` | instrument_ref str · suite_id str · cases list[{case_id, kind enum(planted_truth/planted_noise/insufficient), expected, got, pass bool}] · pass_rate_truth f64 · silence_rate_noise f64 · overall_pass bool | calibration harness | instrument_registered |
| `bulk_manifest` | path str · dataset str · row_count int · byte_size int · file_sha256 str · columns list[{name,dtype}] · ts_min int64 · ts_max int64 | data adapters / detectors | adapter's instrument record |
| `ingest_report` | manifest_refs list · rows_clean int · rows_flagged int · anomaly_counts obj · verdict enum(PASS/FAIL) | data adapter | bulk_manifest(s) |
| `window` | dataset str · ts_start int64 · ts_end int64 · designation enum(TRAINING/EXPLORATION/VIRGIN) | human/protocol | manifest(s) |
| `window_burn` | window_ref str · lineage str · consumed_by str (verdict record_id) | battery (auto) | window, verdict |
| `hypothesis` | lineage str · question_ref str(○) · thesis str · setup_dsl obj · execution obj (entry/stop/target/time_stop) · cost_model_ref str · split_spec obj · outcome_interpretations {PASS:str,FAIL:str,INSUFFICIENT:str} · preregistration_hash str (= this payload's own canonical hash minus this field) · observatory_ancestry list[record_id] | human (composer CLI) | question(○), window |
| `verdict` | hypothesis_ref str · verdict enum(PASS/FAIL/INSUFFICIENT) · n_trades int · gross obj · net obj · statistics obj (per-test name→{stat,p,ci}) · corrections obj {family_m int, method str} · seed int · engine_version str · trades_manifest str | battery | hypothesis, window, calibration, manifests |
| `trial_count` | data_scope str (window_ref or dataset) · lineage str · n_attempts int · source enum(human/screener/generator) · generator_ref str(○) | screener/battery | window |
| `belief_update` | scope enum(family/mechanism) · scope_id str · prior_odds f64 · likelihood_ratio f64 · posterior_odds f64 · driver_ref str (verdict id) | belief layer | verdict, calibration |
| `mechanism` | mechanism_id str · description str · linked_families list[str] · predictions list[str] | human | evidence refs |
| `question` | text str · origin enum(human/belief/observatory/contradiction) · origin_ref str(○) · priority_score f64(○) · status enum(open/answered/retired) via later amendment | any | origin record |
| `observatory_finding` | probe enum(compression/state/info_flow/event_stats/stability) · data_scope str · summary obj · artifact_manifest str(○) | observatory | window (must be TRAINING/EXPLORATION — see ContaminationError) |
| `verification_report` | check_id str · sprint int · class enum(EXACT/NUMERIC/MODELED/STATISTICAL) · rows_compared int · green int · amber int · red int · diffs list · verdict enum(GREEN/AMBER/RED) · human_signoff bool · signoff_notes str · drill_refs list | IVF | verified records |
| `note` / `amendment` | text str / {target_ref, correction obj} | any | target |

Schema evolution rule: additive changes bump `schema_version`; removals
never happen — a new record_type is created instead.

---

## 3. Repository Design — File Level

```
qrf/
├─ pyproject.toml                 # deps, tool config; [tool.qrf] settings
├─ uv.lock
├─ qrf/
│  ├─ kernel/
│  │  ├─ records/
│  │  │  ├─ record.py            # Record dataclass, canonical_bytes, hashing
│  │  │  ├─ schemas.py           # payload schemas per (type, version); validate()
│  │  │  ├─ store.py             # RecordStore: append/get/query/verify
│  │  │  └─ bulk.py              # BulkStore: parquet write/read + manifest emit
│  │  ├─ instruments/
│  │  │  ├─ base.py              # Instrument, Detector protocols; EventFrame spec
│  │  │  ├─ registry.py          # InstrumentRegistry
│  │  │  └─ calibration.py       # CalibrationHarness + case runners
│  │  ├─ registry/
│  │  │  └─ hypotheses.py        # HypothesisRegistry: preregister/freeze/verify
│  │  ├─ protocol/
│  │  │  ├─ windows.py           # WindowLedger: designate/check/burn
│  │  │  ├─ splits.py            # anchored walk-forward, embargo
│  │  │  └─ seeds.py             # seed derivation + recording
│  │  ├─ battery/
│  │  │  ├─ battery.py           # EvidenceBattery: run() orchestration
│  │  │  ├─ tests_stat.py        # statistical test implementations (wraps scipy/arch)
│  │  │  └─ selftest.py          # planted edge / noise / insufficient generators
│  │  ├─ corrections/
│  │  │  └─ trials.py            # TrialCountLedger + Bonferroni/FDR + DSR inputs
│  │  ├─ belief/
│  │  │  ├─ priors.py            # registered family priors + modifiers
│  │  │  └─ update.py            # likelihood-ratio updates from verdicts
│  │  ├─ observatory/
│  │  │  ├─ compression.py  states.py  info_flow.py  event_stats.py
│  │  │  └─ guard.py             # contamination guard (window designation check)
│  │  ├─ graph/
│  │  │  └─ views.py             # DuckDB-derived views: lineage, mechanisms, questions
│  │  └─ errors.py               # full taxonomy (§6)
│  └─ trading/
│     ├─ adapters/  (mt5_csv.py, ccxt_fetch.py, yf_fetch.py, schemas.py)
│     ├─ payloads/  (events.py: price-space semantics; r_units.py)
│     ├─ simulator/ (screener_vbt.py, engine.py, fills.py)
│     ├─ utility/   (cost_models.py: named per-venue models)
│     └─ concepts/  ({family}/detector.py + {family}/fixtures/planted_*.parquet)
├─ configs/         (venues.yaml, datasets.yaml, priors.yaml)
├─ hypotheses/      (H-*.yaml — source of preregistration; hashed into ledger)
├─ datastore/       (journal/ bulk/ index/ — backed up; bulk gitignored)
├─ tests/           (mirrors qrf/; test_kernel_firewall.py; planted fixtures)
├─ dashboard/       (streamlit_app.py, read-only)
└─ docs/            (this file, architecture v1.1, ADRs, runbooks)
```

**Import rules (enforced):**
- `kernel.records` imports nothing from qrf (leaf).
- `kernel.*` may import `kernel.records`, stdlib, numpy/pandas/pyarrow/duckdb/scipy/statsmodels.
- `trading.*` may import `kernel.*`. Reverse is forbidden (firewall test).
- `dashboard` and `tests` may import anything; nothing imports them.

---

## 4. Interface Specifications

Format per module: **Purpose · API · Invariants · Errors · Required tests.**
Signatures are the stable surface; internals are free.

### 4.1 RecordStore (`kernel/records/store.py`)

```python
class RecordStore:
    def append(self, record_type: str, payload: dict, *, producer: str,
               event_ts: int, parents: list[str] = (), meta: dict | None = None,
               schema_version: int = 1) -> Record
    def get(self, record_id: str) -> Record                    # KeyError -> UnknownRecordError
    def query(self, *, record_type: str | None = None,
              producer_prefix: str | None = None,
              parent: str | None = None,
              ts_range: tuple[int, int] | None = None) -> Iterator[Record]
    def verify(self, full: bool = True) -> VerifyReport        # hash chain + manifests
    def resolve(self, record_id: str) -> Record                # amendment-resolved view
```

- Invariants: I-1..I-5 (§1.2). `append` is the only write path; it acquires
  a file lock (single-writer), computes hashes, fsyncs the journal line.
- Errors: `SchemaViolation`, `UnknownParentError`, `LedgerIntegrityError`.
- Tests: round-trip append/get; chain tamper detection (flip one byte →
  verify names exact record); parent enforcement; amendment resolution;
  crash-mid-append leaves valid journal (truncated last line detected & healed
  with operator confirmation only).

### 4.2 BulkStore (`kernel/records/bulk.py`)

```python
class BulkStore:
    def write(self, dataset: str, df: pa.Table, *, producer: str,
              parents: list[str]) -> Record        # returns bulk_manifest record
    def read(self, manifest_ref: str) -> pa.Table  # verifies file sha256 first
    def scan(self, dataset: str, ts_range=None) -> duckdb.Relation
```

- Invariant: `read` refuses a file whose hash mismatches its manifest
  (`BulkIntegrityError`). Files are write-once; re-ingest = new file + manifest.
- Tests: hash verification; schema recorded = schema read; scan range correctness.

### 4.3 Detector contract (`kernel/instruments/base.py`)

```python
class Detector(Protocol):
    instrument_id: str; version: str; family: str
    params: dict                                  # validated vs params_schema
    def detect(self, data: pa.Table) -> pa.Table  # EventFrame
    def planted_cases(self) -> list[CalibrationCase]
```

**EventFrame column spec (normative):**

| column | dtype | rule |
|---|---|---|
| ts | int64 (ns UTC) | knowability moment; confirmation lag applied inside detector |
| event_type | str | namespaced: `{family}.{detector}.{event}` e.g. `smc.fvg.bull` |
| direction | int8 | +1 / −1 / 0 |
| level | f64 | primary level; NaN allowed with meta flag |
| zone_hi / zone_lo | f64 | NaN for point events; zone_hi ≥ zone_lo else SchemaViolation |
| strength | f32 | detector-defined 0..1; documented in detector docstring |
| meta | str (JSON) | family extras; never load-bearing downstream |

- Invariant (anti-hindsight): for every emitted row, `ts` ≥ the timestamp of
  the last input row needed to compute it. Property-tested by feeding data
  incrementally and asserting emissions never change retroactively.
- Tests per detector: planted-truth found; structured-noise silence;
  incremental-consistency property; params round-trip.

### 4.4 InstrumentRegistry + CalibrationHarness

```python
class InstrumentRegistry:
    def register(self, inst) -> Record                       # instrument_registered
    def get(self, instrument_id: str, version: str | None = None) -> InstrumentInfo
    def is_calibrated(self, instrument_ref: str, max_age_days: int | None) -> bool

class CalibrationHarness:
    def run(self, inst, suite: list[CalibrationCase]) -> Record   # calibration record
```

- Invariants: unknown instrument → `UnknownInstrumentError`; any
  record-producing call path checks `is_calibrated` else
  `UncalibratedInstrumentError`; a failed calibration blocks (no soft-pass).
- Tests: registry round-trip; calibration record fields; block-on-fail;
  version bump forces recalibration.

### 4.5 HypothesisRegistry (`kernel/registry/hypotheses.py`)

```python
class HypothesisRegistry:
    def preregister(self, path: Path) -> Record   # parses H-*.yaml, hashes, appends
    def verify_frozen(self, hypothesis_ref: str) -> None
        # recompute file hash vs ledger; mismatch -> TamperedHypothesisError
```

- Invariants: preregistration_hash recomputed from payload must match;
  outcome_interpretations must contain all three keys, non-empty;
  window must exist and be VIRGIN-designated at preregistration time;
  observatory_ancestry entries must reference EXPLORATION-scope findings.
- Tests: freeze/verify; tamper detection; missing-interpretation rejection;
  window-designation rejection.

### 4.6 WindowLedger (`kernel/protocol/windows.py`)

```python
class WindowLedger:
    def designate(self, dataset, ts_start, ts_end, designation) -> Record
    def check_available(self, window_ref: str, lineage: str) -> None
        # overlap with prior burn for lineage -> WindowBurnedError
    def burn(self, window_ref: str, lineage: str, verdict_ref: str) -> Record
    def guard_observatory(self, window_ref: str) -> None
        # designation == VIRGIN -> ContaminationError
```

- Overlap rule: intervals on the same dataset intersecting a burned interval
  for the same lineage (or its declared ancestors) are refused.
- Tests: overlap matrix (touching, containing, disjoint); lineage isolation;
  observatory guard; burn is battery-only (call-site audit test).

### 4.7 EvidenceBattery (`kernel/battery/battery.py`)

```python
class EvidenceBattery:
    def run(self, hypothesis_ref: str, *, simulator: Simulator,
            cost_model: CostModel) -> Record                  # verdict record
```

Pipeline (each step emits into the verdict payload):
1. `verify_frozen(hypothesis)`; 2. `windows.check_available`;
3. `selftest.run_today()` — planted edge PASS / noise FAIL / small-n
   INSUFFICIENT, else `JudgeNotCalibratedError` and abort;
4. derive seed (`seeds.for_run(hypothesis_ref, window_ref)`), record it;
5. simulate via walk-forward splits (embargo from split_spec);
6. statistics: per-test results; block bootstrap CIs (arch);
7. corrections: pull `trial_count` for scope, apply method, record m;
8. verdict decision per pre-registered thresholds;
9. write trades to BulkStore; append verdict; `windows.burn`; emit
   `belief_update` via BeliefLayer hook.

- Invariants: single run per (hypothesis, window) — re-run refused
  (`AlreadyJudgedError`); simulator must be the audited engine
  (screener class rejected by type); gross and net both present.
- Tests: full e2e on synthetic planted edge (PASS), noise (FAIL),
  n=10 (INSUFFICIENT); refusal matrix (unfrozen, burned, uncalibrated,
  screener-passed); determinism: same inputs+seed → byte-identical
  verdict payload.

### 4.8 TrialCountLedger, BeliefLayer, Observatory (abbreviated)

- `trials.bump(scope, lineage, n, source, generator_ref=None)` — screener
  auto-bumps by grid size; battery reads m at step 7. Tests: monotonic;
  generator inheritance.
- `belief.update(verdict_ref)` → belief_update record; LR from the
  day's calibration rates; posterior never read by battery (enforced:
  battery has no import of belief — firewall-style test). Tests: math vs
  hand-computed; ancestry.
- Observatory probes accept only `window_ref`; first line calls
  `guard_observatory`. Findings carry data_scope. Tests: guard; each
  probe on synthetic data with known structure.

---

## 5. Data Flow — Every Arrow Explained

```
(1) broker CSV/API ──adapter──▶ raw frame
(2) raw frame ──pandera validate──▶ clean+flagged frame
(3) frame ──BulkStore.write──▶ observations.parquet + bulk_manifest ──▶ ingest_report
(4) manifest ──WindowLedger.designate──▶ window records (TRAINING/EXPLORATION/VIRGIN)
(5) clean data ──Detector.detect──▶ EventFrame ──BulkStore──▶ events manifest
(6) EXPLORATION data ──Observatory──▶ observatory_finding
(7) human (+findings) ──composer──▶ H-*.yaml ──preregister──▶ hypothesis record
(8) grids ──screener──▶ shortlist + trial_count bump           [never verdicts]
(9) hypothesis ──EvidenceBattery.run──▶ verdict + trades manifest + window_burn
(10) verdict ──BeliefLayer──▶ belief_update
(11) verdicts+findings ──human──▶ mechanism / question / note records
(12) journal+bulk ──rebuild──▶ DuckDB views (lineage, board, beliefs, queue)
```

Arrow contracts: (2) never repairs — flags; (3) manifest hash = file
truth; (4) designation precedes any read by (6)/(9); (5) ts =
knowability; (8) writes no verdict-typed records (type test); (9) is the
only writer of `verdict` and `window_burn`; (12) is derived and
deletable — rebuild test required.

---

## 6. Error Taxonomy (`kernel/errors.py`)

```
QRFError
├─ SchemaViolation            # payload/EventFrame contract broken
├─ UnknownRecordError / UnknownParentError / UnknownInstrumentError
├─ LedgerIntegrityError       # hash chain broken (fatal; halt)
├─ BulkIntegrityError         # parquet hash mismatch (fatal for that file)
├─ UncalibratedInstrumentError# thermometer test missing/stale
├─ JudgeNotCalibratedError    # battery selftest failed today (abort run)
├─ TamperedHypothesisError    # frozen file ≠ ledger hash
├─ WindowBurnedError          # OOS reuse refused
├─ ContaminationError         # observatory touched VIRGIN data
├─ AlreadyJudgedError         # verdict re-run refused
└─ FirewallViolation          # kernel imported domain code (CI-time)
```

Policy: integrity errors halt loudly; refusal errors (burned, unfrozen,
uncalibrated) are expected control flow with actionable messages naming
the exact record ids involved.

---

## 7. Development Order — Sprints

Two-week sprints, part-time. Every sprint: tasks → acceptance criteria
(AC) → tests → Definition of Done (DoD = AC demonstrated + tests green in
CI + journal/backup pushed). Sprint close additionally requires the IVF
Go/No-Go (Verification_Framework §8).

**Sprint 1 — Ledger core.**
Tasks: repo + uv + CI skeleton; `errors.py`; `record.py` (canonical
bytes, hashing, ULID); `schemas.py` for note/amendment/instrument_registered;
`store.py`; firewall test; git remote + backup script; gen_state.py v0.
AC: append/get/verify work; tamper test names the broken record; fresh
clone reproduces journal byte-identically.
Tests: §4.1 list. Deps added: python-ulid, duckdb, pyarrow, pandas, pandera, pytest.

**Sprint 2 — Instruments & calibration.**
Tasks: base protocols + EventFrame validators; registry; harness;
detector #1 (seasonality DIY) + planted fixtures; detector #2
(pandas-ta RSI wrap).
AC: both detectors calibrated via records; uncalibrated call refused;
incremental-consistency property passes.
Tests: §4.3/§4.4 lists.

**Sprint 3 — Data plane (trading adapters).**
Tasks: BulkStore + manifests; mt5_csv adapter + pandera schemas +
anomaly flags; ingest_report; WindowLedger + designations; DuckDB scan.
AC: real (or provided sample) month ingested; flagged rows quarantined
not repaired; VIRGIN reserve declared; scan returns correct ranges.
Tests: §4.2/§4.6 lists + corrupt-file detection.

**Sprint 4 — Screener + costs + SMC.**
Tasks: vectorbt adapter over EventFrames; trial_count auto-bump; named
cost models; detector #3 smartmoneyconcepts (pinned) + hard calibration.
AC: 500-variant grid screened in minutes; random-signal grid yields
empty shortlist; SMC planted cases pass.
Deps: vectorbt, smartmoneyconcepts (pinned).

**Sprint 5 — Battery I: engine + splits + selftest.**
Tasks: audited event engine (fills, costs); walk-forward + embargo;
seed derivation; selftest generators (planted edge / noise / small-n).
AC: engine determinism (same seed → identical trades); selftest tri-state
correct on synthetic suites.
Deps: scipy, statsmodels, arch.

**Sprint 6 — Battery II: verdict end-to-end.**
Tasks: hypothesis YAML + registry; statistics + bootstrap + corrections;
verdict assembly; window burn; MLflow logging; first REAL pre-registered
hypothesis judged.
AC (== Roadmap Phase 4 gate): battery selftest passes same day as first
real verdict; refusal matrix demonstrated; verdict recomputes
byte-identically from disk.
Deps: mlflow, skfolio.

**Sprint 7 — Beliefs + Observatory + dashboard.**
Tasks: priors.yaml + update math; observatory probes + guard; DuckDB
views; Streamlit read-only dashboard; redundancy-study prereg record.
AC: belief math matches hand computation; ContaminationError proven;
dashboard renders board/beliefs/queue from views only.

**Sprint 8 — Catalog wave + redundancy study.**
Tasks: families 4, 6, 7b (with placebo-zone machinery), 9, 16; run the
registered redundancy study; record outcome.
AC (== Roadmap Phase 5 gate): cross-family hypothesis reaches verdict
with zero kernel changes; study outcome recorded either way.

Sprints 9+ map 1:1 to Roadmap phases 6–9 (tuning/regimes, ML-as-witness,
completion, hardening + Gen-2 gate evaluation) and are specified when
Sprint 8 closes — per Layered Teaching, and because their interfaces
already exist above.

---

## 8. Deliberately Deferred Decisions (recorded, not forgotten)

| Decision | Deferred until | Default meanwhile |
|---|---|---|
| Journal sharding / SQLite mirror | journal > ~100k lines or slow scans | single JSONL + DuckDB index |
| Cryptographic signatures on records | multi-party or Gen-2 | hash chain |
| Polars in feature paths | measured pandas bottleneck | pandas |
| Setup-DSL richness (OR/NOT, windows-between-events) | first hypothesis that needs it | AND-of-events + session/regime filters |
| Battery test menu beyond core set | evidence a test earns its keep | t/bootstrap-CI/PF + corrections |

---

*This blueprint reduces uncertainty; it does not eliminate judgment.
Where code and blueprint disagree, stop, record a note, decide once,
amend here. — End of v1.0*
