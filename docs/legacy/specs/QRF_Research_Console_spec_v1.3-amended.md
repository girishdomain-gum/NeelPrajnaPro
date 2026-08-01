# QRF Research Console — Dashboard Specification v1.0 (Future Work)

Status: **PROPOSAL — no implementation yet.** Companion to `Platform
Architecture v1.0` (the Kernel/Trading-plug-in split) and to `ADR-008
(kernel-trading-plugin-split)`. Written in the same discipline as
`dashboard_spec.md` v1.2 and its v1.3 institutional amendment, so the two
consoles — the existing on-chart NeelPrajna panel and this one — read as one
design family rather than two unrelated tools.

Governed by: ADR-008 (Core/Book split), the Communication Contract
(`core/COMMUNICATION_CONTRACT.md`), and the Evidence Pipeline rule that only
the EvidenceBattery may issue a Verdict (`core/EPISTEMIC_RULES.md`). Changes
require a spec amendment committed to the repo, never an ad-hoc UI change —
identical convention to the existing dashboard spec.

Companion mockup: `qrf_research_console_mockup.html` (pixel-honest to a
browser, not an MT5 chart — see §1 for why this console is not an on-chart
panel).

---

## 0. Why a second console, and why it is not on-chart

The existing NeelPrajna dashboard is an MT5 on-chart panel: 360px wide,
built from `OBJ_RECTANGLE_LABEL` / `OBJ_LABEL` / `OBJ_BUTTON`, constrained to
Consolas and ASCII-safe glyphs, and inherently scoped to **one Book** (the
trading plug-in) on **one chart**. The Kernel is explicitly domain-blind
(`core/KERNEL_OVERVIEW.md` §2) and is not a chart-attached process — it has
no natural home inside an MT5 panel, and forcing it into one would either
smuggle trading vocabulary into the Kernel's presentation layer or starve
the Kernel of the richer visualization a knowledge graph and an evidence
ledger actually need (graphs, timelines, filterable tables at row counts an
MT5 object budget cannot hold).

**The QRF Research Console is a separate, browser-based surface**, reading
from the Kernel's own state (a "Kernel State Bus," the Core-side analogue of
StateHub) rather than from `EAState`. It is multi-Book by construction: Book
A (NeelPrajna) is the only populated Book today, but the console's shell
never assumes a single Book, so opening Book B requires no console redesign
— only a new Book entry, per the "growth by mitosis" rule already governing
the documentation tree.

**Visual continuity, not visual reuse.** The console deliberately inherits
the existing dashboard's design tokens (dark HUD, teal accent, Consolas,
hairline rules, right-aligned numerics, one table grammar) so a person
moving between the EA panel and this console recognizes it as the same
product family. It does not inherit the 360px/single-column constraint,
because a browser is not an MT5 chart.

---

## 1. Console shell (always visible)

**Top bar:** `QRF RESEARCH CONSOLE` (label) · Book selector `[ Book A:
NeelPrajna ▾ ]` (dropdown; future Books appear here the day they are opened,
greyed until then) · Kernel health dot (green/gold/red, mirrors
`governance/AUTONOMY_LADDER.md` state) · UTC clock.

**Left nav rail (icons + label, collapsible):** OBSERVE · KNOWLEDGE ·
DISCOVER · EVIDENCE · GOVERNANCE. Exactly five lenses — see §9 for why a
sixth was rejected.

**Footer strip (always visible, same rule as the EA panel's status line):**
Kernel State Bus freshness ("updated 0.4s ago" — silence past a threshold
renders amber, matching `governance/AUTONOMY_LADDER.md`'s "silence is
negative" invariant, G-1) · active Book · console version.

**Rendering rule (identical convention to the EA spec §0):** only the active
lens receives live re-renders; inactive lenses freeze their last frame and
perform one full refresh on activation. The Kernel State Bus itself always
updates regardless of which lens is open — painting is deferred, data is
not.

State: `console.activeLens`, `console.activeBook`, `console.navCollapsed`
(persisted, browser-local — no server round-trip for view state, matching
D8 in the existing spec: view state is not a command).

---

## 2. OBSERVE — Observation Engine health

Purpose: answer "is the Kernel actually seeing the market right now?" before
trusting anything downstream.

2.1 **Feed status table.** One row per registered instrument (InstrumentRegistry):
`INSTRUMENT | SOURCE | LAST TICK | LAG | OBSERVATIONS/MIN`. Lag cell amber
past a per-instrument threshold, red past double that — same semantic-color-
in-text convention as the EA panel, no filled cells except the single
worst-lag row.

2.2 **Anti-hindsight tripwire strip.** One line, always visible when this
lens is open: `ANTI-HINDSIGHT: {n} checks today · 0 violations` (or a red
`VIOLATION — see log` if the property test in `core/KERNEL_OVERVIEW.md` §3
ever fails). This is a Kernel invariant surfaced as UI, not a UI-level
check.

2.3 **Throughput sparkline.** Observations/minute over the last rolling hour,
one polyline per instrument, decimated to ≤128 points — same "one chart per
panel, sparingly used" discipline as the EA's SCOPE equity sparkline
(`dashboard_spec.md` §3.3, D11).

2.4 **RecordStore / BulkStore health.** Two KPI cells: ledger chain integrity
(`RecordStore.verify()` result, PASS/FAIL) and bulk manifest freshness (age
of the newest Parquet manifest). Uses the same KPI-lattice component as the
EA's vitals grid (`dashboard_spec_v1.3` §3) — one shared grammar, less code,
same principle carried across consoles.

---

## 3. KNOWLEDGE — Pattern & Knowledge Graph browser

Purpose: what does the Kernel currently believe, and under what conditions.

3.1 **Pattern table.** `PATTERN ID | WIN RATE | CONFIDENCE | REGIME |
APPLICABILITY | LAST UPDATED`. Applicability renders as a compact scope
chip (instrument · timeframe · session · regime — the Observation Space
fields from `core/COMMUNICATION_CONTRACT.md` §6), not free text, so two
patterns' scopes can be visually diffed at a glance. Sortable columns,
right-aligned numerics — identical convention to VIRT UNIV's table
(`dashboard_spec_v1.3` §4).

3.2 **Graph inspector (single-pattern focus, opened by row click).** Shows
the clicked pattern's neighborhood in the Knowledge Graph: related
hypotheses, contradictions (red edge), supporting evidence (green edge),
missing evidence (dashed grey edge), and the automatic recommendation for
the next experiment, per `KERNEL_OVERVIEW.md` §3's stated Knowledge Graph
behavior. This is the one node-link diagram on the whole console —
deliberately confined to a single-pattern focus view, never an all-patterns
force-directed mess (an explicit design rejection, see §9).

3.3 **Contradiction banner (always-on within this lens).** If any pattern
currently contradicts another, an unmissable strip reads `{n} CONTRADICTION{s}
— review before citing`. Modeled directly on the EA's visual-source badge
(`dashboard_spec.md` §5 delta) — an always-on warning exempt from the
active-lens-only rendering rule, because a contradicted belief is exactly
the kind of state nobody should be allowed to miss by being on the wrong tab.

---

## 4. DISCOVER — Screener & Observatory (candidates, never verdicts)

Purpose: give humans full visibility into what the Kernel is proposing,
while making it structurally impossible to mistake a candidate for a
finding.

4.1 **Mandatory framing header (cannot be hidden, cannot be dismissed):**
`NO VERDICT LIVES ON THIS SCREEN` in the same gold/warning color used for
`BLOCKED` states in the EA panel. This is the console-level enforcement of
the Communication Contract's rule that Screener and Observatory output
carry no evidentiary weight (`COMMUNICATION_CONTRACT.md` §4) — stated in the
UI itself, not left to hover over documentation.

4.2 **Screener shortlist table.** `CANDIDATE | FEATURE SPACE | trial_count |
SUBMITTED` — a "Promote to Hypothesis" action per row (the only
button-styled control on this lens, bordered not filled, per the existing
button-restraint convention) which does not create a Verdict; it only
creates a Hypothesis, queued for §5.

4.3 **Observatory question feed.** A reverse-chronological list of raised
`anomaly_scan + question` pairs (e.g. the Tuesday/Gold example from the
original vision notes), each with a `Promote to Hypothesis` action and a
`Dismiss` action (dismissal is logged, never silent deletion — append-only,
per `governance/AUTONOMY_LADDER.md` §4).

4.4 **Trial-count ticker.** A single always-visible number: current
`TrialCountLedger` running total. Rising quietly in the background is
normal; a sudden jump is the signal an EvidenceBattery reviewer should look
at before trusting the next Verdict at face value.

---

## 5. EVIDENCE — Hypothesis → EvidenceBattery → Verdict

Purpose: the one lens that can show a Verdict, and the one lens built to
make that fact visually unmistakable.

5.1 **Hypothesis queue.** `HYPOTHESIS | SOURCE (human/Screener/Observatory,
origin-blind per §7.1 of the extensibility principles) | STATUS (queued /
running / PASS / FAIL / INSUFFICIENT) | WINDOW`. Status cell is the only
place on the entire console where a filled color block is used other than
the one dangerous control convention borrowed from the EA panel (NUKE) —
Verdicts are treated with the same visual weight as an irreversible action,
deliberately.

5.2 **Window Ledger strip.** `WINDOW {id} · designated {date} · {VIRGIN /
BURNED}` per active window. A burned window renders with a diagonal
hairline hatch (CSS-only, no new object type) so a screenshot alone
communicates "this data cannot be reused," matching the Kernel's own
append-only, no-repair rule (`governance/AUTONOMY_LADDER.md` §4).

5.3 **Epistemic rule reminder (contextual, not always-on).** When a
Hypothesis card is expanded, a small inline note surfaces whichever of R1–R3
(`core/EPISTEMIC_RULES.md`) is most relevant to what's being viewed — e.g. a
multi-arm hypothesis shows the R2 single-variable reminder. This is
deliberately a **reviewer aid, not a gate** — the EvidenceBattery enforces
the rules; the UI only helps a human reviewer apply the same scrutiny.

5.4 **BeliefLayer diff.** On a PASS verdict, a compact before/after strip
shows exactly what changed in the BeliefLayer — never a bare "updated,"
always the specific delta, mirroring the existing dashboard's `NUKED — FLAT
· AUTO OFF` convention of never leaving a state-changing action undescribed.

---

## 6. GOVERNANCE — Supervisor / Runner / autonomy

Purpose: the console's answer to "is the machine currently trustworthy to
leave unattended," at a glance.

6.1 **Autonomy ladder strip.** `L0 ── L1 ── L2 ── L3` rendered as a rail
with the current level lit in accent color — a direct visual counterpart to
`governance/AUTONOMY_LADDER.md` §2, so the ladder is not just documentation
prose but a live-updating fact.

6.2 **Supervisor / Runner health cells.** Two KPI cells, same lattice
component as OBSERVE §2.4: Supervisor state (HEALTHY/DEGRADED/FAILED/STOPPED)
and Runner state, each showing the specific failing check and threshold on
hover — never a bare status word, per G-7 (traceable).

6.3 **Touch counters.** Two large numbers, side by side: **Routine touches
(target 0)** and **Exception touches (external cause, counted not
excused)** — the two-counter design `governance/AUTONOMY_LADDER.md` §2
specifies verbatim, given its own home here rather than buried in a log.

6.4 **Freeze-criterion banner.** A single static line, always present on
this lens: *"No feature may require a Supervisor code change — configuration
only."* Included deliberately as a constant reminder of the test the
Supervisor's freeze exists to pass, not because it is dynamic data.

---

## 7. Cross-cutting behavior

- **Design tokens are shared, not duplicated.** The console's palette is the
  same CSS custom-property block as the EA mockup
  (`--bg`, `--surface`, `--accent`, `--green`, `--red`, `--gold`, etc. — see
  the mockup file's `:root` block), so a future palette change is one file,
  not two designs drifting apart.
- **One table grammar, one KPI-lattice component, one signal-row component** —
  reused verbatim from the existing spec's §3 component grammar. This
  console does not invent new visual primitives; it reuses the ones already
  owner-approved for the trading plug-in.
- **Contract objects are visible, not just structural.** A slide-out "Contract
  Feed" (triggered from the top bar) lists the live stream of the six
  Communication Contract object types as they cross between Core and the
  active Book — useful for debugging, and a constant, honest reminder that
  nothing else is allowed to cross that boundary.
- **Origin-blindness is a UI rule, not just a Kernel rule.** Nowhere on this
  console does a Hypothesis or Pattern's card visually distinguish
  human-submitted from machine-discovered origin beyond the plain-text
  `SOURCE` column in §5.1 — no icon, no badge, no color — enforcing
  `core/COMMUNICATION_CONTRACT.md` §7's "origin grants no shortcuts"
  principle at the presentation layer too.

## 8. Out of scope (v1.0)

Per-Book deep dashboards (NeelPrajna's own LIVE/VIRT UNIV/SCOPE/CTRL panel
stays exactly where it is, on-chart, unchanged by this spec) · natural-
language hypothesis authoring · any control that writes to the Kernel
(this console is read-only in v1.0 — "Promote to Hypothesis" queues a
request for a human-run process, it does not itself invoke
`EvidenceBattery.run()`) · alerting/notification channels · mobile layout.

## 9. Design rejections (recorded so they aren't re-litigated)

- **A sixth "BOOKS" lens was rejected** in favor of a top-bar Book selector.
  Books are a cross-cutting context switch (everything in OBSERVE through
  GOVERNANCE is Book-scoped except GOVERNANCE's Supervisor/Runner state,
  which is programme-wide), not a fifth thing to look *at* — making it a
  selector rather than a destination keeps that distinction visible.
- **An all-patterns force-directed graph view was rejected** for §3.2 in
  favor of a single-pattern focus view. A whole-graph view answers a
  research question worth having eventually, but it is not a v1.0
  dashboard need, and a force-directed layout at real pattern-library scale
  degrades into an unreadable hairball well before it becomes useful —
  parked, not designed away permanently.
- **A combined DISCOVER/EVIDENCE lens was rejected.** They were drafted as
  one lens first; splitting them was the single highest-value change in
  this proposal, because it makes "does this screen carry a Verdict?" a
  question answerable by which lens is open, never by reading carefully.

## 10. Read-only v1.0, and what v1.1 is expected to add

This spec is deliberately read-only so it can ship without touching the
Kernel's write paths at all. The known, deferred v1.1 candidates: a
"Promote to Hypothesis" action that actually enqueues (currently a UI stub
per §8); an EvidenceBattery run-trigger button (currently human-run outside
the console); and a Book-comparison view once a second Book actually opens.
None of these block v1.0 sign-off; all are named here so they enter the
roadmap as scoped future work rather than silent scope creep later.

---

## v1.1 Amendment — states, multi-Book, and detail views

Written after a closer read of the live EA panel's actual implementation
(`Panel.mqh`, `Config.mqh`, `ScopeTab.mqh` at the current shipped revision,
not just the v1.2/v1.3.2 spec text). Additive to v1.0 (§0–§10 unchanged).
Companion mockup: `qrf_research_console_mockup_v1.1.html`.

### A. A finding this amendment is built on: specs drift from code, and that's fine if it's tracked

The v1.3.2 amendment text implies `PANEL_BODY_H` around the v5.4.0-era
value; the shipped `Panel.mqh` is already at **532px** (a v5.5.5 change, "
mockup-height pipeline rows 17→23px; risk gauge row retired"), and the
object budget is **480**, not the 340 the v1.3.2 risk section states.
Neither document is "wrong" — the spec is a decision record, the code is
the current truth, and the gap between them is exactly what an amendment
exists to close. **This console spec adopts the same discipline explicitly:
every future implementation discovery gets appended here as a lettered
delta, never silently reconciled by editing history.** This amendment is
itself the first proof of that practice.

### B. Design tokens — one token was missing in v1.0

`CFG_CLR_ACCENT2` (`#508CFF`, electric blue) exists in the live palette for
secondary chart-side emphasis (Trail SL) and was omitted from the v1.0
console mockup's `:root` block. **Added in v1.1**: used for the console's
*secondary* selection state (a row hovered but not yet opened) so ACCENT
(teal) stays reserved for "this is the active/applied thing," exactly the
restraint rule §3 of the existing dashboard's institutional pass already
established for the EA panel.

### C. Every lens needs three states, not one

The v1.0 mockup showed only the populated state. A dashboard spec that only
specifies the happy path is the same mistake the EA spec's own history
warns against (empty-state wording is a first-class, deliberate design
decision there — `ScopeTab.mqh`'s "no virtual trades closed yet" convention
— not a placeholder afterthought). Each lens now has three named states:

| State | Trigger | Convention |
|---|---|---|
| **Cold-start / empty** | The Kernel or a Book has produced nothing yet in this category | Muted single-line text in the first row's position, exact EA-panel phrasing pattern ("no {noun} {past-participle} yet") — never a blank table |
| **Degraded** | The Kernel State Bus is stale past threshold, or a dependency (RecordStore, Supervisor) is unhealthy | Every value that cannot currently be trusted renders in `--muted` grey with a trailing `‡` mark and a footer note naming which dependency is degraded — never a silently frozen-looking stale number |
| **Populated** | Normal operation | As shown in the v1.0 mockup |

### D. The Book selector is a real flow, not a decoration

v1.0 showed the selector as a static "Book A: NeelPrajna ▾" chip. v1.1 specs
its actual behavior:

- **Opening the dropdown** lists every declared Book: populated ones show
  their one-line health summary inline (mirrors the EA panel's advisor
  status-line convention); a Book that has not yet opened (no Application
  Book folder exists per `docs/books/`) renders **greyed, non-clickable**,
  labeled `NOT YET OPENED` — the console-level enforcement of "growth by
  mitosis, never pre-allocation" (the same rule already governing the
  documentation tree) made visible, not just written down.
- **Switching Books** re-renders all five lenses from that Book's slice of
  the Kernel State Bus. GOVERNANCE is the one lens that does NOT change
  (§6 already notes it is programme-wide) — its content is identical
  regardless of which Book is selected, and the lens header's "Book A" tag
  is replaced with "Programme-wide" as a constant, not a variable.

### E. Two detail views, opened from a row click, closed by an explicit control

Neither view is a route change — both are an overlay on the current lens,
dismissed by an explicit close control (never click-outside-to-dismiss,
matching the EA panel's philosophy that a state-changing or view-changing
action should always be an explicit, nameable control, D8-style).

**E.1 — Hypothesis detail** (opened from EVIDENCE §5.1 row click). Full
history for one hypothesis: originating candidate (with its Screener/
Observatory source), every window it has run against with VIRGIN/BURNED
status, the specific R1–R3 reminder relevant to its shape (§5.3, now shown
expanded rather than inline-summarized), and — only if a Verdict exists —
the exact BeliefLayer diff. A hypothesis with no Verdict yet shows the
"awaiting EvidenceBattery" cold-start state per §C, not an empty page.

**E.2 — Contradiction detail** (opened from KNOWLEDGE §3.3's banner). The
two (or more) contradicting patterns shown side by side with their full
scope chips, supporting-evidence counts, and confidence — deliberately
presented as data for a human to weigh, with **no resolve button and no
suggested winner**. The Kernel does not adjudicate its own contradictions;
a human does, by opening a new Hypothesis that tests which pattern (if
either) survives a stricter Observation Space. The only action available
here is `Open resolving Hypothesis →`, which hands off to EVIDENCE.

### F. What v1.1 deliberately still does not add

Live WebSocket push (the mockup remains a static illustration of states,
not a working app) · a Book-comparison view (still parked, now explicitly
for v1.2) · any write action beyond the existing "Promote to Hypothesis"
stub. Naming these here keeps the boundary honest the same way §8 did for
v1.0.

---

## v1.2 Amendment — grounded in the real Knowledge Base, the real Evidence Battery, and the Generation 1→2 research cycle

Written after reading the actual early Kernel-side Python already in the
repository — `np_knowledge_base.py`, `np_probability_engine.py`,
`np_hypothesis_zero.py`, `np_feature_service.py` — rather than describing
the Kernel only from the Platform Architecture's abstractions. This is not
a hypothetical console anymore in one important sense: **eighteen of its
hypotheses, one real battery, and one real knowledge base already exist on
disk.** Companion mockup: `qrf_research_console_mockup_v1.2.html`.

### G. KNOWLEDGE is grounded in the real 18-hypothesis founding set

`np_knowledge_base.py`'s `FOUNDING` list is not a placeholder — it is 18
real hypotheses (H-01…H-18), each with a real **lineage** (the legacy MQL5
gate or standalone indicator it traces to — e.g. H-07 traces to
`LiquiditySweepGate.mqh → np_feature_service.py`) and a real **executable
definition** path. KNOWLEDGE §3.1's pattern table is revised to show this
schema directly rather than an invented `#hash4` scope chip:

`ID | HYPOTHESIS | LINEAGE | MATURITY | STATUS | EVIDENCE`

- **Maturity (M0–M9)**, exactly as coded: M0 idea · M1 observable defined ·
  M2 feature implemented · M3 evidence collected · M4 statistically
  validated · M5 paper validated · M6 live validated · M7 production ·
  M8 retired · M9 historical reference. Rendered as a 10-segment mini-rail
  (same visual language as GOVERNANCE's autonomy ladder, §6.1) so maturity
  reads as a position on a ladder, not a bare code.
- **Status** (`candidate / validated / decayed / rejected / archived`) is
  a separate axis from maturity, exactly as the code keeps them separate.
  **`validated` can only be set by a Probability Engine PASS verdict —
  humans cannot promote it themselves**, and the console enforces this
  visually: the status cell for `validated` renders with a small lock glyph
  and cannot be clicked to edit, on any Book, ever.
- **Rejected is sticky.** Reopening a rejected hypothesis requires a
  documented reason, permanently recorded in the append-only journal
  (`kb_journal.jsonl`). The console's row action for a rejected hypothesis
  is `Reopen (reason required) →`, never a plain re-activate toggle.

### H. EVIDENCE's Hypothesis detail is grounded in the real seven-gate battery

The v1.1 mockup's Hypothesis detail modal (amendment §E.1) showed a generic
PASS pill and a generic BeliefLayer diff. `np_probability_engine.py`
implements a specific, pre-registered seven-gate battery, frozen before any
P&L was observed, and the detail modal now shows exactly these gates,
matching the code's own field names so a person reading the console and a
person reading the code see the same vocabulary:

| Gate | Checks | Renders as |
|---|---|---|
| B1 sample floor | ≥100 in-sample AND ≥100 out-of-sample trades | pass/fail chip + the two counts |
| B2 OOS discipline | Final 40% chronologically, evaluated once | a fixed protocol note, not a per-run number — it is a design constant, not a statistic |
| B3 significance | Bootstrap CI of mean net R excludes 0 (97.5%, Bonferroni m=2) | the CI interval itself, not just pass/fail |
| B4 walk-forward | 4 folds; late/early expectancy ratio (WFE) ≥ 0.5 | the WFE ratio as a number, e.g. `0.83` |
| B5 perturbation | ±10% on 4 parameters; profit factor ≥ 1.0 in every variant | a small per-variant PF table, not a single pass/fail |
| B6 Monte Carlo | 1000 order-shuffles; p95 max drawdown ≤ 15R (OOS) | the p95 value against the 15R budget |
| B7 cost sensitivity | Net expectancy > 0 at 1.5× costs, OOS | the stressed expectancy number |

**Any single FAIL fails the hypothesis** — the modal's overall verdict pill
is computed the same way the code computes it (`all_pass`), never a
separately-set UI value. If B1 fails, the modal shows only B1 and the
verdict `INSUFFICIENT_EVIDENCE` — the code returns early in exactly this
case ("sample floor not met — not a verdict on the edge"), and the console
must not synthesize the other six gates' numbers when the code never
computed them.

### I. Calibration status — the selftest, surfaced

`np_probability_engine.py selftest` runs the battery against three planted
cases — a planted edge (must PASS), a random walk (must FAIL), and an
artificially small sample (must return INSUFFICIENT_EVIDENCE) — before the
battery is trusted on anything real, exactly the "trust follows
demonstration" principle from the Communication Contract's extensibility
principles (§3.5 of the earlier architecture volume). GOVERNANCE gains one
new KPI cell: **Battery selftest** — `PASS` (green) only if all three
planted cases resolved as expected on the most recent run, with the actual
three verdicts shown on hover, never a bare "OK."

### J. New lens — CYCLE: the Generation 1→2 research loop

The one major idea from the original vision notes not yet given its own
screen: the shift from a human proposing every hypothesis (Generation 1)
toward the Kernel discovering candidates itself (Generation 2), and the
continuous loop this produces once it does — *observe → discover →
generate hypotheses → prioritize → validate → learn → update beliefs →
publish reports → repeat forever.* Added as a sixth nav-rail lens.

**J.1 Generation indicator.** A two-state chip, `GEN 1 — HUMAN PROPOSES`
or `GEN 2 — KERNEL PROPOSES, HUMAN REVIEWS`, reflecting whether any
hypothesis in the current Book currently originates from the Screener/
Observatory (§4) rather than a human. Today, on Book A, this reads **GEN 1**
honestly — none of the 18 founding hypotheses originated from the Kernel
itself yet; they were human-proposed and only their evidence-gathering is
automated. The console does not overstate where the programme actually is.

**J.2 The loop, as a rail.** Eight stages rendered left to right — Observe
· Discover · Generate · Prioritize · Validate · Learn · Update Beliefs ·
Publish — with the stage(s) currently active for the selected Book lit in
accent color. For Book A today: **Observe** (OBSERVE lens, live) and
**Validate** (EVIDENCE lens, the B1–B7 battery actively running against
H-07/H-16) are lit; Discover/Generate/Prioritize are dim because the
Screener and Observatory are specified (`core/KERNEL_OVERVIEW.md`) but not
yet the source of any of Book A's current hypotheses.

**J.3 Why this is a Kernel-wide lens, not per-Book.** The loop describes
the Kernel's own operating cycle, not a Book's data — mirroring
GOVERNANCE's Book-invariant convention (amendment §D). Only the *content*
lit at each stage (which hypotheses, which observations) is Book-specific;
the rail itself is one Kernel-wide diagram.

### K. What v1.2 still does not add

A live link from the CYCLE rail's "Discover" stage to actual Screener
output (still routed through the existing DISCOVER lens only) · automatic
demotion of a hypothesis from `validated` to `decayed` shown as a live
event (currently would require a KNOWLEDGE lens refresh) · a second Book's
own founding hypothesis set (Book B's KNOWLEDGE lens stays in the cold-start
state from amendment §C until it has any). Named here, not silently
deferred.

---

## v1.3 Amendment — Correction: the console was grounded in the wrong Kernel

Written 2026-07-29, after reading the real F:\QRF repository directly for
the first time (`QRF_docs_export.txt`, `QRF_work_export.txt`). This is a
correction, not an extension, and it is the most consequential amendment
this document has received.

### P. What was wrong

Amendment v1.2 (§G–§J) grounded the KNOWLEDGE and EVIDENCE lenses in
`np_knowledge_base.py`'s 18-hypothesis founding set and
`np_probability_engine.py`'s seven-gate battery, describing them as "the
real Kernel data" to distinguish them from earlier, illustrative mockup
content. That framing was a genuine error, not a simplification. Those two
scripts are **NeelPrajna's own small, bespoke research tooling** — written
once, never IVF-drilled, never subjected to a planted-fraud test, with no
selftest-gate discipline and no multi-AI governance record behind them.
**They are not the QRF Kernel.** The real Kernel is a separate repository,
F:\QRF, ten sprints old, Generation 1 closed 2026-07-26, with a
fundamentally more rigorous battery (`qrf/kernel/battery/battery.py`), a
real hash-chained ledger (`qrf/kernel/records/store.py`), a real window-burn
mechanism (`qrf/kernel/protocol/windows.py`), and a real, honestly-counted
trial ledger (`qrf/kernel/corrections/trials.py`).

The error is easy to see in hindsight: v1.2 could only ground the console in
whatever Kernel-shaped code was reachable at the time, and NeelPrajna's own
scripts were the closest thing available. That is precisely the "two-clock
drift" risk this engagement's own Volume II flagged in the abstract, now
observed concretely, in this document, by this author.

### Q. The correction

Every data binding in §G ("KNOWLEDGE — the real 18-hypothesis founding set")
and §H ("EVIDENCE — the real seven-gate battery") should be read as
describing **NeelPrajna's own bespoke research layer**, not the QRF Kernel.
The console's actual KNOWLEDGE and EVIDENCE lenses, once built against the
real Kernel, bind instead to:

| Console element | v1.2's (wrong) source | Corrected source |
|---|---|---|
| Pattern/hypothesis table | `np_knowledge_base.py` FOUNDING list | `qrf/kernel/records/store.py` (RecordStore), filtered to `hypothesis` records |
| Maturity/status | Hand-rolled M0–M9 + candidate/validated enum | QRF has no equivalent maturity ladder yet — a Generation 2 Foundations-track candidate (see ROADMAP_GENERATIONS_2-4.md §3 Track 2), not yet built. The console should show NeelPrajna's ladder only inside a Book-A-scoped view, never as if it were Kernel-wide. |
| Battery gates (B1–B7) | `np_probability_engine.py` | `qrf/kernel/battery/battery.py`'s real 9-step pipeline: type check, selftest gate, window checks, splits, simulate, placebo, trial correction, tri-state verdict, atomic write+burn |
| Verdict states | PASS / FAIL / INSUFFICIENT_EVIDENCE (NeelPrajna's own naming) | Confirmed identical naming in the real Battery — this one detail was, by good fortune, already correct |
| Window/reuse protection | None in NeelPrajna's own scripts | `qrf/kernel/protocol/windows.py` — TRAINING/EXPLORATION/VIRGIN designation, burn-on-use, structural refusal on reuse |
| Trial accounting | None in NeelPrajna's own scripts | `qrf/kernel/corrections/trials.py` — registration spends the attempt (ADR-011) |

### R. What this means for the console's design, going forward

The five-lens shell (OBSERVE / KNOWLEDGE / DISCOVER / EVIDENCE / GOVERNANCE)
and the CYCLE lens added in v1.2 remain the right shape — nothing in this
correction changes the console's structure. What changes is which repository
the data comes from, and a new precondition: **the console cannot show real
KNOWLEDGE/EVIDENCE data for NeelPrajna until NeelPrajna's hypotheses actually
exist inside the real Kernel's ledger.** That migration is not yet done. It
is proposed, concretely and with a scoped first sprint, in
`NeelPrajna_QRF_Integration_Path.docx` \u2014 port H-07 only, as a real
Hypothesis YAML and detector, and re-judge it with the real Battery. Until
that sprint runs, the console's KNOWLEDGE/EVIDENCE lenses for Book A should
show QRF's actual current concept families (`classical`, `seasonality`,
`smc` \u2014 the ones judged in Generation 1) and an explicit cold-start state
(per amendment §C) for anything NeelPrajna-specific, rather than
NeelPrajna's bespoke data dressed as Kernel data.

### S. A note on why this correction belongs here, not in a quiet edit

This project's own subject matter argues for exactly this response to
finding an error: QRF's Generation 1 report states, as one of its Twelve
Principles, that history is append-only and corrections are new records,
never rewrites. Editing v1.0/v1.1/v1.2 in place to make the error
disappear would be the one move this whole engagement has spent the most
words arguing against. The correction is recorded here, dated, with the
mechanism named, for the same reason QRF's own ledger never deletes a
bad record \u2014 because the fact that a mistake happened, and how it was
caught, is itself part of the evidence.



