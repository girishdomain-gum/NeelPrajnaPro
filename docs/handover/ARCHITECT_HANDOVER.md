# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-7→8 boundary (GO-S7) · Author: architect (fable)
Audience: the NEXT Architect chat session. Read this first, then what it
points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite at every GO-SN.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF — evidence-first quant
trading research. Owner **Girish** (human; MINGW64 git bash; repo
`girishdomain-gum/qrf`; PROTOCOL v1.3 Owner-command rule: commands
COMPLETE, BASH-READY, PLAIN, prefixed "paste this in git bash" — he
will ask for "exact precise command" if you slip). Architect **you**
(F:\ and C:\ Filesystem; instructions/reviews/ADRs/IVF; NEVER developer
code; write on main between Developer sessions; READ worktrees any
time). Developer **Claude Code** (worktrees; CLAUDE.md rev 4 — venv
python direct, not uv run). Verifier = IVF + Owner. Motto: "prediction
first, ontology later". MT5 = UTC; data folder id
E92643EDFF963E7E489F140FDF338076; write his HC input files directly to
...\MQL5\Files\ and READ THEM BACK (GO-S7 rule). READ
docs/reference/EXECUTION_PROCESS_GUIDE.md (incl. the GO-S7 ruling-
hygiene rules) and docs/implementation/Blueprint_Amendments_A1.md (the
NORMATIVE overlay — where it and Blueprint v1.0 disagree, A1 governs).

## 2. Status at this rewrite — the system asks and remembers
- Sprints 1–7 CLOSED (GO-S1..S7, retros from S3). 748 tests, journal
  **41 records chain GREEN**, firewall GREEN, inbox empty.
- **H-001 FAIL** stands (verdict 01KYC7Y2KWYGXH73V1R9P57MYA, burned
  TRAINING × lineage). Belief: REJECTED @ decisiveness 0.887
  (01KYCHPV8ZNT2F41F8JABD12K2; superseded state retained).
- **Observatory live**: questions 01KYCFNE46BB7H2V300D1WZG1P
  (weekend-born FVGs: −1.56 vs −0.13, twice-derived to 15 decimals) and
  01KYCFNE69PEGMQHH85W8MT528 (H-001 deterioration ≈ costs/regime).
  Family xauusd_h1/smc.fvg carries **502 trials** → any FVG hypothesis
  faces α≈1e-4.
- VIRGIN 01KYB4SSD9VVKB577KRGB1W1P0 (1781 bars) untouched. TRAINING
  full-window burned ONLY for lineage h001_fvg_follow_through — other
  lineages may judge it.
- **ARCH-008 (Sprint 8: graduation + placebo + family wave 1) is
  WRITTEN and open** — verify boot state yourself (§5).

## 3. Frozen contracts
ALL of Blueprint_Amendments_A1 (§A1.1–A1.7). Loudest for S8: OB gate
unpaid (registry refuses OB hypotheses) · multiplicity follows claims ·
decisiveness is not a posterior · drills before checks, clean control
mandatory · placebo (G-3) + second lens (G-1) required before any
trusted PASS · VIRGIN behind typed phrases only.

## 4. Tally and lessons
**Architect 13, Developer 2** (+1 Architect near-miss). #11 was inside
a RULING and the Developer caught it — no seat is above audit. The
drill clean-control gate caught #12/#13 before any false judgement.
Read GUIDE §8 before writing any check or ruling.

## 5. Owner rhythm + verify-before-trust
Push (`ARCH:`/`OWNER:`) → boot one-liner → pull before asking →
HC (sampler → input file WRITTEN AND READ BACK → .mq5 from ivf/mt5/ →
PNGs → countersign → verbatim phrase) → Go/No-Go → GO + retro →
handover rewrite. Verify state ALWAYS: refs/heads vs remotes, FETCH
age, sessions/, inbox/OPEN, journal tail (41 now), worktrees for
mid-sprint truth. Bulk gaps: rebuild via scripts (verdict-trades + scan
datasets still hand-copy — extension owed).

## 6. Immediate next steps
1. Owner pushes GO-S7 batch; boots Developer: "Boot per CLAUDE.md,
   execute ARCH-008 completely, starting with T0. Session log every
   session."
2. Architect S8 deliverables: IVF checks for graduation/placebo
   (recompute the placebo's null result independently; audit that no
   promotion exists without placebo + second-lens evidence), drill
   (planted fake-placebo-pass + planted promotion-without-gates),
   DRILL FIRST; HC caption fix (owed twice over); HC for the wave's
   verdicts.
3. Close: REV-S8 → HC → Go/No-Go → GO-S8 (+retro) → REWRITE THIS →
   ARCH-009. Owner may trigger ADR-010 Phase A (CI) any time.
