# REV-S8 · Architect review · Sprint 8 (graduation + placebo + Family Wave 1) · 2026-07-25
Author: architect (fable)
Refs: ARCH-008 (+completion report +§4 addendum), DEVQ-018/019/020/021
(CLOSED, 018/019 carrying addenda), ivf/reports/s8_verify.json (rev 1),
s8_drill.json, hc_s8/ (8 PNGs), sessions S8-1/S8-2

## Code review (read-only)
- kernel/battery/placebo.py: the placebo IS the judge — evaluate() shares
  _pipeline with run(), so a null twin faces byte-identical machinery; the
  non-consumption invariant is asserted in-code (verdict/burn counts) AND
  structurally (closed schema). Both ruled null constructions match
  DEVQ-018 exactly. PASS.
- kernel/graduation/promoter.py: sole writer of promotion; all four gates
  refuse BEFORE any write, so a promotion record is proof the gates held;
  gate (c) is honestly unpayable until the Owner provides a second feed —
  promotions are impossible today BY DESIGN. PASS.
- scripts/judge_family_wave1_s8.py: placebo-first ordering, idempotent
  re-run refusal, DEVQ-015 print discipline, setup filters inlined from
  the scan's own rule. PASS.
- §4 micro-session (S8-2): vendored smc-toolkit at the pinned commit;
  I re-hashed both files' below-sentinel bytes MYSELF — exact match to the
  ruling's sha256s; firewall extended so qrf/** structurally cannot import
  the vendored fixture; reconciliation shows the second implementation is
  a strict subset agreeing on the core rule, zones identical on the
  intersection, lookahead column quarantined. PASS.
- 786 tests, ruff clean, firewall GREEN, journal 54 chain GREEN.

## Verification (VC)
- drill_s8.py rev 1 — **CAUGHT ×3, clean control NON-RED**: hidden pass
  (consistency), SEED SWAP (only genuine recomputation can catch — planted
  on H-003 because H-002's 1e-4 deflation makes its outcomes
  seed-insensitive, stated not hidden), fabricated promotion citing a FAIL
  verdict + nonexistent lens (both legs named).
- check_s8_graduation_placebo.py rev 1 — **GREEN, zero amber**:
  * Inputs manifest-hash-verified (the worktree-stranded trades parquets
    consumed as LEDGER bytes, not as trusted files).
  * ANCHORS: both verdicts re-derived end to end from my own event
    construction (1170 FVGs, 25 weekend-born, 1145 intra-week; 52 Monday
    markers) + my own judge (DEVQ-011-A splits, DEVQ-012 fills, stdlib
    incomplete-beta t verified to ~1e-15) — n/dropped/net/t/p/fold
    geometry+means/effective-alpha/tri-state ALL matched (637 FAIL @
    9.96e-5; 28 INSUFFICIENT @ 0.05).
  * All 40 placebo null outcomes REGENERATED from the recorded seeds and
    re-judged: exact sequence match both placebos (0/20, 6/20).
  * Weekend audit: 0 weekend-born events among the 637 H-002 trades.
  * Structure: 0 promotions (the designed state), 0 second_lens, 3
    verdicts each with exactly 1 burn, no placebo producer anywhere.
- Visual HC (HC-S8, generation-4 tool's debut) — **8/8 MATCH**, Owner
  captures in ivf/reports/hc_s8/. FVG entries fill one bar after signal;
  all four MON entries sit on true 2024 Mondays; exits visibly spill into
  early Tuesday exactly as the DEVQ-019 ADDENDUM predicts. The 3-sprint
  caption-naming debt is DISCHARGED: the label now comes from the PROV
  line and the tool refuses to run without one.

## Science of the sprint
Family Wave 1 returned FAIL (H-002) and INSUFFICIENT (H-003) — both
pre-registered as acceptance-valid outcomes. The observatory's weekend
question is answered at the judging tier: excluding weekend-born FVGs does
NOT rescue follow-through (n=637, mean −0.52/oz net, p=0.93). The family
xauusd_h1/smc.fvg now carries two decisive FAILs and is deprioritized per
its own registered interpretation.

**OBS-1 (name it and keep it): the H-003 placebo exceeded the promoter
ceiling (n_pass 6 > 3 at α=0.05).** Random-time long entries on 2024 gold
genuinely profit net of costs — the entry-time-shuffle null carries the
market's base drift, which is precisely the null DEVQ-018 assigned to a
timing claim. Had H-003 squeaked a marginal PASS, gate (b) would have
refused promotion as indistinguishable-from-drift. G-3 fed G-1 in the
wild on the first live placebo. Interpretation guard for any H-003
successor: Monday-drift must beat random-timing drift, not zero.

## Findings
- **F-021-1** (Architect, machine-verified): PyPI smc-toolkit==0.1.0
  ships ZERO importable code — an empty publish; the §4 importorskip gate
  would have skipped forever. Resolved by the vendoring ruling; discharged
  and hash-verified in S8-2.
- **F-13 / Architect bug #14** (self-caught, DEVQ-018 ADDENDUM): my
  ruling asserted placebo_method lives in the hypothesis YAML — false of
  the artifacts it ratified. Corrected to forward-binding; Wave 1
  compliant as sealed.
- **F-14 / Architect bug #15** (self-caught via the HC sampler, DEVQ-019
  ADDENDUM): my "machine-verified: exits within Monday" was computed on
  idealized gap-free bars; on the real feed ALL 28 trades enter at the
  Monday 02:00 open and exit on Tuesday. Trades valid as sealed; ruling
  prose false. NEW STANDING RULE: calendar/session geometry is verified
  against the real dataset's bars, never a constructed calendar.
  Tally: **Architect 15, Developer 2.**
- **NOTE (cosmetic):** S8-1 ran on a handover-named branch rather than an
  ARCH-008-named one; outage-rebase handled correctly, no content impact.
- **OBS-2 (tool, display-only):** HC generation-4 rev 1 captions — line 1
  is white-on-light (illegible on light themes) and line 2 truncates at
  MQL5's 63-char object-text limit, hiding the MON-OK stamp from the PNG
  (the check RAN in code: a MON-BAD forces MISMATCH, and the log shows
  8/8 MATCH). Rev 2 queued in ARCH-009 — this must not become the next
  three-sprint debt.
- **F-15 (praise):** the S8-2 micro-session was exemplary — pinned-commit
  vendoring with a self-verifying provenance test, an unrequested firewall
  extension, and a reconciliation that traces every divergence to a
  declared axis.

## Carried / owed → ARCH-009
1. --rebuild-bulk extension for verdict_trades datasets (hand-copy stays
   banned; this sprint's hash-verify made worktree READS legitimate, but
   rebuildability is the real fix).
2. placebo_method-in-YAML enforcement (DEVQ-018 addendum, forward-binding)
   — registry validation + judge refusal + IVF check from S9.
3. HC tool rev 2: caption legibility + 63-char-safe layout (dow verdict on
   its own line).

Architect verdict on the development scope: **PASS — recommend GO.**
Awaiting Owner Go/No-Go for Sprint-8 close.
