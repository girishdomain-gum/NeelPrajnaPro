# PRE-RATIFICATION REVIEW — NP-ADR H-07 §5 v1.1
*Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30. Evidence: repository at `cdbb71c`, read directly. Nothing in this review edits a normative or frozen document.*

---

## 1. Executive Summary

The ADR's **definition content is sound and fully evidence-supported** — every parameter, event, SHA and span in §3 was re-verified against source this pass. Its **provenance chain, span, and divergence table hold up completely.**

However, verification against the *code* (not the documents) surfaced **seven mandatory issues**, five of which were invisible from the documentation alone. Two are serious: the proposed **lineage name violates the repository's actual naming convention**, and the **α-budget will silently fail to apply** unless one `family` string is pinned across all registrations. A third is conceptually important: **the Battery does not judge the 324 trades at all** — it re-simulates from bars and events over walk-forward TEST ranges only, so the sprint's "same population" premise needs restating before AC-4 can mean anything.

**Verdict: Ready for Chief Scientist review. NOT ready for Owner ratification** until the seven items in §3 are folded in. All seven are text or decision changes; none requires redesign.

## 2. Verified Items ✅

| Item | Method | Result |
|---|---|---|
| Export identity, 324 rows, FAIL verdict | direct read of parquet + `Stage4_EvidenceReport_H07.json` | **Confirmed** |
| All three SHA-256 hashes | recomputed this session | **Match** (`1a0b5d9f…a6c0`, `a9b75aeb…d2ff`, `0f242e2f…0133`) |
| v1.1 parameters (M5/300s, k=3, tol 30t, min_pen 5t, reclose 2, 200-bar window, max/min level) | source read of `np_feature_service.py` + hard-coded call site | **Confirmed** |
| Absence of REVERSAL_CONFIRMED | source read | **Confirmed** |
| v1.0 fidelity to `T3_SweepFVGGate.mqh` | Developer's committed source read (`309843e`) + workflow | **Confirmed** (still second-hand for this session; see Risks) |
| Designated span + UTC conversion | tick-file bounds, settlement-break/half-day evidence | **Confirmed** |
| All commit references | `.git` refs and logs | **All resolve**: `cdbb71c`, `ee4d4e1`, `458bbac`, `482c1a1`, `309843e`, `15259ce`, `f6e66a9`, `b610ffd` |
| All file references | directory listings | **All exist** (one absence is itself a finding — see M5) |
| Five-gate verdict claim | JSON criteria keys | **Confirmed**: B1 pass; B3, B4, B5, B6, B7 all `pass:false` |
| "Registration spends the attempt" = 1 trial per registration | `trials.py` `bump()` contract | **Confirmed** |
| Historical records unchanged; no frozen document modified | diff review of this session's writes | **Confirmed** — all writes are new `ops\` files |

## 3. Outstanding Mandatory Issues — MUST FIX BEFORE RATIFICATION

**M1 · Lineage name violates the repository convention.** *(Contradicts my own ADR §5 Q5.)*
Evidence: `configs/hypotheses/h004_dow_monday_drift_v2.yaml` → `lineage: h004_dow_monday_drift_v2`; `datastore/bulk/verdict_trades.h001_fvg_follow_through`. Lineages are **flat dotless slugs**, and the version is carried *in the slug* (`_v2` — exact precedent). Dotted names are used for *detectors* (`seasonality.calendar@0.1.0`) and *events* (`seasonality.dow.mon`), not lineages. A dotted lineage would also produce the bulk key `verdict_trades.neelprajna.liquidity_sweep.v1_1`.
**Fix:** lineage **`h007_np_liquidity_sweep_v1_1`** (matches Execution Plan §4's own `h007_np_liquidity_sweep.yaml` naming plus the h004 `_v2` precedent); detector instrument id **`neelprajna.liquidity_sweep@1.1.0`**; event types `neelprajna.liquidity_sweep.pool_formed` / `.sweep`.

**M2 · The α-budget will silently not apply unless one `family` string is pinned.**
Evidence: `deflation.py::_trial_belongs_to_family` matches on the declared `family` with prefix-segment logic. Two sibling families (`xauusd/neelprajna.liquidity_sweep` vs `xauusd/neelprajna.other`) do **not** match each other, so per-detector families would give each hypothesis its own budget — the 19-trial deflation would evaporate.
**Fix:** every neelprajna registration — H-07's two **and all 17 counted-only entries** — declares the identical family string, recommended **`xauusd/neelprajna`**. Without this, "α-budget 0.05 across the family" is documentation only.

**M3 · The Battery has EIGHT steps, not nine.**
Evidence: `battery.py` module docstring enumerates 1–8; **ARCH-006 §3 (Gen-1 normative) enumerates the identical 1–8**. "Nine steps" appears in Architecture §2, Execution Plan §4/AC-4 and V&V §3.4 with no source; it most likely derives from Blueprint §5 **arrow (9)**, which `battery.py` cites in its header.
**Fix:** the ADR states eight and the comparison maps against the eight as implemented. Execution Plan §4 is frozen and must **not** be edited; the correction lives in the ADR and the sealed interpretation table. Architecture §2 and V&V §3.4 are *not* frozen and should be corrected in the next write window (documentation defect, recorded against the Architect).

**M4 · "B1–B7" is six reported criteria, not seven.**
Evidence: the report's `criteria` keys are B1, B3, B4, B5, B6, B7. **B2 (OOS discipline) is not a reported gate** — it is a procedural property of the run ("OOS = final 40%, evaluated once").
**Fix:** AC-4's mapping is **8 Battery steps ↔ 6 reported criteria + B2 as a procedure**, sealed in the YAML before the run.

**M5 · Cost model `xauusd_retail_h07` does not exist.**
Evidence: `configs/venues.yaml` contains only `xauusd_retail_median`. ARCH-006 §1 and V&V §2.3: registration validates `cost_model_ref` exists — **a registration citing an unknown cost model is a hard error**. Architecture §3.4 requires the entry to exist "before any NeelPrajna verdict is requested."
**Fix + a decision the Owner must make:** the bespoke stack charged 26 ticks = **$0.26/oz**; QRF's existing retail median is **$0.47/oz**. These are not the same cost world. Whichever is sealed, it must be sealed *before* the run, because a divergence caused by cost assumptions would otherwise be misread as an instrument divergence.

**M6 · The Battery does not judge the 324 trades.**
Evidence: `battery.py` step 5 — the injected audited simulator regenerates trades from `bars` + `events`, **per fold, over its TEST index range only**, dropping and counting trades that cannot open and close inside the block. The 324 are the *bespoke* output; the Battery will produce its own, materially fewer, trade set.
**Fix:** restate deliverable 4's premise honestly — *same window, same detector definition, same trade rule; different instrument, therefore a different judged trade set by construction.* Pre-register the expected n and the `min_n` threshold accordingly, and seal this in AC-4's interpretation table so a smaller n is not later read as a defect.

**M7 · No M5 dataset, scope, or ingestion path exists yet.**
Evidence: every `datastore/bulk` dataset is `xauusd_h1_*`; scopes in use are `xauusd_h1`. Architecture §3.2 states the data path is `NP_Trades_*` / `NPSU_Trades_*` CSVs through `mt5_csv.py` — but the evidenced source is the **Stage-2 tick parquet** aggregated to M5 mid bars, which is a different path entirely.
**Fix:** name the scope (e.g. `xauusd_m5_vantage`), define the ingestion (ticks → M5 mid bars → BulkStore with manifest), and record that Architecture §3.2's stated adapter path does not apply to this population.

## 4. Deferred Items — MAY BE DEFERRED

- **D1** `qrf/trading/concepts/neelprajna/` has no `__init__.py` (not yet a package) — Developer creates it in deliverable 1.
- **D2** `scripts/gen_state.py` targets the Gen-1 `AI_PROJECT_STATE.md`, absent here. Needs a ruling (retire, or re-point at Execution Plan §0). WO-A scope; blocks nothing.
- **D3** Research Console mockup scope chip reads "XAUUSD·M5·London·trend" — corroborating evidence that M5 was visible pre-sprint. Recorded; the proposed standing rule (alignment passes check parameter consistency, not only sprint pointers) can ride with the next amendment.
- **D4** Architecture docx twin still stale vs its md (F-24 consequence).
- **D5** Trial count 19 vs J-029's 18 — already in the ADR as an explicit Owner question; needs a ruling, not a fix.

## 5. Risks

- **R1 (high) · Cost-model confound.** If `xauusd_retail_h07` is sealed at $0.47 while the bespoke run used $0.26, the Battery will almost certainly FAIL and AC-4's "divergence" will be attributable to costs, not to instruments. Sealing the interpretation *before* the run is what prevents a false lesson.
- **R2 (medium) · Trade-set construction.** M6's fold-TEST-only restriction plus embargo could push n below `min_n`, yielding INSUFFICIENT. That is an honest result, but it must be pre-registered as an expected outcome so it is not read as failure of the sprint.
- **R3 (low) · External SHA pinning.** The three hashes pin files in `F:\NeelPrajna`, outside this repository and outside CI. Nothing automatically detects if they change — precisely the gap the queued fingerprint ADR closes.
- **R4 (low) · v1.0 fidelity is second-hand for this session.** I verified the Python side from source; the MQL5 side rests on the Developer's committed read. Adequate (it *is* a committed record), worth one line in the ADR stating the attribution.

## 6. Recommendation

**Ready for Chief Scientist review — NOT ready for Owner ratification.**

Rationale: the ADR's science is sound, but M1, M2 and M5 would each produce a *silently wrong* registration if ratified as written — a mis-keyed lineage, an α-budget that does not bind, and a registration that hard-errors on an unknown cost model. M3, M4 and M6 would corrupt AC-4, the sprint's most valuable deliverable, by mapping it against a step count, a gate count, and a population premise that do not match the instrument.

**Path to ratification-ready, in order:** (1) I fold M1–M7 into the ADR — text and decision changes only, one pass; (2) Chief Scientist reviews the corrected ADR; (3) the Owner rules the two embedded decisions — the cost-model figure (M5) and the trial count (D5/19-vs-18) — and ratifies. The Developer resumes immediately after.

---
*Anchor: **the documents said nine steps, seven gates, and one population; the code says eight, six, and none of them — verification is reading the thing, not the description of the thing.***
