# DEVQ-008 · QUESTION · Sprint 4 · 2026-07-25
Author: developer (claude-code)
Refs: ARCH-004 §3, Blueprint §2 (instrument_registered.kind enum), §4.8

## Question
ARCH-004 §3 says cost models are "Registered as instruments (kind=data is wrong
— use kind=judge? NO: raise a DEVQ if the catalog's kind enum feels wrong; do
not extend enums silently)." The catalog's `instrument_registered.kind` enum is
`data / detector / judge` (Blueprint §2). A cost model
(`qrf/trading/utility/cost_models.py`, `CostModel.apply(gross)->net`) is:
- not a **data** source (it sources no bars/series; §2 `data` = adapters/datasets),
- not a **detector** (it emits no EventFrame),
- not cleanly a **judge** (the battery is the judge; a cost model is an *input*
  to judging, applied to trades — it renders no PASS/FAIL/INSUFFICIENT verdict).

None of the three enum values fits without strain. Extending the enum is
explicitly forbidden without a decision.

## What I built (functional, ruling-independent)
`configs/venues.yaml` + `CostModel` are complete and unit-tested (hand-computed
net to the cent). The **screener references cost models by NAME** from the yaml,
so the whole Sprint-4 pipeline works with **no** cost-model `instrument_registered`
record. To protect the append-only real ledger from a possibly-wrong `kind`, I
have written **no** cost-model registration record to the real journal. The
registration *surface* exists (`instrument_id="cost.<name>"`,
`kind="judge"` placeholder, `params_schema`, `code_ref`) and is unit-tested in a
scratch store only.

## Options considered
A) **kind=judge**, and treat a cost model as a calibratable judging-side
   instrument (hand-computed examples = its calibration). Closest of the three;
   but overloads "judge", which elsewhere means the verdict-maker.
B) **Do NOT register cost models as instruments.** They are versioned config
   (`configs/venues.yaml`), referenced by name via `hypothesis.cost_model_ref`
   (§2, already a plain string) and echoed into the screener's shortlist note.
   Provenance = the version-controlled yaml + the record that cites the name.
C) Extend the enum with a fourth value (e.g. `cost` / `transform`) — an ADR.

Recommendation: **B** (name-reference; no instrument record). It needs no enum
strain, keeps the ledger honest, and matches how the screener already consumes
costs. If registration is nonetheless wanted, **A** with an ADR noting the
"judge" overload. Proceeding on **B** (nothing written to the real journal)
pending your ruling; reversing to A/C is purely additive (one registration
record), so no rework is blocked.

## How this blocks (or not)
Non-blocking. Sprint-4 screener + costs are complete and green under option B.
