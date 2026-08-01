# ARCH-NP-004 — WO-P: EXECUTION-MODEL PARITY (Sprint NP-S2, first work order)
*Sealed instruction for the Developer. Mandated by **NP-D-011** (Owner-ruled 2026-07-30): execution-model parity is a **hard precondition** of any further R6 evidence collection. Architect role · session: Opus 5, claude.ai interface, filesystem connector · 2026-07-30.*

**Written under NP-D-012** — this specification is intended to be sufficient for an independent implementation without reading the answer out of existing code. Where it is not, that is a defect: **raise a DEVQ, do not fill the gap yourself.**

---

## 1. Why this exists

In NP-S1 the audited engine could not express H-007's evidenced trade rule — *stop = penetration extreme ± 10 ticks, target = 1.5R* — because those are **per-trade values derived from each event**, and the engine accepts only hypothesis-level constants. The hypothesis was therefore registered with `stop_offset: null, target_offset: null, exit_rule: time_stop`, and the Battery judged *sweep-then-hold-12-bars* (NOTE-NP-001). The Chief Scientist named this the sprint's largest scientific weakness, and every population judged before parity exists inherits it.

## 2. What exists today (read from source; verify before trusting)

`qrf/trading/simulator/engine.py` → `ExecutionSpec`:

| Field | Type | Today's semantics |
|---|---|---|
| `hold_bars` | `int ≥ 1` | time stop, in bars |
| `strength_min` | `float` | event filter |
| `stop_offset` | `float > 0 \| None` | **one constant price distance for every trade**; `None` = no stop |
| `target_offset` | `float > 0 \| None` | **one constant price distance for every trade**; `None` = no target |
| `size` | `float > 0` | per-trade size |
| `exit_rule` | `"time_stop" \| "calendar_day"` | `_EXIT_RULES` |

**The gap in one sentence: offsets are scalars on the hypothesis, so two trades in the same hypothesis cannot have different stop distances.** Entry, cost, gross/net and the no-look-ahead fill machinery (`qrf/trading/simulator/fills.py`) are all sound and are **not** what this work order changes.

## 3. AC-1 — the requirement that outranks the feature

**Every existing sealed verdict must remain byte-identically reproducible.**

Verdicts record `engine_version` (NP-S1's reads `engine.s5.1`) and IVF re-derives them from raw records. A silent behavioural change to the engine would retroactively break verdicts already accepted — including the programme's first.

Therefore: **bump the engine version**, and prove with a test that for every hypothesis already registered (`h001`–`h004` and both `h007_np_liquidity_sweep_v1_1` registrations), the new engine produces **byte-identical trades** to the recorded `verdict_trades.*` parquet when the new capabilities are unused. **If byte-identity cannot be achieved, stop and raise a DEVQ before proceeding** — do not "improve" a number that a sealed verdict depends on.

## 4. Required capability

**4.1 Per-trade stop, sourced from the event.** The engine shall accept a stop whose distance or price is carried **on the event**, so each trade may differ. The event value must be determined by data available **at or before `signal_ts`** — H-007's penetration extreme qualifies, being fixed by the sweep bar itself. Declare the mechanism (an optional EventFrame column read by the engine, or an equivalent) and specify it well enough to reimplement.

**4.2 R-multiple targets.** The engine shall accept a target expressed as a multiple of the trade's **realized risk**, `R = |entry_price − stop_price|`, computed at entry. H-007's rule is `1.5R`. An R-multiple target without a stop is meaningless and shall be **refused at registration**, not silently ignored.

**4.3 The intrabar tie rule — pin it, do not infer it.** With OHLC bars, a bar can touch both stop and target and the order is unknowable. **The rule is: the stop fills.** This is conservative, and it matches the bespoke stack's own declared behaviour ("SL and TP in the same second → SL"). **State it in the docstring and prove it with a fixture where both levels sit inside one bar's range.**

**4.4 Anti-hindsight preserved.** The existing invariant is non-negotiable: feeding the same data incrementally never changes an already-closed trade. Property-test it **with the new per-trade paths exercised**, not only the legacy ones.

**4.5 Registration validation.** A hypothesis using per-trade stops must declare it, and the registry must refuse: an R-multiple target with no stop · an event-sourced stop the EventFrame cannot supply · a non-positive or non-finite stop distance. **Refusals name the offending field.**

## 5. Acceptance criteria

- **AC-1** every existing sealed verdict's trades reproduce byte-identically under the new engine version (§3).
- **AC-2** a hand-computed fixture with **per-trade varying stops and a 1.5R target** round-trips exactly — the fixture is computed by hand first, then the engine is run against it.
- **AC-3** the both-levels-in-one-bar fixture fills the **stop** (§4.3).
- **AC-4** the anti-hindsight property test passes with per-trade paths exercised.
- **AC-5** registration refuses each malformed case in §4.5, naming the field.
- **AC-6** `ExecutionSpec`'s docstring specifies the new semantics completely enough for an independent reimplementation — **NP-D-012 applied to your own work.**
- **AC-7** kernel firewall stays green; no trading vocabulary enters `qrf/kernel/**`.

## 6. Non-goals

No re-run of any burned window · **no re-registration of H-007** (its verdict stands within its documented scope; parity serves *future* evidence) · no R6 collection, which is gated on this work order and on the Owner's lab-unpause ruling · no changes to cost models, the Battery pipeline, deflation, or the WindowLedger · no new exit rules beyond what §4 requires.

## 7. DEVQ triggers — stop the line

Byte-identity in AC-1 unreachable · the EventFrame column spec cannot carry a per-trade stop without violating anti-hindsight · a registration validation that would reject an already-sealed hypothesis · any place this specification is insufficient to implement without reading existing code for the answer (**NP-D-012 — that is a defect in my instruction, and I want it back as a DEVQ**).

## 8. Sequencing note

**WO-P does not require the lab unpause.** It is pure Kernel-side Python. The unpause ruling gates R6 *collection*, which follows this work order — so WO-P can start immediately and the Owner's unpause decision is not on its critical path.

---
*Anchor: **the engine judged a strategy nobody registered, because it could not express the one that was. Parity is what makes the next comparison mean what it says.***

---
## 9. ADDENDUM — position in the sprint state machine (appended 2026-07-31, P5; §§1–8 unedited)

This instruction was written before `ops\SPRINT_STATE_MACHINE_v1.1.md` existed and referenced none of it. Reconciled here rather than reissued.

**Phase:** WO-P is a **P2 BUILD lane**, concurrency class `PARALLEL`, role **DEV**, write scope `qrf/**` and `tests/**`. It runs alongside the other NP-S2 tracks and shares no files with them.

**Branch:** work goes to the shared sprint branch **`sprint/NP-S2`**, not to `main` and not to a private branch. Commit early, push often — **uncommitted means nonexistent**, and a session that has not pushed is invisible to every other session. `main` stays untouched until the sprint's single merge at P8.

**Handover:** on completion, publish `ops/aro/handovers/WO-P/HANDOVER.md` in the standard ten-section shape. Section 9, *how to verify me*, must give exact commands a stranger can run. **A completion without a handover is not a completion.**

**Mechanical exit check** (the form §9 of the state machine requires):
> the handover exists, CI is green on `sprint/NP-S2`, and a test named for AC-1 passes proving byte-identical reproduction of every existing sealed verdict under the bumped engine version.

**No ledger writes.** P2 forbids them by rule. WO-P touches no record in `datastore/**` at any point — consistent with §6's non-goals.

**Preflight status:** `ops/preflight/PFR_NP-S2.md` returns **NOT GREEN** on three blockers, **none of which touches WO-P** — it needs no scope, no data and no lab unpause, and its specification is complete. **WO-P may proceed now; the collection track waits for G1.**

**Finding recorded against the Architect:** NP-S2 was opened by issuing this instruction directly, with no P0 preflight and no G1 — violating the state machine's first rule on its first use. Corrected by running the preflight retrospectively; recorded rather than quietly repaired.
