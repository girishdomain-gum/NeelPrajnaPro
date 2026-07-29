# Phase 6 — Sequential Strategy Engine (SSE)
## Design & Architecture, v1.1

**Status:** PROPOSED — awaiting owner ruling on D1–D13
**Date:** 2026-07-23
**Deciders:** Girish Kumar (owner)
**Scope class:** ENGINE CHANGE — full §7 safety process per stage (this is
NOT a UI-only phase; "baseline: identical" applies only to stages that
promise it, stated per stage in §8).

---

## 0. Executive summary

Today a NeelPrajna strategy is a *simultaneous* condition:

```
Entry(D) = ALL enabled BIAS gates agree on D
           AND ANY enabled TRIGGER gate pulses D        (EntryGates.mqh)
```

Phase 6 introduces the **Sequential Strategy** — an *ordered* condition:

```
Entry(D) = Step1 satisfied … THEN Step2 satisfied within its window …
           THEN StepN satisfied  →  enter D
```

where each step combines **static gates** (conditions that HOLD — the
bias family) with **dynamic gates** (events that FIRE — the trigger
family). The static strategy is exactly the one-step sequence, so the
new engine is a strict **superset**: one Sequence Engine (SSE) executes
every strategy in the system — real, virtual, static, sequential.

The phase lands in three stages: 6a foundations (runtime-input refactor
+ SSE running SHADOW-ONLY inside NPSU — real account untouched),
6b real-account apply (behavioral, tester-gated), 6c unification (the
legacy static path becomes a compiled one-step sequence; value-identity
proven by A/B tester runs before the old path is deleted).

---

## 1. Big-picture analysis — where the architecture is today

### 1.1 What the Phase 1–5 overhaul bought us (strengths to build on)

| Asset | Why it matters for Phase 6 |
|---|---|
| **Layering (ADR-001)** Core → Engine → Gates → Apps → UI, includes point down only | SSE slots into Engine/ with zero layer violations; gates need not know sequences exist |
| **StateHub (read) / EventBus (write)** | Sequence runtime state publishes like everything else; UI extends, never reaches down |
| **Gate outputs are already a clean contract** | Every gate publishes per closed bar: bias `buy/sell` (a *level*), trigger `buy/sell + hasLevels + SL/TP` (an *event*). SSE consumes exactly this — **no gate changes** |
| **NPSU shadow universes + VirtualBook** | The proving ground: sequences race virtually with real R-accounting before any real money touches them |
| **Roster DSL + StrategyPortfolio identity (name+hash)** | The sequence definition rides the same file/DSL/hash pipeline; Advisor ranks both kinds with the same KPIs |
| **Closed-bar determinism + per-bar caches** | An FSM advanced only on closed bars is reproducible in the tester — the safety method survives |
| **Trigger consume-on-success + per-universe consumption matrix** (`npsu_consumed[u][t][d]`) | The exact machinery a sequence step needs to not re-fire on the same pulse |

### 1.2 Structural limits Phase 6 must respect or fix

1. **The entry law is hard-coded** in EntryGates (ALL-bias AND ANY-trigger)
   and re-implemented in UniverseEngine for virtual books. Two evaluators,
   one law. Phase 6 must not create a *third* evaluator — it must become
   THE evaluator (stage 6c).
2. **`input` variables are not runtime-mutable** (InpNPSU_Enabled,
   InpADV_Enabled — tech-debt, logged). Sequence experimentation demands
   runtime control; the refactor to `CFG_` runtime globals is a Phase 6a
   prerequisite, not an optional cleanup.
3. **Strategy identity = two masks.** `NPSU_Universe{bias_mask, trig_mask,
   rr, trail}` cannot express order, windows, or invalidation. Identity
   (name+hash) must grow to cover the sequence definition or the Advisor's
   comparisons become meaningless.
4. **EG_ bulletin residuals are sanctioned but frozen.** SSE reads the
   same published snapshot the universes read; it must NOT add new EG_
   globals (owner ruling, Phase 5 CLOSED list).
5. **VirtualBook keeps one open position per universe** (policy). A
   sequence universe holds at most one *armed* FSM per direction and one
   open virtual position — same budget, no redesign.

### 1.3 The conceptual gap SSE closes

The current model answers *"is the market in state X right now?"*.
Professional discretionary logic is usually *"did A happen, and then
B confirm it before it went stale?"* — e.g. *key level touched (B3
holds) → liquidity sweep + FVG forms within 12 bars (T3 fires) → a
pattern confirms within 6 bars (T1 fires) → enter.* That is a
finite-state machine over gate outputs. Everything needed to express it
already exists as gate signals; only the combinator is missing.

---

## 2. Concept model

### 2.1 Gate capability classes (formalising what gates already are)

| Class | Semantics | Today's members | Reading consumed by SSE |
|---|---|---|---|
| **STATIC** | A condition that HOLDS across bars (level/state) | B1 B2 B3 B4 B6 | `holds(D)` — the gate's buy/sell flags |
| **DYNAMIC** | An event that FIRES at a bar (pulse) | T1 T2 T3 T4 T5 T7 T8 T9 | `fired(D)` this closed bar + optional SL/TP levels |

No gate is modified, re-registered, or re-classified in code — the class
is a *view* over the existing bias/trigger registry. (T4 already lives a
dual life — trendline bias mode vs breakout trigger mode — which the
classes describe cleanly: its bias reading is STATIC, its pulse DYNAMIC.)

### 2.2 The Sequence

```
Sequence := Step[1..K]  (K ≤ SEQ_MAX_STEPS, D2)  +  rr  +  trail

Step := {
  guards     : AND-set of STATIC gates      // must HOLD for the step to advance
  advancers  : OR-set  of DYNAMIC gates     // any pulse in dir D advances
  window     : max closed bars to wait in this step (0 = no limit)
  invalidate : optional OR-set of STATIC gates whose FLIP resets to Step 1
}
```

**Direction binding (D1):** the sequence's direction D is locked by the
Step-1 advance. Every later guard/advancer is evaluated in that same D.
A sequence instance runs per direction (one BUY chase and one SELL chase
may be armed simultaneously, like today's independent buy/sell pipelines).

**Runtime state per sequence instance:**

```
{ stepIdx, dir, armedBar, stepEnteredBar, lastResetReason }
```

Transitions (evaluated once per CLOSED bar, in this order):
1. *Invalidate*: any invalidator flipped against D → reset to idle,
   record reason.
2. *Expire*: bars-in-step > window → reset to idle, record reason.
3. *Guard check*: all step guards hold in D — else the step simply
   *waits* (guards gate advancement; they do not reset — resetting is the
   invalidators' job; D4).
4. *Advance*: any advancer fired in D (and not yet consumed by this
   sequence, reusing the consumption-matrix pattern) → stepIdx++.
5. *Entry*: advancing past Step K emits an **entry proposal**
   `{dir, SL/TP source = the final advancer's levels, rr, trail}`.

### 2.3 The superset claim (why "all strategies run from this engine")

A static strategy `{bias_mask, trig_mask, rr, trail}` compiles to:

```
Sequence: K = 1
  Step1 = { guards = bias_mask, advancers = trig_mask, window = 0, invalidate = ∅ }
```

Walking §2.2 for K=1 reproduces the legacy law exactly: guards = ALL
enabled bias agree; advance = ANY enabled trigger fires; entry levels =
the firing trigger's SL/TP; consume-on-success preserved by the
consumption matrix. This equivalence is the *formal target of the 6c
A/B proof* — not an assumption (§8, stage 6c gate).

---

## 3. Architecture

### 3.1 Component placement (ADR-001-clean)

```
┌─ UI ───────────────────────────────────────────────────────────────┐
│ LIVE: ACTIVE STRATEGY grows a STEP RAIL (✓ done · ▶ current · ·)  │
│ SCOPE: sequence timeline + reset-reason strip for SEQ universes    │
│ CTRL: apply works identically (identity = name+hash, kind-blind)   │
└──────────────▲─────────────────────────────────────────────────────┘
               │ reads StateHub (SSequenceState, new)
┌─ Apps ───────┴─────────────────────────────────────────────────────┐
│ UniverseRoster: DSL grows SEQ grammar → NPSU_Universe.kind=SEQ,    │
│                 seq descriptor table (parse-time compiled)         │
│ UniverseEngine: per-universe evaluation delegates to SSE_Eval()    │
│ AdvisorEngine / MetaSwitcher / VirtualBook: UNCHANGED              │
│ StrategyPortfolio: apply/restore carries kind + descriptor hash    │
└──────────────▲─────────────────────────────────────────────────────┘
               │ calls down
┌─ Engine ─────┴─────────────────────────────────────────────────────┐
│ **SequenceEngine.mqh (NEW)** — pure FSM evaluator:                 │
│   in : SSeqDescriptor + gate snapshot + SSeqRuntime (by ref)       │
│   out: advanced runtime + optional SEntryProposal                  │
│   NO CTrade, NO chart objects, NO file I/O — testable in isolation │
│ EntryGates: 6a/6b unchanged; 6c its combinator becomes a compiled  │
│             one-step sequence routed through SSE                   │
│ TradeManager: consumes SEntryProposal exactly like today's fires   │
└──────────────▲─────────────────────────────────────────────────────┘
               │ reads gate outputs (published snapshot — no new EG_ globals)
┌─ Gates ──────┴─────────────────────────────────────────────────────┐
│ B1..B6, T1..T9 — **ZERO CHANGES** (capability classes are a view)  │
└────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data structures (Core/StateHub additions)

```
SSeqStep       { int guardsMask; int advMask; int windowBars; int invMask; }
SSeqDescriptor { string name; string hash; int K; SSeqStep steps[SEQ_MAX_STEPS];
                 double rr; bool trailOn; }
SSeqRuntime    { int stepIdx; int dir; datetime armedBar, stepBar;
                 int lastResetReason; }         // per universe × direction
SSequenceState { published mirror for the applied sequence: stepIdx/K,
                 dir, barsLeftInWindow, waitingForMask, lastResetReason }
```

Masks reuse the existing `EG_BIT_*` vocabulary — one bit language across
static and sequential strategies.

### 3.3 Entry execution & magic numbers

Real-account sequential entries route through TradeManager exactly like
trigger fires today. **Magic allocation: `base+15` = SSE entries** (the
next free offset; `+11` stays retired per the standing owner rule).
Virtual sequential entries use VirtualBook unchanged (R-denominated).

---

## 4. Sequence DSL v1 (roster-file grammar extension)

Grammar (one line per strategy file, same pipeline as today):

```
KIND=SEQ NAME=<name> RR=<x.y> TRAIL=<on|off>
STEP1 = GUARD:<B..+B..|NONE> ADV:<T..|T..> WIN:<bars|0> INV:<B..|NONE>
STEP2 = ...
```

Worked examples:

```
# Key-level sweep confirmation (the motivating case)
KIND=SEQ NAME=KL_SweepConfirm RR=2.0 TRAIL=on
STEP1 = GUARD:B3+B6 ADV:T3     WIN:0  INV:NONE
STEP2 = GUARD:B6    ADV:T1|T8  WIN:6  INV:B1

# Today's T1_B1B6 static strategy, expressed as its 1-step sequence
KIND=SEQ NAME=T1_B1B6_seq RR=2.0 TRAIL=on
STEP1 = GUARD:B1+B6 ADV:T1 WIN:0 INV:NONE
```

Parser rules: unknown token / empty ADV / K > SEQ_MAX_STEPS → the slot
goes CONFIG ERR exactly like today's DSL errors (visible in the roster,
never silently ignored). The descriptor hash covers the FULL step table,
so two sequences differing only in a window are distinct identities.

---

## 5. StateHub / EventBus / UI extensions

- **StateHub:** `g_state.seq` (SSequenceState) for the applied strategy;
  `SUniverseRow` gains `kind` + `seqStepTxt` ("2/3 · waiting T1|T8 ·
  4 bars left") for the roster and SCOPE.
- **EventBus:** no new command types needed for 6a/6b apply (CMD_APPLY_
  STRATEGY already carries name+hash; kind resolves from the roster).
  CMD_SET_NPSU_ENGINE / CMD_SET_ADVISOR become REAL commands in 6a
  (see §7).
- **UI (LIVE):** the v5.5.x ACTIVE STRATEGY group grows one row — the
  **step rail**: `S1 ✓ · S2 ▶ T1|T8 (4) · S3 ·` in the established
  token grammar (verified glyphs only, regular weight per §3 rule).
- **UI (SCOPE):** RECENT VIRTUAL gains nothing; a small "SEQ" line above
  VIRT OPEN shows the FSM state + last reset reason ("expired W:6",
  "invalidated B1").
- **UniverseLogger CSVs:** trades rows gain `seq_step_path` (e.g.
  "1@1023,2@1031,E@1035"); header version bumps (schema is versioned,
  analyzers updated in the same stage).

---

## 6. Decision record (owner sign-off required, house D-style)

| # | Decision | Proposal | Alternatives considered |
|---|---|---|---|
| D1 | Direction binding | Locked at Step-1 advance; one instance per direction | Re-evaluate direction each step (rejected: ambiguous identity, untestable claims) |
| D2 | Step cap | `SEQ_MAX_STEPS = 4` | Unlimited (rejected: state explosion, UI unreadable) |
| D3 | Window semantics | Closed bars in the CURRENT step; 0 = unlimited | Wall-clock time (rejected: tester nondeterminism across sessions/gaps) |
| D4 | Guard failure | Step WAITS (no reset); only invalidators/window reset | Guard failure resets (rejected: makes B-gate noise fatal; invalidators exist precisely to express "this flip kills the setup") |
| D5 | Pulse consumption | Reuse the per-universe consumption matrix; a pulse advances a given sequence at most once | Fresh mechanism (rejected: duplicates proven code) |
| D6 | Reattach persistence | v1 RESETS all FSMs to idle on init (honest, simple, logged) | History replay (deferred: bounded-lookback replay is a clean later upgrade; documented as accepted limitation) |
| D7 | SL/TP source | The FINAL advancer's levels (it is the entry event) | First advancer / synthetic (rejected: stale levels) |
| D8 | Magic offset | `base+15` = SSE real entries | Reuse +1 chain (rejected: destroys attribution) |
| D9 | Identity | hash covers kind + full step table + rr/trail | Name-only (rejected: Advisor comparisons need content identity) |
| D10 | Third-evaluator ban | 6c MUST retire the duplicated static law (EntryGates combinator + UniverseEngine copy) into SSE; until then the duplication is explicitly temporary | Keep three evaluators (rejected: the current two are already one too many) |

---

## 7. Folded-in prerequisite: runtime-mutable engine inputs (existing debt)

Stage 6a refactors `InpNPSU_Enabled` / `InpADV_Enabled` consumption to
`CFG_NPSU_Enabled` / `CFG_ADV_Enabled` runtime globals seeded from the
inputs at `Config_Init()`. The CTRL commands `CMD_SET_NPSU_ENGINE` /
`CMD_SET_ADVISOR` then mutate the CFG_ globals for real, and the v5.5.4
LOCKED switches become LIVE switches with no UI change beyond dropping
`locked=true`. Engine-behavioral: full tester gate; the default-on run
must produce a byte-identical baseline (the refactor changes *where* the
flag is read, not its value).

---

## 8. Migration plan — three stages, each with its own gate

| Stage | Content | Real-account behavior | Safety gate |
|---|---|---|---|
| **6a — Foundations** | CFG_ input refactor (§7); SSE module + unit-style tester harness; DSL parser + descriptor hash; SEQ universes run SHADOW-ONLY in NPSU; StateHub/UI read-outs | UNCHANGED — sequences exist only virtually | compile 0/0; **real deal list byte-identical**; NPSU CSVs *intentionally* grow (schema-versioned) — declared `baseline: intentional diff — virtual layer only`; input-refactor A/B: default-on run identical |
| **6b — Real apply** | CTRL APPLY accepts kind=SEQ; TradeManager consumes SEntryProposal; magic base+15 live; LIVE step rail | CHANGED when (and only when) the owner applies a SEQ strategy; input-defaults behavior untouched | full backtest comparison of an applied-SEQ scenario reviewed by owner; default run still byte-identical; explicit owner sign-off before any live attach |
| **6c — Unification** | Legacy static combinator compiled to 1-step sequences inside SSE; UniverseEngine's duplicate law deleted; EntryGates keeps gate registry/walk only | Intended IDENTICAL | **A/B equivalence proof**: tester runs of the legacy engine vs SSE-compiled statics across the standing baseline set must match deal-for-deal before the old path is deleted; any diff = stop and diagnose, never "close enough" |

Rollback: each stage is a branch; 6b ships behind the roster (no SEQ
files present ⇒ engine dormant); 6c deletes code only after the proof.

---

## 9. Risks & mitigations

| Risk | Mitigation |
|---|---|
| FSM state explosion / unreadable UI | D2 step cap; step rail shows one line; windows capped at parser (≤ 512 bars) |
| Repaint / intra-bar ambiguity | Closed bars only (house rule); advancers read the same published pulses the universes read |
| Silent divergence between static law and its 1-step compilation | The 6c A/B deal-for-deal proof is the *release gate*, not a nice-to-have |
| Consumption double-count when a pulse could advance two armed sequences | Per-universe matrix keyed (u, trigger, dir) — same isolation as today |
| CSV/analyzer breakage | Schema version bump + analyzer update in the same 6a commit; old files remain parseable by version switch |
| Reattach loses an armed chase (D6) | Logged loudly at init ("SEQ FSMs reset — N were armed"); replay upgrade documented as the planned fix |
| Scope creep into gate rewrites | Hard rule: Gates layer is untouchable in Phase 6; anything a sequence "wishes" a gate exposed goes to tech-debt for its own phase |

## 10. Out of scope (explicitly)

Multi-symbol sequences; intra-bar (tick-level) steps; nested/branching
sequences (step graphs); ML-selected sequences; changing the single-
applied-strategy radio rule on REAL; any modification to money
management or the 2% rule.

---

## Appendix A — capability map of existing gates

| Gate | Class | Sequence roles |
|---|---|---|
| B1 Nexis MA | STATIC | guard, invalidator |
| B2 MTF Candle | STATIC | guard, invalidator |
| B3 Key Level | STATIC | guard (the classic Step-1 anchor), invalidator |
| B4 SMC Structure | STATIC | guard, invalidator |
| B6 RegChannel | STATIC | guard (quality filter), invalidator |
| T1 Pattern | DYNAMIC | advancer (typical confirmer), levels |
| T2 AutoFibo | DYNAMIC | advancer, levels |
| T3 Sweep+FVG | DYNAMIC | advancer (typical initiator), levels |
| T4 TrendLines | DYNAMIC (trigger mode) / STATIC (bias mode) | either role, mode-dependent |
| T5 Topography | DYNAMIC | advancer, levels |
| T7 Market Metrics | DYNAMIC | advancer, levels |
| T8 CMH Patterns | DYNAMIC | advancer (confirmer), levels |
| T9 CCC Hidden | DYNAMIC | advancer (confirmer), levels |

---

## 11. Definition & distribution — "how do we write a dynamic strategy
as a set file?" (v1.1 addendum, owner question 2026-07-23)

### 11.1 The problem, precisely

A static strategy IS a .set file because its whole definition is a
subset of `input bool` gate enables. A sequence adds ORDER, WINDOWS and
INVALIDATORS — information booleans cannot carry. The .set mechanism
itself is not the obstacle: a .set file assigns values to ANY declared
input, **including `input string`**.

### 11.2 The answer: the sequence rides in the .set as DSL strings

```
InpSeq_Kind  = SEQ                 // "" or STATIC = legacy per-gate reading
InpSeq_Name  = KL_SweepConfirm
InpSeq_RR    = 2.0
InpSeq_Trail = true
InpSeq_Step1 = GUARD:B3+B6 ADV:T3    WIN:0 INV:NONE
InpSeq_Step2 = GUARD:B6    ADV:T1|T8 WIN:6 INV:B1
InpSeq_Step3 =                     // empty = unused (K derived)
InpSeq_Step4 =
```

The owner edits the step strings in the normal F7 inputs dialog and
saves — MT5 writes the .set. The .set stays the SINGLE self-contained
definition of behaviour (tester runs, reproducibility, live attach all
keep working from one file), preserving the property that made static
.sets valuable.

**Dual sourcing mirrors the proven NPSU pattern** (roster inputs vs
`NPSU_Strategies\` files behind `InpNPSU_UseFiles`): the .set strings
are the CANONICAL form for the applied/real strategy; `*.seq` files in
the strategies folder are the CONVENIENCE form for racing many
sequences virtually. Both feed ONE parser producing ONE descriptor.

### 11.3 Module & layer placement

```
DEFINITION SOURCES                    ONE PARSER, ONE DESCRIPTOR
──────────────────                    ──────────────────────────
.set file ─▶ input string InpSeq_* ─┐
                                     │   ┌─ Apps/SeqCodex.mqh (NEW) ───────────┐
NPSU_Strategies\*.seq files ────────┼──▶│ owns InpSeq_* inputs · file scanner ·  │
                                     │   │ grammar parser · normaliser · HASH     │
inline roster inputs (later) ───────┘   │ out: SSeqDescriptor (a Core type)      │
                                         └──────────────┬──────────────────┘
                                                        ▼
                            ┌─ Apps/UniverseRoster ─ slot kind=SEQ + descriptor ─┐
                            │           │                          │             │
                            │           ▼                          ▼             │
                            │ Apps/UniverseEngine          Apps/StrategyPortfolio │
                            │ (virtual racing)             (APPLY to REAL, D9)    │
                            └───────────┬───────────────────────┬───────┘
                                        ▼                          ▼
                            ┌─ Engine/SequenceEngine.mqh — SSE_Eval() FSM ──────┐
                            │  the ONE executor (virtual & real, D10)           │
                            └───────────┬──────────────────────────────┘
                                        ▼ entry proposal
                            Engine/TradeManager (real, base+15) · VirtualBook (virtual)
```

Why this placement: **definition is an Apps concern, execution is an
Engine concern.** SeqCodex sits in Apps/ because parsing strategy
definitions and feeding the roster is exactly UniverseRoster's job
today — and Apps legally includes Engine and Core (ADR-001, downward
only). The descriptor STRUCT lives in Core/StateHub so every higher
layer shares the type. The FSM sits in Engine/ beside EntryGates and
TradeManager because deciding "enter now" is engine work. The inputs
live in SeqCodex next to the logic they control (house rule §"inputs
next to their logic").

### 11.4 New decisions (extend the D-table; owner sign-off)

| # | Decision | Proposal | Alternatives considered |
|---|---|---|---|
| D11 | Definition module | NEW `Apps/SeqCodex.mqh` owns InpSeq_* inputs, file scan, parser, normaliser, hash | Extend UniverseRoster in place (rejected: roster already ~parses two formats; "one module, one job" — codex = definitions, roster = slots) |
| D12 | Canonical form + identity | .set strings canonical for the applied strategy; `*.seq` files for virtual racing; hash computed over the NORMALISED step table (case/whitespace-insensitive) so identical content = identical identity regardless of source | Filename-based identity (rejected: file drift breaks Advisor comparisons); set-only (rejected: racing 20 sequences would need 20 attach cycles) |
| D13 | Precedence & backward compat | `InpSeq_Kind=SEQ` ⇒ the InpSeq_* definition IS the applied strategy and per-gate enables are ignored for entry logic (still honoured for compute-mask); `""`/`STATIC` ⇒ legacy per-gate reading (a 1-step sequence after 6c) | Merge both (rejected: two half-authorities = undebuggable) |

### 11.5 Honest limitation (recorded)

The Strategy Tester's OPTIMIZER cannot iterate `input string` values —
any sequence backtests fine from its .set, but optimising e.g. a window
length needs a packed-integer encoding (per-step int inputs). Deferred:
noted as the Option-C upgrade, not in v1.

