# NeelPrajna Platform & Integration Architecture — v1.2

> **Twin rule:** this file is the machine-readable normative TEXT of the
> programme's one architecture document. The docx render for v1.2 is OWED
> (recorded divergence, not hidden). **Versioning law:** only the current
> version lives here; v1.1 (with its O-055 clarification) is archived at
> docs\archive\NeelPrajnaPro_Architecture-v1.1.md; git preserves everything.

## What changed in v1.2 and why (Owner order O-057, 2026-08-02)

**THE BODY RULING: "A body cannot have its organ outside."** The Owner ruled
that both organs live in ONE root — F:\NeelPrajnaPro — with no source-code
dependency outside the repository. v1.2 enacts this:
1. The NeelPrajna runtime (Book A — until now at F:\Fable) becomes the
   repository's SECOND ORGAN at `runtime/` (§B.9), imported with history
   preserved, migrated at NS3 (re-cut O-058: the transplant travels alone).
2. The wall becomes MECHANICALLY TWO-SIDED for the first time (§B.9.3): CI
   can finally test BOTH prohibitions, which physical separation never could.
3. Scope of "inside": SOURCE CODE ONLY. The evidence shelf
   (F:\NeelPrajnaProData) stays outside by the Owner's own wording ("no
   dependency outside **related to source code**") — data is not source, and
   AM-07's no-unbounded-growth law stands. External TOOLS (the MT5 terminal,
   MetaEditor) are tools, not dependencies; source deploys TO them.
v1.1's changes (NS cycle, CCC/MML track, extension relationship §A.0, restored
Execution-Feedback box) all carry forward unchanged below.

## Part A — The Destination

### A.0 The extension relationship (O-055) + the body ruling (O-057)

**NeelPrajnaPro is an extension OF NeelPrajna, and now also its HOME.** The
dependency direction is asymmetric and permanent: NeelPrajna can trade
without Pro but cannot KNOW; Pro cannot exist without NeelPrajna — no
candidates, no data, no consumer. NeelPrajna is: (1) the ORIGIN of every
hypothesis (H-07's playbook, the founding 18, H-08/CCC — nothing not born
there is judged until Pattern Evolution passes Gate A); (2) the SOURCE of the
evidence base (NPSU estate → journal 112→152; NP-S1's 324 judged trades; the
R6 feed on its own terminal/symbol/clock); (3) the GENERATOR of execution
feedback (§A.1 row 13); (4) the CONSUMER of all knowledge (NS6–NS8).
**The body ruling (O-057):** both organs live in this one repository. One
body, one root, one CI, one firewall over both organs. Location changed;
permission did not: **QRF never trades; NeelPrajna never learns on its own** —
the wall is now enforced in code on both sides (§B.9.3).

The two-organ architecture: Market → Observation Engine (one shared reality)
→ Core QRF Brain (`qrf/`) ‖ Book-A NeelPrajna Runtime (`runtime/`) →
Knowledge+Evidence / Orders+Execution-Feedback → event-driven communication.
Failure asymmetry stands: bad knowledge is filtered by review before it can
act; a bad trade is bounded by the risk layer before it can compound.

### A.1 The box column — canonical

| # | Architecture box | Status (2026-08-02, honest) | Delivered by |
|---|---|---|---|
| 1 | EvidenceBattery / WindowLedger | BUILT (+WO-08 checker, drilled) | closed |
| 2 | Scientific Memory (journal, 152 records) | BUILT; NPSU migration DONE | closed |
| 3 | Observation Engine — R6 real-data path | BUILT (AM-07 store + hash-bound provenance) | NS1 completes (zone pin) |
| 4 | ECF null library (N2) | BUILT + drilled; C2 statistic approved | closed |
| 5 | Detector track 1 — liquidity_sweep (H-07) | BUILT; B.1–B.5 re-verified | judgment NS2 (Owner V9, stable tree) |
| 6 | Detector track 2 — MML/CCC (H-08) | DESIGNED | NS3 intake · NS4 port · NS5 registration |
| 7 | **Runtime organ in-repo (`runtime/`)** | **TARGET — the body ruling** | **NS3 (transplant travels alone; history preserved; two-sided firewall)** |
| 8 | First NP existence judgments + IVF re-derivation | MACHINERY BUILT; runs gated | NS2 (H-07) · NS6 (H-08) |
| 9 | Belief update + Knowledge release format v1 | PLANNED | NS7 |
| 10 | Contract v2 + Publication Boundary | DESIGNED (§4) | NS7 |
| 11 | Consumption design + runtime-integration ruling | PLANNED (Owner ceremony) | NS8 |
| 12 | R6 forward collection (calendar-long) | RECURRING background thread | NS2→NS8 |
| 13 | Execution Feedback → Core (Performance Store) — runtime fills/outcomes as observations | TARGET (CSVs exist; NPSU migration = the historical half, DONE) | NS7 (ingestion path with Contract v2 objects); recurring once runtime resumes |
| 14 | Pattern Evolution Wave-2 | HARD-LOCKED (Gate A + ECF survival + row-11 ruling) | outside the cycle |

Acceptance test unchanged: when no row reads TARGET/PLANNED/DESIGNED, the
architecture is built. Rows 5 and 6 are parallel hypothesis tracks under one
judge — neither borrows the other's evidence, alpha, or windows.

### A.2 The NS cycle (eight sprints; O-051, re-cut O-058 — one character per sprint)

**Cutting principles (learned, not decorative):** one gated/irreversible
activity per sprint · judge on a STABLE tree (no burn while the tree is
mid-transplant) · the transplant travels ALONE · every sprint boundary runs
the TRUTH CHECK ritual (board vs git vs status reconciled from real output —
the document-drift class I-12/O-042 keeps producing).

| Sprint | Character | Contents | Human gate |
|---|---|---|---|
| NS1 | Close-out | WO-10 zone pin (live offset readings) → scope registration (two-key) → OOS designation · batch merge to main | merge block · two-key · Owner ceremony |
| NS2 | Ceremony | H-07 judgment on the stable pre-transplant tree: Battery + N2 alongside, atomic verdict+burn, WO-12 identity-correction countersign | Owner V9 + countersign |
| NS3 | Transplant | Runtime organ import (§B.9: plan → APPROVED → Owner-executed blocks, history preserved) + the two-sided firewall drilled RED both ways + CCC reference pinned in place (arrives with the runtime) + twin-render debt cleared (v1.2 docx) | import blocks |
| NS4 | Port | CCC detector port (§3.6) + parity vs the in-repo MQL5 reference on real XAUUSD + planted-truth/clean-control drills | — |
| NS5 | Registration | H-08 pre-registration: statistic, N2 block-length re-derivation (§3.8), frozen thresholds → registration | two-key + Owner |
| NS6 | Judgment | H-08: Battery + N2 alongside, atomic verdict+burn, IVF re-derivation | Owner V9 |
| NS7 | Integration | Knowledge & Contract: belief update from Verdicts · release format v1 (byte-reproducible) · Contract v2 objects · Publication Boundary (leak drill RED) · Execution-Feedback/Performance ingestion path (row 13) | — |
| NS8 | Ruling | Consumption design packet + Owner's runtime-integration ruling | Owner ceremony |

R6 forward collection remains the recurring background thread (NS2→NS8);
WO-23 remains hard-locked outside the cycle.

## Part B — The Binding Architecture (ratified 2026-07-29; §3 amended v1.1; §B.9 added v1.2)

### 1. The Frozen Basis
1.1 Integration into the real, proven QRF Kernel. 1.2 NeelPrajna's bespoke
research stack (np_knowledge_base.py and kin) is retired from evidentiary
service: exploratory only; no verdicts, burns, or belief updates. 1.3 No
Kernel component is re-implemented runtime-side.

### 2. The Kernel, As Actually Built (write authority is a CLOSED list)
| Component | Real location | Role |
|---|---|---|
| RecordStore | qrf/kernel/records/store.py | Hash-chained, single-writer, append-only ledger; torn-tail detection |
| BulkStore / schemas | qrf/kernel/records/ | Parquet + manifests; payload validation |
| InstrumentRegistry / CalibrationHarness | qrf/kernel/instruments/ | Registration; planted-truth and silence tests |
| WindowLedger | qrf/kernel/protocol/windows.py | TRAINING/EXPLORATION/VIRGIN; burn-on-use; reserve-by-market-time |
| EvidenceBattery | qrf/kernel/battery/battery.py | Sole verdict writer; nine steps; atomic verdict+burn |
| BlockNull (N2) | qrf/kernel/battery/block_null.py | ECF null construction; approved statistic; add-one empirical p |
| TrialCountLedger | qrf/kernel/corrections/trials.py | Registration spends the attempt; family deflation |
| BeliefLayer | qrf/kernel/belief/ | Updates from Verdict-typed inputs only |
| DST invariants | qrf/kernel/protocol/dst.py | Pinned server-clock self-policing; RED on drift |
| Observatory | qrf/kernel/observatory/ | Anomaly scans → questions only |
| Kernel firewall | tests/test_kernel_firewall.py | CI-enforced; EXTENDED at NS2 per §B.9.3 |
2.1 Write authority (closed): store.append · Battery (verdict, window_burn) ·
Screener (trial_count) · belief.update (from Verdicts only).

### 3. NeelPrajna as the Second Concept Family (two detector tracks)
3.1 Track 1 `qrf/trading/concepts/neelprajna/` (liquidity_sweep, sealed
NP-ADR-008, H-07). Track 2 `qrf/trading/concepts/ccc/` (MML hidden patterns,
H-08). Both injected, duck-typed; the Kernel imports neither.
3.2 Data path (F-DOC-2 closed): exporter (ivf/mt5, Vantage-pinned, XAUUSD
exact-match) → external evidence store (§3.5) → hash verification
(scripts/verify_csv_provenance.py, drilled RED) → ingest. mt5_csv.py is
BARS-only.
3.3 Hypotheses: configs/hypotheses/h0NN_*.yaml, hashed at registration; 17
script-registered + H-07 = 18 founding (F-DOC-1 closed); family α is
Owner-set. 3.4 Cost model: xauusd_retail_h07, frozen once cited.
3.5 Evidence store (AM-07): raw bulk data NEVER git-tracked; store
F:\NeelPrajnaProData (incoming\, reference\, test reports per O-051);
provenance twins tracked with csv_sha256; git holds the proof, never the
data. **Explicitly outside the body ruling: data is not source (O-057).**
3.6 MML/CCC track: the CCC suite (merge operator O*=first open, C*=last
close, H*=max, L*=min; shape classification; gates hidden/liquidation/
context) implements Scientific Model Diagram 6. Reference = the in-repo
runtime copy after NS2 (hash-pinned in place); Handbook is DOC-IS-SPEC; .ex5
never tracked, never executed. Ownership: 100% Owner (O-051).
3.7 Contamination quarantine (binding): CCC_Prior[], measured-loser
default-OFF, and live calibration are PRIOR EVIDENCE, never parameters;
thresholds frozen at registration; violation is sand-level.
3.8 Null re-derivation (binding): H-08's N2 block length re-derived from
CCC's own frozen constants by a sealed zero-discretion rule; BLOCK_BARS=7 is
sealed to H-07 and does not transfer.
3.9 Windows: seen NP market time designated honestly (TRAINING/EXPLORATION,
never VIRGIN) by the Owner's typed phrase before registration. H-07's sealed
lineage/alpha/FAIL stay sealed; H-08 is a new hypothesis.

### 4. The Communication Contract v2 and the Knowledge Publication Boundary
4.1 Six object types only: Observation · Pattern · Knowledge ·
Recommendation · Execution Feedback · Performance. 4.2 Two prohibitions: the
runtime never asks about Kernel internals; the Kernel never says BUY or
SELL. 4.3 Published objects reference only sealed, Battery-verdicted beliefs
as versioned, dated releases; rolling/unsealed statistics never cross.
4.4 Batch release, not tick-time; stale is stale, never extrapolated.
4.5 QRF publishes WHAT it knows, never HOW.

### 5. What Stays Separate — now BY STRUCTURE, not by disk (v1.2)
| The runtime organ (`runtime/`, paused) | The Kernel (`qrf/`) |
|---|---|
| Live order execution: TradeManager, MoneyManager, EntryGates, 2% rule | Is this hypothesis statistically real? (Battery) |
| Supervisor/Runner trust split; autonomy ladder; G-invariants; the bridge | Is this window contaminated or burned? (WindowLedger) |
| NPSU shadow universes, Live Advisor, dashboards, the CCC chart indicator | How many attempts has this family made? (TrialCountLedger) |
| Per-trade risk, auto-close, session-only apply | Has the claim been reproduced? (IVF) |
5.1 Execution stays where the hands are; truth moves to where the judge is.
The organs now share a ROOT, never a bloodstream: the only crossing surface
is Contract v2 (§4), enforced by §B.9.3.

### 6. Real-Account Switching Safety (permanent)
Auto-Adopt DISABLED pending hysteresis. Arming anything real requires:
hysteresis ≥ the advisory consecutive-win requirement; OOS-validated
eligibility; an Owner arming decision on the record. The machine may
recommend; only the Owner arms — forever. **The body ruling changes nothing
here: importing the runtime's source does not deploy, enable, or arm
anything; the live terminal is untouched until an Owner-run deployment.**

### 7. Verification & Validation Duties
7.1 Every family detector ships planted-truth + clean-control cases, passed
before observing for a registered claim. 7.2 The CCC port proves PARITY
against the in-repo MQL5 reference on real XAUUSD before registration.
7.3 IVF re-derives every verdict; origin grants no shortcuts. 7.4 Every
sprint ends in the Owner's Go/No-Go. 7.5 Drill law house-wide.

### 8. TARGET Tier
Each TARGET element becomes real only through its NS sprint; nothing is
cited as existing before its verdict-bearing artifact. Tick-time streaming
of unsealed statistics is excluded permanently.

### B.9 The Runtime Organ In-Repo (v1.2, the body ruling — NEW)
9.1 **Location:** `runtime/` at the repository root — a SIBLING of `qrf/`,
never inside it. Target layout (refined at import against the real estate):
`runtime/mql5/` (Book A EA source, Include\CCC, indicators) ·
`runtime/supervisor/` (Supervisor/Runner, G-invariants, bridge) ·
`runtime/npsu/` (shadow-universe subsystem) · `runtime/dashboard/` ·
`runtime/docs/` (the runtime's own document estate).
9.2 **Import law (amended AM-11, Owner order O-061):** F:\Fable is
READ-ONLY from this ruling forward — nothing there is ever modified,
committed, or worked in again; its own .git history is preserved IN PLACE as
the permanent record. The import is a SELECTIVE, PROVENANCE-PINNED COPY:
only the source files the body needs are copied into runtime/, and the NS3
import plan names every one. Discipline: (a) before copying, the Fable
commit hash at HEAD is read and recorded — every copied file's provenance
states "copied from F:\Fable @ <commit> on <date>"; (b) each copied file's
sha256 is recorded, vendored-reference style, so drift from the sealed
original is detectable forever; (c) the copy is Owner-executed blocks,
Architect-prepared, plan APPROVED first; (d) nothing is deleted at Fable —
read-only means read-only. This supersedes v1.2's subtree-merge option: the
Owner chose copy-with-pinned-provenance even though Fable IS a git repo
(verified O-060), because Fable's operational estate (comms, bridge,
backups, ship artifacts) is not source and does not belong in the body.
9.3 **The two-sided firewall (the payoff):** the kernel firewall EXTENDS at
import: (a) `qrf/` never imports `runtime/` — the judge cannot reach for the
hands; (b) `runtime/` never imports `qrf.kernel` internals — the hands
cannot reach into the judge; the ONLY permitted crossing is the Contract v2
surface once it exists (NS7); until then, zero imports either way; (c) both
directions drilled RED with planted violations before the import is called
done. MQL5 sources are additionally token-scanned (they cannot import
Python, but the scan proves no generated bridge code crosses either).
9.4 **Compiled artifacts:** *.ex5/*.ex4 stay git-ignored (already law).
Source deploys TO the MT5 terminal; the terminal is a tool, not a
dependency. 9.5 **Paused means paused:** the import moves source; it does
not deploy, arm, or alter the live terminal (§6). 9.6 The old F:\Fable
location, after import, is sealed history: archived, never scrubbed, never
worked in (one-home-per-organ; a stray edit there is an incident).

## Part C — The Visual Atlas
Renders live in the docx master (v1.2 render OWED). v1.0 captions remain
accurate except: Diagram 4's runtime path is `runtime/` in this repository
(was F:\NeelPrajna, then F:\Fable); Diagram 7's null library is BUILT.

## 9. Change Record
- v2.0 body (2026-07-29): RATIFIED. — Unified v1.0 (2026-07-29). — F-24
  correction (2026-07-30).
- v1.1 (2026-08-02, O-051/AM-08): NS cycle; CCC/MML track 2 with quarantine
  and null re-derivation; F-DOC-1/2 closed; evidence store normative;
  runtime home corrected to F:\Fable. — Clarification 2026-08-02b (O-055):
  §A.0 extension relationship; Execution-Feedback box restored.
- **v1.2 (2026-08-02, Owner order O-057 — the body ruling):** both organs in
  one root; `runtime/` defined (§B.9) with history-preserving import, the
  two-sided firewall (§B.9.3, drilled RED both directions), and the explicit
  scope line: source inside, data outside (AM-07 stands), tools are tools.
  §5 re-titled "separate BY STRUCTURE, not by disk". §6 restated: the import
  deploys and arms NOTHING. The wall, write authority, window law,
  ceremonies: UNTOUCHED.
- **v1.2.1 (2026-08-02, Owner order O-058 — sprint re-cut from findings):**
  the Architect's own NS2 was found OVERLOADED (transplant + burn ceremony +
  intake in one sprint — the two highest-risk activity classes stacked).
  Re-cut on stated principles: one gated thing per sprint; judge on a stable
  tree; the transplant travels alone. New order: NS2 = H-07 ceremony (before
  the tree churns) · NS3 = transplant + firewall + CCC pin + twin-render
  debt · NS4 = port · NS5 = registration · NS6 = judgment · NS7 = Knowledge
  & Contract (former NS6+NS7 merged — release format and the contract that
  carries it belong together) · NS8 = ruling. Still eight sprints. Sprint
  boundaries gain the TRUTH CHECK ritual (board/git/status reconciled from
  real output — the I-12/O-042 drift class). Enacted as AM-10.
- **v1.2.2 (2026-08-02, Owner order O-061 — import method settled):**
  F:\Fable verified a git repository (O-060, Architect's own listing), and
  the Owner ruled the import is a SELECTIVE PROVENANCE-PINNED COPY, not a
  subtree merge: Fable becomes READ-ONLY now, its history preserved in
  place; only needed source files copy into runtime/, each pinned to the
  Fable HEAD commit and its own sha256 (vendored-reference discipline).
  §B.9.2 rewritten accordingly; §B.9.6's sealing moves up to NOW. Enacted
  as AM-11.

---
*Anchor: **one body, one root, two organs, one wall — execution stays where
the hands are; truth stays where the judge is.***
