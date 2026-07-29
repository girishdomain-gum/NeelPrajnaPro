# NeelPrajna Dashboard — Live Advisor Detail & Settings (v1.4 Amendment)

Status: PROPOSAL for owner sign-off. Extends `dashboard_spec.md` v1.2 + the
v1.3/v1.3.1/v1.3.2 institutional amendments. **This document is about Book
A — NeelPrajna's own trading-plug-in dashboard — not the QRF Research
Console.** That distinction is the entire reason this document exists; see
the note below before reading further.

Governed by ADR-001 + ADR-002, same as the parent spec. Data bindings below
are to real StateHub fields and real NPSU CSV schemas (`NPSU-A1`, `NPSU-S1`,
`NPSU-T1`), not illustrative names — every field cited here exists today in
`AdvisorEngine.mqh` and `UniverseLogger.mqh`.

---

## 0. Why this document exists, stated plainly

Three consecutive requests asked for mockups of NeelPrajna's Live Advisor —
its best-strategy detail, Observation Space, analysis stats, entry/exit
criteria, and a settings tab. Three consecutive responses instead expanded
the **QRF Research Console** (the future Kernel/Core side). That was a real
miscommunication, not a preference: "future work for NeelPrajna" was read
as "the Platform Architecture's future Kernel vision," when the actual ask
was "go deeper on NeelPrajna's own dashboard, on the parts that are thin
today" — specifically, the Live Advisor, which the existing spec currently
gives only a one-line status string (§2.4: *"ADVISOR status line ·
eligibility · hysteresis · recommendation"*) and a single toggle
(§4.2: *"ADVISOR LINE (CMD_SET_ADVISOR)"*). This amendment is that missing
depth, on the correct side of the Core/Book boundary — Book A, on-chart,
same design language as `neelprajna_dashboard_v5.2_mockup.html`.

**Placement decision:** no new top-level tab. Per the v1.3.1 ruling
("tabs are permanent" — §1 of that amendment), a fifth tab is not free to
add casually. The detail below is placed as: (a) an expansion of **SCOPE**
when the bound strategy is the current advisor pick, and (b) a new
**ADVISOR SETTINGS** section inside **CTRL**, beside the existing single
toggle. Both are additive to existing tabs, not new surfaces.

---

## 1. Best Strategy Card (SCOPE tab, advisor-bound state)

When SCOPE is bound to the advisor's current recommendation (auto-bound per
v1.3.1 §2, or explicit via VIRT UNIV double-click), the header gains a
dedicated card above the existing vitals grid.

1.1 **Recommendation identity.** `★ {name} #{hash4}` in accent color,
    exactly as VIRT UNIV marks it, plus the eligibility state:
    `ELIGIBLE` (green) or the specific reason it is not
    (`INELIGIBLE — n<{min_trades}` or `INELIGIBLE — unvalidated`).
    Data: `NPSU-A1.recommendation`, `NPSU-A1.eligible_count`.

1.2 **Hysteresis meter.** A 3-segment (or `InpADV_ConfirmEvals`-segment)
    progress rail showing how many consecutive evaluations the current
    challenger has won, e.g. `CHALLENGER 2/3` with the third segment
    outlined but unlit. Data: `NPSU-A1.note` (`"challenger x/y"` parsed) —
    **this field already carries exactly this string**, the UI only needs
    to render it as a rail instead of raw text.

1.3 **Status line, verbatim.** The exact `NPSU-A1.note` enum rendered in
    full: `initialized | holds | challenger x/y | RECOMMENDATION CHANGED |
    no eligible universe`. Never paraphrased — this is the same discipline
    as the existing spec's rule that a blocker's exact enum value drives
    the status line (§5, D6).

1.4 **Benchmark comparison — vs. holding U0 MIRROR.** Two-column mini
    table: the recommended universe's `best_net_R` / `best_trades` /
    `best_dd_R` / `best_streak` / `best_pf` beside U0 MIRROR's own
    `mirror_net_R` / `mirror_trades` in the same window. This answers the
    single most important question a recommendation must answer —
    *"is switching actually better than doing nothing?"* — using fields
    that already exist in `NPSU-A1` for exactly this comparison.

1.5 **Auto-Adopt relationship banner (conditional).** If
    `InpADV_AutoAdopt != NONE`, a small gold banner reads: `AUTO-ADOPT is
    ACTIVE for this criterion — this card is advisory context, not the
    switch itself.` This directly addresses the safety-asymmetry finding
    from the earlier Auto-Adopt audit: the card must never let a person
    mistake the (hysteresis-protected) recommendation shown here for the
    (non-hysteresis) mechanism that may already have acted.

---

## 2. Observation Space panel (SCOPE tab, new section)

Grounded in `NPSU-T1`'s real per-trade columns — `symbol`, `chart_tf`,
`open_hour`, `open_dow`, `atr14_open`, `spread_pts_open`. No field is
invented; where a concept (like "session") is a UI convenience rather than
a native column, that is stated explicitly rather than implied.

2.1 **Instrument & timeframe chip.** `{symbol} · {chart_tf}` — native
    fields, direct passthrough.

2.2 **Session distribution (derived, labeled as such).** A 5-bucket bar
    (Asia / London / Overlap / NY / Late) built by grouping `open_hour`
    into fixed server-time ranges **in the UI layer only** — a small
    footnote reads *"derived from open_hour; NeelPrajna does not compute a
    native session field."* This keeps the panel honest about what the EA
    actually tracks versus what the analyzer/console computes for display,
    the same distinction the QRF Console's Observation Space concept draws
    at the Kernel level, now made concrete for one real universe.

2.3 **Volatility context.** `atr14_open` distribution (min/median/max
    across this universe's trade history) as three numbers, not a chart —
    per the existing spec's D11 discipline (one chart per panel, the
    equity sparkline already claims that slot).

2.4 **Spread context.** `spread_pts_open` — shown as a single median value
    with a footnote if it is constant across the run (*"fixed-spread
    tester setting"*, per the data dictionary's own documented caveat) so
    a person does not mistake a backtest artifact for a live spread
    regime.

2.5 **Counterfactual bias states (advanced, collapsed by default).**
    `b1_state…b4_state` — all four bias gates' state at entry, logged
    regardless of this universe's own bias mask. Collapsed under a
    `COUNTERFACTUAL ▸` disclosure because it answers a research question
    ("would a different bias combination have agreed here too?"), not an
    operational one — matching the existing spec's out-of-scope boundary
    (§6) that deeper analysis belongs to the analyzer, while still
    surfacing the raw fact that the data exists for it.

---

## 3. Analysis Details panel (SCOPE tab, replaces the current single vitals grid with a fuller one)

The current spec's SCOPE vitals grid (§3.2) has six cells. `NPSU-S1` has
materially more real fields already computed by the EA every summary
interval. This amendment expands the grid to a scrollable 12-cell version
(still the same KPI-lattice component, §3 of the v1.3 institutional pass —
no new visual primitive):

`TRADES · WIN% · NET R · PF · MAX DD (R) · WORST STREAK · BEST STREAK ·
AVG WIN (R) · AVG LOSS (R) · SHARPE/TRADE · AVG DURATION (min) · SKIPPED
(signals+spread)`

3.1 **Exit-reason breakdown.** A small 4-segment bar —
    `exits_tp / exits_sl / exits_betrail / exits_eor` — beneath the grid.
    `exits_eor` (forced END_OF_RUN closes) renders in muted grey with a
    footnote that these are excluded from profit factor, per the data
    dictionary's own documented rule.

3.2 **Ambiguous-bar rate.** `ambiguous_bars / trades` as a percentage,
    amber past a threshold, with the exact footnote already in the data
    dictionary: *"a high rate means M1 resolution is too coarse for these
    levels."* This is a data-quality signal the EA already computes and
    the current spec simply never surfaces.

3.3 **PF insufficient-data guard.** If `trades < 20`, the PF cell renders
    `PF —· n<20` instead of a literal `INF` (the data dictionary notes PF
    is literally infinite with zero losses) — never show a number the data
    dictionary itself says to distrust.

---

## 4. Entry/Exit Criteria panel (SCOPE tab, expands the current one-line eyebrow)

The current spec's eyebrow line (§3.1: `bias {mask} · trig {mask} · RR {x}
· trail {on/off}`) is the raw DSL. This amendment adds a plain-language
translation beneath it, parsed directly from the same `cfg` string —
`name=T1_B1B6;bias=B1+B6;trig=T1;trail=0;be=1;rr=3.0` becomes:

```
ENTRY   ALL of: B1 Nexis MA crossover + B6 RegChannel MTF trend
        must agree on direction, AND
        ANY of: T1 Pattern (3-candle reversal / sweep-reclaim)
        fires a pulse in that direction
EXIT    Target 3.0R · Break-even ON · Trail OFF
```

4.1 **Grammar note, shown as a tooltip on "ALL"/"ANY", not as prose.**
    *Bias gates are ANDed (every enabled one must agree); trigger gates
    are ORed (any enabled one may fire)* — the BIAS×TRIGGER model from
    `HANDOVER.md`, given its plain-language form directly beside the
    strategy it governs, not only in a design document.

4.2 **Retired-gate guard.** If a universe's `cfg` somehow names a retired
    gate (T6, B5 — should not occur post-migration, but the parser must not
    silently accept it), the criteria panel renders a red `UNKNOWN GATE —
    definition may be stale` banner rather than a blank or wrong
    translation.

4.3 **Management rule line.** Trail/BE state already exists in the DSL;
    this section adds the *behavior*, not just the flag: `Trail OFF` gets
    the tooltip *"stop stays at initial distance for the life of the
    trade"*; `Trail ON` gets *"stop follows the closing-bar extreme, per
    TradeManager's pessimistic same-bar rule."*

---

## 5. Settings — Advisor Configuration (CTRL tab, new section beside §4.2)

Directly renders `AdvisorEngine.mqh`'s actual input block — this is the
exact dropdown from the reference screenshot, specified field-for-field so
implementation and mockup cannot drift apart the way the v1.3.2 palette
already did once (see the QRF console's own v1.1 amendment §A for that
precedent — this section exists precisely to avoid repeating it here).

5.1 **Auto-adopt criterion.** Dropdown, four options, **in the exact order
    the enum comments specify** (not numeric enum order — the UI order is
    a deliberate authoring choice already made in the code and must not be
    "corrected" by a future implementer):
    `4: manual — decide from the Python reports` (default) ·
    `1: highest win rate (tiebreak: net R)` ·
    `2: highest account value (net R)` ·
    `3: best last trade — whoever is in form right now`.
    Data/command: `InpADV_AutoAdopt` → `CMD_SET_AUTOADOPT(mode)`.

5.2 **Warm-up.** Stepper, `InpADV_AutoWarmup` (default 10 trades) —
    tooltip: *"trades a universe needs before it may be adopted."*

5.3 **Require-all toggle.** `InpADV_AutoRequireAll` (default OFF) —
    tooltip warns exactly as the code comment does: *"may block on slow
    gates."*

5.4 **Cooldown.** Stepper, `InpADV_AutoCooldownMins` (default 60) —
    tooltip: *"minimum minutes between adoptions (anti flip-flop)."*

5.5 **Advisory-path settings, grouped separately below a hairline rule**
    (visually separating the two paths per the Auto-Adopt audit's core
    finding — they are not one feature): `InpADV_WindowDays` (30) ·
    `InpADV_MinTrades` (30) · `InpADV_ConfirmEvals` (3) ·
    `InpADV_RequireValidated` (ON) · `InpADV_Alert` (OFF).

5.6 **Master gate reminder, always visible in this section (not a
    tooltip).** *"Auto-Adopt and the advisory recommendation both require
    NPSU SHADOW ENGINE + InpNPSU_AllowApply — see §4.2."* — a direct link
    back to the existing master toggles so the two settings blocks are
    never edited in isolation from each other.

5.7 **Live preview.** As each stepper/dropdown changes, a one-line preview
    updates beneath the group: *"With these settings: a universe becomes
    adoptable after 10 trades, and the real account will not switch more
    than once per 60 minutes."* Plain-language consequence, not just the
    raw numbers — the same translation principle as §4's criteria panel.

---

## 6. Data bindings (summary table)

| UI element | Field | Source |
|---|---|---|
| Recommendation identity | `recommendation`, `eligible_count` | NPSU-A1 |
| Hysteresis meter | `note` (parsed `challenger x/y`) | NPSU-A1 |
| Benchmark comparison | `best_*`, `mirror_*` | NPSU-A1 |
| Session/volatility/spread context | `open_hour`, `open_dow`, `atr14_open`, `spread_pts_open` | NPSU-T1 |
| Counterfactual bias states | `b1_state…b4_state` | NPSU-T1 |
| Analysis details grid | `trades…avg_duration_min` | NPSU-S1 |
| Entry/exit criteria | `cfg` (DSL string) | NPSU-T1 / NPSU-S1 (`cfg` column) |
| Advisor settings | `InpADV_*` | AdvisorEngine.mqh inputs |

## 7. Out of scope (unchanged from the parent spec, restated for clarity)

Per-strategy equity charts beyond the sparkline, full hourly heat-maps,
multi-strategy comparisons, verification reports — these remain
`np_dashboard.py` / `np_universe_analyzer.py`'s job (parent spec §6). This
amendment surfaces real-time context and the most recent snapshot on-chart;
it does not turn SCOPE into the analyzer.

## 8. Exit checks (same discipline as every other dashboard change)

Compile 0/0 · tester deal list byte-identical to baseline (this is display
logic over existing StateHub/NPSU fields, must not touch trading) · visual
sign-off on demo chart vs. the companion mockup · object budget recount
(new grid cells + criteria text add objects; assert under the current cap
per Panel.mqh's `LAY_MAX_OBJECTS`).

---

## v1.5 Amendment — LIVE and VIRT UNIV, the two tabs not yet covered

The v1.4 amendment covered SCOPE and CTRL (the Live Advisor's own detail
and settings). It did not touch **LIVE** (the real-account tab) or
**VIRT UNIV** (the roster tab) — the two tabs the Book A architecture
diagram's six labels (Live Execution, Risk Management, Order Handling,
Dashboard, Position Management, Live Decisions) actually describe most
directly. This amendment closes that gap, grounded in `LiveTab.mqh`,
`MoneyManager.mqh`, `TwoPCRule.mqh`, and `UnivTab.mqh` exactly as shipped.
Companion mockup: `neelprajna_live_univ_mockup.html`.

### L. A correction worth stating plainly first

Re-reading `TwoPCRule.mqh` while grounding this amendment found that **the
"2% Rule" is a profit-take auto-close, not per-trade risk sizing** —
`input double InpTwoPCThreshold` closes every EA position on the symbol
once floating profit reaches that percentage of balance. Per-trade risk
sizing is a *separate* mechanism in `MoneyManager.mqh`
(`MM_RiskLimitLot`, clamped to `CFG_MaxRiskPct` of balance). The two are
easy to conflate because both are percentage-of-balance rules; this
amendment keeps them in visibly separate sections (§M.2 vs §M.3) rather
than merging them into one "risk" card, exactly to avoid that conflation
in the UI the way it nearly happened in this analysis.

### M. LIVE tab — deep views (maps to Live Execution, Risk Management, Order Handling, Position Management, Live Decisions)

**M.1 — Live Execution & Decisions (pipeline detail).** The existing
two-line pipeline readout (§1.3: `BUY ▲ | {trigger} | {blocker|OK→FIRE}`)
gains an expandable history: the last 5 blocker transitions with
timestamps, so a person can answer "why hasn't this fired in 20 minutes?"
without waiting for the next state change. Every blocker value is the real
enum, not paraphrased:

`BLK_NONE · BLK_SPREAD · BLK_MARGIN · BLK_MAX_POS · BLK_SESSION ·
BLK_AUTO_OFF · BLK_NO_STRATEGY · BLK_RETRY_COOLDOWN · BLK_MANUAL_REFUSED ·
BLK_TWO_PC_ARMED`

A small reference strip (collapsed by default) defines each in one line,
so a person unfamiliar with the codebase can read the blocker name and
immediately know what it means, without opening `Config.mqh`.

**M.2 — Risk Management: per-trade sizing.** New card, sourced from
`MoneyManager.mqh`: current effective lot (`MM_GetEffectiveLot`), the risk
cap in force (`CFG_MaxRiskPct` of balance, in both % and $), and — only
when a lot was actually clamped — a one-line note: *"lot reduced from X to
Y to stay inside the {pct}% cap."* If the minimum broker lot itself would
exceed the cap, the real refusal path (`MM_RiskLimitLot`'s "REFUSED" case)
surfaces as a status-line message, never a silent skipped trade.

**M.3 — Risk Management: 2% profit auto-close (kept visually separate from M.2).**
Its own smaller card: armed state, threshold, and current floating
profit as a percentage of balance on a small progress bar toward the
threshold — so a person can see "how close" the account is to an automatic
close, which the existing spec's plain ON/OFF chip does not convey.

**M.4 — Order Handling & Position Management.** The existing OPEN rows
(§1.4: dir+lots, entry, sl, live R, `[BE] [½]`) gain one derived field per
row: **trail state** (`TRAILING` / `STATIC` / `AT BREAK-EVEN`), computed
from comparing the current SL to the entry price and the trail rule —
this is display-only derived state, not a new StateHub field, so it adds
no engine coupling. `LT_MAX_OPEN = 4` stays the real display cap (REAL is
a single-strategy radio account per ADR-001 §2.6); a 5th simultaneous
position, if it ever occurs, shows a `+1 more (not shown)` row rather than
silently dropping it.

**M.5 — The "½" glyph decision, restated so it isn't re-litigated.** Per
the code's own recorded ruling (P4-2 review, 2026-07-22): the partial-close
button ships as ASCII `"1/2"`, permanently — not a temporary gap. This
amendment's mockup uses `"1/2"` for exactly this reason, not as an
oversight.

### N. VIRT UNIV tab — deep views (maps to Dashboard, the roster side of the architecture box)

**N.1 — Full sort + pager, exactly as coded.** Sort cycles through the
real five keys in `UnivTab.mqh`'s order — `NET R (default) → TRD → WIN% →
PF → MAXDD` — shown as a small cycling chip, not a dropdown (matching the
existing spec's parked "SORT stays a cycle chip" decision). Pager
respects the real pinning rule: U0 MIRROR always on page 1, applied (▶)
and advisor-pick (★) rows pinned regardless of sort position.

**N.2 — Roster health indicator (new).** A small corner count —
`{n} active · {m} meta · {k} corrupt` — surfacing the CTRL §4.1 corrupt-
file state (`!` marker, greyed row, tooltip fix suggestion) directly on
VIRT UNIV too, not only in CTRL, since a corrupt roster file changes what
a person sees in the table they're looking at right now.

**N.3 — Meta-switcher visual distinction, restated precisely.** Meta rows
(`M_EQUITY`/`M_WINRATE`/`M_LASTTRADE`) render in `CFG_CLR_META` (violet),
carry no `#hash4` (they have no DSL definition of their own — they hold a
base universe's), and their row-click behavior differs: double-click does
**not** bind SCOPE to a meta the way it does for a base universe, because
SCOPE's criteria panel (§4) has nothing to parse for a meta — it shows a
one-line explainer instead: *"M_EQUITY currently holds {base universe} —
see that universe's own SCOPE for entry/exit criteria."*

**N.4 — Legend, unabridged.** The existing spec's legend row
(`★/▶/M_/dbl-click`) expands slightly to include the new N.2 corrupt
marker (`!`) so every symbol on the tab is defined in one place a person
can actually find, rather than split between VIRT UNIV and CTRL.

### O. What this amendment still does not add

A live equity curve on LIVE itself (still SCOPE's sparkline only, per D11)
· editable risk-cap input on LIVE (remains CTRL-only, per the existing
tab/behavior-change separation, D8) · a VIRT UNIV search/filter box (roster
sizes to date, up to 59 files, have not yet made one necessary — parked
until they do).

