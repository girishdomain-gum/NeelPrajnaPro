# NeelPrajna Dashboard Specification v1.2 — FROZEN
Status: frozen for Phase 4 implementation (owner-approved mockups, 2026-07-21).
v1.2 amendment — tab-driven chart visual mapping (§7 + §0/§5 deltas), owner-approved 2026-07-22.
Governed by ADR-001 + ADR-002. Changes require a spec amendment committed to the repo;
implementation discoveries (font/object constraints) come back as amendments, never ad-hoc.

Panel: 344px wide, Dark HUD palette (Config/ChartTheme), monospace UI font, write-on-change,
lazy tab build + OBJPROP_TIMEFRAMES show/hide, all data from StateHub, all actions via CMD_*.

---

## 0. Tab bar (always visible)
`LIVE | VIRT UNIV | SCOPE ·{name|—} | CTRL` — active tab: accent underline + tinted bg.
(Owner naming, 2026-07-21. If `VIRT UNIV` proves too wide at implementation, the approved
fallback is `V-UNIV` — an amendment note, not a redesign.) Legacy names in sections below
map: REAL→LIVE, UNIVERSE→VIRT UNIV, DETAIL→SCOPE, CONFIG→CTRL.
Hidden tabs (per CTRL) are removed from the bar (LIVE cannot be hidden). SCOPE shows the
bound strategy name or `·—` (greyed, non-clickable when unbound). Tab click → CMD_SELECT_TAB.
State: ui.activeTab, ui.tabVisible[], ui.detailBinding (persisted, ADR-002 D5).

RENDERING RULE — active tab only: hidden/inactive tabs receive zero object writes per tick.
On activation a tab performs one full refresh from the current StateHub snapshot, then
resumes write-on-change. StateHub always updates every tick regardless of the active tab
(data is always current; only painting is deferred), so switches are instant and never
stale. Two elements update regardless of active tab: the tab bar itself (SCOPE binding
name) and the status line (command results, manual-fire refusals, blocker changes).

v1.2 note (2026-07-22): tab selection is UI-local view state; CMD_SELECT_TAB in the original
§0 text is superseded (D8 — commands are for behavior-changing controls). visualSource changes
flow from ui state per §7.

## 1. REAL tab (default)
1.1 Strategy header bar: `STRATEGY {name}` (accent) + AUTO chip (ON teal-tinted / OFF grey).
    Data: portfolio.active.name; exec.autoOn.
1.2 Vitals grid, 2 rows × 3 cells (label 10px dim / value 13px):
    EQUITY acct.equity · DAY P&L acct.dayPnl + pct (green/red) · MARGIN LVL acct.marginLevel
    OPEN RISK pos[].sumRiskR + pctEquity (amber = attention) · DD FROM PEAK acct.ddFromPeak
    · SPREAD exec.spreadPts + $ (red while blocker==SPREAD).
1.3 Pipeline readout, 2 lines (read-only, D1):
    `BUY ▲ | {first pulsing trigger} | {blocker|OK → FIRE}` and same for SELL.
    Data: pipe[BUY], pipe[SELL] (bias dir, trigger name, exec.blocker mapping).
1.4 OPEN section: one row per position: dir+lots, entry, sl, live R (colored), [BE] [½]
    micro-buttons → CMD_POS_BE(ticket), CMD_POS_PARTIAL(ticket). Data: pos[].
1.5 RECENT — LAST 6 CLOSED table: TIME | DIR | GATE | STRATEGY | R.
    Strategy column shows the attributed strategy name (D3/D4); manual-confirmed trades
    show a `·m` suffix; external/terminal trades show `EXT` and are excluded from stats.
    Data: history.recent[6] (per-gate magic + portfolio attribution, 60s cache).
1.6 Action row: BUY SELL (directional tint) CLOSE 2%✓ — BUY/SELL → CMD_MANUAL_BUY/SELL
    (strategy-confirmed, D2; refusal shown in status line + log), CLOSE → CMD_CLOSE_SYMBOL,
    2%✓ shows armed state (control lives in CONFIG). No NUKE here (D8/D9).
1.7 Optional session strip (toggle in CONFIG): ASIA/LDN/NY active dots + UTC clock.
    Data: clock.sessions[], clock.utc.

## 2. UNIVERSE tab
2.1 Header row: `ROSTER {id} · {n}+{m} META` · SORT dropdown (NET R default; TRD/WIN%/PF/
    MAXDD) persisted · pager `[p/N]` (applied ▶, advisor ★, U0 pinned page 1 — v3.12.1 rule).
2.2 Table columns: # | STRATEGY | TRD | NET R | WIN% | PF | MAXDD.
    Strategy cell: `{name} #{hash4}` (hash dim, D4); metas purple, no hash. ★ advisor pick,
    ▶ applied-on-real. NET R green/red; MAXDD red. Data: universes[] (rank per sort).
2.3 Interaction: single click = select/highlight only; double click = bind DETAIL
    (ui.detailBinding = uid) and activate it. No apply action on this tab (D8).
2.4 Legend row (★/▶/M_/dbl-click) + ADVISOR status line (eligibility · hysteresis ·
    recommendation). Data: advisor.status.
2.5 ✕ on tab header hides the tab (ui.tabVisible).

## 3. DETAIL tab (single inspector)
3.1 Header bar: `{name} #{hash}` + ★ if advisor pick + definition line
    `bias {mask} · trig {mask} · RR {x} · trail {on/off}`. Data: universes[uid].def.
3.2 Vitals grid (R-denominated, mirrors REAL's geometry): NET R · WIN%·TRD · PF ·
    EXPECTANCY (avg R) · MAX DD (red) · SKIPPED {n} sig (amber; VirtualBook policy counter).
3.3 EQUITY (R) sparkline over the trade sequence — single polyline, the only chart on the
    panel (D11). Data: universes[uid].equityPath (decimated to ≤64 points).
3.4 VIRTUAL OPEN row (max 1 by policy, labeled): dir, entry, sl, tp, live R.
3.5 RECENT VIRTUAL — LAST 6: TIME | DIR | EXIT(TP/SL/TRAIL/BE) | MFE/MAE (R) | R.
3.6 Footer: advisor status for this uid · `apply via CONFIG →` (read-only tab, D8).
3.7 ✕ unbinds (ui.detailBinding = none) and greys the tab to `DETAIL ·—`.

## 4. CONFIG tab
4.1 STRATEGY — REAL ACCOUNT: roster list rows `{▶|○} {name} #{hash} … {netR}` (evidence
    beside the decision), click selects; APPLY button always names its target
    (`APPLY T1_B6 #a3f9`) → CMD_APPLY_STRATEGY(uid); RESTORE INPUTS →
    CMD_RESTORE_DEFAULTS. Radio behavior enforced by Portfolio (ADR-001 §2.6).
    Corrupt roster files (D4 nomenclature check) are listed greyed with `!` and the fix
    suggestion in tooltip/log; they cannot be selected.
4.2 EXECUTION switches → commands: AUTO (CMD_SET_AUTO) · MANUAL FIRE (CMD_SET_MANUAL) ·
    2% RULE ARMED (CMD_TWOPC_ARM) · NPSU SHADOW ENGINE (CMD_SET_NPSU) · ADVISOR LINE
    (CMD_SET_ADVISOR).
4.3 2% threshold stepper − {x.x%} + → CMD_SET_TWOPC_PCT (bounds from input; persisted).
4.4 PANEL switches: UNIVERSE TAB · DETAIL TAB · SESSION STRIP ON REAL → ui.tabVisible /
    ui.sessionStrip (persisted).
4.5 DANGER ZONE: NUKE two-step (arm → CONFIRM/CANCEL); confirm → CMD_NUKE = close all EA
    positions + AUTO OFF (D9); post-fire label shows `NUKED — FLAT · AUTO OFF`.
4.5b EXIT EA (danger zone, beside NUKE): two-step; calls ExpertRemove() — detaches the EA
    and touches NO positions. If positions are open, the confirm step states it explicitly:
    `CONFIRM EXIT — {n} POSITION(S) LEFT UNMANAGED` with hint `NUKE first for flat`.
    Separation of concerns: NUKE = flat + auto off, stay attached; EXIT = detach, touch
    nothing (ADR-002 D12).
4.6 Persistence footer: `persisted · restart re-applies {name} #{hash} · logged loud` (D5).

## 5. Cross-cutting behavior
- Status line (bottom of active tab when a transient message exists): command results,
  manual-fire refusals with reason, apply confirmations. Auto-clears after n seconds.
- Blocker display: exec.blocker (closed enum, D6) drives SPREAD cell color, pipeline third
  segment, and status line text.
- Colors: teal=long/positive, crimson=short/negative, amber=attention, dim slate=inactive —
  from the existing ChartTheme palette; ASCII-safe glyphs only (▲▼●○★▶✕ verified in
  terminal fonts during Phase 4; any failure → spec amendment, v2.8.1 lesson).
- Object naming: `NPUI_{tab}_{widget}_{n}`; full delete on Deinit; object budget target
  ≤300 live objects (lazy build + shared cells).
- Every element above maps to a StateHub field or CMD_*; anything not derivable from
  EAState is a Phase 2/3 gap to fix in state, never a UI-side workaround.

## 6. Out of scope (analyzer's job, D11)
Per-strategy equity charts beyond the sparkline, hourly heatmaps, multi-strategy
comparisons, verification reports — np_dashboard.py / np_universe_analyzer.py.

---

## v1.2 Amendment — tab-driven chart visual mapping
Owner-approved 2026-07-22. Additive to v1.1 (§0–§6 unchanged). Adds §7 plus one §0 and one
§5 delta. Recorded as an appended provenance block per the repo's amendment convention.

### §0 delta — ui.visualSource
ui state gains `visualSource` — the strategy whose gate visuals are drawn on the chart:
REAL or a universe uid. D5-persisted. Written by the tab logic per §7; read by gate drawing.

### §5 delta — visual-source badge (always-on)
New always-on element: the **visual-source badge** — whenever visualSource ≠ REAL, an
unmistakable on-chart label "VISUALS: {name} #{hash4} (virtual)" is displayed (chart corner,
theme accent). Rationale: virtual zones must never be misread as live trade levels. The badge
is exempt from the active-tab-only rendering rule (like the tab bar and status line).

## 7. Tab-driven chart visual mapping
7.1 Mapping. The active tab determines visualSource:
   - LIVE → REAL (the applied strategy's gates).
   - SCOPE → the bound strategy (ui.detailBinding).
   - VIRT UNIV → the selected row's strategy; if none selected, resolve a sticky default ONCE
     at tab activation: selection > advisor pick > rank-1 at that moment. The resolved source
     holds until the selection changes or the tab is re-activated (no flapping with rankings).
   - CTRL → the last-active source (the visualSource in effect before switching to CTRL);
     persisted per D5.
7.2 Mechanism. Gate drawing paths consult ui.visualSource (a strategy's gate mask + params)
   instead of assuming the live config. Redraw occurs ONLY on visualSource change, not per
   tick or per tab flip where the source is unchanged; per-source object prefixes allow bulk
   hide/show analogous to tab objects. Object budget: visuals for exactly one source exist at
   a time.
7.3 Scope & sessions. The gate-side work (drawing paths reading visualSource) is engine-
   adjacent (touches Gates/, not only UI/) and constitutes its own Phase 4 session (P4-V),
   scheduled after the four tab sessions, with its own tester tripwire run (drawing must be
   deal-list-neutral by construction; the run proves it).
7.4 Precedent & constraints. B6's compute-all/vote-enabled-only drawing is the model for
   drawing a mask not currently traded. Non-drawing gates simply have no visuals to map.
   The badge (§5 delta) is mandatory whenever visualSource ≠ REAL.

§7.4 note (2026-07-22, P4-V amendment). visualSource controls the VISIBILITY of the LIVE
   computation's visuals, filtered per the source's gate mask — it is NOT a re-render of what
   that strategy would have drawn with its own gate params. A universe strategy differs from the
   applied config only by its enable mask (bias_mask/trig_mask); it carries no per-gate params.
   So under a virtual source the chart shows the live-param version of each masked gate's visuals.
   Parameter-level virtual re-rendering (drawing a strategy's gates as they would compute under
   its own params) is Tier-3, out of scope — ADR-003-era work if ever. The badge already warns
   the visuals are virtual; this note ensures nobody later reads them as a virtual strategy's own
   computed levels. Gates whose visuals cannot be honestly filtered from the live computation
   (transient per-bar marks needing detection replay; lifecycle-entangled recompute) render
   NOTHING under a virtual source — see the P4-V coverage table in
   docs/plans/phase4_session_plan.md.
