# Book A: NeelPrajna — the Trading Plug-in

This is the first Application Book: the domain-specific implementation of
the Core Kernel for markets (XAUUSD on MetaTrader 5). Everything the Kernel
deliberately does not know — price, bid, ask, spread, pip, lot, venue — lives
here.

This README is a **pointer map**, not new content. Every document it lists
already exists in the repository (see `DOCUMENTATION_ARCHITECTURE.md` §3 for
exact old→new paths); this file just gives Book A a single front door.

---

## Start here

| If you need... | Go to |
|---|---|
| The trading plug-in's own architecture (adapters, detectors, simulator, cost models) | `TRADING_PLUGIN.md` |
| The MQL5 EA's internal layering (Core/Gates/Engine/Apps/UI) | `ARCHITECTURE.md` (from the former `HANDOVER.md`) + `adr/ADR-001-statehub-eventbus-portfolio.md` |
| Which gates exist, are retired, or are parked | `ARCHITECTURE.md` §Gates |
| The sequential strategy engine | `adr/ADR-003-sequence-engine.md` |
| The shadow-universe research subsystem (NPSU) | `NPSU_DESIGN.md` |
| How to verify an NPSU result independently | `NPSU_POST_VALIDATION_GUIDE.md` |
| Coding style and the firm safety gates | `CODING_GUIDELINES.md` |
| How Chat / Claude Code / scripts divide work | `DEV_WORKFLOW.md` |
| What is currently unfinished, deferred, or parked | `TECH_DEBT.md`, `plans/PARKED.md` |
| The current phase and what's actually done | `../../roadmap/PHASE_LEDGER.md` (shared with Core — one ladder for the whole programme) |
| Fresh-session bootstrap | `SESSION_BOOTSTRAP.md` + `BOOT_PROMPT.md` |
| Multi-model role briefs | `../../governance/AI_ROLE_PROMPTS.md` (shared, not Book-A-only) |

## Division of intelligence (Book A instance of the Chief Scientist Principle)

| Capability | Core (Kernel) | Book A (NeelPrajna runtime) |
|---|---|---|
| Source of observations | Observation Engine (shared) | Observation Engine (shared) |
| Learning | Pattern learning, belief updates, statistics | None — forbidden by design |
| Trading decisions | None — forbidden by design | Sole decision-maker |
| Outputs | Pattern ID, win rates, confidence, regime, applicability | Orders, positions, execution feedback |
| Failure blast radius | Bad knowledge (filtered by review) | Bad trade (bounded by risk layer) |

See `../../core/COMMUNICATION_CONTRACT.md` for the full contract this table
instantiates.

## Current status (see the roadmap for the authoritative version)

EA version v5.9.0. ADR-001's four-layer refactor is DONE. The Sequential
Strategy Engine (Phase 6) is DONE and CLOSED. The Phase 7 Gate Recorder is
DESIGNED, not started. The R6 long run (3–6 months of real-tick data with an
unseen out-of-sample window) is OPEN and is the single highest-value pending
action — see `../../roadmap/PHASE_LEDGER.md` §1 for the authoritative ladder.

## What Book A is not allowed to do

Per the Communication Contract, Book A may never issue a Verdict, burn a
window, or write directly to the Kernel's BeliefLayer. Its own internal
verification machinery (mirror parity, the independent Python verifier,
NPSU's four-layer audit) produces evidence *about* Book A's own trades — it
is not a substitute for, and does not bypass, the Core EvidenceBattery once
Book A's detectors are migrated to emit Kernel-contract Observations.
