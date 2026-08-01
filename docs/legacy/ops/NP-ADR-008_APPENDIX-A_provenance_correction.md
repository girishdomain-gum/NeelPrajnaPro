# NP-ADR-008 · APPENDIX A — Provenance correction (Gate 7 / Gate 8) · **ACCEPTED 2026-07-30**

> **OWNER ACCEPTANCE (verbatim, 2026-07-30):** *"ok"* — typed in response to the §7.2 clarification request in A.4. Recorded exactly as typed; no fuller wording is attributed. Effect: Appendix A is accepted as a Constitution §7.2 clarification; **§5 v1.0 remains frozen and unedited**; DEVQ-NP-003 and DEVQ-NP-004 are both answered; NP-S1 proceeds to the 17 counted-only registrations, the AC-4 interpretation seal carrying the Gate 7/Gate 8 correction, and then the Battery run.

*Appended correction under P5 (history is append-only; corrections are new records pointing at old ones). **Nothing in the ratified ADR body is edited.** Proposed as a Constitution **§7.2 clarification** — Architect drafts → Owner reads → Owner OK — because no requirement, constant, definition, or decision changes; only a provenance narrative is corrected. Chief Scientist notice recommended (its three statements are strengthened, not weakened). Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Origin:** DEVQ-NP-004 (Developer, commit `bf6fd65`), raised from a roster pointer, then verified by the Developer against git history and by this session against the MQL5 source directly.

---

## A.1 What was verified, and by whom

| Fact | Evidence | Verified by |
|---|---|---|
| `T3_SweepFVGGate.mqh` header reads **"TRIGGER T3 — 1H Liquidity Sweep + FVG (was Gate 8)"** | the file's own header | Developer, and independently this session |
| T3's v2.0 change log states the **old Gate 7 (`LiquiditySweepGate.mqh`) EQH/EQL pool engine is absorbed** into T3 as an alternative sweep-anchor source | same header | both |
| **`LiquiditySweepGate.mqh` is deleted** — "no G7_*/EG_G7_* symbols exist anymore" | same header | both |
| Neither `LiquiditySweepGate.mqh` nor `SweepFVG1HGate.mqh` has ever existed in this repo's git history | git history search | Developer |
| `kb.json` H-07 = *"Equal-high/low sweep + reclose reverses (stop-hunt)"*, exec `LiquiditySweepGate.mqh → np_feature_service.py`; H-08 = *"1H sweep → MSS → FVG tap sequence (NY open)"*, exec `SweepFVG1HGate.mqh` | `F:\NeelPrajna\knowledge_base\kb.json` | Architect |
| T3's **default** anchor source is `T3_ANCHOR_CANDLE` ("v1 behaviour, default"), **not** the pool engine | same header | this session |
| kb.json's H-07 evidence seq 0 records `timeframe_s 300, pivot_k 3, pool_tol_ticks 30, min_pen_ticks 5, reclose_window_bars 2` | kb.json | Architect |

## A.2 The correction

**§5 v1.0 is a hybrid, and documents neither hypothesis cleanly.**

- Its **POOL_FORMED** layer — average-of-member-pivots level, `pool_lookback`, `pool_pivot_len`, `pool_min_touches`, `pool_tol` — is **Gate 7's engine as absorbed into T3**. That lineage is genuinely H-07's.
- Its **REVERSAL_CONFIRMED / MSS** stage, the H1/M1 anchor-exec architecture, and the gap-through exclusion are **T3's own mandatory machinery — Gate 8, i.e. H-08.** H-07 never had an MSS stage.
- Worse for the original framing: the pool path is **not T3's default**; `T3_ANCHOR_CANDLE` is. §5 v1.0 documented an *optional, non-default* path of a *different hypothesis's* gate, wearing H-07's absorbed pool engine.

**Consequently the "seven divergences" in the annex are largely cross-hypothesis, not cross-version.** Divergence 6 (no REVERSAL_CONFIRMED) is not a defect in the Python at all: it is H-08 machinery that H-07 never specified. Divergences 1–2 (H1/M1, ATR tolerance) are T3's anchor settings. Only divergences 3–4 (pool level max/min vs average; 200-bar window vs 500 H1 bars) are genuine MQL5-vs-Python differences *within* H-07's own pool engine, and 5 and 7 remain as recorded.

**The evidenced Python implements H-07 as H-07 was always defined** — kb.json's own text is *"Equal-high/low sweep + reclose reverses (stop-hunt)"*, which is POOL → SWEEP with a reclose and no MSS. Its recorded parameters match v1.1 exactly, from a third independent artifact.

**One consequence that cannot be undone:** `LiquiditySweepGate.mqh` is deleted and predates this repository's git history. **H-07's MQL5 original is unrecoverable.** What survives of it is kb.json's hypothesis text, the absorbed pool engine inside T3, and the Python. **The v1.1 detector is therefore the best surviving expression of H-07, not a degraded version of a richer gate.**

## A.3 What this changes — and what it does not

**Unchanged (nothing ratified is disturbed):** §5 v1.1's definition, every binding constant (lineage, detector id, family, scope, cost model, window), both Owner decisions ($0.41/oz; 19 trials, p < 0.00263), the E2 restatement, the two sealed registrations, §5 v1.0's frozen text. **No re-registration is required** — the registrations describe v1.1 and the H-07 population correctly, and Chief Scientist statement 3 remains true as written.

**Strengthened:** the E2 restatement to POOL→SWEEP was approved as a pragmatic match to the implementation; it is now known to be **H-07's original hypothesis restated**. And the three non-equivalence statements matter *more*, because they separate two genuinely different hypotheses rather than two versions of one.

**Corrected in reading (not in text):** ADR §2 claim 1 stands — v1.0 does faithfully document T3 — but must be read with A.2: **T3 is Gate 8's gate.** ADR §2.1 statement 3's "the original T3/MSS detector" is **H-08**, and judging it belongs to H-08's own future registration with fresh out-of-sample evidence.

**AC-4 consequence, and the reason this lands before the run:** the comparison report interprets divergences. Interpreting them as "one hypothesis, two versions" rather than "two hypotheses" would misstate the sprint's most valuable output. **This correction must be sealed into AC-4's interpretation table before `EvidenceBattery.run()`.**

## A.4 Rulings requested

**DEVQ-NP-003 (roster) — RESOLVED, no Owner ruling required.** The roster exists: `F:\NeelPrajna\knowledge_base\kb.json`, 18 records H-01…H-18 with ids, hypothesis text, lineage tags, executable definitions, status and evidence. **The 17 = H-01…H-06, H-08…H-18.** Option A is available with genuine provenance; Option B's placeholder is unnecessary and should not be used. **The forward-reference is not a conflict:** Execution Plan §4 deliverable 6 counts the 17 as *attempts* (QRF-ADR-011 — the cost of an attempt is paid at conception); §7's NP-S3 ruling decides *which are migrated and with what n-floors*. Counting is not selecting. Register all 17 as counted-only entries under family `xauusd/neelprajna`, using the kb.json ids and hypothesis text as lineage provenance.

**DEVQ-NP-004 (provenance) — this appendix is the answer**, pending Owner OK on the §7.2 clarification.

**Owner wording (type one):**
- **OK:** *"Appendix A to NP-ADR-008 is accepted as a §7.2 clarification. §5 v1.0 remains frozen and unedited. NP-S1 proceeds: register the 17 from the kb.json roster, seal AC-4's interpretation table with the Gate 7/Gate 8 correction, then run the Battery."*
- **RETURN:** *"Not accepted — [reason]."*

---
*Anchor: **the gate we sealed was the neighbour's; the hypothesis was never wrong, only its paperwork — and the file that could have settled it was deleted before this repository began.***
