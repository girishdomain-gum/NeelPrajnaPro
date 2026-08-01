# Changelog

Extracted from the NeelPrajna.mq5 version mega-comment (Phase 0). Newest first.

**Versioning scheme (adopted at v4.3.0, applied retroactively from v4.0.0).**
Semantic, aligned to the overhaul phases — MAJOR = architectural era
(4.x = the Phase 1–3 overhaul world; 5.0.0 when Phase 5 removes the legacy
world), MINOR = a completed Phase-4 session milestone, PATCH = hotfix. The
`4.0.0`–`4.3.0` entries below were reconstructed from `docs/plans/` +
git history to make the log honest from the era's start; entries from v4.4.0
on are written live with their milestone commit (rule: `docs/dev_workflow.md`
§10). Everything at `v3.16.4` and below predates the scheme and is the raw
pre-overhaul history, left verbatim.

## v5.8.0 — Phase 6c: the static law compiles, and the A/B that judges it

Stage 6c, first half. The legacy static law can now be COMPILED into its
1-step sequence form — and every compiled twin races its own source so the
difference is measured rather than assumed.

**New in SeqCodex**
- `SQX_CompileStatic()` — a static universe IS a one-step sequence: bias
  mask → step GUARD, trigger mask → step ADV, `WIN:0`, `INV:NONE`
  (design doc §2.3). The compilation is mechanical and total.
- `SQX_RegisterStaticTwins()` — with `InpSeq_UnifyStatic=true` (default
  false) every active static universe gains a `<name>_1S` twin driven by
  the FSM. The twin inherits the source's RR, trail AND break-even, so the
  ONLY difference between the two books is which evaluator decided the
  entry. `SQX_MAX_SEQ` raised 8 → 32 to hold them.

**Why this is an A/B and not a replacement — ADR-004**
The legacy law is evaluated every tick; a sequence samples at bar close
(D3). A 1-step twin therefore CANNOT reproduce its source deal-for-deal:
it enters at the bar close instead of the tick, and misses pulses that do
not survive to the bar boundary. 6c's original acceptance test ("prove the
deal list unchanged") cannot pass by construction. Owner ruling: proceed on
the design as written, record the constraint, and MEASURE the cost with the
twins before deciding anything about unification. Full reasoning, the
tick-mode escape hatch, and a standing rule for future changes are in
`docs/adr/ADR-004-evaluation-cadence.md`.

**Not in 6c yet**: routing the REAL path through a compiled twin, retiring
`_NPSU_TryEnter`, and the tick-capable FSM split. All three wait on what
the twin books say.

## v5.7.0 — Phase 6b: the sequence reaches the real path (DRY-RUN by default)

Stage 6b. The SAME FSM that races in the shadow books can now open a REAL
order — but it ships disarmed, and disarmed it changes nothing.

**New module**
- `Apps/SeqLive.mqh` — the real-path driver. Keeps its own pulse
  birth/consumed matrices (NPSU may be off, so it cannot borrow theirs),
  advances one FSM step per closed chart bar, and on completion either
  logs or fires. Real orders carry `InpMagicBase+15` (D8), so the existing
  BE/trail/GroupSL management covers them like any other EA position.

**Two-key safety**
- key 1: `InpSeq_Kind="SEQ"` — a sequence must be defined at all.
- key 2: `InpSeq_LiveApply` — DEFAULT false.
- With key 2 off the FSM still runs on the real path and prints
  `SEQL | WOULD FIRE BUY on T1 @ ... — dry-run #n`, places no order and
  touches no gate state. That log is the 6b evidence: real-path entries
  the sequence would have taken, at the real path's cadence, at zero risk.

**Deliberately minimal footprint**
- `EG_OnTick` is untouched. The legacy walk keeps sole ownership of
  `markConsumed()`; SeqLive never consumes a real gate pulse.
- SeqLive refuses to fire when AUTO is off, when the legacy walk already
  fired this tick, or when the direction is disabled — the same refusals
  the legacy law answers to.
- The sequence's step guards ARE its bias law, so `EG_BiasBuy/Sell` is not
  re-applied on top of them (that would be two bias laws stacked).

**Baseline promise**: with `InpSeq_LiveApply=false` (default) the real deal
list stays byte-identical to v5.6.0. Journal gains SEQL lines by design.

**Not in 6b**: 6c unification (legacy static law compiled to 1-step
sequences) still waits on a deal-for-deal A/B; a panel row for sequence
state; sequence trades in the LIVE RECENT table beyond the normal
external/EA attribution.

## v5.6.0 — Phase 6a: Sequential Strategy Engine foundations (SHADOW ONLY)

Stage 6a of the Phase 6 design (docs/plans/phase6_sequential_strategy_engine_design_v1.0.md,
decisions D1–D13 as proposed). Sequences race as SHADOW universes only —
nothing in this build changes what the real account does.

**New modules**
- `Engine/SequenceEngine.mqh` — the ONE pure sequence FSM (SSE). No globals,
  no EG_ reads, no files: the caller hands in a gate snapshot; the FSM walks
  invalidate → expire → guard-wait → advance → complete (D1–D4). Direction
  locks at the step-1 advance; SL/TP come from the FINAL advancer (D7).
- `Apps/SeqCodex.mqh` — the ONE parser/normaliser/FNV-1a-32 hasher for
  sequence definitions (D9, D11, D12): the `InpSeq_*` input block (canonical)
  and `NPSU_Strategies\*.seq` files. Normalised form + hash are byte-matched
  to `tools/seqgen.py` — the same definition gets the same #hash everywhere.

**Engine integration (shadow path)**
- `NPSU_Universe` gains `kind` (0=STATIC, 1=SEQ) + `seqIdx`. SeqCodex claims
  empty file slots at `NPSU_Init`; SEQ gates join the EG compute mask.
- SEQ universes advance one FSM step per CLOSED chart bar (D3); the advancing
  pulse is consumed through the SAME `npsu_consumed` matrix the static path
  uses (D5). Completions open virtual positions through the same open block
  (spread cap, one-position rule, MM SL fallback, VB_Open) with
  `SEQ:<trigger>` audit rows; advances/resets stream as `SEQADV`/`SEQRST`
  audit rows when `InpNPSU_Audit` is on.

**Runtime switches (the v5.5.4 promise paid)**
- `InpNPSU_Enabled`/`InpADV_Enabled` reads refactored to `CFG_NPSU_Enabled`/
  `CFG_ADV_Enabled` runtime globals (seeded from the inputs at OnInit).
  `CMD_SET_NPSU_ENGINE`/`CMD_SET_ADVISOR` now really toggle: CTRL's NPSU
  switch pauses/resumes an initialised engine, ADVISOR toggles live. Honest
  limit: NPSU that was OFF at attach still needs the input + reattach to
  initialise (files/roster/books) — the status line says exactly that.
- CtrlTab: swNpsu/swAdv unlocked (locked=false), caption updated.

**Baseline promise (owner gates)**
- With unchanged inputs and no .seq files, the real deal list must stay
  byte-identical to v5.5.6: CFG defaults mirror the inputs, SEQ code paths
  are dormant without definitions, and everything SEQ is virtual-book only.
- NPSU research CSVs MAY gain rows (SEQ universes, SEQADV/SEQRST audit) —
  intentional, research-only.
- Owner to run: tools\compile.bat (0/0) → baseline backtest → deal-list diff.

**Not in 6a (by design)**: real-path SEQ apply (6b, tester+owner gated),
legacy static law compiled to 1-step sequences (6c, after deal-for-deal A/B),
BE flag in the grammar, FSM replay on reattach (D6 accepted as reset).

## v5.5.6
RECENT RETURNS TO STRATEGY-FIRST — owner ruling on the v5.5.5 review:
LIVE's RECENT — LAST 6 goes back to the v5.5.4 table. UI-only
(baseline: identical).

Columns restored: TIME | dir | STRATEGY (accent, 13-char, ·m marker,
honest fallbacks "inputs"/"external") | GATE (muted, hidden on
externals) | R | sign bar — the row answers "which strategy traded
and how"; the gate stays secondary context.

KEPT from v5.5.5 (correctness, not layout): externals' R shows "—"
with no sign bar and stays excluded from the W/L·ΣR summary — an
external trade has no risk basis, so a money figure there is not an
R-multiple. Everything else in v5.5.5 (object budget 480, pipeline
sizing, Label purge, forced Refront) is unchanged.

## v5.5.5
MOCKUP CONFORMANCE + OBJECT-BUDGET ROOT CAUSE — owner review against
the v5.2 mockup found the live LIVE tab missing its AUTO chip, pipeline
texts, and the whole BUY/SELL/CLOSE/2% action row. UI-only (baseline:
identical).

**ROOT CAUSE — LAY_MAX_OBJECTS breach.** LAY_Ensure silently refuses
creation past the budget (one journal warning). v5.5.3's SCOPE table
(~40 objects) + v5.5.4's CTRL rules pushed the panel past 360, so the
build tail was dropped. Budget 360→480 (census + headroom); the
journal warning remains the tripwire.

**Mockup conformance pass (LIVE):** the v5.3.0 standalone RISK gauge
row is retired (mockup has none — the OPEN RISK vital carries it);
pipeline rows grow to mockup size (22px wells, 10pt, dir column 58);
RECENT returns to the mockup table TIME | dir | GATE | R | bar — the
v5.5.0 STRATEGY column retires (strategy detail lives on SCOPE),
externals show GATE "EXT" and R "—" (they carry NO risk basis: the
review screenshot's "-513.73R" was raw money masquerading as R), and
the W/L·ΣR summary now excludes externals. Session dots live in the
footer by default (ui.sessionStrip starts ON). PANEL_BODY_H 520→532.

**Foreign-object hygiene:** the recurring "Label" OBJ_LABEL is now
purged every Panel_Refront pass (the create-time sweep proved
insufficient — it returns after build); and anchor-less per-tick
movers that evade the overlay signature (v5.5.1 tech-debt) are capped
by a forced rebuild every 15th timer pass (~30s max bleed).

## v5.5.4
CTRL REGROUPED + THREE-STATE SWITCHES — owner request: enable/disable
in EXECUTION, and a layout/visual rework of the groups. UI-only
(baseline: identical).

**tools/deploy.bat (workflow fix, same session).** The owner saw v5.50
in MetaEditor while C:\NeelPrajna\repo was at v5.5.4 — root cause:
MetaEditor's Navigator opens the COPIES inside the terminal data folder
(MQL5\Experts\NeelPrajna-Claude\…), which were stale (v5.2.0/v5.4.0).
New tools\deploy.bat robocopy-mirrors the working repo into both
terminal copies (excluding .git/.claude/logs). Workflow: Claude edits
C:\NeelPrajna\repo → owner runs tools\deploy.bat → F7 in MetaEditor →
reattach.

**What was already true (now made visible):** AUTO, MANUAL FIRE, and
2% RULE are real runtime toggles (bus commands) and always were; the
old OFF styling just made them look disabled. NPSU ENGINE and ADVISOR
are input-locked — their engines read `input` variables MQL5 cannot
reassign at runtime (Phase-6 tech-debt); the dispatcher honestly
refuses with a status-line message.

**Three-state switch grammar.** Live ON = green word + green border;
live OFF = MUTED word + hairline (clearly a working control); LOCKED =
dim LABEL text. A caption row under EXECUTION teaches the unlock path:
"NPSU + ADVISOR follow EA inputs — change via settings (F7) + reattach".

**Regrouped layout, LIVE rule-header grammar.** All group headers move
to LAY_Rule (STRATEGY — REAL ACCOUNT / EXECUTION / RISK / PANEL /
DANGER ZONE, the last keeping its red title + red rule). The 2% RULE
arm switch moves out of EXECUTION into the new RISK group beside the
threshold stepper — arming and sizing risk now live together.

## v5.5.3
SCOPE ADOPTS THE LIVE GRAMMAR — owner ruling: one common visual
standard across tabs, LIVE as the reference. UI-only (baseline:
identical).

The SCOPE tab is restyled section-by-section onto LIVE's patterns:
- **Status chip** beside RESET, mirroring LIVE's AUTO chip: APPLIED
  (accent) > PICK (gold) > WATCH (muted) — the binding's relationship
  to the REAL account at a glance.
- **Rule-line section headers** replace plain labels: EQUITY (R),
  VIRT OPEN, RECENT VIRTUAL all use LAY_Rule with the hairline.
- **VIRT OPEN status lives in its rule title** ("VIRT OPEN — ▲ +0.32R"
  / "— none"), with the entry/SL/TP detail row shown only while a
  virtual position is open — the same title-carries-count pattern as
  LIVE's "OPEN — n".
- **RECENT VIRTUAL becomes a real table**: column-header row (TIME |
  EXIT | MFE/MAE | R), per-cell 8pt rows at LIVE's 15px height, colour
  rules per column, sign bars right-aligned at the LIVE x-offset, and
  LIVE's empty-state wording convention on slot 0.

## v5.5.2
ROSTER LEGIBILITY + LABEL-ORPHAN SWEEP — owner review of the VIRT UNIV
page on a second chart. UI-only (baseline: identical).

**Roster legibility.** Rows move 7pt→8pt with height 14→16 and the
columns re-spaced for the larger face (name lane widened to 118px — the
name/hash collision on long strategy names is gone; hash stays 7pt as a
deliberate small annotation). Visual hierarchy: rows with no trades
recede to LABEL grey so traded rows carry the page; a traded TRD count
reads TEXT.

**"Label" footer orphan (R1, second sighting).** The stray default-text
"Label" seen over the footer is a pre-v5.0 orphan whose name is outside
the swept prefixes — MT5 auto-names loose labels "Label", "Label 1", …
LAY_SweepLegacyPrefixes now also deletes pixel-anchored OBJ_LABEL
objects named "Label*" at panel create. A trader's own chart
annotations are OBJ_TEXT (chart-anchored) and are untouched.

## v5.5.1
OVERLAY FIX + ACTIVE-ONLY GATES — owner review of the v5.5.0 chart:
chart drawings were painting INSIDE the panel, and the gate group should
show active gates only. UI-only (baseline: identical).

**Chart-overlay fix (root cause found).** Gates redraw their chart
objects each closed bar by delete-and-recreate under IDENTICAL names.
The v5.0.1 re-front detector hashed only object NAMES, so the recreated
(newer, on-top) objects never changed the signature and Panel_Refront
never fired — the panel stayed older and the drawings bled through.
`Panel_ForeignSig` now also hashes each foreign object's TYPE and its
bar-quantized time anchor: a per-bar redraw changes the hash once per
bar → one cheap rebuild per bar, no per-tick thrash. Known limitation
(tech-debt): anchor-less per-tick movers (price-only OBJ_HLINE trails)
still evade the signature.

**ACTIVE STRATEGY (renamed from "— GATES").** Owner ruling: the group
shows the strategy's ACTIVE gates only — disabled gates are noise.
Rows gain BIAS / TRIG captions; enabled gates pack left-to-right
(▲ long · ▼ short · "·" idle); a bias-less strategy honestly reads
"none — bias passes".

## v5.5.0
EXIT ✕ + STRATEGY-FIRST LIVE — owner review of the v5.4.0 chart (which
rendered correctly — the bold-glyph fix held) + three requests. UI-only
(baseline: identical).

**EA-exit ✕ (top-right corner).** The tab bar gains an always-live ✕ in
the panel's top-right corner (SCOPE tab trimmed 132→114px to make room).
Two-step, mirroring CTRL §4.5: first click arms it (red "✕?", auto-
disarms after 4s), second click posts CMD_EXIT_CONFIRM — the identical
end-path to CTRL's EXIT EA, so no new removal semantics exist.

**ACTIVE STRATEGY — GATES (new LIVE group).** Between SIGNAL and OPEN:
the applied strategy's composition eyebrow (bias/trig masks · RR ·
trail; "input defaults" honestly named), then two token rows — all 5
bias gates and all 8 trigger gates with their LIVE state (▲ long ·
▼ short · "·" idle · dim = disabled by the strategy). This is the
panel-side mirror of the chart's gate drawings, for row-by-row syncing.
PANEL_BODY_H 456→520.

**RECENT is strategy-first.** Owner ruling: a row answers "which
strategy traded, and how" — STRATEGY becomes the wide accent column
(honest fallbacks: "inputs" for defaults-mode trades, "external" for
terminal-made ones), the gate demotes to a small secondary column and
hides on externals. Sign bars, W/L·ΣR summary, and row rules unchanged.

**Object budget** 340→360 (gate group 16 + exit ✕; refuse-and-warn
guard unchanged).

## v5.4.0
SCOPE RESET + LIVE-CHART FIXES — owner review of the v5.2.0 build on the
live terminal (three screenshots) + rulings: tabs can NEVER close (both
already enforced since v5.3.0), and SCOPE gets a RESET instead. UI-only
(baseline: identical). Written per docs/coding_guidelines.md.

**SCOPE RESET.** Replaces the retired ✕: clears the explicit binding
(auto-bind then reclaims the smart default — applied → advisor pick →
first row), clears the VIRT UNIV selection so the sticky visual source
follows, and forces the equity spark to rebuild. Rebinding stays a
VIRT UNIV double-click.

**Live-chart render fix (screenshot finding).** The v5.2.0 chart showed
the SIGNAL direction heads ("BUY ▲"/"SELL ▼") and the AUTO chip missing
while the identical glyphs render non-bold in RECENT — the "Consolas
Bold"+glyph combination fails on the terminal (guidelines §3, the
v2.8.1 lesson). The heads drop bold, and LiveTab_Update now defensively
re-asserts visibility of the SIGNAL statics, the identity header, and
the AUTO chip every refresh (write-on-change — zero per-tick cost).

**Version-block sync.** `EA_VER_MAJOR/MINOR/PATCH` and
`EA_BUILD_SESSION/BRANCH` had been left at their v5.0.0/v5.1.1 values
through the v5.2–v5.4 bumps — a discipline miss against Config.mqh's own
rule ("change ALL of"). Now 5/4/0 with fresh build markers; caught while
syncing the owner's working directory.

**Sortable columns.** VIRT UNIV numeric column headers are clickable —
one click sorts by that column (page resets); the active column's
header brightens to TEXT. The SORT chip stays as the cycle/status
control.

**Polish.** "advisor off" reads in LABEL grey — gold is reserved for
warnings; an intentionally-off advisor is informational.

## v5.3.0
PERMANENT TABS + SMART LAYER — owner directive: "no tab should be closed"
and "make it way ahead and smarter". UI-only (baseline: identical).

**Tabs are permanent.** The ✕ close buttons on VIRT UNIV and SCOPE are
deleted, along with the whole hide machinery: CTRL's VIRT UNIV TAB /
SCOPE TAB toggles, the TabBar visibility gate, the Panel hidden-tab
guard, and UnivTab nav code 3. Every tab is always one click away.
`ui.tabVisible` stays in StateHub (seeded true) but has no writers.

**SCOPE auto-binds.** With no unbind and no dead end allowed, SCOPE now
binds a smart default when unbound: the applied strategy, else the
advisor pick, else the first published row. A VIRT UNIV double-click
still rebinds explicitly. The old "double-click a row" placeholder
survives only for an empty roster ("waiting for the universe roster…").

**Tab status LEDs.** Each tab gets a 4px LED in its top-right corner so
its headline state reads without opening it: LIVE — green when a
direction is READY, gold when blocked, accent when positions are open;
VIRT UNIV — gold when the advisor has a pick; SCOPE — accent when the
bound strategy holds a virtual open; CTRL — gold when AUTO is off.

**LIVE risk gauge.** A 5px bar under the vitals fills with open risk as
a fraction of the armed 2% threshold — green under half, gold
approaching, red at/over. No arithmetic needed to know how loaded the
account is.

**Derived summaries.** LIVE's RECENT header row gains a right-anchored
"nW nL · ±x.xxR" summary of the visible window; VIRT UNIV's roster line
gains "· ΣTRD n"; SCOPE's recent-virtual rows gain R sign-bars.

## v5.2.0
INSTITUTIONAL PASS II — the spec v1.3 redesign (docs/plans/
dashboard_spec_v1.3_institutional_amendment.md; visual target
neelprajna_dashboard_v5.2_mockup.html). UI-only (baseline: identical).

**One table grammar.** Zebra fills are gone everywhere — tables get 7pt
column headers, 1px ROWRULE separators, and right-anchored numerics
(`LAY_TextR`). LIVE's RECENT becomes a real table (TIME | dir | GATE |
STRAT | R | sign-bar); the R sign-bar (`LAY_SignBar`, width ∝ |R| capped
2R) is the panel's single signature device.

**Colour demoted to text + 1px borders.** New Config palette: BG
neutralised, one SURFACE/SURFACE2/HAIRLINE structure set, semantic text
colours, and dim BD_*/∗_BG tints. The only filled state surfaces left are
the armed 2% chip (GOLD_BG) and NUKE (RED_BG); EXIT EA demotes to a ghost
button; CTRL toggles carry their state in the WORD (green ON / label-grey
OFF) on a constant SURFACE cell. Old CFG_CLR_* names survive as
compatibility aliases (removal candidates for v5.3).

**Chrome.** Tab bar: active tab = TEXT on SURFACE under a 2px ACCENT
top-edge marker (no more filled teal tab). Footer: ● brand dot in ACCENT
+ three slots — the LIVE §1.7 session strip moves into the middle slot
(session dots + UTC clock, still gated by the CTRL SESSION STRIP toggle);
version tag right. Panel widens 344→360 (`PANEL_W`); footer 16→18.

**LIVE.** Identity header is now `name #hash` + AUTO chip (the word
STRATEGY dropped). SIGNAL rows sit on SURFACE strips with a 2px left rail
coloured by state (green READY / gold blocked / hairline waiting).
Section headers unify on `LAY_Rule` (7pt caps + hairline). `LT_PANEL_W`
dup deleted (review R4).

**VIRT UNIV / SCOPE / CTRL.** Roster table columns retuned for 360px;
the applied strategy is framed by a 1px ACCENT outline that follows it
across pages. SCOPE equity bars render as dim BD_GREEN/BD_RED fills
inside a bordered SURFACE well. DANGER ZONE rule tints RULE_RED.

**R1 fix (v5.1.1 screenshot regression).** All four v5.1.1 captures
showed the factory `Label` text in the footer: orphan objects from the
pre-v5.0.0 panel (`DVBDASH_`, `DV_Manual_*`) survive template reloads
outside the NPUI_ namespace. `LAY_SweepLegacyPrefixes()` (closed list,
panel prefixes ONLY — live gate prefixes untouched) now runs at
Panel_Create and logs when it deletes anything.

**Object budget.** `LAY_MAX_OBJECTS` 300→340 (spec v1.3 amendment): the
table grammar trades a handful of zebra fills for per-row 1px rules and
adds sign bars, tab accent markers, and the footer middle slot; the
worst case (all four tabs built) sits ~310–320. Same refuse-and-warn
guard; `LAY_ObjectCount()` to be logged at demo-chart sign-off.

## v5.1.1
INSTITUTIONAL UI PASS — COMPLETE. Extends v5.1.0's treatment to the two
remaining tabs. UI-only (baseline: identical).

**CTRL.** Rule lines under every section header (red-tinted under DANGER
ZONE); the EXECUTION and PANEL toggle walls become two-column grids (5 rows →
3, 3 → 2); the strategy roster gets zebra stripes.

**SCOPE.** Rule lines before the EQUITY (R) and RECENT VIRTUAL sections;
zebra stripes on the recent-virtual rows (visibility follows rows and the
bound/unbound state).

## v5.1.0
INSTITUTIONAL UI PASS — owner directive after the v5.0.2 review: "make it
institutional standard". UI-only (baseline: identical).

**Branded footer (the final "Label" kill).** The status strip's left slot is
never blank any more: idle it reads `● NeelPrajna` (muted), a toast replaces
it in gold and falls back after expiry. A blank label is unrenderable in MT5,
so the brand IS the empty state — the stuck factory "Label" text cannot occur
by construction.

**LIVE tab.** Direction heads split out as always-coloured bold labels
(`BUY ▲` green / `SELL ▼` red) with the verdict text beside them; empty-state
placeholders replace black voids ("no open positions", "no closed trades
yet"); RECENT gets zebra stripes.

**VIRT UNIV.** Zebra-striped table rows (stripe visibility follows row
visibility across pages).

## v5.0.2
PANEL LEGIBILITY REDESIGN — owner review of the v5.0.1 chart: "I don't
understand this dashboard". UI-only (baseline: identical).

**Opaque body cards.** Every tab body now sits on a full-height `CFG_CLR_BG`
card (built first, so all widgets paint above it). The tabs used to float
text straight over the chart, so gate lines / channels / key levels bled
through the rows — the main source of the confusion. `PANEL_BODY_H` 414→456.

**Blank text = hidden (the real "Label" fix).** v5.0.1's single-space
workaround failed: MT5 also trims whitespace-only label text back to empty.
`LAY_SetText` now HIDES an object handed blank text (and leaves its text
alone); StatusLine explicitly re-shows the toast on a real message, and the
VIRT UNIV meta hash cells stay hidden instead of showing "Label1".

**LIVE tab sections.** New `SIGNAL — entry pipeline` header + thin separator
lines between vitals / signal / open / recent / actions. Pipeline verdicts in
plain words: `BUY ▲  trig —  ·  waiting: bias not aligned` (was `BUY ▲ | — |
no bias`), `blocked: <reason>`, `READY`.

## v5.0.1
UI HOTFIX — two on-chart defects found in the owner's v5.0.0 screenshot review.
UI-only; no execution path touched (baseline: identical).

**Empty-label factory text.** MT5 silently refuses an empty `OBJPROP_TEXT` on
`OBJ_LABEL`/`OBJ_BUTTON`, so labels written `""` kept their previous text — a
never-written label showed the factory default (the "Label" bar in the status
line, "Label1" in the VIRT UNIV meta-row hash cells), and an expired status
toast could never clear (stuck on the old message). Fixed once centrally:
`LAY_SetText` maps `""` to a single space (visually blank, always settable);
every widget writes through it.

**Chart lines painting over the panel.** MT5 draws objects in CREATION order
(`OBJPROP_ZORDER` is click-priority only), so chart-space objects born after
the panel — key-level lines, trade lines, channel lines, MTF candles — painted
over the CTRL/LIVE tabs. Fix: `Panel_Refront()` (OnTimer, 2s) hashes the set of
non-`NPUI_` object names and, when it changes, rebuilds the panel's objects so
they are newest again. `Panel_Rebuild` preserves UI state (active tab, tab
visibility, selections); inactive tabs lazy-rebuild on next visit.

## v5.0.0
PHASE 5 — LEGACY REMOVAL. The MAJOR bump: the legacy world is deleted. The
overhaul's closing thesis — *deletion changes nothing* — proven one last time
(execution-identical vs the frozen baseline; the deletion touches no path the
Strategy Tester runs).

**Legacy panel deleted whole.** `UI/Dashboard.mqh` (the `DVBDASH_` panel,
~3,420 lines) is gone, along with the `InpUseNewPanel` flag and its branch
paths. The Phase-4 tab-driven `NPUI_` panel (`UI/Panel.mqh`) is now the only
panel. The legacy per-gate toggle machinery died with it — the StrategyPortfolio
owns runtime enables (radio, ADR-001 §2.6). Orphaned-by-deletion code swept:
`EG_model_buy/sell` + their label block, `TM_ApplyBEToAllProfitable` /
`TM_ApplyTrailToCandleHL` (the all-positions BE/TRAIL buttons — the panel uses
per-ticket `CMD_POSITION_BE`/`HALF`), the `InpNPSU_SortBy` input + `ENPSU_Sort`
enum, and the `InpDashOpaque`/`InpDashCandles` inputs + `CFG_Dash*` globals.
`InpDashX`/`InpDashY` are kept (the panel reads them for its position).

**ATR extracted to an L1 primitive.** `MM_ATRPoints` (Engine/MoneyManager) is
retired; the hand-rolled ATR-in-points is now `ATR_Points()` in the new
`Core/AtrMath.mqh` (byte-identical — same math, same per-(tf,bar) cache).
`GateContext.AtrPoints()` forwards to it and no longer includes Engine — the
gate layer has zero Engine dependency, no `MM_` anywhere. B3's last raw ATR
call reroutes to the primitive directly (its site sits in ctx-less
lifecycle/replay paths). Closes tech-debt `phase3-s0` + the ATR half of
`phase3-b3`.

**EG_ globals — sanctioned residual, not full deletion.** Full EG_ deletion is
NOT achievable execution-identically: the S15b ordering constraint
(`NPSU_OnTick` runs inside `EG_OnTick`, before `SH_PublishAll` at tick-end)
forces EG_ to remain the gate-internal source of truth. The exit proof is
therefore "zero *ad-hoc* EG_ consumers, with a CLOSED, documented set of
sanctioned residuals" — recorded in `HANDOVER.md` §Sanctioned EG_ residuals and
annotated at every site. Five sanctioned readers remain (StateHubPublish
mirror; UniverseEngine ordering-locked pulses; UniverseRoster + StrategyPortfolio
mask/enable vocabulary; TradeLogger deal-timing bias+T1 snapshot). Everything
else — the whole legacy dashboard and the Dashboard-only aggregates — is gone.

**Deferred/closed.** B3 warmup-spread quirk: left as-is (fixing it would change
seeded state → baseline violation). `Bx_Init` enable-seeding retirement,
compute-pass consolidation, roster physical absorption: deferred (not required
by the deletion; see `docs/tech-debt.md`).

## v4.6.0
PHASE-4 FINALE — tab-driven gate visuals (P4-V) + panel cutover.

**Cutover.** `InpUseNewPanel` default flips **false → true**: the new Phase-4
tab-driven panel (`NPUI_`) is now the default UI. The legacy `DVBDASH_` panel
stays fully functional as the escape hatch (`InpUseNewPanel = false`) until
Phase 5 deletes it whole — no half-demolition; its per-gate toggle swatches
still work on the legacy panel. The new panel's world has no gate toggles: the
StrategyPortfolio owns runtime enables (radio, ADR-001 §2.6).

**Full-D1.** The input-defined default is now applied BY the Portfolio at init:
`Portfolio_Init` calls the new `Portfolio_ApplyDefaults()` — the one construction
of the default strategy (gate enable vector + trade config from `Inp*`). It also
backs `Portfolio_RestoreInputs`. Execution-identical by construction: at init the
order is `EG_Init → NPSU_Init → Portfolio_Init`, so every `EG_Bx_Enabled` already
equals `InpBx_Enabled` (seeded in each `Bx_Init`); every `Bx_SetEnabled(Inp*)`
in `ApplyDefaults` therefore hits its `if(enable==EG_Bx_Enabled) return` early-out
(present on all 13 gates) — a proven no-op, so the applied enable vector is
byte-identical to the pre-Full-D1 build. Gate-local `Bx_Init` seeding is left in
place (gates like B3 branch on their enable inside their own Init); fully retiring
it is Phase-5 legacy cleanup.

## v4.6.0-pre
P4-V — tab-driven chart visual mapping (spec §7). Gate drawing paths consult
`ui.visualSource`: REAL draws exactly as today (pixel-identical anchor); a virtual
source filters the LIVE computation's visuals by that strategy's enable mask
(Tier-1+2 visibility). It is NOT a re-render under the source's own gate params
(Tier-3, out of scope — strategies carry only a mask; spec §7.4 note). Mechanism:
shared `EG_VisualSource` + per-IN-gate bits in `GateBase`; each gate's DRAW guard
swaps `EG_Bx_Enabled` for a `REAL?enable:mask` predicate; `EG_ApplyVisualSource`
(EntryGates) sets the bits and reconciles per-gate prefix visibility via
`OBJPROP_TIMEFRAMES` (the panel-tab pattern); `_SyncVisualSource` (.mq5) pushes the
source mask down from the roster (Gates never read `npsu_ros` — ADR-001). Coverage
(plan §9): IN = B1,B2,B6,T2,T3,T4-lines,T5; OUT (render nothing under a virtual
source) = B3,B4,T1,T7,T8,T9 + T4 event arrows — transient per-bar marks /
lifecycle-entangled, un-filterable from live computation without a forbidden
recompute. Drawing-only; deal-list-neutral by construction.

## v4.5.0
VIRT UNIV + SCOPE TABS (Phase-4 sessions P4-4/P4-5) on the S15b research spine.

S15b (v4.5.0-pre, committed separately): universe + advisor StateHub publishing
— `SH_PublishUniverses` fills the `SUniverseRow` stats (trades/netR/winPct/pf/
maxDD/expectancy/skipped + a cumulative-R `equityPath`), `SH_PublishAdvisor`
mirrors the Live Advisor line + ★ recommendation into `SAdvisorStatus`. Plus the
one value-identical consumption switch: AdvisorEngine auto-adopt now consumes
`Portfolio_ApplyStrategy`/`Portfolio_AppliedUid` directly and the
`BD_NPSU_ApplyStrategy` forwarder is retired (`BD_NPSU_AppliedId` stays for the
legacy panel). The UniverseEngine per-tick raw-`EG_` reads are deliberately NOT
switched (they'd read a one-tick-stale StateHub snapshot) — they retire with the
globals in Phase 5. All publishing is shadow-write (execution-identical).

VIRT UNIV (§2): the shadow-universe monitor — a sortable (`ui.sortKey`, cycles
NET R/TRD/WIN%/PF/MAXDD), paged table with U0 / applied ▶ / advisor ★ pinned to
page 1; single click selects (drives the §7 visual source), double click binds
SCOPE and opens it; ✕ hides the tab. Metas render violet with no hash.

SCOPE (§3): the single-universe inspector — definition line, R-denominated
vitals grid (incl. amber SKIPPED), the equity-R sparkline (the panel's only
chart; rendered as pixel-anchored bars — MT5 HUD objects can't use a chart-
anchored polyline), the virtual-open row, and the RECENT VIRTUAL last-6 (newest
row full detail; older rows show time+R with "—" for DIR/EXIT/MFE/MAE — the book
ring keeps only time+R, see tech-debt). ✕ unbinds. Binding a universe drives
`ui.visualSource` → the §5-delta visual-source badge renders (first live use).

New read-only StateHub for the tabs: `SUniverseRow` definition + virtual-open
fields, and `SScopeDetail` (bound-universe recent-virtual strip). Object budget
with all four tabs built: 225 / 300. Panel default stays behind `InpUseNewPanel`
(OFF). Legacy `DVBDASH_` panel untouched.

## v4.4.0
D2 MANUAL-FIRE CONFIRMATION. The LIVE tab's BUY/SELL now execute only when the
active strategy currently signals that direction (ADR-002 D2): bias aligned + a
trigger pulsing + no blocker, read from the same pipeline state the auto path
uses — `EG_TryManualEntry` reuses `EG_EvaluateAllGates` output and the same
`g_egTrigWalk` consume order, not a second evaluation. A confirmed fire opens a
manual trade (magic base+0) flagged manual-confirmed — blotter ` ·m` (§1.5) —
through TradeManager with the confirming trigger's structural levels and the
same MM checks, and consumes that trigger's pulse exactly as the auto walk does
(owner ruling: manual == auto on the setup lifecycle). A refusal opens nothing
and states the concrete reason on the status line + journal
(`exec.blocker=MANUAL_REFUSED`, transient). The MANUAL FIRE switch (CTRL) gates
the whole path. Click-only — dead in the tester; the auto path (`EG_OnTick`) is
left byte-identical (execution-identical).

## v4.3.0
SEMANTIC VERSIONING + P4-3 CTRL. Adopted the phase-aligned scheme above and
applied it retroactively (4.0.0–4.3.0). Version is now single-sourced in
`Core/Config.mqh` (EA_VERSION) and consumed by the `#property version` string,
both panel headers (legacy + new NPUI_), and the OnInit build marker
(`[EA] v4.3.0 build=P4-3-ctrl branch=phase4-dashboard flag=…`). The malformed
`#property version "3.1604"` — which overran MQL5's minor-field limit and
raised compiler warning 68 — became `"4.30"`, clearing the warning. Shipped in
the same commit as P4-3: the CTRL tab (spec §4) and its control-surface command
wiring.

## v4.2.0
P4-2 LIVE TAB. The new panel's LIVE body (spec §1) — strategy header + AUTO
chip, OPEN/RECENT sections — backed by StateHub lifecycle fills. RECENT shows a
blank strategy column for EXT/input-sourced rows rather than a doubled "EXT
EXT". Still behind InpUseNewPanel (default OFF); the legacy panel remains the
live surface.

## v4.1.0
P4-1 PANEL CHROME. New tab-driven panel shell (spec v1.2) — tab bar, status
line, visual-source badge, lazy per-tab build — running in parallel behind
`InpUseNewPanel` (default OFF), reading only StateHub. Added the OnInit runtime
build marker so the journal proves which .ex5 is actually loaded.

## v4.0.0
OVERHAUL (Phases 1–3). The major-version event: architecture changed, trading
behaviour provably did not (Checkpoint 3 execution-identical vs the frozen
baseline). Layered include graph (downward-only, ADR-001); the StateHub /
EventBus spine; all 13 gates migrated onto GateBase + GateContext behind a
registry walk; the 2% rule and NPSU-apply lifted out of the dashboard into
StrategyPortfolio. Hotfix 4.0.1 followed: StrategyPortfolio empty-roster guard
(init crash).

## v3.16.4
B6 DRAWING PARITY: all 3 regression channels drawn always (compute-all, vote-enabled-only), identity colours HIGHER=blue/PRIMARY=purple/LOWER=yellow with widths 1/2/3, per-channel label "NAME [TF] UP/DOWN R=x.xx" (InpB6_ShowLabels), no scenario table by owner request

## v3.16.3
CONTEXT PACK: docs/SESSION_BOOTSTRAP.md for fresh-chat resumption, work orders in docs/, HANDOVER research-state rewritten as single resumption source; docs only

## v3.16.2
GOVERNANCE PACK: docs/NP_Architecture_Roadmap_v1.0.md (layer map, Python-as-research-layer decision, phased roadmap), docs/AI_ROLE_PROMPTS.md (common brief + 4 role briefs so any AI model produces conformant work), docs/FABLE_COMMS_STANDARD.md (owner-issued communication standard); ROSTER R6 (6-strategy long-run confirmation, --roster R6 + ready-made NPSU_Strategies_R6_LONGRUN folder); no EA code changes

## v3.16.1
ANALYZER QoL: all Python scripts run with NO arguments (folder auto-detect: NEELPRAJNA_FILES env -> cwd -> %APPDATA% Common\Files); NEW analyzer/np_dashboard.py - self-contained HTML with per-strategy totals + hour-by-hour strategy comparison (heat-map with hover context + per-strategy 24h detail table: trades/netR/win%/PF/avgR), REAL path included; no EA code changes

## v3.16.0
BIAS GATE B6 RegChannel MTF: exact-OLS regression channels ported from the owner's RegressionChannelMTF_Pro (itself a corrected Pine conversion) as a BIAS gate - up to three TF-perspective windows (auto length presets W1/D1/H1/M15/M5/M1) must agree on slope direction AND each clear the |Pearson R| >= InpB6_MinR quality cut, else NEUTRAL; closed bars only (indicator's forming-bar channels deliberately dropped); NPSU bias token B6 (bit 0x1000), dashboard bias row 5, bias_state string gains |B6=x (NPT-2 column count unchanged); ROSTER R5 (B6 replacement-vs-addition test) + ready-made NPSU_Strategies_R5_B6 folder. Recorded overlap warning: regression slope correlates with B1 - the R quality cut and MTF agreement are the marginal information; R5 tests both bias=B6 (replace) and bias=B1+B6 (add)

## v3.15.1
np_trade_verifier.py FIX: pandas sort_values default quicksort is UNSTABLE and shuffled same-minute BE/TRAIL audit rows into false R2/R3/R5 violations (1297 on run 81906); kind="stable" restores write order - run 81906 then certifies 2199/2199 virtual trades clean

## v3.15.0
T4 PRECISIONTRENDPRO v4.1 PARITY: three parallel line groups L(21)/M(14)/S(5, opt-in) each with own bull+bear best-pair line, per-group breakout/failure watches and consumed-event latches (pulse priority L->M->S), v4.1 touch label with true visual slope angle in degrees; kept deliberately different from the indicator: best-pair pivot selection (v2.1.2 rationale), closed-bars-only breakout tests, no push alerts. PLUS: ROSTER R4 (13-strategy T8/T9 audition, generator --roster R4 + ready-made NPSU_Strategies_R4_T8T9 folder) and NP_AUTO_1/2/3 auto-adopt presets (WIN_RATE / EQUITY / LAST_TRADE, backtest-only until a meta wins OOS)

## v3.14.0
TRIGGER GATES T8 + T9: full signal-core ports of the standalone CMH Candlesticks suite (v1.5, 27 patterns) and CCC Hidden Patterns suite (v4.0, merged-candle reveals) as NeelPrajna trigger gates — quality-scored pulses (trend/prior/shape/volume/size), selectable immediate-vs-confirmed firing (InpT8/T9_ConfirmBars), structural SL = pattern extreme, magics base+13/+14, NPSU DSL tokens T8/T9

## v3.13.1
folder scan skips ROSTER_VERSION.txt metadata

## v3.13.0
capacity: up to 59 strategy FILES (ids 1..59) + mirror + 3 metas = 63 slots; 15 string inputs remain legacy fallback only

## v3.12.3
ROSTER R2 default, versioned report labels (--label), NP_REAL_default + longrun presets

## v3.12.2
audit logs BE and TRAIL as separate rows (verifier finding); verifier understands ADOPT + armed-BE + rounding tolerance

## v3.12.1
universe table paging (best on page 1; U0/applied/advisor-pick pinned) via [n/N] header button

## v3.12.0
META-SWITCHERS: M_EQUITY/M_WINRATE/M_LASTTRADE race as virtual universes inheriting held strategies trades; pre-registered switching-vs-holding experiment

## v3.11.0
AUTO-ADOPT: EA adopts the best virtual performer at runtime (win-rate / equity / last-trade / NONE), warm-up n trades, cooldown; default NONE

## v3.10.1
apply swatches highlight exactly like gate toggles (fill+border)

## v3.10.0
VERIFICATION SUITE: NPSU_Audit decision log (NPSU-D1), runtime fill invariants, per-universe visual trades, np_trade_verifier.py independent replay

## v3.9.0
one-click APPLY: NPSU row buttons load a strategy gates+trail/BE/RR into the REAL account (radio, session-only); master button in section header

## v3.8.1
advisor status line shortened to fit the section width

## v3.8.0
NPSU table is a NATIVE dashboard section swapping with CANDLE TIMEFRAMES ([NPSU]/[TF] header button); floating panel removed

## v3.7.2
— advisor⇄candle-TF default coordination, theme-adaptive panel colours, panel default beside the dashboard

## v3.7.1
— NPSU toggle PANEL: rank/strategy/equity/P-L/win%/floating-R rows, sortable, advisor status line, * marks recommendation

## v3.7.0
— LIVE ADVISOR (Phase 3): rolling-window survival-first recommendation with eligibility + hysteresis, advisory only

## v3.6.4
— absolute input/output paths printed at start+exit; analyzer/README.md

## v3.6.3
— EA no longer generates the strategy folder: strategies are EXTERNAL input (np_strategy_generator.py)

## v3.6.2
— periodic summary snapshots + loud export journal

## v3.6.1
— NPSU strategy FILES: one file in Common\Files\NPSU_Strategies\ = one virtual universe (auto-bootstrapped)

## v3.6.0
— NPSU shadow universes + self-describing CSV logs

## v3.5.0
— T1 Pattern S + CSV TradeLogger

## v3.4.0
— B5 removed, T7 arrows-only

## v3.2.0
— T7 Market Metrics
