# NOTE-NP-003 · Sprint NP-S2 (WO-P) · 2026-07-31
Author: developer (claude-code)
Refs: `scripts/rebuild_bulk.py` (`_LINEAGE_DATASET`, `rebuild_all`); `tests/scripts/test_rebuild_bulk_s9.py`; `ops/ARCH-NP-004_WO-P_execution_parity.md` §9 addendum (write scope).
Tag: discovery (pre-existing test break, unrelated to WO-P)

## Finding
While building WO-P's AC-1 byte-identity reproduction test
(`tests/scripts/test_ac1_engine_parity_np004.py`), calling
`rebuild_bulk.rebuild_all()` raised `SystemExit: no dataset registered for
lineage 'h007_np_liquidity_sweep_v1_1'`. `scripts/rebuild_bulk.py`'s
`_LINEAGE_DATASET` dispatch (and its sibling `_events_for_lineage`) only
covers `h001_fvg_follow_through` / `h002_fvg_intraweek_follow_through` /
`h003_dow_monday_drift` / `h004_dow_monday_drift_v2` — it was never extended
to the h007 lineage, and `rebuild_all()` iterates **every** verdict in the
journal unconditionally, so **any** invocation now fails, on any change or
none. Confirmed pre-existing and unrelated to this work order:
`scripts/rebuild_bulk.py` is untouched by any WO-P edit (`git diff` against
it is empty), and `tests/scripts/test_rebuild_bulk_s9.py` — which touches
none of the files WO-P changed — fails the same way
(`test_rebuild_all_matches_recorded_manifests`:
`assert len(recorded) == 4` now finds 5, since the h007 verdict is in the
journal; `test_rebuild_byte_stable_across_process_restart`: the subprocess
rebuild raises the same `SystemExit`). The h007 verdict was already in the
journal (T-04x, NP-S1) before this session started; the script simply never
caught up.

## Disposition
Did not fix `scripts/rebuild_bulk.py`. WO-P's write scope is `qrf/**` and
`tests/**` (ARCH-NP-004 §9 addendum); `scripts/` is neither, and this gap has
nothing to do with per-trade stops or R-multiple targets. WO-P's own AC-1
test drives the same underlying pipeline pieces
(`rebuild_bulk.rebuild_bars`/`rebuild_lens_bars`/`_LINEAGE_DATASET`/
`_events_for_lineage`, `EvidenceBattery.evaluate`/`trades_table` — reused,
never re-implemented) directly, filtering to the four lineages
`_LINEAGE_DATASET` actually knows, instead of calling the broken
`rebuild_all()` orchestrator. h007 is proven byte-identical separately, by
the same evaluate/trades_table pipeline `scripts/judge_h007_prediction_s1.py`
used originally.

## What I have NOT done
Not edited `scripts/rebuild_bulk.py`, not weakened
`tests/scripts/test_rebuild_bulk_s9.py`'s assertions (`RED` stands, per
CLAUDE.md's "never weaken a failing invariant test" rule — this is a real,
pre-existing defect, not a wrong invariant). A DEVQ naming this belongs to
whoever owns `scripts/` maintenance; flagging it here rather than raising a
DEVQ myself since it does not block WO-P and touches no file this instruction
governs.
