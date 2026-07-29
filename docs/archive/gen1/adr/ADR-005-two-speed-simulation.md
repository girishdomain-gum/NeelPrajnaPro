# ADR-005 — Two-Speed Simulation; Verdict Engine Is Custom

**Status:** Accepted · 2026-07-24 · Owner: Architecture (frozen in v1.1)

## Decision
vectorbt screens large grids fast and is barred (by type) from
producing verdicts. Final judgments run on a custom ~500-line audited
event engine (bid/ask fills, in-engine costs).

## Reason
One engine cannot be both fast and realistic; verdict-grade fills must
be fully auditable line by line. NautilusTrader/LEAN rejected: framework
assumptions and learning curve exceed benefit for a solo evidence
pipeline.

## Consequences
Screener runs auto-bump the trial-count ledger. IVF verifies the engine
against MT5 Strategy Tester via the frozen-signal RefEA pattern
(execution verified independently; signals verified separately).
