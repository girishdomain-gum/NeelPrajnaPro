# ARCH-002 · Sprint 2 — Instruments & Calibration · 2026-07-24
Author: architect (fable) · Level: INSTRUCTION · Status: OPEN

## Read first (in this order)
1. `docs/coordination/reviews/GO-S1.md` — Sprint 1 is closed; your
   T0 below puts that close into the ledger.
2. `docs/coordination/reviews/REV-S1.md` — OBS-1 and OBS-3 are in YOUR
   test budget this sprint (OBS-2 is parked; not yours).
3. Blueprint §4.3 (Detector contract + EventFrame — normative),
   §4.4 (Registry + Calibration), §2 rows `instrument_registered`,
   `calibration`, §7 Sprint 2.
4. Architecture (docx) Ch.3.2 if you want the why; not required to build.

## T0 — Ledger note for GO-S1 (5 minutes, do first)
Append one `note` record via RecordStore, producer `human:girish`
(transcribing the Owner), parents = [both genesis record ids]:
"Sprint 1 signed off by Owner: 'Signed off — Sprint 1 closed'.
GO-S1: AC met, VC GREEN (s1_verify.json), HC done, Drill S1 caught
(s1_drill.json)." Commit: `ARCH-002: T0 GO-S1 ledger note`.

## Scope (build exactly this)
Sprint 2 per Blueprint §7: the instrument layer + first two detectors.

### Kernel (domain-blind)
- `qrf/kernel/instruments/base.py` — `Detector` protocol,
  `CalibrationCase` dataclass, and an `EventFrame` validator enforcing
  the §4.3 column spec (names, dtypes, zone_hi ≥ zone_lo, ts int64 ns).
  NOTE: base.py is kernel — the EventFrame validator speaks in the
  §4.3 column names only (ts, event_type, direction, level, zone_hi,
  zone_lo, strength, meta); no trading vocabulary beyond those.
- `qrf/kernel/instruments/registry.py` — `InstrumentRegistry` per §4.4
  (register → instrument_registered record; get; is_calibrated).
- `qrf/kernel/instruments/calibration.py` — `CalibrationHarness.run`
  per §4.4 → `calibration` record; failed calibration BLOCKS (raises
  `UncalibratedInstrumentError` on any later use; no soft-pass).
- `qrf/kernel/records/schemas.py` — add v1 payload schema for
  `calibration` (fields per Blueprint §2 row). `instrument_registered`
  already exists.
- REV-S1 follow-ups in `records/`:
  - OBS-1: `RecordStore.resolve()` result must be loudly marked —
    set `meta={"resolved": true, "amendments": [ids...]}` on the
    returned view AND make `append()` refuse any record whose meta
    contains `resolved` (so a resolved view can never be persisted).
  - OBS-3: add a test where an amendment is itself amended; document
    (in the test) the resulting shallow-override order.

### Trading plug-in (first detectors)
- `qrf/trading/concepts/seasonality/detector.py` — DIY detector #1:
  session/day-of-week events over bar data. Params: session definitions
  (named UTC windows), emit `event_type="seasonality.session.open"` /
  `.close` and `"seasonality.dow.<mon..fri>"` markers, direction=0,
  level=NaN(+meta flag), strength=1.0. Keep it deliberately simple —
  its job this sprint is to prove the contract, not to be clever.
- `qrf/trading/concepts/classical/detector_rsi.py` — detector #2:
  pandas-ta RSI wrap. Params: period (default 14), overbought/oversold
  thresholds. Events on threshold CROSSINGS only (not while beyond),
  `classical.rsi.overbought_cross` (direction=-1) /
  `oversold_cross` (+1), level = the RSI value in meta, price level =
  bar close. Knowability: event ts = the CLOSE time of the bar that
  completed the crossing — never the bar's open time.
- Planted fixtures under each detector's `fixtures/`: hand-CONSTRUCTED
  bar series (built in the fixture code with comments, not downloaded)
  containing textbook cases + structured-noise series (e.g. trending
  sine + drift) where the detector must stay silent.
- Deps added this sprint: `pandas-ta` (pin exact version in uv.lock).

## Out of scope
BulkStore, adapters/real data, screener, battery, SMC, everything
Sprint 3+. No edits to ivf/**, docs/** beyond the sanctioned paths.

## Acceptance criteria (Blueprint Sprint 2 + REV-S1)
- Both detectors registered + calibrated via ledger records; an
  uncalibrated (or calibration-failed) detector's use raises
  `UncalibratedInstrumentError`.
- Version bump of a detector forces recalibration (is_calibrated goes
  false until a new calibration record for the new version).
- EventFrame validator rejects each contract violation with
  `SchemaViolation` (bad dtype, zone_hi < zone_lo, non-ns ts,
  unknown column).
- Anti-hindsight property test per §4.3: feed each detector data
  incrementally; previously emitted events never change retroactively.
- OBS-1 behaviour: resolved views are marked; persisting one is refused.
- Hand-audit hook: a tiny CLI or test helper that prints N random
  events from a detector run with their source bars, for the Owner's
  Sprint-2 HC (10 events per detector, IVF §7 S2).

## Required tests (minimum)
instruments/: registry round-trip; calibration record fields;
block-on-fail; version-bump recalibration; EventFrame validator matrix.
concepts/: planted-truth found (exact expected events, exact ts);
structured-noise silence; incremental-consistency property; params
round-trip. records/: OBS-1 refusal + marker; OBS-3 amendment-chain.

## Definition of Done
T0 + all above; tests green in CI; ruff clean; gen_state run;
completion report appended below (test counts, record ids for the
calibration records, any DEVQs). Sprint close remains: IVF Sprint-2
VC (MT5 SessionStats/IndicatorDump/SwingMarker comparisons — the
Architect delivers those MQL5 tools; NOT yours), Owner HC (10 events
per detector on chart), Drill S2 (timestamp shift — Architect plants
it), Owner Go/No-Go.

## How to ask
DEVQs as ever. Known judgment areas where a DEVQ is expected rather
than a guess: session boundary handling across broker timezones
(if bar data lacks tz info), and RSI warm-up period exclusion rules.

## COMPLETION REPORT (developer)
Author: developer (claude-code) · 2026-07-24 · Status: code COMPLETE, one
DoD item (state refresh) held on DEVQ-004.

### T0 — done first
GO-S1 close appended as a `note` record, producer `human:girish`, parented
to both genesis records. Record id **01KYAJA3TMM03K1MYMCTRE9033**. Chain
re-verified GREEN. Commit `ARCH-002: T0 GO-S1 ledger note`.

### Built
Kernel (`qrf/kernel/instruments/`, domain-blind):
- `base.py` — `Detector` protocol, `CalibrationCase`, EventFrame contract
  (`EVENTFRAME_SCHEMA`, `build_event_frame`, `empty_event_frame`,
  `validate_event_frame`) enforcing §4.3 names/dtypes, int64-ns `ts`
  (a `timestamp`/`int32` column is rejected), and `zone_hi ≥ zone_lo`.
- `registry.py` — `InstrumentRegistry`: register → `instrument_registered`;
  `get`/`info_for_ref`; `is_calibrated` (passing + in-date, no soft-pass);
  `require_calibrated`/`run_detector` as the calibration gate. instrument_ref
  = the registration record id, so a version bump (new ref) is uncalibrated
  until re-calibrated.
- `calibration.py` — `CalibrationHarness.run` → `calibration` record; records
  pass AND fail (the block lives in `is_calibrated`).
- `records/schemas.py` — added the v1 `calibration` payload schema (§2).

REV-S1 follow-ups in `records/store.py`:
- OBS-1 — `resolve()` returns a view marked
  `meta={"resolved": true, "amendments":[…]}`; `append()` refuses any record
  whose meta carries `resolved`, so a resolved view can never be persisted.
- OBS-3 — amendment-of-an-amendment test documents the shallow, non-transitive,
  ULID-ordered (last-write-wins) resolution.

Trading plug-in (`qrf/trading/concepts/`):
- `seasonality/detector.py` (+ `fixtures/`) — session open/close + DOW markers
  over UTC-ns bars; pure integer arithmetic; anti-hindsight by construction.
- `classical/detector_rsi.py` (+ `fixtures/`) — pandas-ta RSI threshold
  crossings; `level` = bar close, RSI in `meta`; `ts` = completing bar close;
  `period`-bar warm-up exclusion; sub-`period+1` inputs are `insufficient`.
- `hand_audit.py` + `scripts/hand_audit_s2.py` — Owner's HC hook: 10 sampled
  events per detector with their source bars.
- Dep added, pinned: `pandas-ta==0.4.71b0` (see NOTE-006; the legacy 0.3.x is
  dead under numpy 2 / pandas 3; numpy pinned to 2.2.6 as a consequence).

Ledger bootstrap (`scripts/bootstrap_s2_instruments.py`, idempotent) — both
detectors registered + calibrated into the real journal:
- seasonality.calendar@0.1.0 — instrument_registered **01KYAKYY1298M1N3JWAA8HBQ5P**,
  calibration **01KYAKYY2BQHJPMSZA6WTMPQJG** (truth 1.0, silence 1.0).
- classical.rsi@0.1.0 — instrument_registered **01KYAKYY4RVVBFWKY6PWH43CFS**,
  calibration **01KYAKYY5TK1N5YV7BNYGJB4WZ** (truth 1.0, silence 1.0).
Journal now 7 records, chain GREEN.

### Tests
83 passed (35 prior + 48 new); ruff clean; kernel firewall GREEN. New:
instruments — EventFrame validator matrix (11), registry incl. gate +
version-bump + staleness (9), calibration record fields + block-on-fail (4);
records — OBS-1 (4), OBS-3 (3); concepts — seasonality (6), rsi (8),
hand-audit (3). Anti-hindsight is a property test on each detector (prefixes
never change prior events).

### Acceptance criteria
Met: both detectors registered+calibrated via records; uncalibrated/failed use
raises `UncalibratedInstrumentError`; version bump forces recalibration;
EventFrame validator rejects each contract violation with `SchemaViolation`;
anti-hindsight property passes; OBS-1 marked+refused; hand-audit hook prints 10
events/detector with source bars.

### Open DEVQs
- DEVQ-002 (QUESTION) — seasonality timezone contract; proceeding on UTC-ns
  input + UTC DOW (option A).
- DEVQ-003 (QUESTION) — RSI warm-up exclusion; proceeding on `period`-bar
  exclusion + insufficient handling (option A).
- DEVQ-004 (QUESTION) — **`gen_state.py` v0 rows are stale**: running it would
  regress the rev-3 Status table and falsely show Sprint 1 as "Go/No-Go
  pending" (it is CLOSED per GO-S1 / the T0 note). I did NOT overwrite the
  tracked state file (one-direction rule). This is the ONLY unmet DoD item
  ("gen_state run → refresh"); all code, tests, ruff, and T0 are complete.
NOTE-006 (FYI) — pandas-ta version choice + numpy/numba consequences (renamed
from NOTE-004 per NOTE-005's ID-collision rule).

### Not done (blocked on DEVQ-004)
`gen_state` refresh of `docs/handover/AI_PROJECT_STATE.md`. Awaiting the
architect's decision on how to reconcile the stale generator with the ledger.

## COMPLETION REPORT — FINAL (post Architect rulings, 2026-07-24)
All DoD items now closed; branch merged to main and pushed.

- **DEVQ-002 / DEVQ-003 RATIFIED**, **DEVQ-004 decided** — replies appended,
  all three moved to `inbox/CLOSED/`. OPEN inbox empty.
- **DEVQ-004 implemented**: `gen_state.py` v1 splits the Status table into
  DERIVED rows (test counts, ADR range, journal record count = journal.jsonl
  line count, git branch/commit — recomputed each run) and HAND rows (sprint
  statuses, preserved verbatim like the two hand-maintained sections).
  `tests/test_gen_state.py` (4) locks the model. Also fixed the write path to
  emit LF (`.gitattributes eol=lf`). Ran it: state file refreshed — Sprint 1
  CLOSED survives (the earlier regression is gone), Journal `7 records`, Test
  suite `87 passed (green)`.
- **ID collision resolved** (NOTE-005 rule): my pandas-ta note renamed
  NOTE-004 → **NOTE-006**; all references updated. Merged the Architect's
  NOTE-004 (status-reads) and NOTE-005 (push-in-DoD + ID rule) cleanly.
- **Push-in-DoD (NOTE-005) satisfied**: branch pushed; `main` fast-forwarded to
  the merged tip **428efa6** and pushed.
- Final gate: **87 tests pass** (35 S1 + 48 S2 + 4 gen_state), ruff clean,
  kernel firewall GREEN, journal 7 records chain GREEN.

Sprint-2 close still awaits (not developer scope): IVF Sprint-2 VC (Architect's
MT5 tools), Owner HC (10 events/detector — `scripts/hand_audit_s2.py`), Drill S2,
Owner Go/No-Go. Handing off for Architect review.
