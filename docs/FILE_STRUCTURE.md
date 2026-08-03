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
│       └── S01.md
├── tools/
│   └── run_job.sh              the Owner's one command; the Architect's job runner
├── qrf/                        the left organ (research/statistics)
│   ├── __init__.py
│   ├── errors.py                QRFError, SchemaViolation, IntegrityViolation,
│   │                            WriterLockHeld, ChainCorruption, TornTail,
│   │                            BulkMismatch, WindowConflict, LedgerImbalance
│   └── kernel/
│       ├── __init__.py
│       ├── records/             S02: the record store (evidence as proof)
│       │   ├── __init__.py
│       │   ├── store.py          RecordStore — append-only, hash-chained,
│       │   │                     single-writer, torn-tail detection
│       │   └── bulk.py           BulkStore — hash-binds bulk files to a manifest
│       └── windows/             S02: the window ledger (market time as a
│           ├── __init__.py       spendable, accounted resource)
│           └── ledger.py         WindowLedger — reserve/burn/balances
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
│   └── windows/                 S02: D9-D14 (window ledger drills)
│       ├── __init__.py
│       └── test_ledger.py
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
Nothing is written there yet — S02 has no real data to store (S03 begins
ingest).
