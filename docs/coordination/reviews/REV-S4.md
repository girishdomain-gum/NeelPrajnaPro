# REV-S4 · Architect review · Sprint 4 (screener + costs + SMC) · 2026-07-25
Author: architect (fable)
Refs: ARCH-004 (+completion report), DEVQ-008/009/010 (CLOSED; 010 has the
FVG-definition ADDENDUM), ivf/reports/s4_verify.json, s4_drill.json

## Code review (read-only, main @ dee2cd4 line)
- screener_vbt.py: telescope discipline enforced three ways (AST audit
  test, TRAINING/EXPLORATION-only guard, single code path binding
  shortlist to trial_count). Declaration-before-ranking honored in the
  note payload. PASS.
- trials.py: §4.8 surface, monotone, kernel-clean. PASS.
- cost_models.py + venues.yaml: deterministic, hand-computed to the
  cent; name-reference per DEVQ-008. PASS (freeze test owed — below).
- smc/detector.py: the sprint's crown. The Developer independently
  discovered the library's non-causality (DEVQ-010) and built a
  knowability wrapper that upholds §4.3; registered + calibrated
  1.0/1.0 through the real journal. PASS.
- 182 tests, ruff clean, firewall GREEN, journal 25 records chain GREEN.

## Verification (VC)
- check_s4_screener.py rev 3 — **AMBER (honest)**: sections A/B/C/D all
  bite; 1 shortlist audited (grid 500 == trial_count 500, declarations
  complete, cost model resolves); **FVG full recomputation 105/105
  exact** on the real sample. Sole amber: shortlist seed=null.
- drill_s4.py rev 3 — **CAUGHT** on both mandated frauds (planted
  verdict-writing screener; trial under-count 180-of-500) with the
  correct control pair unflagged and scratch FVG recomputation clean.

## Findings
- **F-2 (the sprint's headline): the FVG definition was UNDERSPECIFIED.**
  rev-2 recomputation went RED (107 vs 105) on first real contact; Owner
  bar inspection proved both deltas had bearish middle candles; the
  displacement-candle condition is now RATIFIED in the DEVQ-010 ADDENDUM
  and encoded in check rev 3. Two independent implementations + real
  data + a refusal to shrug at 2/107 = the IVF working as designed.
- F-3 (observation): both delta patterns spanned the 50-hour weekend
  hole; row-adjacency == bar-adjacency is the shared convention.
  Research question queued for Sprint 7 observatory.
- F-4 (minor): real screener runs should record a seed (currently null
  in the shortlist note). Micro-task below.
- F-5 (process): F-1 recurred for detector/screener datasets (events +
  shortlist copied from the S4 worktree by hand). Extend --rebuild-bulk.
- Architect first-contact bugs this sprint: #8 (rev-1 check silently
  audited zero shortlists — soft-pass sin, now structurally AMBER),
  #9a/9b (drill format lag + impure scratch data). All caught by the
  drill mechanism before any real reliance. Tally: **Architect 10,
  Developer 2** — and the asymmetry is the system's health, not its
  shame: the side that writes the checks gets checked hardest.

## Micro-tasks for one small Developer session (pre-GO)
1. venues.yaml freeze test (DEVQ-008 ruling): cited names' parameters
   pinned by snapshot test.
2. Screener records a derived seed in the shortlist note (F-4).
3. --rebuild-bulk covers detector/screener datasets (F-5).

## Remaining for GO-S4
1. Micro-task session (above) — small, single session.
2. **Visual HC (ADR-009 first outing):** sample_s4_zones.py over the
   real FVG events → HC_S4_input.txt (two lines) → IVF_S4_HC_Zones.mq5
   on the XAUUSD H1 chart → PNGs with zone rectangles, provenance
   caption, and chart-side FVG MATCH → Owner eye + verbatim "HC-S4
   PASS" → Architect countersign.
3. Owner Go/No-Go → GO-S4 (with Retrospective) → handover rewrite →
   ARCH-005 (Sprint 5: battery I — engine, splits, selftest).

Architect verdict on the development scope: **PASS — recommend GO**
once the micro-tasks land and the visual HC completes.
