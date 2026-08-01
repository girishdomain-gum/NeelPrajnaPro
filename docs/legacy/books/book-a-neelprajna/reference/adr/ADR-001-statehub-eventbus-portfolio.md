# ADR-001 — Communication spine (StateHub + EventBus) and StrategyPortfolio

- Status: **Accepted** (owner-approved, 2026-07-21)
- Applies to: NeelPrajna v3.16.4 → v4.x overhaul
- Companion docs: `docs/plans/overhaul.md`, `NeelPrajna_Dev_Workflow_v1.0.md`, target diagram v2

---

## 1. Context

Architecture review of v3.16.4 (21.6k lines, 28 files) found four structural problems:

1. `EG_*` globals act as a shared bulletin board — 18 of 28 files read or write them; no single owner of gate state.
2. `Dashboard.mqh` (3,506 lines) contains business logic: the 2% rule, trade actions, NPSU apply/restore. UI cannot be changed without re-testing trading behavior.
3. Gates call *upward* into TradeManager/MoneyManager (T3/T4/T5 → `TM_*`; six gates → `MM_*`), inverting the dependency direction and blocking isolated testing.
4. Blocker visibility is scattered — the BTCUSDT silent spread-block incident was a symptom: no contractual place where "why didn't we trade?" is answered.

Additionally, the concept of a *strategy* (gate mask + RR/trail/BE) exists in three fragments with no owner: UniverseRoster DSL files (virtual), `BD_NPSU_ApplyStrategy` (real, session-only, in the UI), and the raw inputs/toggles (the real account's unnamed implicit strategy).

The NPSU subsystem (UniverseEngine/VirtualBook/MetaSwitcher) already demonstrates the desired discipline internally: observe state, never mutate gates, never touch real orders.

## 2. Decision

### 2.1 Four layers, downward-only dependencies

```
L4 UI              Dashboard (thin renderer + widgets + layout engine)
Core spine         StateHub · EventBus
L3 Application     AdvisorEngine · UniverseEngine · MetaSwitcher
                   → StrategyPortfolio (funnel to domain)
L2 Domain          EntryGates pipeline (registry walk, 2% rule) ·
                   Gates B1–B6/T1–T9 (GateBase + GateContext) ·
                   TradeManager · MoneyManager
L1 Infrastructure  Config · Loggers (CSV) · ChartTheme
External           Python analyzer (research layer, file boundary via CSV)
```

A *layer* is a dependency boundary; modules within a layer are boxes, not bands. No fifth layer is introduced (see §4, rejected alternatives).

### 2.2 StateHub

One `EAState` struct, written by domain/application code every tick, read by UI and observers. Contains bias/trigger states, exec state (auto, spread, positions, retry, **blocker**), per-direction pipeline readout, account, and positions. The UI is a pure function `render(EAState)`.

**Contract:** every entry block writes `exec.blocker`. Silent blocking becomes structurally impossible.

### 2.3 EventBus

Fixed enum of commands and events, synchronous dispatch (MQL5 is single-threaded per chart), single logged chokepoint.
- UI → down: `CMD_TOGGLE_GATE`, `CMD_BUY/SELL/CLOSE/NUKE`, `CMD_TWOPC_ARM`, `CMD_APPLY_STRATEGY(uid)`.
- Down → observers: `EVT_SIGNAL_FIRED`, `EVT_ENTRY_BLOCKED(reason)`, `EVT_DEAL_CLOSED`, `EVT_STRATEGY_APPLIED`.

### 2.4 GateBase + GateContext

All 14 gates implement a common contract: `Enabled/SetEnabled`, `Evaluate(GateContext) → GateResult{dir, sl, tp, note}`, `PublishState(hub)`. `GateContext` carries spread, session, ATR, and anything gates currently fetch from TM/MM — passed *down* by the pipeline. Gates lose all upward TM_/MM_ calls. EntryGates becomes a registry walk; adding a gate = registration, not edits across files.

### 2.5 StrategyPortfolio (application layer)

Single owner of the strategy concept:
- `Strategy` is a domain value object: gate mask + RR/trail/BE parameters.
- Portfolio owns the roster (absorbs UniverseRoster's registry role), the **named** active real strategy, apply/restore (evicted from Dashboard — UI posts `CMD_APPLY_STRATEGY`), and feeds UniverseEngine (one virtual book per entry), AdvisorEngine, and MetaSwitcher.

### 2.6 Constraint — real account concurrency (owner decision)

> **The REAL account runs exactly one strategy at a time (radio behavior). Concurrent multi-strategy execution is permitted only for virtual books and meta-universes.**

The Portfolio enforces this invariant in code. Real concurrent allocation (capital budgets, netting-conflict resolution) is deliberately **not** built — it may be revisited only if a meta/multi-strategy configuration wins out-of-sample in NPSU research, mirroring the v3.11 auto-adopt discipline. Revisiting requires a new ADR superseding this section.

## 3. Consequences

Positive: Dashboard shrinks to a renderer (~1,500 lines target from 3,506); gates unit-testable and pluggable; blocker class of bugs eliminated by contract; strategy identity explicit ("REAL is running T1_B6B2B4"), enabling honest attribution; NPSU discipline generalized rather than invented.

Negative / costs: migration window where state exists in both `EG_*` globals and StateHub (mitigated: dual-write until Phase 5 deletes legacy); GateContext migration doubles effort for T3/T4/T5 (the gates with direct TM_ calls); one extra indirection when reading state (negligible in MQL5 single-thread).

Validation: per phase — compile clean, Strategy Tester deal list byte-identical to frozen baseline through Phase 3; on-chart manual test of toggle round-trips (tester does not exercise chart events).

## 4. Alternatives considered

- **Strategy portfolio as a fifth layer** (owner-proposed, discussed, rejected jointly): a layer is a dependency rule, not a concept; a portfolio band would force ceremony (e.g. Advisor→TM only via Portfolio) without benefit. Chosen: module in L3.
- **Async/queued event bus**: rejected — MQL5 single-threaded per chart; synchronous is simpler, deterministic, fully debuggable.
- **Keep globals, document conventions**: rejected — conventions already exist as comments and did not prevent the coupling or the spread-block incident.
- **Build real-account multi-strategy allocation now**: rejected as speculative generality; see §2.6.

---

## Errata

**ERRATA 2026-07-22:** §1 item 3 overstated — code inventory at Phase 3 Session 0
found zero live `TM_` calls in gates; actual upward coupling is `MM_ATRPoints`
(B3×1, T3×2, T4×2) + B3 live-spread read. GateContext severs these. (History not
rewritten; §1 stands as the 2026-07-21 pre-refactor characterization. See
`docs/plans/phase3_gate_recipe.md` §Step-1 for the grounding inventory.)
