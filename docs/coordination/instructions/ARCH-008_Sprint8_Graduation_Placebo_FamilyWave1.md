# ARCH-008 · Sprint 8 — Graduation Gates + Placebo + Family Wave 1 · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL v1.3 · **Blueprint_Amendments_A1 (NORMATIVE overlay — read in
full)** · Blueprint §7 Sprint 8 · GO-S7 (T0 anchor; carried items) ·
PROGRAM_RETRO_001 (G-1 second lens, G-3 placebo — this sprint BUILDS
those gates) · DEVQ-015/016/017 (family multiplicity; belief
contracts your promotions consume).

## T0 — chain the sprint
Append the GO-S7 `note` record (decision GO, both Owner phrases, the
question/belief ids), parents = [the S7 T0 GO-S6 note]. Commit "S8 T0".

## Scope

### 1. Placebo battery run (G-3 → code)
`qrf/kernel/battery/placebo.py`: given a judged hypothesis's exact
setup, run the SAME pipeline on a null-preserving synthetic twin of the
window (seeded circular block-shuffle of returns, or label-permutation
of event directions — choose via DEVQ, document the null it preserves).
Output: a `placebo_run` record {hypothesis_ref, method, seed, n_runs,
outcomes[], n_pass} — with N_RUNS >= 20 seeded repetitions. A healthy
judge finds ~alpha·n_runs passes AT MOST. Placebo NEVER burns windows
and NEVER writes verdicts (type-audited). Wire into the judge scripts:
every future real verdict is accompanied by its placebo record.

### 2. Graduation / promotion machinery
`qrf/kernel/graduation/`: a `promotion` record for a claim may ONLY be
appended when ALL hold: (a) a PASS verdict; (b) its placebo_run shows
no excess null passes; (c) a SECOND-LENS evidence record exists (G-1 —
schema this sprint: `second_lens` {source_name, overlap_manifest,
agreement_summary}; the actual second feed arrives when the Owner
provides one — the GATE exists now, so promotion is IMPOSSIBLE until it
does); (d) belief stance not CONTESTED. Refusals tested for each
missing leg. Promotions update the belief chain (stance PROMOTED is NOT
added — promotion is a lifecycle record, beliefs stay verdict-only).

### 3. Family Wave 1 — two pre-registered hypotheses (thresholds fixed HERE)
Both registered v2.1 (thesis + outcome_interpretations + family +
ancestry where real), judged on the TRAINING window (burned only for
h001's lineage — these are new lineages), each WITH its placebo run:

**H-002 `h002_fvg_intraweek_follow_through`** · family xauusd_h1/smc.fvg
· ancestry [01KYCFNE46BB7H2V300D1WZG1P] · thesis: "Intra-week-only FVG
follow-through (weekend-born excluded) is profitable net of costs."
Setup = H-001 minus weekend-born events (the scan's spans_weekend rule,
inlined as the setup filter). execution/cost/splits = H-001's exactly.
thresholds: min_n=100, base_alpha=0.05, Bonferroni family — **the 502
burden applies: effective alpha ≈ 1e-4.** outcome_interpretations:
PASS → "the weekend subset was masking a real intra-week edge —
escalate to second-lens"; FAIL → "FVG follow-through has no edge even
intra-week; the family is deprioritized"; INSUFFICIENT → "filter cost
too many trades; no conclusion".

**H-003 `h003_dow_monday_drift`** · family xauusd_h1/seasonality.calendar
(FRESH family — expected N_trials 0 or near; this is the DEVQ-017
zero-deflation boundary IN THE WILD: if it PASSes marginally, the
Bayesian ADR triggers before any promotion, per the ruling). ancestry
[] · thesis: "Monday (UTC) long-at-open, hold to Monday close, is
profitable net of costs on XAUUSD." setup_dsl: enter next-open after
the first Monday bar's signal; hold_bars = declare via DEVQ from the
session structure (recommend 22 to approximate Mon close; embargo
>= hold+1 accordingly). cost xauusd_retail_median. splits n_folds=4.
thresholds: min_n=40 (≈52 Mondays), base_alpha=0.05, Bonferroni family.
outcome_interpretations: PASS → "calendar seasonality exists at retail
costs — replication + second lens next"; FAIL → "no Monday drift net of
costs"; INSUFFICIENT → "not enough Mondays in one year — needs more
data, not looser thresholds".

### 4. Cross-implementation detector check (T-1, small)
Add dev-dependency `smc-toolkit`; a TEST (not a detector) that runs its
FVG detection over the sample dataset and reconciles against our
calibrated smc.fvg events, with a WRITTEN mapping of definitional
differences (their FVG def vs our gap+displacement contract). Goal:
know exactly where a second implementation agrees/disagrees — the
library-level IVF. No registry entry; UNPROVEN role per A1.3.

## Out of scope
OB restatement (gate stays; separate DEVQ if you want to propose the
break-bar rule) · TA-Lib baseline (S9) · real second feed ingestion
(Owner-provided, future) · Bayesian beliefs · any ivf/** edit · VIRGIN.

## Acceptance criteria
- Placebo: on H-001's setup, >=20 seeded null runs, ~0 passes (report
  exact); type-audit proves no verdict/burn writes.
- Graduation: all four refusal legs tested; no promotion record can
  exist in the journal without its three evidence legs (structural
  test).
- H-002/H-003 judged on the real journal with placebo records;
  outcomes are WHATEVER THE DATA SAYS (all tri-states acceptance-valid).
- Cross-impl test green with the difference-map documented in-code.
- Journal chain GREEN; VIRGIN untouched; firewall GREEN; every judge
  script prints family/N_trials/effective_alpha (DEVQ-015).

## Definition of Done
T0 + scope + tests in CI; ruff clean; gen_state; session log EVERY
session; completion report appended below WITH both verdicts' tri-states
and all record ids; merged + pushed; DEVQs for anything ambiguous.
Expected DEVQ areas: placebo null-construction choice; H-003 hold_bars/
session convention; second_lens schema fields; smc-toolkit version pin.

## Sprint close (after you — not yours)
Architect: IVF S8 (independent placebo recomputation — rerun the null
myself from the recorded seeds; promotion-gate audit; H-002 weekend-
filter recomputation against the scan rule) + Drill S8 (planted
placebo-pass-hidden + planted promotion-missing-a-leg; DRILL FIRST;
clean control) + HC caption fix (owed) + visual HC (the wave's trades).
Owner: HC + Go/No-Go → GO-S8 (+retro) → ARCH-009.
