# QRF Independent Verification Framework (IVF) v1.0

**Status:** PROPOSED · 24 July 2026
**Companion to:** Architecture v1.1 (frozen) · Implementation Blueprint v1.0
**Mode:** Engineer
**Standing assumption:** the implementation is wrong until it independently
proves itself correct.

---

## 1. Purpose — in plain words first

Suppose Sprint 5 reports "Evidence Battery complete." All unit tests are
green. What do we actually know?

Only that the code agrees with itself. A bug in the fill logic and a bug
in the test that checks the fill logic can agree perfectly. Internal
consistency is not correctness.

What would settle it? A second, independent implementation computing the
same thing from the same inputs. If two systems that share no code, no
author, and no assumptions produce the same trades — confidence is
earned. If they disagree — a bug has been found *before* it corrupted a
verdict.

That is the IVF: an outside party whose only job is to reproduce the
implementation's claims independently, report every difference
automatically, and give a human a short, concrete checklist before each
sprint is allowed to close.

**New architectural principle (adopted):**

> **Trust Through Independent Reproduction.** Never trust a module
> because it passed its own tests. Trust it only after an independent
> implementation reproduces the same result. Agreement builds
> confidence; disagreement becomes an investigation record.

Note that this is not a new philosophy bolted on — it is the existing
calibration invariant ("no instrument trusted until it proves itself")
applied to the system as a whole. The implementation is an instrument.
The IVF is its thermometer test.

---

## 2. Independence Rules (what makes the IVF actually independent)

| Rule | Statement | Enforced by |
|---|---|---|
| IND-1 | IVF code lives in top-level `ivf/`, outside `qrf/`. It may **never import** `qrf.*`. | AST firewall test (same mechanism as the kernel firewall) |
| IND-2 | IVF consumes only **file outputs**: journal.jsonl, parquet files, verdict JSON, CSVs. Never in-process objects. | code review + IND-1 |
| IND-3 | Where possible, the reference implementation uses a **different language or engine**: MQL5/MT5 Strategy Tester, DuckDB SQL re-derivations, published statistical tables, hand computation. | per-check design (§4) |
| IND-4 | Where the reference must be Python, it must use a **different library or a from-scratch formula** than the implementation used. | per-check design |
| IND-5 | IVF results are written to the ledger as `verification_report` records — verification history is permanent evidence. Writing to the ledger is allowed; reading implementation *code* is not. | schema + review |
| IND-6 | The IVF itself is verified by **planted-bug drills** (§6). An auditor that has never caught a planted bug is untested. | drill log per sprint |

---

## 3. The Three Verification Instruments

### 3.1 The MT5 Reference Kit (`ivf/mt5/`)

Small, single-purpose MQL5 tools — deliberately primitive, so they are
easy to trust by inspection:

| Tool | Purpose | Output |
|---|---|---|
| `IVF_TickExporter.mq5` | Export ticks/bars for an exact window straight from the terminal — a second, independent copy of the data | CSV |
| `IVF_SessionStats.mq5` | Independent seasonality reference: per-session/per-weekday bar statistics computed in MQL5 | CSV |
| `IVF_SwingMarker.mq5` | Independent swing highs/lows (simple k-bar pivots) — the shared primitive under SMC/S&D/chart patterns | CSV |
| `IVF_IndicatorDump.mq5` | MT5's own built-in RSI/ATR/MA values per bar — reference for classical indicators | CSV |
| `IVF_RefEA.mq5` + Strategy Tester | The opposing backtester: a minimal EA that takes a frozen signal file (timestamps + direction + SL/TP from the Python side) and executes it in MT5's Strategy Tester; the tester report becomes the independent P/L | Tester HTML/XML report |
| `ivf/mt5/parse_tester.py` | Parses Strategy Tester reports into normalized trade CSV (IVF-side Python; imports nothing from qrf) | CSV |

The `IVF_RefEA` pattern is the key trick for backtest verification:
instead of re-implementing strategy logic in MQL5 (error-prone), the
*frozen signals* cross the boundary as a file, and only **execution**
(fills, costs, P/L arithmetic) is independently reproduced. Signal
generation is verified separately at the detector level (rows 2–4 +
human charts), execution at the engine level (RefEA). Divide and verify.

### 3.2 Reference-Value Cross-Checks (`ivf/reference/`)

For mathematics, the independent party is a *known answer*:

- Statistical tests recomputed on published worked examples (textbook
  datasets with known t/p values) and cross-library (scipy vs
  statsmodels where both exist).
- Block bootstrap validated on a synthetic AR(1) series whose CI
  behaviour is known analytically in the limit.
- Bonferroni/FDR verified by hand on tiny cases (m=3, m=10).
- Belief updates recomputed in a 20-line standalone script from the
  ledger's own calibration and verdict records — must match the
  implementation's `belief_update` records exactly.
- Hash chain re-verified by a standalone `ivf/verify_journal.py` that
  re-implements canonical serialization from the Blueprint §1.3 spec
  text (not from qrf code).

### 3.3 The Human Inspection Protocol (`ivf/human/`)

Ten-minute structured checklists, one per sprint (embedded in §7).
Rules: samples are drawn **randomly by the IVF tool** (never chosen by
the person — cherry-picking is the failure mode); every checklist ends
with an explicit signed line in the ledger (`verification_report` with
`human_signoff: true/false + notes`).

---

## 4. Tolerance Policy — when "equal" means equal, and when it can't

Two independent systems will not always match to the last decimal, and
pretending otherwise produces either false alarms or fudged
comparisons. So every comparison declares its class up front:

| Class | Rule | Applies to |
|---|---|---|
| EXACT | Byte/value identical. Any difference = RED. | Record hashes, event counts, trade counts, direction fields, timestamps at declared resolution, verdict category |
| NUMERIC | abs/rel tolerance stated per check (default: 1e-9 rel for pure math; 1 tick for prices) | Indicator values, statistics, P/L arithmetic on identical fills |
| MODELED | Systems legitimately differ (MT5 tester fill model ≠ our audited engine). Compare on the **common subset**: same trades, same entry/exit bars; then reconcile P/L delta against the *declared* cost-model difference. Residual unexplained delta beyond band = RED. | Engine vs Strategy Tester P/L |
| STATISTICAL | Property must hold in distribution (e.g., planted-noise runs FAIL ≥ 99% over N seeds) | Selftest behaviour, bootstrap coverage |

Every difference report states, per row: class, expected, got, delta,
band, status (GREEN/AMBER/RED), and — for AMBER/RED — a required
`explanation` field that a human must fill before sign-off.

---

## 5. Difference Reports

### 5.1 Generation

Each check is a standalone script `ivf/checks/check_{name}.py` with a
uniform CLI: inputs = file paths only; output = one JSON report + one
human-readable summary. A runner `ivf/run.py --sprint N` executes the
sprint's check set.

### 5.2 Report JSON (normative)

```json
{
  "check_id": "s4.trades_mt5_vs_engine",
  "sprint": 4,
  "class": "MODELED",
  "inputs": {"engine_trades": "…parquet", "tester_report": "…xml"},
  "rows_compared": 412,
  "green": 409, "amber": 3, "red": 0,
  "diffs": [ {"key": "...", "expected": "...", "got": "...",
              "delta": "...", "band": "...", "status": "AMBER",
              "explanation": null} ],
  "verdict": "AMBER",
  "generated_ts": 1753350000000000000
}
```

### 5.3 Ledger record

`record_type: verification_report`, payload = the JSON above plus
`human_signoff bool`, `signoff_notes str`, `drill_refs list` (§6).
Parents: the manifests/verdicts/records that were verified. RED reports
additionally spawn a `question` record (origin=contradiction) — an
investigation is a research question like any other.

### 5.4 Investigation workflow

RED → stop the sprint clock → reproduce minimally → determine which side
is wrong (the IVF can be the buggy one — that is a finding too, recorded
the same way) → fix → re-run the *entire* sprint check set (a fix can
break another agreement) → new report → sign-off.

---

## 6. Verify the Verifier — Planted-Bug Drills

Once per sprint, before sign-off, at least one deliberate bug is
introduced on a scratch branch and the sprint's checks must go RED:

| Sprint | Example drill |
|---|---|
| 1 | Flip one byte in a journal payload → `verify_journal.py` must name the exact record |
| 2 | Shift all detector event timestamps by one bar (hindsight bug) → event comparison must flag timestamp mismatches |
| 3 | Silently "repair" one flagged row during ingest → CSV↔parquet diff must catch the changed value |
| 4 | Off-by-one in screener grid trial count → trial-count cross-check must catch it |
| 5 | Drop spread cost on short trades only → RefEA P/L reconciliation must go RED beyond band |
| 6 | Reverse one correction (report uncorrected p) → reference stats check must catch it |
| 7 | Point observatory at a VIRGIN window in a sandbox copy → guard must raise; IVF confirms no finding record exists |
| 8 | Corrupt one family's events before overlap calc → independent overlap recomputation must diverge |

Drill results are recorded in the sprint's `verification_report`
(`drill_refs`). **A sprint cannot close without at least one successful
drill catch.**

---

## 7. Verification Matrix — per sprint

Legend: **AC** = acceptance criteria (Blueprint §7, unchanged) ·
**VC** = independent verification criteria · **HC** = human checklist
(10 min) · **Go/No-Go** in §8.

### Sprint 1 — Ledger core
- VC: `ivf/verify_journal.py` (independent canonical-serialization
  re-implementation) verifies the full hash chain; DuckDB SQL over raw
  JSONL re-derives record counts by type and matches store.query.
- HC: read 5 random records raw in a text editor — fields present,
  timestamps sane, parents resolvable by hand.
- Drill: S1 (byte flip).

### Sprint 2 — Instruments & calibration
- VC: `IVF_SessionStats` output vs seasonality detector aggregates
  (NUMERIC); `IVF_IndicatorDump` RSI vs pandas-ta RSI per bar (NUMERIC,
  documented warm-up exclusion); `IVF_SwingMarker` pivots vs Python
  swings (EXACT on k-matched definition).
- HC: 10 IVF-random-sampled events opened on the actual MT5 chart —
  does the pattern visibly exist at that bar, and was it knowable then?
- Drill: S2 (timestamp shift).

### Sprint 3 — Data plane
- VC: `IVF_TickExporter` window vs BulkStore read-back: row counts EXACT,
  prices EXACT at tick resolution; flagged-row audit — every anomaly row
  present and unmodified in parquet (EXACT); DuckDB re-derives
  ingest_report counts from files and matches the record.
- HC: pick one FAILed/flagged day; eyeball the flagged cluster — does
  the flag reason make sense against the raw CSV?
- Drill: S3 (silent repair).

### Sprint 4 — Screener + costs + SMC
- VC: for a 20-variant sub-grid, trades re-derived by an independent
  DuckDB/SQL join of events×rules and compared to screener shortlist
  inputs (EXACT counts); trial_count vs grid-size recomputation (EXACT);
  SMC events vs a *second* independent SMC implementation (different
  GitHub lineage) on the same bars — agreement rate reported, divergent
  cases sent to HC.
- HC: 10 random SMC events on chart (as S2); 5 divergent cases between
  the two SMC implementations adjudicated by eye against the written
  definition — which implementation matches the spec?
- Drill: S4 (trial off-by-one).

### Sprint 5 — Battery I (engine, splits, selftest)
- VC: frozen-signal file → `IVF_RefEA` in Strategy Tester (same window,
  modeled costs) → parse report → trade-by-trade reconciliation
  (MODELED): same entries/exits on common subset EXACT; P/L delta
  reconciled to declared fill-model difference within band.
  Split boundaries re-derived by standalone date arithmetic (EXACT).
  Selftest STATISTICAL properties over 200 seeds.
- HC: walk one full trade by hand — entry price, spread charge, exit,
  R arithmetic — from raw ticks to trade record.
- Drill: S5 (missing short-side spread).

### Sprint 6 — Battery II (first real verdict)
- VC: every statistic in the verdict recomputed by `ivf/reference/`
  (NUMERIC); corrections re-applied by hand-scale script (EXACT m,
  method, adjusted threshold); full end-to-end replay from journal on a
  clean checkout reproduces the verdict payload (EXACT); window_burn
  presence and interval verified by SQL.
- HC: architecture-compliance read: verdict record vs Architecture
  Ch. 7 pillar-by-pillar — sign each pillar off by name.
- Drill: S6 (dropped correction).

### Sprint 7 — Beliefs + Observatory + dashboard
- VC: standalone belief recomputation from ledger (EXACT); contamination
  guard drill (S7) run in sandbox; dashboard numbers spot-checked
  against direct DuckDB queries (EXACT).
- HC: read the belief trajectory of one family aloud — does each move
  correspond to a verdict you can point at?
- Drill: S7 (virgin-window probe).

### Sprint 8 — Catalog wave + redundancy study
- VC: overlap/co-occurrence matrices recomputed by independent SQL over
  event parquet (NUMERIC); placebo-zone machinery verified by planting a
  synthetic series where fib zones are *constructed* to be meaningless —
  study must report no advantage (STATISTICAL).
- HC: review the registered prediction vs outcome; confirm the record
  was written before the computation (hash timestamps).
- Drill: S8 (corrupted events).

---

## 8. Go/No-Go Policy

A sprint closes only when **all four** hold:

1. **AC met** (Blueprint) — implementation's own bar.
2. **VC verdict GREEN**, or AMBER with every amber row carrying a
   written explanation accepted at sign-off. Any RED = No-Go until the
   investigation record closes.
3. **HC signed** in the ledger (`human_signoff: true`) by the owner.
4. **Drill caught** — at least one planted bug detected this sprint.

No-Go is not failure; it is the system working. A No-Go finding before
Sprint N is strictly cheaper than the same bug discovered inside a
verdict after Sprint N+3. The matrix exists to make bugs expensive
*early* and impossible to ignore *ever*.

Escalation rule: the same check going RED twice after a fix ("fix
ping-pong") freezes forward work entirely until a `note` record
documents root cause — patch-until-green without understanding is the
one behaviour this framework must never reward.

---

## 9. Repository Placement

```
ivf/
├─ run.py                    # runner: --sprint N executes the check set
├─ checks/check_*.py         # one file per check; file-inputs only
├─ reference/                # known-answer datasets + standalone math
├─ mt5/                      # .mq5 sources + parse_tester.py
├─ human/checklist_s{N}.md   # printable 10-minute checklists
└─ tests/                    # IVF's own unit tests + firewall (no qrf imports)
```

IVF is versioned in the same git repo (one history, one backup) but
firewalled by IND-1. MQL5 sources are copied to the terminals manually
per the existing operational pattern; their outputs return as CSV.

---

*The implementation proves itself the way every instrument in this
project proves itself: against an independent measure, on the record,
before it is trusted. — End of IVF v1.0*
