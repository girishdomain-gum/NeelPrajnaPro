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
│   └── SPRINT_EXECUTION_MODEL_v2.md
├── qrf/                        the left organ (research/statistics)
│   ├── __init__.py
│   ├── errors.py                QRFError, SchemaViolation, IntegrityViolation
│   └── kernel/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              shared fixtures
│   ├── test_smoke.py            proves qrf imports, the suite runs
│   ├── test_firewall.py         THE WALL: qrf/ <-> runtime/ import ban
│   └── drills/
│       ├── __init__.py
│       ├── harness.py            control/tampered drill harness, reused by every later sprint
│       └── test_harness_selftest.py   proves the harness itself can fail
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
