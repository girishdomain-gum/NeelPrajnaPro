# ARCH-007 · Sprint 7 — Observatory + Beliefs · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL.md v1.3 · Blueprint §4 (observatory + belief interfaces), §2
(question / belief / anomaly-scan payloads — reconcile divergences via
DEVQ, the DEVQ-014 pattern), §7 Sprint 7 · GO-S6 (T0 anchor; carried
items) · DEVQ-010 ADDENDUM (the weekend-FVG research question — your
first REAL observatory output) · DEVQ-014 (observatory_ancestry
returns THIS sprint) · DEVQ-015 (family model your scans must respect).

## T0 — chain the sprint
Append the GO-S6 `note` record (decision GO, both Owner phrases, the
first-verdict ids), parents = [GO-S5 note 01KYC5RRRZHM60CTGJRVH1HVK8].
Commit "S7 T0".

## Scope (Blueprint §7 Sprint 7)

### 1. Observatory (`qrf/kernel/observatory/`)
Systematic anomaly scanning over TRAINING/EXPLORATION windows ONLY
(VIRGIN read anywhere in a scan path = ContaminationError; guard-test
it). A scan run: (dataset manifest(s), window, declared scan family,
seeded) → `anomaly_scan` record (what was scanned, with what method,
seed, findings summary) → zero or more `question` records, each
parented to its scan, each carrying: the observation in plain words,
the data slice refs, and a candidate-hypothesis sketch. Questions are
NOT hypotheses — they carry no thresholds and burn nothing. EVERY scan
bumps the trial ledger for its family (scans are searches; searches
are burdens — DEVQ-015 applies to looking, not just screening).

### 2. First real questions (pre-declared here)
Run the observatory for real and register AT LEAST these:
(a) **Q: weekend-spanning FVGs** (DEVQ-010 addendum): do FVG patterns
    whose 3 bars span the weekend hole behave differently from
    intra-week ones? Scan: partition the 105+ FVG events by
    weekend-spanning flag; compare follow-through distributions
    descriptively (NO thresholds, NO verdict language).
(b) **Q: fold-4 deterioration**: H-001's fold means worsened
    monotonically-ish (−0.03, −0.87, −0.08, −1.25). Scan: net-outcome
    drift across 2024 for the FVG family. Descriptive only.
Both questions cite the H-001 verdict/trades manifest as evidence refs.

### 3. Beliefs (`qrf/kernel/belief/`)
The belief ledger: a `belief` record per (family, claim) updated ONLY
by verdict events — append-only states like
{claim, stance: SUPPORTED/REJECTED/UNTESTED, strength, verdict_refs}.
Seed it from the real ledger: H-001's FAIL must produce a REJECTED
belief for "naive FVG follow-through, xauusd_h1" citing the verdict.
Beliefs never cite screener metrics, selftest results, or questions as
evidence (type-audited, the arrow-8 pattern). A future PASS verdict
updates, never overwrites (append-only chain of belief states).

### 4. Ancestry wiring (DEVQ-014)
hypothesis schema v2.1: optional `observatory_ancestry` = list of
question record ids. Registry validates each id exists and is a
question record. judge scripts print ancestry when present.

## Out of scope
New detectors · graduation/promotion (S8) · any VIRGIN read · touching
H-001's records · ivf/** · empirical costs · UI/dashboard.

## Acceptance criteria
- Scan on VIRGIN refused (guard test); scans bump trials with family.
- The two pre-declared questions exist as real records, parented to
  real scans, citing real evidence refs; journal chain GREEN.
- Belief ledger seeded from the real verdict set: exactly one REJECTED
  belief for the FVG follow-through claim, citing 01KYC7Y2KWYGXH73V1R9P57MYA.
- Type-audit: belief module cannot cite non-verdict evidence; question
  module cannot write thresholds/verdict/burn.
- Determinism: same scan seed → identical findings summary.

## Definition of Done
T0 + scope + tests green in CI; ruff clean; gen_state run; session log
EVERY session; completion report appended below; merged + pushed; DEVQs
for anything ambiguous. Expected DEVQ areas: question/belief payload
schemas vs Blueprint §2 (reconcile, DEVQ-014 pattern); scan-method
declaration granularity; belief strength semantics.

## Sprint close (after you — not yours)
Architect: IVF S7 checks (scan discipline + no-VIRGIN audit; beliefs
recomputed independently from the verdict set; ancestry traces;
+ the long-owed params-reading) + Drill S7 (planted VIRGIN-referencing
question + planted belief ignoring a FAIL — both must be caught; DRILL
FIRST) + HC caption-layout fix + visual HC (the two questions' data
slices on the chart). Owner: HC + Go/No-Go → GO-S7 (+Retrospective) →
Blueprint consolidation pass → ARCH-008.
