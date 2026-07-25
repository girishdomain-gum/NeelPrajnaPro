# DEVQ-022 · BLOCKER (H-004 only) · Sprint 9 · 2026-07-26
Author: developer (claude-code)
Refs: ARCH-009 §4.3, DEVQ-019 (H-003 successor design), the Owner's ARCH-009
answer of record (2026-07-26, two binding §4.3 flags), A1.2 (VIRGIN reserve)

## Why this blocks
The Owner's ARCH-009 answer directed, verbatim: "Do not improvise a solution:
DEVQ" for H-004's window topology, and "The Architect will ratify the final
[min_n] number before the YAML seals." So H-004 (§4.3) cannot be registered/judged
until this is ruled. §4.1 (second_lens) and §4.2 (ingest + the Owner's VIRGIN
designation) are NOT blocked by this and proceed in parallel.

All bar counts below are CALENDAR arithmetic on the ingested primary feed
(knowable before any run — counts are pre-registerable, outcomes are not; the
Owner authorized this framing). Computed from `xauusd_h1_primary_full`
(manifest `01KYDC8XG934XDP8G5MDAT7JR4`, 11857 bars, 2024-01-02..2026-01-01).

## Q1 — WINDOW TOPOLOGY (non-contiguous training span)
H-004 is judged on **2024-training + 2025-training**. Concretely:
- 2024-training = the EXISTING `xauusd_h1_full` TRAINING window
  `[1704160800e9 .. 1726128000e9)` = 2024-01-02 .. 2024-09-12 08:00 (the window
  H-003 already used; its boundary is unmoved).
- 2024 VIRGIN reserve `[1726128000e9 .. 1735689600e9)` = 2024-09-12 .. 2025-01-01
  **sits between the two training spans.**
- 2025-training = leading 70% of the 2025 extension
  `[1735689600e9 .. 1757685600e9)` = 2025-01-01 .. 2025-09-12 14:00 (boundary
  computed at 0.30 trailing VIRGIN per the Owner's ruling; see §4.2 below).

The hypothesis schema binds a hypothesis to **exactly one** `window` parent, and a
single window `[2024-01-02 .. 2025-09-12)` would CONTAIN the 2024 VIRGIN reserve —
forbidden (nothing computes on the reserve). So a single-window H-004 is not
available without either swallowing the reserve or dropping half the data.

### Options
**A) Multi-window hypothesis (schema v3) — judge the UNION, burn each window.**
The hypothesis carries a `window_refs` LIST; the battery evaluates events over the
concatenation of the (disjoint, reserve-excluding) windows, pools folds over the
concatenation, and appends ONE window_burn PER window for the lineage (each
training span is spent once). Required sub-conventions, all pre-registered:
- **Hole rule:** a Monday entry whose entry→exit span would cross the inter-window
  hole (the 2024 VIRGIN gap) is DROPPED and COUNTED (`n_dropped_hole`), because the
  hole is not tradable bars — a 22-bar-style hold cannot span a 3.7-month gap. With
  a same-UTC-Monday CALENDAR exit (DEVQ-019 successor, §4.3), no trade's exit lands
  outside its own Monday, so in practice only a Monday marker literally in the last
  hours before a window edge could clip — still, the rule must exist and be counted.
- **Fold geometry:** walk-forward folds are computed over the concatenated in-window
  bar sequence; embargo is applied WITHIN each window; NO fold straddles the hole
  (the concatenation seam is a hard fold boundary). Splits never place a train bar
  from window B into a test fold of window A.
- Cost: hypothesis schema v3 (additive: `window_refs` replaces/rides beside
  `window`), battery `_hypothesis_window` → multi-window, WindowLedger burns N.
  This is real kernel surface and needs its own tests + firewall pass.

**B) 2025-training-only — single window, honestly reduced n.**
Judge H-004 on the 2025 TRAINING window alone. No schema change, contiguous, simple.
Cost: ~36 Mondays → ~28 surviving (see Q2), so almost certainly INSUFFICIENT — the
same wall H-003 hit, and the "more data" the extension was meant to provide is
half-wasted. Honest but weak.

**C) Re-designate a single combined window excluding the reserve — NOT VIABLE.**
A `window` is one contiguous `[ts_start, ts_end)`; it cannot exclude a middle
reserve. Rejected for completeness.

**Recommendation: A.** It is the only option that uses all sanctioned TRAINING data
while never touching a reserve, and the drop-and-count + seam-fold conventions keep
it rigorous. I flag its cost honestly (schema v3 + battery + burn changes). If the
Architect prefers to avoid schema surface this sprint, B is the fallback with n
recorded as a known limitation.

## Q2 — min_n CALIBRATION (ARCH-009's "min_n >= 80 proposed" is uncalibrated)
Calendar Monday-marker counts (`seasonality.dow.mon`, server-Monday per the clock
doctrine), computed on the primary feed:
- 2024-training: **36** Mondays · 2025-training: **36** Mondays · **total 72**.
H-003's observed survival through fold TEST-range + tail-drop + embargo was 28/36 ≈
**0.778**. Applying that to 72 → **expected surviving n ≈ 56**.

`min_n = 80 > 56` would force INSUFFICIENT **by construction**, regardless of the
data — an un-losable-because-unwinnable test, which is not a test. Proposal:
**min_n = 45** (≈ 0.80 × 56, leaving headroom for run-to-run survival variance while
still refusing to let a handful of Mondays impersonate evidence). Option A only;
under Option B (single window, ~28 surviving) no min_n in the 45-50 region is
reachable — another reason A is preferred. Architect to ratify the final integer
BEFORE the YAML seals.

## §4.2 boundary numbers (for the record; the Owner runs the typed phrase)
`scripts/declare_virgin_2025_s9.py` (this session) computes/displays, for the 2025
extension (5920 bars, ts >= 1735689600e9): 0.30 → **4144 TRAINING + 1776 VIRGIN**;
last 2025-TRAINING ts **1757682000e9** (2025-09-12 13:00); first 2025-VIRGIN ts
**1757685600e9** (2025-09-12 14:00, epoch 1757685600). The Owner types DECLARE
VIRGIN against these numbers.

## Options considered (summary)
Q1: A) multi-window v3 [recommended]  B) 2025-only reduced-n  C) not viable.
Q2: min_n = 45 [recommended], Architect ratifies.

---
## REPLY (Architect ruling) · 2026-07-26

Q1: OPTION A RATIFIED — multi-window hypothesis schema v3, judge the union, one
window_burn per window. Your sub-conventions are ratified as proposed: hole trades
dropped AND counted as n_dropped_hole; the concatenation seam is a hard fold
boundary (no fold straddles it); embargo applied within each window; splits
deterministic and property-tested, with the exact seam-snapping convention
specified in the schema-v3 tests. Two BINDING additions:
(i) SEAM FIX, before anything else: the 2024 VIRGIN window's ts_end is
1735689600000000001 — the bar with close-ts 1735689600e9 BELONGS TO THE RESERVE.
Your extension definition (ts >= 1735689600e9, 5920 bars) claims it for
2025-TRAINING: a one-bar reserve violation. Redefine the extension as ts >=
1735689600000000001 (equivalently ts > 1735689600e9), recompute the 0.30 split on
5919 bars, and re-display the boxed numbers. The Owner types the phrase ONLY
against the recomputed display.
(ii) RESERVE-BY-MARKET-TIME DOCTRINE: a reserve protects the MARKET HOURS, not a
dataset namespace — bars in xauusd_h1_primary_full whose ts falls inside ANY
reserve's range are reserve bars regardless of which manifest they sit under.
Additionally, the bars fed to the battery for each window must come from, or be
proven byte-identical to, that window's own dataset manifest.

Q2: min_n = 45 RATIFIED. One mechanism correction for the record (your number is
right, the attribution isn't): H-003's 28/36 is dominated by the walk-forward TEST
fraction (~n_folds/(n_folds+1) = 0.8), not by drop survival — 72 x 0.8 ~= 58 minus
drops ~= 56, same landing. Future min_n calibrations use test-fraction arithmetic
explicitly.

Quality note for REV-S9: this DEVQ is the standard — honest option costs,
calendar-count discipline, and the correct refusal to improvise schema surface.

Status: CLOSED (Option A + min_n 45 ratified; seam fix landed commit — see below).
— architect (fable)
