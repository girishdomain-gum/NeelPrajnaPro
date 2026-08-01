# NOTE-NP-001 · Sprint NP-S1 · 2026-07-30
Author: developer (claude-code)
Refs: NP-ADR-008 §3 (prediction layer, frozen 2026-07-10) and §4 M6; `qrf/trading/simulator/engine.py` (`ExecutionSpec`); `qrf/trading/simulator/fills.py` (`resolve_exit`); `configs/hypotheses/h001_fvg_follow_through.yaml` (precedent).
Tag: discovery (engine-capability gap, AC-4-relevant)

## Finding
NP-ADR-008 §3's prediction layer specifies a **per-trade-variable** stop and
target: *"Stop: penetration extreme ± 10 ticks buffer... Target: 1.5R... 1-second
mid resolution."* The real, drilled Kernel's audited simulator
(`EventEngine.simulate` / `ExecutionSpec`) supports only a single **fixed**
price-distance `stop_offset`/`target_offset` per whole hypothesis (`entry_price ±
offset`, checked intrabar against each bar's own high/low — not 1-second mid) —
there is no mechanism to pass a per-event variable stop/target through the
standard `events` DataFrame (`EventEngine.simulate` reads only `ts, direction,
strength` from it; `level`/`zone_hi`/`zone_lo`/`meta` are never consumed).

This means the evidenced prediction rule **cannot be expressed exactly** by the
real engine — a structural capability gap, not an ambiguity with multiple
defensible readings. Extending the shared, already-certified `EventEngine` to
support per-event variable stops would be a change with blast radius across
every existing hypothesis in this Kernel, is outside NP-S1's deliverables, and
is not something a Developer session should do unilaterally.

## Disposition (Developer judgment, not an Owner/Architect ruling — see below)
Registered the H-07 prediction claim with **no stop, no target**
(`stop_offset: null, target_offset: null`), pure time-stop exit at `hold_bars:
12` (matching the evidenced 12-bar / 1h time stop exactly, which the engine
*does* support natively) and next-bar-open entry in the event's own encoded
direction (which also matches exactly). This tests direction + timing only —
an honest subset of the evidenced rule, not a fabricated fixed-stop
approximation that would misrepresent it. **Direct precedent for this exact
pattern already exists in this Kernel:** `h001_fvg_follow_through.yaml` registers
with `stop_offset: null, target_offset: null` and is described in its own header
as *"naive, no stop/target — the first thing the battery should be able to say
NO to."* I did not raise a DEVQ for this specific choice because it is a hard
engineering constraint (not a judgment call among several valid readings) with
an already-accepted in-repo fallback pattern — but it **is** a real divergence
from §3, and per NP-ADR-008 M6's own framing ("different instrument, therefore a
different judged trade set by construction... pre-registered here so it is read
as arithmetic, not defect"), this note pre-registers it the same way, before any
run.

## Consequence for deliverable 5 (the comparison report, AC-4)
This is a **new, previously-uncatalogued divergence** beyond M1–M7: the real
Battery's trade rule is not just a different *judged trade set* (M6) but a
different *trade rule* (no stop/target at all vs. a 1.5R/10-tick-buffer rule).
AC-4's mapping and interpretation table must name this explicitly — it is not
covered by any of M1–M7 as drafted in NP-ADR-008 §4.

## What I have NOT done
Not extended or modified `qrf/trading/simulator/engine.py` or `fills.py`. Not
attempted to encode a fixed numeric approximation of the variable stop/target
(which would silently misrepresent the evidenced rule as something it is not).
