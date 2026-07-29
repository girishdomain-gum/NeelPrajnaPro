# ADR-006 — Trust Through Independent Reproduction (IVF)

**Status:** Accepted · 2026-07-24 · Owner: Verification

## Decision
No sprint closes on its own tests. An independent framework (`ivf/`,
never importing `qrf`, consuming file outputs only) must reproduce key
results via MT5/MQL5 tools, reference values, and human checklists;
differences are auto-reported; each sprint must also catch one planted
bug (drill). Go/No-Go per IVF §8.

## Reason
Internal consistency is not correctness: a bug and its test can agree.
This is the calibration invariant applied to the implementation itself —
the system is an instrument and must pass its own thermometer test.

## Alternatives rejected
- "More unit tests": same codebase, same blind spots.
- Full parallel MQL5 reimplementation of strategies: error-prone;
  instead frozen signals cross as files and only execution is
  independently reproduced.

## Consequences
verification_report records in the ledger; RED spawns a question
record; fix ping-pong (same check RED twice) freezes forward work.
