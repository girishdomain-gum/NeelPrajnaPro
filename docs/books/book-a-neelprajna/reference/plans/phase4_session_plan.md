# Phase 4 — Dashboard Rebuild: Session Plan (P4-0)
Status: **DRAFT — held for owner review.** Plan-only session; the only code produced is the
`UI/Layout.mqh` draft (compile-harnessed, 0 errors). Nothing is wired into `NeelPrajna.mq5`.

Governing document: `docs/plans/dashboard_spec.md` **v1.2 (FROZEN)** — the authority for
everything visual. ADRs: ADR-001 (StateHub/EventBus/Portfolio), ADR-002 (D1–D12 interaction
model), ADR-003 (Phase-6 sequence engine — informs §7 only, no Phase-4 dependency).

This document becomes the per-session briefing source for the whole phase (Phase-3
`phase3_gate_recipe.md` pattern): each session below is one branch/one session, opened against
its "Exit check" row.

---

## 1. Deliverable — `UI/Layout.mqh` (the vertical-flow engine) — DRAFTED
Committed on this branch, compiled clean via a throwaway harness (deleted; not committed).
It is the engine only — it knows nothing of StateHub fields or CMD_*; widgets compose it.

What it provides, mapped to the spec:
- **Object namespace** `NPUI_{tab}_{widget}_{n}` (spec §5) via `LAY_Name`; one prefix (`NPUI_`)
  is the single point of truth for teardown and per-tab show/hide.
- **≤300 live-object budget** (spec §5): every create routes through `LAY_Ensure`, which
  refuses past the cap with one loud warning rather than silently overflowing; `LAY_Recount`
  resyncs the counter defensively.
- **Write-on-change** (spec §5): `LAY_SetText/SetColor/SetBg` read-compare-write with no
  external cache — also the documented fix for the legacy panel's swallowed clicks
  (`BD_CheckboxSync`).
- **Vertical flow**: `LAY_Begin/LAY_Row` own the running Y so no widget computes absolute Y;
  adding/removing a section reflows everything below it.
- **Row / Chip / Cell primitives** (spec §5): `LAY_Chip` (pill: rect + centered label — AUTO
  chip, status, badge), `LAY_Cell` (labelled value box — the §1.2 vitals-grid unit), both
  built on the `LAY_Rect`/`LAY_Text` marks.
- **Tab show/hide** (spec §0): `LAY_SetTabVisible` bulk-toggles a tab's objects via
  `OBJPROP_TIMEFRAMES` (the legacy `OBJ_NO_PERIODS` trick) — the mechanism the tab layer uses.
- **Prefix-scoped teardown**: `LAY_DeleteAll` sweeps only `NPUI_`, never the legacy `DVBDASH_`
  panel — essential to the coexistence window (§5 below).

Open discovery flagged in-file: the monospace face. Spec header mandates a monospace UI font;
the legacy panel uses Arial. The draft uses `"Consolas"` (bold via `" Bold"` suffix, matching
the house `"Arial Bold"` idiom). **Glyph set must be verified on the live terminal** (spec §5
ASCII-safe list `▲▼●○★▶✕`); a miss → spec amendment, fallback face `"Courier New"`.

---

## 2. Deliverable — Widget file map (`UI/Widgets/`) → spec sections
Each widget is a small module composing `Layout.mqh` primitives and binding one StateHub
region / CMD_* set. Split by tab so a session owns one file plus the always-live chrome it
depends on. Proposed layout:

| File | Spec | Content | Reads (StateHub) | Posts (CMD_*) |
|---|---|---|---|---|
| `UI/Panel.mqh` | §0 | Panel shell: owns Layout lifecycle, tab state machine, dispatch of OnChartEvent; hosts the always-live chrome | `ui.*` | `CMD_SET_TAB_VISIBLE` |
| `UI/Widgets/TabBar.mqh` | §0 | **Always-live** tab bar `LIVE\|VIRT UNIV\|SCOPE·{name}\|CTRL`; SCOPE binding name; active-tab accent | `ui.activeTab/tabVisible/detailBinding`, `portfolio` | tab switch (see §8 gap) |
| `UI/Widgets/StatusLine.mqh` | §5 | **Always-live** transient status/toast (command results, manual-fire refusals, blocker changes) | `ui.statusText/statusExpiry`, `exec.blocker` | — |
| `UI/Widgets/VisualBadge.mqh` | §5 delta / §7 | **Always-live** visual-source badge — `VISUALS: {name} #{hash4} (virtual)` whenever `visualSource ≠ REAL`; exempt from active-tab-only rule | `ui.visualSource`, `universes[]` | — |
| `UI/Widgets/LiveTab.mqh` | §1 | Strategy header, vitals grid, pipeline readout, open positions (+BE/½), recent table, action row, optional session strip | `account`, `exec`, `positions[]`, `recent[]`, `buy/sell`, `clock` | `CMD_MANUAL_BUY/SELL`, `CMD_CLOSE_POSITION`, `CMD_POSITION_BE/HALF` |
| `UI/Widgets/UnivTab.mqh` | §2 | Roster table, sort, pager, legend, advisor status line; single-click select / double-click bind SCOPE | `universes[]`, `advisor` | `CMD_SET_TAB_VISIBLE` |
| `UI/Widgets/ScopeTab.mqh` | §3 | Inspector: def line, R-vitals grid, R-equity sparkline (the one permitted chart, §3.3/D11), virtual-open row, recent-virtual, footer | `universes[detailBinding]` | — |
| `UI/Widgets/CtrlTab.mqh` | §4 | Strategy roster+APPLY/RESTORE, execution switches, 2% stepper, panel toggles, danger zone NUKE+EXIT | `portfolio`, `exec`, `ui` | full CONFIG set (D8/D9/D12) |

Always-live elements (TabBar, StatusLine, VisualBadge) are painted every tick regardless of
active tab, per spec §0/§5; all tab widgets obey the active-tab-only rule.

---

## 3. Deliverable — Tab mechanism (spec §0 rendering rule)
Owned by `UI/Panel.mqh`. Rules implemented:
- **Lazy build on first activation.** A tab's objects are created the first time it becomes
  active (its widget's `Build()` runs once), then never rebuilt — only shown/hidden.
- **Show/hide, not rebuild.** Switching tabs = `LAY_SetTabVisible(old,false)` +
  `LAY_SetTabVisible(new,true)` (OBJPROP_TIMEFRAMES). On activation, one full refresh from the
  current StateHub snapshot, then write-on-change resumes. Switches are instant and never stale
  because StateHub updates every tick regardless of active tab (spec §0).
- **Always-live exceptions.** TabBar, StatusLine, and VisualBadge are never hidden; they update
  every tick. Hidden tabs (per CTRL, `ui.tabVisible[]`) are removed from the bar; LIVE cannot
  be hidden; SCOPE greys to `·—` when unbound.
- **`ui.visualSource` persistence (§0-delta / §7).** The tab logic writes `ui.visualSource`
  (LIVE→REAL, SCOPE→bound uid, VIRT UNIV→sticky-resolved once on activation, CTRL→last-active).
  It is D5-persisted alongside `activeTab/tabVisible/detailBinding/sortKey`. **This requires a
  new field `visualSource` on `SUiState`** (StateHub Section 4) — see §6/§8. Gate drawing reads
  it (P4-V); redraw only on change (§7.2).

---

## 4. Deliverable — Build order & exit checks
One session = one branch = one session-doc briefing. UI-only sessions exit on **compile +
owner on-chart review against the frozen mockups**; the phase carries a **single owner-run
tester tripwire at phase end**, plus two extra owner-run tripwires where execution semantics or
gate code are touched (S15b, P4-V). Per project memory, the tester is **owner-run** — automation
compiles only, never launches the tester (live-money single instance).

| # | Session | Scope | Depends on | Exit check |
|---|---|---|---|---|
| P4-0 | Governance + plan | ADR-003 + spec v1.2 on main; this plan; `Layout.mqh` draft | — | compile (harness, done) + **owner review of this plan** |
| P4-1 | Chrome + coexistence scaffold | `Panel.mqh`; input flag; TabBar + StatusLine + VisualBadge (always-live); tab state machine (lazy build + show/hide); `SUiState.visualSource` field + persistence | P4-0 | compile + owner on-chart: panel appears behind flag, tabs switch, chrome always-live, legacy untouched with flag off |
| P4-2 | LIVE tab (§1) — **DONE** (owner-accepted on-chart 2026-07-22) | `LiveTab.mqh` **+ the LIVE-tab StateHub state-fill** (dayPnl, ddFromPeak, openRiskR/Pct, position snaps, recent attribution — §6). BUY/SELL stubbed to refusal (→ D2 session); §1.4 "½" ships ASCII "1/2" (permanent fallback, owner-accepted); EXT rows read-only (ADR-002 D12) | P4-1 | compile + owner on-chart vs §1 mockup. State-fill is publish-only → deal-list-neutral |
| P4-3 | CTRL tab (§4) | `CtrlTab.mqh`; full control surface incl NUKE/EXIT. AUTO/2%-arm/2%-threshold/APPLY/RESTORE wired; MANUAL FIRE switch is state-only (D2 session consumes it); NPSU/ADVISOR are read-only reflections (their `Inp*` gates are not runtime-mutable — refactor to runtime globals is out of scope, see tech-debt) | P4-1 | compile + owner on-chart vs §4 mockup |
| D2 | Manual-fire confirmation (engine-adjacent) | strategy-confirmation logic in the pipeline (a manual BUY/SELL fires only with an aligned bias+trigger, else refuses per D2), refusal messaging + `EVT_MANUAL_REFUSED`, the real order path (SL/TP/magic/consume/log). Consumes the P4-2 stub + P4-3 MANUAL FIRE state | P4-3 | compile + **owner-run tester tripwire** (opens real orders; must be deal-list-neutral by the click-only construction — the run proves it) |
| S15b | Research publishing + consumption switch (Phase-3 carryover, **prerequisite**) | roster absorption; `SUniverseRow` stats + `SAdvisorStatus` publishing; UniverseEngine/Advisor/MetaSwitcher read Portfolio+StateHub not raw EG_ pulses (semantics preserved) | P4-1 | compile + **owner-run tester: execution-identical required** (touches observer read paths) |
| P4-4 | VIRT UNIV tab (§2) | `UnivTab.mqh`; needs live roster stats | P4-3, **S15b** | compile + owner on-chart vs §2 mockup |
| P4-5 | SCOPE tab (§3) | `ScopeTab.mqh`; sparkline needs `equityPath` | P4-4, **S15b** | compile + owner on-chart vs §3 mockup |
| P4-V | Gate-side visual mapping (§7) | drawing paths read `ui.visualSource`; per-source object prefixes; badge enforcement; B6 compute-all/vote-enabled precedent (§7.4). Touches `Gates/`, engine-adjacent | P4-1…P4-5 | compile + **owner-run tester tripwire** (drawing must be deal-list-neutral by construction; the run proves it) — spec §7.3 |
| P4-6 | Cutover / legacy retirement | flip default to new panel; retire `DVBDASH_` `Dashboard.mqh` (or defer to Phase 5 per tech-debt) | all above | compile + owner on-chart + **owner-run phase-end tester** (deal-list-neutral) |

Ordering rationale: chrome first (everything hangs off it); LIVE next (default tab, self-fillable
state); CTRL early (self-contained, unlocks APPLY used to exercise other tabs, no research data);
**S15b gates VIRT UNIV + SCOPE** exactly as required; P4-V after all four tab sessions per §7.3.
**D2 (manual-fire) is scheduled after P4-3** (owner ruling 2026-07-22): it is engine-adjacent
(real order path + pipeline confirmation), so it gets its own tester-gated slot rather than
riding a UI session; until it lands, the P4-2 BUY/SELL buttons refuse honestly.

**D2 landed v4.4.0.** `EG_TryManualEntry` reuses the auto pipeline's readiness — bias-aligned
+ first enabled trigger pulsing (same `g_egTrigWalk` order) + the same blocker predicates — then
fires a manual trade (magic base+0, manual-confirmed comment, confirming trigger's levels) through
TM. **Pulse consumption** (owner ruling 2026-07-22): a confirmed manual fire consumes the
confirming trigger's pulse via the same `markConsumed()` as auto — manual == auto on the setup
lifecycle (one signal, one trade; a re-validated setup pulses again and can be fired again).
Auto path (`EG_OnTick`) left byte-identical; click-only, dead in the tester.

---

## 5. Deliverable — Coexistence strategy (recommendation)
**Recommend: parallel new panel behind an input flag** (agrees with owner predisposition).

Mechanism: a new input (e.g. `InpUseNewPanel`, default **false** until the phase is complete and
owner-approved). `OnInit/OnTick/OnTimer/OnChartEvent/OnDeinit` branch on it — legacy `BD_*`
(`DVBDASH_`) path when false, new `Panel_*` (`NPUI_`) path when true. The two namespaces never
collide and never draw at once.

Why parallel-behind-flag wins here:
- **Live trading never depends on a half-built UI.** Default stays on the proven legacy panel
  through the entire rebuild; the new panel is opt-in until it's whole.
- **Every session is independently abandonable.** The new panel is purely additive
  (`Layout.mqh` + `Panel.mqh` + `Widgets/*` + one flag + a dispatch branch). Delete them and the
  flag → the EA is byte-for-byte the pre-Phase-4 panel. No half-migrated intermediate state.
- **The panel is already fully optional** (tester/headless never touch it), so gating is a
  one-line branch in each of the ~4 lifecycle hooks — cheap to add, cheap to remove at cutover.
- **Clean-room geometry.** The legacy panel is a 3,431-line lattice of interdependent absolute
  offsets (`BD_Y_*`, `BD_TF_*`). The new vertical-flow engine owns its own coordinates; not
  editing legacy geometry avoids a whole class of reflow regressions.

Incremental in-place replacement — **rejected**: it would mutate the live legacy panel section by
section, so any mid-phase session could leave the *only* panel broken during live trading;
sessions become non-abandonable (no clean revert point); and every session fights the legacy
geometry constants. The one saving (no temporary flag) is trivial next to those costs. Cutover
(P4-6) removes the flag and the legacy module in a single reviewed step.

---

## 6. Deliverable — Spec §5 StateHub `[P3]`-stub inventory
Fields the spec's elements bind that are declared but **not yet populated** (zero until filled),
with the session that must fill them. Publishing to StateHub is a read-only shadow write — it is
**execution/deal-list-neutral**, so these fills carry no tester risk on their own.

**LIVE tab (§1) — fill in P4-2 (state-fill sub-step):**
- `account.dayPnl`, `account.ddFromPeak` — §1.2 vitals.
- `exec.openRiskR`, `exec.openRiskPct` — §1.2 OPEN RISK cell.
- `positions[].riskR`, `.snapRR`, `.snapTrailOn`, `.snapBeOn` — §1.4 open rows / live R (per-
  position entry snapshot; `StateHubPublish` notes "true snapshot arrives with lifecycle work").
- `recent[].stratName`, `.stratHash`, and true per-trade R — §1.5 attribution column (D3/D4).

**VIRT UNIV (§2) + SCOPE (§3) — fill in S15b (the named prerequisite):**
- Entire `SUniverseRow` stats: `trades, netR, winPct, pf, maxDD, expectancy, skippedSignals,
  equityPath[]/equityLen, vHasOpen/vOpenIsBuy/vFloatingR` (`universeCount==0` today; S15 shipped
  only the name/hash/count skeleton).
- Entire `SAdvisorStatus`: `enabled, warmedUp, statusText, adoptedName, adoptedHash` — §2.4/§3.6.

**Optional / cross-cutting:**
- `SSessionClock` (`asiaOpen/londonOpen/nyOpen/activeLabel`) — §1.7 optional session strip
  (fill with P4-2 only if the strip is enabled; otherwise defer).
- **New field required:** `SUiState.visualSource` (§0-delta) — does not exist yet; add in P4-1.

So: the LIVE-tab account/position/recent `[P3]` fills are a **distinct prerequisite from S15b**
(lifecycle-publishing vs research-publishing) and land inside the LIVE session; S15b remains the
gate specifically for the research tabs, exactly as scoped.

---

## 7. Not in scope / holds
- No code beyond `Layout.mqh` this session. `Panel.mqh` and `Widgets/*` are named, not written.
- No changes to `NeelPrajna.mq5` (no include, no flag) until P4-1 is opened and approved.
- Analyzer-side visuals (per-strategy curves, heatmaps, verification) stay Python (§6/D11).
- This branch (`phase4-dashboard`) is **not pushed** — held for owner review.

---

## 8. Open design questions for owner (surfaced during P4-0)
1. **Tab-switch command gap.** Spec §0 says "Tab click → CMD_SELECT_TAB", but `EventBus.mqh`
   has **no such command** — only `CMD_SET_TAB_VISIBLE` (show/hide). Active-tab is pure view
   state (`ui.activeTab`, D5-persisted) and changes no engine behavior. **Recommend**: switch
   `ui.activeTab` UI-locally in `OnChartEvent` (no bus command), same for `ui.visualSource`
   (§7) — the bus is for engine-affecting commands, and a logged tab switch adds noise for no
   consumer. Alternative: add `CMD_SELECT_TAB` for uniform logging. Owner's call.
2. **Monospace face** — confirm `"Consolas"` acceptable, or pin `"Courier New"` (glyph-verify
   against the §5 ASCII-safe list on the live terminal at P4-1 review).
3. **`SUiState.visualSource` type** — `int` reusing the uid convention (`REAL` = a reserved
   sentinel, e.g. `-1`, matching `detailBinding == -1` for "none")? Proposed; confirm at P4-1.
4. **Legacy retirement timing** — retire `Dashboard.mqh` at P4-6, or leave it for the Phase-5
   legacy-removal sweep (tech-debt already lists Full-D1 / legacy cleanup under Phase 4/5)?

---

## 9. P4-V — Gate visual coverage table (spec §7) — v4.6.0-pre
Owner-approved 2026-07-22 as **Tier-1+2 (visibility-mask)**; Tier-3 (parameter-level virtual
re-rendering) confirmed out of scope.

**Honest semantic (owner-facing record).** Under a virtual source the chart shows the LIVE
computation's visuals, filtered to the virtual strategy's enabled-gate mask — NOT a re-simulation
of what that strategy would have drawn with its own params. A universe strategy differs from the
applied config only by its enable mask (`bias_mask`/`trig_mask`); it carries no per-gate params
(`StrategyPortfolio.Portfolio_ApplyStrategy` sets each gate's enable from a mask bit and nothing
else). So where a virtual strategy's gate params would differ from live's, its visuals are the
**live-param version**. The visual-source badge already warns the visuals are virtual; this table
+ the spec §7.4 note are the durable record that these are live-computed visuals filtered by mask,
not a virtual strategy's own computed levels.

**Why this is possible without recompute.** Every gate's `Evaluate` runs whenever
`EG_Bx_Enabled || EG_Bx_Compute`, and `EG_Bx_Compute` is the union of every active universe's mask
(`NPSU_ComputeMaskFromRoster` → `EG_SetComputeMask`). A selectable virtual source is an active
universe, so each gate in its mask is already computing its geometry every tick — the only thing
withholding the visuals today is the draw guard keying on `EG_Bx_Enabled`. P4-V swaps that guard,
it does not add computation ("visuals follow existing computation, never create it").

**IN vs OUT criterion.** IN = the gate draws a **current-picture** set from retained geometry that
is refreshed every tick under compute (guard-swap repaints a complete, correct picture). OUT = the
gate's visuals are an **accumulation of transient per-bar marks** (arrows/boxes stamped at signal
bars, no retained full set) or are **lifecycle-entangled** — backfilling them would require replaying
detection = the forbidden parallel pipeline. OUT gates render NOTHING under a virtual source.

| Gate | Prefix (code) | Draws | Geometry | Verdict |
|---|---|---|---|---|
| B1 Nexis | `NXS_` | Fast/Converging MA polylines | Retained `_b1_fma/_cma`; full delete+rebuild redraw | **IN** |
| B2 MTFCandle | `MTFC_G3_` | Mapped-HTF candles | Stateless — rebuilt from HTF price in `MTFCM_Draw` | **IN** |
| B6 RegChannel | `B6RC_` | Regression channels | Retained `_b6_ch[]`; compute-all (§7.4 **model**) | **IN** |
| T2 AutoFibo | `AFG5_` | Fibo legs + fills (+ POC) | Legs retained; POC-line coords computed in draw path | **IN** (POC minor) |
| T3 Sweep+FVG | `G8SW_` | Anchor/pool lines, FVG+OB zones | Retained state machine (`T3_UpdateChart`) | **IN** |
| T4 TrendLines | `G9TL_` | Trendlines + touch labels; event/fail arrows | Line structs retained; **arrows transient** | **IN (partial)** — lines in, arrows out |
| T5 Topography | `G10_` | Confluence HLINEs + labels | Retained `t5_levels[]` | **IN** |
| B3 KeyLevel | `KLG4_` | Zones + fired-plan boxes/arrows | Zones retained but ATR+spread lifecycle-entangled (tech-debt phase3-b3); plan marks event-history | **OUT** |
| B4 SMC | `SMC6_` | CHoCH/BOS segments; FVG/OB zones | Segments drawn inline & discarded (no retained set) | **OUT** |
| T1 Pattern | `PG3_` | Pattern boxes | Transient per-detection | **OUT** |
| T7 MktMetrics | `T7SMM_` | Signal arrows | Transient per-latch-bar | **OUT** |
| T8 CMH | `T8CMH_` | Signal arrows | Transient (only newest in statics) | **OUT** |
| T9 CCC | `T9CCC_` | Signal arrows | Transient per-latch-bar | **OUT** |

**IN (7):** B1, B2, B6, T2, T3, T4(lines), T5. **OUT (6):** B3, B4, T1, T7, T8, T9.
For T4, the event/failure arrows are treated as OUT sub-visuals (kept off under a virtual source);
its trendlines + touch labels are the IN current-picture set.

**Mechanism (spec §7.2).**
- Shared draw-state in `Gates/GateBase.mqh` (visible to all gates): `g_egVisualSource` (=`UI_VISUAL_REAL`
  anchor, else a uid) + one visibility bool per IN gate.
- Each gate's draw guard swaps `EG_Bx_Enabled` for a predicate: REAL → `EG_Bx_Enabled` (unchanged,
  the anchor); virtual → the IN bool (source mask bit) / `false` for OUT gates.
- `EG_ApplyVisualSource(uid, mask)` in `Engine/EntryGates.mqh` (after the gate includes, mirroring
  `EG_SetComputeMask`): top-guards on unchanged source (steady REAL/virtual = zero work), sets the IN
  bools from `mask = bias_mask|trig_mask`, and reconciles per-gate prefix visibility via
  `OBJPROP_TIMEFRAMES` (`OBJ_ALL_PERIODS`/`OBJ_NO_PERIODS`, the panel-tab pattern). Draw-only latches
  `_b1_lastDrawBarTime`/`MTFCM_LastHTFBarTime` are reset for an instant repaint; **no compute latch is
  touched**. Called from `NeelPrajna.mq5` (top layer, can read `npsu_ros`) when `ui.visualSource` changes.
- **REAL is a provable no-op:** when `g_egVisualSource == UI_VISUAL_REAL` every gate's guard returns
  `EG_Bx_Enabled` and the setter's top guard makes zero visibility calls — the anchor holds by
  construction, not by testing.

**Execution safety.** Only draw guards change; compute paths, the entry decision (bias-agree +
trigger-walk, keyed on `EG_Bx_Enabled`), pulse consumption and TM calls are untouched. Deal-list-neutral
by construction; the P4-V tester tripwire proves it.

**Known minor.** A gate entering the visible set repaints on its next draw cadence (next tick for
per-tick gates B6/T4; next bar for new-bar gates, minus B1/B2 whose draw latch is reset for immediacy).
Acceptable for a research overlay; no live-trade-level misread risk (those are OUT gates → nothing drawn).

**Stale prefix comments fixed in-scope:** `MTFC_G3_` (hdr said `MTFC_T1_`), `KLG4_` (`KLB3_`),
`AFG5_` (`AFT2_`), `PG3_` (`PT1_`) — the P4-V teardown/visibility keys off the code prefixes.
