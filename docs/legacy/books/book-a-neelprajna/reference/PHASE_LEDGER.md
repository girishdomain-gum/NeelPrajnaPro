# PHASE LEDGER — the one phase ladder (reconciliation)

- Written: 2026-07-23, at v5.9.0, after closing SSE Phase 6.
- Purpose: the repo accumulated THREE phase ladders written at different
  times (the overhaul plan, the Fable roadmap, and the SSE line). They
  disagree. This document reconciles them into ONE ladder and records what
  was completed, what was superseded, and what remains — so "which phase are
  we in?" has exactly one answer from now on.
- Rule going forward: **new phases are numbered on THIS ladder only.** The
  older documents stay as history; each carries its status here.

---

## 1. The one ladder (authoritative)

| Phase | What | Status | Evidence |
|---|---|---|---|
| A. Restructure 0–4 | repo, layers, StateHub/EventBus, GateBase registry, StrategyPortfolio, dashboard rewrite | **DONE** | code exists and ships in v5.9.0 |
| A. Restructure 5 | legacy removal | **RE-SCOPED — see §3.1** | grep shows 5 EG_ readers outside Engine/Gates |
| B. SSE Phase 6 (6a/6b/6c) | Sequential Strategy Engine | **DONE, CLOSED at v5.9.0** | `docs/plans/phase6_completion_record.md` |
| C. Phase 7 | Gate Recorder + Python replay (absorbs "NP Lab") | **DESIGNED, not started** | `docs/plans/phase7_gate_recorder_design_v1.0.md` |
| D. R6 long run | 3–6 months real-tick data + OOS window | **OPEN — the most valuable pending item, see §3.2** | files shipped 2026-07-20, never run |

Anything not in this table is either superseded (§2) or tech-debt
(`docs/tech-debt.md`), not a phase.

## 2. Supersessions (old plans, resolved)

### 2.1 `docs/plans/overhaul.md` — "Phase 6: New features"
The overhaul plan's Phase 6 was a UI feature list: equity/drawdown
sparkline, per-gate win-rate %, session clock strip, per-position BE and
partial-close buttons. **Superseded, not completed.** The name "Phase 6" was
later reused by the SSE line, which is the Phase 6 that actually happened.
The feature list items are NOT cancelled — they are unscheduled UI
candidates, to be pulled individually if wanted. None blocks anything.

### 2.2 `docs/NP_Architecture_Roadmap_v1.0.md` — "Phase 2: NP Lab"
The roadmap's Python research layer ("bar loader + counterfactual engine +
coarse screener") is **superseded by the Phase 7 Gate Recorder design**,
which reaches the same goal with a stronger method: instead of Python
approximating fills over exported bars, the EA records gate truth and
Python replays it, with a trade-for-trade acceptance gate (P7 §7 / D7).
The roadmap's key decision — "Python = research, NOT a second engine" —
is PRESERVED and strengthened (P7 D1: Python never computes a gate).

### 2.3 `docs/NP_Architecture_Roadmap_v1.0.md` — "Phase 1: hourly filter"
Not implemented (no `hours=` DSL key, no mask input in code). **Parked, not
superseded.** Rationale: it is a strategy-selection feature, and every
strategy-selection question is currently starved of data (§3.2). Revisit
after the R6 long run; if built, it enters the ladder as its own phase with
the usual gates. Note it would extend the SeqCodex grammar (a `HOURS=` key
would enter the normalised form and move hashes — plan it like BE in v5.9.0).

### 2.4 Roadmap "Phase 0: R6 long run"
Not superseded — **promoted** to ladder item D. See §3.2.

## 3. The two decisions

### 3.1 Restructure Phase 5 (legacy removal) — RE-SCOPED, exit check rewritten

Original exit check: *"grep proves zero EG_ reads outside EntryGates/Gates."*

That check is **unachievable as written**, and the codebase already knew it:
`docs/tech-debt.md` sanctions specific residual EG_ readers (TradeLogger for
deal-event timing; NPSU ordering-locked reads), and the SSE design doc §4
froze the bulletin as a sanctioned interface. Phase 6 then legitimately
added two more readers (`UniverseEngine._NPSU_SeqBar`, `SeqLive`) because
SequenceEngine's purity contract requires its CALLERS to build the gate
snapshot, and StateHub does not publish per-gate booleans.

**Decision (owner-ratified by adopting this ledger):** Phase 5 is complete
under a rewritten exit check:

> Zero EG_ readers outside Engine/Gates **except those on the CLOSED
> sanctioned-residual list below.** Adding a reader requires adding it to
> this list in the same commit, with a reason.

**The closed sanctioned-residual list (v5.9.0):**
| Reader | Why sanctioned |
|---|---|
| `Core/TradeLogger.mqh` | deal-event timing precedes `SH_PublishAll`; routing via StateHub skews research CSVs by one tick (tech-debt 2026-07-21 entry) |
| `Core/StateHub.mqh` / `StateHubPublish.mqh` | they ARE the bridge — EG_ is their input by definition |
| `Apps/UniverseEngine.mqh` | builds SSeqGateSnap + static-law reads; ordering-locked (runs inside the same tick, after EG evaluation, before publish) |
| `Apps/SeqLive.mqh` | builds SSeqGateSnap for the real path; same ordering argument |

The alternative — publishing all 26 gate booleans through StateHub and
migrating the four readers — remains a legal future change. It is VALUE-
IDENTICAL work with regression risk and no behavioural gain, so it lives in
tech-debt, not in a phase.

### 3.2 The R6 long run — revived as ladder item D, and scoped to today

This is the one item from the old plans that current work genuinely still
needs. Every open statistical question — is TrendPullback_Fibo real? do
sequences beat statics? BE on or off? hourly filter worth building? — is
unanswerable on 15–18 trade samples (ADR-004 amendment R1). The roadmap
said it plainly a week ago: *"nothing can be promoted survival-first at
n<100."* Still true.

Scope, updated for the post-Phase-6 world:
- 3–6 months XAUUSD M1, every-tick, plus a later UNSEEN window held for OOS.
- Roster: the R6 six PLUS the v5.9.0 `.seq` files PLUS `InpSeq_UnifyStatic`
  twins — one run feeds the survival ranking AND re-confirms the cadence
  result on a real sample AND gives the sequences their first fair test.
- Add the clean TrendPullback BE A/B (second `.seq`, BE=off, only diff).
- Constitution applies: survival-first ranking (maxDD → worst streak →
  ranging weeks → PF, never ROI), pre-registered predictions before looking.
- Practical: the July runs did ~22 days fine; 3–6 months every-tick is a
  long tester session — run overnight, and never compare across history
  re-downloads (roadmap standing risk).

**This is the recommended next action, ahead of Phase 7 code.** Phase 7's
own acceptance gate (reproduce existing books) gets stronger reference data
from this run for free.

## 4. Standing rules that carry across all phases

- ADR-001 layering; ADR-004 cadence rule + §5 acceptance-gate rule.
- ADR-004 amendment R1/R2/R3 (deterministic vs statistical; one-difference
  A/Bs; within-run comparisons only).
- Grammar and `seqgen.py` move together; management flags (RR/TRAIL/BE)
  belong in the hash.
- Version discipline per `docs/coding_guidelines.md`; §7 gates on engine
  changes.
- The sanctioned-residual list in §3.1 is CLOSED: additions are commits,
  not drift.

## 5. Bookkeeping done with this ledger

- `BOOT_PROMPT_post_phase6.md` should point here as the phase authority.
- `overhaul.md` and `NP_Architecture_Roadmap_v1.0.md` remain unmodified as
  historical documents; this ledger is the reconciliation layer above them.
