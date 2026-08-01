# NeelPrajna × QRF Integration — Verification, Validation & Acceptance Plan
*Four levels of assurance for the neelprajna concept family: unit testing · verification · validation · black-box acceptance*

Status: DRAFT, conditional on ratification. Companion: the docs\execution_plan\ master (sprint mapping lives there). Presentation copy: to be built (see docs\architecture\ for the twin pattern).

**Governing rule, from Volume 0 and the Gen-1 record:** trust follows demonstration — for claims, for instruments, for the platform, and now for a migrated family. Origin grants no shortcuts: NeelPrajna's hypotheses being "already tested" by the bespoke stack earns them nothing here; the bespoke results are treated as *predictions to compare against*, never as evidence. Every pass threshold is sealed before any test runs. Every failure is a tallied finding: root cause, fix, re-run from a clean state — never explained away.

## 1. The Four Levels at a Glance

| Level | Question it answers | Method | Primary sprint |
|---|---|---|---|
| L1 — Unit Testing | Does each ported component compute what its specification says? | Fixtures, property tests, boundary tests | NP-S1, NP-S3 (continuous after) |
| L2 — Verification | Do independent implementations agree on every number — including across the MQL5/Python boundary? | IVF re-implementation from normative text; parity to tolerance; bespoke-battery comparison | NP-S1, NP-S3 (every sprint) |
| L3 — Validation | Does each NP detector find what exists and stay silent when nothing does? | Sealed planted-truth and clean-control drills per detector | NP-S1, NP-S3 (re-run on any change) |
| L4 — Acceptance | Does the migrated family, treated as a black box, behave as trustworthy science? | Blinded adversarial campaign NB-1…NB-5 | NP-S4 |

**The levels nest exactly as in the Gen-2 plan:** L1 failures invalidate L2 runs; any certified component changed voids its certificates and re-triggers the level above; L4 runs only on GREEN L1–L3 and passes only as a single unbroken campaign.

## 2. Level 1 — Unit Testing

### 2.1 The `neelprajna.liquidity_sweep` detector
- Hand-computed fixtures ported from the MQL5 source semantics: equal-high/equal-low pool identification, sweep trigger, reversal confirmation — each with known event counts on synthetic bars, including zero-event fixtures.
- Knowability contract: no event emitted before its confirmation bar; `ts ≥` timestamp of the last input needed — property-tested by incremental feeding with the assertion that emissions never change retroactively (the anti-hindsight invariant, machine-checked).
- Boundary tests: weekend seams (Friday close → Monday open), US DST spring-forward/fall-back weekends — computed from data, never convention (Gen-1 Finding #4's standing rule, inherited verbatim).
- EventFrame column-spec conformance: namespaced `event_type` (`neelprajna.liquidity_sweep.*`), `zone_hi ≥ zone_lo`, `strength ∈ [0,1]` documented, `meta` never load-bearing.

### 2.2 The adapter path
- `NP_Trades_*` / `NPSU_Trades_*` CSV exports through `mt5_csv.py`: OBS-4 close-time normalization asserted on fixtures (adapter ts = open + timeframe); explicit-timeframe parameter required, mismatch is a hard error, never a guess.
- Schema drift guard: an export with an unknown column set is refused with the unknown columns named — silence is never acceptance.

### 2.3 Registration artifacts
- `h0NN_*.yaml` files validate against the existing hypothesis schema; the sealed hash covers claim, scope (full 12-layer Observation Space), n-floor, thresholds, placebo type, and cost-model name; a registration citing an unfrozen or unknown cost-model name is a hard error.

### 2.4 Cost model
- The reconciled `configs/venues.yaml` entry (Owner-ruled name) round-trips: the same trade population costed under it reproduces the sealed round-trip figure to the tick on fixtures; name-immutability test — a second definition under a cited name must be refused.

## 3. Level 2 — Verification (Independent Re-derivation)

1. **IVF parity:** the IVF re-implements the sweep rules from the sealed registration and the Scientific Model text alone — never from the Developer's Python, never from the MQL5 — and must agree on event counts and every ensemble statistic to tolerance 1e-9 on fixtures and on a sealed sample of designated real bars.
2. **Cross-implementation parity (the migration's own risk):** MQL5 gate semantics vs the Python detector on the identical bar series — event-for-event agreement on a sealed sample, with every divergence named and dispositioned before any real registration is judged. This is the dual-implementation discipline the programme already practices, applied to the port itself.
3. **Verdict parity:** every NP Battery ruling re-derived end-to-end from raw CSVs before it is relied upon.
4. **The bespoke-battery comparison (NP-S1's central deliverable):** the real Battery's nine steps vs the recorded B1–B7 result for H-07, gate by gate. Agreement is corroboration; divergence is the sprint's most valuable output; results are never averaged; the drilled instrument's verdict stands. Sealed before the run: the mapping of B1–B7 to the nine steps, and the interpretation of every possible agree/disagree pattern.
5. **Drill-before-judge:** the IVF is drilled with planted frauds, clean control included, before it verifies anything real in this family — the Gen-1 tradition, unchanged.

## 4. Level 3 — Validation (Scientific Certification, per detector)

### 4.1 Planted-truth drills (sensitivity)
- Synthetic bar streams with injected pool/sweep/reversal structure at sealed strengths and counts; the detector must recover the plants at or above claimed power. Drill designs sealed before running.

### 4.2 Clean-control drills (specificity)
- The identical pipeline on surrogates carrying realistic nuisance only (drift, volatility clustering, sessions, seams). Pass: detection rate at or below the sealed false-positive rate. A detector that finds sweeps in silence does not observe for any real claim — this drill has veto power.

### 4.3 Per-hypothesis power and floors
- For predictive claims judged by the existing certified Battery, n-floors come from the sealed registration and may not be set below the floor the Gen-1 power discipline implies for the claim type; where an NP hypothesis is re-expressed as an ECF existence claim (NP-S3 option), its floor comes from Gen-2 S4's injection-calibrated curves and may not undercut them.

### 4.4 Re-certification triggers
- Any change to the detector, the adapter contract, the cost model (new name), or bucket/threshold definitions voids the affected certificates; the drill class re-runs from a clean state before the changed component touches a real claim. NP-S3 detectors are certified one by one; no batch waiver.

## 5. Level 4 — Black-Box Acceptance (NP-S4)

The examiner (Architect, with the Owner holding answer keys) feeds the family blinded inputs and grades outputs only. **Six** drill classes, not five — NB-6 added 2026-07-29.

**NB-1 · Blinded planted-sweep trial (sensitivity).** Synthetic exports, format-indistinguishable from real MT5 CSVs, with injected sweep-reversal structure at certified strengths, interleaved with empty sets. Detection → registration → Battery → verdict, operator blind. Pass: plants ESTABLISHED/PASS at the predicted rate.

**NB-2 · Blinded empty-world trial (specificity).** The interleaved no-structure sets. Pass: nothing establishes beyond the sealed false-positive rate. A failure of NB-2 fails the family's acceptance outright, whatever else passed.

**NB-3 · Negative-control instrument.** The complete NP Wave-1 program executed end-to-end on a synthetic instrument (stochastic-volatility random walk, calendar-matched to gold). Pass: every claim returns NOT ESTABLISHED, FAIL-consistent-with-null, or INSUFFICIENT. The dress rehearsal where nothing must happen.

**NB-4 · Stranger audit.** An independent session — raw CSVs, the ledger, and the normative documents only; no Developer code — re-derives every NP Wave-1 number through to the verdicts. Pass: agreement to IVF tolerance.

**NB-5 · Tamper & boundary drills (integrity).** In a sacrificial copy: an edited NP record; a registration whose hash post-dates its data access; a detector run touching one bar of the R6 withheld window; a second cost-model definition slipped under the frozen name; one evidentiary invocation of the retired bespoke stack. Pass: chain verification, seal-order audit, WindowLedger, the venues loader, and the tripwire in Roadmap §1 each catch their plant; the untampered control raises nothing.

**NB-6 · Interpretation-Lock (ontological discipline).** *(Added 2026-07-29 — adopted from the DeepSeek IVF document's BB-6, a clean non-conflicting fit.)* A human-led sweep of every NP record and verdict for explanatory drift: no classical-pattern names smuggled in outside a declared alias registry, no mechanism claimed before it's earned, every verdict scoped to exactly the operationalization that was registered — never a broader claim than the sealed definition supports. Pass: zero violations found; any violation found is corrected by an appended record (never an edit), tallied as a finding, and the sweep re-run after the fix.

### 5.1 Grading and the acceptance decision
1. Each drill class passes or fails against criteria sealed before the campaign begins.
2. Any failure: tallied finding → root cause → fix → full re-run of the failed class from a clean state.
3. The neelprajna family is ACCEPTED only when all **six** classes pass in one unbroken campaign. Only then do the console unblock and any runtime-consumption design conversation begin (Roadmap §3) — and arming anything that touches the real account remains, at every level, the Owner's typed decision alone.

---
*Anchor: **a migrated family earns trust the way everything here earns trust — planted frauds first, clean control mandatory, and the old judge's opinion is a prediction, not a verdict.***
