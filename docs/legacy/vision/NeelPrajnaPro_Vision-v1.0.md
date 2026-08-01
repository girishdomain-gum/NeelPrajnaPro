# VISION — the destination architecture
*Version 1.0 · 2026-07-29 · Ruled by the Owner: "this is what we want to develop this time." Source diagram: NeelPrajna_Architecture_Diagrams_CORRECTED (reference shelf). One doc; history lives in git and in the Change Record at the bottom.*

## The picture we are building toward

```
                    MARKET (Tick / M1 / M5 / H1 / D1)
                              │
                    OBSERVATION ENGINE
        single source of observations — both organs see the same reality
                    │                           │
   CORE — QRF BRAIN (domain-blind)     BOOK A — NEELPRAJNA RUNTIME (plug-in)
   Scientific Memory                    Live Execution
   Pattern Learning                     Risk Management
   Knowledge Graph                      Order Handling
   Statistics & Confidence              Dashboard
   Pattern Evolution                    Position Management
   EvidenceBattery / WindowLedger       Live Decisions
                    │                           │
   KNOWLEDGE + EVIDENCE                 ORDERS / EXECUTION FEEDBACK
   validated beliefs, confidence,       fed back to Core as
   applicability                        OBSERVATIONS
                    └───────────┬───────────────┘
              CONTINUOUS COMMUNICATION — event-driven,
                  nobody waits, nobody blocks
```

**The load-bearing wall (Chief Scientist Principle, unchanged forever):** *QRF never trades. NeelPrajna never learns on its own.* Neither organ can perform the other's function.

## Every box, in black and white: what it really is, and which sprint delivers it

**Row numbers and box names below are identical to §A.1 of the docs\architecture\ master, which is the canonical spine.** The docs\execution_plan\ master names the same boxes against the same sprints. A divergence between any of the three is a finding.

| # | Architecture box | What it concretely is | Exists today? | Delivered by |
|---|---|---|---|---|
| 1 | EvidenceBattery / WindowLedger | The judge and the reserves — already drilled, frozen | ✅ | Gen-1 (done) |
| 2 | Scientific Memory | The append-only RecordStore + verdicts + belief records | ✅ | Gen-1; NP records begin **NP-S1** |
| 3 | Observation Engine | Detectors + adapters + EventFrames on the shared ledger — one reality, both organs | ✅ Kernel side | NP feed **NP-S1**; widened **NP-S2**, **NP-S3** |
| 4 | Statistics & Confidence | Battery statistics + belief layer (verdict-sealed figures only) | ✅ core | enriched every verdict; further at **NP-S6** |
| 5 | Execution feedback → Core | Fills/outcomes as observations into the Performance Store | ⚠ CSV exports exist | **NP-S2** (R6 pipeline + RecordStore migration) |
| 6 | Pattern Learning | Candidate discovery (screener/observatory) + ECF establishment of phenomena | ⚠ partial | **NP-S3** (first NP existence judgments; ECF nulls certify on the Gen-2 track) |
| 7 | Knowledge + Evidence → runtime | Versioned belief releases across Contract v2 (§ boundary) | ❌ | **NP-S5** — Contract v2 goes live (built, not merely ruled) |
| 8 | Continuous Communication | **Event-driven releases and observations** — "nobody waits, nobody blocks" means asynchronous events, not tick-streaming; a release is an event, freshness is its date | ❌ | **NP-S5** |
| 9 | Knowledge Graph | The beliefs document + atlas: per-phenomenon stances, scoped, linked | ❌ | **NP-S6** (+ Gen-2 S7 synthesis) |
| 10 | Pattern Evolution | Hypothesis refinement as new sealed registrations, versioned, priced | ❌ | **NP-S9+** (Phase 5; machine-proposed only after Gate A) |
| 11 | Surface — Research Console (Core side) | Browser-based five-lens view onto the Kernel: OBSERVE / KNOWLEDGE / DISCOVER / EVIDENCE / GOVERNANCE + CYCLE | ❌ | **NP-S7** (spec v1.3) |
| 12 | Surface — Book A Dashboard (Runtime side) | The on-chart panel — Live Advisor card, Observation Space, LIVE and VIRT UNIV deep views | ✅ basic; depth ❌ | **NP-S8** (spec v1.4/v1.5) |

**On rows 11–12:** the two surfaces are *views onto* the organs, not organs themselves — which is why they appear nowhere in the two-organ diagram above (only "Dashboard" shows, inside the Book A organ). They are enumerated so every sprint maps to a row and no delivered work sits outside the box column.

**Honesty line, so this vision can never fool us:** the two-organ picture is the *destination of this development cycle*; today one organ (the Brain) is fully real, the other (the Runtime) is fully real, and the nervous system between them is the work. Re-tiered by this ruling: Pattern Learning, Knowledge Graph, Pattern Evolution, and Continuous Communication move from ASPIRATIONAL to **TARGET — evidence-gated**: each becomes real only through sealed sprints, in the order above, and no box may be claimed "done" without its verdict-bearing artifact. The one thing that stays out of every envelope: what the real account trades changes only by the Owner's typed hand.

## Change Record
- **v1.0 (2026-07-30, alignment correction):** the delivery table was written when Execution Plan v1.0 ended at NP-S4, and described rows 7–10 as *rulings at the NP-S4 boundary*. Execution Plan v2.0 schedules them as real sprints. Table replaced with the canonical 12-row form matching §A.1 of the architecture master exactly; rows 11–12 added for the two surfaces, which had no delivery row anywhere. Part of finding F-24 (Architect), corrected across all three documents in one pass.
- v1.0 (2026-07-29): created from the Owner's vision ruling; supersedes the ASPIRATIONAL-tier framing of Architecture §8 for the four boxes named above (Architecture updated same day).
