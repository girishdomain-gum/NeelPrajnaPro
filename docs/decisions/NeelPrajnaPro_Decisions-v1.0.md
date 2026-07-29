# NeelPrajnaPro — Decisions v1.0
*The ONE decisions document: every architectural decision of the programme, consolidated. Originals (full ADR texts) preserved in docs\archive\gen1\adr\ as provenance. New decisions are appended here as new sections (NP-D-###) and the version bumps; never a second file.*
*v1.0 · 2026-07-29 · Author: Fable (Architect)*

## Part 1 — Generation-1 decisions (QRF-ADR-001..011, condensed faithfully; full texts in archive)

**QRF-ADR-001 · Documentation policy — unique responsibility.** Exactly one artifact answers each question; when two documents answer the same question, neither is trusted. *(Superseded in form by the Owner's one-doc-per-thing law of 2026-07-29 — but this ADR is its direct ancestor and its principle is unchanged.)*

**QRF-ADR-002 · Append-only hash-chained ledger as sole store of truth.** All knowledge is immutable Records in a hash-chained JSONL journal; corrections are new amendment records; derived indexes are rebuildable, never authoritative. Knowledge that can be quietly revised is not knowledge.

**QRF-ADR-003 · Manifest pattern for bulk data.** Heavy series live in write-once Parquet; the journal stores a manifest (path, counts, sha256, schema, ts range); reads verify hash first. The ledger stays small yet remains the root of trust for gigabytes.

**QRF-ADR-004 · Domain-blind Kernel with mechanical firewall.** `qrf/kernel/**` contains no trading vocabulary and may not import `qrf/trading/**` — enforced by a CI test, not convention. The honesty rules are the scientific method; domain-blindness makes them harder to bend on a disappointing week.

**QRF-ADR-005 · Two-speed simulation; the verdict engine is custom.** vectorbt screens fast and is type-barred from verdicts; judgments run on a ~500-line audited event engine (bid/ask fills, in-engine costs). Screener runs auto-bump the trial ledger.

**QRF-ADR-006 · Trust through independent reproduction (IVF).** No sprint closes on its own tests: `ivf/` (never importing qrf) reproduces key results from file outputs, must catch one planted bug per sprint, and a check RED twice freezes forward work. Internal consistency is not correctness.

**QRF-ADR-007 · Generated state.** The status/handover file is generated from the ledger; only two sections are hand-maintained. A stale dashboard is worse than none — it is confidently wrong. *(In this repo the live handover is EXECUTION_PLAN §0.)*

**QRF-ADR-008 · Multi-AI coordination protocol.** Role-based team coordinated through files, not chat: ARCH / DEVQ / REV / NOTE ids; inbox OPEN→CLOSED; Developer writes only in its lanes; instructions are self-contained. No AI is indispensable; all state is external.

**QRF-ADR-009a · Research program track.** Deep questions raised mid-sprint go to the RQ backlog, never into redesigns: freeze the interfaces, not the thinking. *(Backlog now lives in docs\research\ one-doc.)*

**QRF-ADR-009b · Visual evidence as a standing verification layer.** Chart-anchored claims get captioned MT5-rendered captures with provenance lines; pictures illustrate, numbers decide; a capture contradicting the numbers freezes the claim. HC without a human is just another VC.

**QRF-ADR-010a · Observational neutrality (permanent principle).** "Richer data changes what QRF can see, never how QRF decides what is true." Any argument that a data source's richness deserves a lower evidence bar is rejected by citing this decision.

**QRF-ADR-010b · Supervised autopilot — phased automation with a drilled human gate.** Phases A (tireless CI) → B (autonomous Developer) → C (orchestrated cycle + Owner packet), each Owner-gated and reversible. Permanently human: Go/No-Go phrases, VIRGIN acts, changes to ivf/CI/this decision, audits of the automation. Binding constraints R-1..R-7 including Owner drills (planted defects the Owner must catch — a miss pauses autopilot), Developer-write-refusal on ivf/** and workflows, scratch-datastore default, typed-phrase journal grants, no-web least-privilege agents, budget caps, heartbeat-or-STALE plumbing. *The sentence it enforces: automation does not remove judgment; it hides where judgment stopped happening — so every mitigation makes stopped judgment LOUD.*

**QRF-ADR-011 · Trial accounting — registration spends the attempt.** Every registration appends one trial_count in the same flow; multiplicity deflation sees every attempt a family ever made at judging time. Closed the last unpaid channel by which the framework could flatter itself (smc.fvg now prices at α≈5e-5).

**Rejected Concepts Register (R-001..R-017).** Seventeen ideas declined or deferred through the Three Gates (scientific necessity · architectural uniqueness · implementation independence), each with origin and failing gate preserved — rejection is knowledge. Full table in archive; standing procedure: every new rejection gets its row in the same write window.

## Part 2 — NeelPrajnaPro decisions (2026-07-29, all Owner-ratified; sources: JOURNAL J-001..J-007)

**NP-D-001 · Integration, not duplication.** NeelPrajna becomes the second concept family inside the real Kernel; the bespoke research stack is retired from evidentiary service. *(Basis: Volume IV; REV F-3.)*

**NP-D-002 · Knowledge Publication Boundary (constitutional).** QRF publishes what it knows, never how it knows; only Battery-verdicted, versioned, dated belief releases cross Contract v2; no rolling/unsealed statistic ever crosses; execution feedback enters as observations only.

**NP-D-003 · Auto-Adopt: DISABLE pending hysteresis.** `InpADV_AutoAdopt = NONE`; re-enable per strategy only after ECF survival + Battery-passed pre-registered hypothesis + explicit Owner arming. The machine may recommend; only the Owner arms.

**NP-D-004 · Cost model `xauusd_retail_h07`.** One authoritative venues.yaml entry reconciling $0.47/oz with the 26-tick figure; frozen once cited; changes require a new name.

**NP-D-005 · H-07 claim form E2 (arrangement), null N2.** Definition-trap rule applied; dual registration (prediction judged NP-S1 by the certified Battery; existence judged when N2 nulls certify); both attempts priced at birth.

**NP-D-006 · Namespacing.** QRF-ADR-### / NP-D-### / ARCH-### / ARCH-NP-### — adopted after the Architect committed and tallied the ARCH-011 collision.

**NP-D-007 · Single home + pause.** F:\NeelPrajnaPro authoritative for everything; F:\QRF frozen archive; F:\NeelPrajna paused, execution-only, scoped unpause per need.

**NP-D-008 · Vision ruling.** The two-organ destination architecture is this cycle's TARGET, evidence-gated box by box (VISION.md); the Chief Scientist wall is permanent.

**NP-D-009 · One document per thing.** Versions live inside documents and in git; folders hold one current master; superseded versions auto-archive; a second changelog anywhere is a finding.

## Change Record
- v1.0 (2026-07-29): created per the one-doc-per-folder ruling; consolidates 13 Gen-1 ADRs + rejected register + 9 NP decisions.
