# ADR-010 — The Principle of Observational Neutrality

**Status:** Accepted · 2026-07-25 · Owner: Owner + Architecture
**Origin:** Microstructure Extension Reference (2026-07-24) and external
architectural review of it; elevated on the Owner's direction.

## Decision
The following sentence is adopted as a permanent architectural
principle of QRF, ranking with the invariants:

> **"Richer data changes what QRF can see, never how QRF decides what
> is true."**

Formally: QRF's epistemic machinery — ledger, canonical records,
calibration (planted truth + structured-noise silence), placebo
controls, windows and burning, battery, belief classes, independent
verification — is OBSERVATION-NEUTRAL. It judges any measurable,
provenance-preserving observation stream by the identical process.
New data sources may extend the observatory; nothing about a data
source may ever weaken, bypass, or specialize the judging process.

## Reason
The Microstructure Extension Reference demonstrated, stage by stage,
that ingesting professional order-flow data would require new adapters,
schemas, detectors and calibration suites — and zero changes to the
scientific engine. That is not a fact about order flow; it is a fact
about the architecture: QRF is not tied to market data, it is tied to
the scientific evaluation of observations. A property this load-bearing
must be protected by name, or a future extension will erode it
accidentally ("this data is special, so just this once...").

## Consequences
- The principle is queued for inclusion in the Architecture document's
  invariants list at its next editorial revision (joining the existing
  ten; no revision is opened for this alone — the ADR carries it until
  then).
- Any future proposal in which a data source's richness is used to
  argue for a lower evidence bar, a calibration exception, or a
  verification shortcut is rejected by citation of this ADR.
- The reference paper itself remains unchanged and outside Generation-1
  scope; RQ-013 (Observation Layer abstraction) records the eventual
  structural expression of this principle as a post-Gen-1 design study.
