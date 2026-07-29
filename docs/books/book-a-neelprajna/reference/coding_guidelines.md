# NeelPrajna Coding Guidelines v1.1
Owner-issued. Applies to all MQL5 (.mq5/.mqh) and Python (analyzer/) code, and to any AI
(Claude Code, Chat) writing code for this repo. Include this file in CLAUDE.md.

Philosophy: these are GUIDELINES for better structure, not mandates. Size numbers are
symptom checks — a review trigger that asks "does this file have more than one job?",
never a reason to block or artificially split good code. Judgment wins over numbers;
when deviating, a one-line note in the commit is appreciated but not required.

The only firm items in this document are the SAFETY GATES in §7 (compile clean,
baseline behavior diff, downward-only layer includes). Those protect the live account
and the refactor's validation method — they are process safety, not coding style.

---

## 1. Size guidance (review triggers, not limits)

| Unit | Comfortable | Worth a second look above | Rationale |
|---|---|---|---|
| Source file (.mqh/.mq5/.py) | ≤500 lines | ~800 lines | Reviewable in one sitting; hints at one responsibility |
| Function | ≤40 lines | ~80 lines | Fits on one screen; testable |
| Function parameters | ≤4 | ~6 | More → consider a struct (e.g. GateContext) |
| Nesting depth | ≤3 | ~4 | Deeper → consider extract-function or early-return |
| Line length | ≤100 chars | ~120 chars | Side-by-side diffs |
| Composition root (NeelPrajna.mq5) | ≤300 | ~400 | Wiring only, no logic |

Crossing a trigger means: pause and ask whether the unit has grown a second
responsibility. If the honest answer is "no — it is one cohesive thing that happens to
be long" (a complex gate's signal core, for example), keep it and move on. An honest
600-line file beats two artificial 300-line halves.

Existing large files (Dashboard 3506, T3 1609, T4 1283, T8 1151, T2 1150, B3 1088,
T9 1054, T5 1041, B4 976, T1 862) simply carry a standing intent: prefer shrinking
them over growing them, and let the overhaul phases split them along responsibilities
as planned. No freeze, no penalty — just direction.

Splitting guidance: split along responsibilities, not line counts — a gate splits into Signal core / Drawing / State-publish before it splits into "part1/part2". Avoid `Utils.mqh` dumping grounds.

## 2. Structure & responsibility (the rules that prevent big files)

- **One module, one job.** A file's header comment must state its single responsibility in one sentence. If the sentence needs "and", split the file.
- **Layer rules are law** (ADR-001): includes point downward only. UI includes Core only; gates include Core only; no file includes anything from a layer above it.
- **No new globals.** Module state lives in a single `static`-style struct per module (e.g. `SDashboardState g_bd;`). The EG_* bulletin board is legacy, scheduled for deletion (Phase 5) — never add to it.
- **All cross-module interaction** goes through StateHub (read) or EventBus (write/command). Direct cross-module function calls are allowed only downward within the same layer.
- **Magic numbers**: any literal used twice, or any literal with a unit (px, points, seconds, %) gets a named constant next to its section, with the derivation shown (the `64 = 3+58+3` style in Dashboard v2.8 is the model — keep that habit).

## 3. MQL5-specific rules

- **UTF-8 only**, enforced (existing repo mandate). ASCII in UI strings where terminal fonts are unreliable (learned: v2.8.1 glyph fix).
- Compile with `#property strict` semantics in mind; aim for **0 errors, 0 warnings** (errors are a safety gate, §7; warnings are strongly preferred clean but may be accepted with a commit note).
- **Closed bars only** for signal logic unless an ADR says otherwise (existing project rule — forming-bar data is nondeterministic in the tester).
- Every `OnTick`-path function must be **cheap or cached**: per-bar caches keyed on bar time (existing gate pattern); no history scans per tick.
- Chart objects: always prefixed (`BD_PFX` pattern), always deleted in Deinit, write-on-change only (no redundant ObjectSet calls per tick).
- Trade operations only via TradeManager; only TradeManager touches CTrade. Magic-number ranges are allocated in one table in Config.
- No `Sleep()` in EA code paths; no blocking calls in OnTick/OnChartEvent.
- Handle every error path: any function returning bool/ticket is checked; failures publish `exec.blocker` or an `EVT_*` — never silently ignored (BTCUSDT lesson).

## 4. Naming

- Modules: `PascalCase.mqh`. Functions: `ModulePrefix_PascalCase` (`TM_OpenPosition`, `SP_ApplyStrategy`). File-private helpers: no prefix, marked `// private`.
- Structs `S` prefix (`SEAState`), enums `E` prefix with UPPER members (`ECommand::CMD_BUY`).
- Booleans read as assertions: `isEnabled`, `hasPulse`, `spreadOK`.
- Python: PEP 8, snake_case, one script = one purpose = runnable with no arguments (existing v3.16.1 rule).

## 5. Comments & docs

- File header: responsibility sentence + owner invariants (the VirtualBook "NEVER touches real orders" style is the model — invariants in headers, in caps).
- Comment the **why**, not the what. Version history goes to CHANGELOG.md, never into header comments or the .mq5 property line (Phase 0 migrates the existing mega-comment).
- Every public function in Core/ and Engine/: one-line contract comment (inputs, outputs, side effects, events emitted).

## 6. Guidance for Claude Code sessions

1. Read `CLAUDE.md` (includes this file) and the referenced phase plan before editing.
2. Treat §1 as design taste: prefer small cohesive units; when a generated file wants to grow past a trigger, briefly consider a responsibility split — but choose whichever is genuinely better code.
3. Run `tools/compile.bat` after every substantive edit; `tools/backtest.bat` before declaring done (safety gates, §7).
4. Prefer one logical change per commit; one gate per commit during migrations. Commit message: what + why + baseline status (`baseline: identical` / `baseline: intentional diff — <reason>`).
5. When touching a legacy large file, lean toward leaving it smaller or better-factored than found — but never contort a fix to satisfy a number.
6. Avoid drive-by refactors outside the session's phase scope — note findings in `docs/tech-debt.md` instead.
7. When guidance here conflicts with older code patterns, this doc wins; when it conflicts with ADR-001, the ADR wins; flag conflicts to the owner.

## 7. Safety gates (the only firm items)

These are not style rules — they protect the live account and the refactor's validation method:

1. **Compiles with 0 errors** (`tools/compile.bat`) before any commit.
2. **Baseline behavior diff** (`tools/backtest.bat` vs frozen baseline) passes per the phase plan's rules before merge to main.
3. **Layer includes point downward only** (ADR-001) — upward includes reintroduce the coupling the overhaul exists to remove.

Everything else in this document is advisory. `tools/check_limits.py` (Phase 0) reports on §1 triggers as information for the commit author — it never fails the build.
