# PFR_NP-S2 — PREFLIGHT REPORT, Sprint NP-S2
*P0 · SERIAL · Architect. The first use of the v0.0 checklist (`ops\WO-Q_ARO_implementation_ladder.md`) and of the state machine's P0 gate. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-31.*

**Why this exists at all, stated plainly:** NP-S2 was opened by issuing WO-P directly, with no preflight and no G1. That violates the machine's first rule on its first use, and the violation is the Architect's. This report is the correction, run before any WO-P work is claimed.

---

## 1. Data

| Check | Result |
|---|---|
| scope name for R6 collection exists and is registered | **NO — blocker B1.** `xauusd_m5_vantage` exists for NP-S1's historical M5 bars. NP-S2 collects *forward* real ticks; its scope is unnamed. |
| dataset ingested with manifest, row count recorded | **N/A this sprint** — collection is the deliverable, not a precondition. |
| timestamps int64 ns UTC, source timezone stated | **CARRIED RULE.** Source is broker server time (UTC+3, DST-clean over NP-S1's span); conversion happens at the adapter boundary. Must be re-verified for forward data, since a DST transition *will* occur in a 3–6 month window. **See B2.** |

## 2. Registration constants

**Not applicable — NP-S2 has no judging phase.** No registrations, no verdict, no burn. Cost model, lineage, family string and trial count are all N/A this sprint. `configs/venues.yaml` already holds `xauusd_retail_median` and `xauusd_retail_h07`; neither is touched.

*Worth recording in itself: a sprint whose preflight has an entire section marked N/A is a sprint with no scientific exposure, and its risk profile is operational rather than evidentiary.*

## 3. Capability

| Check | Result |
|---|---|
| the engine can express the trade rule the hypothesis needs | **NO — and that is the sprint.** `ExecutionSpec.stop_offset` / `target_offset` are hypothesis-level scalars. WO-P exists to fix exactly this. Not a blocker; it is the deliverable. |
| every specification needed is complete enough to reimplement (NP-D-012) | **YES for WO-P** — written under NP-D-012, with spec-insufficiency named as a DEVQ trigger against the Architect. **UNKNOWN for the NPSU→RecordStore migration and the windows.json↔WindowLedger check**, which have no written specification at all. **Blocker B3.** |

## 4. Boundaries

**Frozen — must not be edited:** Execution Plan §4 and §5 (frozen by the NP-S1 GO) · Constitution (ratified) · NP-ADR-008 with Appendices A and B (ratified; corrections append only) · the NP-S1 verdict, burn and all 19 registrations · `ivf/reports/IVF_NP-S1_AC6.md` §§0–6 · `NOTE-NP-002` §§1–6.

**Open findings carried in:** F-23 (Book A mockup vs Auto-Adopt — bites at NP-S8) · F-24 consequence (Architecture docx twin stale) · queued non-frozen doc fixes (Architecture §2 and V&V §3.4 "nine steps"; Architecture §3.2 adapter path) · attribution corrections on four ops/DEVQ artifacts · the unratified design stack (ARO ADR, organization/roles ADR, repository autonomy, this state machine, detector-fingerprint ADR).

## 5. Blockers

- **B1 · The R6 scope is unnamed.** Collection cannot produce a manifest that anything can later cite. *Fix: name it at G1 (e.g. `xauusd_ticks_vantage_r6`) and record what it covers.*
- **B2 · A DST transition will occur inside a 3–6 month collection window.** NP-S1's span was DST-clean and its timezone handling was verified only against that. Forward data crosses at least one transition — and NP-S1 already cost a full bug-and-revert cycle on exactly this class of error. *Fix: state the conversion rule at G1 and require the ingestion to prove it across a transition.*
- **B3 · Two of the three build tracks have no written specification.** The migration and the consistency check exist as one-line deliverables in §6. Under NP-D-012 that is insufficient. *Fix: write them before G1, or narrow NP-S2 to WO-P alone.*

## 6. Owner decisions that belong at G1, batched

NP-S1 spent four separate Owner round-trips because decidable things surfaced mid-flight. These are the ones visible now:

1. **Lab unpause** (scoped) — required before any collection; on no critical path for WO-P.
2. **The R6 scope name** (B1).
3. **The withheld-OOS designation *policy*.** §6 requires the designation to be typed *before collection completes* — a date nobody can know at G1. **But the policy can be sealed now** ("the final N% by time is withheld, designated when collection reaches X"), leaving only a mechanical act later. *This converts a mid-sprint judgment into a rule — the §12 lever applied for the first time.*
4. **Scope of NP-S2** — all three build tracks, or WO-P alone (B3).

## 7. RESULT

**RESULT: NOT GREEN — three blockers (B1, B2, B3), four decisions for G1.**

**None of them blocks WO-P itself.** WO-P is Kernel-side: it needs no scope, no data, no unpause, and its specification is complete. The honest reading: **WO-P may proceed now as a P2 lane; the collection track may not open until G1 clears B1–B3.**

**Recommendation:** seal G1 with the four decisions above. If that is inconvenient, rule the narrowing instead — *NP-S2 is WO-P only* — and the collection track becomes NP-S3's problem, with a clean preflight of its own.

---
*Anchor: **the first preflight found three blockers and four decisions in a sprint that had already started — which is precisely the argument for running it before starting.***
