# DEVQ-01 — Sprint NP-S1 · §5 parameter trigger fired (definitional divergence)
*WORKING RECORD ONLY — not a normative document. Written 2026-07-30 on Owner approval ("Handover Files: Approved"). Session: Developer-analog via claude.ai chat with Filesystem connector (read/analysis + these two approved writes only; no code, no commits, no registrations — the implementation sprint runs in Claude Code per the boot prompt).*
*[WORKTREE COPY — verbatim from mainline `ops\DEVQ-01_NP-S1.md`, placed here 2026-07-30 so the sprint session can read the authoritative state from its own disk; the mainline file is the original and the two converge in git.]*

---

## 1. The question, as raised

Execution Plan §5 (frozen): *"if the 324-trade export was produced under non-default gate parameters, halt and raise a DEVQ. The definition re-seals as v1.1 with the evidenced values; it is never silently adjusted."*

During the blocking first obligation (resolve the market-time span of the H-07 324-trade export), the evidence showed the export was produced by the Python Stage 2→3→4 pipeline under a **materially different detector definition** than §5 v1.0 — not merely different parameter values. Work on the registration line was stopped per the DEVQ protocol; nothing registered, ran, or burned.

## 2. Identification of the export (resolved before the DEVQ)

- **The H-07 324-trade export is `F:\NeelPrajna\Validation\Stage4\h07_trades.parquet`** — exactly 324 rows; matches `Stage4_EvidenceReport_H07.json` (`trades_total: 324`, generated 2026-07-10T18:19:13+00:00 by `np_probability_engine.py` v1.0; verdict **FAIL**, consistent with §4's recorded bespoke verdict).
- SHA-256 of the population file: `0f242e2f6a89836fdb9e60e3e7b2b803b04688af7e59c01fd707fd8ac8de0133`
- Naming discrepancy stated openly: the boot prompt pointed at `NP_Trades_*`. Those are bridge backtest CSVs from runs dated **2026-07-27** — seventeen days after the Stage 4 report — and cannot be its source; none holds 324 trades. Identification of the parquet is unambiguous by count, provenance chain (Stage 2 ticks → Stage 3 features → Stage 4 report, all generated 2026-07-10), and verdict match.

## 3. Resolved market-time span — **OWNER CONFIRMED 2026-07-30**

- **Timezone basis:** broker server time (Vantage Markets MT5, UTC+3 across this span, NY-close aligned), stored as epoch integers — not true UTC. Evidence: every trading day's ticks run 01:00:01 → ~23:58 in the file's own clock (daily 00:00–01:00 maintenance break; zero trades in hour 0); Friday trade entries stamped as late as 23:10, impossible in genuine UTC for XAUUSD.
- **Covered market time:** first tick Tue **2026-04-21 01:00:01** server → last tick Fri **2026-07-10 17:32:59** server (≈ 2026-04-20 22:00:00 → 2026-07-10 14:33:00 UTC). 60 trading-day files (59 BACKFILL + 1 LIVE tail), ~80.7 days span per the Stage 3 report.
- **Trade entries within it:** first 2026-04-21 08:55, last 2026-07-10 06:05 (server); 324 trades, 160 BUY / 164 SELL; every entry aligned to a 300-second bar boundary.
- **Gaps:** eleven weekend gaps (all normal Fri→Mon closures; no missing trading weeks), the daily one-hour maintenance break, one intraday >300s tick gap on the 2026-07-10 backfill (flagged in the Stage 2 report, PASS overall). No missing weekdays.

**Owner ruling (2026-07-30), key text:** *"Span confirmed. For NP-S1, the H-07 evidence population is designated as covering: Vantage Server Time (UTC+3): 2026-04-21 01:00:00 → 2026-07-10 17:33:00. Equivalent UTC: 2026-04-20 22:00:00 → 2026-07-10 14:33:00. This span is now the designated market-time coverage for the 324-trade H-07 population unless future evidence demonstrates a factual error."*

Under J-030 this completes the scope-designated TRAINING window: the span above is the market time the designation **burns**. In-sample; corroborative, never confirmatory.

## 4. The evidence behind the DEVQ (summary — full detail in the annex)

The Stage 3 report header states the export's feature engine ran at **TF=300s, k=3, pool_tol=30.0t fixed, min_pen=5.0t**. Reading `np_feature_service.py` and `np_probability_engine.py` end to end shows **seven divergences** from §5 v1.0, of which only the first two are parameter swaps; the rest are event-definition, mathematical-definition, causal-model, and provenance changes — including the complete absence of REVERSAL_CONFIRMED (§5's third event) from the evidenced chain. See `ops\H07_evidenced_definition_annex_NP-S1.md` for the full evidenced definition and divergence table.

## 5. Review (Chief Scientist, relayed by Owner 2026-07-30)

Concurred that the divergence is **definitional, not parametric**; item 6 (removal of REVERSAL_CONFIRMED) assessed as *"a fundamental causal model change… no longer observing the same phenomenon… a different hypothesis."* Recommended: §5 v1.0 frozen forever; §5 v1.1 as *"the first authoritative documentation of the detector definition embodied by the evidence"* (not a correction of v1.0); plus a broader ADR on immutable detector identities, machine-readable manifests, and definition fingerprints with Battery preflight enforcement. Deliberately did not confirm the span — correctly deferring that typed power to the Owner.

## 6. OWNER RULING — DEVQ-01 RESOLVED (2026-07-30)

Verbatim key content:
- *"§5 v1.0 remains permanently frozen and is not to be edited."*
- *"The evidenced detector definition shall be documented as §5 v1.1 through the ADR process."*
- *"The 324-trade evidence population shall reference §5 v1.1, not §5 v1.0."*
- *"No historical record is to be rewritten."*
- **Registration remains blocked until:** the Architect authors the v1.1 ADR · the ADR is ratified · the detector definition is re-sealed · registrations reference the re-sealed definition. *"No workaround or implicit substitution is authorized."*
- Handover files approved (this record and the annex; working records only, non-normative).
- Fingerprint/identity ADR: to be included **as a recommendation to the Architect**, evaluated during architecture review; **not** part of the current re-seal.

## 7. Consequences flagged for the v1.1 ADR (Architect to rule, Owner to ratify — not decided here)

1. **E2 claim wording.** §5 v1.0 defines E2's testable content as *"does REVERSAL_CONFIRMED follow SWEEP beyond chance timing?"* The evidenced population contains **no REVERSAL_CONFIRMED events**; E2 as worded cannot be judged on this population. The ADR must restate E2 against v1.1's actual event chain (POOL→SWEEP, entry next bar) or rule how the existence claim is handled.
2. **α-budget pricing.** If v1.1 is "a different hypothesis" (Chief Scientist's assessment), the ADR must rule how it counts against the neelprajna family α-budget (0.05): one trial or two. Trial count moves the per-claim bar for the whole family (currently p < 0.0028 at 18 trials).
3. **Detector implementation target.** §4 deliverable 1 says the detector implements "exactly §5's events." Once registrations cite v1.1, the NP-S1 detector must implement **v1.1's** events, or the Battery would judge a different phenomenon than the one that produced the population.

## 8. Status

**RESOLVED — awaiting execution of the ruling.** Blocked chain: Architect v1.1 ADR → Owner ratification → re-seal → registrations cite v1.1 → Claude Code session implements per boot prompt. Nothing has registered, run, or burned. These two ops files are uncommitted on disk; per the F-22 standing rule, the next commit must stage `docs` **and** `ops` together.

---
*Append below this line only.*

## Addendum A · 2026-07-30 · Independent verification — corroboration recorded (interim); reconciliation instruction

**Source:** a separate Claude Code session in `F:\NeelPrajnaPro` ("NeelPrajnaPro Sprint NP-S1 boot") ran a six-agent verification workflow (`np-s1-h07-verify`) over the same evidence, without access to this record's reasoning. Its interim report, and the Chief Scientist's assessment of it (relayed by the Owner 2026-07-30), are recorded here so the corroboration lives in the decision record, not in chat.

**Independently converged conclusions (all material points):** identification of `h07_trades.parquet` as the unique 324-row export · rejection of the `NP_Trades_*` filename hint (unrelated NPSU backtests) · broker server-time (Vantage EEST/UTC+3) interpretation, established via gold's daily settlement break · the market-time span (its table reports first/last **trade entries**, 2026-04-21 08:55 → 2026-07-10 06:05 server — compatible with, and contained in, the Owner-designated full coverage window of §3; the designation correctly burns the coverage the detector consumed, not merely the entry moments) · exact M5 grid alignment · the definitional detector divergence (M5 single-TF; fixed 30-tick tolerance; max/min pool level; no REVERSAL_CONFIRMED/MSS stage) · the §5 governance halt · and the same discipline: nothing registered, no Battery run, no window burned.

**Genuinely new evidence contributed:** the verifying session read **`T3_SweepFVGGate.mqh` directly** and confirmed that **§5 v1.0 is a faithful seal of the original MQL5 gate** — H1/M1 architecture, `PoolTol = 0.15×ATR14`, pool level = average of member pivots, mandatory MSS = REVERSAL_CONFIRMED stage, all matching. This closes the remaining provenance question: the divergence exists **entirely within the Python lineage**; v1.0 is not at fault. Chief Scientist recommendation, Owner-endorsed: the v1.1 ADR should explicitly record this provenance chain.

**Reconciliation instruction (Owner/Chief Scientist direction, 2026-07-30):** the span is Owner-confirmed and DEVQ-01 is resolved; these decisions on disk are the authoritative programme state. **No new DEVQ is to be opened for this already-resolved question.** The verifying session must read this record and the annex before filing anything, and append its completed verification output (workflow results, agent findings, any artifacts) below this addendum as additional corroborating evidence — a single decision history, never a parallel one.

*Status at this addendum: the verification workflow was still running when its interim report was captured; its final output is expected to be appended here by the session that produces or receives it.*

## Addendum B · 2026-07-30 · Developer session's DEVQ-NP-001/002 found on branch `claude/neelprajnapro-sprint-np-s1-a8171d`; answered on the record; new evidence adopted

**What happened, honestly.** The Developer session (worktree `.claude\worktrees\neelprajnapro-sprint-np-s1-a8171d`, branched from T-036) committed at 309843e a correct halt with two DEVQs in `docs\coordination\inbox\OPEN\`: **DEVQ-NP-001** (the same definitional divergence, independently derived with a 10-row parameter table and its own direct read of `T3_SweepFVGGate.mqh`) and **DEVQ-NP-002** (window-scope and timezone-basis questions). It could not see this record: the worktree branched before these ops files existed, and they were **uncommitted** — invisible to any branch or clone. That is the F-22 species recurring at the record level, against the Architect-analog session for leaving decision records uncommitted while parallel sessions ran. Standing consequence: **decision records are committed the same day they are approved; an uncommitted decision is not yet a decision the repository can defend.**

**Actions taken (Architect, same day):** replies written into both DEVQ files on the branch — DEVQ-NP-001 ANSWERED (core already Owner-ruled; its A/B/C sprint-level options adopted as evidence into the pending NP-ADR; its hold on deliverable 6 endorsed); DEVQ-NP-002 ANSWERED (Q1 by the Owner's span confirmation = its option (ii); Q2 by Architect ruling: ledger window recorded in true UTC as half-open **[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)** with broker-EEST provenance noted). Verbatim copies of this record and the annex placed into the worktree's `ops\` so the session reads the authoritative state from its own disk. OPEN→CLOSED moves left to the Developer session (its lane).

**New evidence adopted from the session's DEVQs (attribution: developer, claude-code, commit 309843e):**
1. **Direct T3 source verification on the branch** — v1.0's fidelity to the MQL5 gate is now confirmed by a committed record, upgrading Addendum A's interim-report attribution to source-verified.
2. **Divergence #5 sharpened:** the evidenced code reads `h,l,c` only and never the bar **open**, so §5 v1.0's "opens inside the defended side" condition and gap-through exclusion are *unenforceable* in that code path, not merely unimplemented.
3. **325 sweeps → 324 trades** (exactly one degenerate-geometry drop; risk < 5 ticks) — essentially every sweep trades, underscoring that the population carries no reversal-selection content.
4. **`knowledge_base/kb.json` independently attests "XAUUSD M5"** — a third in-repo witness to the M5 basis.
5. **Timezone evidence upgraded:** settlement break at 00:00 stored = 17:00 New York; Friday 23:55 closes; half-day truncations 2026-06-19 and 2026-07-03 at 19:55 stored (13:00 ET early close); zoneinfo confirms no DST transition inside the span. Adopted as the timezone evidence of record, superseding the maintenance-break inference in §3 as the primary argument (conclusions identical).

**New contingency recorded for the NP-ADR (from DEVQ-NP-001 Option A × DEVQ-NP-002 Q1):** if the ADR selects a fresh §5-v1.0-faithful population, that detector's pool_lookback pre-roll (up to 500 H1 bars ≈ 21 days, cap 2000 ≈ 83 days) would consume market time **earlier than the designated start**. Under P8, a **supplementary Owner designation** covering the pre-roll span is a hard precondition of any such run. Written into the NP-ADR question set (annex §7 item 5, added in the worktree copies and to be mirrored here at the ADR draft).

**Sprint-level open question set for the v1.1 ADR now reads (consolidated):** (1) E2 restatement · (2) α-budget pricing (one trial or two) · (3) detector implementation target (v1.1 events) · (4) anti-repaint restated in v1.1 terms · **(5) which population deliverable 4 judges — the Developer's Options A / B-as-ruled / C — with the pre-roll supplementary-designation precondition if A.**
