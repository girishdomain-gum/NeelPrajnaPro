# NeelPrajna Platform & Integration Architecture — v1.1

> **Twin rule (Owner-confirmed 2026-07-29):** this file is the machine-readable
> normative TEXT of the programme's one architecture document. The human docx
> render for v1.1 is OWED and not yet regenerated — until it exists,
> `docs\legacy\docx\NeelPrajnaPro_Architecture-v1.0.docx` is one version behind
> this file. That divergence is RECORDED here (per the twin rule, a divergence
> is a finding, and this note is the finding), not hidden.
> **Versioning law:** only the current version lives in docs\architecture\;
> v1.0 moves to docs\archive\ by the Owner's commit block that lands this file.

## What changed in v1.1 and why (Owner order O-051, 2026-08-02)

The Owner ruled three misalignments real and ordered this revision:
1. **Sprint map retired.** Part A's NP-S1..NP-S9+ mapping described a plan that
   was never how this repository actually worked (it ran phases P1..P6 and a
   WO board). Replaced by the NS1..NS8 consolidated cycle (AM-08).
2. **The runtime organ was under-integrated.** Book A / NeelPrajna runtime —
   home **F:\Fable** (path corrected from the stale F:\NeelPrajna; Owner,
   2026-08-02) — appeared in legacy docs but not in the live sprint cycle.
   v1.1 names it explicitly as the second organ, with its integration points
   scheduled (NS6–NS8) instead of implied.
3. **The MML track was missing.** Scientific Model v1.0 Diagram 6 defines the
   Market Morphology Language — the candle as three non-negative fractions, the
   MERGE OPERATOR, the zero-range convention. The CCC Hidden Patterns suite
   (Owner's own work, 100%, confirmed O-051; already integral to the F:\Fable
   runtime) is the MML made operational. v1.1 adds it as the second detector
   track (H-08), governed by §3.6–§3.8 below.

Two standing document findings are also closed in this text: F-DOC-1 (the "18
founding" vs "17 script-registered" wording — resolved by D-014 §2-Q1's
evidence: 17 script-registered + H-07 separate = 18 distinct) and F-DOC-2
(§3.2's data-path claim — mt5_csv.py is a BARS-only adapter; corrected below).

## Part A — The Destination (Owner vision ruling 2026-07-29; cycle re-cut 2026-08-02)

The two-organ architecture is the TARGET: Market → Observation Engine (one
shared reality) → Core QRF Brain (domain-blind, this repository) ‖ Book-A
NeelPrajna Runtime (trading organ, F:\Fable) → Knowledge+Evidence /
Orders+Execution-Feedback → event-driven communication.
**The load-bearing wall, permanent: QRF never trades; NeelPrajna never learns
on its own.** Failure asymmetry stands as ruled: bad knowledge is filtered by
review before it can act; a bad trade is bounded by the risk layer before it
can compound.

### A.1 The box column — canonical (aligned to the NS cycle, AM-08, 2026-08-02)

| # | Architecture box | Status (2026-08-02, honest) | Delivered by |
|---|---|---|---|
| 1 | EvidenceBattery / WindowLedger | BUILT (Gen-1; WO-08 checker added, drilled) | closed |
| 2 | Scientific Memory (RecordStore, journal 152 records) | BUILT; NPSU migration DONE (WO-07) | closed |
| 3 | Observation Engine — R6 real-data path | BUILT: exporter + evidence store + hash-bound provenance (AM-07) | NS1 completes (zone pin) |
| 4 | ECF null library (N2 block-resampling) | BUILT + drilled (WO-15); C2 statistic approved (A-054) | closed |
| 5 | Detector track 1 — liquidity_sweep (H-07, sealed) | BUILT; B.1–B.5 re-verified (D-040) | judgment at NS2 (Owner V9) |
| 6 | Detector track 2 — MML/CCC hidden patterns (H-08) | DESIGNED (reference = Owner's CCC suite) | NS2 intake · NS3 port · NS4 registration |
| 7 | First NP existence judgments + IVF re-derivation | MACHINERY BUILT; runs gated | NS2 (H-07) · NS5 (H-08) |
| 8 | Belief update + Knowledge release format v1 | PLANNED | NS6 |
| 9 | Contract v2 + Knowledge Publication Boundary | DESIGNED (this doc §4) | NS7 |
| 10 | Consumption design + runtime integration ruling | PLANNED (Owner ceremony NP-S4-class) | NS8 |
| 11 | R6 forward collection (calendar-long) | RECURRING background thread, not a sprint | NS2→NS8 |
| 12 | Pattern Evolution Wave-2 | HARD-LOCKED (Gate A + ECF survival + row-10 ruling) | outside the cycle |

**The plan's acceptance test is unchanged:** when no row still reads TARGET/
PLANNED/DESIGNED, the architecture is built. Rows 5 and 6 are parallel
hypothesis tracks under one judge — neither may borrow the other's evidence,
alpha, or windows.

### A.2 The NS cycle (replaces NP-S1..NP-S9+; ≤10 sprints by Owner order)

| Sprint | Contents | Human gate |
|---|---|---|
| NS1 | Close-out: WO-10 zone pin (live offset readings), AM-07 store verified, batch merge to main | merge block |
| NS2 | H-07 judgment ceremony (Battery + N2 alongside, atomic verdict+burn, WO-12 identity correction countersign) · CCC reference intake (vendored, sha256-gated; .ex5 excluded) | Owner V9 + countersign |
| NS3 | CCC detector port (§3.6) + parity vs MQL5 reference on real XAUUSD + planted-truth/clean-control drills | — |
| NS4 | H-08 pre-registration: statistic, N2 block-length re-derivation (§3.8), frozen thresholds → registration | two-key + Owner |
| NS5 | H-08 judgment: Battery + N2 alongside, atomic verdict+burn, IVF re-derivation | Owner V9 |
| NS6 | Belief update from Verdicts + Knowledge release format v1 (byte-reproducible) | — |
| NS7 | Contract v2 objects + Publication Boundary implementation (leak drill RED) | — |
| NS8 | Consumption design packet + Owner's runtime-integration ruling | Owner ceremony |

## Part B — The Binding Architecture (ratified 2026-07-29; §3 amended v1.1)

Version 2.0 body RATIFIED by the Owner 2026-07-29; carried here unchanged
except where a section carries an explicit v1.1 amendment note. Predecessors:
Constitution v2.0 · Scientific Model v1.0 (docs\scientific_model\, normative
.md with docx teaching twin).

### 1. The Frozen Basis
1.1 The architecture is integration into the real, proven QRF Kernel carried
forward into this repository. NeelPrajna's research questions are judged by
the instrument that closed QRF Generation 1.
1.2 NeelPrajna's bespoke research stack (np_knowledge_base.py,
np_probability_engine.py, np_hypothesis_zero.py, np_cost_threshold.py,
np_trade_verifier.py in its judging role) is retired from evidentiary
service. It may run as exploratory tooling; its outputs carry no epistemic
weight and may never write a verdict, burn a window, or update a belief.
1.3 No Kernel component is re-implemented on the NeelPrajna side.

### 2. The Kernel, As Actually Built (write authority is a closed list)
| Component | Real location | Role |
|---|---|---|
| RecordStore | qrf/kernel/records/store.py | Hash-chained, single-writer, fsync'd append-only ledger; torn-tail detection |
| BulkStore / schemas | qrf/kernel/records/ | Parquet + manifests; payload validation |
| InstrumentRegistry / CalibrationHarness | qrf/kernel/instruments/ | Registration; planted-truth and silence tests |
| WindowLedger | qrf/kernel/protocol/windows.py | TRAINING/EXPLORATION/VIRGIN; burn-on-use; structural refusal on reuse; reserve-by-market-time |
| EvidenceBattery | qrf/kernel/battery/battery.py | Sole verdict writer; nine steps; selftest gate; atomic verdict+burn |
| BlockNull (N2) | qrf/kernel/battery/block_null.py | ECF existence-null construction; statistic per A-054; add-one empirical p |
| TrialCountLedger | qrf/kernel/corrections/trials.py | Registration spends the attempt; family deflation at judgment |
| BeliefLayer | qrf/kernel/belief/ | Updates from Verdict-typed inputs only |
| DST invariants | qrf/kernel/protocol/dst.py | Pinned server-clock self-policing (WO-10); RED on drift |
| Observatory | qrf/kernel/observatory/ | Anomaly scans → questions only |
| Kernel firewall | tests/test_kernel_firewall.py | CI-enforced: kernel never imports trading |

2.1 Write authority (closed): store.append · Battery (verdict, window_burn) ·
Screener (trial_count) · belief.update (from Verdicts only). Everything else
proposes or reads.

### 3. NeelPrajna as the Second Concept Family (v1.1: two detector tracks)
3.1 Detector package root: qrf/trading/concepts/ — track 1
`neelprajna/` (liquidity_sweep, sealed H-07 definition, NP-ADR-008); track 2
`ccc/` (MML hidden patterns, H-08; v1.1 addition, §3.6). Both are injected,
duck-typed objects (`.detect(bars_table) -> EventFrame`); the Kernel never
imports either.
3.2 **Data path (v1.1 correction, closes F-DOC-2):** R6 real data flows
exporter (`ivf/mt5/export_xauusd_m5.py`, Vantage-pinned, XAUUSD exact-match)
→ external evidence store (§3.5) → hash verification
(`scripts/verify_csv_provenance.py`, drilled RED) → ingest. The historical
claim that trade logs feed `mt5_csv.py` was wrong: that adapter is BARS-only.
3.3 Hypotheses: configs/hypotheses/h0NN_*.yaml, hashed at registration; 17
script-registered + H-07 separate = 18 distinct founding hypotheses (F-DOC-1
closed by D-014 evidence); family α-budget is Owner-set.
3.4 Cost model: xauusd_retail_h07 — one authoritative configs/venues.yaml
entry; FROZEN once cited; changes require a new name.
3.5 **Evidence store (AM-07, normative):** raw bulk market data is never
git-tracked. Store: `F:\NeelPrajnaProData` (incoming\ for exports; the Owner
extended it to all test-data reports/CSVs, O-051). Provenance twins stay
tracked and carry csv_sha256; ingest-side verification refuses on mismatch.
Git holds the proof of what the data was, never the data.
3.6 **MML/CCC track (v1.1, new):** the CCC Hidden Patterns suite (merge
operator O*=first open, C*=last close, H*=max, L*=min; shape classification;
three gates — hidden / liquidation / context) implements Scientific Model
Diagram 6's Market Morphology Language. The MQL5 source + CCC Handbook are
the REFERENCE SPEC, vendored sha256-gated (like the smc toolkit precedent);
the .docx Handbook is DOC-IS-SPEC where code and doc diverge; the .ex5 binary
is never tracked and never executed. Ownership: 100% Owner's work (O-051).
3.7 **Contamination quarantine (v1.1, binding):** CCC_Prior[] (7-week XAUUSD
M1 measured-edge scores), the measured-loser default-OFF rule, and live
per-instrument calibration (CCC_Calib) are PRIOR EVIDENCE, never parameters.
The H-08 port takes the Handbook's definitional thresholds only, FROZEN at
registration. Any data-derived calibration happens on TRAINING windows before
registration or not at all. Violating this converts pre-registration into
theater and is a sand-level finding.
3.8 **Null re-derivation (v1.1, binding):** N2's BLOCK_BARS=7 was derived
from the sweep detector's own pivot geometry and is sealed TO H-07. H-08's
block length is re-derived from CCC's own frozen constants by a sealed
zero-discretion choice rule (Developer proposes, Architect seals) before
registration. Reusing 7 because it exists is forbidden as settled-by-accident.
3.9 Windows: seen NeelPrajna market time designated honestly (TRAINING/
EXPLORATION, never VIRGIN) by the Owner's typed phrase before registration.
H-07's sealed lineage, spent alpha, and NP-S1's FAIL verdict remain sealed
history; H-08 is a NEW hypothesis with its own registration, alpha, and burn.

### 4. The Communication Contract v2 and the Knowledge Publication Boundary
4.1 Six object types only: Observation · Pattern · Knowledge ·
Recommendation · Execution Feedback · Performance. 4.2 Two prohibitions: the
runtime never asks about Kernel internals; the Kernel never says BUY or SELL.
4.3 Published Knowledge/Pattern objects reference only sealed,
Battery-verdicted beliefs as versioned, dated releases — never streams;
rolling/unsealed statistics never cross. 4.4 Batch release, not tick-time; a
stale release is stale knowledge, never extrapolated. 4.5 QRF publishes WHAT
it knows (Pattern ID, applicability, regime conditioning; verdict-sealed
statistics frozen at release; advisory Recommendations; validated Knowledge),
never HOW (belief state and mechanics, raw observations, calibration and
drill state, decision processes, knowledge-in-progress).

### 5. What Stays Separate, On Purpose (v1.1: runtime home corrected)
| Stays with the runtime (home: **F:\Fable**; paused; execution home) | Lives in the Kernel (this repository) |
|---|---|
| Live order execution: TradeManager, MoneyManager, EntryGates, 2% rule | Is this hypothesis statistically real? (EvidenceBattery) |
| Supervisor/Runner trust split; autonomy ladder; G-invariants; the bridge | Is this window contaminated or burned? (WindowLedger) |
| NPSU shadow universes, Live Advisor, dashboards, CCC chart indicator | How many attempts has this family made? (TrialCountLedger) |
| Per-trade risk, auto-close, session-only apply | Has the claim been independently reproduced? (IVF) |
5.1 The dividing line: execution stays where the hands are; truth moves to
where the judge is. The CCC *indicator* (rendering, dashboard, alerts) stays
runtime-side at F:\Fable; only the MML *mathematics* (§3.6) crosses into the
Kernel's concept family, as a detector that is judged like any other.

### 6. Real-Account Switching Safety (permanent)
Auto-Adopt DISABLED pending hysteresis. Any mechanism changing what the real
account trades without a human click requires, before arming: hysteresis ≥
the advisory path's consecutive-win requirement; OOS-validated eligibility;
an Owner arming decision on the record. Re-enable is per strategy, only after
ECF survival + a Battery-passed pre-registered hypothesis + explicit Owner
enablement. The machine may recommend; only the Owner arms — forever.

### 7. Verification & Validation Duties
7.1 Every family detector — liquidity_sweep AND ccc — ships with
planted-truth and clean-control cases and passes them before observing for
any registered claim. 7.2 The CCC port additionally proves PARITY against its
MQL5 reference on real XAUUSD data before registration (NS3). 7.3 IVF
re-derives every NeelPrajna-family verdict from normative texts, drilled
first; origin grants no shortcuts. 7.4 Every sprint ends in the Owner's
Go/No-Go. 7.5 The drill law is house-wide: no checker is trusted until shown
able to fail.

### 8. TARGET Tier
The two-organ destination — belief releases, Knowledge Graph, Pattern
Evolution, event-driven communication, the two surfaces — becomes real only
through the NS sprint named against its row in §A.1; nothing may be cited as
existing before its verdict-bearing artifact does. Tick-time streaming of
unsealed statistics remains excluded permanently.

## Part C — The Visual Atlas
Renders live in the docx master (v1.1 render OWED — see the twin-rule note at
the head of this file). Caption statuses of the v1.0 atlas remain accurate
except: Diagram 4's runtime path reads F:\NeelPrajna and is corrected to
F:\Fable by this text; Diagram 7's "TARGET null library" is now BUILT (WO-15).

## 9. Change Record
- v2.0 body (2026-07-29): RATIFIED. — Unified-doc v1.0 (2026-07-29): twin
  restructure. — Alignment correction (2026-07-30, F-24): box table matched
  Execution Plan v2.0.
- **v1.1 (2026-08-02, Owner order O-051, enacted with AM-08):** NP-S* sprint
  map replaced by the NS1–NS8 cycle; MML/CCC added as detector track 2 (H-08)
  with contamination quarantine (§3.7) and null re-derivation (§3.8); data
  path corrected (F-DOC-2 closed); founding-hypothesis wording fixed (F-DOC-1
  closed); evidence store made normative (§3.5, AM-07); runtime home
  corrected to F:\Fable and its integration scheduled (NS6–NS8). The wall,
  the Publication Boundary, the write-authority list, window law, and
  real-account safety are UNTOUCHED.

---
*Anchor: **execution stays where the hands are; truth moves to where the
judge is — and now the judge hears two witnesses, one at a time.***
