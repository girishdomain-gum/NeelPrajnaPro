# HANDOVER — WO-P, Execution-Model Parity (Sprint NP-S2)
*Developer session · claude-code · 2026-07-31. Instruction: `ops/ARCH-NP-004_WO-P_execution_parity.md` (+ §9 addendum) via `ops/DEVELOPER_BOOT_WO-P.md`.*

---

## 1. What was asked

Make the audited engine's `stop_offset`/`target_offset` — today hypothesis-level
scalars, one constant for every trade — into **per-trade** values, sourced from
the event data, plus **R-multiple targets** (a multiple of realized risk
`R = |entry - stop|`). **AC-1 outranks the feature**: every existing sealed
verdict (`h001`–`h004`, both `h007_np_liquidity_sweep_v1_1` registrations) must
reproduce byte-identically under a bumped `engine_version`, or the work stops
and a DEVQ goes up instead. Seven acceptance criteria (AC-1–AC-7, ARCH-NP-004
§5); no re-registration of H-007, no R6 collection, no cost-model/deflation/
WindowLedger changes.

## 2. What I did

Read the full boot chain (`ARCH-NP-004` incl. §9 addendum, `PFR_NP-S2.md`,
`SPRINT_STATE_MACHINE_v1.1.md` §9–§10, `engine.py`, `fills.py`), then explored
the registry (`hypotheses.py`, `schemas.py`), the EventFrame schema
(`qrf/kernel/instruments/base.py`), the sealed verdict/manifest records in the
journal, and the existing test suite/conventions before writing anything.

Implemented per-trade stops as an **effective-offset resolution** inside
`EventEngine.simulate`: for each event, compute an effective `stop_offset`/
`target_offset` (from the new per-trade mechanism if declared, else the legacy
scalar unchanged) and hand it to the **existing, unmodified** `fills.resolve_exit`
— so the intrabar geometry, the stop-before-target tie rule, and pessimistic
gap-through all apply exactly as before, and `fills.py` needed zero logic
changes. Added registration-time validation (three layers: `ExecutionSpec.
__post_init__`, `schemas._validate_execution`, `hypotheses._EXECUTION_KEYS` —
the same layering `stop_offset`/`target_offset` already used) refusing every
case AC-5 names, plus two consistency guards not explicitly named but implied
by "declare it": a stop/target may be declared by exactly one mechanism, never
both. Bumped `engine_version` `s5.1` → `s5.2`. Wrote AC-1–AC-7 tests (details
in §7). Discovered and documented (did not fix — out of write scope) a
pre-existing, unrelated break in `scripts/rebuild_bulk.py` (§4, §6).

## 3. What changed

| File | Change |
|---|---|
| `qrf/trading/simulator/engine.py` | `ExecutionSpec` gains `event_stop_column: str \| None` and `target_r_multiple: float \| None` (+ validation, `as_dict`/`from_dict`, docstring). `EventEngine.simulate` resolves per-event effective stop/target offsets before calling `fills.resolve_exit` (unchanged). `engine_version` `"engine.s5.1"` → `"engine.s5.2"`. |
| `qrf/trading/simulator/fills.py` | Docstring note only — no logic change. |
| `qrf/kernel/records/schemas.py` | `_validate_execution` accepts the two new optional keys and enforces AC-5's three refusals + the two mutual-exclusivity guards; added `math.isfinite` to the existing `stop_offset`/`target_offset` check (a `math.inf` value previously passed `val > 0`). |
| `qrf/kernel/protocol/hypotheses.py` | `_EXECUTION_KEYS` carries the two new keys through to the payload (else `schemas.py` would never see them). |
| `tests/simulator/test_engine.py` | AC-2, AC-3, AC-4 tests; `ExecutionSpec`-level mirrors of the AC-5 refusals; `_events_with_level` helper. |
| `tests/protocol/test_hypotheses.py` | AC-5 registration-refusal tests (all three named cases + the two mutual-exclusivity guards + one valid-registration happy path). |
| `tests/scripts/test_ac1_engine_parity_np004.py` | **New.** AC-1: h001–h004 and the judged h007 registration reproduce byte-identically; the unjudged 2nd h007 registration's execution parses unaffected. |
| `tests/battery/test_battery.py` | One assertion updated from the literal `"engine.s5.1"` to `EventEngine.engine_version` (the real engine's version legitimately changed; the test now tracks the class, not a frozen string). |
| `docs/coordination/notes/NOTE-NP-003_...md` | **New.** Records the pre-existing `rebuild_bulk.py` gap (§4). |
| `ops/aro/handovers/WO-P/HANDOVER.md` | This file. |

## 4. Decisions made (no DEVQ raised — reasoning below; flag me if any should have been one)

- **Mechanism (§4.1):** the per-trade stop is carried on an EventFrame column
  named by `ExecutionSpec.event_stop_column`, restricted to `{"level", "zone_hi",
  "zone_lo"}` — the only float64 (price-shaped) columns in the kernel's closed
  EventFrame schema (`qrf/kernel/instruments/base.py`). This makes AC-5's "an
  event-sourced stop the EventFrame cannot supply" a real, mechanically
  checkable refusal (any other name), rather than vacuous. The column holds an
  **absolute price**, not a distance; the engine derives `R = |entry - value|`
  itself, so a caller cannot mis-sign a stop onto the favorable side without it
  producing an obviously-degenerate (immediate or unreachable) fill.
- **`fills.py` untouched:** per-trade values are resolved to a per-trade
  *effective* `stop_offset`/`target_offset` inside `engine.py`, then handed to
  the existing `resolve_exit` unchanged. When neither new field is set this
  computation is a no-op passthrough (`eff_stop_offset = execution.stop_offset`,
  literally, no arithmetic) — which is *why* AC-1 holds by construction, not
  just by the test in §7.
- **Missing/NaN per-event stop value:** degrades to "no stop for that one
  trade" (falls through to time-stop exit) rather than raising or dropping the
  trade under a new counter. No AC covers this edge case; adding new
  drop-tracking machinery for it felt like scope creep beyond what's asked. If
  this is wrong, it's cheap to change — the branch is three lines in
  `engine.py`'s `simulate`.
- **Two extra mutual-exclusivity refusals** (stop_offset + event_stop_column
  together; target_offset + target_r_multiple together) beyond AC-5's literal
  three cases: an ambiguous double declaration isn't "declaring it" per §4.5's
  own framing. Same `SchemaViolation` convention, same "registration refused"
  phrasing as every other refusal in this file.
- **`engine_version` → `"engine.s5.2"`:** a minor bump (capability addition,
  not a behavioral change to any existing path — AC-1 is the proof).

## 5. What I did not do

- Did not touch `qrf/trading/concepts/neelprajna/detector.py` or any hypothesis
  YAML — H-007 is not re-registered (non-goal), and no detector was changed to
  actually populate `level` with a penetration extreme. This work order builds
  the engine *capability*; wiring a real detector to it is R6/future work,
  explicitly out of scope.
- Did not touch cost models, deflation, the WindowLedger, or the Battery
  pipeline (`battery.py`) — verified by inspection that `_run_folds`/`evaluate`/
  `run` pass `execution` straight through as a dict, needing zero changes.
- Did not fix `scripts/rebuild_bulk.py`'s missing h007 lineage dispatch
  (discovered while building the AC-1 test) — pre-existing, unrelated to this
  instruction, and `scripts/` is outside WO-P's declared write scope (`qrf/**`
  + `tests/**`). Documented in `NOTE-NP-003`; worked around in my own AC-1 test
  by driving the same underlying pipeline pieces directly instead of the
  broken orchestrator.
- Did not fix `tests/adapters/test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags`
  (missing external CSV, `IVF_S2_XAUUSD_PERIOD_H1.csv`, not present in this
  worktree) — confirmed unrelated: that test imports nothing this work order
  touched.
- Did not write any record to `datastore/journal/**` (verified by explicit
  `len(store)` before/after assertions in the new AC-1 tests) — P2's "no
  ledger writes" rule. The AC-1 tests do write derived, gitignored
  `datastore/bulk/*.parquet` scratch files (the same thing `scripts/
  rebuild_bulk.py` already does, sanctioned by its own existing test); the
  h007 scratch file is deleted in a `finally` block, the h001–h004 files are
  the normal rebuild-bulk cache and are gitignored either way.

## 6. Open questions

- Should `scripts/rebuild_bulk.py` be fixed to cover the h007 lineage? It's a
  real, pre-existing gap (`NOTE-NP-003`) but outside this instruction's scope
  and not blocking anything WO-P needed. Whoever owns `scripts/` should decide
  whether this becomes a DEVQ.
- `test_real_ivf_export_ingests_zero_flags`'s missing CSV — likely just an
  artifact never placed in this particular worktree (same class of thing as
  `datastore/bulk/` needing a rebuild); not investigated further since it's
  unrelated to engine/execution code.

## 7. Evidence of done

- **AC-1** — `tests/scripts/test_ac1_engine_parity_np004.py`, 3 tests: h001–h004
  (drives `rebuild_bulk`'s own bars/event-builder pieces + `EvidenceBattery.
  evaluate`/`trades_table`, sha256-compares against each recorded manifest);
  the judged h007 registration (same pipeline, bars rebuilt straight from the
  raw ticks via `ingest_h07_m5_vantage.build_m5_bars`, no bulk-store I/O
  needed); the unjudged 2nd h007 registration (execution dict round-trips to
  an unaffected `ExecutionSpec`). All assert `len(store)` is unchanged
  (no ledger writes).
- **AC-2** — `test_ac2_hand_computed_per_trade_stop_and_r_multiple_target`
  (`tests/simulator/test_engine.py`): two events, two different event-sourced
  stops (95.0 / 206.0), one hypothesis, hand-computed R and 1.5R target for
  each, engine output matches exactly.
- **AC-3** — `test_ac3_pessimistic_tie_stop_before_target_per_trade_path`: one
  bar spans both the event-sourced stop and the R-multiple target; stop wins.
- **AC-4** — `test_ac4_no_look_ahead_incremental_feed_per_trade_paths`: the
  existing incremental-feed property test, re-run with an event-sourced stop +
  R-multiple target exercised throughout.
- **AC-5** — `tests/protocol/test_hypotheses.py` (registry-level, the layer
  §4.5 names) + `tests/simulator/test_engine.py` (`ExecutionSpec`-level
  mirror): all three named refusals, both added mutual-exclusivity guards, one
  valid-registration happy path.
- **AC-6** — `ExecutionSpec`'s docstring (`qrf/trading/simulator/engine.py`)
  documents both mechanisms, their interaction with the legacy path, why AC-1
  holds structurally, and the tie/gap-through rules by reference; judged by
  review, no automated check (matches how the rest of this docstring is
  verified).
- **AC-7** — `.venv/Scripts/python.exe -m pytest tests/test_kernel_firewall.py -q` → 8 passed.
- **Mechanical exit check (state machine §9):** this file exists; a test named
  for AC-1 passes (`test_ac1_h001_through_h004_reproduce_byte_identically`,
  `test_ac1_h007_reproduces_byte_identically`) proving byte-identical
  reproduction of every existing sealed verdict under `engine.s5.2`. CI status
  on `sprint/NP-S2` is for the Architect/Owner to observe after push — not
  something this session can see from here.
- **Full suite:** `.venv/Scripts/python.exe -m pytest tests/ -q` → all green
  except two failures, both confirmed pre-existing and unrelated (§5, §6):
  `test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags` (missing external
  CSV) and the two `test_rebuild_bulk_s9.py` failures (`NOTE-NP-003`).

## 8. What's next

- R6 collection (gated on G1, not this work order).
- Wiring a real detector (e.g. `LiquiditySweepDetector`) to actually populate
  `level` with a penetration extreme for a future H-007-successor hypothesis —
  this work order built the capability, not the wiring; that's a future
  registration decision, not a Kernel change.
- Someone should decide whether `NOTE-NP-003`'s `rebuild_bulk.py` gap becomes
  a DEVQ.

## 9. How to verify me

```bash
git fetch origin
git log --oneline -5 sprint/NP-S2          # this session's commits should be at the tip
.venv/Scripts/python.exe -m pytest tests/simulator/test_engine.py tests/protocol/test_hypotheses.py tests/scripts/test_ac1_engine_parity_np004.py tests/test_kernel_firewall.py tests/battery/test_battery.py -q
.venv/Scripts/python.exe -m pytest tests/ -q
# Expect: all green except test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags
# and the two test_rebuild_bulk_s9.py failures — pre-existing, see NOTE-NP-003.
```
Read `qrf/trading/simulator/engine.py`'s `ExecutionSpec` docstring and
`EventEngine.simulate`'s per-event stop/target resolution block (search
`ARCH-NP-004` in that file) — that is the whole capability in one place.

## 10. Risks

- **Silent per-row stop degradation** (§4, "missing/NaN per-event stop
  value"): a hypothesis that declares `event_stop_column` but is fed a row
  with a NaN value gets a *silent* no-stop trade for that one row, not an
  error. No test exercises this path (deliberately, per §4) — worth a DEVQ or
  an explicit ruling if a future hypothesis actually hits it in practice.
- **`scripts/rebuild_bulk.py`'s h007 gap (`NOTE-NP-003`)** means the *general*
  "rebuild everything and check" story is currently broken for anyone running
  `rebuild_bulk.py` directly (not just my test) — until someone extends
  `_LINEAGE_DATASET`, any full-repo rebuild audit needs the same workaround
  this session used.
- **CLAUDE.md's session-close `gen_state.py` step could not run** (`NOTE-NP-004`):
  its target, `docs/handover/AI_PROJECT_STATE.md`, has not existed since a
  `docs/` restructure at commit `a6823c3` archived it to
  `docs/archive/gen1/handover/AI_PROJECT_STATE.md`, and `gen_state.py` only
  updates an existing file in place. Left unfixed (out of write scope; and
  hand-writing the target myself would violate the "only sanctioned way to
  touch it" rule the same step depends on) — every session's DERIVED status
  rows (test count, journal count, branch) have therefore been stale since
  that restructure, not just this one.
- I did not run the state machine's own CI check on `sprint/NP-S2` — that
  happens after push, outside this session's visibility.
