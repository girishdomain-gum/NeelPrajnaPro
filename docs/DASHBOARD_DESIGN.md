# NeelPrajnaPro Dashboard — Design Document (tab map & rules)

> One-doc-per-thing law: this is THE dashboard design document. Owner rulings
> O-067/O-068 (2026-08-02) are its foundation. The Figma mockups
> (https://www.figma.com/design/XMIWxlvvgi5skV030ZJzqY) are sketches of this
> document, not the other way around. Implementation target: the `dashboard/`
> surface, detailed design due with the NS8 consumption packet.

## The two founding rulings (Owner, 2026-08-02)

1. **A runtime dashboard shows the state of the market and the machine —
   never the state of the project** (O-067). Sprints, ceremonies, git,
   suite counts are GOVERNANCE and live on a separate instrument that is
   never on the trading screen.
2. **One application, multiple tabs, both organs** (O-068): the dashboard
   serves screens for the left organ (QRF) and the right organ (NeelPrajna),
   with push buttons — under the safety line in §"The mirror rule" below.

## The tab map

| Tab | Organ | Contents | Buttons |
|---|---|---|---|
| 1 · RESEARCH | QRF (left) | Evidence gates table (H-07 / H-08 state-cell columns under KERNEL / TRACK groups), pipeline status strips, scientific memory (journal growth, verdicts incl. honest FAILs), window burn strip, evidence-store health | Read-only actions only: VERIFY JOURNAL · TRUTH CHECK · LEDGER · RUN SUITE · IVF RE-DERIVE · a red NO BURN WITHOUT V9 (permanently disabled button that states the law) |
| 2 · CCC / H-08 | QRF (left) | The CCC pattern stats table in the indicator's own idiom (swatch rows, OCC/S.L/S.H/MFE/MAE), tabs MEASURED (7wk M1) / HANDBOOK SPEC / N2 RE-DERIVE, PRIOR EVIDENCE — QUARANTINED badge, §3.7 note printed on-panel: measured edges never become parameters | Select All · Deselect All · CSV |
| 3 · KNOWLEDGE | the bridge | Contract v2 traffic: published knowledge releases (version, date, sealed beliefs referenced), staleness clocks per release, what crossed the boundary and when; six object types ledger | EXPORT RELEASE (re-emit an existing sealed release). Nothing on this tab creates knowledge |
| 4 · RUNTIME | NeelPrajna (right) | Read-only mirror of the EA's world: account strip (spread/step/cap), signal-gate summary, open positions, NPSU shadow universes, execution feedback flowing back, per-gate scoreboard (n · $pnl) | NONE that act. See the mirror rule |
| 5 · HEALTH | both | R6 feed status, DST clock self-policing, store sha256 checks, backup status, firewall (two-sided) state | RE-CHECK buttons only |

**Separate instrument — PROGRAMME BOARD (not a tab):** NS cycle tiles,
ceremony queue (waiting-on-Owner), main/suite/truth-check chips, amendments
in force. Footer law: "this board never ships to the terminal."

## The mirror rule (safety line — never settled by accident)

The RUNTIME tab is a **mirror, not a remote control**. Every button that can
act on the live runtime — buy, sell, close, breakeven, trail, arm — lives
ONLY where it already lives: in the EA's own panel inside the MT5 terminal,
behind the Owner's hands. The unified dashboard watches the right organ; it
never steers it. Reasons: Architecture §6 (only the Owner arms anything
real) and auditability (one control path is auditable; two are not).

## Data supply (honest scheduling)

- Tabs 1–2 are viewable from data that exists today (journal, ledger,
  hashes, the sealed CCC reference).
- Tab 3 becomes real at **NS7** (Contract v2 + release format v1).
- Tab 4's deep data (fills, per-gate performance, NPSU state) arrives via
  Contract v2's **Execution Feedback / Performance objects — also NS7** —
  by design, not coincidence: the dashboard's data supply is the
  architecture's own delivery order.
- Tab 5 aggregates checks that all exist today.
- Detailed implementation design: **NS8 consumption packet**, ruled by the
  Owner.

## Visual language (from the Owner's own instruments)

Terminal style, not SaaS cards: dense cell tables with colored state cells
(green ready / red spent-or-blocked / amber waiting-on-Owner / grey off),
muted section-caps headers, cyan nameplate, checkbox swatches,
countdown-style tiles, EA-idiom pipeline readouts ("H-07 ▲ | battery ready |
AWAIT OWNER V9"), chip strips. Palette anchored to CCC_Config.mqh (panel
C'28,34,42', bull C'39,174,96', bear C'192,57,43', tab-on C'46,80,120') and
Dashboard.mqh v2.8 conventions. Rendering rule learned the hard way: every
auto-layout container gets an explicit fill (default-white is a defect).
The Wall appears on every screen as a red footer: QRF never trades ·
NeelPrajna never learns alone · only the Owner arms anything real.

## Change record
- v1.0 (2026-08-02, O-069): created from the O-067/O-068 rulings and the
  session's mockup iterations (v1 rejected → v2 rejected → v3 terminal
  style accepted → runtime/governance split → tab map).
