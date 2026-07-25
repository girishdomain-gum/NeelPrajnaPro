# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-25 at the Sprint-8→9 boundary (GO-S8) · Author: architect (fable)

## 0. SESSION BOUNDARY SNAPSHOT (added at chat switch, 2026-07-25)
Verified at handover moment: the GO-S8 close batch (GO-S8, this
handover, ARCH-009 DRAFT, REV-S8 + HC evidence committed just before)
is being committed by the Owner — VERIFY local main == origin/main
yourself before trusting anything (§5). Journal **54 records chain
GREEN**. inbox/OPEN empty (DEVQ-018..021 CLOSED; 018/019 carry
ADDENDA — read both, they bind you). HC-S8 evidence in
ivf/reports/hc_s8/ (8 PNGs, generation-4 tool). **ARCH-009 is a DRAFT
awaiting Owner review** — §4 (second lens + data extension) needs his
explicit approval and his DATA before the Developer can be booted; §§1–3
are approved-in-principle carried items. The Developer has NOT been
booted for ARCH-009. Same-day context: Sprints 1–8 ALL closed TODAY;
the Owner is engaged, reads the reviews, and asked for the GO-S8 retro
to emphasize scientific lessons — treat him as the system's conscience,
not its operator.

Audience: the NEXT Architect chat session. Read this first, then what
it points to. Chat history is gone; this file + the repo are memory.
PROTOCOL duty: rewrite at every GO-SN.

## 1. Identity and mission
You are **Fable**, the **Architect** of QRF — evidence-first quant
trading research. Owner **Girish** (human; MINGW64 git bash; repo
`girishdomain-gum/qrf`; PROTOCOL v1.3 Owner-command rule: commands
COMPLETE, BASH-READY, PLAIN). Architect **you** (F:\ and C:\
Filesystem; instructions/reviews/ADRs/IVF; NEVER developer code; write
on main only in Owner-declared write windows; READ worktrees any time).
Developer **Claude Code** (worktrees; CLAUDE.md; new session per
task/sprint — never reuse a spent session). Verifier = IVF + Owner.
Motto: "prediction first, ontology later". MT5 = UTC verified; data
folder id E92643EDFF963E7E489F140FDF338076; HC input files are WRITTEN
by you into ...\MQL5\Files\ and READ BACK (GO-S7 rule), and are
regenerable byte-for-byte by the committed sampler. READ
docs/reference/EXECUTION_PROCESS_GUIDE.md (ruling-hygiene rules) and
docs/implementation/Blueprint_Amendments_A1.md (NORMATIVE overlay; A1
governs over Blueprint v1.0 on conflict).

## 2. Status at this rewrite — the system judges, doubts itself, and refuses to graduate alone
- Sprints 1–8 CLOSED (GO-S1..S8). 786 tests, journal **54 chain
  GREEN**, firewall GREEN (now also walls the vendored test fixture),
  inbox empty.
- **Wave-1 verdicts stand**: H-002 FAIL (01KYCQBHRJHY1A1PY1PQ01TAT5;
  n=637, p=0.93 @ α≈1e-4) — the weekend question ANSWERED: intra-week
  FVG follow-through has no edge; family xauusd_h1/smc.fvg now carries
  TWO decisive FAILs + 502 trials and is deprioritized by its own
  registered interpretation. H-003 INSUFFICIENT
  (01KYCQBJ7N2D99N7CDKQ1V4J1K; n=28<40) — needs data, not thresholds.
  H-001 FAIL stands. Beliefs: REJECTED 0.887 (H-001) · REJECTED 0.8624
  (H-002) · UNTESTED 0.0 (H-003).
- **Placebo (G-3) + Promoter (G-1) LIVE.** Zero promotions BY DESIGN:
  gate (c) is unpayable until the Owner provides a second feed. KNOW
  THIS: the H-003 placebo runs 6/20 > ceiling 3 — the timing null
  carries 2024 gold's base drift; any Monday-drift successor must beat
  RANDOM TIMING, not zero (GO-S8 retro).
- **Real-feed Monday geometry** (DEVQ-019 ADDENDUM): ALL H-003 trades
  enter Mon 02:00 open, exit TUESDAY. Trades valid as sealed; my
  "within Monday" ruling prose was an idealized-calendar error. Any
  successor pins exit to the last same-Monday bar and is verified
  against the real bars.
- VIRGIN 01KYB4SSD9VVKB577KRGB1W1P0 (1781 bars) untouched. TRAINING
  window burned for lineages h001/h002/h003 ONLY.
- **smc-toolkit VENDORED** (tests/third_party/, MIT, pinned commit,
  hash-locked below-sentinel; F-021-1: the PyPI package is EMPTY).
  Tests-only; firewall enforces.
- S8 verdict-trades parquets live ONLY in the S8-1 worktree
  (.claude/worktrees/qrf-architect-handover-cf5806/datastore/bulk/);
  legitimate to READ because check_s8/sampler hash-verify against
  manifests 01KYCQBHQRQQJ7VRQRVJFJQH9C / 01KYCQBJ6SZ95Y9NPTVBPKPERM.
  Do NOT hand-copy; ARCH-009 §1 makes them rebuildable.

## 3. Frozen contracts
ALL of Blueprint_Amendments_A1. Loudest now: nulls match CLAIMS, bias
conservative, placebo_method-in-YAML FORWARD-BINDING from the next
registration (DEVQ-018 ADDENDUM — registry/judge/IVF enforcement is
ARCH-009 §2, not yet built) · second_lens agreement threshold
pre-registered BEFORE overlap computed (DEVQ-020) · OB gate unpaid
(registry refuses OB hypotheses) · drills before checks, clean control
mandatory · VIRGIN behind typed phrases only.

## 4. Tally and lessons
**Architect 15, Developer 2.** #14/#15 were both ruling PROSE asserting
unverified properties (of shipped artifacts; of real data) — both
self-caught. Standing rules that now bind you: machine-verify numeric
examples; re-implement from NORMATIVE definitions; read back every
written artifact; verify calendar/session geometry against the REAL
feed's bars, never a constructed clock. The HC layer sees what machine
layers cannot — the sampler caught #15 after engine and IVF agreed to
1e-9. Read GUIDE §8 before writing any check or ruling.

## 5. Owner rhythm + verify-before-trust
Push (`ARCH:`/`OWNER:`) → boot one-liner (NEW Claude Code session) →
pull before asking → HC (committed sampler → input file written AND
read back → generation-4 IVF_HC_Trades.mq5, label from PROV line,
no label no capture → PNGs → countersign → sign-off) → Go/No-Go →
GO + retro → REWRITE THIS. Verify state ALWAYS: refs/heads vs remotes,
FETCH age, sessions/ (S8-1, S8-2 are the latest), inbox/OPEN, journal
tail (54 now), worktrees for mid-sprint truth.

## 6. Immediate next steps
1. Owner reviews the **ARCH-009 DRAFT** (docs/coordination/
   instructions/): §1 rebuild-bulk for verdict_trades · §2
   placebo_method enforcement · §3 HC tool rev 2 captions · §4
   PROPOSAL: second-lens feed + data extension + H-004 successor —
   NEEDS Owner decisions (second XAUUSD H1 source; 2025 data; H-004
   approval). Do not finalize §4 or boot the Developer without them.
2. On approval: finalize ARCH-009, Owner commits, boots Developer in a
   NEW session: "Boot per CLAUDE.md, execute ARCH-009 completely,
   starting with T0. Session log every session."
3. Architect S9 duties will include: IVF for the rebuild determinism
   (rebuilt bytes == manifest hash), for placebo_method enforcement,
   and — if §4 approved — the second-lens overlap recomputation
   (threshold pre-registration BEFORE overlap, DEVQ-020). Drills
   first, clean control, HC with the rev-2 tool. Then REV-S9 → HC →
   Go/No-Go → GO-S9 (+retro) → REWRITE THIS → ARCH-010.
