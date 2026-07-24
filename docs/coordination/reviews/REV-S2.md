# REV-S2 · Architect Review of Sprint 2 (Instruments & Calibration) · 2026-07-24
Reviewer: architect (fable) · Basis: full read of base.py, registry.py,
calibration.py, detector_rsi.py; journal (7 records) verified by eye;
completion report + closed DEVQ threads; git history on merged main.
Verdict: **APPROVED — high quality**, 2 observations, 1 forward contract.

## What is right
1. **base.py is genuinely domain-blind** and the docstring *says why*
   ("the kernel only knows the shape") — the firewall as understanding,
   not just compliance. `build_event_frame` validating before return
   means a detector cannot emit a malformed frame even by accident.
2. **The version-bump gate is elegant**: instrument_ref = registration
   record id, calibrations name the ref, so a new version is
   automatically uncalibrated. No status field to forget — the ledger's
   structure IS the gate. Exactly the record-first philosophy.
3. **Calibration honesty**: the harness records failures as ledger facts
   and the block lives in `is_calibrated` (no soft-pass). Case payloads
   store expected AND got — the journal now carries reproducible
   evidence, not just verdicts. Both calibrations verified in the
   journal: truth 1.0, silence 1.0, full descriptor lists.
4. **RSI knowability is right**: ts = the completing bar's close time;
   warm-up exclusion per DEVQ-003; insufficient input → silence, not
   crash. Crossings-only semantics correctly implemented (strict
   inequality on the crossing side).
5. **DEVQ-002/003/004 execution faithful**; NOTE-006 rename clean;
   gen_state v1 DERIVED/HAND row model with its own tests — locking a
   process fix with tests is exactly the right instinct.

## Observations (recorded; no rework)
- OBS-4 **Input-ts contract is now load-bearing**: RSIDetector trusts
  that the input `ts` column holds bar CLOSE times. True for Sprint-2
  fixtures; MT5 bar times are OPEN times. The Sprint-3 adapter MUST
  normalize (close_ts = open_ts + timeframe) and say so in its schema.
  Written into ARCH-003's contract section; IVF S2 export already
  emits both time_open and time_close for this reason.
- OBS-5 **Near-threshold crossing sensitivity**: pandas-ta RSI vs MT5
  RSI can differ in late decimals; a crossing where |RSI − threshold|
  is tiny may legitimately diverge between implementations. The IVF S2
  check treats such divergences as AMBER-with-explanation rather than
  RED (band: 0.5 RSI points). This is a MODELED-style tolerance inside
  an otherwise EXACT comparison — declared here per IVF §4.

## Forward contract
Seasonality sessions are UTC-second windows (DEVQ-002). When broker
data arrives (Sprint 3), server-timezone normalization happens in the
ADAPTER, never in the detector — detectors stay UTC-pure.

## Sprint close status
Developer work: DONE (87 tests, firewall GREEN, journal chain GREEN).
Remaining for close: IVF S2 VC (kit delivered with this review:
IVF_S2_Export.mq5 + check_s2_detectors.py), Drill S2 (drill_s2.py),
Owner HC (checklist_s2.md), Owner Go/No-Go. SwingMarker comparison is
DEFERRED to Sprint 4 (no swing-emitting detector exists yet — deferral
recorded here per unique-responsibility; the IVF §7 S2 row anticipated
a detector set that Sprint 2 did not include).
