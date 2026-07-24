# ARCH-001 · Sprint 1 — Ledger Core · 2026-07-24 (rev 2)
Author: architect (fable) · Level: INSTRUCTION · Status: OPEN
Rev 2: added Session 0 (git initialization) — previously assigned to
Owner; reassigned to Developer, remote push remains Owner-side.

## Session 0 — repository initialization (do this first, once)
1. `git init` in the repo root (F:\QRF); default branch `main`.
2. Create `.gitignore` BEFORE the first commit: `datastore/bulk/`,
   `datastore/index/`, `__pycache__/`, `.venv/`, `*.pyc`,
   `experiments/` artifacts. `datastore/journal/` IS tracked.
3. First commit: everything currently in the tree, message
   `ARCH-001: initial commit — docs, structure, coordination protocol`.
4. Do NOT create or push to any remote — the Owner adds the private
   remote and pushes. Leave a line in your completion report reminding
   the Owner this is pending.

## Read first (in this order)
1. `docs/coordination/PROTOCOL.md` (your role)
2. `docs/implementation/Implementation_Blueprint_v1.0.md` §0, §1, §2
   (record schema — normative), §3 (file layout), §4.1 (RecordStore),
   §6 (errors), §7 Sprint 1
3. `docs/adr/ADR-002` and `ADR-003` (why the ledger is shaped this way)
4. `CONTRIBUTING.md`

## Scope (build exactly this)
Sprint 1 per Blueprint §7: the ledger core plus project plumbing.

## Out of scope (do NOT build now)
BulkStore beyond a stub, detectors, adapters, battery, belief,
observatory, dashboard, any `qrf/trading/` code, MLflow, vectorbt.
Empty packages may receive `__init__.py` only.

## Deliverables (exact paths)
```
pyproject.toml                  # py3.13; deps: python-ulid, duckdb,
                                #   pyarrow, pandas, pandera, pytest, ruff
uv.lock                         # committed
.gitignore                      # per Session 0
.github/workflows/ci.yml        # uv sync; ruff; pytest (all tests)
qrf/__init__.py  qrf/kernel/__init__.py  (+ __init__.py per package dir)
qrf/kernel/errors.py            # full taxonomy, Blueprint §6, verbatim classes
qrf/kernel/records/record.py    # Record (frozen dataclass), canonical_bytes,
                                #   content_hash, ULID generation
qrf/kernel/records/schemas.py   # payload validation for: note, amendment,
                                #   instrument_registered  (v1 schemas, Blueprint §2)
qrf/kernel/records/store.py     # RecordStore per Blueprint §4.1 API
tests/test_kernel_firewall.py   # AST import scan of qrf/kernel/** forbidding
                                #   'qrf.trading' imports + forbidden identifier
                                #   tokens: price, bid, ask, spread, pip, lot, venue
tests/records/test_record.py    # canonicalization + hashing unit tests
tests/records/test_store.py     # store behaviour tests (list below)
scripts/gen_state.py            # v0: regenerates docs/handover/AI_PROJECT_STATE.md
                                #   status table from: ADR file list, git branch,
                                #   test result summary; preserves the two
                                #   hand-maintained sections verbatim
scripts/backup.ps1              # git add/commit/push + robocopy datastore/journal
                                #   to a configurable second path
```

## Key contracts (inlined so this file is self-contained)
Canonical serialization — copy exactly; the IVF re-implements this
independently from the spec text, so any deviation fails verification:
```python
def canonical_bytes(d: dict) -> bytes:
    return json.dumps(d, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
```
content_hash = sha256 over canonical_bytes of
`{record_type, schema_version, producer, event_ts, parents, payload}`.
prev_hash = previous record's content_hash; genesis = "0"*64.
Record fields, immutability, and invariants I-1..I-5: Blueprint §1 is
the single source — implement it as written; do not improvise fields.
Journal path: `datastore/journal/journal.jsonl`, one record per line,
append + fsync, single-writer file lock.

## Acceptance criteria
- `RecordStore.append/get/query/verify/resolve` work per §4.1.
- Tampering with any byte of any journal line → `verify()` raises
  `LedgerIntegrityError` naming that record_id.
- Appending with a nonexistent parent raises `UnknownParentError`;
  invalid payload raises `SchemaViolation` (all three v1 schemas).
- Amendment flow: append `amendment` targeting a record; `resolve()`
  returns the corrected view; original unchanged in journal.
- Fresh clone + `uv sync` + `pytest` = all green on a clean machine.

## Required tests (minimum)
test_record.py: canonical bytes stable under key order; float repr
cases; NaN rejected; hash matches a hand-computed vector (include one
hard-coded expected sha256 in the test).
test_store.py: round-trip; chain tamper detection (byte flip); parent
enforcement; schema rejection per type; amendment resolution;
crash-mid-append simulation (truncated final line detected on open,
healing requires explicit confirm flag); query filters (type, parent,
ts_range); ULIDs strictly increasing within a session.
test_kernel_firewall.py: passes on current tree; and (negative case,
via tmp file) detects a planted `from qrf.trading import x`.

## Definition of Done
Session 0 complete (repo on `main`, initial commit); all acceptance
criteria demonstrated; all tests green in CI config (CI runs on push
once the Owner adds the remote); ruff clean; `scripts/gen_state.py`
runs and updates the state file; completion report appended below; any
open DEVQs listed there.
Sprint formally closes only after IVF Sprint-1 checks (Verification
Framework §7 Sprint 1: independent `ivf/verify_journal.py` + human
5-record read + drill S1) — the Owner runs that step; your job ends at
the completion report.

## How to ask
Anything ambiguous → `docs/coordination/inbox/OPEN/DEVQ-NNN_slug.md`
per PROTOCOL.md. Known intentional gap: `ivf/verify_journal.py` is NOT
yours — the Architect writes it (independence rule IND-1); do not
implement it even though it is referenced here.

## COMPLETION REPORT (developer)
Author: developer (claude-code) · 2026-07-24 · Status: DELIVERED (awaiting IVF Go/No-Go)

### Session 0 — repository initialization
- `git init` on branch `main`; `.gitignore` written before the first commit
  (ignores `datastore/bulk/`, `datastore/index/`, `__pycache__/`, `.venv/`,
  `*.pyc`, `experiments/`, journal `*.lock`; `datastore/journal/` stays
  tracked). Added `.gitattributes` to force LF / mark the journal `-text` so a
  fresh clone reproduces byte-identically (AC).
- Initial commit `cc13b65` = docs + structure + coordination protocol.
- **PENDING (Owner):** no remote created or pushed. The Owner must add the
  private remote and `git push -u origin main`. CI (`.github/workflows/ci.yml`)
  runs on push once the remote exists.

### What was built (exact paths)
- `pyproject.toml` (py3.13; deps python-ulid, duckdb, pyarrow, pandas, pandera;
  dev: pytest, ruff; ruff + pytest + `[tool.qrf]` config) and committed `uv.lock`.
- `.github/workflows/ci.yml` — `uv sync --locked` → ruff → pytest.
- `qrf/` + `qrf/kernel/` + all package `__init__.py` (trading subtree stubs only).
- `qrf/kernel/errors.py` — full §6 taxonomy, verbatim class names.
- `qrf/kernel/records/record.py` — `canonical_bytes` (verbatim §1.3), `content_hash`
  over the six semantic fields, monotonic ULID generation, frozen `Record` + wire I/O.
- `qrf/kernel/records/schemas.py` — v1 payload schemas for note / amendment /
  instrument_registered; unregistered `(type, version)` → `SchemaViolation`.
- `qrf/kernel/records/store.py` — `RecordStore.append/get/query/verify/resolve`
  (§4.1); append-only, single-writer file lock (msvcrt/fcntl), per-line fsync,
  hash chain, verify-on-startup, torn-tail detection + opt-in healing.
- `tests/test_kernel_firewall.py`, `tests/records/test_record.py`,
  `tests/records/test_store.py`.
- `scripts/gen_state.py` (v0, ADR-007) and `scripts/backup.ps1`.

### Test / verification results
- **35 tests pass**; ruff clean. Verified on a **fresh `git clone` + `uv sync
  --locked` + `pytest`** (all green) — the reproducibility AC.
- Acceptance criteria demonstrated by tests: chain tamper (byte flip) →
  `LedgerIntegrityError` naming the record; broken chain link detected;
  `UnknownParentError`; `SchemaViolation` for all three v1 types + unregistered
  type; amendment `resolve()` (original unchanged); truncated-final-line
  detection + heal-flag; query filters (type/producer/parent/ts_range); ULIDs
  strictly increasing; hand-computed sha256 vector; NaN/Inf rejected.
- Firewall: passes on the current kernel tree; negative cases prove it catches a
  planted `qrf.trading` import (direct + submodule) and a planted forbidden
  identifier, while allowing look-alikes (`pipeline`, `task`, `slot`).

### Deviations / not done, and why
- `scripts/gen_state.py` was built and verified (`--out <tmp>` diff touches only
  the header + Status table; hand-maintained sections preserved) but **not run
  against the real `docs/handover/AI_PROJECT_STATE.md`** — see **DEVQ-001**
  (QUESTION): the DoD asks the Developer to update a `docs/` file, which
  CLAUDE.md Hard rules forbid. Awaiting the Architect/Owner decision.
- `qrf.kernel.records` imports `qrf.kernel.errors` — documented in **NOTE-001**
  (FYI): interpreting Blueprint §3 "records is a leaf" as excluding the
  stdlib-only shared error module. Not enforced against by the firewall.

### Open DEVQs
- DEVQ-001 (QUESTION) — gen_state.py writing under `docs/` vs the Hard rule.
  Blocks only the "gen_state updates the state file" DoD line, nothing else.

### Commits (branch `main`)
cc13b65 initial · 2d7b83e plumbing · c681abb ledger core · b6973ab tests ·
416fbfc scripts · a6e0274 DEVQ-001 + NOTE-001 · (this report follows).
