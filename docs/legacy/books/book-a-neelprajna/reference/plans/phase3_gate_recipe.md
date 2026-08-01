# Phase 3 — Gate migration recipe (Sessions 1–13)

Session-0 deliverable. Template so every gate migration (Sessions 1–13) is
mechanical, repeatable, and reviewable against one reference. Pairs with the
uncommitted drafts `Gates/GateContext.mqh` and `Gates/GateBase.mqh`.

Status: **proposal, uncommitted, awaiting owner review.** No gate file was
touched in Session 0.

---

## Step-1 — Dependency inventory (the table that drove the contract)

Grounded in the **current** code (post-Phase-1 restructure), not ADR-001 §1's
pre-refactor description. `CFG_*` (Config) and `LOG_*`/`CFG_DebugMode`
(EALogger) are L1 infrastructure — downward-legal, they STAY as direct calls and
are omitted from the "upward calls" column. Every gate `#include`s exactly
`Core/Config.mqh` + `Core/EALogger.mqh` today.

| Gate | Kind | Consumed inputs (beyond Config/Logger) | Upward / cross-module calls | Published outputs |
|---|---|---|---|---|
| B1 Nexis | bias | bars (InpB1_TF hi/lo/close/time); `_Point/_Digits` | — none — | `EG_B1_Buy/Sell/Enabled/Compute` |
| B2 MTF Candle | bias | bars (multi-TF closed candles); symbol specs | — none — | `EG_B2_Buy/Sell/Enabled/Compute` |
| B3 Key Level | bias | bars; **live spread `ASK−BID`** (1); **`MM_ATRPoints(resolvedTF,14)`** (1) | **`MM_ATRPoints` ×1** (SL buffer) + live spread read | `EG_B3_Buy/Sell/Enabled/Compute` |
| B4 SMC | bias | bars; `TimeCurrent` (setup expiry); symbol | — none — | `EG_B4_Buy/Sell/Enabled/Compute` |
| B6 RegChannel | bias | bars; `TimeCurrent`; `CFG_CLR_*` | — none — | `EG_B6_Buy/Sell/Enabled/Compute` |
| T1 Pattern | trigger | bars; `TimeCurrent` (last-fire) | — none — | `EG_T1_Buy/Sell/Enabled/Compute`, `EG_T1_SL/TP/HasLevels`, `EG_T1_VariantTag`, `EG_T1_LastFireTime`; `T1_MarkConsumed` |
| T2 AutoFibo | trigger | bars; symbol | — none — | `EG_T2_*` + `SL/TP/HasLevels`; `T2_MarkConsumed` |
| T3 Sweep+FVG | trigger | bars; `TimeCurrent` (draw/expiry); **`MM_ATRPoints(execTF,14)` + `(anchorTF,14)`** (2) | **`MM_ATRPoints` ×2** (tol + SL buffer) | `EG_T3_*` + `SL/TP/HasLevels`; `T3_MarkConsumed` |
| T4 TrendLines | **hybrid** | bars; **`MM_ATRPoints(tf,14)`** (2); `CFG_RRRatio`; `T4_JoinsChain()` (mode) | **`MM_ATRPoints` ×2** (SL buffer, 2 modes) | `EG_T4_Buy/Sell` (bias *or* pulse), `EG_T4_SL/TP/HasLevels` (breakout modes only); `T4_MarkConsumed` |
| T5 Topography | trigger | bars (heavy); `TimeCurrent`; `CFG_RRRatio` | — none — | `EG_T5_*` + `SL/TP/HasLevels`; `T5_MarkConsumed` |
| T7 Market Metrics | trigger | bars; `TimeCurrent`; `CFG_CLR_*` | — none — | `EG_T7_*` + `SL/TP/HasLevels`; `T7_MarkConsumed` |
| T8 CMH | trigger | bars; `TimeCurrent`; symbol (heavy) | — none — | `EG_T8_*` + `SL/TP/HasLevels`; `T8_MarkConsumed` |
| T9 CCC Hidden | trigger | bars; `TimeCurrent` | — none — | `EG_T9_*` + `SL/TP/HasLevels`; `T9_MarkConsumed` |

### What the inventory proved (and disproved)

1. **The only genuine upward domain call is `MM_ATRPoints`** — 5 call sites in
   **3 gates**: B3 ×1, T3 ×2, T4 ×2. That is the entire coupling GateContext
   must sever. Everything else a gate touches is either a downward L1 call
   (`CFG_*`, `LOG_*`) or a symbol-global infra primitive (`i*`/`CopyRates`,
   `SymbolInfo*`, `TimeCurrent`) that is legal to keep in-gate.

2. **No gate calls `TM_` at all.** Every `TM_*` token in a gate file is a
   comment. ADR-001 §1 and the tech-debt row *"T3/T4/T5 call TM_ directly"* are
   **stale vs current code.** What those rows actually describe is that T3/T4/T5
   (and T1/T2/T7/T8/T9) *produce* `EG_Tx_SL/TP/HasLevels` globals that
   **EntryGates** — not the gate — feeds to `TM_OpenTradeWithLevels`. → Action:
   reconcile the ADR/tech-debt text; the "double-effort three" are heavy because
   of their *structural-level production + `MM_ATRPoints`*, not a TM call.

3. **No account fields, no session fields.** No gate reads `AccountInfo*`/
   `ACCOUNT_*`, and no gate reads a session API. So GateContext carries neither
   (both would be speculative). The `BLK_SESSION` blocker still has **no producer
   in code** (tech-debt SESSION row) — Phase-3 decision, deferred to an ADR
   amendment, **not** patched by inventing a session field here.

4. **GateContext ended up leaner than ADR-001 §2.4's illustrative list.** It
   carries symbol specs, live spread (bid/ask), `nowServer`, and an `AtrPoints`
   accessor — exactly the union of the "consumed inputs" column. No precomputed
   rate cache (gates fetch heterogeneous TFs; hoisting them would recreate the
   coupling — see the GateContext header).

---

## The contract (recap of `Gates/GateBase.mqh`)

- `GateResult { fired; dir; hasLevels; sl; tp; note }` — one uniform verdict.
  Bias gates leave `hasLevels=false`, `sl=tp=0` (uniformity over purity — owner).
- `Evaluate(const GateContext &ctx, const int dir) → GateResult` — direction is a
  parameter, not a context field.
- `Enabled()/SetEnabled()`, `PublishState(EAState&)`, identity (`code`, `name`,
  `kind`, `magicOffset`), `MarkConsumed` (triggers), `joinsBiasChain` (T4 hybrid).
- **Polymorphism = function-pointer descriptor table.** Each gate keeps its free
  functions and adds a thin adapter + `Descriptor()`, then self-registers. No
  class rewrite (huge diff, live-money risk), no god-switch (scatter). Justified
  in the GateBase header; compile-harnessed 0/0 including the fn-pointer path.

---

## Migration recipe — one gate, one commit

Legend: **[all]** every gate · **[atr]** B3/T3/T4 only · **[trig]** triggers only.

1. **[all]** Add `#include "../GateBase.mqh"` after the gate's existing
   `Core/` includes. (Pulls GateContext → MoneyManager → Config, and StateHub;
   include guards make the duplication with EntryGates' graph a no-op.)

2. **[all]** Thread the context into the legacy evaluator. Change
   `void Bx_Evaluate()` → `void Bx_Evaluate(const GateContext &ctx)`. Update the
   call site in `EntryGates.EG_EvaluateAllGates()`:
   `Bx_Evaluate();` → `Bx_Evaluate(ctx);`. (In **B1's session only**, first add
   `GateContext ctx = GateContext_Build();` at the top of `EG_EvaluateAllGates`,
   before the bias block — one line, reused by every later gate's call site.)

3. **[atr]** Reroute the upward call **in place**:
   `MM_ATRPoints(tf, 14)` → `ctx.AtrPoints(tf, 14)`. Nothing else in the signal
   core changes. `ctx.AtrPoints` forwards to `MM_ATRPoints`, so the numbers are
   **byte-identical** → tester unchanged.

4. **[all]** Append the contract adapter block before `#endif` (mechanical; the
   signal core is untouched):

   ```mql5
   //--- Phase 3 contract adapter ------------------------------------
   bool Bx_IsEnabled()             { return EG_Bx_Enabled; }
   // Bx_SetEnabled already exists in most gates — reuse; else add the
   // same guarded body (set EG_Bx_Enabled, clear EG_Bx_Buy/Sell). Reuse
   // binds cleanly because GateSetEnabledFn is void(*)(bool) (corrected
   // from (const bool) per the B1 finding — MQL5 fn-ptr binding is strict).

   GateResult Bx_EvaluateCtx(const GateContext &ctx, const int dir)
     {
      // Legacy path already ran this tick (EntryGates calls Bx_Evaluate(ctx)
      // above) and populated EG_Bx_*; read them through into the result so
      // values are identical to the baseline.
      GateResult r = GateResult_None(dir);
      r.fired = (dir == GATE_DIR_BUY) ? EG_Bx_Buy : EG_Bx_Sell;
      // [trig] add levels:
      // r.hasLevels = EG_Tx_HasLevels; r.sl = EG_Tx_SL; r.tp = EG_Tx_TP;
      return r;
     }

   void Bx_PublishState(EAState &s)   // writes this gate's ONE state row
     {
      // s.bias[i] (bias) or s.trig[i] (trigger) — mirror the row
      // SH_PublishGates writes today. Inert until Session 14 (see below).
     }

   SGateDescriptor Bx_Descriptor()
     {
      return GateDescriptor_Make(
         "Bx", "Display Name", GATE_BIAS /*or GATE_TRIGGER*/, -1 /*or magic*/,
         Bx_Init, Bx_Deinit, Bx_IsEnabled, Bx_SetEnabled,
         Bx_EvaluateCtx, Bx_PublishState,
         NULL /*[trig]: Tx_MarkConsumed*/,
         GateContract_JoinsChain_Always /*bias*/ /* Never (trig) / T4_JoinsChain (T4) */);
     }
   ```

5. **[all]** Self-register at the end of `Bx_Init()` (on success):
   `GateRegistry_Register(Bx_Descriptor());`.

6. **[all]** `tools/compile.bat` → **0 errors** (warnings clean preferred).

7. **[all]** Baseline check per the batch rule below.

8. **[all]** Commit: one gate. Message: what + why +
   `baseline: identical` (expected for every Phase-3 gate).

> **Dual-state invariant (why this stays byte-identical).** Through Sessions
> 1–13 the legacy path stays authoritative: `Bx_Evaluate(ctx)` still writes the
> `EG_Bx_*` globals, EntryGates still walks its explicit trigger list and still
> reads `EG_Tx_SL/TP` to call `TM_OpenTradeWithLevels`. The registry is
> *populated but never walked*; `Bx_PublishState` is *defined but not called*
> (`SH_PublishGates` remains the writer). Nothing new is on the decision path, so
> the tester deal list cannot move. **Session 14** flips EntryGates to (a) walk
> `g_gateRegistry` instead of the hand-written calls and (b) consume
> `GateResult.sl/tp` instead of `EG_Tx_SL/TP` — the first commit that *replaces*
> rather than *shadows* the legacy path, and the one to scrutinise hardest.

---

## Special cases

### T4 — the hybrid (bias in one mode, trigger in two)
`InpT4_Mode == T4_MODE_STRUCTURAL_BIAS` makes T4 join the bias AND-chain; the
breakout modes make it a levels-carrying trigger. Encode this exactly as today:
`kind = GATE_TRIGGER` (its StateHub home is `trig[]`), and pass
`joinsBiasChain = T4_JoinsChain` (the existing function) into the descriptor. The
Session-14 walker uses `joinsBiasChain()` to decide bias-agree vs trigger-walk
membership — the same `T4_JoinsChain()` test EntryGates and StateHubPublish use
now. `EG_T4_HasLevels` stays false in bias mode, so `Bx_EvaluateCtx` naturally
returns `hasLevels=false` there. No logic change.

### T3 / T4 / T5 — the "double-effort three": what their "TM_ call" becomes
There is **no** TM_ call to rewrite (see inventory finding #2). Concretely:
- **T3:** two `MM_ATRPoints` sites (`t3_anchorTF` tolerance, `t3_execTF` SL
  buffer) → `ctx.AtrPoints(...)` (step 3). Its `EG_T3_SL/TP/HasLevels` production
  is untouched; it surfaces through `GateResult` in step 4 and is consumed by
  EntryGates→`TM_OpenTradeWithLevels` exactly as before.
- **T4:** two `MM_ATRPoints` sites (SL buffer, both breakout modes) →
  `ctx.AtrPoints(...)`; plus the hybrid handling above.
- **T5:** **no `MM_ATRPoints`** — its TP is `CFG_RRRatio`-derived from a
  structural SL. Its "double effort" is purely the *size / care* of packing
  `EG_T5_SL/TP/HasLevels` into `GateResult` and re-verifying byte-identical
  output on a large gate, **not** an upward-call reroute. It is a pure wrap.

So for all three, "what the TM_ call becomes in context terms" = *(a)* the
`MM_ATRPoints` fetches (T3, T4 only) become `ctx.AtrPoints`, and *(b)* the
structural `EG_Tx_SL/TP` they already compute become `GateResult{hasLevels,sl,tp}`
— a relocation of where the levels live, with **zero recomputation**.

### B3 — the only live-spread consumer
`SymbolInfoDouble(_Symbol,SYMBOL_ASK) − ...SYMBOL_BID` → `ctx.spreadPrice`
(RECOMMENDED, not required for decoupling — it is a market read, not an upward
call). Do it in B3's session so the spread-adjusted RR becomes injectable/
testable; `ctx.spreadPrice` equals the live value, so baseline is unchanged.
B3 also carries the sole bias-gate `MM_ATRPoints` (step 3 applies).

### T1 — extra published fields
`EG_T1_VariantTag` / `EG_T1_LastFireTime` have no home in `GateResult` (they are
attribution, not a fire verdict). Leave them as `EG_T1_*` globals for now;
`SH_PublishGates` already surfaces them to `g_state.trig[0]`. Revisit only if a
later phase needs them off the globals.

---

## Exit-check — template-strict diffs + three checkpoint tester runs (revised owner ruling)

**Revised owner ruling — supersedes the earlier "Strategy Tester every 3–4
gates" schedule.** The routine batch-of-3 tester runs are **dropped**. Tester
validation is consolidated into **three checkpoints — after Session 13, after
Session 14, and after Session 15.** The compensating control for removing the
per-batch runs is strict per-migration diff discipline (below): a migration diff
that departs from the recipe template forfeits the "no tester until the
checkpoint" allowance and forces an immediate tester run.

**Every commit (all 13):**
- `tools/compile.bat` → 0 errors. (0 warnings preferred; note in commit if not.)
- On-chart smoke sanity is not required per-commit in Phase 3 (no chart-event
  path changes until Session 14); it IS required at Session 14.

**Compensating control — template-strict diffs (every migration commit):**
- Each gate's diff must match the migration recipe template (steps 1–5)
  **line-for-line in the gate's signal core.** The only signal-core changes the
  template permits are the mechanical ones it prescribes: the `#include` (step
  1), the `ctx` threading (step 2), and — **[atr]** gates only — the
  `MM_ATRPoints(...)` → `ctx.AtrPoints(...)` reroute (step 3). The adapter block,
  descriptor, and self-register (steps 4–5) are strictly additive and sit outside
  the signal core.
- **Any out-of-template diff line in a gate's signal core triggers an immediate
  tester run for that gate's batch** (grouping table below) — do not defer to the
  next checkpoint. Reconcile the diff back to template-identical, or, if the
  change is genuinely intentional and correct, obtain owner sign-off, before
  proceeding.

**The three checkpoints (run `tools/backtest.bat` vs `tools/report_baseline`):**

| Checkpoint | After | Scope validated | Pass condition |
|---|---|---|---|
| 1 | Session 13 | all 13 gate migrations complete (registry populated, legacy path still authoritative — shadow only) | deal list **byte-identical** to frozen baseline |
| 2 | Session 14 | EntryGates flipped to the registry walk + consuming `GateResult.sl/tp` (first commit that replaces, not shadows) | deal list **byte-identical** to frozen baseline |
| 3 | Session 15 | scope per that session's brief (2% rule into pipeline / Phase 3c) | deal list **byte-identical** to frozen baseline |

- **A checkpoint passes** only if the tester deal list is **byte-identical** to
  the frozen baseline (Phase 3 rule: identical, no documented-diff allowance).
- **If a checkpoint diff is NOT identical:** stop, do **not** proceed to the next
  session. Bisect per-gate across the sessions since the last passing checkpoint
  (revert to the relevant commit, test each gate's commit in turn) to isolate the
  offending change, fix, re-verify identical, then resume.

**Batch grouping (retained only for the compensating-control tester run):** these
groups no longer drive a routine tester schedule; they define the unit re-tested
when an out-of-template signal-core diff is detected.

| Batch | Gates | Notes |
|---|---|---|
| 1 | B1, B2, B6 | pure wraps, lowest risk |
| 2 | T1, T7, T8 | pure-wrap triggers |
| 3 | T9, B3, T2 | B3 = first `MM_ATRPoints` + spread reroute |
| 4 | B4, T5 | T5 large |
| 5 | T4, T3 | the two `MM_ATRPoints` triggers + T4 hybrid |

**Tester determinism guards (standing risk, overhaul.md):** pinned model/date
range, cached history, never compare across a history re-download. A checkpoint
(or compensating) run that "fails" identical-check must first be re-run to rule
out tester nondeterminism before bisecting code.

---

## Migration order (given) + rationale

`B1, B2, B6, T1, T7, T8, T9, B3, T2, B4, T5, T4, T3`

- **B1, B2, B6, T1, T7, T8, T9, T2, B4** — no upward call; pure wraps. Prove the
  contract + registry plumbing on low-risk gates first (batches 1–2, most of 3–4).
- **B3** (batch 3) — first gate exercising `ctx.AtrPoints` + `ctx.spreadPrice`;
  do it once the wrap pattern is proven.
- **T5, T4, T3** (batches 4–5, last) — largest gates; T3/T4 carry the
  `MM_ATRPoints` reroutes, T4 the hybrid, T5 the heavy level-packing. Highest
  regression surface, migrated when the recipe is fully shaken out.

Session 14 (out of scope here) then converts EntryGates to the registry walk and
moves the 2% rule into the pipeline (Phase 3c).
