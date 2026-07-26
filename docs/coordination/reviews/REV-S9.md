# REV-S9 · Architect review · Sprint 9 (Second Lens, Rebuild, Enforcement) · 2026-07-26
Author: architect (fable)
Refs: ARCH-009 FINAL + ADDENDUM (VIRGIN exclusion) + ADDENDUM 2 (clock
doctrine, DST-refined) + completion report; DEVQ-022/023 (CLOSED);
sealed notes 01KYDCNRM4…/01KYDDMKQJ…/01KYE3BBE2…; ivf/reports/s9_verify.json
(GREEN), s9_drill.json (CAUGHT ×5), hc_s9/ (6 PNGs); sessions S9-1/2/3.

## Code review (read-only)
- schema v3 / walk_forward_multi / multi-window battery: seam a hard fold
  boundary, hole drops structurally counted, one burn per union window,
  verdict v3 additive (v1/v2 untouched). PASS.
- calendar_day exit (fills.py): epoch-day walk matching the detector's day
  index, hold cap, drop on truncation OR unconfirmed day-end — no-look-ahead
  preserved at the data tail. The placebo stays valid because the exit is an
  ENGINE rule, not a precomputed column. PASS.
- §1 rebuild: trades_table single-construction shared by write + rebuild
  paths — byte-identity BY CONSTRUCTION. All 4 lineages + overlap parquet
  regenerate sha-assert-equal on main (witnessed by the Owner's run). PASS.
- §2 seal: registry + judge refusals; Wave-1 grandfathered. PASS.
- overlap engine: faithful to the sealed correction note; self-STOPped
  under the original criterion; append path inert until ruled. PASS.
- 843 tests · firewall 8/8 · ruff clean · journal 73 chain GREEN.

## Verification (VC)
- **drill_s9 rev 1 — CAUGHT ×5, clean control**: seam-straddling fold ·
  hole miscount · single-shift-across-DST lens (both the doctored CHOSEN
  shifts and the flattered pooled totals flagged) · ORDERING FRAUD (the
  sealed note moved after the lens — the chain-position audit fired) ·
  broken placebo_method seal.
- **check_s9 rev 1 — GREEN, zero amber**, and REHEARSAL-PROVEN: the entire
  check ran end-to-end on the Architect's machine against the raw CSVs +
  real journal BEFORE shipping (a program first). On main it consumed only
  rebuilt, manifest-hash-verified parquets and re-derived EVERYTHING:
  H-004's verdict to the last digit (n=56 FAIL, 8 folds, 2 tail / 0 hole
  drops, t/p to 1e-9, bootstrap CI replayed exactly from the recorded
  engine seed, 56 trades key-identical to the parquet); all 20 placebo
  outcomes from the recorded seeds (1/20); the second lens INDEPENDENTLY
  recomputed from the sealed note text — pooled 8290/7912/0.9544028950542822
  exact, same era shifts (−2/−3/−2/−3), recorded boundary instants inside
  the maximizing tie-sets; ordering note<manifest<lens (70<71<72); 0
  reserve timestamps in the overlap slice; burns exactly one per window
  incl. H-004's two; 0 promotions (counted fact — H-004 FAILed).
- **HC 6/6 MATCH (rev-2 tool debut)**: every H-004 entry AND exit opens on
  the SAME Monday per MT5's own series (the MONX assertion is part of
  MATCH) — the DEVQ-019 successor exit visually and mechanically confirmed;
  the REV-S8 caption defects fixed and verified in the same pass.

## Science of the sprint
**The second eye is open and the feeds corroborate**: first second_lens
01KYE3WCKK40PNJ8JEATQ4XTNT, tier=BROKER (declared, spectrum recorded),
agreement 0.9544 ≥ the pre-sealed 0.95, aligned piecewise across
empirically-detected US-DST eras — with the full guard-fired history in
the record. Gate (c) is satisfiable for the first time; nothing promotes
because H-004 FAILed, which is the machinery agreeing with the data, not
failing it. **H-004**: Monday longs earn +5.00/trade net over 2024+2025
but p=0.108 — indistinguishable from RANDOM TIMING at n=56. The claim as
worded by OBS-1 ("beats random timing") is answered NO at this n; the
family's honest state is two attempts, no edge shown.

## Findings tally (Architect 17, Developer 4 — three sides of honesty)
- **#16 (Architect, self-caught by own tool)**: "UTC verified" was a
  circular internal-consistency test; the clock is broker server time.
  Clock doctrine now binds; zero ledger impact.
- **#17 (Architect, self-caught by own guard)**: the shared-COUNT
  alignment criterion saturates on a dense hourly grid — foreseeable; the
  5% tripwire I attached caught it in all four eras.
- **Developer #3 (caught in Architect review)**: the 2025 extension's
  `>=` boundary claimed the 2024 reserve's final bar — a one-bar reserve
  violation fixed BEFORE the typed phrase was run.
- **Developer #4 (caught in ruling review)**: EU-hardcoded DST instants vs
  ADDENDUM 2's "detected" instruction — winter agreement depressed to
  0.73–0.76; empirical detection restored 0.966/0.953, CONFIRMING the
  Architect's recorded US-DST prediction (boundaries 2024-03-09 /
  2025-03-08).
- **Counterweights (praise)**: the overlap engine's SELF-STOP under its
  own guard rather than a silent pick — the sprint's finest moment; the
  DEVQ-022/023 quality (calendar counts, honest option costs, Option C
  condemned by the Developer itself); the coalescing bug self-caught by
  its own test and disclosed; the S9-3 audit-trail lens notes.
- **NOTE (housekeeping)**: branch/worktree sprawl (S9-2 recycled the
  arch-002 dir; -41df8b ancestor branch dangling) — prune at close;
  AI_PROJECT_STATE.md stale at S9-2 boot — regenerate; t0_s9.py ruff nit.

## Policy carried to ARCH-010
1. TRIAL ACCOUNTING: H-004 judged at α=0.05 undeflated by H-003's attempt
   (no trial_count convention for hypothesis attempts). Its FAIL is
   a-fortiori honest, but the policy must be settled before any family's
   THIRD try: proposal — each registered hypothesis appends trial_count 1
   to its family, forward-binding. ADR required.
2. Worktree pruning + state-file regeneration discipline.
3. Independent-Observation-Lenses naming (Owner's architecture note) as
   new lens work arrives.

Architect verdict on the development scope: **PASS — recommend GO.**
Awaiting Owner Go/No-Go for Sprint-9 close.
