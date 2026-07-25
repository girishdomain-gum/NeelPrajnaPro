# REV-S5 · Architect review · Sprint 5 (battery I) · 2026-07-25
Author: architect (fable)
Refs: ARCH-005 (+completion report), DEVQ-011/012/013 (CLOSED, ratified with
additions), ivf/reports/s5_verify.json, s5_drill.json, sessions S5-1/S5-2

## Code review (read-only, main @ fb33f32)
- splits.py: pure geometry, normative docstring matching the DEVQ-011
  ratified convention word for word; empty-train boundary case explicit.
  PASS.
- engine.py + fills.py: no-look-ahead by construction; distinct audited-
  simulator type; gross+net; DEVQ-012 confirmations landed (pessimistic
  gap-through both ways — "gaps can only hurt, never help"; n_dropped_tail
  inside the canonical byte image). PASS.
- seeds.py: documented, reproducible-by-hand derivation. PASS.
- selftest.py: kernel-clean (engine injected), decisive calibration per
  DEVQ-013, AST-audited no-verdict. PASS.
- 655 tests, ruff clean, firewall GREEN, journal 26 chain GREEN.

## Verification (VC)
- drill_s5.py rev 1 — **CAUGHT, first run**: look-ahead fill (signal-bar
  entry at a better price) flagged by ts AND price; embargo-swallowing
  train flagged; broken cross-process determinism flagged; clean control
  NON-RED. The standing drill-first rule (GO-S4) was followed.
- check_s5_battery.py rev 1 — **GREEN, first run, zero amber**:
  (A) cross-process byte determinism; (B) all 3 micro trades match an
  independent re-simulation field-by-field to the cent, totals
  +4.00/+2.59, dropped-tail count agreed; (C) split geometry equals the
  independent re-derivation across 6 cases incl. remainder spread and
  embargo-collapsed trains; (D) tri-state correct on all suites, planted-
  edge t recomputed independently and equal to 1e-6.

## Findings
- F-6 (praise recorded as a finding): first sprint with ZERO first-contact
  bugs on either side of the verification boundary. The drill-first rule
  and the DEVQ-before-build pattern are working. Tally unchanged:
  Architect 10, Developer 2.
- F-7 (observation): the engine's cost is per-trade flat (cost_for_size);
  when empirical slippage models arrive (DEVQ-008 deferred horizon) the
  micro-scenario and check section B must grow with them.

## Remaining for GO-S5
1. **Visual HC (ADR-009, tool generation 3):** real engine trades over the
   real FVG events drawn on the MT5 chart — entry/exit arrows, PnL and
   cost in the caption, and a chart-side verification that each entry
   price equals the NEXT bar's open in MT5's own series (the no-look-ahead
   rule, human-visible). Tools: ivf/human/sample_s5_trades.py +
   ivf/mt5/IVF_S5_HC_Trades.mq5. Owner eye + verbatim "HC-S5 PASS".
2. Owner Go/No-Go → GO-S5 (+Retrospective) → handover rewrite →
   ARCH-006 (Sprint 6: hypothesis registry + corrections + the first
   pre-registered verdict; carries the DEVQ-011 embargo>=hold_bars+1
   battery validation and the DEVQ-010 OB break-bar gate).

Architect verdict on the development scope: **PASS — recommend GO** once
the visual HC completes.

---
## ADDENDUM · HC-S5 result · 2026-07-25
Owner sign-off, verbatim: **"HC-S5 PASS"** · Experts log confirmed 5/5 MATCH.

Evidence (ADR-009 generation 3 — engine trades with chart-side
no-look-ahead verification): tool IVF_S5_HC_Trades.mq5 rev 1, sampler
seed=5, hold=4, engine over the real FVG events (105 closed trades,
n_dropped_tail=0). PNGs: ivf/reports/hc_s5/HC_S5_1704891600 /
1705093200 / 1706097600 / 1706580000 / 1706684400 .png. All five
entry AND exit prices confirmed equal to the bars' opens in MT5's OWN
series — the fill rule verified by an independent lens. Architect
countersigned; notable frames: the weekend-spanning short (row-adjacency
convention visible) and the sole winner exiting at its time stop BEFORE
a crash it could not have known about. 4/5 sampled trades lose after
costs — recorded as the honest reminder of why the battery exists.

Cosmetic nit carried (caption line 1 vs chart title) — queued with the
S4 caption fix; verdicts unaffected.
