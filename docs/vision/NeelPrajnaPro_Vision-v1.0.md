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

| Diagram box | What it concretely is | Exists today? | Delivered by |
|---|---|---|---|
| Observation Engine | Detectors + adapters + EventFrames on the shared ledger — one reality, both organs | ✅ Kernel side (Gen-1) | NP-side feed: **NP-S1** (H-07 detector), widened each family sprint |
| EvidenceBattery / WindowLedger | The judge and the reserves — already drilled, frozen | ✅ | Gen-1 (done) |
| Scientific Memory | The append-only RecordStore + verdicts + belief records | ✅ | Gen-1 (done); NP records begin **NP-S1** |
| Statistics & Confidence | Battery statistics + belief layer (verdict-sealed figures only) | ✅ core | Enriched every verdict |
| Pattern Learning | Candidate discovery (screener/observatory) + ECF establishment of phenomena | ⚠ partial | ECF certification (Gen-2 S3–S4 track); first NP existence judgment after nulls certify (**NP-S3** window) |
| Knowledge Graph | The beliefs document + atlas: per-phenomenon stances, scoped, linked | ❌ | **NP-S3/S4** + Gen-2 S7 synthesis |
| Pattern Evolution | Hypothesis refinement as new sealed registrations, versioned, priced | ❌ | Wave 2 (post **NP-S4** gate; machine-proposed only after Gate A) |
| Knowledge + Evidence → runtime | Versioned belief releases across Contract v2 (§ boundary) | ❌ | Consumption design ruled at **NP-S4**; arming anything real stays permanently human |
| Execution feedback → Core | Fills/outcomes as observations into the Performance Store | ⚠ CSV exports exist | Formalized **NP-S2** (R6 pipeline) |
| Continuous Communication | **Event-driven releases and observations** — "nobody waits, nobody blocks" means asynchronous events, not tick-streaming; a release is an event, freshness is its date | ❌ | Contract v2 implementation, **NP-S4** ruling |

**Honesty line, so this vision can never fool us:** the two-organ picture is the *destination of this development cycle*; today one organ (the Brain) is fully real, the other (the Runtime) is fully real, and the nervous system between them is the work. Re-tiered by this ruling: Pattern Learning, Knowledge Graph, Pattern Evolution, and Continuous Communication move from ASPIRATIONAL to **TARGET — evidence-gated**: each becomes real only through sealed sprints, in the order above, and no box may be claimed "done" without its verdict-bearing artifact. The one thing that stays out of every envelope: what the real account trades changes only by the Owner's typed hand.

## Change Record
- v1.0 (2026-07-29): created from the Owner's vision ruling; supersedes the ASPIRATIONAL-tier framing of Architecture §8 for the four boxes named above (Architecture updated same day).
