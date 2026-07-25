# ARCH-005 · Sprint 5 — Battery I: Engine + Splits + Selftest · 2026-07-25
Author: architect (fable) · Level: instruction · Executor: Developer

## Read first
PROTOCOL.md v1.3 · Blueprint §4.7 (EvidenceBattery pipeline — this
sprint builds its FOUNDATIONS, not the verdict), §7 Sprint 5, §2
(verdict/window_burn schemas — READ ONLY, you write neither this
sprint), §5 arrows (9) context · GO-S4 (T0 anchor; carried items) ·
DEVQ-008/009 (cost + metric contracts your engine must respect).

## T0 — chain the sprint
Append the GO-S4 `note` record (decision GO, both Owner phrases, key S4
record ids), parents = [GO-S3 note 01KYB5ARJPK3YK0AKCE9FP7DAH]. Commit
"S5 T0".

## Scope (Blueprint §7 Sprint 5) — deps enter: scipy, statsmodels, arch

### 1. Audited event engine (`qrf/trading/simulator/engine.py` + fills.py)
The JUDGING simulator (vs the screener's telescope): event-driven,
bar-by-bar over EventFrames + bars, applying a named CostModel per
trade. HARD RULES: (a) NO LOOK-AHEAD BY CONSTRUCTION — a fill may use
only information from bars with ts <= decision ts; entries fill at the
NEXT bar's open (or a documented, pre-declared fill rule), never at the
signal bar's close-in-hindsight; property-test this by feeding data
incrementally (S4 anti-hindsight pattern, applied to fills). (b) Both
gross and net computed; cost model applied per DEVQ-008 named-reference.
(c) The engine is a distinct TYPE from the screener (Blueprint: battery
rejects screener class by type — build the type distinction now).

### 2. Determinism + seeds (`kernel/protocol/seeds.py`)
seeds.for_run(hypothesis_ref, window_ref) → deterministic derivation
(document the recipe); engine consumes an explicit seed; SAME INPUTS +
SAME SEED → BYTE-IDENTICAL trade list (serialize trades canonically and
compare bytes in the test, not floats loosely).

### 3. Walk-forward + embargo (`kernel/protocol/splits.py`)
Anchored walk-forward per Blueprint: split_spec {n_folds, embargo_bars}
→ ordered (train, test) index ranges over a window; embargo bars
excluded AFTER each test range boundary; folds never overlap test
ranges; all ranges stay strictly inside the window. Tests: boundary
matrix (first/last fold, embargo at edges), no-overlap property,
determinism.

### 4. Selftest generators (`kernel/battery/selftest.py`)
Three synthetic suites, seeded: PLANTED EDGE (known injected effect the
engine+stats must call PASS), PURE NOISE (must call FAIL/no-edge),
SMALL-N (must call INSUFFICIENT). This sprint the selftest exercises
ENGINE + basic statistics only (t-stat / bootstrap CI groundwork ok);
the full verdict tri-state wiring is Sprint 6. Output: a plain report
object + tests asserting the tri-state on all three suites; NO verdict
records written (type-level test like the screener's).

## Out of scope
verdict / window_burn / belief records (Sprint 6) · hypothesis YAML +
registry (S6) · corrections application (S6; trials ledger exists) ·
observatory · any ivf/** edit · VIRGIN data in any code path (guard
test required again).

## Acceptance criteria (Blueprint §7 S5)
- Engine determinism: same seed → byte-identical trades (test proves it
  twice in one CI run and across a process restart).
- No-look-ahead property test green (incremental feed, fills never
  change retroactively).
- Hand-computed micro-scenario: 3 events, known bars, known cost model
  → engine's gross and net match to the cent.
- Splits: boundary matrix green; embargo verified by construction.
- Selftest tri-state correct on all three synthetic suites, seeded and
  reproducible.
- Firewall GREEN (scipy/statsmodels/arch allowed in kernel per
  Blueprint import rules; vectorbt still trading-only).

## Definition of Done
T0 + scope + tests green in CI; ruff clean; gen_state run; session log
EVERY session; completion report appended below; merged + pushed; DEVQs
for anything ambiguous. Expected DEVQ areas: exact fill rule (next-open
vs configurable), embargo placement convention (after-test vs
symmetric), selftest effect-size calibration (how strong is the planted
edge).

## Sprint close (after you — not yours)
Architect: IVF S5 checks (determinism cross-run byte compare; fill/cost
spot recompute; split+embargo independent recomputation; selftest
tri-state audit) + Drill S5 (planted look-ahead fill + embargo
violation — both must be caught; Architect runs own drill BEFORE real
check, standing S4 rule) + HC (visual: sampled trades drawn on the MT5
chart — entry/exit arrows + cost annotation, ADR-009 tool generation
3). Owner: HC + Go/No-Go → GO-S5 (+Retrospective) → ARCH-006.
