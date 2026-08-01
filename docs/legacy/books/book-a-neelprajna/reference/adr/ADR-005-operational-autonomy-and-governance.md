# ADR-005 — Operational autonomy and human governance

- Status: **ACCEPTED** — owner ruling recorded 2026-07-27 (§9)
- Date: 2026-07-27 · rev 2 after Chief Scientist review (§2 goal wording,
  §6 supervisor boundary, §7 immutable evidence) · rev 3 owner ruling
- Context: owner's stated requirement — "0% involvement in the
  development or validation process; I participate as reviewer, planner,
  designer, architect" — plus the reviewer's Autonomous Engineering
  Laboratory proposal.
- Relates to: automation v2 design v1.1 + amendment v1.2 (design freeze),
  ADR-001 (layering), ADR-004 (evidence rules).
- This is a principles ADR, not a design revision. It does not unfreeze
  the design. Implementation items go to `PARKED.md` with a stage number.

---

## 1. Decision

**Operations are automated to the maximum the machine allows. Governance
stays human. The two are named separately and never traded against each
other.**

**Operations** (target: no owner action in the normal path): writing code,
compiling, deploying, launching terminals, running experiments,
regression, collecting and validating evidence, generating passports and
review packages, health monitoring, recovery after reboot, queue
management.

**Governance** (owner only, permanently): approving architectural change,
changing scientific methodology or acceptance criteria, defining what
question an experiment answers, promoting or retiring a golden baseline,
marking a window BURNED, arming anything that touches a real account,
approving a release.

## 2. The goal statement

Rev 1 said "0% is not achievable". That mixed two different things and the
reviewer was right to separate them:

> **The platform shall require zero routine operational involvement.
> External governance events and environmental failures remain outside the
> platform's control.**

Accepted as written, with one addition, because "outside our control" must
not become a place where costs hide. From the owner's chair, an
environmental failure still costs a touch. So autonomy is measured with
**two counters** in the weekly health report:

- **Routine touches — target 0. Any non-zero value is a platform defect**
  and gets a fix, not an explanation.
- **Exception touches — external cause** (power cut, broker password,
  forced MT5 update, disk failure). Not defects, but counted, named, and
  reviewed for whether the platform could have absorbed them.

The distinction is honest and the count keeps it from becoming an excuse.

## 3. The autonomy ladder

| Level | Meaning | Routine touches |
|---|---|---|
| L0 | Owner runs deploy, F7, tester, uploads results | ~4 per iteration (where we were) |
| L1 | Owner starts the watcher; Claude drives jobs | 1 per session |
| L2 | Supervisor starts at boot, recovers, self-tests; experiments queue and run unattended | 1 per runner change (D0 restart) |
| L3 | Runner code changes adopt themselves behind the trust split | 0 |

A1 + A2 reach **L2**. L3 arrives with G3 (§4).

## 4. The bootstrap paradox

"Never needs a human restart" and D0 ("the agent runs only code that was
on disk when the owner started it") cannot both be true. If the agent
adopts Claude-written code with no human, Claude can change what this
machine executes, unsupervised.

- **G1 — keep D0.** One double-click per *runner code change*, not per
  experiment. Strongest boundary, lowest autonomy.
- **G2 — self-adopting runner behind a policy gate.** Weakness: the policy
  is enforced by the same mutable code it polices.
- **G3 — split the trust (recommended).**
  - **Supervisor** — small (target < 300 lines), boring, frozen. Owner
    installs and reviews it once. Process lifecycle, restart policy,
    heartbeat, health aggregation, recovery, shutdown. **Claude may not
    write to it.** Its hash is recorded in every manifest.
  - **Runner** — everything else. Mutable, Claude-authored, restarted
    freely by the supervisor.

G3 gives L3 for experiments and runner code while the machine's ability to
recover, report and stop stays anchored in code the owner has read. Blast
radius of a Claude mistake becomes "the experiments are wrong", never
"the machine cannot be stopped".

## 5. Outside the platform's control (named, not hidden)

Environmental and external dependencies, listed so they are recognised as
exception touches rather than mistaken for platform failure:

1. **Windows must be logged in** for MT5 to run. After a power cut the
   machine waits at the login screen. Auto-login solves it and is a
   security trade on a machine holding trading accounts (§9.3).
2. **Broker credentials** — password changes, server moves, 2FA, expired
   demos. Claude never handles these; the agent does not store them.
3. **MT5 auto-updates itself.** A new build can change results silently
   and break every golden baseline. Mitigation: terminal build number in
   every manifest, and a build change marks results NOT COMPARABLE.
   Prevention is partial at best.
4. **Broker-side reality** — history gaps, outages, symbol spec changes.
5. **Machine reality** — disk, antivirus, forced reboots, drivers.
6. **Governance** (§1), by choice.

Standing rule: when the system is broken it **says so, names the cause,
and refuses to run**. Fail closed. The current agent warns about a missing
terminal path and continues — that is how it came to point at a folder
that does not exist on this machine.

## 6. Supervisor boundary

Adopted from the review: **the supervisor knows nothing about MT5,
MetaEditor, brokers, NeelPrajna or experiments.** Domain knowledge lives
in the runner's **preflight module**, which publishes a health report.
This keeps the supervisor small and reusable.

One correction, because the reviewer's version has a hole. If the
supervisor merely asks the runner "are you healthy?", then a broken runner
reports on itself — the exact failure this ADR exists to prevent. So the
responsibilities split by **what can be observed without domain
knowledge**:

**Supervisor observes directly** (all domain-free, all generic to any
process supervisor): process alive; heartbeat freshness; exit codes;
restart count and crash-loop detection; log file growth; free disk;
orphaned work items at startup; age of the last health report.

**Runner's preflight publishes** (domain-specific): terminal and
MetaEditor exist and are executable; terminal build number; EA version and
.ex5 hash; symbol history available; bridge writable; dictionary version.

**The joining rule: a missing or stale health report is DEGRADED, never
"unknown".** Silence is a negative result. The supervisor never needs to
understand the report's contents to act on its absence.

Health states: `HEALTHY` / `DEGRADED` / `FAILED`. **DEGRADED refuses to
start experiments.** It does not warn and continue.

## 7. Immutable evidence

Adopted from the review, and it belongs beside ADR-004's evidence
philosophy.

**Once a bundle reaches COMPLETE it is sealed. Evidence is append-only.**

- Sealing writes a `SEALED` marker plus a SHA-256 of every artefact.
  Files are marked read-only on disk. The runner has no delete capability
  and never gains one.
- Improvements are **additive, never in place**: `analysis_v2.md`,
  `validation_v2.json`. The bundle index records that v2 supersedes v1;
  v1 stays.
- **A bundle that fails validation is never repaired.** It stays
  INCOMPLETE for ever and a new run is made. Repairing evidence to make it
  pass is the one thing that would make the whole archive worthless.
- Re-analysis with a better model, a better validator or a better renderer
  produces new artefacts and a new record — never a rewritten past.

**Interaction with D19 (capture is a separate pass).** The visual capture
pass runs *after* the measured run, so it cannot write into a sealed
bundle. Resolution: the run bundle seals when the run completes; a capture
pass writes a **child bundle** (`visual_001/`) with its own manifest that
records the parent bundle's hash. Parent stays sealed; evidence stays
linked; both remain append-only. Two later capture passes therefore
coexist as `visual_001/` and `visual_002/` rather than one overwriting the
other.

## 8. The Automation Terminal

A named system role, owned entirely by the platform: never opened by a
human, never carrying a chart, never trading.

Two facts ride with it, because policy alone does not make a terminal
interchangeable:

- **The tester runs the `.ex5` in that terminal's own data folder.**
  Pipeline: build workspace → compile → deploy the .ex5 into the
  automation terminal's data folder → run.
- **The terminal is part of experiment identity.** It carries a broker:
  symbol name, spread, contract spec, trading hours, tick history.
  Changing it invalidates every golden baseline. Terminal path, broker,
  server, account type and terminal build go in every manifest; changing
  them is governance, not operations.

Recommended shape: a **dedicated portable install** used by nothing else,
with a self-contained data folder. Whether `/portable` also isolates
`Common\Files` — which would incidentally fix the parallel-run CSV
collision — is verified in A1, not assumed.

## 9. Owner ruling — recorded 2026-07-27

1. **Trust model: G3 — APPROVED.** Supervisor and Runner are permanent,
   separate trust domains. Supervisor: frozen, owner-reviewed, owns
   lifecycle. Runner: mutable, owns experiments and evidence.
2. **Fail-closed — APPROVED.** Scientific correctness outranks throughput.
   Missing or degraded prerequisite → refuse execution, report the reason.
   "No experiments today" beats untrustworthy evidence.
3. **Laboratory allocation — RULED.**
   - `MetaTrader 5 EXNESS` → **primary automation laboratory**
     (data folder `53785E09…`, which is already the deploy/compile target)
   - `Vantage International MT5` → secondary automation, if needed
   - `Winprofx MT5 Terminal` → **human** terminal: manual development,
     review, investigation, UI sign-off
   Manual work and automation are physically separated.
4. **Auto-login — DEFERRED (revised 2026-07-27 evening).** Initially
   approved; the owner then held it for future work. Windows auto-login is
   NOT enabled.
   - Consequence, recorded honestly: after a reboot or power cut the machine
   waits at the login screen and the laboratory does not return until a human
   logs in. Autonomy is therefore capped at **L2** for recovery, not L3.
   Each such event is an **exception touch** (§2), external in cause, and is
   counted rather than explained away.
   - Separate and still required for unattended runs: the laboratory MT5
   terminal must save its trade-account credentials, or an automated backtest
   starts a terminal that never connects. That is a terminal setting, not a
   Windows one, and its risk is bounded by the account it holds — which is
   why real-money profiles do not belong in the laboratory terminal.
   - To be revisited before any real-money account is hosted on this machine,
   and before unattended overnight batches (A5) are relied upon.
5. **Laboratory identity is permanent.** Changing broker, server, account
   type, terminal build lineage or automation terminal starts a **new
   experiment lineage**. Historical baselines stay valid only inside the
   environment that produced them.

### 9.1 The laboratory is production infrastructure (owner rule)

Even during development, the automation terminal is treated as production:
no manual edits inside it, no opening MetaEditor there by hand, no
settings changed by hand, no files copied by hand, no experimental
scripts. Everything flows through the automated pipeline. This keeps the
laboratory deterministic and reproducible from day one.

One engineering exception, stated so it is not mistaken for a breach:
**the pipeline itself uses the laboratory's own MetaEditor to compile**,
because compiler and terminal build must match or the `.ex5` may be
rejected. That is automated use, not manual use. No human opens it.

Consequence to schedule: `deploy.bat` targets the laboratory. Human UI
sign-off happens on Winprofx, which therefore needs its own deploy target.
A second deploy path is added in A1 (`deploy_human.bat`) — parked until
UI sign-off is next needed.

### 9.2 Traceability invariant (added after A1 was authorised)

**Every autonomous decision must be traceable to deterministic evidence.**
Whenever the platform rejects a run, restarts a process, marks a bundle
DEGRADED, refuses execution, or publishes a conclusion, the record must
contain enough for a human to reconstruct why. In practice: every refusal
names the failing check, its observed value and its threshold — never just
"preflight failed".

## 10. Consequences

- The human-only list from AUTOMATION_BRIDGE §2 is unchanged, and is now
  understood as *governance*, not a temporary automation gap.
- "Smoke test by the owner" is removed from every procedure. The
  supervisor self-tests; the owner reads a result.
- Reports change voice: never "did it pass?" to the owner, always "it
  passed because…" or "it failed because…", with the bundle attached.
- Design freeze holds, with the exception the reviewer names and this ADR
  affirms: **implementation discoveries may change the design; speculative
  improvements may not.** A discovery is recorded with its evidence, as an
  ADR or an amendment, in the same commit as the change it causes.
- Renaming the programme (Autonomous Engineering Laboratory) stays
  **parked**. Names follow a working system; they do not lead it.
- The first start of the supervisor on a fresh machine is human. Once.
  That is the floor, and it is an installation step, not an operation.

---

## 11. Read-only status glances at the laboratory terminal (owner request, 2026-07-28)

- Status: **ACCEPTED**, narrow exception. Everything else in section 3's
  "never opened by a human, no charts, no trading" rule for EXNESS stands.

### 11.1 The problem this solves

R6 and runs like it take hours. Waiting idle for a status file to appear is
a worse use of the owner's time than a glance at the running terminal.
That need is real and this ADR should not pretend otherwise.

### 11.2 What the original rule was actually protecting against

Not "a human must never see the screen." It was protecting against a human
**acting** on the laboratory terminal — trading, changing settings, editing
inputs, picking a symbol by hand — the things a manual terminal does that
an automation terminal must never do, because they make a run
non-reproducible and cannot be recorded in a manifest.

Looking at a window in progress does not touch any of that, provided
nothing is clicked. The risk is not seeing; it is touching.

### 11.3 What is permitted

- Opening the EXNESS terminal window to **look** at the Graph and Journal
  tabs of a **running** Strategy Tester pass, purely to gauge progress, and
  optionally to screenshot it for Claude.
- Nothing else. Not Settings, not Inputs, not Trade, not Symbols. Not
  clicking anything, ever, while a job is running — **most of all not the
  Stop button**, which sits directly beside the Journal pane. One misclick
  loses the run: no report file, signal 1 fails, nothing sealed, nothing to
  redo it from. Look, do not touch.
- This is a **viewing** exception, not a monitoring duty. The owner is not
  obligated to check; Claude does not ask for a check. "Bring me a
  screenshot" is not a job type and never will be (ADR-006 boundary).

### 11.4 What stays absolutely forbidden, no exception

- Opening the terminal **during A4 visual-capture work**, once that stage
  exists. Window state, focus and z-order will matter to `ChartScreenShot`
  captures at that point, and a casual-glance habit formed now must not
  carry over into interfering with it later. When A4.0 is scheduled, this
  section is revisited before that work starts.
- Anything on the list in section 1 under Governance, or the human-only
  list in section 10 — none of that is touched by this addition.
- Opening the terminal to **make** a decision (should this run be killed,
  is this result good) rather than to observe progress. A decision reached
  by eye, off-manifest, is exactly what ADR-004's evidence rules exist to
  prevent.

### 11.5 Owner ruling

> Ruling: **APPROVED**, scoped exactly as sections 11.3–11.4 describe.
>
> Date: 2026-07-28
