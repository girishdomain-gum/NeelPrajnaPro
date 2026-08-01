# Decision Register

Institutional memory of *what was decided and why*. Recommended by the
Architect's Response and Production Plan (P1, "evidence before prose") and
never formally started as a standalone artifact — this seeds it from
decisions already on record elsewhere in the repository, so the perishable
asset is captured before it evaporates further.

**Register rules:** entries are immutable once written — a later correction
is a new entry that cites the old one. Every entry names at least one piece
of primary evidence. New entries are written in the same session as the
decision, not reconstructed afterward.

Format per entry: **Decision → Why → Evidence → Status**

---

### DR-001 — BIAS × TRIGGER as the entry model
**Decision:** `Entry(D) = ALL enabled BIAS gates agree on direction D AND ANY
enabled TRIGGER gate fires a pulse in D.`
**Why:** separates "is the market in a state worth trading" (bias) from
"has something specific just happened" (trigger), so each half can be
audited and evolved independently.
**Evidence:** the model has held unchanged across 5+ major EA versions while
individual gates were added, retired, and replaced.
**Status:** ACTIVE, foundational.

### DR-002 — Consume-on-success trigger contract
**Decision:** a trigger's pulse is held until the real path trades it
(`Tx_MarkConsumed`) or the gate expires it — never consumed speculatively.
**Why:** prevents a trigger from silently firing into a trade that never
actually happened, which would corrupt attribution.
**Evidence:** magic-offset attribution has remained reliable across the
version history with no reported cross-gate misattribution.
**Status:** ACTIVE.

### DR-003 — Magic-offset immutability
**Decision:** magic-number offsets identifying which gate opened a trade are
permanent constants, never reassigned, even for retired gates (T6, B5).
**Why:** historical CSV logs must remain attributable forever; reassigning
an offset would silently corrupt old evidence.
**Evidence:** retired gates T6/B5 kept their offsets reserved rather than
recycled.
**Status:** ACTIVE, permanent.

### DR-004 — Survival-first evaluation, never raw ROI
**Decision:** official ranking order is max drawdown → worst losing streak →
ranging-week behaviour → profit factor. Raw ROI is never used to rank.
**Why:** ROI rewards variance; a strategy can rank well on ROI while being
one bad week from ruin.
**Evidence:** applied consistently across NPSU universe ranking, the Live
Advisor, and meta-switcher evaluation.
**Status:** ACTIVE, constitutional (see `core/EPISTEMIC_RULES.md`).

### DR-005 — Strategies as external data files, EA read-only
**Decision:** NPSU strategy definitions live as plain-text DSL files in a
shared folder; the EA only reads them, never writes them; a companion Python
tool generates them.
**Why:** decouples strategy authoring from EA recompilation; keeps the EA's
read/write boundary auditable.
**Evidence:** roster capacity raised from 15 to 59 files without any EA
code change.
**Status:** ACTIVE.

### DR-006 — Advisory-only before autonomous action, with eligibility + hysteresis
**Decision:** the Live Advisor recommends but never trades; a later
"auto-adopt" escalation requires eligibility (minimum trade count, validated
flag) and hysteresis (consecutive-win confirmation) before any live
suggestion is acted on.
**Why:** prevents a single lucky window from flipping the real account's
strategy.
**Evidence:** the LAST_TRADE auto-adopt criterion was rejected after scoring
+29R then −25R on n=2 — exactly the failure this rule exists to prevent (see
LR-004).
**Status:** ACTIVE.

### DR-007 — One-click apply as human-in-the-loop, radio-style, session-only
**Decision:** a human may apply an NPSU universe's configuration to the real
account with one click; only one strategy may be active on the real account
at a time; the apply is session-only (reattaching the EA resets it).
**Why:** keeps a human decision point in the loop while making the
mechanical part of switching strategies fast and low-error.
**Evidence:** in production since v3.9.0 with no reported unintended
switches.
**Status:** ACTIVE.

### DR-008 — A meta-switching criterion may drive the real account only after it wins backtest + out-of-sample
**Decision:** no meta-switcher criterion (equity, win-rate, last-trade) may
be applied to the real account until it has beaten simply holding the best
static strategy in both backtest and an out-of-sample window.
**Why:** switching criteria are themselves hypotheses and must clear the
same bar as any other strategy claim.
**Evidence:** written directly in response to the LAST_TRADE failure (LR-004);
enforced ever since.
**Status:** ACTIVE.

### DR-009 — REAL account runs exactly one strategy at a time; concurrency is virtual-only
**Decision:** the real account never runs more than one strategy
simultaneously; concurrent multi-strategy execution exists only inside
NPSU's virtual books.
**Why:** avoids capital-allocation and netting-conflict complexity that has
no proven research payoff yet.
**Evidence:** ADR-001 §2.6; changing this requires a superseding ADR.
**Status:** ACTIVE, changeable only by ADR.

### DR-010 — Supervisor/Runner trust split (G3) over a single mutable agent
**Decision:** operational autonomy is split into a frozen, small,
owner-reviewed Supervisor and a mutable, AI-authored Runner, rather than one
self-modifying agent.
**Why:** resolves the bootstrap paradox between "no human restart needed"
and "the agent only runs code the owner has seen."
**Evidence:** ADR-005 §4, owner-ruled APPROVED 2026-07-27.
**Status:** ACTIVE, constitutional.

### DR-011 — Only the EvidenceBattery may issue a Verdict
**Decision:** Screener and Observatory outputs (candidates, anomalies,
questions) never carry evidentiary weight on their own; only a Verdict from
the EvidenceBattery may burn a window or update the BeliefLayer.
**Why:** makes high-volume or autonomous hypothesis generation safe — a
candidate cannot smuggle itself into "known" status.
**Evidence:** Platform Architecture §6, "Beliefs never cite screener
metrics, selftest results, or questions as evidence."
**Status:** ACTIVE, Core-constitutional.

---

## How to add an entry

1. Write it in the same session as the decision.
2. Cite at least one piece of primary evidence (a run ID, an ADR, a commit,
   a dated observation).
3. Never edit a past entry's substance — append a new entry that supersedes
   it and says so explicitly.
