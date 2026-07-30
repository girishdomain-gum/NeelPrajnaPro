# IVF NP-S1 AC-6 — independent re-derivation of the H-07 prediction verdict

*IVF / Validator session · fresh worktree `ivf-validator-neelprajnapro-a9bdfe`, no prior
context · 2026-07-30. Instruction: `ops/ARCH-NP-002_IVF_instruction_AC6.md`. Scope: AC-6
only.*

**OVERALL VERDICT: RED.** The drill passed clean (6/6 frauds caught, control clean). The
core chain re-derivation (NP-ADR-002 §2, all 15 lines) reproduces the ledger to 1e-9 on
every float, with no softening needed — this session has no disagreement with the
mechanical verdict. But two of the four §3 items that "no one has checked" do not
survive the check: the three non-equivalence statements are **not byte-verbatim** in
either H-07 registration, and an independent SWEEP recount from the M5 bars disagrees
with the reported 325 by 6 events. Per instruction, RED is named plainly and this report
does not proceed to HC.

---

## 0. Independence note — where the evidence actually lives

`ivf/` never imports `qrf/`. Every number below was re-derived from file outputs read
directly (journal JSON lines, parquet via `pyarrow`, YAML via `pyyaml`) using formulas
taken from **normative or self-declared-normative text** — never from asking the
Developer's Python what a sweep is. The two exceptions, both explicitly sanctioned by
the instruction's own pattern (it names `deflation.py`'s stated rule and `seeds.for_run`'s
stated derivation as things to re-derive from, not import) and by the modules' own
docstrings, which address the IVF directly:

- `qrf/kernel/corrections/deflation.py` — read for its stated prefix-segment family-match
  rule (§A below), reimplemented independently in `ivf/checks/check_np_s1_ac6.py`.
- `qrf/kernel/protocol/seeds.py` and `qrf/kernel/records/record.py` — both docstrings say,
  verbatim, "reproduce it exactly to audit a seed" / "the IVF re-implements canonical
  serialization independently from the spec text." Reimplemented, not imported.
- `qrf/kernel/battery/battery.py` — read *only* for the statistics engine's mechanical
  procedure (one-sided t-test formula, and the seeded-bootstrap-CI recipe:
  `np.random.default_rng(seed)`, 2000 resamples, `percentile([2.5, 97.5])`), because
  ARCH-006 §2's normative text ("seeded bootstrap CI") does not pin down the resample
  count or RNG scheme precisely enough to hit 1e-9, and this is Kernel judge machinery,
  not detector/domain logic. **The detector definition itself (POOL_FORMED/SWEEP
  mechanics) was taken exclusively from NP-ADR-008 §3's text** for the independent
  SWEEP recount (§3 item 3) — `np_feature_service.py` / `np_probability_engine.py` were
  never opened.

**Provenance finding, stated plainly:** the target verdict `01KYSGQR3D8SYSVJFSF9M77CMY`
and its burn are **not present on `main`** (or on this worktree's branch) at the commit
this instruction was issued from (`9b2df73`). The Battery run that produced them
(Execution Plan deliverable 4+5) lives only on the unmerged branch
`claude/np-adr-008-liquidity-sweep-7aa72b` (commit `2e8d40a`), whose worktree also holds
the only copy of `datastore/bulk/verdict_trades.h007_np_liquidity_sweep_v1_1/` and
`datastore/bulk/xauusd_m5_vantage/` on this machine (both gitignored, unrecoverable from
git objects alone). This session read those files directly, read-only, from that
worktree's working tree — it did not modify anything there. **Anyone auditing this
verdict from `main` alone, today, cannot find it**; that branch must merge first. This is
named here because the ARCH instruction itself was written against that unmerged data
without saying so.

---

## 1. Drill — six plants + control, all separately run

Full detail: `ivf/reports/ac6_drill.json`. Harness: `ivf/checks/drill_np_s1_ac6.py`,
checker under test: `ivf/checks/check_np_s1_ac6.py` (chain-check exit code only — see
§2's scope note). **Drill verdict: CAUGHT.**

| # | Plant | Expected catch | Outcome |
|---|---|---|---|
| P1 | Altered one trade's `net_pnl` (+100) in the trades parquet | pooled mean/p/verdict mismatch | **CAUGHT** — `D.net_mean`, `D.t_stat`, `D.p_one_sided`, `D.ci_low/high`, `F.per_trade_cost`, `K.file_sha256` all fired |
| P2 | Verdict `corrections.family_m` 19→18 (+ consistent `effective_alpha`) | effective alpha ≠ 0.05/family trials | **CAUGHT** — `A.family_m` (mine=19 vs recorded=18), `A.effective_alpha`, `J.hash_chain` |
| P3 | Deleted one `trial_count` record from the family | family total ≠ 19 | **CAUGHT** — `A.family_m` (mine=18 vs recorded=19), `J.hash_chain` |
| P4 | Cost model swapped to $0.26 (baked into parquet `cost`/`net_pnl`) | gross−net ≠ 0.41 | **CAUGHT** — `F.per_trade_cost` (found 0.26), plus cascading `D.*` stat mismatches |
| P5 | Window `ts_end` moved back one bar (300s) | trade set/fold boundaries shift | **CAUGHT** — `G.bounds` (window no longer equals ratified interval), `J.hash_chain` |
| P6 | Hypothesis `thresholds` edited after the fact (verdict's copy untouched) | thresholds no longer byte-equal | **CAUGHT** — `B.thresholds`, `J.hash_chain` |
| C0 | Untampered control | must raise nothing | **CLEAN** — exit 0, no red lines |

All six plants caught, control raised nothing. Per instruction, the real re-derivation
proceeds.

---

## 2. Real verdict re-derivation — chain checks (tolerance 1e-9)

Target: verdict `01KYSGQR3D8SYSVJFSF9M77CMY` · hypothesis `01KYSETR2C85MRRVWZCM8V0GMC` ·
window `01KYSEDSM6K5ZKWK0XRCC4SVZ7` · burn `01KYSGQR6K1HHRT66R78BV6Z8Y` · trades manifest
`01KYSGQQKWABAZS4Y6TNF9Q7SP`. Full machine-readable output: `ivf/reports/ac6_verify.json`.
Script: `ivf/checks/check_np_s1_ac6.py`. **Every line below is PASS; no disagreement with
the ledger's own figures.**

| Quantity | Ledger value | Independently re-derived | Line |
|---|---|---|---|
| n_trades | 259 | 259 | PASS |
| net mean | 1.5195945945945775 | 1.5195945945945766 (Δ9e-16) | PASS |
| gross mean | 1.9295945945945765 | 1.9295945945945765 | PASS |
| one-sided p | 0.057415412388292036 | 0.057415412388292036 | PASS |
| t stat | 1.5821919583845476 | 1.5821919583845476 | PASS |
| CI | [−0.3067311776062075, 3.389103764478732] | [−0.3067311776062075, 3.389103764478732] | PASS |
| family_m / effective_alpha | 19 / 0.002631578947368421 | 19 / 0.002631578947368421 | PASS |
| fold n | 64, 70, 63, 62 | 64, 70, 63, 62 | PASS |
| fold means | +3.1896093750000145, +3.7879285714285915, +0.4915079365079102, −1.7206451612904061 | +3.1896093750000145, +3.7879285714285915, +0.49150793650790897 (Δ1e-15), −1.7206451612904068 (Δ7e-16) | PASS |
| verdict | FAIL | FAIL (re-derived from n≥min_n, mean>0, p≥effective_alpha) | PASS |

**Chain checks (ARCH-NP-002 §2, each a separate line):**

1. **Hash chain intact, whole journal.** Recomputed `content_hash` (SHA-256 of canonical
   `{record_type, schema_version, producer, event_ts, parents, payload}`, per
   `record.py`'s own "IVF re-implements... independently" docstring) and the `prev_hash`
   chain for all 112 records in the source journal, genesis (`0`×64) to tail. **PASS —
   intact, no torn tail.** (The drill's tampered copies broke this chain immediately,
   confirming the check has teeth — see `J.hash_chain` hits in §1.)
2. **Burn atomic with verdict.** Exactly one `window_burn` for
   (window `01KYSEDSM6K5ZKWK0XRCC4SVZ7`, lineage `h007_np_liquidity_sweep_v1_1`); its
   `consumed_by` is the verdict id; the verdict id is among its `parents`; its
   `window_ref` matches. **PASS.**
3. **Family total is exactly 19**, re-derived from `deflation.py`'s *stated*
   prefix-segment rule (reimplemented independently, not imported), summed over
   `trial_count.n_attempts` for family `xauusd/neelprajna`: the 2 `h007_np_liquidity_sweep_v1_1`
   registrations (prediction + E2-existence) + the 17 counted-only entries
   (H-01…H-06, H-08…H-18, per Appendix A.4's ruling) = **19, exactly**, with no
   sibling-family record miscounted in either direction. **PASS.**
4. **Cost model applied.** Every one of the 259 trades' `gross_pnl − net_pnl` = exactly
   **0.41** (no other value found); `configs/venues.yaml`'s `xauusd_retail_h07` recomputes
   `0.24 + 2×(0.05 + 0.035) = 0.41`. **PASS.**
5. **Thresholds byte-equal** between the hypothesis record and the verdict's copy
   (canonical-JSON compared). **PASS.**
6. **Window designation is TRAINING**, bounds `[2026-04-20T22:00:00+00:00,
   2026-07-10T14:33:00+00:00)` — exactly the ratified UTC half-open interval. **PASS.**
7. **Selftest gate recorded** (`selftest_seed 20260725`); the run seed
   `2702931253379642539` reproduces exactly from `seeds.for_run`'s stated recipe —
   `int.from_bytes(sha256(canonical_bytes({hypothesis_ref, window_ref}))[:8], "big") &
   (2**63−1)` — reimplemented independently. **PASS.**
8. **`embargo_bars ≥ hold_bars + 1`**: 15 ≥ 13. **PASS.**

Additional integrity checks not in the ARCH's numbered list, added because they were
free given the tooling already built: the trades parquet's own SHA-256
(`1cf638a2a7fc35e3cc9321595dc6c86bc84c05bee46c6b631705a191c24f4db3`) and row count (259)
match the `bulk_manifest` record exactly. **PASS.**

---

## 3. The four things nobody had checked

### 3.1 Does the FAIL survive at undeflated alpha? — **PASS**

p = 0.057415412388292036 > base_alpha = 0.05. The FAIL does not depend on deflation at
all; the 19-vs-18 family-count ruling (Appendix A.4 / DEVQ-NP-003) could not have
changed the outcome either way, since deflation only ever *lowers* the bar the evidence
must clear. **Confirmed.**

### 3.2 Three non-equivalence statements verbatim in the registration — **FAIL**

NP-ADR-008 §2.1 states three sentences, verbatim, as ones that "must survive into every
derived artifact":

1. *"E2-v1.1 is not equivalent to the original v1.0 hypothesis."*
2. *"It is a new hypothesis bound to the documented v1.1 detector lineage."*
3. *"Any future judgment of the original T3/MSS detector requires a separate
   implementation and fresh out-of-sample evidence."*

Both H-07 registrations (`01KYSETR2C85MRRVWZCM8V0GMC` prediction,
`01KYSETR3VACRBCWN9QYRRX6DW` E2-existence) carry the *substance* of all three, in their
`outcome_interpretations` and `thesis` fields — but joined as one semicolon-separated
clause rather than reproduced as three sentences, and with statement 1's subject
shortened: **"v1.1 is not equivalent to the original v1.0 hypothesis"** (drops the
`E2-` prefix), and statements 2–3 lower-cased at the clause boundary ("...lineage; **it**
is..."; "...evidence" joined without a capital **A**ny). Byte-for-byte substring match
against each of the three ADR sentences: **0 of 3 found, in either registration.**

This is a real, if narrow, finding: the meaning is faithfully preserved (an informed
reader would not be misled), but the instruction's own §3.2 asks specifically whether
these "appear... verbatim," and they do not. **Their absence-as-worded is exactly the
condition NP-ADR-008 §2.1 warns about** ("Their absence would mean the verdict can be
read as speaking for the historical T3 gate") — reported honestly rather than waved
through as "close enough."

### 3.3 Independent SWEEP recount from the M5 bars, NP-ADR-008 §3 text alone — **DISAGREEMENT (331 vs 325)**

Full output: `ivf/reports/ac6_sweep_recount.json`. Script:
`ivf/checks/sweep_recount_np_s1_ac6.py`. Re-derived, from the 16,029 M5 bars and
NP-ADR-008 §3's mechanical definition alone (frozen parameters: pivot_k 3, member
window 200 bars, pool_tol 30 ticks / 0.30, min_pen 5 ticks / 0.05, reclose_window 2
bars; level = max/min of member prices, frozen at formation):

- 3,099 pivots confirmed (fractal, k=3)
- 476 pools formed
- **331 sweeps** — vs the Developer's reported **325** (vs the bespoke stack's
  historical 325)

**This is a disagreement, named per instruction rather than softened.** The ADR's own
text is honest that it under-specifies the mechanics fully: the call site
`build_pools_and_sweeps(bars, swings, 30.0, 5.0, 3, 2)` takes a `swings` argument the
ADR never defines the computation of, and the pool-formation clustering rule ("same-side
pivots within the last 200 bars priced within pool_tol... ≥2 members") does not specify
whether membership is transitive/pairwise or anchored on the newest pivot, nor what
happens to a pivot that arrives near an already-active pool but does not extend it. This
recount made three disclosed, textually-reasonable choices (documented in the script's
docstring): a standard strict-extremum fractal pivot test; star/anchor clustering on the
newest confirmed pivot; and full suppression (no merge) of a new pool near an active
same-side pool. A 6-event / 1.8% difference on 325 is well within what a different, still
ADR-consistent choice on any of these three points would produce. **Per instruction: "the
Developer reports 325 against the bespoke stack's historical 325. Agreement corroborates;
disagreement is more valuable." This is disagreement — surfaced, not resolved by this
session, because resolving it would require the very source (`np_feature_service.py`'s
`swings` construction) the IVF is built not to read.**

### 3.4 Bar build honesty — **PASS**

Independently rebuilt from the raw Stage2 tick parquets at `F:\NeelPrajna\Validation\Stage2\parquet\`
(60 files, external to this repository but present and readable on this machine —
distinct from any Developer Python; only the raw tick columns `time_msc`/`bid`/`ask` were
read). Method: clean ticks only (`bid>0 ∧ ask>0`, applied directly rather than trusting
the file's own `clean` column), mid = (bid+ask)/2, broker time (UTC+3) → UTC by
subtracting 3h, bucketed `(ts−300s, ts]`.

- **Bar count: 16,029** — matches exactly.
- **First bar** (`ts=2026-04-20T22:05:00Z`, from the `20260421_BACKFILL` file):
  2,974 ticks bucketed; open/high/low/close reproduce the recorded bar **exactly**
  (open 4822.39, high 4831.01, low 4820.805, close 4825.105).
- **Last bar** (`ts=2026-07-10T14:33:00Z`, from the `20260710_LIVE` file): 1,852 ticks;
  open/high/low/close reproduce the recorded bar **exactly** (open 4105.53, high
  4107.925, low 4088.13, close 4088.13).
- **Weekend seam spot-check:** the largest bar-to-bar gaps in the 16,029-bar series are
  ~49–53 hours; the one inspected in detail runs **Friday 2026-06-19T17:00:00Z →
  Sunday 2026-06-21T22:05:00Z**, a genuine market-closure gap (no flat/fabricated bars
  interpolated across the weekend).

**Confirmed honest**, on the two bars and the seam instructed to be spot-checked.

---

## 4. What this session could not verify

- **H-07's true MQL5 original.** `LiquiditySweepGate.mqh` is deleted and predates this
  repository's git history (Appendix A.1); no session, this one included, can
  independently re-derive what it actually computed. What survives — `kb.json`'s
  hypothesis text and the absorbed pool engine inside `T3_SweepFVGGate.mqh` — was not
  re-read here beyond what NP-ADR-008 and its Appendix A already quote, per the "never
  from the Developer's Python" rule extending to the bespoke MQL5 lineage too.
- **Full independent bar rebuild.** Only the first bar, last bar, and one weekend seam
  were spot-checked (§3.4), as instructed — not all 16,029 bars against all 60 tick
  files. Not claimed as exhaustive.
- **Cross-implementation parity (V&V §3 item 2)** — MQL5 vs Python event-for-event — is
  out of AC-6's scope (a Level-2 item this instruction did not ask for) and was not
  attempted.
- **Whether a different, equally ADR-consistent pivot/clustering implementation would
  reproduce 325 exactly** — this session's recount used one reasonable, disclosed
  reading of underspecified mechanics (§3.3); it does not claim to have found *the*
  unique correct reading.

## 5. Non-goals — confirmed honored

No code written under `qrf/**`. No new hypotheses, registrations, runs, or burns. No
normative-document edits. **No re-run of the Battery** — confirmed structurally: exactly
one `window_burn` exists for this (window, lineage) in the source journal (§2 check 2),
and this session only *read* files from the sibling worktree, never wrote to it.

---

## 6. Verdict

| Section | Result |
|---|---|
| Drill (§1) | CAUGHT — proceed |
| Chain re-derivation (§2, 8 numbered checks + summary table) | **GREEN** — all PASS, 1e-9 |
| §3.1 undeflated alpha | PASS |
| §3.2 non-equivalence statements verbatim | **FAIL** |
| §3.3 independent SWEEP recount | **DISAGREEMENT** (331 vs 325) |
| §3.4 bar build honesty | PASS |

**Overall: RED.** Per instruction, this is named plainly, not averaged against the clean
drill and clean chain re-derivation, and this report does not proceed to HC. The
mechanical verdict itself (FAIL, 259 trades, p=0.0574, matches the ledger to 1e-9 with a
clean drilled instrument behind it) is trustworthy. What is not clean is the
registration's literal wording against a stated verbatim requirement, and one
under-specified corner of the detector's own textual definition surfacing a 6-event
disagreement on independent recount — both of which NP-ADR-008 §3 anticipated might
fail, and both should be dispositioned by the Architect/Owner before this lineage is
relied on further.
