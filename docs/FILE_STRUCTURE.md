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
│   └── retrospectives/
│       ├── S01.md
│       └── S02.md
├── tools/
│   └── run_job.sh              the Owner's one command; the Architect's job runner
├── mql5/
│   └── Scripts/
│       └── QRF/
│           └── ExportXAUUSD.mq5   S03: the MT5 script the launcher runs to
│                                  export XAUUSD bars (compiled .ex5 is
│                                  never tracked, per .gitignore)
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
│   │                            TerminalBusy, TerminalMismatch
│   └── kernel/
│       ├── __init__.py
│       ├── records/             S02: the record store (evidence as proof)
│       │   ├── __init__.py
│       │   ├── store.py          RecordStore — append-only, hash-chained,
│       │   │                     single-writer, torn-tail detection
│       │   └── bulk.py           BulkStore — hash-binds bulk files to a manifest
│       ├── windows/             S02: the window ledger (market time as a
│       │   ├── __init__.py       spendable, accounted resource)
│       │   └── ledger.py         WindowLedger — reserve/burn/balances
│       └── observation/         S03: first contact with the real world
│           ├── __init__.py
│           ├── symbols.py         exact-symbol enforcement (E1)
│           ├── provenance.py      the provenance twin: write_twin/verify (E2/E3/E7)
│           ├── clock.py           server-clock offset measurement + self-policing (E5)
│           ├── ingest.py          verify-then-bind into S02's BulkStore (E4/E6)
│           └── launcher.py        the ONLY module touching a live MT5 terminal:
│                                  launches Vantage by explicit path, runs the
│                                  MQL5 script, harvests, checks the pins
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
│   └── observation/             S03: E1-E7 (all terminal-independent; see
│       ├── __init__.py           launcher.py's own docstring for why
│       ├── test_symbols.py       run_export() itself has no CI test)
│       ├── test_provenance.py
│       ├── test_clock.py
│       ├── test_ingest.py
│       └── test_launcher.py
├── .gitignore
├── BOOT_PROMPT_ARCHITECT.md
├── BOOT_PROMPT_DEVELOPER.md
├── pyproject.toml               project metadata, deps, pytest + ruff config
├── uv.lock                      lockfile
└── README.md
```

`runtime/` does not exist yet (added in S07). The firewall test's
`SCANNED_ROOTS` constant already names it, so an empty side is checked and
passes trivially — it is never skipped.

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
