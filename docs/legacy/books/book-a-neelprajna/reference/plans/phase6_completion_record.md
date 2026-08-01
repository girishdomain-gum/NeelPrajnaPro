# Phase 6 — completion record

- Phase: 6, Sequential Strategy Engine (SSE)
- Closed at: v5.9.0
- Design authority: `docs/plans/phase6_sequential_strategy_engine_design_v1.0.md`
- Constraint discovered mid-phase: `docs/adr/ADR-004-evaluation-cadence.md`
- Versions: 5.6.0 (6a) → 5.7.0 (6b) → 5.8.0 (6c) → 5.9.0 (grammar close-out)

## 1. What shipped

| stage | version | what | state |
|---|---|---|---|
| 6a foundations | 5.6.0 | `Engine/SequenceEngine.mqh` (pure FSM), `Apps/SeqCodex.mqh` (parser/normaliser/hash), shadow racing in NPSU | **validated on real data** |
| 6b live apply | 5.7.0 | `Apps/SeqLive.mqh` — same FSM on the real path, two-key safety, dry-run log | shipped disarmed, **not yet exercised** |
| 6c compiler + A/B | 5.8.0 | `SQX_CompileStatic()`, `SQX_RegisterStaticTwins()` — every static universe races a compiled 1-step twin | shipped, **measurement not yet run** |
| grammar close-out | 5.9.0 | `BE=ON\|OFF` enters the grammar and the hash | shipped |

## 2. What the first real run proved (v5.8.0, XAUUSD M1, 2026.07.01–22)

**Identity holds (D9).** The EA reproduced all four descriptor hashes computed
independently by `tools/seqgen.py`. The parser, normaliser and FNV-1a-32 agree
byte-for-byte between tool and EA.

**The FSM works.** 72 advances, 54 resets (39 window expired, 15 invalidator),
multi-step chases progressing `T4 → S1/3`, `T3 → S2/3`. Trade accounting
balances exactly: TrendPullback 22 starts − 5 resets = 15 trades + 2 skipped.

**Bar-close sampling cost zero entries on M1.** `Mirror1Step_T1_B1B6` and its
static twin `T1_B1B6` took the SAME 15 trades at the SAME open times to the
minute. This is the ADR-004 C1 concern answered in the favourable direction —
on M1, at least.

**A sequence beat every static universe.** `TrendPullback_Fibo`: 15 trades,
53.3% win, **+13.0 R**, against `T1_base` +2.97 R (142 trades) and `MIRROR`
−5.79 R. Achieved with break-even disabled.

**And it exposed a real defect.** `Mirror1Step` scored −3.00 R against its
twin's +5.84 R on identical trades, purely because the 6a grammar had no
break-even: the static universe protected 7 of 15 trades, the sequence none.
That is what v5.9.0 fixes, and it is why the experiment is worth more than
the result.

## 3. What is deliberately NOT in Phase 6

**Unification** — retiring `_NPSU_TryEnter` and routing the real path through
compiled sequences — was the original 6c goal. It is re-scoped to Phase 7,
not abandoned, for the reason recorded in ADR-004 §2 C2: its acceptance test
("prove the deal list unchanged") cannot pass while the two evaluators sample
at different moments. Shipping it without that gate would mean replacing the
law that trades the account on the strength of an argument rather than a
measurement.

Also deferred: the tick-capable FSM split (ADR-004 §4), a panel row for
sequence state, timeframe-aware steps, and `SUniverseRow` sequence fields.

## 3b. MEASURED (v5.9.0, run 40906) — the 6c question is answered

The twin A/B ran under every-tick modelling with break-even matched on both arms:

    7 static universes vs their compiled 1-step twins
    trades  597 -> 596        net R  -3.806 -> -2.847
    five of seven pairs identical to three decimals

    T1_B1B6 (legacy law) = Mirror1Step_T1_B1B6 (.seq) = T1_B1B6_1S (twin)
    all three: 17 trades, 64.7% win, +5.565 R, 3 TP / 6 SL / 8 BE

**The cadence cost is zero**, because every gate is computed on the closed bar, so tick-level
evaluation re-reads a value that only changes at bar edges. ADR-004 C2 is lifted and the
tick-mode split is not being built. See `docs/adr/ADR-004-amendment-summary.md`.

This licenses unification (Phase 7) on measurement rather than argument. It licenses nothing
about strategy selection — those samples are 15–18 trades.

## 4. Entry criteria for Phase 7

Phase 7 opens on data, not on a date. Three runs are required first:

1. **The 6c measurement** — `PHASE6_2_ALL_DRYRUN.ini` with the twins active.
   Compare each `_1S` twin against its source on trade count and net R. With
   v5.9.0 the twin inherits its source's RR, trail AND break-even, so any gap
   is caused by cadence alone. This decides whether the tick-mode split is
   needed or whether bar-close is free.
2. **The 6b dry-run** — `SEQL | WOULD FIRE` lines over a meaningful period,
   to see what the real path would have done.
3. **Re-run the four `.seq` files under v5.9.0**, to confirm the break-even
   fix closes the `Mirror1Step` gap and to re-measure `TrendPullback_Fibo`
   with protection enabled.

## 5. Standing rules earned in this phase

- **ADR-004 §5**: any new or moved evaluator must state its cadence, and
  "deal list byte-identical" is a legal acceptance gate only when old and new
  paths are evaluated at the same moments.
- **Grammar and tool move together.** `SQX_Normalise()` and
  `seqgen.py::normalised_descriptor()` are one contract in two languages. A
  change to either without the other silently breaks strategy identity.
- **Management belongs in the hash.** RR, TRAIL and now BE all affect what a
  trade is worth, so all three are part of what a strategy IS. A comparison
  is only valid when the two sides differ in exactly one thing.

## 6. Test kit

`tests/phase6/` — `.seq` files, config generator, README with the full
procedure, expected journal output and troubleshooting. The `.seq` files
carry their first-run results in their headers, so the next person sees what
happened last time before running them again.
