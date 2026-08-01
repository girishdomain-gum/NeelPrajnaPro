# Core: The Communication Contract

> **CORRECTED 2026-07-29.** Written before the real F:\QRF repository was
> read. The real Kernel does not yet have a NeelPrajna-facing Communication
> Contract implemented — that is precisely the gap
> `NeelPrajna_QRF_Integration_Path.docx` proposes closing, concretely, via
> `qrf/trading/adapters/mt5_csv.py` and a new `qrf/trading/concepts/neelprajna/`
> package. Treat this file as the **pre-integration design sketch** the
> integration path document now supersedes with a buildable plan, not as a
> contract that already exists in the real Kernel today.

Canonical source for what may pass between the Kernel (Core) and any
Application Book plug-in. Previously described in the Platform Architecture
§5 and re-derived informally for the MQL5 EA's StateHub/EventBus mechanism —
this document is now the single place both descriptions must agree with.

---

## 1. What it is

The interface between the Kernel and a plug-in is intentionally narrow. Only
six object types travel between them — **never internal variables**.

## 2. The six object types

| Type | Direction | Purpose |
|---|---|---|
| **Observation** | plug-in → Kernel | Raw facts with full context (see Observation Space, below) |
| **Pattern** | Kernel → plug-in | Statistical regularities |
| **Knowledge** | Kernel → plug-in | Validated beliefs |
| **Recommendation** | Kernel → plug-in | Suggested actions |
| **Execution Feedback** | plug-in → Kernel | Outcome of actions taken |
| **Performance** | plug-in → Kernel | Metrics and analytics |

## 3. The two prohibitions

1. **The plug-in never asks about Kernel internals.** It does not query
   "is condition X true?" — it receives a named Observation or Pattern with
   its own strength, confidence, and applicability already attached. This
   prevents the plug-in from depending on Kernel implementation details that
   are free to change.
2. **The Kernel never issues an action.** It does not say "buy" or "sell" (or
   the equivalent action verb in any future domain) — it publishes a Pattern
   with a win rate, a confidence, a regime, and an applicability, and the
   plug-in alone decides what to do with it.

## 4. The five interface contracts and who may issue a Verdict

Not every pipeline stage is allowed to produce a verdict. This is the
concrete mechanism that makes autonomous or high-volume hypothesis
generation safe:

```
Detector      → EventFrame          → BulkStore.write()   → bulk_manifest
Hypothesis    → EvidenceBattery.run() → Verdict + window_burn
Screener      → Shortlist + trial_count bump      (NO verdict, NO window_burn)
Observatory   → anomaly_scan + question           (NO verdict, NO burn)
Verdict       → BeliefLayer.update() → belief state
```

**Beliefs never cite screener metrics, self-test results, or Observatory
questions as evidence.** A candidate or an anomaly may earn a place in the
research queue; it earns no epistemic weight until it passes through the
EvidenceBattery and becomes a Verdict.

## 5. The Chief Scientist Principle

> **The plug-in must never become smarter by itself. The Kernel must never
> take an action by itself.**

| Principle | Meaning |
|---|---|
| Plug-in's intelligence | Derives exclusively from validated Knowledge + its own live observations |
| Kernel's intelligence | Derives from observations + execution outcomes, independent of taking any action |
| The boundary | Learning and acting live in separate components, connected only by this contract |

This is the load-bearing wall of the whole architecture. Every consequence
in `books/book-a-neelprajna/README.md` §"Division of Intelligence" traces
back to this one sentence.

## 6. Worked example (Book A: NeelPrajna)

Instead of the plug-in asking the Kernel "is Gate B3 true?", it receives:

> Observation: Liquidity Sweep at 2412.35, time 14:30, strength 0.87,
> confidence 0.92, applicability: XAUUSD M5, London session, trending regime.

Instead of the Kernel saying "buy gold now", it publishes:

> Pattern X active, win rate 63%, confidence 0.87, applicability: XAUUSD M5,
> London session, trending regime.

The plug-in — and only the plug-in — decides what, if anything, to do with
that Pattern.

## 7. Extensibility principles that govern this contract

| Principle | Statement |
|---|---|
| Origin grants no shortcuts | Human, machine, atlas-browse, or external-AI-sourced hypotheses run the identical pipeline. |
| Trust follows demonstration | Every verifier must first catch planted frauds before judging anything real. |
| Independence is a spectrum, declared never upgraded | Independence tier (broker / LP / venue, or the domain-appropriate equivalent) is fixed at declaration time. |
| Scoping is mandatory | Every Observation and Pattern carries its Observation Space; a claim without a scope is not a claim. |
| History is immutable | The RecordStore is append-only; corrections are new records, never rewrites. |
