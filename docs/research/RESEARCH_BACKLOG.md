# QRF Research Backlog — living register
Owner: Architect · Governance: ADR-009 · Companion: QRF_Future_Research_Program docx (Edition 1.1)
RULE: nothing here changes Generation-1 architecture unless supported by
evidence AND an approved ADR. New entries use the next RQ number
(allocate after `git fetch`, per NOTE-005). Full template in the docx,
Part 4. Statuses: Open / Exploring / Prototyped / Evidence-gathered /
Promoted (ADR-nnn) / Retired (reason preserved — rejection is knowledge).
WINDOW RULE: research experiments obey the WindowLedger; any experiment
that consumes or burns windows requires Owner approval BEFORE it runs.

---
## RQ-001 · Autonomous Concept Discovery · Open · Priority High · Gen-2 · Blocks Phase 1? No
Can candidate concepts emerge from recurring observational regularities
in the event stream, while passing the same calibration bar (thermometer
test) as human concepts? Assumption today: concepts are human-authored.
First experiment: mine recurring event-context motifs on TRAINING
windows; register candidates as ordinary instruments; compare against
the Fibonacci placebo family as the control. Deps: battery+belief layer,
event history, RQ-005, RQ-008.

## RQ-002 · Scientific Agency · Open · Priority High · Gen-3 · Blocks Phase 1? No
Can QRF generate and prioritize research questions (a machine-fed
question queue) that a human researcher judges worth asking? Assumption:
agency is human; the queue is hand-fed. Boundary: proposals only — truth
decisions stay human. Experiment: shadow queue — machine proposals
logged beside human ones for one quarter; blind usefulness rating.
Deps: belief layer, queue history, RQ-008.

## RQ-003 · Mechanism Discovery · Open · Priority Medium · Gen-4 · Blocks Phase 1? No
Can mechanism nodes be synthesized from accumulated evidence links, and
can competing mechanisms coexist with explicit belief mass? Assumption:
mechanisms are human explanations attached after evidence. Machine
mechanisms stay UNPROVEN until a confirmed out-of-sample prediction.
Experiment: mechanism ablation — remove a human mechanism node, test
whether evidence topology re-suggests it.

## RQ-004 · Concept Lifecycle & Evolution · Open · Priority Medium · Gen-2 · Blocks Phase 1? No
When does a recurring pattern deserve concept status, and when should a
concept retire? Assumption: registration and retirement are human acts.
Experiment: define promotion/retirement criteria (stability across
regimes, out-of-window persistence, incremental predictive value) and
back-apply to existing concepts as a dry run.

## RQ-005 · Novelty Measurement · Open · Priority Medium · Gen-2 · Blocks Phase 1? No
How is novelty measured so discovery isn't data-snooping in disguise?
Assumption: novelty is judged by the human eye. Experiment: candidate
metrics (distance from registered concepts' event signatures; burned-
window-aware validation) scored against placebo discoveries. Novelty is
never sufficient — calibration and persistence remain the bar.

## RQ-006 · Meta-Science / Self-Audit · Open · Priority Low · Gen-5 · Blocks Phase 1? No
Can QRF detect flaws in its own reasoning — contamination beyond the
Tuesday-trap rule, observer bias, silent prior drift? Assumption: the
IVF + human eyes are the only auditors. Experiment: planted-flaw drills
at the reasoning layer (the Drill pattern, promoted from data to
inference). Drill authors independent of audited machinery (IVF rule,
recursively applied).

## RQ-007 · Cross-Market Concept Transfer · Open · Priority Medium · Gen-2/3 · Blocks Phase 1? No
Does a concept survive a market it has never seen? Promoted from the
Deferred list (editorial review): it was filed as a data-plane issue but
is a validity instrument — generalization to untouched data is the
strongest out-of-sample test available. Experiment: freeze a battery-
proven concept; ingest a second market under fresh window designations;
run the identical battery; classify outcome (survives/degrades/dies).
Placebos must fail to transfer. Caveat recorded for correlated markets.
Deps: multi-instrument data plane, cross-instrument window discipline.

## RQ-008 · Observation Compression · Open · Priority Medium · Gen-2 · Blocks Phase 1? No
Can event history be compressed without losing evidence? A hidden
prerequisite of RQ-001/002 made explicit (editorial review): discovery
and agency both assume the history is summarizable. Experiment: answer a
fixed panel of evidential questions from raw records AND from summaries;
divergence must be ≈0, and an adversarially hidden contradiction must
surface, not smooth away. Summaries carry provenance; IVF pattern
applies (independent re-derivation from raw). Risk named: compression
as censorship.
