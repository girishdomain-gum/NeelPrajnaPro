# ARCH-NP-005 — Fix NOTE-NP-003: rebuild_bulk.py's missing h007 lineage dispatch
*Sealed instruction. Owner ruling 2026-07-31: "Fix NOTE-NP-003." Mechanical, isolated, independently testable — per the Owner's own characterization. Architect role · session: Opus 5, claude.ai interface, filesystem connector.*

---

## 1. The defect, as found (NOTE-NP-003, verbatim source)

`scripts/rebuild_bulk.py`'s `_LINEAGE_DATASET` dispatch (and its sibling `_events_for_lineage`) covers only `h001_fvg_follow_through` / `h002_fvg_intraweek_follow_through` / `h003_dow_monday_drift` / `h004_dow_monday_drift_v2`. `rebuild_all()` iterates **every** verdict in the journal unconditionally, so since the h007 verdict landed in NP-S1, **any invocation of `rebuild_all()` now fails** with `SystemExit: no dataset registered for lineage 'h007_np_liquidity_sweep_v1_1'` — on any change or none.

**Confirmed pre-existing and unrelated to WO-P** (empty `git diff` against the file). Two tests already fail from this, independent of any WO-P change: `test_rebuild_bulk_s9.py::test_rebuild_all_matches_recorded_manifests` (expects 4 recorded lineages, finds 5) and `::test_rebuild_byte_stable_across_process_restart` (subprocess rebuild raises the same `SystemExit`).

## 2. Fix

Add `h007_np_liquidity_sweep_v1_1` to `_LINEAGE_DATASET` (and `_events_for_lineage` if it dispatches separately), pointing at the same pipeline pieces WO-P's own AC-1 test already drives directly: `ingest_h07_m5_vantage.build_m5_bars` for bars, the v1.1 detector for events. **Reuse, do not reimplement** — the AC-1 test in `tests/scripts/test_ac1_engine_parity_np004.py` is the reference for exactly which calls produce the byte-identical result; read it before writing the dispatch entry.

## 3. Acceptance

- `test_rebuild_bulk_s9.py::test_rebuild_all_matches_recorded_manifests` passes with all 5 lineages (4 pre-existing + h007).
- `::test_rebuild_byte_stable_across_process_restart` passes.
- A new regression test: `rebuild_all()` invoked directly reproduces the h007 verdict's trade manifest byte-identically (reuse WO-P's AC-1 comparison logic; do not duplicate it — import or parameterize).
- Full suite green: `pytest tests/ -q`.
- Kernel firewall green: `pytest tests/test_kernel_firewall.py -q`.

## 4. Non-goals

No changes to `qrf/**` or the engine — this is a `scripts/`-only fix. No re-registration, no new verdict, no ledger writes. Do not touch the h001–h004 dispatch entries beyond what's needed to add h007 alongside them.

## 5. Branch and handover

Work on **`sprint/NP-S2`** (already open, scoped to WO-P plus this fix per the Owner's G1 ruling). Commit early, push often. On completion, publish `ops/aro/handovers/ARCH-NP-005/HANDOVER.md` in the standard ten-section shape.

---
*Anchor: **mechanical, isolated, independently testable — fixed now because there was never a reason to wait.***
