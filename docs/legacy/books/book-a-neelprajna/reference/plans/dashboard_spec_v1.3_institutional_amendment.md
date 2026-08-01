# Dashboard spec v1.3 amendment — Institutional pass II ("v5.2.0")

Status: PROPOSAL for owner sign-off. UI-only. Baseline: identical (mandatory).
Supersedes the visual sections of dashboard_spec v1.2 + the v5.0.2/v5.1.x
amendment candidates already parked in `docs/tech-debt.md`. Companion mockup:
`neelprajna_dashboard_v5.2_mockup.html` (pixel-honest to MT5 capabilities).

---

## 1. Why another pass

v5.1.x fixed legibility (opaque body, sections, zebra). What still reads
"hobby" rather than "desk" in the v5.1.1 screenshots:

1. **Two grammars per tab.** Cards, chips, zebra fills, filled buttons and
   plain text rows all coexist. Institutional panels use ONE table grammar.
2. **Colour is loud.** Full-saturation button fills (BUY/SELL/CLOSE/2%/NUKE)
   compete with the data. Semantic colour should live in TEXT and 1-px
   borders; fills are reserved for the single most dangerous control.
3. **Numbers are left-ragged.** R values, counts and prices are left-aligned
   prose; a desk panel right-aligns every numeric column (tabular).
4. **The footer regressed.** All four v5.1.1 captures show the factory
   `Label` text (gold) in the status strip — see review finding R1.

## 2. Design tokens (single source: Core/Config.mqh)

Replace the palette block (§ around lines 95–144) with:

```mql5
//--- v5.2.0 institutional palette ------------------------------------
#define CFG_CLR_BG          (color)C'12,14,18'    // panel body (neutralised navy)
#define CFG_CLR_SURFACE     (color)C'18,21,28'    // card / row surface   (was SEC_A/HDR)
#define CFG_CLR_SURFACE2    (color)C'23,27,36'    // raised surface / btn (was SEC_B/INNER)
#define CFG_CLR_HAIRLINE    (color)C'38,44,58'    // ALL rules + borders  (was BORDER)
#define CFG_CLR_ROWRULE     (color)C'22,26,34'    // sub-hairline between table rows

#define CFG_CLR_TEXT        (color)C'198,206,220' // primary values
#define CFG_CLR_MUTED       (color)C'102,113,138' // secondary text
#define CFG_CLR_LABEL       (color)C'73,83,107'   // uppercase section/column labels

#define CFG_CLR_ACCENT      (color)C'70,200,192'  // brand teal — active tab, applied strategy, footer dot ONLY
#define CFG_CLR_GREEN_TXT   (color)C'79,201,143'  // direction/PnL positive
#define CFG_CLR_RED_TXT     (color)C'224,96,96'   // direction/PnL negative
#define CFG_CLR_GOLD        (color)C'217,169,62'  // warnings, blocked, armed
#define CFG_CLR_META        (color)C'165,130,200' // meta-switcher rows (kept)

#define CFG_CLR_GREEN_BG    (color)C'14,42,29'    // dim tint behind ON chips only
#define CFG_CLR_RED_BG      (color)C'46,20,20'    // dim tint behind NUKE only
#define CFG_CLR_GOLD_BG     (color)C'46,36,14'    // dim tint behind armed chip only
#define CFG_CLR_BD_GREEN    (color)C'30,74,52'    // 1-px semantic borders
#define CFG_CLR_BD_RED      (color)C'74,36,36'
#define CFG_CLR_BD_GOLD     (color)C'74,58,22'
```

Keep the old names as aliases for one session (`#define CFG_CLR_SEC_A
CFG_CLR_SURFACE` …) so widgets migrate file-by-file, then delete the aliases
in the closing commit. Glow ring (`CFG_CLR_GLOW`) is retired — the frame is a
single 1-px `HAIRLINE` border.

**Type scale (Consolas only, MT5 sizes):** 7pt = section/column labels
(UPPERCASE, LABEL colour) · 8pt = body rows · 9pt = identity line ·
10pt = KPI values · buttons 9pt. Nothing else. Bold only on direction heads
and the applied-strategy row.

**Spacing:** panel width 344 → **360** (`PANEL_W`, and retire the duplicated
`LT_PANEL_W` — see R4). Body pad 12. Section rhythm: 14 above header,
7 below. Row height 17 with a 1-px `ROWRULE` beneath (replaces zebra fills;
−1 object per stripe pair, budget-friendlier).

## 3. Component grammar (all tabs)

- **Section header** = 7pt uppercase label + hairline rule filling the rest
  of the line (two objects: label + 1-px rect). DANGER ZONE uses RED text and
  a red-tinted rule `C'74,32,32'`.
- **KPI cell** = SURFACE rect on a 1-px HAIRLINE lattice (draw one backing
  hairline rect, then 6 surface rects inset by 1px — 7 objects, no borders).
  Label 7pt top-left; value 10pt below, right side free for a 7pt unit/delta.
- **Table** = column-header row (7pt LABEL) over data rows; every numeric
  column right-aligned via `ANCHOR_RIGHT` at a fixed column x. Row separator
  = ROWRULE rect, not zebra fill.
- **Signal row** = 2-px left rail rect whose colour is the state (green
  READY / gold BLOCKED / hairline WAITING) + direction head + verdict text.
- **Button** = SURFACE2 fill, 1-px semantic border, semantic TEXT colour.
  Only two filled surfaces exist on the whole panel: the armed 2% chip
  (GOLD_BG) and NUKE (RED_BG).
- **Chip** = 1-px border + 9pt text; ON = green text/border on GREEN_BG,
  OFF = muted on SURFACE.
- **Footer strip** = brand `● NeelPrajna` left (dot in ACCENT), context
  middle (session dots + UTC clock migrate here from LIVE §1.7), version
  right. Toasts replace the middle+left in GOLD, then fall back.

## 4. Per-tab deltas (content unchanged, layout only)

**LIVE** — identity line becomes `<strategy> #hash` + AUTO chip (drop the
word "STRATEGY"; the tab already says LIVE). KPI lattice per §3. SIGNAL rows
gain the state rail. RECENT becomes a 5-column table (TIME | dir | GATE |
R | sign-bar); the sign bar is a 3–40 px rect scaled by |R| (cap 2R) — the
panel's single signature device, ~6 objects. Action row: bordered buttons
per §3. Session strip row deleted (footer takes it): frees 16 px.

**VIRT UNIV** — real table with a column-header row; hash ids render in
LABEL colour; applied row = ACCENT text + `★` + 1-px ACCENT outline rect
(replaces the current row highlight). Zebra fills → ROWRULEs. SORT stays a
cycle chip (spec-amendment already parked). Pager as two ghost buttons.

**SCOPE** — identity line + eyebrow (`BIAS B1 · TRIG T1 · RR 2.0 · TRAIL
ON`), then the SAME KPI lattice component as LIVE (shared builder in
Layout.mqh — one grammar, less code). Equity bars restyled to
GREEN_BG/RED_BG bars inside a SURFACE well. Empty states keep v5.1.0
wording, restyled as dashed-border wells (border style `BORDER_FLAT`,
colour HAIRLINE).

**CTRL** — toggle wall becomes label-left / state-right cells: the WORD
carries the state (`ON` green / `OFF` label-grey), the cell itself stays
SURFACE — no more green/blue filled walls. Strategy radio list becomes a
table with `○/●` + APPLIED tag. NUKE is the only red-filled control; EXIT EA
demotes to a ghost button.

## 5. Implementation plan (one session, UI-only)

1. Config.mqh: new palette + aliases. Compile.
2. Layout.mqh: add `LAY_Rule` (section header pair), `LAY_KpiGrid`,
   right-anchor helper, ROWRULE row builder. Compile.
3. One widget per commit: LiveTab → UnivTab → ScopeTab → CtrlTab →
   TabBar/StatusLine (footer takes session strip; ver bumps via EA_VERSION).
4. Delete aliases + retired tokens; bump `EA_VERSION` "5.2.0" /
   `EA_VERSION_SHORT` "5.20" / `#property version "5.20"` together.
5. Object budget: recount — net change is negative (zebra fills removed,
   glow ring removed, session row moved; sign bars +6). Assert < 300 in log.

**Exit checks:** compile 0/0 · tester deal list byte-identical to
report_baseline (UI must not touch trading) · visual sign-off on demo chart
vs the mockup · toggle/apply round-trips · `Label` regression test of R1
(fresh chart + template-reload + EA re-init: footer never shows `Label`).

## 6. Risks

- MT5 renders ★/●/○/▲/▼ in Consolas (already in the Phase-4 verified set);
  no new glyphs introduced.
- `ANCHOR_RIGHT` column alignment is the only new layout technique; verify
  once on the live terminal before rolling across tabs.
- Width 360 nudges `InpDashX` charts — note in CHANGELOG.
- Object budget: `LAY_MAX_OBJECTS` raised 300→340 (implemented) — the row-rule
  grammar + sign bars + tab markers put the all-tabs-built worst case at
  ~310–320. Guard behaviour unchanged; log `LAY_ObjectCount()` at sign-off.


---

## v1.3.1 delta (v5.3.0 — permanent tabs + smart layer)

Owner rulings folded in after the v5.2.0 build:

1. **Tabs are permanent.** Spec §2.5 (✕ hides VIRT UNIV) and §3.7 (✕
   unbinds SCOPE) are RETIRED, together with CTRL §4.4's tab-visibility
   toggles. `ui.tabVisible` remains in StateHub but has no writers.
2. **SCOPE auto-bind.** When unbound, SCOPE binds applied → advisor
   pick → first published row (UI-local). Explicit rebinding stays a
   VIRT UNIV double-click.
3. **Tab status LEDs.** 4px corner LEDs per tab (LIVE ready/blocked/
   positions · UNIV advisor pick · SCOPE virtual-open · CTRL auto-off).
4. **LIVE risk gauge** (open risk vs armed threshold) and **derived
   summaries** (RECENT nW nL · ΣR; roster ΣTRD; SCOPE recent sign-bars).

Object cost: +≈14 (LEDs 4, gauge 3, summary 1, SCOPE bars 6), −4
retired (2 ✕ buttons, 2 toggles) — comfortably inside the 340 cap.

## v1.3.2 delta (v5.4.0 — SCOPE RESET + live-chart fixes)

1. **SCOPE RESET** replaces the retired ✕ (owner ruling: tabs never
   close, SCOPE only resets). RESET = clear explicit binding → auto-bind
   default; clear UNIV selection; rebuild the equity spark.
2. **Bold+glyph ban:** direction heads render REGULAR weight — the live
   terminal drops "Consolas Bold" glyph labels (v5.2.0 screenshots).
   Rule: panel glyphs (▲▼●○★▶) ship in regular weight only.
3. **Defensive visibility:** per-tab Update re-asserts its always-on
   statics (write-on-change) so no rebuild path can strand them hidden.
4. **Sortable columns:** VIRT UNIV header click = sort by column; active
   header brightens to TEXT.
