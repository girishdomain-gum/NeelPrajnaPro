# HANDOVER — ARCH-NP-005, Fix NOTE-NP-003 (rebuild_bulk.py missing h007 lineage)

*Developer session · claude-code · 2026-07-31. Instruction: `ops/ARCH-NP-005_fix_rebuild_bulk_h007.md`, fixing `docs/coordination/notes/NOTE-NP-003_rebuild_bulk_missing_h007_lineage.md` (raised by the prior WO-P session).*

---

## 1. What was asked

`scripts/rebuild_bulk.py`'s `_LINEAGE_DATASET` dispatch (and its sibling
`_events_for_lineage`) covered only h001–h004. `rebuild_all()` iterates every
verdict in the journal unconditionally, so since the h007 verdict landed in
NP-S1, **any invocation now raised** `SystemExit: no dataset registered for
lineage 'h007_np_liquidity_sweep_v1_1'`. Fix: add h007 to both dispatch
tables, pointing at the same pipeline pieces WO-P's own AC-1 test already
drives directly — reuse, don't reimplement. Scope: `scripts/**` only; no
`qrf/**` or engine changes; no re-registration, no new verdict, no ledger
writes. Acceptance: both currently-failing `test_rebuild_bulk_s9.py` tests
pass; a new regression test proves `rebuild_all()` reproduces the h007
verdict's manifest byte-identically; full suite green; kernel firewall green.

## 2. What I did

Read `ARCH-NP-005`, `NOTE-NP-003` (the finding it fixes), and
`tests/scripts/test_ac1_engine_parity_np004.py` (the reference for exactly
which calls produce the byte-identical h007 result) before touching
anything. Traced the h007 pipeline: bars come from
`ingest_h07_m5_vantage.build_m5_bars(TICK_DIR)` against raw Vantage ticks
(dataset name `xauusd_m5_vantage`, `NP-ADR-008` §5 v1.1), and its
`bulk_manifest` record already exists in the journal from NP-S1 — but, like
every other bars dataset, the actual gitignored parquet file does not exist
on a fresh worktree checkout. `rebuild_all()`'s existing `_bars()` closure
calls `bulk.read()`, which requires the file on disk, hash-verified against
that manifest — so a plain dispatch-table entry wasn't enough; h007 also
needed its own bars-rebuild step, exactly like `rebuild_bars()` (h001-family,
via `judge_h001.rebuild_bulk`) and `rebuild_lens_bars()` (h004, via
`ingest_lens_feeds_s9.rebuild`) already provide for their datasets.

Added `ingest_h07_m5_vantage.rebuild_bulk()`, mirroring `judge_h001.
rebuild_bulk`'s pattern: find the existing `bulk_manifest` for
`xauusd_m5_vantage`, rebuild the bars table from raw ticks (`build_m5_bars`,
untouched), write it to the manifest's own path, and hash-verify via
`bulk.read()` — raising `SystemExit` on any mismatch, never silently. To
avoid two independent copies of the exact `pa.table(...)` construction
(ingest-time vs. rebuild-time), factored it into a small `_bars_to_table`
helper both `_run_ingest` and `rebuild_bulk` now call — the ingest-time
write is unchanged in every observable way (same columns, same dtypes).

Registered `h007_np_liquidity_sweep_v1_1` in `rebuild_bulk.py`'s
`_LINEAGE_DATASET` (pointing at the h007 ingest's own `DATASET` constant,
`xauusd_m5_vantage`) and in `_events_for_lineage` (calling
`LiquiditySweepDetector().detect(...)`, filtered to the sweep event type —
the exact two calls `test_ac1_engine_parity_np004.py`'s own h007 test
already makes). Wired `rebuild_h007_bars()` (aliased from the new
`ingest_h07_m5_vantage.rebuild_bulk`) into `rebuild_all()`'s bars-rebuild
step, alongside the existing two.

## 3. What changed

| File | Change |
|---|---|
| `scripts/ingest_h07_m5_vantage.py` | New `_bars_to_table()` helper (extracted, no behavior change to `_run_ingest`) and new `rebuild_bulk()` function that reconstructs the gitignored `xauusd_m5_vantage` parquet from raw ticks and hash-verifies it against the existing manifest. |
| `scripts/rebuild_bulk.py` | Loads `ingest_h07_m5_vantage` as a sibling module; adds `rebuild_h007_bars` (called from `rebuild_all()`); adds `h007_np_liquidity_sweep_v1_1` to `_LINEAGE_DATASET`; adds the h007 branch to `_events_for_lineage` (`LiquiditySweepDetector`, filtered to the sweep event type); docstring updated to name all five lineages instead of three. |
| `tests/scripts/test_rebuild_bulk_s9.py` | `test_rebuild_all_matches_recorded_manifests`'s hardcoded manifest count updated `4 → 5` (the h007 verdict already had a `trades_manifest` in the journal — this assertion was simply stale, not something my fix changed). New regression test `test_rebuild_all_reproduces_h007_manifest_byte_identically`, named and isolated on top of the generic per-lineage loop above it. |
| `tests/scripts/test_ac1_engine_parity_np004.py` | `test_ac1_h001_through_h004_reproduce_byte_identically`'s skip condition changed from "not yet in `_LINEAGE_DATASET`" (a proxy for "is h007") to an explicit lineage-name check — h007 IS now registered, so the old proxy would have pulled it into the "h001-h004 only" loop and broken its hardcoded `checked == 4`. |
| `ops/aro/handovers/ARCH-NP-005/HANDOVER.md` | This file. |

## 4. Decisions made (no DEVQ raised — reasoning below; flag me if any should have been one)

- **A dedicated `rebuild_h007_bars()` step, not just a dispatch-table entry.**
  ARCH-NP-005 §2 named the two dispatch tables explicitly, but a plain entry
  in `_LINEAGE_DATASET` alone would still raise on a fresh worktree — `_bars()`
  calls `bulk.read()`, which needs the actual parquet bytes on disk, and
  `datastore/bulk/` is entirely gitignored. h001 and h004 already needed (and
  have) their own bars-rebuild functions for exactly this reason; h007 is not
  structurally different, so I gave it the same treatment rather than a
  half-fix that would only work on a machine that happened to already have
  the file locally.
- **`_bars_to_table` extraction in `ingest_h07_m5_vantage.py`.** Small,
  in-file-only refactor (still `scripts/**`) so the rebuild path and the
  original ingest path share one table-construction call instead of two
  copies that could silently drift apart — the same reuse discipline
  `judge_h001.py` and `ingest_lens_feeds_s9.py` already follow for their own
  datasets.
- **Sweep event type derived, not hardcoded.** `_events_for_lineage`'s h007
  branch computes `f"{LiquiditySweepDetector.instrument_id}.sweep"` rather
  than the literal string `test_ac1_engine_parity_np004.py` uses — same
  value, but tied to the detector's own class attribute so a future rename
  of `instrument_id` can't silently desync the two.
- **Updating the two test files WO-P wrote, not just the scripts.** The
  ARCH-NP-005 instruction's headline scope note says "scripts/** only," but
  its own §3 acceptance criteria requires `test_rebuild_bulk_s9.py`'s
  existing tests to pass with 5 lineages and a *new* regression test — both
  necessarily live under `tests/`. I read "scripts/** only" as scoping the
  *fix itself* (no `qrf/**`, no engine changes), not as forbidding the test
  edits its own acceptance criteria requires; WO-P's own precedent (adding
  `tests/scripts/test_ac1_engine_parity_np004.py`) treated `tests/**` as
  fair game the same way. The `test_ac1_engine_parity_np004.py` skip-condition
  fix was not explicitly asked for, but was a direct, mechanical consequence
  of the dispatch-table addition (that test's own "not yet in
  `_LINEAGE_DATASET`" proxy for "is h007" stopped meaning that the moment
  h007 was registered) — leaving it broken would have violated "never weaken
  a failing invariant test" in the other direction (a test that now fails
  for a reason unrelated to what it's actually checking).

## 5. What I did not do

- Did not touch `qrf/**` or `qrf/trading/simulator/engine.py` — no engine or
  Kernel changes, per the non-goals.
- Did not re-register H-007, run any new judge, or write to
  `datastore/journal/**` — verified by explicit `len(store)` before/after
  assertions in the new regression test, not just asserted in prose.
- Did not touch the h001–h004 dispatch entries beyond what was needed to
  add h007 alongside them (per the non-goals' explicit instruction).
- Did not add a `--rebuild-bulk` CLI flag to `ingest_h07_m5_vantage.py`
  (unlike `judge_h001.py`/`ingest_lens_feeds_s9.py`, which expose one) —
  `rebuild_bulk.py` calls the new `rebuild_bulk()` function directly, and
  ARCH-NP-005 didn't ask for a standalone CLI entry point; adding one felt
  like scope creep beyond the stated fix.
- Did not fix `tests/adapters/test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags`
  (missing external CSV, `IVF_S2_XAUUSD_PERIOD_H1.csv`) — confirmed
  pre-existing and unrelated (same failure WO-P's session documented; this
  session touched no file that test imports).

## 6. Open questions

None raised as a DEVQ — the fix was mechanical and isolated exactly as
ARCH-NP-005 characterized it, and the one scope ambiguity (test file edits
under "scripts/** only") resolved cleanly against the instruction's own
acceptance criteria and WO-P's precedent (§4).

## 7. Evidence of done

- `tests/scripts/test_rebuild_bulk_s9.py::test_rebuild_all_matches_recorded_manifests` —
  passes; asserts all 5 anchored lineages (h001/h002/h003/h004/h007) rebuild
  to their manifest's exact sha256, and the ledger is unchanged.
- `tests/scripts/test_rebuild_bulk_s9.py::test_rebuild_byte_stable_across_process_restart` —
  passes; two independent fresh-interpreter subprocess rebuilds of `rebuild_all()`
  produce identical bytes, matching the recorded manifests (this is the test
  that directly proves `rebuild_all()` no longer raises on invocation).
- **New regression test** — `tests/scripts/test_rebuild_bulk_s9.py::
  test_rebuild_all_reproduces_h007_manifest_byte_identically`: calls
  `rebuild_bulk.rebuild_all()` directly, asserts the h007 manifest ref is in
  the returned list (proves dispatch, not just absence-of-crash), and
  independently re-hashes the rebuilt file against the recorded sha256 (reusing
  the same imported `_sha256_file`/`BulkStore.path_for` this file already
  uses, not a re-implementation of the comparison) plus `bulk.read()`'s own
  hash gate.
- `.venv/Scripts/python.exe -m pytest tests/test_kernel_firewall.py -q` →
  8 passed.
- `.venv/Scripts/python.exe -m pytest tests/ -q` → 887 passed, 1 failed:
  `test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags` (pre-existing,
  missing external CSV, unrelated — same failure documented in WO-P's
  session log and confirmed again here by inspection).

## 8. What's next

- Nothing blocking. `scripts/rebuild_bulk.py` now covers every lineage
  currently in the journal; a future new hypothesis lineage will hit the
  same loud `SystemExit` this one did until its own dispatch entry (and, if
  its bars aren't already covered by an existing rebuild step, its own
  bars-rebuild function) is added — same pattern, same place.
- `test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags`'s missing CSV
  remains open (not this instruction's concern; flagged again for whoever
  eventually decides whether it needs a DEVQ or just a placed fixture file).

## 9. How to verify me

```bash
git fetch origin
git log --oneline -5 sprint/NP-S2          # this session's commit should be at the tip
.venv/Scripts/python.exe -m pytest tests/scripts/test_rebuild_bulk_s9.py tests/scripts/test_ac1_engine_parity_np004.py tests/test_kernel_firewall.py -q
.venv/Scripts/python.exe -m pytest tests/ -q
# Expect: all green except test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags
# (pre-existing, missing external CSV, unrelated to this fix).
```
`scripts/rebuild_bulk.py`'s `_LINEAGE_DATASET` dict and `_events_for_lineage`
dispatch are the whole fix in one place; `scripts/ingest_h07_m5_vantage.py`'s
`rebuild_bulk()` is the new bars-rebuild step it depends on.

## 10. Risks

- **A future lineage needs the same two-part treatment** (dispatch entry +
  its own bars-rebuild step if its dataset isn't already covered) — this fix
  didn't generalize that into a single registration point; it followed the
  existing per-dataset-function pattern (`rebuild_bars`/`rebuild_lens_bars`/
  `rebuild_h007_bars`, three separate aliases) rather than refactoring it
  into something more declarative. Worth a DEVQ if a sixth lineage arrives
  and the pattern starts feeling repetitive.
- **Raw tick source dependency:** `rebuild_h007_bars()` (and therefore
  `rebuild_all()` as a whole, from this fix onward) now requires
  `F:\NeelPrajna\Validation\Stage2\parquet` to exist on the machine running
  it — present on this machine, confirmed by the passing subprocess test,
  but the same class of external-data dependency `judge_h001.rebuild_bulk`
  already has for its own CSV. Not new risk, just extended to a second
  external source.
