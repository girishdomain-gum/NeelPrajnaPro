# Blueprint Amendments A1 — consolidation of Sprints 1–7 · 2026-07-25
Status: NORMATIVE OVERLAY on Implementation_Blueprint_v1.0.md
Authority: Owner GO sign-offs S1–S7 · Compiled by: Architect (GO-S7 duty)
Rule: where this file and Blueprint v1.0 disagree, THIS FILE GOVERNS.
Each entry cites the ruling record that ratified it; the ruling text
(in docs/coordination/inbox/CLOSED/) remains the full normative source.

## A1.1 — Records & schemas
- `preregistration_hash` is DEAD; the hypothesis record's own
  content_hash is the pre-registration seal; verify_frozen re-derives
  and checks it. [DEVQ-014]
- hypothesis v2 REQUIRES `thesis`, `outcome_interpretations`
  {PASS,FAIL,INSUFFICIENT — written BEFORE running}, and `family`;
  v2.1 adds optional `observatory_ancestry` = question record ids,
  registry-validated. [DEVQ-014/015/016]
- §2's `observatory_finding` is replaced by `anomaly_scan`
  {family, window_ref, manifest_refs, method, seed, findings,
  n_searched}; `question` is the ARCH-007 superset (thresholds/verdict/
  burn keys structurally forbidden); `belief_update` (odds/LR) is
  DEFERRED to a future Bayesian ADR — the shipped model is the
  append-only STANCE ledger {family, claim, stance, strength,
  verdict_refs, prev_state}. [DEVQ-016]
- trial_count v2 adds `family`; v3 adds source enum "observatory".
  [DEVQ-015/016]
- ingest_report v2 carries `params` {timeframe_seconds, gap_k,
  holidays, dataset}. [DEVQ-006]

## A1.2 — Windows & data
- §4.5's "VIRGIN at preregistration" is SUPERSEDED: VIRGIN is the
  Owner-declared untouchable trailing reserve (typed phrase DECLARE
  VIRGIN); the battery judges TRAINING/EXPLORATION and raises
  ContaminationError on VIRGIN; burns are once per (window, lineage).
  [GO-S3, DEVQ-014, ARCH-006 §3]
- Gap handling: flag-never-repair; `__flagged` suffix convention;
  quarantine datasets carry manifests. [DEVQ-006/007]
- Bulk parquet never travels via git; every dataset must be
  deterministically rebuildable (--rebuild-bulk) and hash-verified
  against EXISTING manifests. [GO-S4 F-1/F-5; extension to
  verdict-trades/scan datasets carried]

## A1.3 — Detectors & instruments
- FVG (NORMATIVE, completing §4.3's sketch): 3-bar gap AND displacement
  middle candle; ts = bar 3 (knowability); row-adjacency spans holes —
  weekend-spanning patterns are a RECORDED research question, not an
  error. smartmoneyconcepts==0.0.27 pinned behind the knowability
  wrapper. [DEVQ-010 + ADDENDUM]
- Order Block: registration of ANY smc.order_block.* hypothesis is
  REFUSED until the break-bar knowability restatement ships.
  [DEVQ-010; still unpaid at A1]
- External-code roles: TRUSTED BASELINE / UNPROVEN / VISUAL ONLY /
  SYNTHETIC FIXTURE; nothing UNPROVEN touches the belief layer except
  through a calibrated detector. [PROGRAM_RETRO T-3, Owner catalog]

## A1.4 — Screener & costs
- The screener is a telescope: type-barred from verdict/burn records;
  its metric (net Sharpe per DEVQ-009) is NEVER evidence; it counts
  EVERY variant into trial_count and carries `family`. [DEVQ-009/015]
- Cost models are frozen named configs in venues.yaml; editing a cited
  entry is CI-red; changes require a NEW name. [DEVQ-008]

## A1.5 — Engine, splits, selftest (§4.7 foundations)
- Fills: next-open entry; time-stop exit; pessimistic stop-before-
  target tie; pessimistic gap-through BOTH ways ("gaps can only hurt,
  never help"); n_dropped_tail inside the canonical byte image.
  [DEVQ-012]
- Splits: anchored expanding walk-forward; contiguous boundary-gap
  embargo; battery VALIDATES embargo_bars >= max hold_bars + 1.
  [DEVQ-011]
- Selftest: MIN_N=30, α=0.05 one-sided, decisive planted edge; a
  wiring gate, never evidence. [DEVQ-013]
- Determinism: same inputs + seed → byte-identical trades, across
  process restarts. [ARCH-005 AC]

## A1.6 — Verdicts, corrections, beliefs
- Verdict pipeline order is ARCH-006 §3 (type gate → selftest → window
  checks → splits → engine on TEST ranges → pooled stats → tri-state at
  DEFLATED alpha → verdict + burn in ONE code path). [ARCH-006]
- **Multiplicity follows CLAIMS, not data**: burden accrues to
  (market, instrument-family), prefix-matched over trial_count lineage/
  family; append-only preserved; Bonferroni base/max(1,N). [DEVQ-015]
- Belief strength = DECISIVENESS 2·|p−0.5| (NOT a posterior);
  CONTESTED stance when decisive verdicts disagree, replication-gated;
  beliefs cite verdicts ONLY. [DEVQ-016/017]
- Observatory scans bump the trial ledger — looking is a burden.
  [ARCH-007 §1, DEVQ-015]

## A1.7 — Verification & process (per Verification_Framework + guide)
- Go/No-Go = AC + VC + HC + Drill; drills run BEFORE checks touch real
  outputs; a drill's CLEAN CONTROL is mandatory (it caught Architect
  bugs #12/#13). [GO-S4..S7]
- ADR-009 visual layer: captured, self-proving evidence; pictures
  illustrate, numbers decide; stratified HC sampling (best/worst/
  boundary/random). [ADR-009, PROGRAM_RETRO HC-1]
- Before any trusted PASS: placebo battery run (G-3) and second
  independent data lens (G-1). [PROGRAM_RETRO]
- Ruling hygiene: numeric examples machine-verified; re-implement from
  NORMATIVE definitions, never prose; read back written artifacts
  against sources. [GO-S7]
- Supervised autopilot phases + seven binding risk constraints.
  [ADR-010]

Blueprint v1.0 text remains authoritative for everything not amended
here. Next consolidation (A2) at a future GO when the queue warrants.
