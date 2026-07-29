# Automation v2 — the Experiment Runner (design v1.0)

- Status: DESIGN. Not started. Written 2026-07-27 from the owner's
  automation note plus a code review of `tools/np_agent.py` (v1, shipped
  2026-07-23).
- Supersedes nothing. `docs/AUTOMATION_BRIDGE.md` stays the description of
  v1; this document describes what v2 should become and why.
- Author's stance: the owner's note is right about the destination. It is
  optimistic about the order. This document keeps the destination and
  changes the order.

---

## 1. Where we actually are today (honest reading)

`np_agent.py` v1 is ~250 lines. It is a **remote hands** tool, not an
experiment platform. It does three things — `deploy`, `compile`,
`backtest` — one at a time, when Claude asks. It has no memory, no
archive, no queue, no run identity.

Known facts, checked on the machine today (2026-07-27):

- `C:\NeelPrajna\bridge\` **does not exist**. No mailbox, no heartbeat.
  So the watcher has not been running. That is not a code failure; it is
  a lifecycle failure — nothing starts the watcher, so it stays down.
- `tests\longrun\` holds only README + PREDICTIONS + the .seq folder. No
  results archived there.
- The pieces v2 needs already exist and are unused by the agent:
  `tools/diff_deals.py`, `tools/seqgen.py`,
  `tests/phase6/make_phase6_configs.py`.

Weaknesses in v1 that will bite as soon as runs get longer (code review,
not speculation):

| # | Weakness | Consequence |
|---|---|---|
| W1 | Job file is read the moment it appears | A job file still being written parses as bad JSON, gets a FAIL status and is thrown into `done\`. Silent loss. |
| W2 | Job is moved to `done\` after the action returns | If the agent or machine dies during a 6-hour backtest, no status is ever written and the job vanishes. Claude cannot tell "never ran" from "died". |
| W3 | Success = `terminal64.exe` exit code 0 | MT5 returns 0 in cases where the tester did not produce a report. False "OK". |
| W4 | Harvest walks the terminal folder for `report_base*` and grabs Common\Files CSVs modified in the last 2 h | Time-window harvesting. Two runs in one evening can cross-contaminate. |
| W5 | No run identity | The report says nothing about which EA version, which .set, which .seq hashes, which broker, which tick data produced it. Two weeks later the file is evidence of nothing. |
| W6 | Results pile up in one flat `bridge\results\` folder | No archive, no comparison, no cleanup. |
| W7 | No watchdog | A hung tester holds the queue for the full 24 h timeout. |

W1, W2 and W5 are the important ones. W5 is the one that destroys value
quietly.

---

## 2. What the owner asked for, restated

From the owner's note, the target is: **experiments run without a human
in the loop.** Prepare experiment → launch MT5 → wait → collect → archive
→ next. Hundreds of them. Regression across EA versions, brokers,
symbols, spreads, date ranges, modelling modes and parameter sets. Keep
MT5-specific logic in one component so NeelPrajna just asks for a result.

I agree with all of that as a destination, including the architecture
recommendation — that one is exactly right and is D3 below.

Where I push back: "hundreds of experiments" is a capability, and on this
project it is currently a **liability multiplier**, not an asset. See §11
and §13. The runner should be built so that it makes good evidence cheap,
not so that it makes searching cheap. Those are different machines.

---

## 3. The boundary that does not move

v1's security model stands, unchanged:

- **No job may name a program, a shell command, or a script to run.**
  Never. Not with a whitelist of names, not "just for the generator".
  A file-writing agent that can execute arbitrary programs is a machine
  with no boundary at all.
- Executable paths live in the runner's own config, never in a job.
- Human-only list unchanged: attaching the EA to a live chart, arming
  `InpSeq_LiveApply` or any real-trading switch, any order/position/
  account action, deleting data, visual UI sign-off.

**The honest part.** v2 needs to generate `.ini`/`.set` files, parse
reports and diff deal lists. That is code, and Claude writes code. So the
real boundary is not "Claude cannot execute" — it is:

> **D0 — The agent executes only code that was on disk when the owner
> started it.** The agent never imports or reloads anything after start.
> Restarting the agent is therefore the owner's review checkpoint, and it
> is the only way new runner code takes effect.

This is a weaker guarantee than "Claude cannot run code", and I would
rather write that down than pretend otherwise. If the owner wants the
stronger version, the option is: keep `tools/npexec/**` in a folder Claude
may not write to, and have Claude propose changes as patch files the owner
applies. That costs one manual step per runner change. My recommendation
is D0 as written, because the agent restart already exists as a natural
gate, and because the same trust is already extended to the .mq5 that the
tester executes.

---

## 4. Architecture

Three layers. Includes point down only, same discipline as the EA.

    ┌──────────────────────────────────────────────────────────┐
    │  agent  (tools/np_agent.py)                              │
    │  mailbox, queue, job validation, status, heartbeat       │
    │  knows NOTHING about MT5 paths or NeelPrajna semantics   │
    └───────────────┬──────────────────────────────────────────┘
                    │
    ┌───────────────▼──────────────────────────────────────────┐
    │  npexp  (tools/npexp/)          EXPERIMENT LAYER         │
    │  experiment spec → runs, manifest, archive, compare,     │
    │  regression verdicts, guardrails                         │
    └───────────────┬──────────────────────────────────────────┘
                    │
    ┌───────────────▼──────────────────────────────────────────┐
    │  npexec (tools/npexec/)         MT5 LAYER (the only one) │
    │  terminal/metaeditor paths, ini+set writing (UTF-16LE),  │
    │  launch, completion detection, report+CSV harvest        │
    └──────────────────────────────────────────────────────────┘

- `npexec` is the only place that knows an MT5 exists. It takes a fully
  resolved run request and returns raw artefacts. No opinions.
- `npexp` is the only place that knows what NeelPrajna considers a valid
  experiment. It never launches a process itself.
- The agent is a dispatcher and a queue. Thin on purpose.

This is the owner's "Architecture Recommendation" made concrete: swapping
MT5 build, terminal, or even the tester for the Phase 7 `npreplay` engine
means replacing `npexec` only.

---

## 5. Decisions

- **D1 — Typed jobs only.** New job types are added as named types with a
  validated schema. No generic escape hatch. (§6)
- **D2 — One executor, many requesters.** Only one tester process per
  terminal, ever. Concurrency is a `npexec` concern (§12), never achieved
  by two agents racing on one mailbox.
- **D3 — MT5 logic lives only in `npexec`.** Owner's recommendation,
  adopted verbatim.
- **D4 — Every run produces a manifest or it is not a run.** A result
  without its manifest is deleted, not archived. (§8)
- **D5 — Archive is append-only and outside the repo**:
  `C:\NeelPrajna\runs\<UTC>_<expid>_<runid>\`. Git stays clean; reports
  and tick-heavy artefacts never enter version control.
- **D6 — Job hand-off is atomic.** Claude writes `<id>.json.tmp`, then
  renames to `<id>.json` (`Filesystem:move_file`). The agent ignores
  anything not ending exactly in `.json`. Fixes W1.
- **D7 — Three-state job lifecycle**: `jobs\` → `running\` → `done\`.
  On startup, anything found in `running\` gets a FAIL status
  "agent restarted mid-job". Fixes W2.
- **D8 — Completion is proven, not assumed.** Exit code is one signal of
  four. (§9) Fixes W3.
- **D9 — Harvest by identity, not by clock.** Every run gets a run id;
  the EA's CSV outputs and the report name carry it; harvest matches the
  id. Time windows are a fallback only, and are flagged in the manifest
  as untrusted. Fixes W4. Needs one small EA-side change (§8.3).
- **D10 — The runner refuses to hide non-comparability.** Bars, ticks,
  symbol, spread model, and data-source fingerprint go in the manifest;
  `npexp compare` marks any cross-run comparison where these differ as
  NOT COMPARABLE (ADR-004 R3, mechanically enforced). (§11)
- **D11 — Burned windows are data, not memory.** `tests/windows.json`
  lists windows and their state (IN_SAMPLE / OOS_UNUSED / BURNED). A job
  that asks for a BURNED window as an out-of-sample test is refused. Only
  the owner may move a window to BURNED... and it is one-way. (§11)
- **D12 — Optimisation jobs are Tier 3 and stay disabled until Phase 7
  validation passes.** (§13)
- **D13 — The agent starts itself.** Registered as a Windows scheduled
  task at logon, plus restart-on-failure. Today's finding — no bridge
  folder at all — is what happens without this.

---

## 6. Job types

Existing, unchanged in meaning: `deploy`, `compile`, `backtest`.

New:

```json
{"job": "experiment", "spec": "tests/longrun/exp/R6_INSAMPLE.json"}
```
Runs one experiment spec (§7): N runs, sequential, archived, with a
summary written at the end. This is the workhorse.

```json
{"job": "regress", "baseline": "runs/2026-07-22_R6_BASE_001"}
```
Re-runs the exact archived config of a baseline against the current
build, then diffs the deal lists with `tools/diff_deals.py`. Verdict is
one of IDENTICAL / DIFFERS / NOT COMPARABLE. This automates house rule
§7 — the single highest-value job on the list. (§10)

```json
{"job": "config", "spec": "tests/longrun/exp/R6_INSAMPLE.json"}
```
Generates the `.set` / `.ini` files for a spec (correct UTF-16LE BOM +
CRLF) and writes them into the spec's folder — without running anything.
Lets Claude and the owner review the exact settings before hours of
compute. Replaces hand-running `make_phase6_configs.py`.

```json
{"job": "control", "action": "cancel", "target": "0007"}
```
`cancel` (kill the running tester, mark the run ABORTED), `status`
(dump queue + current run to results), `rescan` (re-harvest a run whose
collection failed). Nothing here can start work.

Refused, permanently: anything with a `cmd`, `exe`, `script`, `python`,
`args` or `path-to-run` field, under any name.

---

## 7. Experiment spec

One JSON file describing a set of runs. Lives in the repo, is reviewable,
is archived with the results.

```json
{
  "id": "R6_INSAMPLE",
  "purpose": "R6 six statics + phase6 seq + noBE arm, in-sample only",
  "predictions": "tests/longrun/PREDICTIONS.md",
  "base_ini": "tests/phase6/ini/PHASE6_2_ALL_DRYRUN.ini",
  "base_set": "tests/phase6/set/PHASE6_2_ALL_DRYRUN.set",
  "window": "IN_SAMPLE_2026H1",
  "model": "every_tick",
  "runs": [
    {"name": "twins_on",  "inputs": {"InpSeq_UnifyStatic": true}},
    {"name": "twins_off", "inputs": {"InpSeq_UnifyStatic": false}}
  ]
}
```

Rules the spec layer enforces:

- `window` is a **name**, resolved through `tests/windows.json`. Raw dates
  in a spec are allowed only with `"window": "AD_HOC"` and are recorded
  as ad-hoc in the manifest. This makes window discipline visible.
- Each `runs[]` entry may override inputs. Everything not overridden comes
  from `base_set`. So an A/B is literally a one-key difference in the
  file — ADR-004 R2 becomes readable at a glance instead of a hope.
- If two runs in one spec differ in more than one input, the runner emits
  a warning into the manifest: `MULTI_FACTOR: 3 inputs differ`. It does
  not block. It just refuses to let a confound be invisible. (v5.8.0's
  BE mismatch cost 8.8 R of pure confound; this is the cheap vaccine.)

---

## 8. Run identity — the manifest

### 8.1 Why this comes before batching

A hundred archived runs with no identity is a hundred unusable files.
One archived run with a full manifest is evidence. Identity first.

### 8.2 `manifest.json` contents

- **Code**: EA version string, `EA_BUILD_SESSION`/`BRANCH`, git commit +
  dirty flag, .ex5 SHA-256 and mtime, agent version, npexec version.
- **Strategy**: every loaded `.seq` file name + its FNV-1a-32 hash, the
  roster, `InpSeq_Kind`, `InpSeq_LiveApply` (must be false), twins flag.
- **Config**: full `.set` and `.ini` copied into the run folder verbatim.
- **Market**: symbol, broker/server name, account currency, spread setting
  (fixed value or "current"), modelling mode, leverage, deposit.
- **Data**: from the tester report — bars, ticks, first/last bar time,
  and a hash of the symbol's history file size+mtime.
- **Execution**: start/end UTC, duration, terminal path, exit code,
  completion evidence (§9), agent-detected anomalies.
- **Outcome**: trades, net R, PF, max DD, worst losing streak, and per
  universe rows harvested from the NPSU CSVs.

### 8.3 One small EA-side change

For D9 (harvest by identity), the EA needs a run tag in its CSV output
names — an input like `InpRunTag` (default empty = today's behaviour),
appended to `NPSU_*` file names when set. The runner injects it. Without
this the runner is guessing from timestamps, and two runs an hour apart
can be mixed. Small change, big correctness win. Should be bundled with
whatever engine work happens next, not shipped on its own.

---

## 9. Completion detection

Four signals; a run is COMPLETE only when 1 and at least two of 2–4 hold:

1. Terminal process exited (or was killed by the watchdog → ABORTED).
2. Report file exists, non-zero, and parses as an MT5 tester report.
3. Tester log tail shows the final summary line, and shows no
   `critical error` / `not enough memory` / `no history` lines.
4. Expected EA CSV outputs exist with the run tag.

Watchdog: if neither the log file nor the report has grown in
`STALL_MINUTES` (default 30) the run is declared STALLED, the terminal is
killed, and the job returns FAIL with the last 50 log lines. Fixes W7.
Long runs are slow, but they are never silent — the tester log grows.

Retry policy: an environmental FAIL (terminal missing, history download
failed) is retried **once**, then the queue pauses and the agent writes a
`NEEDS_OWNER.json`. No hammering. Matches the existing failure etiquette.

---

## 10. Regression — the part that pays for the whole build

House rule §7 already says: engine changes need a baseline backtest whose
deal list is byte-identical. Today that is a human ritual, so it gets
skipped when tired. The `regress` job makes it a 30-second request.

Mechanism:

1. A run can be promoted to **golden** by the owner (a flag file in the
   run folder — owner-only action, like arming).
2. `regress` re-runs a golden run's archived `.set`/`.ini` on the current
   build, in the same window, same model, same spread.
3. Deal lists are compared with `tools/diff_deals.py`.
4. Verdict: IDENTICAL / DIFFERS (with first divergence: deal #, time,
   universe) / NOT COMPARABLE (manifest fingerprints disagree — e.g. the
   history file changed, so a difference proves nothing).

Overnight regression across the golden set is then one job. That is the
"objective evidence for every change" the owner's note asks for, and it
is the only feature here that improves safety rather than throughput.

Caveat, stated plainly: byte-identical deal lists are only a valid gate
when old and new paths share evaluation cadence (ADR-004 §5). The runner
records cadence-relevant inputs in the manifest and marks the verdict
CADENCE_DIFFERS when they changed, instead of reporting a false failure.

---

## 11. Guardrails the runner enforces

Automation removes friction. Friction is currently one of the things
protecting this project from bad conclusions. So v2 has to put the
protection back explicitly:

- **Burned windows (D11).** `tests/windows.json` is the register.
  2026.07.01–22 is BURNED — examined four times during Phase 6. A job
  that names a BURNED window as OOS is refused with the reason. In-sample
  or replication use of a burned window is allowed but stamped
  `BURNED_WINDOW` in the manifest and in every summary that quotes it.
- **Comparability (D10).** `compare` refuses to rank runs whose bar/tick
  counts or data fingerprints differ. ADR-004 R3 was violated once by
  hand; a machine will not violate it by accident.
- **Sample size.** Any comparison where either arm has n < 30 trades is
  reported as `STILL OPEN — n=17 vs n=15`, never as a winner. The runner
  prints the sample size next to every ranking number, always.
- **Pre-registration.** A spec may point at a predictions file. If it
  does, the summary refuses to be written until that file exists and is
  older than the run start time. Predictions after data are not
  predictions.
- **Ranking order.** Summaries sort survival-first: max DD → worst losing
  streak → ranging-week behaviour → PF. ROI is displayed last and never
  sorts. This is the standing rule; hard-coding it removes the temptation.

None of these are technically hard. They exist because the failure mode
of a fast experiment factory on 22 days of data is not a crash — it is a
confident wrong answer.

---

## 12. Parallelism, and one trap

Two or three tester instances would cut long-run wall-clock time roughly
proportionally, using separate portable terminal installs.

**The trap:** NPSU CSVs are written to the *shared* `Common\Files`
directory. Two parallel runs will write the same file names and overwrite
each other's output. Discovering this after an overnight batch would be
expensive. Requirements before any parallelism:

1. `InpRunTag` in output names (§8.3), **or** portable terminals with
   their own Files directory (`/portable`).
2. Separate history caches, or accept a first-run download per terminal.
3. Manifest records which terminal executed the run — different installs
   can carry different builds, which is exactly a non-comparability.

Recommendation: build parallelism in Tier 3, after tagging exists. One
correct run beats three colliding ones.

---

## 13. Optimisation and mass search — deliberately last

The owner's note lists optimisation as an automatable action. It is.
My recommendation is to build it last and switch it on later still:

- The MT5 optimiser searches by re-running the whole tester per
  combination. Phase 7's `npreplay` searches by replaying recorded gate
  truth. For parameter search, replay is likely orders of magnitude
  faster and reproducible offline. Building a big MT5-optimiser workflow
  now risks building the slow one twice.
- Current samples are 15–18 trades per strategy. A search over hundreds
  of parameter sets on that data will find winners with certainty and
  they will be noise. Phase 7 D8 already says no ranking without
  walk-forward; the optimiser is the fastest way to violate that rule at
  scale.
- Correct role for the MT5 optimiser: **confirmation** of a candidate
  chosen by design intent or by walk-forward replay, on a window that has
  not been burned.

So: `optimise` job designed, schema reserved, implementation deferred,
and gated behind Phase 7b acceptance (replay reproduces existing books
trade-for-trade).

---

## 14. Staging

**A1 — Make v1 trustworthy (≈ half a session).** D6 atomic hand-off,
D7 three-state lifecycle, D8 completion proof, D13 scheduled-task start,
watchdog, agent version in heartbeat. No new capability at all.
*Acceptance:* kill the agent mid-backtest → after restart, Claude can read
a FAIL status explaining exactly that. Reboot the machine → bridge comes
back by itself.

**A2 — Identity and archive (≈ one session).** `npexec` extracted,
manifest, run folders under `C:\NeelPrajna\runs\`, harvest by run id,
report+CSV parsing into the outcome block.
*Acceptance:* re-run the R6 in-sample config twice; the two manifests
differ only in timing fields, and `compare` says IDENTICAL.

**A3 — Experiments and regression (≈ one session).** `npexp`, spec
format, `config` + `experiment` + `regress` jobs, guardrails from §11,
golden-run promotion.
*Acceptance:* a two-run A/B spec executes unattended and produces a
summary that names the single differing input; `regress` against a golden
run of the same build returns IDENTICAL.

**A4 — Scale (later).** Parallel terminals, overnight batch scheduling,
`optimise` behind the Phase 7 gate.

A1 and A2 are worth doing regardless of what else happens, because the R6
long run and the 6c unification both need archived, identified evidence.
A3 pays for itself the first time an engine change needs a §7 gate.

---

## 15. What I recommend against building

- A generic "run this command" job, in any disguise. (§3)
- A web dashboard for the runner. The results are read by Claude and by
  the owner in a text summary. A UI here is cost with no evidence value.
- Broker/symbol matrix testing before the single-symbol single-broker
  case is stable. The note lists it; it is correct eventually. Right now
  XAUUSD on one broker is not yet understood.
- Auto-promotion of anything to live. The two-key rule stands: the
  machine may build and measure, only the owner arms.

---

## 16. Open questions for the owner

1. **D0 or the stricter variant?** Agent code reviewed-at-restart (my
   recommendation), or `tools/npexec/**` write-protected from Claude with
   patches applied by hand?
2. **Which terminal is the automation terminal?** v1's CONFIG points at
   `C:\Program Files\MetaTrader 5`. The bridge doc says use the second
   install (E92643…). These disagree. The automation terminal gets closed
   after every run, so this must be a terminal with no live charts.
3. **Archive location and budget.** `C:\NeelPrajna\runs\` acceptable?
   Every-tick multi-month runs produce large reports and CSVs. Is there a
   disk budget, and should runs older than N days auto-compress?
4. **Is `InpRunTag` acceptable as an EA input?** It is a recorder-adjacent
   change and could ride along with Phase 7a instead.
5. **Who writes `tests/windows.json` first**, and does the owner agree
   that BURNED is one-way and owner-only?
6. **Does the long run get re-done under A2** (so it lands archived with a
   manifest), or do we archive the in-flight run's outputs by hand and
   start clean from the next experiment?

## 17. One-line recommendation

Build A1 and A2 next — reliability and run identity — and do not build
the experiment factory until a single run can prove what produced it.
