# Core: The QRF Kernel — Overview

> **CORRECTED 2026-07-29.** This document was written from the Platform
> Architecture's abstract description, before this engagement had access to
> the real Kernel repository. **F:\QRF now exists as a separate,
> ten-sprint-old, Generation-1-closed repository with its own excellent,
> ratified documentation.** This file should not be maintained as an
> independent description of the Kernel going forward — that would create
> exactly the two-clock drift risk this project's own analysis (Volume II,
> Errata) flagged. It is kept here **only as a pointer**, re-scoped below.
> The authoritative source is now:
> `F:\QRF\docs\architecture\` (frozen v1.1), `F:\QRF\docs\adr\` (ADR-004
> kernel firewall, ADR-002 append-only ledger, ADR-006 independent
> verification), and `F:\QRF\docs\reference\Architecture_Map.md` (the
> one-page orientation). Read those; treat everything below this notice as
> historical record of the pre-integration understanding, not current truth.

Canonical source for what the Kernel is. This document is domain-blind by the
same rule it describes: if a future edit adds the word "price", "spread", or
"XAUUSD" to this file, that is a defect in the file, not a stylistic choice.

Source: Platform Architecture v1.0, §1–3. This document exists so those
sections have a stable, Core-only address instead of living inside a
document that also contains Trading-plug-in specifics.

---

## 1. The one-sentence architecture

**The Kernel implements the scientific method as domain-blind code. A
plug-in (Book A: NeelPrajna today) supplies the domain vocabulary the Kernel
deliberately does not know.**

## 2. What "domain-blind" means, concretely

The Kernel contains no trading vocabulary — no price, bid, ask, spread, pip,
lot, venue — and this is not a style guideline, it is a build gate:

| Rule | Enforced by |
|---|---|
| No import of `qrf/trading/**` from Kernel code | AST import scan |
| No identifiers: `price`, `bid`, `ask`, `spread`, `pip`, `lot`, `venue` in Kernel code | Token scan |
| Violation fails the build | CI |

If the Kernel ever needs one of these words to do its job, that is a signal
the job belongs in a plug-in, not evidence the rule should be relaxed.

## 3. Kernel components

| Component | Responsibility |
|---|---|
| **RecordStore** | Append-only, hash-chained ledger. History is immutable; corrections are new records. |
| **BulkStore** | Bulk columnar storage (e.g. Parquet) plus manifests. |
| **InstrumentRegistry** | Register and retrieve instruments — domain-agnostic identity, not domain-specific meaning. |
| **CalibrationHarness** | Planted-truth and silence tests. A verifier must catch a planted fraud before it is trusted to judge anything real. |
| **WindowLedger** | Designation, burning, and VIRGIN protection of evaluation windows — the mechanism that prevents data reuse from inflating confidence. |
| **EvidenceBattery** | The judge. The only component allowed to issue PASS / FAIL / INSUFFICIENT. |
| **TrialCountLedger** | Multiplicity corrections — tracks how many things have been tried, so a lucky result can be discounted. |
| **BeliefLayer** | The stance ledger. Updated only by a Verdict (see `COMMUNICATION_CONTRACT.md` §3). |
| **Observatory** | Anomaly scanning — surfaces a `question`, never a verdict. |

## 4. The Kernel firewall, in one sentence

**The Kernel knows how to judge a claim. It does not know what the claim is
about.** That is the plug-in's job (see `books/book-a-neelprajna/TRADING_PLUGIN.md`
for the concrete, market-specific implementation).

## 5. What only the EvidenceBattery may do

A recurring failure mode in autonomous-discovery systems is a candidate or an
anomaly quietly acquiring the weight of a proven result. The Kernel prevents
this structurally: only `EvidenceBattery.run()` may produce a `Verdict`, and
only a `Verdict` may burn a window or update the `BeliefLayer`. See
`COMMUNICATION_CONTRACT.md` §4 for the exact interface contracts this implies.

## 6. Related Core documents

- `COMMUNICATION_CONTRACT.md` — what may pass between the Kernel and any
  plug-in, and the two prohibitions that keep them independent.
- `EPISTEMIC_RULES.md` — the standing rules that keep every EvidenceBattery
  verdict honest, generalized from real practice (not imported theory).

## 7. Relationship to the Application Book layer

The Kernel is designed to generalize patterns already proven inside
Book A (NeelPrajna) — the independent verifier, the resurrection test, the
survival-first evaluation discipline — rather than invent new ones. See
`books/book-a-neelprajna/README.md` for how these patterns look once a
domain (markets) is attached.
