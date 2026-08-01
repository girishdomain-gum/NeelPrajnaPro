# Automation v2 — the Experiment Runner (design v1.1)

- Status: DESIGN. Not started.
- v1.0 written 2026-07-27 from the owner's automation note + a code review
  of `tools/np_agent.py`. **v1.1 (this file) adds the multimodal evidence
  layer** after the Chief Scientist review and a code review of the
  reference tool `IVF_HC_Trades.mq5`.
- v1.0 is kept alongside this file for history. This file supersedes it.
- Changes in v1.1: new §5 (reference tool review), new §12 (the evidence
  model), new §13 (visual evidence pipeline), decisions D14–D24, staging
  re-ordered — old A4 (Scale) becomes **A5**, new **A4 = Multimodal
  Evidence Collection**, as the reviewer recommended.

---

## 1. Where we actually are today (honest reading)

`np_agent.py` v1 is ~250 lines. It is a **remote hands** tool, not an
experiment platform. It does three things — `deploy`, `compile`,
`backtest` — one at a time, when Claude asks. It has no memory, no
archive, no queue, no run identity.

Facts checked on the machine 2026-07-27:

- `C:\NeelPrajna\bridge\` **does not exist**. No mailbox, no heartbeat.
  Nothing starts the watcher, so it stays down. Lifecycle failure, not a
  code failure.
- `tests\longrun\` holds only README + PREDICTIONS + the .seq folder. No
  archived results.
- Pieces v2 needs already exist and are unused by the agent:
  `tools/diff_deals.py`, `tools/seqgen.py`,
  `tests/phase6/make_phase6_configs.py`.

Weaknesses in v1 (code review, not speculation):

| # | Weakness | Consequence |
|---|---|---|
| W1 | Job file is read the moment it appears | A job still being written parses as bad JSON, gets FAIL, is thrown into `done\`. Silent loss. |
| W2 | Job moves to `done\` only after the action returns | Agent or machine dies during a 6-hour backtest → no status ever written. "Never ran" and "died" look the same. |
| W3 | Success = `terminal64.exe` exit code 0 | MT5 can return 0 without producing a report. False OK. |
| W4 | Harvest = filename prefix + files touched in the last 2 h | Time-window harvesting. Two runs in one evening cross-contaminate. |
| W5 | No run identity | Nothing records which EA version, .set, .seq hashes, broker or tick data made the result. Two weeks later it proves nothing. |
| W6 | Flat `bridge\results\` | No archive, no comparison, no cleanup. |
| W7 | No watchdog | A hung tester holds the queue for the full 24 h timeout. |

W1, W2 and W5 matter most. W5 destroys value quietly.

---

## 2. What the owner asked for, restated

Experiments run without a human in the loop: prepare → launch MT5 → wait →
collect → archive → next. Hundreds of them. Regression across EA versions,
brokers, symbols, spreads, date ranges, modelling modes, parameter sets.
Keep MT5-specific logic in one component so NeelPrajna just asks for a
result and gets one.

Agreed as a destination. The architecture recommendation is adopted
verbatim (D3).

Push-back kept from v1.0: "hundreds of experiments" is a capability that,
on 22 days of data with 15–18 trades per strategy, is a **liability
multiplier**. Build the machine that makes good evidence cheap, not the
machine that makes searching cheap. §14 and §18.

---

## 3. What the Chief Scientist review adds

The review is right on its central point, and I am adopting it:

> Numerical evidence proves the EA **computed** correctly. It does not
> prove the EA **behaved** correctly. A shifted FVG box, a sweep line at
> the wrong price, a marker two candles late — the CSV cannot see any of
> these. A human sees them instantly.

Adopted: four evidence categories, the evidence bundle, event-driven
capture instead of periodic screenshots, machine-written captions, and the
staging position (after A3, before scale). Rationale accepted in full:
scaling a runner that cannot yet produce complete evidence just multiplies
runs, not knowledge.

Three corrections I am making to the proposal, in §13:

1. **The verdict must be computed numerically and drawn into the image.**
   An AI reading pixels should *report* a verdict, never *compute* one.
2. **The regression layer for drawings is an object dump, not an image
   diff.** Chart objects have exact coordinates; comparing them catches
   "the box moved one bar" precisely, cheaply and deterministically. An
   image comparison is a weaker instrument for the same question.
3. **Capture is a separate pass, not part of the measured run.** See §5 —
   the owner's own reference tool already works this way, and that is the
   design that survives the tester's constraints.

---

## 4. The boundary that does not move

- **No job may name a program, shell command, or script to run.** Ever.
  Not with a whitelist, not "just for the generator".
- Executable paths live in the runner's config, never in a job.
- Human-only, unchanged: attaching the EA to a live chart, arming
  `InpSeq_LiveApply` or any real-trading switch, any order/position/
  account action, deleting data, visual UI sign-off.
- **New for v1.1:** an AI visual verdict may never promote, arm, or pass a
  gate on its own. It is advisory input to the owner. D22.

**D0 — The agent executes only code that was on disk when the owner
started it.** No reload after start. Restarting the agent is therefore the
owner's review checkpoint. This is weaker than "Claude cannot execute
code", and I would rather write it down than pretend. Stricter option:
keep `tools/npexec/**` unwritable by Claude and apply patches by hand.

---

## 5. Review of the reference tool `IVF_HC_Trades.mq5`

Read in full (217 lines, rev 2, "ADR-009 tool, generation 4"). It belongs
to the QRF/IVF line, which is out of scope for this automation work — it
is used here as a **technique reference only**. No code is copied; the
patterns are.

### 5.1 What it actually is

A **script** (`OnStart`, `#property script_show_inputs`) run manually on a
live XAUUSD H1 chart. It reads `MQL5\Files\HC_input.txt` — a PROV line
plus a semicolon-separated list of already-decided trades from a Python
sampler — then, for each trade: re-derives the bars from MT5's own series,
verifies the claimed prices, draws arrows + a trend line + captions,
navigates the chart, screenshots to PNG, and deletes its objects again.

### 5.2 What it proves, and what it does not

Proves: annotated chart capture with machine-written captions works, and
has been made to work reliably enough to be someone's fourth generation.

Does **not** prove: that any of this works **inside the Strategy Tester**.
Scripts do not run in the tester at all, and in non-visual tester mode MT5
provides no chart — object drawing and `ChartScreenShot` are expected to
be ignored or to fail. This is the single most important technical
unknown in the whole visual proposal, so it gets its own spike (A4.0,
§17) before anything is designed on top of it.

### 5.3 Seven patterns worth stealing (all adopted below)

1. **No provenance, no capture.** The tool refuses to run if the PROV line
   carries no `label=`, because a previous generation stamped one sprint's
   evidence with another sprint's name. → D14.
2. **Provenance travels with the artefact.** The label is stamped into
   every caption, every object tag, every PNG filename and every log line.
   An image found alone still says what it is. → D15.
3. **The tool knows when its own evidence is worthless.** It checks that
   the target bar is actually inside the visible window
   (`CHART_FIRST_VISIBLE_BAR` + `CHART_WIDTH_IN_BARS`), retries three
   times, and if it still fails it renames the file `_NAVFAIL` and logs
   "evidence INVALID". Most screenshot automation silently produces
   useless pictures. → D16, and this is the best idea in the file.
4. **The verdict is numeric; the image only carries it.** MATCH/MISMATCH
   comes from comparing claimed prices against `iOpen()` at
   `iBarShift()` within a tolerance, and is drawn in green or red. The
   picture is the human-readable wrapper around a computed result. → D17.
5. **Hermetic images.** Objects are deleted after each screenshot, so
   image N never contains leftovers from image N−1. → D18.
6. **Honest captions.** The day-of-week is *reported*, not asserted, where
   the real feed legitimately differs. Evidence that overstates itself is
   worse than none.
7. **Hard-won display constraints**, already paid for: `OBJ_LABEL` text
   silently truncates past ~63 characters, and captions must use
   `CHART_COLOR_FOREGROUND` rather than a fixed colour or they vanish on a
   light theme. Both go straight into our caption spec (§13.4) instead of
   being rediscovered.

### 5.4 The design lesson (most valuable part)

The tool is **decoupled from the run that produced the trades**. Python
decides, writes an event file; the chart tool renders and verifies later.

That is exactly the architecture that survives the tester constraint:

> **Measure headless and fast. Capture visually afterwards, from the run's
> own event file.**

So NeelPrajna does not need screenshots inside a 6-hour every-tick
backtest. It needs the run to emit an **event file**, and a separate
capture pass to turn that file into annotated images. This keeps
measurement fast, keeps capture optional, and makes images reproducible
without re-running the experiment. → D19.

### 5.5 Costs observed in the tool

- ~1–3 s per image (`Sleep(1000)` per navigation attempt, up to 3). A few
  hundred images is minutes; tens of thousands is not viable. Capture must
  be bounded. → D21.
- `ChartScreenShot` writes into that terminal's `MQL5\Files`, **not**
  `Common\Files`. The harvester currently only looks at `Common\Files`.

---

## 6. Architecture

    ┌──────────────────────────────────────────────────────────┐
    │  agent  (tools/np_agent.py)                              │
    │  mailbox, queue, job validation, status, heartbeat       │
    │  knows NOTHING about MT5 paths or NeelPrajna semantics   │
    └───────────────┬──────────────────────────────────────────┘
    ┌───────────────▼──────────────────────────────────────────┐
    │  npexp  (tools/npexp/)          EXPERIMENT LAYER         │
    │  spec → runs, manifest, archive, compare, regression,    │
    │  guardrails, evidence bundle assembly, AI review calls   │
    └───────────────┬──────────────────────────────────────────┘
    ┌───────────────▼──────────────────────────────────────────┐
    │  npexec (tools/npexec/)         MT5 LAYER (the only one) │
    │  terminal/metaeditor paths, ini+set writing (UTF-16LE),  │
    │  launch, completion detection, report/CSV/PNG harvest    │
    └──────────────────────────────────────────────────────────┘

`npexec` is the only layer that knows an MT5 exists. `npexp` is the only
layer that knows what NeelPrajna considers a valid experiment; it never
launches a process. The agent is a dispatcher and a queue. Swapping the
tester for the Phase 7 `npreplay` engine means replacing `npexec` only.

---

## 7. Decisions

Foundation (from v1.0):

- **D1** Typed jobs only; no generic escape hatch.
- **D2** One tester process per terminal, ever.
- **D3** MT5 logic lives only in `npexec`.
- **D4** Every run produces a manifest or it is not a run.
- **D5** Archive append-only, outside the repo:
  `C:\NeelPrajna\runs\<UTC>_<expid>_<runid>\`.
- **D6** Atomic job hand-off: write `<id>.json.tmp`, rename to
  `<id>.json`; agent ignores anything else. Fixes W1.
- **D7** Three-state lifecycle `jobs\ → running\ → done\`; anything in
  `running\` at startup gets FAIL "agent restarted mid-job". Fixes W2.
- **D8** Completion is proven by four signals, not assumed. Fixes W3.
- **D9** Harvest by run id, not by clock. Fixes W4.
- **D10** Manifest fingerprints make non-comparability visible;
  `compare` marks NOT COMPARABLE (ADR-004 R3, enforced).
- **D11** `tests/windows.json` is the window register; BURNED is one-way
  and owner-only; BURNED refused as OOS.
- **D12** Optimisation is last and gated behind Phase 7b acceptance.
- **D13** The agent starts itself (scheduled task at logon + restart on
  failure).

Evidence layer (new in v1.1):

- **D14 — No provenance, no capture.** The capture pass refuses to run
  without run id, EA version, config fingerprint and .seq hashes. Refusing
  is correct behaviour, not an error to work around.
- **D15 — Provenance travels with every artefact.** Run id in the PNG
  filename, in the caption block, in the object tags, in the log line, and
  in `visual/index.json`. An image found on its own is still evidence.
- **D16 — Capture self-invalidates.** If the event bar is not verifiably
  inside the visible window after N attempts, the image is written with a
  `_NAVFAIL` suffix and marked `valid: false` in the index. Invalid images
  are never counted, never compared, never shown to the AI reviewer as
  evidence.
- **D17 — Verdicts are computed, then drawn.** Every captioned image
  carries a verdict that was calculated numerically (levels, times, prices
  from the EA's own values vs the drawn object's coordinates). The picture
  transports the verdict; it does not produce it.
- **D18 — Images are hermetic.** Only the annotations belonging to that
  event are on the chart when the shutter fires.
- **D19 — Capture is a separate pass over an event file.** The measured
  run stays headless and fast; it emits `events.csv`. The capture pass
  consumes it. Re-rendering images never requires re-running the
  experiment.
- **D20 — Drawing regression is an object dump, not an image diff.**
  Every capture emits `objects.csv` (name, type, time1, price1, time2,
  price2, colour, width, tag). Baseline vs candidate is a text diff.
  Deterministic, tiny, exact. Images serve human and AI review.
- **D21 — Capture is bounded.** Per-run caps on events, images and total
  MB, declared in the spec. Exceeding a cap truncates and records
  `CAPTURE_TRUNCATED` in the manifest, rather than filling the disk.
- **D22 — The AI verdict is advisory.** It can say PASS / REVIEW /
  SUSPECT. It can never gate, promote or arm. The model name, version and
  prompt hash are recorded in the manifest; a verdict without them is
  discarded. Two AI runs may disagree — that is expected, and it is
  exactly why this cannot be the gate.
- **D23 — Event vocabulary is NeelPrajna's own.** Not the reference
  tool's. §13.2.
- **D24 — Visual capture is off by default.** Same principle as the Phase
  7 recorder (D10 there). Most regression runs never need it.

---

## 8. Job types

Unchanged: `deploy`, `compile`, `backtest`.

New:

```json
{"job": "experiment", "spec": "tests/longrun/exp/R6_INSAMPLE.json"}
{"job": "regress",    "baseline": "runs/2026-07-22_R6_BASE_001"}
{"job": "config",     "spec": "tests/longrun/exp/R6_INSAMPLE.json"}
{"job": "control",    "action": "cancel", "target": "0007"}
```

New in v1.1:

```json
{"job": "capture", "run": "runs/2026-07-28_R6_INSAMPLE_003",
 "profile": "detector_review"}
```
Runs the visual capture pass over an archived run's `events.csv`, writes
`visual/` into that run's bundle, and updates `summary.json`. Never
launches a measured backtest, so it can be re-run freely and cheaply.

```json
{"job": "visual_compare", "baseline": "runs/...A", "candidate": "runs/...B"}
```
Diffs `objects.csv` (deterministic verdict), then optionally asks the AI
reviewer about the surviving image pairs (advisory verdict). Produces
`visual_diff.md`.

Permanently refused: any job with a `cmd`, `exe`, `script`, `python`,
`args` or path-to-run field, under any name.

---

## 9. Experiment spec

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
  ],
  "visual": {
    "enabled": false,
    "profile": "detector_review",
    "window": "VISUAL_2026_03",
    "events": ["PULSE_BIRTH", "SEQ_STEP", "WOULD_FIRE",
               "ENTRY", "BE_MOVE", "EXIT"],
    "max_images": 200,
    "max_mb": 300,
    "resolution": [1600, 900],
    "caption_style": "full"
  }
}
```

Rules enforced by the spec layer:

- `window` is a **name** resolved through `tests/windows.json`. Raw dates
  need `"window": "AD_HOC"` and are stamped as ad-hoc.
- Runs override inputs; everything else comes from `base_set`. An A/B is
  literally a one-key difference in the file — ADR-004 R2 becomes
  readable instead of hoped for.
- If two runs differ in more than one input, the manifest gets
  `MULTI_FACTOR: 3 inputs differ`. Not blocked — just never invisible.
  (v5.8.0's BE mismatch cost 8.8 R of pure confound. This is the vaccine.)
- `visual.window` must be a **sub-window** of the run window and is
  normally days, not months. §13.5.

---

## 10. Run identity — the manifest

A hundred archived runs with no identity is a hundred unusable files.
Identity first.

`manifest.json`:

- **Code**: EA version, `EA_BUILD_SESSION`/`BRANCH`, git commit + dirty
  flag, .ex5 SHA-256 + mtime, agent version, npexec version.
- **Strategy**: every loaded `.seq` name + FNV-1a-32 hash, roster,
  `InpSeq_Kind`, `InpSeq_LiveApply` (must be false), twins flag.
- **Config**: the `.set` and `.ini` copied verbatim into the run folder.
- **Market**: symbol, broker/server, currency, spread setting, modelling
  mode, leverage, deposit.
- **Data**: bars, ticks, first/last bar time, history-file fingerprint.
- **Execution**: start/end UTC, duration, terminal path, exit code,
  completion evidence, anomalies.
- **Outcome**: trades, net R, PF, max DD, worst losing streak, per-universe
  rows from the NPSU CSVs.
- **Visual (v1.1)**: capture profile, events captured, images valid vs
  NAVFAIL, bytes, truncation flag, AI model + prompt hash if reviewed.

### One small EA-side change

Harvest-by-identity (D9) needs a run tag in output names — an input like
`InpRunTag` (default empty = today's behaviour) appended to `NPSU_*` file
names. The runner injects it. Without it the runner guesses from
timestamps and two runs an hour apart can mix. The same tag names the
event file and every PNG, so it also serves D15. Best bundled with Phase
7a rather than shipped alone.

---

## 11. Completion detection

COMPLETE requires signal 1 plus at least two of 2–4:

1. Terminal exited (or was killed by watchdog → ABORTED).
2. Report file exists, non-zero, parses as an MT5 tester report.
3. Tester log tail shows the final summary and no `critical error` /
   `not enough memory` / `no history`.
4. Expected EA CSV outputs exist, carrying the run tag.

Watchdog: no growth in log or report for `STALL_MINUTES` (default 30) →
STALLED, terminal killed, FAIL with the last 50 log lines. Long runs are
slow but never silent.

Retry: one retry for environmental failures, then the queue pauses and the
agent writes `NEEDS_OWNER.json`. No hammering.

---

## 12. The evidence model

Adopted from the review. Four categories, one bundle:

| Category | Artefacts | Proves |
|---|---|---|
| Numerical | metrics.csv, per-universe CSVs, report | the arithmetic |
| Textual | tester.log, ea.log, manifest.json, analysis.md | what ran, in what conditions |
| Execution | deals.csv, orders, positions | what the broker side did |
| Visual | visual/*.png, objects.csv, visual_report.md | that behaviour looked as intended |

Bundle layout — one folder, everything needed to understand and reproduce
the run:

    C:\NeelPrajna\runs\2026-07-28_R6_INSAMPLE_003\
      manifest.json
      config\        run.set  run.ini  spec.json  seq\*.seq
      tester.html    tester.log    ea.log
      metrics.csv    deals.csv     events.csv
      visual\        index.json    objects.csv
                     event_0001_PULSE_BIRTH_B3.png
                     event_0002_WOULD_FIRE.png
                     ...
      analysis.md    summary.json

**D4 restated with teeth:** a bundle missing `manifest.json` is deleted,
not archived. A bundle whose `visual/index.json` says every image is
NAVFAIL reports `VISUAL: NO VALID EVIDENCE` — it does not quietly pass.

---

## 13. Visual evidence pipeline

### 13.1 Shape

    measured run (headless, fast)
        └── events.csv  (time, event, universe, gate mask, levels, prices)
                │
        capture pass  ── job: capture ──▶  visual\*.png + objects.csv
                │                            (each image: computed verdict
                │                             drawn in, provenance stamped)
                ▼
        visual_compare  ──▶ objects.csv diff   = DETERMINISTIC verdict
                        └─▶ AI image review    = ADVISORY verdict
                                │
                                ▼
                        visual_report.md → owner

The measured run never waits for a screenshot. That is what makes this
affordable.

### 13.2 Event vocabulary (D23)

The review's example events — liquidity sweep, FVG, HC entry — are QRF/IVF
vocabulary. NeelPrajna does not have those concepts; it has gates and
sequences. Our list:

| Event | Fires when | Drawn |
|---|---|---|
| `PULSE_BIRTH` | a B1–B6 / T1–T9 gate turns true | gate name, trigger level line, bar marker |
| `SEQ_STEP` | a sequence FSM advances a step | step index, window remaining, step condition |
| `SEQ_EXPIRE` | a sequence step times out | expiry bar, step that lapsed |
| `WOULD_FIRE` | SeqLive dry-run "WOULD FIRE" | intended direction, entry, SL, TP |
| `ENTRY` | a book or real order opens | entry price, SL, TP, size, risk % |
| `BE_MOVE` | stop moves to break-even | old and new stop lines |
| `EXIT` | TP / SL / BE close | exit price, R result |
| `BOOK_DIVERGE` | twin book differs from source book | both books' values side by side |

`BOOK_DIVERGE` is not in the review's list and is the one I would fight
for: it is the visual form of the 6c unification gate, and it turns "twin
books identical" from a number into a picture of exactly where they parted.

### 13.3 The verdict inside each image (D17)

Each event carries a numeric self-check, drawn into the caption in green
or red, in the spirit of the reference tool's MATCH/MISMATCH:

- drawn object coordinates vs the EA's own decision values (this is what
  catches "the FVG box is one bar left" — exactly, not approximately)
- level vs the bar series (`iOpen`/`iHigh` at `iBarShift`, tolerance
  declared)
- event time vs the bar it claims
- for `BOOK_DIVERGE`: the two book values and their difference

An AI reading the image then reports what the image says. It does not
decide what is true.

### 13.4 Caption spec

Two blocks, machine-written, using the constraints the reference tool
already paid for: every line ≤ 63 characters (longer text is silently
truncated by `OBJ_LABEL`), and colour from `CHART_COLOR_FOREGROUND`, never
a fixed light or dark colour.

    line 1  RUN R6_INSAMPLE_003  EV#0042  PULSE_BIRTH  B3
    line 2  2026-03-11 09:31 UTC  XAUUSD M1  spread 18
    line 3  UNIV TrendPullback_Fibo  #4bc2b282  BE=ON
    line 4  trig 2412.35  ATR 3.8  risk 1.0%  step 2/3
    line 5  VERDICT  MATCH   (drawn 2412.35 = decision 2412.35)
    line 6  ea 5.9.0  ex5 3f9a…  prov: spec R6_INSAMPLE

Line 5 is green or red. Line 6 makes a stray PNG self-explaining.

### 13.5 Cost control (D21)

- Capture runs on a **visual sub-window** — days, not months. The point is
  to inspect behaviour, not to photograph six months.
- ~1–3 s per image measured from the reference tool. 200 images ≈ 5–10
  minutes. That is the right order of magnitude for a review pass.
- Caps on images, MB and events, declared in the spec; exceeding a cap
  truncates and flags the manifest.
- Off by default (D24).

### 13.6 AI review — what it is good for

Good: holistic sanity ("does this chart look like a pullback entry?"),
spotting missing or duplicated labels, ranking image pairs by how
different they look so the owner reviews 6 images instead of 200,
producing readable prose for `visual_report.md`.

Bad, and therefore not used for: deciding whether a level moved, whether a
box shifted, whether a line is identical. Those are `objects.csv`
questions, answered exactly.

Verdicts: `PASS` (nothing notable), `REVIEW` (worth owner's eyes),
`SUSPECT` (looks wrong). Never `FAIL` — failure is a deterministic word
and this instrument is not deterministic. D22.

---

## 14. Guardrails the runner enforces

Automation removes friction, and friction is currently one of the things
protecting this project from bad conclusions. So the protection goes back
explicitly:

- **Burned windows.** `tests/windows.json` is the register; 2026.07.01–22
  is BURNED (examined four times in Phase 6). Refused as OOS; allowed for
  replication but stamped `BURNED_WINDOW` in every summary quoting it.
- **Comparability.** `compare` refuses to rank runs whose bar/tick counts
  or data fingerprints differ. R3 was broken once by hand; a machine will
  not break it by accident.
- **Sample size.** Either arm under 30 trades → `STILL OPEN — n=17 vs
  n=15`, never a winner. Sample size printed next to every ranking number.
- **Pre-registration.** If a spec names a predictions file, the summary
  refuses to be written unless that file exists and is older than the run
  start. Predictions after data are not predictions.
- **Ranking order.** max DD → worst losing streak → ranging weeks → PF.
  ROI displayed last, never sorts.
- **Visual honesty (new).** NAVFAIL images never count as evidence; an AI
  verdict without model+prompt hash is discarded; `VISUAL: NO VALID
  EVIDENCE` is a real, reportable outcome.

---

## 15. Regression — the part that pays for the build

House rule §7 already requires a byte-identical deal list for engine
changes. Today that is a human ritual, so it gets skipped when tired.

`regress`: re-run a golden run's archived `.set`/`.ini` on the current
build, diff deal lists with `tools/diff_deals.py`, verdict IDENTICAL /
DIFFERS (with first divergence: deal #, time, universe) / NOT COMPARABLE.
Golden status is set by the owner only — a flag file in the run folder,
like arming.

With v1.1 the verdict becomes layered:

    deal list   → IDENTICAL / DIFFERS      (blocking)
    objects.csv → IDENTICAL / DIFFERS      (blocking, when captured)
    metrics     → within tolerance?        (blocking)
    AI visual   → PASS / REVIEW / SUSPECT  (advisory)
    ──────────────────────────────────────
    final verdict = owner, holding all four

Caveat, plainly: byte-identical deal lists are a valid gate only when old
and new paths share evaluation cadence (ADR-004 §5). Cadence-relevant
inputs are in the manifest, and a change marks the verdict
CADENCE_DIFFERS instead of reporting a false failure.

---

## 16. Parallelism, and one trap

Two or three portable terminal installs would cut wall-clock roughly
proportionally.

**Trap:** NPSU CSVs are written to the shared `Common\Files` directory.
Parallel runs will write the same names and overwrite each other.
Discovering this after an overnight batch is expensive. Also, PNGs land in
each terminal's own `MQL5\Files` (§5.5), which the current harvester never
looks at. Requirements before any parallelism:

1. `InpRunTag` in output names, or portable terminals with their own Files
   directory.
2. Separate history caches, or one download per terminal.
3. Manifest records which terminal ran it — different installs can carry
   different builds, which is precisely a non-comparability.

One correct run beats three colliding ones.

---

## 17. Staging

**A1 — Make v1 trustworthy (≈ half a session).** D6, D7, D8, D13,
watchdog, agent version in heartbeat. No new capability.
*Acceptance:* kill the agent mid-backtest → after restart Claude reads a
FAIL saying exactly that. Reboot the machine → the bridge returns by
itself.

**A2 — Identity and archive (≈ 1 session).** `npexec` extracted, manifest,
run folders, harvest by run id, report+CSV parsing.
*Acceptance:* run the R6 in-sample config twice; manifests differ only in
timing fields; `compare` says IDENTICAL.

**A3 — Experiments and regression (≈ 1 session).** `npexp`, spec format,
`config` + `experiment` + `regress`, guardrails (§14), golden promotion.
*Acceptance:* a two-run A/B executes unattended and the summary names the
single differing input; `regress` against a golden run of the same build
returns IDENTICAL.

**A4 — Multimodal evidence collection (≈ 2–3 sessions).**

- **A4.0 — Feasibility spike (~30 minutes, do this before anything
  else).** Answer one question with a throwaway EA: can an EA in the
  Strategy Tester create chart objects and produce a `ChartScreenShot` —
  in visual mode, and in non-visual mode? Three outcomes:
  - works in both → capture may optionally run inside the tester;
  - visual mode only → capture stays a separate pass on a chart
    (expected, and the design already assumes it);
  - neither → capture pass runs on a live chart replaying `events.csv`,
    exactly like the reference tool. Still viable.
  Nothing in A4 is built until this is answered on this MT5 build.
- **A4.1** `events.csv` emitted by the EA (event vocabulary §13.2, off by
  default). Shares plumbing with the Phase 7a recorder — likely the same
  work; check before writing a second stream.
- **A4.2** capture pass: navigation with visibility check + NAVFAIL,
  hermetic objects, caption spec, computed verdicts, `objects.csv`,
  `visual/index.json`.
- **A4.3** `visual_compare`: objects diff first, images second, AI review
  advisory, `visual_report.md`.
- **A4.4** evidence bundle assembly + `summary.json` + human review page.
*Acceptance:* take one known-good run and one deliberately broken build
(shift a drawn level by one bar, change nothing else). `objects.csv` diff
must name the exact object and the exact offset. The AI review must flag
it as REVIEW or SUSPECT — and, critically, must not be needed to find it.

**A5 — Scale (later).** Parallel terminals, overnight batches, `optimise`
behind the Phase 7 gate.

Sequencing note: A4 before A5 is the reviewer's recommendation and I
agree. Scaling a runner that cannot yet produce complete evidence
multiplies runs, not knowledge.

---

## 18. Optimisation and mass search — deliberately last

- MT5's optimiser re-runs the whole tester per combination. Phase 7's
  `npreplay` searches by replaying recorded gate truth — likely orders of
  magnitude faster and reproducible offline. Building the slow one first
  risks building it twice.
- With 15–18 trades per strategy, a search over hundreds of parameter sets
  will find winners with certainty, and they will be noise. Phase 7 D8
  already forbids ranking without walk-forward; the optimiser is the
  fastest way to break that rule at scale.
- Correct role: **confirmation** of a candidate chosen by design intent or
  walk-forward replay, on an unburned window.

Schema reserved, implementation deferred, gated behind Phase 7b acceptance.

---

## 19. What I recommend against building

- A generic "run this command" job, in any disguise.
- An AI verdict that can pass or fail a gate by itself.
- Pixel-diffing images to detect coordinate changes when `objects.csv`
  answers the same question exactly.
- Capturing images for every experiment by default. Most runs never need
  them, and the storage and time are real.
- A web dashboard for the runner. Results are read by Claude and by the
  owner in text.
- Broker/symbol matrix testing before the single-broker single-symbol case
  is understood.
- Auto-promotion of anything to live. The machine may build and measure;
  only the owner arms.

---

## 20. Open questions for the owner

1. **D0 or the stricter variant?** Agent code reviewed-at-restart (my
   recommendation), or `tools/npexec/**` unwritable by Claude with patches
   applied by hand?
2. **Which terminal is the automation terminal?** The script's CONFIG says
   `C:\Program Files\MetaTrader 5`; the bridge doc says the second
   install. They disagree, and that terminal gets closed after every run,
   so it must hold no live charts.
3. **Archive location and budget.** `C:\NeelPrajna\runs\` acceptable? With
   visual bundles added, is there a disk cap, and should runs older than N
   days auto-compress?
4. **`InpRunTag` and `events.csv` — Phase 7a or here?** My reading is that
   `events.csv` is close to the Phase 7 recorder stream. Writing two
   parallel event streams would be a mistake. Should A4.1 be folded into
   Phase 7a instead?
5. **Who writes `tests/windows.json` first**, and does the owner confirm
   BURNED is one-way and owner-only?
6. **Does the in-flight long run get re-done under A2** so it lands with a
   manifest, or do we archive its outputs by hand and start clean from the
   next experiment?
7. **Which AI reviews the images, and where do they go?** An image review
   means sending chart pictures to a model. Is that in-session with Claude
   (owner uploads the shortlist), or an automated API call from the
   runner? The second is more automatic and also the first time this
   pipeline sends project data out by itself. Owner's call.
8. **Is a QRF/IVF pattern reference acceptable inside NeelPrajna docs?**
   §5 cites the technique only, no code. Say if even that should be kept
   out.

## 21. One-line recommendation

Build A1 and A2 next — reliability and run identity. Do the A4.0 spike
early and cheaply, because the answer changes the shape of A4. Do not
build the experiment factory until a single run can prove what produced
it, and do not scale it until a run can also show what it did.
