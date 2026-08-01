# ADR-002 — Dashboard information architecture & strategy interaction model

- Status: **Accepted** (owner-approved, 2026-07-21)
- Extends: ADR-001 (StateHub/EventBus, StrategyPortfolio, real = one strategy)
- Companion: `docs/plans/dashboard_spec_v1.md` (frozen UI spec), phase plan v1.1 (Phase 4)

## 1. Context
ADR-001 made the dashboard a pure renderer of StateHub posting commands to EventBus. Design sessions (mockups v1, owner-reviewed) then forced a set of policy decisions about how the operator interacts with strategies, trades, and the panel itself. This ADR records them; the spec freezes the resulting UI.

## 2. Decisions

### D1 — Strategies are immutable at runtime; interaction is selection-only
Gates are never toggled at runtime. A strategy (gate mask + RR/trail/BE, defined by its roster file) is a research-validated artifact; the operator selects among strategies, never edits one live. Consequences: `CMD_TOGGLE_GATE` does not exist; gate enable state is StrategyPortfolio-internal, derived from the applied strategy; gate state on the panel is display-only (pipeline readout). The v2.x per-gate swatch UI is retired.

### D2 — Manual trades are strategy-confirmed fires
`CMD_MANUAL_BUY/SELL` executes only if the active strategy currently has a valid signal in that direction (bias aligned + trigger pulsing + no blocker). Otherwise it is refused with a logged, displayed reason (e.g. "MANUAL BUY refused — no T1 pulse"). Executed manual trades are strategy trades flagged `manual-confirmed`; there is no trade outside a strategy. A CONFIG switch (MANUAL FIRE) can disable the pathway entirely.

*Pulse lifecycle (implemented v4.4.0):* a confirmed manual fire consumes the confirming trigger's pulse via the same path as an auto fire — manual == auto on the setup lifecycle (one signal, one trade). A re-validated setup pulses again and can be fired again; nothing legitimate is lost, and an AUTO+MANUAL double-fire on one signal is prevented by construction rather than left to MaxPositions.

### D3 — Open-trade lifecycle belongs to the parent strategy
TradeManager snapshots the managing parameters (SL/TP/RR, trail, BE) per position at entry. Applying a new strategy affects new entries only; open positions live and die by the strategy that opened them. Attribution is therefore exact across switches.

### D4 — Strategy identity = content; nomenclature is validated
Identity is the content hash of the meaningful definition lines (e.g. `bias=B6+B2+B4|trig=T1` → `#a3f9`). Any file modification mints a new identity; logs, trade records, and CSVs carry name + hash; the analyzer aggregates by name+hash so histories never blend. Additionally the filename must agree with content (T1_B6B2B4.txt ⇒ trig=T1, bias=B6+B2+B4); on mismatch the Portfolio refuses the file as corrupt and logs a warning with a concrete fix suggestion (rename or restore).

*Clarification (Phase 3 S15 implementation):* Validation enforces **filename stem == `name=` field**; the mask-style filename in the example (`T1_B6B2B4`) is generator convention, not a checked rule (enforcing it would reject the descriptive names the generator actually emits — `T1_base`, `T8_noBias` — for no integrity gain, since the hash already provides gate-level tamper evidence). The hash covers the **definition only** (`bias/trig/trail/be/rr/validated`); the **name is excluded**. Consequence, by design: two differently-named files with identical definitions share a hash (identity = definition; name = label). Therefore **(name, hash) together are the unique key** everywhere — apply verification, logs, CSVs, analyzer aggregation — and no consumer may key on hash alone, or distinct strategies with the same gate-set would blend. The hash is **8 hex** (32-bit; 4 hex risks collisions across a ~59-file roster); logs/CSV/StateHub carry all 8, though space-constrained displays (the dashboard mockups) may show the leading 4 (`#a3f9`).

### D5 — Restart persistence, loud re-apply
Applied strategy (name+hash), tab visibility, DETAIL binding, sort state, and 2% settings persist across EA reload (MT5 global variables / state file). On restart the persisted strategy is re-applied and logged loudly; the EA never silently reverts to input defaults. If the persisted strategy's file is missing or its hash no longer matches, the EA falls back to input defaults with a prominent warning.

### D6 — Blocker taxonomy is a closed enum
`exec.blocker` ∈ { NONE, SPREAD, SESSION, MAX_POS, RETRY_COOLDOWN, MARGIN, TWO_PC_ARMED, AUTO_OFF, NO_STRATEGY, MANUAL_REFUSED }. Every block site writes one of these (Phase 2 instrumentation); free-text reasons go to the log line, not the state field.

### D7 — Tab model
Four tabs: REAL (always open, default), UNIVERSE, DETAIL, CONFIG. UNIVERSE/DETAIL/CONFIG visibility is controlled from CONFIG (PANEL section); DETAIL is a single inspector bound by double-click on a UNIVERSE row, cleared by its ✕ (single click selects/highlights only). Tab contents are built lazily on first activation, then hidden/shown via OBJPROP_TIMEFRAMES; write-on-change throughout; the dashboard module is fully optional (tester/headless never touch it).

### D8 — Monitoring is separated from control
REAL/UNIVERSE/DETAIL are read-only monitors (REAL's BUY/SELL/CLOSE/BE/½ act on the live book and remain, governed by D2). All behavior-changing controls live in CONFIG: strategy select+APPLY / RESTORE INPUTS, AUTO, MANUAL FIRE, 2% arm+threshold, NPSU engine, advisor line, tab visibility, and the danger zone.

### D9 — NUKE is two-step and ends in AUTO OFF
NUKE lives in CONFIG's danger zone: first click arms (CONFIRM/CANCEL), confirm closes all EA positions and sets AUTO OFF. Rationale: post-nuke, the operator has declared an emergency; automated re-entry must require an explicit human re-arm.

### D10 — Risk-per-trade stays compile-time
Money-management sizing inputs are EA inputs, not runtime controls. Changing risk sizing mid-session is deliberately hard.

### D12 — EA exit is distinct from NUKE
An EXIT EA control (CTRL danger zone, two-step) detaches the EA via ExpertRemove() without
touching positions; open positions are explicitly called out as left unmanaged at confirm
time. NUKE and EXIT are never combined into one action. Owner-approved 2026-07-21, together
with: external/terminal trades displayed as EXT but excluded from strategy stats (§3), and
the D5 missing/changed-strategy restart fallback (input defaults + prominent warning).
EXT position rows are **read-only** on the panel: the LIVE tab renders no BE/½ (or any
management) control on a position the EA does not own — the terminal remains the tool for
terminal-made trades. The §3 "displayed but excluded" rule thus extends to management, not
only stats (owner ruling 2026-07-22, P4-2 review).

### D11 — Analytics division of labor
The panel shows live, decision-grade state only. The single chart permitted on-panel is DETAIL's R-equity sparkline. Deep analytics (per-strategy curves, hourly heatmaps, verification) remain the Python analyzer's job.

## 3. Consequences
Positive: a whole class of accidental-state risk (live gate toggles) is deleted; attribution is total (D2+D3+D4); research history is tamper-evident (D4); the panel's state is fully reconstructible after restart (D5); UI complexity drops (no swatch grid, one inspector). Negative/costs: manual trading is constrained by design — the operator cannot force a counter-strategy trade from the panel at all (accepted deliberately; the escape hatch is the MT5 terminal itself, which the EA will record as an untagged external position and display but exclude from strategy stats); double-click detection needs a click-timing implementation in OnChartEvent (~20 lines).

## 4. Alternatives rejected
Runtime gate toggles (v2.x behavior) — rejected as strategy-editing-by-accident; N spawned DETAIL tabs — rejected for chart-object budget, single bound inspector chosen; free manual trading with MANUAL tag — superseded by owner's stricter D2; risk-per-trade in CONFIG — rejected per D10; one-click NUKE — rejected per D9.
