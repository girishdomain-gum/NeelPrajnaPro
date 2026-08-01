# Lesson Register

Institutional memory of *what went wrong and what changed as a result*.
Companion to `DECISION_REGISTER.md`. Format follows the pattern the
Architect's Response recommended: **why this exists → the failure that
forced it → the lesson → the architectural change → the evidence.**

---

### LR-001 — "Looks wired" is not wired
**Why this exists:** early NPSU features appeared to work but had never
produced independently verified output.
**The failure:** a feature compiled, ran, and looked correct on inspection
while its actual output had never been checked against ground truth.
**The lesson:** a feature is not done when it compiles or even when it runs
— it is done when its output has been independently verified.
**The architectural change:** acceptance tests AT-1 (a fresh run must
produce rows) and AT-9 (cold-start resurrection); the NPSU-D1 audit trail;
a second, independent Python implementation of the trading rules
(`np_trade_verifier.py`, rules R1–R9); runtime invariants that raise a loud
violation banner rather than passing silently.
**Evidence:** the verifier, tested against a deliberately corrupted trade,
caught all six planted violations and passed the clean trade 9/9
(2026-07-12).

### LR-002 — An unstable sort can manufacture false violations
**Why this exists:** the independent trade verifier began reporting
violations that were not real.
**The failure:** pandas' default quicksort is unstable and reordered
same-minute BE/TRAIL audit rows, producing 1,297 false-positive violations
on a single run.
**The lesson:** any sort used for causal/sequential reasoning over
timestamped data must be stable, not merely "sorted."
**The architectural change:** switched to `kind="stable"` in the verifier's
sort call.
**Evidence:** the same run then certified 2,199 of 2,199 virtual trades
clean.

### LR-003 — A correlated gate is not additive evidence
**Why this exists:** a new bias gate (B6, regression-channel trend quality)
was added and initially evaluated as if it were independent information.
**The failure:** B6's regression slope correlates substantially with an
existing bias gate (B1); crediting it as fully independent would overstate
its marginal value.
**The lesson:** when a new signal correlates with an existing one, only the
marginal information (here: the correlation cut plus multi-timeframe
agreement) should be credited — recorded explicitly as a caveat rather than
silently assumed away.
**The architectural change:** B6 shipped with the correlation caveat
recorded in the version history, and a dedicated roster (R5) was built to
test it as both a replacement and an addition.
**Evidence:** R4/R5 audition runs (81906, 92546, 68484).

### LR-004 — n=2 is not evidence, however dramatic
**Why this exists:** an auto-adopt criterion (LAST_TRADE) scored +29R on one
run.
**The failure:** the same criterion then scored −25R on the very next
window — the entire "signal" was variance on a two-observation sample.
**The lesson:** a criterion may drive the real account only after it wins in
both backtest and out-of-sample — never on the strength of a single
dramatic result.
**The architectural change:** DR-008 (see Decision Register) was written
directly in response, and meta-switchers were required to race as virtual
universes under the same rule before being trusted.
**Evidence:** the +29R / −25R pair itself, recorded in the version history.

### LR-005 — A comparison across two runs can look like a real effect and be a data artifact
**Why this exists:** a cadence change (evaluating on bar close vs. every
tick) appeared, in one comparison, to cost 8.8R.
**The failure:** the two compared arms differed in more than the cadence —
one had a break-even rule the other lacked — and separately, two runs used
to draw a conclusion about break-even's effect on a strategy had different
underlying tick counts entirely.
**The lesson:** (1) a comparison is valid only when the arms differ in
exactly one thing; (2) only compare within a run, never across runs with
different underlying data.
**The architectural change:** R2 and R3 in `core/EPISTEMIC_RULES.md`
(originally ADR-004's amendment); an earlier conclusion that break-even had
hurt a strategy was explicitly withdrawn once traced to the dataset
difference.
**Evidence:** run 94984 (20,464 bars) vs. run 40906 (21,844 bars) —
different data, therefore not comparable; ADR-004-amendment-summary.md.

### LR-006 — Copying files while a process is running corrupts state
**Why this exists:** a NeelPrajna-adjacent side project (DriftPro) moved
files while its process had them open.
**The failure:** the running process's writes were lost or corrupted mid-move.
**The lesson:** copy, don't move, files a running process may still be
writing.
**The architectural change:** carried forward as one of eleven DriftPro
design rules (L1–L11) informing NeelPrajna's own file-handling discipline.
**Evidence:** DriftPro bug inventory, NPSU design doc §3.

### LR-007 — A single exporter is a single point of failure for evidence
**Why this exists:** some result files were found to contain only a header
row, with no data ever written.
**The failure:** the exporter wrote its header once and never streamed
subsequent rows under certain conditions, and this went unnoticed because
nothing checked for it.
**The lesson:** never rely on a single exporter firing once at the end;
stream periodically so a partial failure still leaves partial evidence.
**The architectural change:** NPSU summary snapshots write on every interval,
not only at EA deinit; every export logs its own row count.
**Evidence:** v3.6.2 changelog entry.

### LR-008 — A frozen contract still needs a change procedure for the day it must change
**Why this exists:** the Supervisor is deliberately frozen, but "frozen"
cannot mean "can never be fixed."
**The failure (avoided, not experienced):** none yet — this is a
preventive lesson, recorded because the failure mode (a security issue or
defect with no sanctioned path to fix it) was foreseeable.
**The lesson:** evolve safety-critical, rarely-changing components like
firmware, not like software — valid reasons to change are a security issue,
a defect, or an environment change; "we thought of a better way" is not
valid.
**The architectural change:** SUPERVISOR_CONTRACT.md §5–7: any proposed
change requires a written ADR first, showing the need cannot be met in a
lower layer, before the contract itself may be amended.
**Evidence:** Supervisor Contract v1.1, amended 2026-07-27 after
owner-endorsed signature.

---

## How to add an entry

Written in the same session as the event whenever possible — knowledge
streams at close, the same discipline already applied to trade logs (see
LR-007, the lesson this rule itself follows).
