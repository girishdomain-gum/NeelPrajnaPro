# NeelPrajna Development Workflow v1.0
**Hybrid approach: Claude Chat (think) + GitHub + Claude Code (build) + Compile/Backtest script (verify)**
Owner-issued companion to FABLE_COMMS_STANDARD.md · 2026-07-21

---

## 1. Executive Summary

We develop NeelPrajna with two Claude environments, each doing what it is best at:

- **Claude Chat** = the architect's table. Deep thinking, design decisions, reviews, docs, mockups.
- **Claude Code** = the workshop. Executes agreed plans on the real repo, compile-checked, committed to Git.
- **The compile/backtest script** = the referee. Every change must compile and must not silently change trading behavior.

Rule of thumb: **decide in Chat, execute in Code, prove with the script.**

---

## 2. Problem Statement

Why a defined workflow at all?

- The EA is ~21,600 lines across 28 files. Zip-in-chat editing cannot verify compilation, loses history, and resets context every session.
- A live-money EA cannot tolerate "it probably still works." Refactors need empirical proof (baseline backtest diff), not code reading.
- Architecture decisions made ad-hoc in chat get lost. They must land in the repo as documents Claude Code can read.

---

## 3. The Three Pillars

### Pillar A — Claude Chat (thinking layer)
Use Chat for work where discussion beats execution:

| Use Chat for | Example |
|---|---|
| Architecture & design decisions | StateHub/EventBus design, layer boundaries |
| Trade-off analysis | Tabbed panel vs. two-column dashboard |
| Code review of a focused diff | Paste/attach one gate's migration diff |
| Documentation drafting | ADRs, design docs, this document |
| Data analysis | Strategy Tester / NPSU exports → xlsx analysis |
| Visual mockups | Dashboard layout concepts before coding |

Output of every Chat session that matters: a **written artifact committed to the repo** (ADR, plan, spec). If it isn't in the repo, it doesn't exist.

### Pillar B — GitHub repo + Claude Code (execution layer)
Use Claude Code for work where hands beat talk:

| Use Claude Code for | Example |
|---|---|
| Multi-file refactors | Phase 1 folder restructure, include-graph fix |
| Repetitive migrations | Moving 14 gates onto GateBase, one commit each |
| Rewrites with verification | Dashboard rewrite, compile after every edit |
| Bug hunts | Reproduce → isolate → fix with tester runs |
| Mechanical cleanups | Encoding checks, dead-code removal |

Repo conventions:
- `main` is always compiling and baseline-clean. Work on branches: `phase1-restructure`, `gate-b1-migration`, etc.
- One logical change per commit. Gate migrations: **one gate per commit** (bisectable).
- **No floating source edits in the primary checkout.** Review/demo conveniences (e.g. flipping `InpUseNewPanel`) go through chart inputs (F7, per-chart persisted) or an explicit commit — never an uncommitted source tweak. A dirty primary makes committed≠compiled, the exact ambiguity the OnInit build marker exists to catch (and which the marker cannot itself detect — MQL5 has no compile-time git state).
- **Verify the worktree base before any work.** A session's first action is confirming its base equals the current phase branch tip: `git rev-parse HEAD` vs `git rev-parse origin/<phase-branch>`. A worktree cut from a stale base (e.g. a session opened at a Phase-3 commit while the phase branch has advanced through Phase-4) silently builds features on modules that do not exist on that base — invisible until the expected files turn up missing. If behind and it is a clean fast-forward with no unique commits, `git merge --ff-only <phase-branch>` first; otherwise stop and re-cut. (Companion to the primary-checkout rule above; both guard committed≠intended.)
- `CLAUDE.md` at repo root contains: project overview, layer rules, FABLE_COMMS_STANDARD content, and the validation rules from §4. Claude Code reads it automatically every session — this is how decisions persist.
- `docs/adr/` holds Architecture Decision Records. `docs/plans/` holds phase plans from Chat.

### Pillar C — Compile/Backtest script (verification layer)
Two scripts, run locally (Claude Code can invoke them):

**`tools/compile.bat`** — compiles the EA headlessly:
```bat
@echo off
set ME="C:\Program Files\MetaTrader 5\metaeditor64.exe"
%ME% /compile:"%CD%\NeelPrajna.mq5" /log:"%CD%\tools\compile.log"
findstr /C:"0 errors" tools\compile.log || (type tools\compile.log & exit /b 1)
echo COMPILE OK
```

**`tools/backtest.bat`** — runs a fixed, deterministic Strategy Tester pass:
```bat
@echo off
set MT="C:\Program Files\MetaTrader 5\terminal64.exe"
%MT% /config:"%CD%\tools\baseline.ini"
REM baseline.ini pins: symbol, period (e.g. 2025.01–2025.06), model,
REM deposit, preset file, and Report=tools\report_current
```
Then compare `report_current` deal list against the frozen `tools/report_baseline` (a small diff script or Chat/xlsx comparison).

Baseline rules:
- Freeze `report_baseline` **before** starting any refactor phase.
- Phases 1–3 (restructure, StateHub, GateBase): deal list must be **byte-identical**.
- Phases 4–5 (dashboard, new features): deal list must be identical unless a behavior change is intentional and documented in the phase plan.
- Re-freeze the baseline only via an explicit commit that says why.

---

## 4. The Loop (how a change actually flows)

```
 CHAT                          REPO / CLAUDE CODE                 SCRIPTS
 ────                          ──────────────────                 ───────
 1. Discuss & decide   ──►  2. Commit plan/ADR to docs/
                            3. Branch; Claude Code executes  ──► 4. compile.bat
                                                              ──► 5. backtest.bat
                            6. Diff vs baseline: PASS?
                               │ yes                 │ no
 8. Review diff in Chat ◄──  7. Push branch / PR      └─► back to 3 (fix)
 9. Approve             ──►  10. Merge to main; next phase
```

Small fixes (typos, comment edits) may skip steps 1–2 and 8–9 but never skip 4–5.

## 5. Session Protocols

**Starting a Chat session:** state the goal in one line; attach or reference the relevant repo files/ADRs (Chat has no memory of the repo). End by writing the decision artifact.

**Starting a Claude Code session:** it reads `CLAUDE.md` automatically. Point it at the current plan file ("execute Phase 3, gate B2, per docs/plans/overhaul.md"). It must run compile.bat after every substantive edit and backtest.bat before declaring a task done.

**Handoffs are always files, never memory.** Chat → Code: plan/ADR in docs/. Code → Chat: a diff, a report file, or a pushed branch.

## 6. Roles Cheat Sheet

| Task | Where |
|---|---|
| "Should EventBus be sync or queued?" | Chat |
| "Migrate B2 to GateBase" | Claude Code |
| "Why did the tester diff change?" | Claude Code reproduces → Chat analyzes if subtle |
| "Analyze NPSU R6 results" | Chat (xlsx skill) |
| "New dashboard widget concept" | Chat mockup → plan → Claude Code builds |
| "Panel misaligned by 3px" | Claude Code |

## 7. Risks & Mitigations

- **Tester nondeterminism** (ticks model, history quality): pin the model and date range in baseline.ini; use "Every tick based on real ticks" with a cached history set; never compare across history re-downloads.
- **Baseline drift**: baseline re-freeze requires its own commit with justification.
- **Decisions lost between environments**: mitigated by the files-only handoff rule and CLAUDE.md.
- **Scope creep inside Claude Code sessions**: one plan file, one phase, one branch per session.

## 8. Key Takeaways

1. Chat thinks, Code builds, scripts prove — never blur the three.
2. Nothing is "decided" until it is a file in the repo.
3. Nothing is "done" until compile.bat and backtest.bat pass against the frozen baseline.
4. One gate / one logical change per commit keeps a 21k-line refactor bisectable and safe.

## 9. Next Steps

1. Create the GitHub repo; commit v3.16.4 as-is (tag `v3.16.4-baseline`).
2. Add `CLAUDE.md` (this doc's rules + FABLE_COMMS_STANDARD) and `tools/` scripts; adjust MT5 paths.
3. Run backtest.bat once and freeze `report_baseline`.
4. Commit the overhaul phase plan to `docs/plans/overhaul.md`.
5. Begin Phase 1 in Claude Code.

## 10. Versioning (semantic, phase-aligned)

Adopted at **v4.3.0**. Semantic versioning tied to the overhaul phases:

- **MAJOR** — architectural era. `4.x` = the Phase 1–3 overhaul world (layers,
  StateHub/EventBus spine, GateBase, StrategyPortfolio). `5.0.0` lands when
  Phase 5 removes the legacy world.
- **MINOR** — a completed Phase-4 session milestone. Map: `4.0` Phases 1–3
  (retroactive) · `4.1` P4-1 chrome · `4.2` P4-2 LIVE · `4.3` P4-3 CTRL ·
  `4.4` D2 · `4.5` S15b · `4.6` VIRT UNIV · `4.7` SCOPE · `4.8` P4-V visuals ·
  `4.9` cutover · `5.0` Phase 5 complete.
- **PATCH** — hotfix / tweak, no new feature (the empty-roster crash = `4.0.1`).

**Two firm rules:**

1. **A version bump rides the milestone commit** — same commit that lands the
   feature, never a separate "bump version" commit.
2. **Every bump adds a `CHANGELOG.md` entry** (newest first, one short honest
   paragraph). No entry, no bump.

**What to change on a bump** (single source is `Core/Config.mqh`): `EA_VER_MAJOR/
MINOR/PATCH`, `EA_VERSION` (full triplet), `EA_VERSION_SHORT`, and the
`#property version` literal in `NeelPrajna.mq5` (MQL5 needs a literal there and
it sits above the Config include, so keep it in lockstep — it is `MAJOR.MINOR‖
PATCH`, e.g. `4.3.0 → "4.30"`; display-only, CHANGELOG holds the true triplet).
Also update `EA_BUILD_SESSION`/`EA_BUILD_BRANCH` for the OnInit marker. All
in-code surfaces (both panels, journal) read `EA_VERSION`, so they follow
automatically.
