# NeelPrajnaPro — File Structure (and how it maps to the Architecture)

> One-doc-per-thing law: this is THE file-structure document of the repository.
> Every mapping cites the Architecture (docs\architecture\
> NeelPrajnaPro_Architecture-v1.1.md — "Arch" below) or another normative doc.
> Written from a REAL directory walk on 2026-08-02 (Owner order O-056), not
> from memory. If the tree and this document diverge, the tree wins and the
> divergence is a finding — update this file.

## The one-line map

```
F:\NeelPrajnaPro          = the BODY  (both organs — Arch v1.2 §B.9, the body ruling)
  qrf/                    = the JUDGE (Core QRF Brain — left organ)
  runtime/                = the HANDS (NeelPrajna Book A — right organ; ARRIVES AT NS2)
F:\NeelPrajnaProData      = the EVIDENCE SHELF (bulk data, outside git — AM-07; data is not source)
F:\Fable                  = the runtime's OLD home — sealed history after the NS2 import (§B.9.6)
```
This repository's qrf/ never trades; runtime/ never learns on its own (the
wall — enforced two-sided in CI from NS2, §B.9.3).

## Repository root

| Entry | What it is | Architecture alignment |
|---|---|---|
| `qrf/` | The Kernel + the trading-side concept families — all judged code | Arch Part B §2 (Kernel) + §3 (families) |
| `runtime/` | THE SECOND ORGAN (PLANNED, arrives NS2 — the body ruling O-057): Book A EA source (mql5/), Supervisor/Runner (supervisor/), NPSU (npsu/), dashboards, the runtime's own docs. History-preserving import; two-sided firewall; *.ex5 stays ignored; nothing deployed or armed by the import | Arch v1.2 §B.9 |
| `ivf/` | Independent Verification Framework — stdlib-only, re-derives verdicts | Arch §7.3; IND-1 (independence by construction) |
| `tests/` | The full suite (~1078 tests) + the kernel firewall | Arch §7; drill law |
| `scripts/` | One-shot, auditable ritual scripts — each names its sprint/purpose | The V-gate rhythm; every judgment/registration is a script, never a REPL |
| `configs/` | `hypotheses/` (h0NN_*.yaml, hashed at registration) + `venues.yaml` (frozen cost models incl. xauusd_retail_h07) | Arch §3.3–§3.4 |
| `datastore/` | `journal/` = THE hash-chained ledger (tracked); `bulk/`+`index/` = derived, rebuildable (git-ignored) | Arch §2 RecordStore; Scientific Model Diagram 2 (Records root) |
| `hypotheses/` | Founding hypothesis materials (NeelPrajna-origin) | Arch §A.0.1 — every hypothesis is born at F:\Fable |
| `docs/` | The normative document tree (below) | One-doc-per-thing law |
| `tools/` | `run_job.sh` (the Owner's job runner) + `accept.sh` (the accept ritual, with its guards) | DEVELOPMENT_CYCLE / GIT_WORKFLOW; the Owner's three spells |
| `dashboard/` | Read-only status surface | Arch §A.1 rows 11–12 class (a view, not an organ) |
| `comms/` | Agent communication (NOT in git — the one live copy) | COMMS_PROTOCOL v1.6 §2 |
| `.claude/worktrees/` | The Developer's dev-branch worktree(s) | GIT_WORKFLOW layout: root = main, Developer works in a worktree |
| Root .md files | ADOPTION_ADAPTATIONS (all pins) · DEVELOPMENT_CYCLE · GIT_WORKFLOW · ROADMAP · CHANGELOG · boot prompts · README/CONTRIBUTING | The operating law around the code |
| `pyproject.toml` / `uv.lock` | Dependencies (locked; uv.lock committed on purpose) | Reproducibility |

## qrf/kernel/ — the judge itself (write authority is a CLOSED list, Arch §2.1)

| Folder | Contents / role | Arch §2 row |
|---|---|---|
| `records/` | RecordStore (hash-chained, single-writer, append-only) + BulkStore/schemas | RecordStore, BulkStore |
| `battery/` | EvidenceBattery (sole verdict writer, atomic verdict+burn) + `block_null.py` (N2 null construction, n_local_sweeps, add-one empirical p) | EvidenceBattery, BlockNull |
| `protocol/` | WindowLedger (TRAINING/EXPLORATION/VIRGIN, burn-on-use) + `dst.py` (pinned server-clock self-policing, RED on drift) | WindowLedger, DST invariants |
| `corrections/` | TrialCountLedger — registration spends the attempt; family deflation | TrialCountLedger |
| `belief/` | BeliefLayer — updates from Verdict-typed inputs ONLY | BeliefLayer |
| `instruments/` | InstrumentRegistry / CalibrationHarness — planted-truth and silence tests | Instruments/Calibration |
| `observatory/` | Anomaly scans → questions only; no verdict, no burn | Observatory |
| `graduation/` | The graduation ladder machinery (Observation→…→Theory) | Scientific Model Diagram 7 |
| `graph/` | Knowledge-graph substrate (TARGET tier) | Arch §A.1 row (Knowledge Graph) |
| `registry/` | Registration plumbing | Arch §3.3 |
| `errors.py` | SchemaViolation and kin — the loud, named refusals | Drill law / fail-closed style |

**The firewall:** `tests/test_kernel_firewall.py` proves the kernel never
imports `qrf.trading` (CI-enforced). Detectors reach the kernel only as
injected, duck-typed objects — which is exactly why swapping/adding detector
tracks (H-07 → +H-08) never touches kernel code.

## qrf/trading/ — the domain side (proposes and observes; never judges)

| Folder | Contents / role | Alignment |
|---|---|---|
| `concepts/neelprajna/` | Detector track 1: liquidity_sweep per sealed NP-ADR-008 (H-07) | Arch §3.1 |
| `concepts/ccc/` | Detector track 2: MML hidden patterns (H-08) — CREATED AT NS3; listed here so the map is complete before the folder exists | Arch §3.6; Scientific Model Diagram 6 (MML) |
| `concepts/classical/`, `seasonality/`, `smc/` | The Gen-1 concept families (sealed history; smc's vendored reference lives under tests/third_party/) | Arch §3.1 "a family, not a framework" |
| `adapters/` | `mt5_csv.py` and kin — BARS-only (F-DOC-2: it does NOT ingest trade logs) | Arch §3.2 |
| `simulator/` | Execution simulation + cost-model application for judgments | Battery inputs |
| `payloads/`, `utility/`, `observatory/` | Event payload schemas; helpers; trading-side scans | — |

## ivf/ — the independent second key (propose-only; Developer never edits verify_*)

| Entry | Role |
|---|---|
| `verify_journal.py`, `checks/` | Re-derivation of ledger/verdict truth from normative texts; drilled before trusted |
| `mt5/` | Data-ACQUISITION tooling (export_xauusd_m5.py — Vantage-pinned, XAUUSD exact-match). The ONLY Developer-writable ivf area, by bounded grant A-050: collects, never judges |
| `reference/`, `reports/`, `human/`, `tests/` | Normative source copies, run reports, human-facing summaries, IVF's own tests |

## scripts/ — the ritual record (why so many files is a FEATURE)

Every registration, VIRGIN declaration, judgment, GO note, and migration is a
named, frozen, one-shot script (`register_h007_*`, `declare_virgin_*`,
`judge_*`, `note_go_s*`, `migrate_npsu.py`, `ingest_r6.py`,
`verify_csv_provenance.py`…). Nothing evidentiary ever happens in an
interactive session — the script IS the audit trail, byte-for-byte re-runnable
by IVF. Alignment: Arch §7's V-gate rhythm; the completion rule.

## tests/ — mirror of the code, plus two special citizens

Per-area folders mirror qrf/ (`battery/`, `protocol/`, `records/`,
`concepts/`, …). Special: `test_kernel_firewall.py` (the wall, CI-enforced)
and `third_party/smc_toolkit_vendored/` — vendored upstream source held
byte-identical under a sha256 provenance test, lint-excluded. **This is the
precedent AM-07/AM-08 generalized:** git holds proof-of-what-a-thing-was; the
CCC reference will be vendored the same way at NS2.

## docs/ — one document per thing

| Entry | Contents |
|---|---|
| `architecture/` | THE architecture (v1.1 md; docx render owed). Predecessors auto-archive |
| `scientific_model/` | THE scientific model (md normative; docx teaches it) |
| `constitution/` | The constitution — the permanent law above everything |
| `journal/` | The human-readable programme journal |
| `APPENDIX_TERMINOLOGY.md` | THE glossary (O-054) |
| `archive/`, `legacy/` | Superseded versions and the pre-adoption estate — sealed history, never scrubbed |

## Outside the repository, on purpose

| Location | What lives there | Law |
|---|---|---|
| `F:\NeelPrajnaProData\incoming\` | Bulk market-data exports (CSV) — hash-recorded in tracked provenance twins | AM-07: bulk outside git, proof inside; off-disk backup Owner-confirmed (O-053) |
| `F:\NeelPrajnaProData\reference\` | CCC_Indicator.zip and future reference material | AM-08 §3 |
| `F:\NeelPrajnaProData\` (root) | All test-data reports/CSVs | O-051/D3 extension |
| `F:\NeelPrajnaPro\comms\` | In the folder but OUT of git (.gitignore) — the one live comms copy | COMMS_PROTOCOL v1.4 |
| `F:\Fable` | The NeelPrajna runtime — origin of every hypothesis, source of the evidence base, generator of execution feedback, consumer of all knowledge | Arch §A.0; §5 (execution stays where the hands are) |

## Change record
- v1.0 (2026-08-02, O-056): created from a real directory walk. Known
  future entries: `runtime/` (NS2, the body ruling O-057),
  `qrf/trading/concepts/ccc/` (NS3), Contract v2 object
  schemas (NS7), Execution-Feedback ingestion path (NS7, Arch row 13).
- v1.0.1 (2026-08-02, O-057): one-line map re-drawn for the body ruling —
  both organs in one root; runtime/ row added as PLANNED; F:\Fable re-marked
  as the old home, sealed after import.
