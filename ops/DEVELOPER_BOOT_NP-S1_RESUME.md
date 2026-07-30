# DEVELOPER BOOT — Sprint NP-S1 RESUME (post-ratification)
*Written 2026-07-30 after Owner ratification of NP-ADR-008. Supersedes `ops\DEVELOPER_BOOT_NP-S1.md` for all work from this point: that artifact's blocking first obligation is **discharged**, and its `NP_Trades_*` name-hint was wrong. Architect role · session: Opus 5, claude.ai interface, filesystem connector.*

---

## What changed since the original boot

The blocking first obligation is **complete**. The H-07 export was identified (`F:\NeelPrajna\Validation\Stage4\h07_trades.parquet`, 324 rows), its span resolved and **Owner-confirmed**, and the §5 parameter trigger fired and was resolved through the ADR process. **DEVQ-NP-001 and DEVQ-NP-002 are CLOSED.** `NP-ADR-008` is ratified: **§5 v1.1 is sealed; §5 v1.0 remains frozen and unedited.**

## Read these, in this order

1. `ops\NP-ADR-H07_definition_v1.1_draft_v2.0.md` — **sealed as NP-ADR-008. This is your normative detector definition.**
2. `docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md` **§0** (handover, binding constants) and **§4** (your sealed instruction — frozen text, unchanged)
3. `ops\DEVQ-01_NP-S1.md` and `ops\H07_evidenced_definition_annex_NP-S1.md` — the full evidence trail
4. `ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md` — the seven documentation-vs-code corrections you must honour
5. `docs\roles\` master §2.4 — your mandate and your shall-nots
6. `docs\vv_plan\` master §§1–3 — the assurance levels your work must satisfy

## Binding constants — a registration missing any of these is wrong by construction

| | |
|---|---|
| lineage | `h007_np_liquidity_sweep_v1_1` |
| detector / instrument | `neelprajna.liquidity_sweep@1.1.0` |
| event types | `neelprajna.liquidity_sweep.pool_formed` · `.sweep` |
| **family** | **`xauusd/neelprajna` — identical in ALL 19 registrations** |
| scope | `xauusd_m5_vantage` |
| cost model | `xauusd_retail_h07` (already in `configs/venues.yaml`, $0.41/oz) |
| window | UTC half-open `[2026-04-20T22:00:00Z, 2026-07-10T14:33:00Z)`, TRAINING |
| α | base 0.05, **19 family trials → effective p < 0.00263** |

**Why the family string is load-bearing:** `deflation.py::_trial_belongs_to_family` matches on the declared `family` with prefix-segment logic, and sibling families do **not** match each other. A per-detector family string would give every hypothesis its own budget and the α-budget would silently not bind.

## THE ORDERING TRAP — read this twice

`deflate_family` totals `trial_count` records **at judgment time**. If the 17 counted-only registrations (deliverable 6) are written *after* the Battery run, the deflation will see 2 trials instead of 19 and the effective α will be **0.025 instead of 0.00263 — a bar ten times too loose.**

**Therefore deliverable 6 executes BEFORE deliverable 4.** Correct order:

1. **Scope + ingestion.** Register scope `xauusd_m5_vantage`. Build M5 mid bars from the Stage-2 tick parquet (`(bid+ask)/2`, 300 s buckets, clean ticks only) → BulkStore with manifest. Timestamps int64 **ns UTC** — the source is broker EEST (UTC+3), convert at the adapter boundary. *Note: Architecture §3.2's `NP_Trades_*`/`mt5_csv.py` path does **not** apply to this population; that divergence is recorded.*
2. **Detector + certification.** `qrf/trading/concepts/neelprajna/liquidity_sweep.py` implementing **v1.1's two events only**. Add the missing `__init__.py`. Then `planted_cases()` — all planted frauds caught, silence on clean controls — **before any real run** (AC-1). Anti-hindsight property test per ADR §3's knowability paragraph (AC-2).
3. **Window record.** TRAINING designation over the UTC interval above.
4. **All 19 registrations**, every one citing the family string. Two sealed for H-07 (prediction + E2 existence), 17 counted-only.
5. **Seal the AC-4 mapping** in the YAML **before** the run: **8 Battery steps ↔ 6 reported bespoke criteria + B2 as a procedure**, with every agree/disagree interpretation written down first.
6. **One Battery run.** Verdict + burn, atomic (AC-3).
7. **Comparison report** (AC-4). 8. **IVF** re-derives (AC-6).

## Corrections you must honour (documentation vs implementation, all verified against code)

- **The Battery has EIGHT pipeline steps, not nine.** `battery.py` docstring and ARCH-006 §3 agree. "Nine" in Architecture §2, Execution Plan §4/AC-4 and V&V §3.4 has no source. **§4 is frozen — do not edit it**; map against the eight as implemented.
- **The bespoke report has SIX reported criteria, not seven.** Keys are B1, B3, B4, B5, B6, B7 — **B2 is procedural**, not a gate. Recorded outcome: **B1 pass (194/130); B3–B7 fail — a five-gate FAIL**, not "FAIL on cost sensitivity."
- **The Battery does not judge the 324 trades.** It re-simulates from bars + events, **per fold, over TEST index ranges only**, dropping trades that cannot open and close inside their block. Same window, same definition, same trade rule — **different judged trade set by construction**, and the judged n will be materially smaller than 324. Set `min_n` accordingly and pre-register this so a small n reads as arithmetic, not defect.
- **`embargo_bars ≥ hold_bars + 1`** is re-checked by the Battery and refuses the run otherwise (DEVQ-011).

## The three statements that must survive into every artifact (ADR §2.1, verbatim into `outcome_interpretations`)

1. E2-v1.1 is not equivalent to the original v1.0 hypothesis.
2. It is a new hypothesis bound to the documented v1.1 detector lineage.
3. Any future judgment of the original T3/MSS detector requires a separate implementation and fresh out-of-sample evidence.

**No verdict under v1.1 validates, corroborates, or speaks to the historical T3 gate.**

## Non-goals (violations are findings)

No live-execution / TradeManager / NPSU changes · no hypotheses beyond H-07 (the 17 registration-only entries excepted) · no console work · no edits to `ivf/**`, CI workflows, ledger internals, or any normative document · **no edit to Execution Plan §4 or §5, which are frozen by the GO.**

## DEVQ protocol

Raise a numbered DEVQ and **stop that line of work** at any ambiguity, boundary case, or suspected specification error — before implementing, not after. **Exception: do not open a new DEVQ on the H-07 definition question family.** That decision history is single-threaded through `ops\DEVQ-01_NP-S1.md`; append evidence there instead. Silence binds no one; an assumption in place of an answer is a finding. Refusing an instruction that conflicts with a rule is a duty, not insubordination.

## Done

AC-1 through AC-6. **AC-4 in particular: the comparison report must name every divergence with its cause. Agreement is corroboration; divergence is this sprint's most valuable output. Either outcome satisfies AC-4. Results are never averaged; the drilled instrument's verdict stands.**

Work on the existing worktree branch `claude/neelprajnapro-sprint-np-s1-a8171d` (pull mainline first). Session log at every stop. Commit and push after every commit.
