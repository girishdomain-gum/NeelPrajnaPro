# ADR-008 — Adopt the Kernel / Trading Plug-in split as the programme's Core/Book architecture

- Status: **PROPOSED** — awaiting owner ratification
- Date: 2026-07-29
- Context: the Platform Architecture v1.0 ("Document 4") specifies a
  domain-blind Kernel (QRF) and a domain-specific Trading plug-in
  (NeelPrajna), joined by a six-object Communication Contract. This ADR
  ratifies that split at the same authority level as ADR-001 ratified the
  MQL5 EA's internal four-layer split.
- Relates to: ADR-001 (internal EA layering — remains valid, now understood
  as Book A's internal structure within the Core/Book split this ADR adds
  above it), ADR-004 and its amendment (epistemic rules, promoted to Core in
  `core/EPISTEMIC_RULES.md`), ADR-005 (governance, unaffected — governance
  already sat above both Core and Book conceptually).
- Does **not** unfreeze ADR-001, ADR-003, or any existing trading-plug-in
  design. This ADR adds a layer above the existing architecture; it does not
  revise anything below it.

---

## 1. Decision

**The programme adopts a two-tier architecture: a domain-blind Core (the QRF
Kernel) and one or more Application Books (NeelPrajna is Book A). Every
future joint project opens its own Book; none of them edit the Core.**

The Core is defined by:
- containing no domain vocabulary, enforced by a CI firewall (AST import
  scan + forbidden-token scan);
- owning the Communication Contract, the Observation Space discipline, and
  the epistemic rules (R1–R3) that govern every EvidenceBattery verdict,
  regardless of domain;
- never issuing an action (trade, or the domain-appropriate equivalent) —
  see the Chief Scientist Principle in `core/COMMUNICATION_CONTRACT.md` §5.

Book A (NeelPrajna) is defined by:
- containing everything the Core forbids: price, bid, ask, spread, pip, lot,
  venue, and the entire MQL5 EA, gates, engine, dashboard, and NPSU
  subsystem already built under ADR-001;
- never learning on its own — all pattern learning and belief updates are a
  Core responsibility, received through the Communication Contract.

## 2. Why now

Three independent lines of work arrived at the same shape without
coordinating: the original architecture vision notes (Observation Space,
concept-after-observation), the Platform Architecture's formal Kernel/plug-in
split, and the Architect's Response's Core/Application-Book proposal for the
wider methodology programme. Three independent arrivals at the same
structure is stronger evidence for that structure than any one argument for
it — this ADR exists to stop the shape from being re-derived a fourth time
and instead give it one ratified home.

## 3. Consequences

**Positive:** a future second project (Book B) inherits the Core unchanged
and starts research-disciplined from its first session, per the Architect's
Response's success criterion; the existing MQL5 EA's proven disciplines
(independent verification, survival-first ranking, sealed evidence) become
Core-level guarantees available to any future domain instead of NeelPrajna-
specific habits; the CI firewall gives the domain-blindness claim a
falsifiable test instead of leaving it as a design aspiration.

**Costs / risks:** two development clocks now exist — Core Kernel
construction and Book A feature velocity — and they can drift apart if not
tracked on the same ladder (see `roadmap/PHASE_LEDGER.md`, which this ADR
requires be updated to carry both clocks); some content currently living in
Book A documents (the epistemic rules, the Observation Space discipline) must
be explicitly promoted to Core, a one-time migration cost paid by the
Documentation Re-architecture (`roadmap/MIGRATION_PLAN.md`).

## 4. Alternatives considered

- **Keep everything as one undifferentiated NeelPrajna-specific system,
  documented informally as "the QRF idea" inside NeelPrajna's own docs.**
  Rejected: this is the status quo the redundancy in
  `DOCUMENTATION_ARCHITECTURE.md` §1 already shows is failing — the same
  idea written three times at three levels of formality.
- **Formalize the Kernel but leave ADR-001's internal EA layering as a
  competing, parallel architecture description.** Rejected: ADR-001's
  layering is not competing, it is nested — Book A's internal structure sits
  entirely inside the Trading-plug-in half of this split. No content in
  ADR-001 needs to change.
- **Wait for Document 5 (Implementation Blueprint) before ratifying
  anything.** Rejected: the Blueprint depends on this split being settled
  first; ratifying the shape now, before the code exists, is the same
  sequencing the Architect's Response used successfully for the wider
  methodology programme ("vision and test harness before content").

## 5. Approval

- Status: **PROPOSED**
- Ratified by: _______________________ Date: _______________
