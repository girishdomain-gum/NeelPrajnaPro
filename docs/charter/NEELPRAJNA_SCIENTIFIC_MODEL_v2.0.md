# NeelPrajna Scientific Model v2.0

| | |
|---|---|
| **Version** | 2.0 (supersedes DeepSeek draft v1.0; retains its strongest content per REV §"what to retain") |
| **Date** | 2026-07-29 · **Status** | DRAFT — awaiting Owner ratification · **Layer** | Charter (normative) |
| **Predecessor** | NEELPRAJNA_CONSTITUTION_v2.0.md · **Successor** | PLATFORM_INTEGRATION_ARCHITECTURE_v2.0.md |

---

## 1. The Question and the Order

1.1 Every inquiry shall answer, in order: **Existence** (does the phenomenon objectively recur beyond chance?) → **Mechanism** (why?) → **Prediction** (does it pay?). No stage may be skipped; no later stage may be claimed on evidence gathered for an earlier one.

## 2. The Two Roots

2.1 **Records** are immutable assertions that something happened: append-only, hash-chained, timestamped. Corrections are new Records pointing at old ones. In the integrated system, the Record substrate **is** the real QRF `RecordStore` (`qrf/kernel/records/store.py`) — NeelPrajna maintains no second ledger.

2.2 **Scientific Objects** are versioned concepts (phenomena, instruments, mechanisms): every change is a new version with a parent, and every version change is evidence-gated.

2.3 Records and Scientific Objects are never stored in the same structure.

## 3. The Observation Model

3.1 Three layers, strictly ordered: **Measurement** (raw numbers, indisputable) → **Observation** (arithmetic comparison, no theory) → **Concept** (a name; theory enters only here). A Concept is a name for a place where several numbers agree.

3.2 **Observation Space (mandatory scoping).** Every claim carries the complete conditions of its validity across twelve layers: Domain · Instrument · Data Source · Temporal Space · Market State · Market Structure · Statistical Context · Event Context · Observation Window · Detector Context · Confidence Context · Research Context. A claim without a scope is not a claim.

## 4. Phenomenon Taxonomy and Lifecycle

4.1 Six kinds: Event · Structure · State · Transition · Regime · Relationship.

4.2 Lifecycle (no rung-skipping): Candidate → Sealed mechanical definition → ECF registration (claim type + null design) → Planted-truth drill → Clean-control drill → Evidence collection to the pre-sealed n-floor → ECF judgment → Established → Mechanism investigation → Predictive claim.

4.3 In the integrated system, the drills of 4.2 are executed under the real Kernel's CalibrationHarness and IVF disciplines; a detector that has not caught its planted frauds shall not observe for any real claim (P9, "trust follows demonstration").

## 5. The Existence Claim Framework (ECF)

5.1 Claim forms — each registration declares exactly one: **E1 Rate** (occurs at a rate different from expected; rotation nulls) · **E2 Arrangement** (structured clustering/duration/transitions; block-resampling nulls) · **E3 Association** (X predicts Y; model-based surrogates).

5.2 **Definition-trap rule.** An occurrence rate fixed by the phenomenon's own definition is never evidence. For percentile-anchored definitions, testable content lives in the *arrangement*, never the *amount*.

5.3 Null constructions are pre-sealed per claim: N1 rotation · N2 block-resampling · N3 model-based surrogate. The null shall preserve everything about the market that is not the claim and destroy only the claim.

5.4 Verdicts are tri-state — ESTABLISHED / NOT ESTABLISHED / INSUFFICIENT — with P11 semantics. Establishment licenses mechanism and predictive investigation; it licenses no trading conclusion.

5.5 In the integrated system, ECF judgments are rendered by the real EvidenceBattery's nine-step pipeline; the ECF adds claim-form and null-family vocabulary on top of, never instead of, that pipeline.

## 6. The Market Morphology Language (MML)

6.1 Purpose: a deterministic, arithmetic geometry language for candle shapes. The descriptor describes; only the evidence establishes.

6.2 Decomposition — notation corrected (REV F-9). For any OHLC object with Open O, High H, Low L, Close C:

```
upper wick   W_up = H − max(O, C)
body         B    = |C − O|
lower wick   W_lo = min(O, C) − L
range        R    = H − L = W_up + B + W_lo
```

Normalize by R so W_up + B + W_lo = 1: every candle shape is a point on a 2-simplex.

6.3 **Zero-range convention (new, normative):** if R = 0 (H = L), the descriptor is the reserved code `MD-000` and shall be excluded from all shape statistics; detectors shall emit it explicitly rather than dividing by zero or dropping the bar silently.

6.4 Descriptor: `MD-UBL`, three deciles read top-to-bottom (upper, body, lower); digit d denotes the fraction ∈ [10d%, 10(d+1)%), digit 9 covering [90%, 100%].

6.5 Merge operator over any contiguous window: O* = first Open, C* = last Close, H* = max High, L* = min Low — identical to timeframe aggregation. A geometry is **merge-revealed** when descriptor(merged) ∈ S and descriptor(candleᵢ) ∉ S for every constituent i.

## 7. The Graduation Ladder

Observation → Pattern → Concept → Belief → Knowledge → Principle → Theory. A Principle requires cross-instrument and cross-regime survival plus a mechanism-level statement. A Theory requires multiple established Principles, joint explanatory power, novel pre-registered predictions, and stated falsifiers — named, never promised. No rung-skipping.

## 8. Trial Accounting for the NeelPrajna Family (new, normative)

8.1 The 18 founding hypotheses register as ≥18 counted attempts in the real TrialCountLedger at migration; every prior bespoke sweep that can be reconstructed from `np_*` artifacts shall be counted honestly against the family, per QRF-ADR-011.

8.2 The family α-budget ceiling is set by the Owner (§6 of the Constitution) before the first NeelPrajna verdict is requested.

## 9. Deferred Questions

Unchanged from draft v1.0; reviewed only at generation boundaries, by the Owner: object vs question as the deepest unit · universal vs market-specific mechanisms · whether market principles are attainable · theory as achievable or asymptotic · discovery as phenomena vs better questions.

---
*Anchors: **first that it happens, then why, only then whether it pays** · **for a rule that buys its own base rate, existence lives in the arrangement** · **the descriptor describes; only the evidence establishes.***
