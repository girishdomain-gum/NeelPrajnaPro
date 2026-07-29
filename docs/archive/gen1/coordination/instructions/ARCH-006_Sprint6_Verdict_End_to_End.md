# ARCH-006 · Sprint 6 — Verdict End-to-End: Registry + Corrections + Battery II · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL.md v1.3 · Blueprint §2 (hypothesis / verdict / window_burn
payloads), §4.7 (battery pipeline, ALL steps), §4.8 (corrections), §5
arrows (9)(10) · GO-S5 (T0 anchor; BINDING carried rules) · DEVQ-011
(embargo >= max hold_bars + 1 — battery-side validation, THIS sprint) ·
DEVQ-012/013 (engine + selftest contracts you consume).

## T0 — chain the sprint
Append the GO-S5 `note` record (decision GO, both Owner phrases, key S5
facts), parents = [GO-S4 note 01KYBX4SWX0DJXSV59526CZHD6]. Commit "S6 T0".

## Scope (Blueprint §7 Sprint 6)

### 1. Hypothesis registry (`qrf/kernel/protocol/hypotheses.py` + configs/hypotheses/)
YAML → validated `hypothesis` record (§2 payload: instrument_refs,
setup_dsl, execution, cost_model_ref, split_spec, thresholds, scope,
lineage). Registration appends the record; the YAML is the human
surface, the RECORD is the truth (hash of canonical payload; a changed
YAML re-registers as a NEW hypothesis id — lineage links versions).
VALIDATIONS at registration: embargo_bars >= execution.hold_bars + 1
(DEVQ-011 BINDING); cost_model_ref exists in venues.yaml (DEVQ-008);
instruments exist AND are calibrated; **any smc.order_block.* in
instrument_refs → REFUSE registration** citing DEVQ-010 (break-bar
restatement gate) — test this refusal explicitly.

### 2. Corrections (`qrf/kernel/corrections/deflation.py`)
The multiple-testing penalty that makes trial counting BITE (§4.8):
`effective_alpha(base_alpha, scope, lineage, store)` = Bonferroni
against the trial ledger: base_alpha / max(1, N_trials) where N_trials
= TrialCountLedger.total for the hypothesis's scope+lineage AT JUDGING
TIME. Conservative and simple by design; refinements (BH, deflated
Sharpe) arrive only via future DEVQ/ADR. The verdict payload must
record base_alpha, N_trials, and effective_alpha used.

### 3. Battery verdict pipeline (`qrf/kernel/battery/battery.py`)
The full §4.7 run, in order, all enforced:
1. `require_audited_simulator` (type gate — screener rejected).
2. SELFTEST GATE: run_selftest must pass TODAY, else
   JudgeNotCalibratedError; the verdict records the selftest seed.
3. Window checks: window exists, designation is TRAINING/EXPLORATION
   (VIRGIN → ContaminationError), **not already burned for this
   lineage** (else WindowBurnedError).
4. Splits per the hypothesis split_spec (embargo validation re-checked).
5. Engine per fold TEST ranges only; seeds.for_run derivation; collect
   per-fold trades; n_dropped_tail carried per fold.
6. Statistics: pooled per-trade net outcomes across fold TEST ranges;
   one-sided t (H0: mean <= 0) + seeded bootstrap CI; n_total,
   per-fold means recorded.
7. Tri-state against PRE-REGISTERED thresholds with the DEFLATED alpha:
   n_total < thresholds.min_n → INSUFFICIENT; else PASS iff mean > 0
   AND p_one < effective_alpha; else FAIL.
8. Append `verdict` record (§2) referencing hypothesis, window,
   selftest seed, engine seed, all stats, thresholds AS REGISTERED
   (byte-equal), correction fields — then append `window_burn`
   (window, lineage) in the same flow. One code path: a verdict
   without its burn must be impossible by construction.

### 4. Owner-facing run (`scripts/judge_h001.py`)
Registers (idempotently) and judges H-001 below on the FULL-dataset
TRAINING window. Prints every record id + the tri-state outcome, plainly.
Refuses re-run after the burn (idempotency via the ledger). PROTOCOL
v1.3 output discipline: any command it prints must be complete/bash-ready.

## H-001 — PRE-REGISTERED HERE (thresholds fixed BEFORE any run)
The engine has NEVER run on xauusd_h1_full; this registration is
therefore clean. Recorded now, in the instruction, so no result can
move the goalposts:
- name/lineage: `h001_fvg_follow_through` · scope: `xauusd_h1`
- instruments: smc.fvg@0.1.0 (bull AND bear, symmetric follow-through:
  trade event direction)
- execution: hold_bars=4, size=1.0, no stop/target (DEVQ-012 defaults)
- cost_model_ref: xauusd_retail_median
- window: TRAINING 01KYB4SSC96SSS8RA7D1NMTPEX (xauusd_h1_full, 4157 bars)
- split_spec: n_folds=4, embargo_bars=8 (>= 4+1 ✔; extra margin chosen)
- thresholds: min_n=100 · base_alpha=0.05 one-sided · correction:
  Bonferroni vs trial ledger scope=xauusd_h1 (currently 500 trials →
  effective_alpha ≈ 1e-4; whatever the ledger says at judging time is
  what applies)
- PRE-REGISTERED EXPECTATION (Architect, for the record): FAIL or
  INSUFFICIENT is the LIKELY and healthy outcome — naive FVG
  follow-through with real costs showed 4/5 sampled losers on the
  (contaminated, different) sample set. The first verdict's value is
  the machinery proving it can say NO. A PASS here would itself demand
  suspicion and IVF scrutiny before celebration.

## Out of scope
Observatory, beliefs, mechanisms (S7) · graduation/promotion ·
touching VIRGIN in ANY code path (guard test again) · new detectors ·
any ivf/** edit · empirical cost models.

## Acceptance criteria
- Registration validations all enforced by tests (incl. the OB refusal
  and the embargo>=hold+1 refusal).
- Corrections: effective_alpha exactly base/max(1,N) with N read from
  the real ledger; unit-tested against hand numbers.
- Full pipeline on SYNTHETIC planted-edge data (selftest-style, big n,
  huge drift) → PASS verdict + burn, end-to-end in a scratch datastore.
- Same synthetic judged twice → WindowBurnedError on the second run.
- judge_h001.py on the real TRAINING window: completes, appends
  hypothesis + verdict + window_burn to the REAL journal, prints ids;
  outcome is WHATEVER THE DATA SAYS (any tri-state value is acceptance-
  valid; the machinery, not the outcome, is under test).
- Journal chain GREEN; firewall GREEN; no VIRGIN touch.

## Definition of Done
T0 + scope + tests green in CI; ruff clean; gen_state run; session log
EVERY session; completion report appended below (INCLUDING the real
H-001 verdict tri-state and all record ids); merged + pushed; DEVQs for
anything ambiguous. Expected DEVQ areas: pooled-vs-per-fold decision
statistics; verdict payload field completeness; burn scope semantics
(window,lineage) exactness.

## Sprint close (after you — not yours)
Architect: IVF S6 checks (corrections recomputation vs the ledger;
verdict-vs-registration byte equality; burn presence + double-burn
refusal; fold stats recomputed from trades) + Drill S6 (planted
threshold-swap verdict + planted double burn — both must be caught;
DRILL FIRST) + HC (the verdict's fold trades on the chart). Owner:
HC + Go/No-Go → GO-S6 (+Retrospective) → ARCH-007 (observatory +
beliefs).

---
## COMPLETION REPORT (developer) · claude-code · 2026-07-25

**Status: COMPLETE.** All ARCH-006 scope delivered; 683 tests pass (655→+28),
ruff clean, firewall GREEN, journal chain GREEN at 31 records.

### T0
GO-S5 note appended = **01KYC5RRRZHM60CTGJRVH1HVK8** (parent GO-S4 note
01KYBX4SWX0DJXSV59526CZHD6). Commit "S6 T0".

### Scope delivered
1. **Hypothesis registry** `qrf/kernel/protocol/hypotheses.py` +
   `configs/hypotheses/h001_fvg_follow_through.yaml`. YAML→resolved+validated
   `hypothesis` record; the record's own content_hash is the seal (changed YAML
   = new id); `verify_frozen` catches drift. All ARCH-006 §1 validations
   enforced + tested: embargo>=hold+1 refusal (DEVQ-011), cost_model_ref
   allowlist (DEVQ-008; injected so the kernel never reads the venue config),
   instruments exist + calibrated, **order-block refusal (DEVQ-010)**.
   Idempotent registration.
2. **Corrections** `qrf/kernel/corrections/deflation.py`. `effective_alpha =
   base_alpha / max(1, N_trials)`, N_trials = TrialCountLedger.total(scope,
   lineage) at judging time; unit-tested against hand numbers. Verdict records
   base_alpha, N_trials (=family_m), effective_alpha.
3. **Battery** `qrf/kernel/battery/battery.py` — the §4.7 pipeline in order:
   type gate → **selftest gate** (fixed validated seed 20260725, robust to any
   cost model; JudgeNotCalibratedError on failure) → window checks
   (TRAINING/EXPLORATION only; VIRGIN→ContaminationError; check_available→
   WindowBurnedError on re-run) → walk-forward splits (embargo re-checked) →
   engine per fold TEST range only (n_dropped_tail carried) → pooled one-sided t
   + seeded bootstrap CI → tri-state at the DEFLATED alpha → append verdict THEN
   window_burn in one code path (a verdict without its burn is impossible).
   Sole writer of verdict + window_burn. Simulator + cost model injected
   (kernel firewall-clean). `hypothesis`/`verdict` schemas added to schemas.py.
4. **Owner run** `scripts/judge_h001.py` (+ `--rebuild-bulk` for the gitignored
   full parquet, hash-verified). Registers H-001 idempotently, judges, prints
   all ids; refuses re-run after the burn.

Supporting: `EventEngine.engine_version="engine.s5.1"` + `ExecutionSpec.from_dict`
(so the kernel passes a plain execution dict — no trading type in the kernel).

### H-001 REAL VERDICT (the deliverable outcome)
- hypothesis   = **01KYC7Y1S2534DVYHWHNCZGTGZ**
- verdict      = **01KYC7Y2KWYGXH73V1R9P57MYA** → **FAIL**
- window_burn  = **01KYC7Y2PQ4KN58AVGAYBJ2P2A** (lineage h001_fvg_follow_through)
- trades_manifest = **01KYC7Y2JQY15BVJP146FX1QGF**
- window (TRAINING) = 01KYB4SSC96SSS8RA7D1NMTPEX (4157 bars, 825 in-window FVG)
- n_trades=654, n_dropped_tail=2; gross_total=-56.20, net_total=-363.58,
  net mean/trade=-0.556; one-sided t=-1.587, p=0.944; all 4 folds negative.
- correction: bonferroni, N_trials=0 → effective_alpha=0.05 (see DEVQ-015).

**FAIL is the pre-registered, healthy outcome** — the machinery proving it can
say NO. Real costs turn a naive FVG follow-through into a clear loser (even
gross is negative on this window). Re-run refused (burn-safe; ledger unchanged).

### DEVQs raised (both QUESTION, non-blocking — implemented per my recommendation)
- **DEVQ-014** — `hypothesis`/`verdict` payload field sets and the
  TRAINING-window judging model diverge from Blueprint §2/§4.5 (which say
  VIRGIN-at-preregistration + a different field list). Reconciled in ARCH-006's
  favor (its the specific, most-recent instruction, built around the corrections
  machinery §2 predates); verdict is a superset honoring both. Requests REV-S6
  ratification / Blueprint amendment. Module at protocol/ per the instruction
  (Blueprint §3 said registry/).
- **DEVQ-015** — the trial ledger has no count at (xauusd_h1,
  h001_fvg_follow_through), so N_trials=0 and effective_alpha=0.05 — NOT the
  "500→1e-4" the H-001 note assumes (the only trial_count is scoped to the
  *sample* window + lineage smc.fvg.screen.s4). Implemented the literal
  scope+lineage contract; asks whether the screener's FVG burden should be
  re-keyed to bite (a scope-granularity decision). Outcome acceptance-valid
  either way; the goalposts (pre-registered thresholds) did not move.

### Design note (for IVF S6)
Selftest gate uses a FIXED seed (20260725), not a per-run derivation: it is a
WIRING gate (DEVQ-013), so it must fail only when the engine/stats are actually
broken, never by seed luck (the driftless noise suite has an inherent ~5%
t-test false-positive). Validated to classify all three suites correctly with
the audited engine at both zero and real cost. Recorded on every verdict.
