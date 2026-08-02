# NeelPrajnaPro — Appendix: Shortcut Terminology (Glossary)

> One-doc-per-thing law: this is THE glossary of the programme. Written for
> the Owner first — plain English, one line where one line is enough.
> Maintained by the Architect; updated whenever a new shorthand enters use.
> Created 2026-08-02 (Owner order O-054). If a term used in comms, code, or
> docs is missing here, that is a finding — add it, don't assume it.

## 1. Sprints, phases, and cycles

| Term | Meaning |
|---|---|
| **NS1..NS8** | The current sprint cycle (Architecture v1.1 §A.2, AM-08). NS = "New Sprint". NS1 close-out · NS2 H-07 judgment + CCC intake · NS3 CCC port · NS4 H-08 registration · NS5 H-08 judgment · NS6 belief/release · NS7 Contract v2 · NS8 consumption ruling. |
| **NP-S1..NP-S9+** | RETIRED sprint numbering from the old execution plan. Appears in sealed history only. NP-S1 also names the first real judgment (verdict: FAIL) — that usage stays. |
| **S0..S16 / S1..S10** | Session numbers used on the WO board's history rows (chat-window work sessions, not the NS cycle). |
| **P1..P6** | The phase numbering used before the NS cycle (ROADMAP era). History only. |
| **Gen-1 / Gen-2** | Generation 1 = the original QRF cycle (closed: ten sprints, four hypotheses judged, zero promoted). Gen-2 = this programme. |
| **WO-xx** | Work Order — one unit of scoped work on the STATE.md board (e.g. WO-10 = R6 activation). |

## 2. Message and record ids (comms\)

| Term | Meaning |
|---|---|
| **A-xxx** | A message FROM the Architect. |
| **D-xxx** | A message FROM the Developer. |
| **O-xxx** | An Owner order, recorded by an agent in its console file. Both agents assign O-ids: next = max+1 across BOTH consoles. Collisions stand, disambiguated by file (O-034 precedent). |
| **I-xx** | Incident — something that went wrong, with the rule it forged. Never deleted. |
| **F-xxx** | Finding (e.g. F-DOC-2, F-PROBE-2) — a discovered discrepancy, tracked to closure. |
| **AM-xx** | AMENDMENT — the only way the spec changes. Written by the Architect only, indexed in STATE.md, highest number wins. |
| **JOB-xxx** | A file-based job for tools\run_job.sh (the Owner runs the oldest pending job). |

## 3. Hypotheses and detectors

| Term | Meaning |
|---|---|
| **H-07** | Hypothesis 07: the liquidity-sweep detector claim (sealed definition NP-ADR-008). Registered, alpha spent, lineage sealed; judgment scheduled NS2. |
| **H-08** | Hypothesis 08: the CCC hidden-patterns claim (MML track). A NEW hypothesis — own registration, own alpha, own burn. Registered at NS4. |
| **CCC** | Candlestick Combination Concepts — the Owner's own hidden-patterns method and MQL5 indicator suite (Handbook + source, 100% Owner's work). Reference at F:\NeelPrajnaProData\reference\. |
| **MML** | Market Morphology Language (Scientific Model Diagram 6): a candle as three non-negative fractions summing to one, plus the MERGE OPERATOR and the zero-range convention. CCC is the MML made operational. |
| **Merge operator** | Combining w adjacent candles into one: O* = first open, C* = last close, H* = max high, L* = min low. |
| **The three gates (CCC)** | hidden (no component candle shows the shape) · liquidation (window has both red and green bodies) · context (ATR-significant range at a swing extreme). |
| **smc / smc toolkit** | Smart-money-concepts vendored reference (sha256-gated, byte-identical). Precedent for how CCC is vendored. |
| **Detector** | An injected, duck-typed object `.detect(bars_table) -> EventFrame`. The Kernel never imports one. |

## 4. The judging machinery

| Term | Meaning |
|---|---|
| **QRF** | Quantitative Research Framework — the Kernel; the judge. QRF never trades (see "the wall"). |
| **Battery / EvidenceBattery** | The SOLE verdict writer. Nine steps, selftest gate, atomic verdict+burn. |
| **Verdict** | The Battery's tri-state answer on a pre-registered hypothesis. NP-S1's was FAIL — treated as a success of the machinery. |
| **ECF** | Existence Claim Framework — how "does this exist?" is judged: claim forms E1/E2/E3, each with a null family N1/N2/N3 built to destroy exactly that claim. |
| **N2** | The block-resampling null: shuffle whole blocks of real bars (weekday-matched) to destroy event arrangement while keeping local candle geometry. |
| **BLOCK_BARS** | N2's block length. =7 for H-07 (derived from its pivot geometry, sealed). H-08 gets its OWN re-derived value — 7 does not transfer. |
| **n_local_sweeps** | H-07's approved N2 existence statistic (A-054): sweep events with pool_age_bars ≤ BLOCK_BARS. |
| **Empirical p (add-one)** | (ge+1)/(n+1) — the honest p-value from n null runs; can never claim an impossible 0.0. |
| **MFE / MAE** | Max Favourable / Adverse Excursion after a signal (used in CCC's own stats; prior evidence, never a parameter here). |
| **Alpha (α)** | The error budget a registration spends. Spent at registration, deflated per family at judgment; never reused. |
| **Pre-registration** | The claim, statistic, thresholds, and window are fixed and hashed BEFORE looking at the judging data. |
| **IVF** | Independent Verification Framework — stdlib-only tools that re-derive every verdict from normative texts. Propose-only; the Developer never edits ivf\verify_*. |
| **NP-ADR-008** | The sealed Architecture Decision Record defining the liquidity-sweep detector (appendix B.1–B.5 = its exact rules). |

## 5. Windows, burns, ceremonies

| Term | Meaning |
|---|---|
| **Window** | A span of market time with a designation: TRAINING, EXPLORATION, or VIRGIN. |
| **VIRGIN** | Market time never seen by anyone. The only source of untainted out-of-sample evidence. |
| **Burn** | Using a window for a judgment spends it forever. Atomic with the verdict. |
| **OOS** | Out-Of-Sample — evidence from data not used to build the thing being tested. |
| **V9 / GO-NO-GO** | The Owner's typed ceremony authorizing a judgment run/burn. Every burn of every class takes the full ceremony. |
| **Two-key** | A real-journal write needs the Architect's prepared job PLUS the Owner's action, verifier before/after, and the delta committed+pushed. |
| **V1..V9 (V-gate)** | The per-WO validation ladder: own ATs · full suite · drills · ruff · commit+push · Architect review · Owner accept · IVF re-derivation · Owner GO/NO-GO. |
| **WindowLedger** | The Kernel component that enforces designation and burn-on-use; checker: check_window_ledger (windows/burns/virgin counts). |

## 6. Data and evidence

| Term | Meaning |
|---|---|
| **R6** | The real Vantage XAUUSD M5 dataset programme: export → verify → ingest → (eventually) OOS designation. WO-14 = its recurring collection. |
| **Evidence store** | F:\NeelPrajnaProData — bulk data (incoming\), reference material (reference\), test reports. NEVER git-tracked (AM-07/AM-08); backed up off-disk (Owner-confirmed O-053). |
| **Provenance twin** | The small tracked text file beside every export: what/when/where it came from, plus csv_sha256 — git holds the PROOF of what the data was. |
| **csv_sha256 / hash-bound** | The file hash recorded in the twin; scripts\verify_csv_provenance.py refuses on mismatch (drilled RED). |
| **Zone pin / DST pin** | The evidence-backed conclusion that Vantage's server clock is a fixed-offset (non-DST) zone; self-policing in qrf/kernel/protocol/dst.py. The absolute offset still needs two live readings. |
| **NPSU** | NeelPrajna Shadow Universe — runtime-side research subsystem; its historical trades were migrated into the journal (WO-07); its outputs are candidates, never evidence. |
| **Journal** | The hash-chained append-only ledger (datastore/journal/journal.jsonl, 152 records); verified by ivf.verify_journal. |
| **Vantage pins** | Terminal `C:\Program Files\Vantage Markets MT5 Terminal\` · server VantageMarkets-Demo · symbol **XAUUSD exact-match** (XAUUSD.crp never used) · VANTAGE ONLY, no other broker. |
| **xauusd_retail_h07** | The frozen, named cost model every registration cites. |

## 7. Law, habits, and house language

| Term | Meaning |
|---|---|
| **The wall** | QRF never trades; NeelPrajna never learns on its own. Permanent. |
| **Drill law** | No checker is trusted until it has been SHOWN to fail: tampered input → RED, clean control → GREEN. |
| **DOC-IS-SPEC** | Where a reference implementation and its documentation diverge, the DOC is the spec and the code is a quarry. |
| **Settled by accident** | A decision made by a side effect (a path typo, a default) instead of by a person. Forbidden; always escalate. |
| **Sand-level finding** | A flaw in the scientific foundation itself (e.g. contamination) — surfaces immediately, even mid-sprint. |
| **Checkpoints are claims** | Every expected-output line in a command block is a claim the author must have verified. |
| **Completion rule** | Nothing is "landed" until the Owner pastes the log and the Architect confirms it from the output. |
| **Two-key evidence** | Machine checks never replace the Owner's eyeball, and neither replaces the Architect's own look. |
| **Append-only** | Message/console files: read whole, append at bottom, never edit an existing block. Position is NOT chronology (I-12) — ids and dates are. |
| **One window per role** | Exactly one live chat per role (Architect/Developer); a new window opens only after "prepare handover" closes the old one (protocol v1.6, incident I-12). |
| **Prepare handover** | The closing ritual: flush messages, overwrite handover+status files, then the window may close. |
| **Contamination quarantine** | Measured-performance numbers from prior work (e.g. CCC_Prior[]) are PRIOR EVIDENCE, never parameters (Architecture v1.1 §3.7). |
| **Gate A** | The autonomy gate that must pass before any machine-proposed pattern work (WO-23) may even be designed. |
| **Hard-locked** | Cannot be started under ANY amendment (only WO-23). |
| **CLOSED-OBE** | Closed, Overtaken By Events — a WO made unnecessary before it ran. |
| **The board** | comms\STATE.md — the single source of truth; if it and any other document disagree, the board wins and the disagreement is a finding. |

## Change record
- v1.0 (2026-08-02, O-054): created. Sources: Architecture v1.1, Scientific
  Model v1.0, COMMS_PROTOCOL v1.6, STATE.md, GIT_WORKFLOW, AM-01..AM-08, and
  the session record through O-053.
