# ARCH-009 · Sprint 9 instruction · **FINAL** · 2026-07-25
Author: architect (fable) · For: developer (claude-code)
Status: FINAL. Owner approved 2026-07-25: §§1–3 without change; §4
Decisions 1/2/3 all GO, with one binding amendment to Decision 1 (the
independence definition below) and one recorded architecture note (the
lens-generality note at the end). Owner's assessment of record: "ARCH-009
is approved in principle … Sprint 9 doesn't broaden QRF indiscriminately;
it completes an important capability that Sprint 8 deliberately left
unavailable: independent corroboration before promotion."

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

## §4 — the independent lens + data extension + H-004 (Owner-approved)
The program's stated bottleneck (GO-S8): no promotion is possible until
an independent feed exists. This section opens that eye. All three
decisions are GO.

DECISION 1 (GO, with the Owner's amendment now BINDING): the Owner
provides a second XAUUSD H1 source. **Independence is defined by the
ORIGIN of the market observations, not by the broker label on the
export: the second feed must come from an independently generated
market data production process, materially different from the
primary's. A re-export, mirror, cache, or repackaging of the primary
feed does NOT qualify.** Independence is a SPECTRUM, recorded, not a
binary: tiers are (i) broker-independent (different broker, possibly
shared liquidity provider), (ii) LP-independent (different liquidity
sourcing), (iii) venue-independent (different exchange/venue). At
provision time the Owner states the source's provenance (broker,
platform, what is known of its liquidity sourcing); the Developer
records the DECLARED tier — tier=UNKNOWN is acceptable and recorded
honestly, never silently upgraded. The tier lives in the ingest note
and in the lens record's source_name context so future consumers can
weight agreement by depth of independence.
DECISION 2 (GO): primary-feed 2025 data under NEW window records; the
2024 VIRGIN reserve stays untouched and its boundary unmoved.
DECISION 3 (GO): H-004 registered as Wave 2, with the Owner's
emphasis of record: the claim under test is "Monday beats RANDOM
TIMING", not "Monday is profitable".

Developer scope:
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
agreement AND a declared independence tier; new windows ingested with
VIRGIN extension designated; H-004 judged with its placebo; all three
tri-states acceptance-valid.
NOTE: even a clean H-004 PASS does NOT promote unless every gate holds
— that is the machinery working, either way.

## Architecture note of record (Owner, 2026-07-25 — no S9 scope change)
The "second lens" is the FIRST IMPLEMENTATION of a more general
concept: **Independent Observation Lenses**. Future lenses (order
flow, volume profile, macro, news, options…) may join without changing
the scientific engine — only the number of observation sources and the
cross-lens agreement layer grow. Naming and schemas introduced this
sprint should therefore avoid baking "exactly two" into anything
structural: `second_lens` remains the sealed DEVQ-020 record type for
THIS lens, but new code comments and any new identifiers should speak
of independent lenses generally. Sprint 9 stays strictly two-feed.

## Acceptance (sprint)
§1 hashes assert-equal on all three lineages · §2 refusals tested,
Wave 1 grandfathered · §4 second_lens (declared tier) + windows + H-004
judged placebo-first · journal chain GREEN · VIRGIN(s) untouched ·
firewall GREEN · session logs per session · DEVQs to inbox/OPEN at any
genuine decision point.

## ADDENDUM (Architect, 2026-07-25, pre-boot) — VIRGIN exclusion from overlap
The second feed's export spans the VIRGIN months. BINDING: the §4
overlap/agreement computation runs on the TRAINING-window timespan
ONLY — timestamps inside any VIRGIN-designated window (2024's reserve
and the new 2025-extension reserve alike) are EXCLUDED from the
cross-feed comparison and from the agreement_summary. A bar-integrity
comparison is not a hypothesis evaluation, but the reserve's value is
that NOTHING computes on it without the typed-phrase authorization —
no exceptions by category. The exclusion is stated in the
pre-registration note (before overlap is computed) and the IVF will
audit it. The raw second-feed CSV/parquet may of course CONTAIN those
rows — storage is not computation; the exclusion applies to the
overlap/agreement calculation and anything derived from it.

## ADDENDUM 2 (Architect, 2026-07-26, pre-boot) — CLOCK DOCTRINE
The QRF_Data_Export provenance measured the PRIMARY terminal at
server-vs-GMT = +10800 s (2026-07). FINDING: the primary feed's
timestamps are BROKER SERVER TIME (NY-close-aligned, GMT+2 winter /
GMT+3 summer pattern), NOT absolute UTC. The historical "UTC verified"
claim was an INTERNAL-consistency verification only — chart and CSV
share the server clock, so HC offset-0 matches could never test the
absolute clock. Corroboration from our own data: no Sunday bars +
Mondays beginning at the 01:00-open bar is the signature of an
EET-style clock, not UTC. Consequences, BINDING:
(a) NO ledger impact: every existing verdict/scan/burn computed on one
    consistent timeline; nothing is re-run. Prose labels saying "UTC"
    for primary-feed timestamps are re-read as "server time"; H-003's
    "Monday" is server-Monday (begins ~Sun 22:00 true UTC).
(b) §4 overlap MUST establish clock alignment BEFORE agreement is
    measured, and the alignment procedure is PRE-REGISTERED in the
    same note as the agreement threshold. Alignment is PIECEWISE BY
    CLOCK ERA (2026-07-26 refinement, from the delivered feeds: the
    primary runs +2h winter / +3h summer while the second feed is UTC
    year-round, so no single constant shift can align the full span —
    the per-bar stamp-difference distribution is bimodal by design):
    compute the per-bar stamp-difference of matched market hours,
    segment the timespan at the primary's DST-transition instants
    (the shift-change points), and record PER ERA the chosen
    integer-hour shift (candidates at least {0, ±1h, ±2h, ±3h}),
    chosen by maximum shared-timestamp count within that era over the
    TRAINING timespan. The era boundaries, per-era shift tables, and
    winners are all RECORDED in the agreement_summary notes. Within
    any era, if the runner-up shift comes within 5% of the winner's
    shared count, STOP and DEVQ.
(c) Both feeds' measured offsets + the caveat that historical DST-era
    offsets may differ are recorded in the ingest params (the
    provenance sidecars are the source documents).
(d) Tally: Architect bug #16 — an absolute claim ("UTC verified")
    resting on a circular test; self-caught by the provenance tool
    before the second feed could turn it into a real error.

## Sprint close (Architect duties, recorded for symmetry)
IVF-S9: drill first (planted rebuilt-parquet byte-drift; planted
overlap-computed-before-threshold), then checks (rebuild determinism;
placebo_method enforcement audit; second-lens overlap recomputation
with ordering audit; H-004 verdict anchor). HC with the rev-2 tool.
REV-S9 → Owner Go/No-Go → GO-S9 → handover rewrite → ARCH-010.

## COMPLETION REPORT (developer)
Developer: claude-code · Closed: 2026-07-26 (session S9-3) · Branch:
`claude/arch-009-hypothesis-schema-v3-cebf6a` (merged to main).

All sections DONE; sprint AC met. Journal 73 records, chain GREEN;
both VIRGIN reserves UNTOUCHED; firewall 8/8 GREEN; full suite GREEN
(843 tests: 835 baseline + 8 new §4.1 cases); ruff clean.

- **§1 rebuild-bulk** (S9-1): every `verdict_trades.*` regenerates from
  (journal + bars) with sha256 assert-equal, all four lineages
  (h001/h002/h003/h004), cross-process byte-stable. `scripts/rebuild_bulk.py`.
- **§2 placebo_method under the seal** (S9-1): hypothesis schema bump;
  registration refuses an unknown method; `PlaceboBattery.run` refuses a
  sealed/requested mismatch; Wave-1 grandfathered. Tests green.
- **§3 HC tool rev 2**: Architect-owned; no developer action (as specified).
- **§4.2 primary-2025 window + VIRGIN extension** (S9-1): Owner designated
  the 2025 reserve by typed phrase; DEVQ-022 seam fix applied.
- **§4.3 multi-window schema v3 + H-004** (S9-2): hypothesis/verdict v3
  (`window_refs`), calendar exit, multi-window battery + splits. H-004
  `h004_dow_monday_drift_v2` judged placebo-first → **FAIL** (n=56, net
  +5.00/trade but p=0.108 > deflated α=0.05: no edge over RANDOM TIMING,
  the OBS-1 arbiter). All tri-states acceptance-valid; the FAIL is the data.
- **§4.1 second lens** (S9-3, this session — the DEVQ-023 close):
  The sealed shared-COUNT discriminator self-STOPPED on its own 5% guard in
  all four EU eras (dense-grid count saturation); DEVQ-023 raised, and the
  Architect ruled Option A + four binding amendments. Executed verbatim:
  (1) agreement-RATE discriminator + shared-count sanity floor (≥90% of max);
  (2) two-part guard (≥3× runner-up AND ≥0.80 absolute); (3) EMPIRICAL
  US-DST era segmentation (coarse weekly scan → flip detection K=2 → hour
  refinement), replacing the retired EU-hardcoded instants; (4) winter<0.90
  prediction guard. A correction note (`01KYE3BBE2PK0EP87D62S57CE6`, procedure
  only) was sealed BEFORE the overlap run (DEVQ-020 ordering). Result: all
  four detected eras PASS; winter agreement rose from the pre-fix 0.73–0.76
  to **0.966 / 0.953** — the Architect's US-DST prediction CONFIRMED (boundaries
  2024-03-09, 2025-03-08). `second_lens 01KYE3WCKK40PNJ8JEATQ4XTNT`
  (tier=BROKER): n_overlap=8290, n_agree=7912, **agreement_rate=0.9544 ≥ 0.95**
  → the feeds corroborate. `agreement_summary.notes` carry both metric tables
  (count+agreement) pre/post-fix per era, the guard-fired history, the detected
  boundary instants, and the declared tier (amendment 4). Overlap slice
  reserve-clean (0 reserve ts). `scripts/overlap_second_lens_s9.py`
  `--rebuild-bulk` regenerates the overlap parquet byte-identically (§1
  discipline). DEVQ-023 CLOSED (inbox/CLOSED).

Handoff to the Architect (sprint-close duties): IVF-S9 drills + checks
(rebuild determinism; placebo_method audit; **second-lens overlap
recomputation with ordering audit** — note precedes overlap in the chain;
no reserve ts in the slice; H-004 verdict anchor), HC rev-2, REV-S9, Owner
Go/No-Go. Tally for REV-S9 (from DEVQ-023): Architect #17 (count criterion
saturated on a dense grid, caught by its own tripwire) + Developer #4
(EU-hardcoded instants were a deviation from ADDENDUM 2's "detected"
segmentation; the guard caught it before any record was written); the
engine's self-STOP and the DEVQ's quality are the counterweight.
