# ARCH-004 · Sprint 4 — Screener + Costs + SMC · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL.md v1.3 (session log EVERY session; Owner-command rule applies
to any command your scripts print for the Owner); Blueprint §4.8
(TrialCountLedger), §5 arrows (5)(8), §7 Sprint 4, §2 (trial_count
schema); GO-S3 (T0 anchor + carried items); DEVQ-006/007 CLOSED
(contracts you already implement); ADR-009 (visual evidence — your
detectors' planted fixtures should make chart-anchored claims capturable).

## T0 — chain the sprint
Append the GO-S3 `note` record to the journal: text summarizing GO-S3
(decision GO, both Owner phrases, TRAINING/VIRGIN window ids), parents =
[the GO-S2 note record id] (find it: query record_type=note, the S2
close entry). Commit "S4 T0". Everything in this sprint descends from it.

## Scope (Blueprint §7 Sprint 4)

### 1. Screener (`qrf/trading/simulator/screener_vbt.py`)
vectorbt adapter over EventFrames: take (dataset manifest(s), an
EventFrame manifest, a parameter grid, a cost_model name) → run vectorized
entry/exit sweeps → emit a SHORTLIST (plain artifact: parquet via
BulkStore + a `note` record referencing it) ranked by pre-declared
screening metric. HARD RULES (arrow 8): the screener writes NO
verdict-typed records and NO window_burn — it is a telescope, not a
judge; screening runs only on TRAINING/EXPLORATION windows
(WindowLedger.check via designation; VIRGIN → ContaminationError).

### 2. Trial counting (`qrf/kernel/corrections/trials.py`)
TrialCountLedger per §4.8: `bump(scope, lineage, n, source,
generator_ref)` appends a `trial_count` record (§2 schema). The screener
auto-bumps by EXACT grid size (every variant evaluated counts — no
netting, no dedup) in the same run that produces a shortlist; a
shortlist without its trial_count bump must be impossible by
construction (single code path).

### 3. Cost models (`qrf/trading/utility/cost_models.py`)
Named per-venue models from `configs/venues.yaml`: at minimum
`xauusd_retail_median` (spread + commission + slippage-per-side, all
explicit numbers in the yaml, sourced honestly — if estimated, say
"estimate" in a comment). API: `CostModel.apply(gross_trades) ->
net_trades`, deterministic, unit-tested against hand-computed examples.
Registered as instruments (kind=data is wrong — use kind=judge? NO:
raise a DEVQ if the catalog's kind enum feels wrong; do not extend enums
silently).

### 4. Detector #3 — SMC (`qrf/trading/concepts/smc/detector.py`)
Wrap `smartmoneyconcepts` (PINNED version; new dep enters uv.lock this
sprint per Blueprint rule) for a first event set: `smc.fvg.bull/bear`
and `smc.order_block.bull/bear` as EventFrame rows (zones: zone_hi/
zone_lo; ts = knowability with confirmation lag INSIDE the detector —
anti-hindsight property test required). HARD calibration: planted
fixtures where the true zones are constructed by hand (parquet under
concepts/smc/fixtures/), structured-noise silence cases, insufficient
case. Register + calibrate through the real journal.

## Out of scope
Battery, statistics, verdicts (Sprint 5–6); observatory; beliefs; any
ivf/** edit; live data connections; VIRGIN data in ANY code path of this
sprint.

## Key contracts (inlined where normative)
- Arrow (8): screener produces shortlist + trial_count ONLY. A type-level
  test must prove the screener module cannot append `verdict` or
  `window_burn` records (call-site audit like burn's).
- EventFrame §4.3 exactly; zone_hi ≥ zone_lo or SchemaViolation.
- trial_count payload §2: data_scope, lineage, n_attempts, source enum,
  generator_ref optional.
- Screening metric(s) must be DECLARED in the shortlist note payload
  before ranking (no post-hoc metric picking).

## Acceptance criteria (Blueprint §7 S4)
- A 500+-variant grid over `xauusd_h1_sample` TRAINING data screens in
  minutes on the Owner's machine; shortlist artifact + trial_count(n≥500)
  recorded in one run.
- A random-signal grid (same size, seeded synthetic no-edge events)
  yields an EMPTY shortlist under the declared metric thresholds.
- SMC planted cases pass (truth 1.0 / silence 1.0); uncalibrated SMC
  call refused; anti-hindsight property test green.
- Cost model applied: gross vs net visibly differ in shortlist metrics;
  hand-computed example matches to the cent.
- Journal chain GREEN; kernel firewall GREEN (vectorbt and
  smartmoneyconcepts must NOT be imported by kernel/**).

## Required tests (minimum)
screener: grid size == trial_count bump (exact); no-verdict type audit;
TRAINING-only guard (VIRGIN refused); determinism (seeded) ·
trials: monotonic accumulation; generator inheritance ·
cost models: hand-computed match; determinism ·
smc: planted truth/noise/insufficient; zone validity; incremental
consistency (anti-hindsight); version pin recorded in
instrument_registered payload.

## Definition of Done
T0 + all above; session log EVERY session; tests green in CI; ruff
clean; gen_state run; completion report appended below; merged to main
and pushed; DEVQs for anything ambiguous. Expected DEVQ areas: cost
model instrument `kind`; screening metric definition; SMC library
version choice and any disagreement between its zone definitions and
the architecture's.

## Sprint close (after you — not yours)
Architect: IVF S4 checks (screener no-verdict audit; trial_count vs
grid cross-count; SMC planted-case independent recomputation; cost
spot-recompute) + Drill S4 (planted verdict-writing screener AND a
trial under-count — both must be caught) + HC tool rev 5 (ADR-009 zone
overlays). Owner: visual HC on SMC zones + Go/No-Go → GO-S4 (with
Retrospective section) → ARCH-005.
