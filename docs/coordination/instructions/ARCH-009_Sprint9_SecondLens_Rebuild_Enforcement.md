# ARCH-009 · Sprint 9 instruction · **DRAFT — awaiting Owner review** · 2026-07-25
Author: architect (fable) · For: developer (claude-code)
Status: DRAFT. §§1–3 are Owner-approved-in-principle carried items
(GO-S8). §4 is a PROPOSAL requiring three Owner decisions (marked ◆)
before this instruction is finalized. Do not boot on a DRAFT.

Theme: **make evidence portable, make honesty enforceable, open the
second eye.** Sprint 8 built the gates; Sprint 9 supplies what the
gates were built to demand — rebuildable artifacts, sealed placebo
declarations, and the independent feed without which nothing can ever
graduate.

## T0 — boot + note
Boot per CLAUDE.md (NEW session, own branch, own S9-1 log). Append a
`note` record: sprint 9 open, refs to this instruction and GO-S8.

## §1 — rebuild-bulk for verdict_trades (carried debt, now due)
Extend the rebuild path (scripts/judge_h001.py --rebuild-bulk lineage
or a dedicated scripts/rebuild_bulk.py — your choice, DEVQ if unsure)
so that EVERY verdict_trades.* dataset named by a journal
bulk_manifest can be regenerated from (journal + full-bars parquet)
alone, by deterministically re-running the recorded experiment
(events → splits → fills exactly as the verdict pipeline did — reuse
_pipeline, never a parallel implementation).
BINDING: the rebuilt parquet's sha256 MUST equal the manifest's
file_sha256, asserted in the script, else loud failure (a rebuild that
"mostly matches" is a fabrication). Prove it on all three lineages
(h001/h002/h003) on main — after this lands, the S8 worktree is no
longer load-bearing and may be pruned by the Owner.
AC: rebuild all three on a clean main; hashes assert-equal; property
test that a rebuild is byte-stable across process restarts.

## §2 — placebo_method under the seal (DEVQ-018 ADDENDUM, forward-binding)
1. HypothesisRegistry: schema bump — any NEW hypothesis whose claim
   will be judged with a placebo MUST carry `placebo_method` (one of
   the DEVQ-018 ruled nulls) in its YAML; content-hash seal covers it.
   Registration REFUSES an unknown method. Wave-1 records are
   grandfathered exactly as sealed (no migration, no rewrite).
2. PlaceboBattery.run: REFUSES if the sealed method disagrees with the
   requested method (SchemaViolation naming both).
3. Tests: registry refusal, judge refusal, grandfather path.
AC: a new toy registration without placebo_method (when placebo
requested) is refused; mismatch refused; H-002/H-003 untouched.

## §3 — HC capture tool rev 2 (display only; owed from REV-S8 OBS-2)
ivf/mt5/IVF_HC_Trades.mq5 is ARCHITECT-owned — the Developer does NOT
edit it. This section is a placeholder so the sprint plan is complete:
the Architect ships rev 2 (caption line 1 theme-safe color; all caption
lines ≤63 chars; MON dow verdict on its own line) during a write
window. Developer: no action.

## §4 — PROPOSAL: the second lens + data extension + H-004 ◆◆◆
The program's stated bottleneck (GO-S8): no promotion is possible until
an independent feed exists. This section opens that eye. It requires:

◆ DECISION 1 (Owner): provide a SECOND, independent XAUUSD H1 source —
  a different broker's MT5 export (not Winprofx), same 2024 span at
  minimum. Independence means a different originating venue, not a
  re-download.
◆ DECISION 2 (Owner): provide 2025 H1 data from the PRIMARY feed, to
  give H-003's successor statistical room (28 Mondays cannot clear a
  40 floor; ~2 years can). New data is ingested under NEW window
  records; the 2024 VIRGIN reserve stays untouched and its boundary
  unmoved.
◆ DECISION 3 (Owner): approve registering H-004 (below) as Wave 2.

If approved, Developer scope:
1. Ingest the second feed (ingest_report v2, params recorded; new
   dataset + manifest). Compute the OVERLAP against the primary per
   DEVQ-020: shared-timestamp bars, agreement on OHLC within a
   declared tolerance. **The agreement threshold and tolerance are
   PRE-REGISTERED in a note record BEFORE the overlap is computed**
   (DEVQ-020 binding — this ordering is the whole point). Then append
   the first `second_lens` record ({source_name, overlap_manifest,
   agreement_summary}).
2. Ingest primary-feed 2025 (Decision 2): new TRAINING window; a NEW
   VIRGIN slice from the extension is designated at ingest per A1
   (typed-phrase protected) so the reserve grows with the data.
3. Register + judge **H-004 h004_dow_monday_drift_v2** (placebo-first,
   per §2 with placebo_method: entry_time_shuffle sealed in YAML):
   Monday long at next-open after the marker, exit at the OPEN of the
   LAST bar whose open falls on the same UTC Monday (the DEVQ-019
   successor design — a calendar exit, not a bar count), judged on the
   2024+2025 TRAINING window, fresh lineage. Thresholds pre-registered
   in the YAML before any run; min_n ≥ 80 proposed. INTERPRETATION
   GUARD baked into the YAML's outcome_interpretations: given OBS-1,
   a PASS claims "Monday beats random timing", and the placebo ceiling
   at the deflated alpha is the arbiter of that claim.
AC (§4): second_lens record exists with pre-registered-then-computed
agreement; new windows ingested with VIRGIN extension designated;
H-004 judged with its placebo; all three tri-states acceptance-valid.
NOTE: even a clean H-004 PASS does NOT promote unless every gate holds
— that is the machinery working, either way.

## Acceptance (sprint)
§1 hashes assert-equal on all three lineages · §2 refusals tested,
Wave 1 grandfathered · §4 (if approved) second_lens + windows + H-004
judged placebo-first · journal chain GREEN · VIRGIN(s) untouched ·
firewall GREEN · session logs per session · DEVQs to inbox/OPEN at any
genuine decision point.

## Sprint close (Architect duties, recorded for symmetry)
IVF-S9: drill first (planted rebuilt-parquet byte-drift; planted
overlap-computed-before-threshold), then checks (rebuild determinism;
placebo_method enforcement audit; second-lens overlap recomputation
with ordering audit; H-004 verdict anchor). HC with the rev-2 tool.
REV-S9 → Owner Go/No-Go → GO-S9 → handover rewrite → ARCH-010.
