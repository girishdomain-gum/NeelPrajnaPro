# ADR-003 — Sequential/Dynamic Strategy Engine (SequenceEngine)

- Status: **Accepted direction — design pending** (owner-approved, 2026-07-22)
- Relationship: extends ADR-001 (layers, GateBase) and ADR-002 (D4 identity); does not modify either.
- Build phase: **Phase 6** (after Phase 5 legacy removal). No Phase 4/5 dependency.

## 1. Context
The current strategy model is static-concurrent: a strategy = bias mask AND-ed + trigger walk,
all firing within the same evaluation pass. The owner requires support for a *class* (20–30
anticipated) of sequential/dynamic strategies: cross-timeframe chains where each step's signal
matters only to arm the next step, then expires. Canonical example: 1H range liquidity sweep →
5m FVG/OB/POC rejection → 1m CHoCH entry; SL from the 1m structure; target from the 1H mother
body. Because the demand is a stated family, a declarative template engine is justified rather
than hand-written composite gates (which remain possible for one-offs but do not scale to 30).

## 2. Decision (directional)
Build **SequenceEngine** — an application-layer (L3) module executing declarative, state-machine
strategy definitions, developed and validated **virtual-first** in the NPSU universe system.

Core design commitments (binding for the future detailed design):
1. **Step-primitive library.** Sequences compose *primitives* (detectors: liquidity sweep,
   FVG/OB/POC tap-rejection, CHoCH, etc.), each parameterized by timeframe. Primitives are new,
   purpose-built detector units — existing gates are tick-evaluators with private lifecycles and
   are NOT assumed reusable as steps; where a gate's detection logic is wanted, it is extracted
   into a primitive (tech-debt style), not called in place.
2. **Chain runtime.** One state-machine instance per sequence definition per direction: states =
   steps; transitions armed by the prior step's signal; each step carries a TTL/expiry (bars or
   time on its own TF) after which the chain resets. Step relevance ends at handoff by design.
3. **Shared chain memory.** Steps write named artifacts (e.g. step1.range) that later steps and
   the exit/SL/TP resolver reference — the mechanism by which entry uses 1m structure while the
   target uses the 1H mother body.
4. **DSL + identity.** Sequence definitions are roster files with new keys (e.g. seq=, per-step
   tf/ttl/params). D4 identity extends unchanged in principle: canonical-normalized definition →
   8-hex content hash; stem == name= nomenclature; (name, hash) the unique key.
5. **Integration surface.** A running sequence presents to the existing pipeline as ONE trigger
   descriptor (GateBase contract): it pulses with GateResult{sl, tp} only when its final step
   confirms. Registry, walk list, magic attribution, StateHub publishing, and StrategyPortfolio
   ownership all apply unchanged. No GateBase rework anticipated.
6. **Virtual-first, evidence-gated.** Sequences execute ONLY in virtual universes (VirtualBook)
   until a sequence strategy meets the same promotion bar as any other (survival-first + OOS,
   per the R6 discipline). Real-account eligibility is a per-strategy promotion, not an engine
   property. The ADR-001 §2.6 radio invariant applies unchanged.
7. **Dashboard.** Sequence state (current step, armed/expired, chain memory highlights) surfaces
   through StateHub into the SCOPE tab and the visual-mask system (spec v1.2 §7) — a chain's
   step zones are strategy visuals like any other.

## 3. Explicitly deferred to the detailed design (future ADR-003a)
Primitive catalog and parameter schema; DSL grammar; multi-instance concurrency per chart;
per-step re-arm vs. full-chain reset semantics; interaction with MetaSwitchers; analyzer/CSV
schema extensions; performance budget for multi-TF detection on M1 symbols.

## 4. Consequences
Positive: the stated 20–30-strategy family becomes data (roster files), not code; research
velocity moves to the generator/DSL like the existing NPSU flow; identity/attribution/promotion
machinery is reused wholesale. Costs: a new subsystem comparable to NPSU in size; a primitive
library that must be built and verified; DSL/hash canonicalization extensions. Guard: no
SequenceEngine code lands before Phase 5 completes; hand-written composite gates remain the
escape hatch for any urgent single sequence in the interim.
