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
