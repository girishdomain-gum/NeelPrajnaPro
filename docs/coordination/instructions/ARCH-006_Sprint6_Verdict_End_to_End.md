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
