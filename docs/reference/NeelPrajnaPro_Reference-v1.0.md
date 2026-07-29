# NeelPrajnaPro — Reference Handbook v1.0
*The ONE reference document: the working vocabulary and frameworks of the programme in one place. Full original texts (Glossary, SMC Concept Glossary, ECF, MML, Architecture Map, Execution Process Guide, the Gen-1 user manual docx) preserved in docs\archive\gen1\reference\. Reference material is an aid, never authority (QRF-ADR-001): where this handbook and a ratified canonical doc differ, the canonical doc wins and the difference is a finding.*
*v1.0 · 2026-07-29*

## 1. The vocabulary that matters (working glossary)
**Record** — immutable, hash-chained assertion that something happened; corrections point, never replace. **Scientific Object** — versioned concept; every change evidence-gated. **EventFrame** — a detector's output table (namespaced event_type, knowability-honest timestamps). **Window** — market time designated TRAINING / EXPLORATION / VIRGIN; burned on judging use; reserved by market time, not by file. **Verdict** — the Battery's signed tri-state ruling (PASS/FAIL/INSUFFICIENT · ESTABLISHED/NOT ESTABLISHED/INSUFFICIENT); nothing overrides it. **Trial** — a counted attempt, spent at registration. **Family** — the multiplicity-accounting unit (e.g. smc.fvg, neelprajna). **Belief release** — versioned, dated, verdict-sealed knowledge crossing Contract v2. **Placebo** — claim-matched null (e.g. random-timing) every prediction claim must beat. **Drill** — a planted fraud the verifier must catch before judging anything real. **IVF** — independent verification framework re-deriving results from normative texts only. **HC/VC** — human check / verification check; HC without a human is just another VC. **DEVQ** — Developer question; silence binds no one. **Pool / Sweep / MSS** — see the sealed H-07 definition (EXECUTION_PLAN §3).

## 2. The ECF in one panel (normative source: SCIENTIFIC_MODEL.md §5)
Claim forms: **E1 Rate** (occurs ≠ expected rate; rotation nulls N1) · **E2 Arrangement** (clustering/duration/transitions structured beyond chance; block-resampling nulls N2) · **E3 Association** (X predicts Y; model surrogates N3). **Definition-trap rule:** an occurrence rate purchased by the definition is never evidence — the testable content of percentile-anchored phenomena lives in the arrangement. Verdicts tri-state; establishment licenses mechanism/prediction investigation, never a trading conclusion.

## 3. The MML in one panel (normative source: SCIENTIFIC_MODEL.md §6)
W_up = H − max(O,C) · B = |C−O| · W_lo = min(O,C) − L · R = H − L; normalize by R; descriptor MD-UBL (three deciles, top-to-bottom); R=0 → reserved MD-000, excluded from shape statistics, emitted explicitly. Merge operator = timeframe aggregation; merge-revealed geometry = descriptor(merged) ∈ S while every constituent ∉ S. The descriptor describes; only the evidence establishes.

## 4. The architecture map in one panel (normative source: ARCHITECTURE.md / the one docx)
Market data → adapters (mt5_csv, OBS-4) → detectors (concept families: classical · seasonality · smc · **neelprajna**) → EventFrames → Battery (nine steps) → Verdict + burn → BeliefLayer → belief releases → Contract v2 → runtime (paused lab at F:\NeelPrajna). Write authority closed list: store.append · Battery · Screener trial bumps · belief.update(Verdict). Kernel firewall: kernel never imports trading.

## 5. Process quick card (normative source: EXECUTION_PLAN + ROLES_AND_COMMUNICATION)
Sprint rhythm: ARCH → Developer (fresh session, worktree, DEVQs) → IVF (drill first) → HC → REV → Owner Go/No-Go → GO + retro → EXECUTION_PLAN §0 rewrite. Ops channel: scripts in ops\, logs out, Architect reads logs. Findings format: claimed / true / species / standing rule — immediately, factually, against a name, including one's own.

## Change Record
- v1.0 (2026-07-29): created per one-doc-per-folder ruling; condensed from the archived Gen-1 reference set; every panel names its normative source.
