# FILE_STRUCTURE.md — the real tree

Maintained by the Developer, every sprint. This is what actually exists in
the repo, not what is planned.

```
.
├── .github/
│   └── workflows/
│       └── ci.yml              CI: uv sync, ruff check, pytest — every push + PR
├── docs/
│   ├── FILE_STRUCTURE.md       this file
│   ├── GIT_WORKFLOW.md
│   ├── MASTER_SPRINT_PLAN_v1.md
│   ├── SPRINT_EXECUTION_MODEL_v2.md
│   ├── HYPOTHESIS_SPECIFICATION.md   AM-04: concept/measurement/judgment format
│   ├── concepts/
│   │   └── LS-01_liquidity_sweep.md   the liquidity_sweep concept spec
│   ├── measurements/
│   │   └── LS-01-R001_filtered_sweep.md   S07: SPECIFIED, NOT REGISTERED
│   ├── detectors/                 S06: prose definitions, written and
│   │   ├── fair_value_gap.md       APPROVED before any detector code
│   │   ├── order_block.md          (A-018's definition gate; order_block.md
│   │   │                           also carries A-020's consumed-swing fix)
│   │   └── market_structure_shift.md
│   └── retrospectives/
│       ├── S01.md
│       ├── S02.md
│       ├── S03.md
│       ├── S04.md
│       ├── S05.md
│       └── S06.md
├── tools/
│   └── run_job.sh              the Owner's one command; the Architect's job runner
├── mql5/
│   └── Scripts/
│       └── QRF/
│           ├── ExportXAUUSD.mq5   S03: the MT5 script the launcher runs to
│           │                     export XAUUSD bars (compiled .ex5 is
│           │                     never tracked, per .gitignore). S07
│           │                     Phase 1B extended it to accept an
│           │                     optional staged historical cutoff
│           │                     (MQL5\Files\QRF\export_end_time.txt)
│           │                     so a fresh window can be exported
│           │                     strictly BEFORE already-examined time,
│           │                     not just "most recent N bars"
│           └── QueryHistoryDepth.mq5   S07 F-07: capability query ONLY
│                                       (SeriesInfoInteger SERIES_FIRSTDATE,
│                                       no CopyRates) — proved M5 XAUUSD
│                                       history begins 2025-09-23, ruling
│                                       out any pre-2024 untouched span
├── mql5/EA/QRF/
│   └── RefusalEA.mq5           S07 (A-029 §3): fresh, from-scratch, refusal-
│                                only EA. Reads a staged instruction, VALIDATES
│                                structure + expiry (against TimeGMT(), never
│                                S03's latency-inflated clock_drift_probe_
│                                seconds), REFUSES loudly naming which check
│                                failed. NO order-placement call anywhere in
│                                the file (W9, token-scanned in
│                                tests/runtime/test_ea_source.py) and NO
│                                pattern logic (AM-02). Compiled clean (0
│                                errors, 0 warnings) against the real
│                                terminal; compiled .ex5 never tracked, per
│                                .gitignore, same as ExportXAUUSD.mq5
├── runtime/                    S07: the right organ (execution), added this
│   ├── __init__.py              sprint. Never imports qrf.kernel (the
│   │                             firewall enforces this both ways) — nothing
│   │                             here shares a Python type with qrf/; every
│   │                             boundary crossing is a plain dict, verified
│   │                             independently on this side (types.py)
│   ├── errors.py                runtime/'s OWN exceptions — deliberately
│   │                             independent of qrf.errors, full severance
│   ├── types.py                 ReleasedKnowledge — the ONLY way to
│   │                             construct one is from_release_dict(),
│   │                             which independently recomputes the sealed
│   │                             hash qrf/kernel/publication/release.py
│   │                             produced, agreeing byte-for-byte without
│   │                             sharing code
│   ├── belief.py                Belief.update() requires an actual
│   │                             ReleasedKnowledge instance — a raw dict is
│   │                             refused BY NAME even with every field
│   │                             correct (A-029 §2.1)
│   ├── contract.py               Instruction (conditional, expiring) +
│   │                             build_instruction() — clock source is
│   │                             documented in this file's own docstring
│   ├── consumption.py            consume() refuses an expired instruction
│   │                             BEFORE staging it for the EA;
│   │                             ingest_feedback() appends execution
│   │                             feedback as plain JSONL (deliberately NOT
│   │                             qrf's hash-chained RecordStore — runtime
│   │                             bookkeeping, never S08 evidence)
│   └── dashboard.py              render_mirror() — the mirror dashboard.
│                                 Pure, no side effects, no action-capable
│                                 control anywhere (W7, drilled by source-
│                                 text scan in tests/runtime/test_dashboard.py)
├── data/
│   └── provenance/              S03: provenance twins, TRACKED IN GIT — the
│       └── *.provenance.json     proof of what an export was, never the
│                                 export itself (that lives outside the repo)
├── qrf/                        the left organ (research/statistics)
│   ├── __init__.py
│   ├── errors.py                QRFError, SchemaViolation, IntegrityViolation,
│   │                            WriterLockHeld, ChainCorruption, TornTail,
│   │                            BulkMismatch, WindowConflict, LedgerImbalance,
│   │                            SymbolRefused, ProvenanceViolation, ClockDrift,
│   │                            TerminalBusy, TerminalMismatch,
│   │                            InsufficientResamples, HypothesisNotRegistered,
│   │                            BudgetExhausted, RegistrationMismatch,
│   │                            CeremonyRefused, UnverifiedObservations,
│   │                            PublicationLeak (S07)
│   ├── kernel/
│   │   ├── __init__.py
│   │   ├── records/             S02: the record store (evidence as proof)
│   │   │   ├── __init__.py
│   │   │   ├── store.py          RecordStore — append-only, hash-chained,
│   │   │   │                     single-writer, torn-tail detection
│   │   │   └── bulk.py           BulkStore — hash-binds bulk files to a manifest
│   │   ├── windows/             S02: the window ledger (market time as a
│   │   │   ├── __init__.py       spendable, accounted resource)
│   │   │   └── ledger.py         WindowLedger — reserve/burn/balances, plus
│   │   │                         supersede() (S07 F-07/A-025 R3): retracts a
│   │   │                         mistaken VIRGIN reservation without editing
│   │   │                         or deleting the original record
│   │   ├── observation/         S03: first contact with the real world
│   │   │   ├── __init__.py
│   │   │   ├── symbols.py         exact-symbol enforcement (E1)
│   │   │   ├── provenance.py      the provenance twin: write_twin/verify (E2/E3/E7)
│   │   │   ├── clock.py           server-clock drift probe + self-policing (E5)
│   │   │   ├── ingest.py          verify-then-bind into S02's BulkStore (E4/E6)
│   │   │   └── launcher.py        the ONLY module touching a live MT5 terminal
│   │   ├── detection/           S04: the Detector SDK (AM-01) — the JUDGE's
│   │   │   ├── __init__.py       vocabulary. INNER WALL: nothing here may
│   │   │   ├── types.py          import qrf.trading.* (extends the firewall)
│   │   │   │                     Bar, DetectorConfig, Observation (C1/C3),
│   │   │   │                     ObservationSet
│   │   │   └── interface.py       Detector ABC (C2: detect() must be pure)
│   │   ├── null/                S05: the null model
│   │   │   ├── __init__.py
│   │   │   └── resampling.py      block resampling, add-one p-value (N1-N4)
│   │   ├── registration/        S05: the trial ledger + the Owner's ceremony
│   │   │   ├── __init__.py
│   │   │   ├── alpha.py           geometric alpha spending (AM-03)
│   │   │   ├── ledger.py          TrialLedger — per-family, capacity 100 (R1-R3)
│   │   │   └── ceremony.py        phrase-gated registration (R4/R5)
│   │   ├── battery/              S05: the sole verdict writer
│   │   │   ├── __init__.py
│   │   │   └── battery.py         Battery — refuses before it reports (B1-B5)
│   │   ├── publication/          S07: the Publication Boundary (A-029 §2.3)
│   │   │   ├── __init__.py
│   │   │   └── release.py         publish(Verdict) -> a plain dict release,
│   │   │                          WHAT crosses (measurement_id, significant,
│   │   │                          direction — significant-conditional per
│   │   │                          A-030 R1, validity window), never HOW
│   │   │                          (no p_value/alpha/seed/observed_statistic);
│   │   │                          verify_no_leak() is the boundary's own
│   │   │                          allow-list check; sealed_hash makes a
│   │   │                          release byte-reproducible from its inputs
│   │   └── measurement/          S08 Phase 1 (A-032 §2.3): the ONE genuinely
│   │       ├── __init__.py        new module — pure: (ObservationSets +
│   │       └── ls01_r001.py        bars) -> a number. Duck-typed on the
│   │                              inner wall's qrf.trading side on purpose
│   │                              (reads .kind/.sweep_bar/.direction/
│   │                              .shift_bar, never imports the detector
│   │                              modules). qualifying_events() reads ONLY
│   │                              bar indices (causality by construction);
│   │                              signed_forward_return() is the only place
│   │                              bars are read, strictly after
│   │                              qualification is decided
│   └── trading/                 S04+S06: the PROPOSERS (AM-02) — detectors
│       ├── __init__.py           live here, never in qrf/kernel/; may import
│       └── concepts/             qrf.kernel.* freely (the allowed direction)
│           ├── __init__.py
│           ├── liquidity_sweep/
│           │   ├── __init__.py
│           │   └── detector.py    LiquiditySweepDetector, H-07 track, NP-ADR-008
│           │                      §5 v1.1 as pinned by Appendix B — frozen
│           │                      constants, exact parity: 3099 pivots /
│           │                      465 pools / 325 sweeps on the designated
│           │                      16,029-bar window
│           ├── fair_value_gap/    S06: M7 — 3-candle rule (docs/detectors/
│           │   ├── __init__.py    fair_value_gap.md)
│           │   └── detector.py
│           ├── order_block/       S06: M6 — origin-candle method (docs/
│           │   ├── __init__.py    detectors/order_block.md)
│           │   └── detector.py
│           └── market_structure_shift/   S06: M5 — simplest structure-
│               ├── __init__.py            shift rule (docs/detectors/
│               └── detector.py             market_structure_shift.md)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              shared fixtures
│   ├── test_smoke.py            proves qrf imports, the suite runs
│   ├── test_firewall.py         THE WALL: qrf/ <-> runtime/ import ban
│   ├── drills/
│   │   ├── __init__.py
│   │   ├── harness.py            control/tampered drill harness, reused by every later sprint
│   │   └── test_harness_selftest.py   proves the harness itself can fail
│   ├── records/                 S02: D1-D8 (store + bulk drills)
│   │   ├── __init__.py
│   │   ├── test_store.py
│   │   └── test_bulk.py
│   ├── windows/                 S02: D9-D14 (window ledger drills)
│   │   ├── __init__.py
│   │   └── test_ledger.py
│   ├── observation/             S03: E1-E7 (all terminal-independent; see
│   │   ├── __init__.py           launcher.py's own docstring for why
│   │   ├── test_symbols.py       run_export() itself has no CI test)
│   │   ├── test_provenance.py
│   │   ├── test_clock.py
│   │   ├── test_ingest.py
│   │   └── test_launcher.py
│   ├── kernel/
│   │   ├── __init__.py
│   │   ├── test_s08_rehearsal.py  S08 Phase 1 (A-032): X1/X2/X6 — the
│   │   │                          full judgment sequence end to end, twice
│   │   │                          (planted effect -> significant, no
│   │   │                          effect -> not significant), entirely
│   │   │                          against THROWAWAY stores under
│   │   │                          pytest's own tmp_path; X6 hashes the
│   │   │                          REAL window ledger before/after to
│   │   │                          prove it untouched
│   │   ├── test_s08_power_check.py  A-033 R1: power check at the REAL
│   │   │                          block_length=200/alpha=0.025 against a
│   │   │                          population shaped like the real one
│   │   │                          (~170 jittered events, ~20,000-51,000
│   │   │                          bars). SKIPPED BY DEFAULT (minutes of
│   │   │                          real compute; run by hand). RESULT
│   │   │                          RECORDED IN THE MODULE DOCSTRING: not
│   │   │                          significant across three independent
│   │   │                          constructions (uniform/10x-magnitude/
│   │   │                          clustered) — a finding about the null
│   │   │                          construction against a population-wide
│   │   │                          effect, reported per instruction rather
│   │   │                          than tuned away
│   │   ├── detection/           (SDK types are exercised via the sweep
│   │   │   └── __init__.py       detector's own tests; no separate suite yet)
│   │   ├── null/                 S05: N1-N4
│   │   │   ├── __init__.py
│   │   │   └── test_resampling.py
│   │   ├── registration/         S05: R1-R3 (ledger) + R4-R5 (ceremony)
│   │   │   ├── __init__.py
│   │   │   ├── test_ledger.py
│   │   │   └── test_ceremony.py
│   │   └── battery/              S05: B1-B5, honest atomicity, known-answer
│   │       ├── __init__.py       both directions
│   │       └── test_battery.py
│   ├── publication/               S07/A-030: W3/W4 (leak drill, byte-
│   │   ├── __init__.py            reproducibility) + R1 (direction
│   │   └── test_release.py         significant-conditional) drills
│   ├── measurement/               S08 Phase 1: X3/X4/X5 drills for
│   │   ├── __init__.py             ls01_r001.py, on lightweight duck-typed
│   │   └── test_ls01_r001.py       fakes (this module is duck-typed on
│   │                                purpose, see its own docstring)
│   ├── trading/                 S04+S06: planted-truth + clean-control per
│       ├── __init__.py           detector (all synthetic bars; real-run
│       └── concepts/             counts are run by hand, see sprint reports)
│           ├── __init__.py
│           ├── liquidity_sweep/
│           │   ├── __init__.py
│           │   └── test_detector.py   S04: P1/P2 + M1-M7, parity by hand
│           ├── fair_value_gap/
│           │   ├── __init__.py
│           │   └── test_detector.py
│           ├── order_block/
│           │   ├── __init__.py
│           │   └── test_detector.py
│           └── market_structure_shift/
│               ├── __init__.py
│               └── test_detector.py
│   └── runtime/                 S07: W1(firewall)/W2/W5/W6/W7/W8/W9
│       ├── __init__.py
│       ├── test_types.py
│       ├── test_belief.py
│       ├── test_contract.py
│       ├── test_consumption.py
│       ├── test_dashboard.py
│       ├── test_ea_source.py    static token-scan of RefusalEA.mq5
│       └── test_end_to_end.py   W8: SYNTHETIC verdict, published ->
│                                 consumed -> feedback ingested
├── .gitignore
├── BOOT_PROMPT_ARCHITECT.md
├── BOOT_PROMPT_DEVELOPER.md
├── pyproject.toml               project metadata, deps, pytest + ruff config
├── uv.lock                      lockfile
└── README.md
```

`runtime/` was added in S07 (A-029) — the transplant ruling (A-028) found no
clean thin-hands boundary to import from F:\Fable, so every file under it is
written fresh, quarrying F:\Fable for MECHANICS only (terminal lifecycle,
file staging), never for pattern logic or bytes. Nothing under it may import
qrf.kernel — see `tests/test_firewall.py::test_wall_holds_with_real_runtime_code`
for the wall proven against real content, not an empty directory.

`comms/` lives outside the repo (`.gitignore`d, per protocol). The reference
snapshot and previous era's comms live outside the repo entirely, under
`F:\NeelPrajnaProData\reference\`.

S02's stores are exercised only against `tests/` fixtures (`tmp_path`) in
this repo. A live deployment writes under `F:\NeelPrajnaProData\datastore\`,
in NEW, S02-specific paths kept clearly apart from the previous era's sealed
journal (per O-005, independent, not migrated): the record store at
`F:\NeelPrajnaProData\datastore\s02_records\` (`ledger.jsonl` + `bulk/`) and
the window ledger at `F:\NeelPrajnaProData\datastore\s02_windows\ledger.jsonl`.

S03 real exports: raw CSVs land in `F:\NeelPrajnaProData\incoming\` (never
in the repo); bound bulk copies + manifest live at
`F:\NeelPrajnaProData\datastore\s03_bulk\` /
`F:\NeelPrajnaProData\datastore\s03_bulk_manifest.jsonl`. Only the
provenance twins (`data/provenance/*.provenance.json`) are tracked in git —
per A-007 §3.2, git holds the PROOF of what the data was, never the data.
