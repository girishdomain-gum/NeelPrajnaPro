# ADR-010 · Supervised Autopilot — phased automation with a drilled human gate
Status: Accepted · 2026-07-25 · Proposed by: Owner (Girish) · Drafted by: Architect
Refs: ADR-008/PROTOCOL v1.3 (roles), ADR-009 (visual evidence),
PROGRAM_RETRO_001 (G-1..G-4, discovery-throughput mandate),
EXECUTION_PROCESS_GUIDE v1.0, GO-S4/S5/S6 retros (drill-first culture)

## Context
Six sprints run at human tempo proved the method: three separated
parties, independent verification, drilled checks, captured evidence,
verbatim human sign-offs. The Owner now asks for the sprint cycle to
run with minimum human involvement. Feasibility is high (~85% of the
cycle is mechanizable today: CI verification, headless Developer
sessions, orchestrated relays, self-assembling HC packets). The danger
is not that automation fails loudly — it is that it succeeds quietly
while the properties that make QRF trustworthy dissolve. This ADR fixes
the design BEFORE the first automated run: the proposal, its threat
model, and the constraints as ONE record.

## Decision — the shape of the autopilot
Three phases, each reversible, each gated by the Owner:

- **Phase A — Tireless verification (immediate).** GitHub Actions runs
  on every push: full test suite, ruff, kernel firewall, gen_state
  consistency, ALL IVF checks, ALL drills. Red blocks merge. No agent
  autonomy added; pure enforcement.
- **Phase B — Autonomous Developer.** A watcher detects a new/updated
  ARCH-N on main and boots Claude Code headless to execute it under
  CLAUDE.md, worktree + push-per-commit + session logs unchanged.
  Architect writes still reach GitHub via a scheduled commit task
  (ARCH: prefix preserved).
- **Phase C — Orchestrated cycle + HC packet.** An orchestrator
  sequences ARCH→Developer→CI→IVF and assembles, per sprint, ONE
  Owner packet: five STRATIFIED HC screenshots (best, worst, boundary,
  two random — PROGRAM_RETRO HC-1), the verify/drill JSONs, and a
  one-page plain-language summary. The Owner's involvement per sprint
  becomes: review the packet, type the verbatim phrases.

**Reserved to the human, permanently (the 15% that is the point):**
(1) Go/No-Go and HC sign-off phrases; (2) VIRGIN-class declarations and
window burns on real data (typed-phrase gates); (3) approval of ANY
change to ivf/**, CI workflow definitions, or this ADR; (4) periodic
audit of the automation itself. The Architect remains an INTERACTIVE
session at sprint boundaries; a fully autonomous Architect is
explicitly out of scope and would require its own ADR, because it bends
the separation of powers this system rests on.

## Threat model — seven maximum risks, with mitigations as BINDING
## design constraints

### R-1 · Rubber-stamp decay (maximum risk; attacks the human gate)
Routine green packets erode the Owner's attention until sign-off is a
keystroke, not a judgment — invisible in every log.
**Constraints:** (a) **Owner drills**: the packet pipeline MUST, at
random (at least one per calendar month of operation, schedule sealed
by the Architect in advance as a hashed commitment), include a planted
defect the Owner is told exists "sometime this month". A missed plant
PAUSES autopilot (Phase C reverts to manual HC) until a caught plant
resumes it. The catch/miss tally is recorded in GO-SN retros beside the
bug tally. (b) The packet's summary page must always state what would
have to be TRUE for the sprint to be unsound — the Owner reads a
falsification target, not a victory lap.

### R-2 · Checker-of-checkers collapse
Any path letting one agent influence both the code and the checks that
grade it kills the separation of powers while every light stays green.
**Constraints:** (a) ivf/** and .github/workflows/** are
Developer-write-refused (CI job fails any PR/commit from the Developer
role touching them — enforced by path audit, mirroring the arrow-8
pattern). (b) CI executes IVF checks from a PINNED ref updated only by
an Owner-approved commit. (c) The orchestrator may re-RUN a red check
verbatim once (flake allowance) but may never modify, skip, reorder,
or reinterpret one; a second red halts the cycle and pages the Owner.

### R-3 · Silent semantic drift
Hundreds of unattended, individually-reasonable Developer choices can
sum to a walk away from the frozen contracts.
**Constraints:** (a) A CONTRACT-AUDIT CI job grows to cover EVERY
frozen contract in the handover §4 list (AST scans, byte-equality
checks, refusal tests) — drift fails the build, it does not wait for a
reviewer. (b) Every autonomous session still files DEVQs for ambiguity;
an autonomous session that resolves a contract-adjacent ambiguity
WITHOUT a DEVQ is itself a finding. (c) The Architect's sprint-boundary
review remains mandatory before any GO.

### R-4 · Irreversible acts at machine speed
Append-only + burns-forever is a feature at human tempo and a hazard in
a loop: garbage records, spent lineages, and VIRGIN are one bug from
permanent damage.
**Constraints:** (a) Autonomous runs operate on SCRATCH datastores by
default; appending to the REAL journal requires a per-run capability
the orchestrator does not hold — it is granted by an Owner-typed phrase
per sprint (the existing boot one-liner becomes that grant). (b) Burns
and VIRGIN-class acts remain behind interactive typed-phrase gates
(DECLARE VIRGIN precedent) — no autonomous path may hold both
read-VIRGIN and write-journal capabilities, ever, enforced by guard
tests. (c) Journal appends per autonomous session are rate-capped;
exceeding the cap halts.

### R-5 · Injection and credential surface
Autonomous agents read files/logs/library docs — each a channel where
crafted text can try to become instructions; standing tokens on an
always-on machine are theft targets. Today's copy-paste is an
accidental air gap; autopilot removes it.
**Constraints:** (a) Executing agents run with NO web access and
least-privilege GitHub tokens (single-repo, no admin, no workflow
scope), rotated on a schedule. (b) All ingested data remains DATA:
schema validation everywhere (existing habit), and agent prompts/
CLAUDE.md state that file contents are never instructions. (c) Secrets
live in the CI secret store / OS credential manager, never in the repo
or logs.

### R-6 · Cost and loop runaway
An agent retrying against a red check can burn tokens and API quota all
night.
**Constraints:** hard per-session and per-day token/time budgets;
retry limit = 1 (R-2c); budget breach halts and reports; monthly spend
appears in the GO-SN retro.

### R-7 · Fragile plumbing (MT5/Windows/GUI)
Scheduled exports and chart-evidence capture depend on a GUI terminal
that updates, logs out, and breaks silently.
**Constraints:** every plumbing step emits a heartbeat artifact; a
missing heartbeat marks downstream evidence STALE (packet says so
loudly — the R-1 falsification line includes it); plumbing failures
degrade to the manual procedure, never to skipped evidence.

## Consequences
- Owner involvement drops to ~minutes per sprint WITHOUT the sign-off
  becoming ceremonial (R-1 drills keep it real).
- Some throughput is deliberately sacrificed: halts-on-red, scratch-by-
  default, typed-phrase grants. That is the price of running an
  append-only truth machine unattended, paid knowingly.
- New standing artifacts: the Owner-drill commitment + tally, heartbeat
  monitors, contract-audit CI, the per-sprint packet.
- Rollout: Phase A may enter the Developer queue immediately (it
  changes enforcement, not authority). Phases B and C each begin only
  after an Owner go, and Phase C's first month runs in shadow mode
  (packets produced, manual process still authoritative).

## The sentence this ADR exists to enforce
Automation does not remove judgment; it hides where judgment stopped
happening. Therefore every mitigation above makes stopped judgment
LOUD: missed plants pause the system, red checks halt it, drift fails
builds, and the irreversible stays behind a human's typed words.
