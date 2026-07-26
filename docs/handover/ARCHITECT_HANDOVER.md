# QRF — Architect Handover (Fable → next Fable session)
Rewritten 2026-07-26 at the **GENERATION 1 → 2 boundary** (GO-S10 + FREEZE)
Author: architect (fable)

## 0. WHERE YOU ARE
**Generation 1 is COMPLETE and FROZEN.** Freeze note
01KYEMDYSFRXWZ4TSFDK2BW7TJ (producer human:girish), journal **84
records chain GREEN**. Sprints 1–10 closed (GO-S1..S10). Read, in this
order: docs/reports/GENERATION_1_FINAL_REPORT.md (the permanent
reference — architecture, verdict record, tally 17/4, limitations,
Gen-2 recommendations), then docs/planning/GEN2_PLANNING.md (six
charter questions AWAITING THE OWNER'S ANSWERS). **Nothing happens
until the Owner answers them** — the pause is his own prescription. Do
not draft ARCH-011 before the answers arrive; when they do, they ARE
the Generation-2 charter and ARCH-011 is drafted from them for his
review. inbox/OPEN empty (DEVQ-001..024 CLOSED). The Developer is
idle; its next boot is the first Gen-2 session.

## 1. Identity and rules (unchanged, proven over 10 sprints)
You are Fable, Architect. Owner Girish (git bash; commands COMPLETE,
BASH-READY, PLAIN). You write on main only in Owner-declared write
windows; NEVER developer code (qrf/, scripts/); ivf/** is yours; ADRs
are yours (DEVQ-024 held that boundary — keep it). Developer = Claude
Code, new session per task, worktrees. **FREEZE DOCTRINE (binding):
no new framework subsystems. Generation 2 builds knowledge — new
concept families arrive as detectors + sealed hypotheses +
applications on frozen machinery.** The one pre-flagged possible
exception: a VIRGIN-unlock ceremony IF the Owner's Q5 answer requires
it — and only via his explicit approval.

## 2. The frozen estate (verify, don't trust — refs/journal/sessions)
Ledger: 84 records; every dataset rebuilds sha-assert-equal from
committed CSVs (ivf/mt5/) via the rebuild scripts. Reserves: 2024
01KYB4SSD9… and 2025 01KYDE784NHY…, both untouched, typed-phrase
protected. Lens: 01KYE3WCKK40PNJ8JEATQ4XTNT (Exness, tier=broker,
0.9544; sealed procedure in note 01KYE3BBE2…). Clock doctrine: broker
server time, piecewise US-DST alignment. Trial ledger complete
(ADR-011): smc.fvg 1004 (α≈5e-5, deprioritized), seasonality.calendar
2. Verdicts: 3 FAIL, 1 INSUFFICIENT, 0 promotions — reproducible to
the last digit (IVF S8/S9/S10 all GREEN, drills all CAUGHT). Wave-2:
39/500 leads = "the trend in 39 costumes" (Owner's read, GO-S10);
candidates for a Gen-2 conversation, NOT claims. HC tooling:
generation-4 rev-2 (label-driven, MONX). 853 tests · firewall GREEN.

## 3. Standing rules distilled (the 21 findings' residue)
Verify prose against real artifacts and real data; tripwires on your
own criteria, honored when they fire on you; predictions recorded so
they can fail; calendar/session/seam arithmetic from data, never
convention; rehearse every check end-to-end on raw data before
shipping; machine-verify numerics before rulings; read back every
write; drills before checks, clean control; DEVQs over guesses —
refusal at a boundary is the system's finest behavior. Tally
Architect 17 / Developer 4: keep counting honestly, including
yourself. The full lessons live in the Final Report §3.

## 4. Next actions (in order, gated on the Owner)
1. Owner reads the Final Report + answers GEN2_PLANNING.md Q1–Q6 (his
   pace; do not prompt beyond a gentle reminder if asked).
2. You draft ARCH-011 (the first Gen-2 instruction) FROM his answers,
   as DRAFT with ◆ decisions where his answers leave choices; he
   approves; only then the Developer boots ("Boot per CLAUDE.md,
   execute ARCH-011 completely, starting with T0. Session log every
   session.").
3. The rhythm thereafter is unchanged and proven: instruction →
   Developer sessions (DEVQs ruled in write windows) → IVF (drill
   first) → HC → REV → Owner Go/No-Go → GO(+retro) → REWRITE THIS.
Generation 1's last words, the Owner's: the framework no longer needs
to know what the concept is — it already knows how to evaluate
scientific claims about it. Your job now is to keep that true.
