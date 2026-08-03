# MASTER SPRINT PLAN v2 — NeelPrajnaPro, fresh-start build
**Status:** DRAFT v0.2 for Owner approval. Written by the ARCHITECT under
docs/SPRINT_EXECUTION_MODEL_v2.md stage 2 (Owner orders O-072..O-079).
**Baseline:** empty tree at main 6941042. Reference snapshot (READ-ONLY):
`F:\NeelPrajnaProData\reference\NeelPrajnaPro_v1` @ commit 67b1d69.
**Changed in v2 (Owner order O-079):** eight sprints instead of twelve;
REWRITE-FROM-SCRATCH ruled as the build law (§1.1).

---

## 0. The objective (Owner's words, O-078)

Same objective as before. NeelPrajnaPro is a **research system**:

- **LEFT ORGAN — QRF (`qrf/`)**: the judge. It proves or refuses trading
  hypotheses with statistical evidence that cannot be gamed.
- **RIGHT ORGAN — NeelPrajna runtime (`runtime/`)**: the hands. It trades.
- **The flow:** QRF proves a hypothesis → publishes sealed knowledge → the
  runtime consumes it. Execution feedback flows back as observations.
- **The wall, permanent and two-sided:** QRF never trades; the runtime never
  learns on its own. The only crossing surface is the Contract.

## 1. Build law and cutting principles

### 1.1 REWRITE FROM SCRATCH (Owner ruling O-079) — binding
The Developer **writes every line fresh, and tests and validates it himself.**
The reference snapshot and all previous work are **INPUT ONLY**: read them,
learn from them, take ideas, designs, formulas, constants and hard-won lessons
from them — but no file is copied into the new tree.

Why the Owner's rule is right: copied code carries assumptions nobody living
still remembers, and a system whose job is to refuse unproven claims cannot be
built on unexamined inheritance. Rewriting forces every design decision to be
re-understood before it is re-made.

What this does NOT mean: it does not mean ignoring the reference. Re-deriving a
sealed constant by hand and getting a different number is a FINDING, not a
correction — stop and ask. Where the reference documents a decision (DOC-IS-SPEC),
the doc still governs.

Citation duty: when a design comes from the reference, the new code's docstring
says so — "design after reference/NeelPrajnaPro_v1 @ 67b1d69, re-implemented".

### 1.2 Cutting principles
1. **One gated or irreversible thing per sprint.** Never a burn and a
   transplant in the same sprint.
2. **Foundations before users.** A store nobody can trust makes every later
   verdict worthless, so the ledger and window accounting come before any
   detector.
3. **Every sprint ends in something demonstrable** — a passing drill, a real
   number, a file the Owner can open. Never "framework progress".
4. **No checker is trusted until it has been shown to FAIL** (drill law:
   control GREEN, tampered RED). Every sprint's validation obeys this.
5. **The transplant travels alone.**
6. **Judge on a stable tree.** No judgment in a sprint that also restructures.
7. **Sealed things stay sealed.** `datastore\` — the journal, window ledger and
   H-07 lineage — is READ-ONLY to the rebuild (ruling O-079). The new system
   reads it; it never rewrites or re-judges it. Writing there is a stop-and-ask.

## 2. The sprint map (eight sprints, S01..S08)

| # | Name | One-line purpose | Human gate |
|---|---|---|---|
| S01 | Foundation | Empty root → running project, CI, two-sided firewall skeleton, drill-law harness | Owner sign-off |
| S02 | Ledger & Windows | Tamper-evident record store + market time as a spendable, accounted resource | Owner sign-off |
| S03 | Observation | MT5 export → external evidence store → hash verification → ingest; server-clock self-policing | Owner sign-off |
| S04 | Detector 1 | Liquidity-sweep detector (H-07 track), planted-truth / clean-control drills | Owner sign-off |
| S05 | Null, Battery & Registration | The judge: block-resampling null, EvidenceBattery (sole verdict writer, atomic verdict+burn), pre-registration + trial ledger | **Owner ceremony (typed phrase)** |
| S06 | Judgment | First real existence judgment on fresh un-burned time + independent IVF re-derivation | **Owner V9 (burn word)** |
| S07 | Transplant & Detector 2 | Runtime organ imported to `runtime/`, firewall drilled RED both ways; CCC/MML detector (H-08) with parity proof | Import blocks (Owner-run) |
| S08 | Contract & Consumption | Belief update, sealed knowledge release, Contract objects, Publication Boundary, runtime consumption + execution feedback, mirror dashboard | **Owner ruling** |

**Recurring background thread (S03 → S08):** real market data collection. Never
a sprint of its own; each sprint's report states what was collected.

**Permanently outside the cycle:** Pattern Evolution Wave-2 — hard-locked. No
sprint may start it under any amendment.

**Note on the merges (v1 → v2):** v1's Ledger+Windows became S02 (both are one
discipline: accounting you cannot fake). v1's Null&Battery+Registration became
S05 — the machinery and the act of freezing what it will test belong together.
v1's Transplant+Detector 2 became S07 (the CCC reference arrives with the
runtime, so porting it in the same sprint avoids a pointless wait). v1's
Contract+Consumption became S08. Every gated act still sits alone.

## 3. Per-sprint detail

Each sprint's briefing expands these into implementation-ready detail. All code
is written fresh by the Developer per §1.1.

---

### S01 — FOUNDATION
- **Features:** a project that runs, tests itself, and enforces its own wall
  before there is anything to wall off.
- **Modules:** package skeleton, test harness, CI workflow, the two-sided
  firewall test, the drill-law harness every later sprint uses.
- **Folders/files:** `pyproject.toml`, `uv.lock`, `README.md`,
  `.github/workflows/ci.yml`, `qrf/__init__.py`, `qrf/kernel/__init__.py`,
  `tests/`, `tests/test_firewall.py`, `tests/drills/`, `docs/FILE_STRUCTURE.md`.
- **Validation:** suite green from a clean checkout; firewall shown **RED**
  against a planted violating import and **GREEN** once removed; CI runs on push.
- **Outcome:** plumbing is never touched again; the wall exists from day one.

### S02 — LEDGER & WINDOWS
- **Features:** (a) an append-only, tamper-evident record store; (b) market
  time as a spendable, accounted resource.
- **Modules:** RecordStore (hash-chained, single-writer, torn-tail detection),
  BulkStore + schemas, WindowLedger (TRAINING / EXPLORATION / VIRGIN,
  burn-on-use, reserve-by-market-time), window-accounting checker.
- **Folders/files:** `qrf/kernel/records/*`, `qrf/kernel/protocol/windows.py`,
  `tests/kernel/records/*`, `tests/kernel/protocol/*`.
- **Validation — drills RED on:** altered record · deleted record · torn tail ·
  second concurrent writer · schema violation · double-burn · reuse of a burned
  window · designating seen time as VIRGIN · ledger arithmetic that fails to
  balance. Control runs GREEN.
- **Outcome:** everything written from here on is provably unaltered, and
  contaminated evidence becomes structurally impossible rather than a matter
  of discipline.

### S03 — OBSERVATION
- **Features:** real market data enters with its integrity proven.
- **Modules:** MT5 exporter, provenance verifier, ingest, server-clock pinning
  and self-policing (DST invariants).
- **Folders/files:** `ivf/mt5/*`, `scripts/verify_provenance.py`,
  `scripts/ingest.py`, `qrf/kernel/protocol/clock.py`, `data/` provenance twins
  (tracked). **Bulk CSVs live at `F:\NeelPrajnaProData\incoming` — never in git.**
- **Validation:** a real XAUUSD export the Developer performs himself through
  the MT5 terminal; sha256 bound into the provenance twin; ingest **refuses
  loudly** on a one-byte-altered copy (drill RED); boundary check refuses on a
  drifted server clock.
- **Outcome:** every later number traces to a dataset provably byte-identical
  to the one it was computed from.

### S04 — DETECTOR 1
- **Features:** the liquidity-sweep detector (H-07 track) observing real bars.
- **Modules:** `qrf/trading/concepts/neelprajna/liquidity_sweep.py`.
- **Folders/files:** that package, `tests/concepts/neelprajna/*`,
  `configs/hypotheses/h007_*.yaml`.
- **Validation:** planted-truth cases detected; clean-control cases produce
  nothing — both mandatory before any registered observation. Behaviour checked
  against the sealed detector specification in the reference; **a divergence is
  a FINDING to report, not a thing to quietly match.**
- **Outcome:** a detector whose false-positive and false-negative behaviour is
  demonstrated, not assumed.

### S05 — NULL, BATTERY & REGISTRATION *(Owner ceremony)*
- **Features:** the machinery that decides whether an effect is real, and the
  discipline of freezing what will be tested before testing it.
- **Modules:** block-resampling null (empirical p by the add-one estimator —
  it must never be able to return an unattainable 0.0), EvidenceBattery (sole
  verdict writer, atomic verdict+burn), TrialCountLedger, registration flow,
  hypothesis config hashing.
- **Folders/files:** `qrf/kernel/battery/*`, `qrf/kernel/corrections/*`,
  `configs/hypotheses/*`, `tests/kernel/battery/*`, `docs/REGISTRATION.md`.
- **Validation:** null distribution reproducible from a seed; known-answer test
  on a synthetic planted effect; **drills RED on** a non-atomic verdict+burn ·
  a second writer attempting a verdict · a schema-invalid input · an attempt to
  un-spend a registered attempt · a post-registration threshold edit.
  The block length is **derived from the hypothesis's own constants** by a
  stated zero-discretion rule — never inherited.
- **Outcome:** the judge exists, its refusals are demonstrated, and the system
  cannot quietly test until it likes the answer.
- **HUMAN GATE:** the Owner's typed designation phrase. The machine prepares;
  only the Owner registers.

### S06 — JUDGMENT *(Owner V9)*
- **Features:** the first real verdict, and an independent re-derivation of it.
- **Modules:** judgment runner; IVF re-derivation path.
- **Folders/files:** `ivf/*`, `tests/ivf/*`; verdict artifacts written to the
  new store; reports and screenshots under `F:\NeelPrajnaProData\`.
- **Judged on:** fresh, un-burned window time (ruling O-079). **H-07's existing
  sealed verdict is not re-judged** — its alpha is spent and its windows burned;
  a second answer on the same evidence is not a second piece of evidence.
- **Validation:** the Battery's verdict and IVF's independent re-derivation
  agree; **any discrepancy is a HIGH finding that freezes the result** — never
  resolved by preferring the friendlier number.
- **Outcome:** a real, defensible verdict produced by machinery built entirely
  in this cycle.
- **HUMAN GATE:** the Owner's typed burn word, one sitting, countersigned.

### S07 — TRANSPLANT & DETECTOR 2
- **Features:** the right organ comes home, the wall becomes mechanical, and
  the second hypothesis track is built.
- **Modules:** `runtime/mql5/`, `runtime/supervisor/`, `runtime/npsu/`,
  `runtime/dashboard/`, `runtime/docs/`; `qrf/trading/concepts/ccc/`.
- **Import law:** the PLAN names every single file **before** anything is
  copied; each carries "copied from `F:\Fable` @ \<commit\>" plus its sha256.
  `F:\Fable` is READ-ONLY — never modified, never worked in. The runtime is
  imported as-is source (it is the other organ, not part of the QRF rewrite);
  §1.1's rewrite law governs the new QRF side, and the CCC **detector** is
  written fresh in Python from the reference as specification.
- **Validation:** two-sided firewall drilled **RED both ways** — `qrf/` may not
  import `runtime/`; `runtime/` may not import `qrf.kernel`. MQL5 sources
  token-scanned. The import compiles, deploys and arms **nothing**. CCC:
  **parity proof** against the in-repo MQL5 reference on real XAUUSD, plus
  planted-truth and clean-control drills.
- **Quarantine (binding):** measured priors are EVIDENCE, never parameters;
  thresholds frozen at registration.
- **Outcome:** one body, one root, one CI, one firewall over both organs, and
  a second independent hypothesis track that borrows neither evidence nor alpha
  from the first.

### S08 — CONTRACT & CONSUMPTION *(Owner ruling)*
- **Features:** knowledge becomes publishable without leaking method, the
  runtime consumes it, and feedback returns as observations.
- **Modules:** belief layer (updates from Verdict-typed inputs only), knowledge
  release format, Contract object schemas, Publication Boundary, runtime-side
  consumption, execution-feedback ingestion, dashboard.
- **Folders/files:** `qrf/kernel/belief/*`, `qrf/contract/*`, `tests/contract/*`,
  `runtime/` consumption module, `dashboard/`, `docs/CONTRACT.md`,
  `docs/DASHBOARD_DESIGN.md`.
- **Validation:** a non-Verdict input is REFUSED (drill RED); an unsealed or
  rolling statistic cannot cross the boundary (leak drill RED); a release is
  byte-reproducible from the ledger; end-to-end on paper — published →
  consumed → feedback ingested as observations. **The dashboard is a MIRROR:
  it watches, it never steers.** Act buttons live only in the EA's own panel.
- **Outcome:** the loop closes. QRF publishes WHAT it knows, never HOW. The
  machine may recommend; **only the Owner arms — forever.**
- **HUMAN GATE:** the Owner's integration ruling.

## 4. The folder structure, first sprint to last

```
F:\NeelPrajnaPro\
  README.md  pyproject.toml  uv.lock  .gitignore  .gitattributes
  GIT_WORKFLOW.md  BOOT_PROMPT_ARCHITECT.md  BOOT_PROMPT_DEVELOPER.md
  .github\workflows\            S01
  qrf\                          the LEFT organ (the judge)
    kernel\
      records\                  S02   store, bulk, schemas
      protocol\                 S02/S03  windows, clock
      battery\                  S05   battery, block null
      corrections\              S05   trials
      belief\                   S08
    trading\concepts\
      neelprajna\               S04   liquidity sweep (H-07)
      ccc\                      S07   MML hidden patterns (H-08)
    contract\                   S08
  runtime\                      the RIGHT organ (the hands) — born S07
    mql5\  supervisor\  npsu\  dashboard\  docs\
  ivf\                          S03/S06  independent verification + MT5 export
  scripts\                      S03   ingest, provenance verification
  configs\hypotheses\           S04/S05/S07
  tests\                        every sprint; mirrors qrf\ + drills\
  datastore\                    the real journal + window ledger (SEALED, read-only)
  data\                         provenance twins only (tracked); never bulk
  docs\                         plan, architecture, structure, contract, retros
  comms\                        live, NEVER in git
```

**Outside the repo, by law:**
```
F:\NeelPrajnaProData\
  incoming\                      raw exports (bulk, never git)
  reference\NeelPrajnaPro_v1\    the read-only snapshot @ 67b1d69 (INPUT ONLY)
  reports\  logs\  screenshots\  all Developer run evidence, per sprint
```

**Standing rule:** the tree wins over the doc. Any divergence between the real
tree and this map is a FINDING, raised, never silently reconciled.

## 5. How each sprint runs

1. Architect opens the sprint with a complete briefing — enough to finish
   without asking. A blocking question means the briefing was defective.
2. Developer **writes, tests and validates the whole sprint alone**, compiles
   and runs MT5 himself, and writes all logs, reports, analysis and screenshots
   to `F:\NeelPrajnaProData\`.
3. Developer reports completion via the standard inbox message.
4. Architect verifies and reviews all development and validation.
5. **Owner reviews manually** — his eyeball, never a relayed claim.
6. Retrospective written → sprint CLOSED on the board → next sprint opens.

Every sprint-close report ends with the Owner's plain-English inventory: what
was built, how many folders and files were introduced and their names, the
running project total, and where the evidence lives.

## 6. What carries over unchanged

Completion rule · drill law · two-key for anything real · one live window per
role · append-only comms with ids · no history rewrite, no force-push ·
AMENDMENTs only from the Architect · sealed lineages stay sealed · Wave-2
hard-locked · `ivf/verify_*` protected · the Owner arms everything real.
