# S07 IMPORT PLAN — survey of F:\Fable, step 1 of the import-plan gate (A-027 §3)

Written by the Developer. `F:\Fable` was surveyed READ-ONLY — nothing there
was modified, and nothing has been copied yet. No file moves until the
Architect rules on this plan.

## 0. THE HEADLINE FINDING — READ THIS BEFORE THE FILE LIST

The master plan's guessed layout (`mql5/, supervisor/, npsu/, dashboard/,
docs/`) does not match the real tree, exactly as A-027 warned. But the more
important mismatch is structural, not naming: **`F:\Fable`'s own architecture
doc (`docs/NP_Architecture_Roadmap_v1.0.md`) describes its own EA as one
integrated machine, not a layered stack with a clean "thin execution shell"
at the bottom.** Its own diagram:

```
LOGICAL LAYER 1 — SIGNALS:    B1-B6 bias gates, T1-T9 trigger gates
LOGICAL LAYER 2 — EXECUTION:  EntryGates (BIAS x TRIGGER walk), TradeManager,
                               MoneyManager
SKELETON:                     NeelPrajna.mq5 events, Config.mqh, Dashboard,
                               loggers
```

I read `EntryGates.mqh` and `NeelPrajna.mq5` directly (not just their
headers): the "execution" layer's whole job is to walk the BIAS x TRIGGER
gate outputs and decide direction — it does not merely execute a decision
made elsewhere, it computes `Entry(D) = ALL enabled BIAS gates agree on
direction D AND ANY enabled TRIGGER gate fires a pulse in D` itself, inline.
`NeelPrajna.mq5`'s own header states the same formula as ITS entry model.
There is no file boundary in this codebase that separates "decides what to
trade" from "executes the trade" — AM-02's thin-hands split does not exist
here today. It would have to be built, not copied.

**CONSEQUENCE FOR THIS PLAN: I am not proposing to import any `.mq5`/`.mqh`
file from `NeelPrajna_v3.16.4/` as-is.** Every one of them either contains
pattern logic directly (the fourteen gate files), or is wired to gate state
closely enough that importing it would import the coupling too (`EntryGates.mqh`,
`NeelPrajna.mq5`, `AdvisorEngine.mqh`, `MetaSwitcher.mqh`, `UniverseEngine.mqh`,
`UniverseRoster.mqh`, `Dashboard.mqh`). I list all of them below, named
individually with sha256+size as instructed, but under FLAGGED, not PROPOSED.

**I am also surfacing a real ambiguity rather than guessing past it**: A-027
§2.1 says "`runtime/` imported from F:\Fable" and §3 asks for files "to be
imported," which reads as a copy-based transplant. But the mechanics-only
precedent this project already has — `qrf/kernel/observation/launcher.py`,
built from `F:\Fable\tools\np_agent.py` as "a CODE QUARRY for the MECHANICS
only... re-implemented here from scratch" — is NOT a copy; it is a rewrite
that borrowed shape, never bytes. Given what I found (no clean thin-hands
boundary exists in the source), I believe the SAME approach — survey Fable's
skeleton/execution mechanics (event loop shape, order-send wrappers, SL/TP/
trail primitives, magic-number scoping, logger structure) as reference, and
write `runtime/` fresh, obeying AM-02 from the first line — is more
consistent with BUILD LAW and AM-02 than importing files that would need to
be gutted of pattern logic after the fact. But this is your ruling to make,
not mine to assume. **STOP-AND-ASK, per A-027 §7: does "the transplant" mean
literal file import (then I need your file-by-file ruling on every FLAGGED
file below before touching any of them), or does it mean this project's usual
mechanics-only-quarry rewrite (in which case nothing here is "imported" and
the sha256 list below is provenance for what was consulted, not what
lands)?**

## 1. NeelPrajna_v3.16.4/ — the EA. FLAGGED, none proposed for import.

### 1a. Pattern/signal logic (B1-B6 bias gates, T1-T9 trigger gates) —
directly what AM-02 forbids in MQL5. Not proposed under any interpretation.

| File | Size (bytes) | sha256 |
|---|---|---|
| B1_NexisGate.mqh | 29812 | 8a08b12264a876d7dcbfc51b304e7694a2657d3725630416a2ce56669797a1b2 |
| B2_MTFCandle.mqh | 23573 | 64bf2c8d700847c82d5c2bf3bdbf752514008d52cc01dbb9bf7b0cc16f474211 |
| B3_KeyLevelGate.mqh | 48702 | 479ce42c9af6df749ccf004ab7569e8e014414eb342735f9da16dd7e702a4a5e |
| B4_SMCGate.mqh | 45988 | 0be319d9875b9f52f673032480247e2f934d7ad8f4daa4e9722c43a2e16280c2 |
| B6_RegChannelGate.mqh | 20496 | b0201136f907591d0654375a95c54abf6d6e60fe0ca256f863e1d7a10752a6a5 |
| T1_PatternGate.mqh | 42016 | 6318e041074be91ed37a4d774d1674bdd416f3b6b398be38085a8a44280fa27b |
| T2_AutoFiboGate.mqh | 54147 | 82feed66c7cf1f8f5979162584b465ec8d52f35c15d470161668784759fbc819 |
| T3_SweepFVGGate.mqh | 74201 | 52a46266b946b1376a772d3fb90f046faa0c5a1fc8bd05dfd3df887304e4bf60 |
| T4_TrendLinesGate.mqh | 62543 | b19af9cf367a2ee68057d5452703c7dac6cebd591e7f20d456954aefc77436ae |
| T5_TopographyGate.mqh | 45900 | 48e686eca69c32f098f0c628e326c740896fb8610d6fe0d52bc9aa44892f99cf |
| T7_MarketMetricsGate.mqh | 26486 | 276dfa27a00aa2c4ffd3a546b98cf2bb21954dd4d85d3a7c43829c2cfbf89b0f |
| T8_CMHCandleGate.mqh | 50048 | 2e180c1188812b14b304c83a7116f03703fc0a3e49580617a8af84eb9824e63f |
| T9_CCCHiddenGate.mqh | 46033 | 6c465f64e8064bbe76d5acca005addf34b41e12e376f6137bdde6d50afab5a3e |

### 1b. Directly coupled to the gates (orchestrates or reports on their
output) — flagged, not proposed:

| File | Size | sha256 | Why coupled |
|---|---|---|---|
| EntryGates.mqh | 29120 | afa731d7dec27c1705a581ac5cb1182e0c028721d84a7ce428e867880980dd70 | IS the BIAS x TRIGGER decision, inline — see §0 |
| NeelPrajna.mq5 | 17220 | 2869e433f5327cc3775adab2120e07ccf3b28becd87b6c66aa38fd02df769753 | EA entry point, states the same BIAS x TRIGGER formula as its own model |
| AdvisorEngine.mqh | 22286 | a12281e3b06f1958139e701728317d86cc4c97e85faa30b78ff2dbda5c9d5129 | "Live Advisor" — turns gate signals into human-readable trade advice |
| MetaSwitcher.mqh | 12342 | 4d9b7d204221c3841850ea7d45eb077a275f88b9affd37ea5170453451b8dcbc | Ranks/selects among strategy variants by live performance — a decision-making brain in MQL5 |
| UniverseEngine.mqh | 32068 | 7d02e2b7ce8b56b681ef13a79af14962756b2dce0b161c4902f090ab5f602d71 | Runs NPSU shadow universes (parallel gate-combo simulations) |
| UniverseRoster.mqh | 36541 | b210512f9a0ed40151493f6d41b5f1d52d51cc6baee5159ae49bc177aa851de1 | Strategy-combo roster driving UniverseEngine |
| **Dashboard.mqh** | 177353 | a02e900340abd7d78d9c3bf6c54d4a047b6baeb593202c6ecdd882467bcffb25 | **Confirmed by reading the click handler: has live BUY/SELL/CLOSE buttons (`BD_HandleBuy/Sell/Close`) and per-gate enable/disable checkboxes wired to `CHARTEVENT_OBJECT_CLICK`. This is a steering cockpit, not a mirror — the exact A-027 §7 stop condition ("the dashboard appears able to steer anything").** S07's dashboard must be a mirror only (§2.5); nothing here qualifies as one. |

### 1c. Execution primitives — closest to "thin hands," but still flagged
pending a read for gate-coupling (magic-number scoping, config values shared
with the gate layer via `Config.mqh`); I have NOT read these two closely
enough yet to certify them clean, and would rather say so than guess:

| File | Size | sha256 |
|---|---|---|
| TradeManager.mqh | 37007 | d2be200673dffb80c9d0e50a95a6d9f8f269e2cd8cefbeeb9da6ba979c668217 |
| MoneyManager.mqh | 22860 | d1b1eb28a259259038623eed9477529306badd8059a16ece651516a06cb2aff4 |
| VirtualBook.mqh | 30728 | 64f37f8774d820293d1f093a1e394c5313156a55d308c72b6c9e34b3a04bdd84 |

### 1d. Skeleton/utility — smallest and least coupled, still flagged (not
proposed) pending your ruling on §0's ambiguity:

| File | Size | sha256 |
|---|---|---|
| Config.mqh | 21834 | f9c368f6c95fd085b83036a7edbc071f2503dc905fac273ed9c72a3b253838fd |
| BuildTag.mqh | 1325 | 5262ba44544caf97859b6b7426c765b8ebc7539ca6f38905c5a84b26ed9468ad |
| ChartTheme.mqh | 7704 | 792914595eb005fb978239723e9a8338b1a7161271ed982f17fcbbec62b5a082 |
| CTsLogger.mqh | 19350 | 232a020d0122416588e9fbc83e59c6af131dbe239af9bdbd009e2ec61af756ee |
| EALogger.mqh | 5910 | f4411a9ab4d8955496721ea8bac002c7bbe2cff7f8a15b148f5f7ab794556482 |
| TradeLogger.mqh | 16291 | f496d40d3e9cb3e84860a6c0cecfabe4e82bed23e14d1e95cdc77add3f45abba |
| UniverseLogger.mqh | 23455 | 8ae90d7c172ee78bb029a09ed7ff35229bb1fb3448b374388a56c6a2a71ecec0 |

### 1e. Everything else in NeelPrajna_v3.16.4/ — NOT proposed, no ruling
needed, listed only as an inventory:

- `analyzer/*.py` (np_dashboard.py, np_post_validation.py,
  np_strategy_generator.py, np_trade_verifier.py, np_universe_analyzer.py) —
  Python-side research/verification tools that read the gate logic's own CSV
  log formats (NPT-2/NPSU-T1/S1/D1/A1), which don't exist in our system.
  We already own an independent verification layer (S05's Battery/
  registration/null-model) built for our own record formats — this would be
  a second copy of logic we already have, in a shape that doesn't fit our
  ledgers. Left behind.
- `Presets/*.set`, `NPSU_Strategies_R4_T8T9/`, `NPSU_Strategies_R5_B6/`,
  `NPSU_Strategies_R6_LONGRUN/` (`*.txt` DSL rosters) — parameter sets and
  strategy-combo rosters for the excluded gate/universe layer. Left behind,
  same reason as the gates themselves.
- `docs/*.md`, `methodology/*.md`/`.docx`, `HANDOVER.md`, `CLAUDE.md` — Fable's
  own project status/planning documents (its comms record, its own AI-role
  briefs). Not runtime code; this project keeps its own docs discipline.
  Left behind.
- `tests/test_LG_LogFlood.mq5`, `tests/test_MM_LastClosedShiftAt.mq5` —
  Fable's own drills for its own logger/MoneyManager modules; meaningless
  without those modules. Left behind.

## 2. Everything OUTSIDE NeelPrajna_v3.16.4/ — none proposed for import

- **`bridge/`** (528 files: `agent/`, `done/`, `jobs/`, `results/`, `running/`)
  — Fable's job-bridge automation history and results archive. Explicitly
  named in A-027 §3 as having no place here ("Fable's governance, job-bridge
  and whitelist machinery has no place here"). Left behind entirely, not
  individually catalogued — it is job-run history, not source.
- **`ivf/`** and **`ivf-reference/`** (141 files total) — Fable's own
  "Independent Verification Framework" (backtest-journal re-derivation
  checkers, per `IVF_MU_RULES.md`'s IND-1..4 rules). This plays the same
  role S05's Battery/null-model/registration already plays for us, in a
  shape built for Fable's own CSV/journal formats. A second copy of logic we
  already own, per the same principle as `analyzer/`. Left behind.
- **`kit/`** — bootstrap templates for starting a NEW Fable-pattern project
  (`NEW_PROJECT_BOOTSTRAP.md`, `EXISTING_PROJECT_ADOPTION.md`). Not runtime
  code, not applicable to an already-running project. Left behind.
- **`comms/`** — Fable's own comms record (its `architect.md`/`developer.md`/
  `STATE.md`/etc.). Governance, explicitly out of scope, same as `bridge/`.
  Left behind.
- **`tools/`** (`np_agent.py` and its drills) — ALREADY consulted, mechanics
  only, in S03 (`qrf/kernel/observation/launcher.py`'s own docstring
  documents this). No further action; not proposed for import now, since
  nothing new is needed from it for S07 as currently understood.
- Root-level Fable docs (`BOOT_PROMPT_ARCHITECT.md`, `BOOT_PROMPT_DEVELOPER.md`,
  `DEVELOPER_CHAT_PROMPTS.md`, `GIT_WORKFLOW.md`, `JOURNEY.html`,
  `IVF_MU_ADOPTION.md`, `deploy.bat`, `make_kit.bat`) — Fable's own
  operating instructions for itself. Left behind.
- `.git/`, `.claude/`, `backups/` — obviously excluded, not source.

## 3. What I could NOT determine the purpose of

Nothing, this pass — `NP_Architecture_Roadmap_v1.0.md`'s own layer diagram
plus reading `EntryGates.mqh`/`NeelPrajna.mq5`/`Dashboard.mqh` directly
answered every question I had about what each file does. The open question
in §0 is not "what is this file for" but "what does 'the transplant' mean
given what these files actually are" — a scope question, not a comprehension
gap.

## 4. Summary — what I am asking you to rule on

1. **The interpretation question in §0**: literal file-copy import (then
   rule file-by-file on §1a-1d below, understanding that 1a and most of 1b
   are pattern logic and 1c/1d are unverified-clean at best), or a
   mechanics-only-quarry rewrite matching this project's existing precedent
   and BUILD LAW (then nothing is imported, and I design `runtime/` fresh
   using this survey as a map of what exists and how it is shaped).
2. If literal import: a ruling on `Dashboard.mqh` specifically — it cannot
   become S07's mirror dashboard without being stripped of every button
   handler, which is close enough to a rewrite that I'd rather know your
   intent before starting.
3. Confirmation that `bridge/`, `ivf/`, `ivf-reference/`, `kit/`, `comms/`,
   `analyzer/*.py`, `Presets/`, `NPSU_Strategies_*/`, and Fable's own docs
   are correctly left out under either interpretation — I believe they are,
   for the reasons stated in §1e and §2, but this is exactly the kind of
   read I'd rather have checked than assumed.

No file has been copied. `F:\Fable` was only read. Waiting for your ruling
before step 2 of the gate.
