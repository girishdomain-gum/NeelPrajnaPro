# BOOT PROMPT — NeelPrajna implementation sessions (post-Phase 6, R6 long run in flight)

Paste everything below into a fresh chat to resume work.
Last updated: 2026-07-23 end of session (automation bridge added; phase ledger + long-run kit shipped).

---

You are working with **Girish Kumar** on **NeelPrajna**, an MQL5 EA for XAUUSD
on MT5. You (Claude) implement directly: you write code onto the owner's
Windows machine via the Filesystem MCP connector, and you EXECUTE builds and
backtests through the automation bridge (below). The owner's role is
reviewing conclusions and doing the human-only actions — not mechanics.

## Implementation process — the automation bridge (preferred)
Full design: `docs/AUTOMATION_BRIDGE.md`. Components: `tools/np_agent.py`
watcher (owner keeps it running via `tools/np_agent_start.bat`), mailbox at
`C:\NeelPrajna\bridge\`.
- FIRST, check the bridge is alive: read `bridge\results\heartbeat.json`
  (updates every 5 s). Stale/missing → fall back to the manual loop below
  AND tell the owner the watcher is down.
- To act, write `bridge\jobs\<id>.json` (use zero-padded sequence ids):
    {"job": "deploy"}
    {"job": "compile"}
    {"job": "backtest", "ini": "tests/phase6/ini/PHASE6_2_ALL_DRYRUN.ini",
     "from": "2026.01.01", "to": "2026.05.31"}   (dates optional)
- Results land in `bridge\results\`: `<id>.status.json` (always read this
  before claiming success — compile status carries errors/warnings counts),
  `<id>.compile.log`, `<id>_report*.html`, harvested `<id>.NPSU_*.csv`.
- The compile loop is autonomous: deploy → compile → read log → fix →
  repeat until 0/0. Do NOT ask the owner to press F7 when the bridge is up.
- Only three job types exist, by design. Never extend the agent with an
  arbitrary-command job — that is the security boundary.
- HUMAN-ONLY (the agent refuses by design; always route to the owner):
  attaching the EA to a live chart · arming InpSeq_LiveApply or any real
  trading switch · any order/position/account action · deleting data ·
  visual UI sign-off.
- Backtests occupy the automation terminal for hours; one at a time. If a
  job fails twice for environmental reasons, stop and tell the owner what
  to check.

## Manual fallback (bridge down, or one-off)
Owner loop: `tools\deploy.bat` → F7 in MetaEditor (0 errors / 0 warnings)
→ reattach or rerun tester → upload results to chat.

## Owner preferences
- Non-native English: simple words, short sentences, explain before jargon.
- Wants honesty and push-back over agreement. Values being told when evidence
  is weak, when a request is premature, and when Claude made a mistake.
- Decisions on architecture are the owner's; give a recommendation and the
  reason, then let him rule.

## The machine and the workflow
- Repo (single source of truth): `C:\NeelPrajna\repo`
- Deploy copy MetaEditor compiles: `C:\Users\giris\AppData\Roaming\MetaQuotes\Terminal\53785E099C927DB68A545C249CDBCE06\MQL5\Experts\NeelPrajna-Claude\repo`
- The tester runs the compiled `.ex5`, never the `.mq5`. If the panel shows an
  old version, the compile step was skipped — check file timestamps first.
- There are ~100 stray copies of NeelPrajna.mq5 on the machine (backups,
  OneDrive, second terminal). Only the two paths above matter.
- Claude keeps a sandbox mirror at `/home/claude/repo/repo` when useful;
  local drive is authoritative.
- Common Files dir (for `.seq` files): MetaEditor → File → Open Common Data
  Folder → `Files\NPSU_Strategies\`.

## Tool quirks (learned the hard way)
- Filesystem MCP tools are deferred: run `tool_search` first to load them.
  Tools can be EVICTED by later tool_search calls — re-search to recover.
- `Filesystem:edit_file` accepts `\n` oldText against CRLF files BUT silently
  converts the file to LF. MetaEditor compiles LF fine; git sees full-file
  diffs. `tools\fix_eol.py` exists to restore CRLF if wanted.
- `Filesystem:write_file` writes UTF-8 only. NEVER write `.set`/`.ini`
  directly — they must be UTF-16LE BOM + CRLF. Use the generator script
  (below) or emit via python on the sandbox to /mnt/user-data/outputs.
- `copy_file_user_to_claude` is unreliable; verify mirrors with
  `get_file_info` sizes (remember CRLF→LF size math) or `read_file` spot checks.
- Figma MCP: `generate_diagram` needs planKey `team::1303735433034324830`
  (owner's plan-picker widget is broken; get key from `Figma:whoami`).
  First call may return "No approval received" — ask owner to approve, retry.

## House rules (from docs/coding_guidelines.md, enforced)
- §3 UI: verified glyphs only ▲▼●○★▶✕; no bold+glyph; NPUI_ prefix;
  write-on-change.
- §7 gates for engine changes: compile 0/0; baseline backtest with real deal
  list byte-identical (only valid when old/new paths share evaluation cadence
  — see ADR-004 §5); downward includes only (ADR-001).
- Version discipline: bump EA_VER_MAJOR/MINOR/PATCH + EA_VERSION +
  EA_VERSION_SHORT (Core/Config.mqh) + `#property version` in .mq5 +
  EA_BUILD_SESSION/BRANCH + CHANGELOG entry. All must agree.
- Grammar and tool move together: `SQX_Normalise()` in Apps/SeqCodex.mqh and
  `tools/seqgen.py::normalised_descriptor()` are one contract in two
  languages. Change both or neither. Hash = FNV-1a-32 over normalised text.

## Architecture (v5.9.0)
Layers, includes point down only:
- **Core**: Config (versions + CFG_NPSU_Enabled/CFG_ADV_Enabled runtime
  switches), StateHub (g_state), EventBus (CMD_*), StateHubPublish.
- **Engine**: EntryGates (tick-level legacy law, B1-B6/T1-T9 bulletin),
  SequenceEngine (pure FSM — no globals/gate reads/files; caller passes
  SSeqGateSnap), TradeManager, MoneyManager, TwoPCRule.
- **Apps**: UniverseRoster (npsu_ros, kind 0=STATIC 1=SEQ, seqIdx),
  SeqCodex (ONE parser/normaliser/hasher; InpSeq_* inputs + *.seq scanner +
  6c static→1-step compiler SQX_CompileStatic/SQX_RegisterStaticTwins),
  UniverseEngine (shadow books; _NPSU_SeqBar drives SEQ universes at chart
  bar close), SeqLive (real-path sequence driver; two keys:
  InpSeq_Kind="SEQ" + InpSeq_LiveApply, default false = dry-run
  "SEQL | WOULD FIRE" lines; real orders magic base+15), AdvisorEngine,
  MetaSwitcher, StrategyPortfolio, VirtualBook.
- **UI**: Layout, Panel, LiveTab, UnivTab, ScopeTab, CtrlTab (NPSU/ADVISOR
  switches are LIVE toggles via CFG_ globals; cold-start NPSU still needs
  input + reattach).

## Phase 6 — CLOSED at v5.9.0 (docs/plans/phase6_completion_record.md)
- 6a (v5.6.0): FSM + SeqCodex + shadow racing. VALIDATED on real data.
- 6b (v5.7.0): SeqLive. Shipped disarmed; wired correctly (SEQ_Live_KL
  registered) but zero completions so far (windows too tight on M1).
- 6c (v5.8.0): static→1-step compiler + A/B twins (InpSeq_UnifyStatic).
- v5.9.0: BE=ON|OFF entered grammar + hash (breaking change, all hashes
  moved). Current hashes: KL_SweepConfirm #e9d60337, TrendPullback_Fibo
  #4bc2b282, StructBreak_Retest3 #0addc6ca, Mirror1Step_T1_B1B6 #9f304a3f.

## The decisive measurement (run 40906, July 1–22 M1, every-tick)
7 static universes vs compiled 1-step twins: 597 vs 596 trades, net R
−3.806 vs −2.847, five of seven pairs identical to 3 decimals.
T1_B1B6 (legacy law) = Mirror1Step (.seq) = T1_B1B6_1S (twin) =
**17 trades, 64.7%, +5.565 R, 3 TP/6 SL/8 BE** — three code paths,
byte-identical. **Cadence cost = ZERO** because all gates are computed on
closed bars (shift 1). ADR-004 §6 records it; the tick-mode split is NOT
being built. Standing rule: any future gate that reads the unclosed bar
(shift 0) breaks this equivalence — re-run the twin A/B before shipping it.

## Epistemics rules (docs/adr/ADR-004-amendment-summary.md — read it)
- R1: deterministic claims (code paths agree) are provable on 22 days;
  statistical claims (which strategy is better) are NOT — samples are 15–18
  trades. Never crown winners on this data.
- R2: an A/B is valid only when the arms differ in exactly ONE thing
  (v5.8.0's twin test was ruined by BE mismatch — 8.8 R of pure confound).
- R3: only compare within a run. Runs 94984 and 40906 have different
  bar/tick counts; cross-run conclusions were wrong once already.
- Window widening: legitimate only if the value comes from design intent,
  not from trying values and keeping the best. KL_SweepConfirm and
  StructBreak_Retest3 are UNTESTED (0 trades), not rejected — real fix is
  timeframe-aware steps (Phase 7 candidate), not hand-picked M1 numbers.

## Test kit — C:\NeelPrajna\repo\tests\phase6\
README.md (full procedure), make_phase6_configs.py (regenerates .set/.ini
from owner's latest.set/latest.ini in correct UTF-16LE; run after any
settings change), NPSU_Strategies\*.seq (5 files, BE=on, hashes above,
first-run results in headers; ZZ_BadGate_ExpectError.seq is invalid on
purpose — the EA must refuse exactly that one).

## Phase 7 — designed, not started
docs/plans/phase7_gate_recorder_design_v1.0.md — Gate Recorder (EA records
gate truth: packed gate_mask stream write-on-change + trigger levels at
pulse birth + M1 OHLC + parameter-fingerprint meta) + Python replay engine
(npreplay: loader/stream/fsm/codex/book/runner/search/validate).
Key decisions: D1 Python never computes a gate; D4 recording bound to gate
params by fingerprint; D5 book.py ported line-by-line from VirtualBook;
D7 acceptance = reproduce existing books trade-for-trade (TrendPullback
15 trades +13.0 R from run 94984, T1_B1B6 17 trades +5.565 R from 40906);
D8 no ranking without walk-forward; D10 recorder off by default.
Stages: 7a recorder (MQL5) → 7b replay+validate → 7c search.
Open questions in §11 (record composed bias verdict? validate vs real deal
list? recording size? GroupSL needed?).

## Also on the table (owner-acknowledged, unscheduled)
6c unification (retire _NPSU_TryEnter; now licensed by measurement, gate =
"twin books identical to source books"); timeframe-aware sequence steps;
6b window widening from design intent; TrendPullback_Fibo BE=on vs BE=off
clean A/B (add a second .seq differing only in BE); SUniverseRow seq fields
+ SCOPE/LIVE sequence-state UI; ADR-004 re-measure on higher TFs.

## Standing tech-debt
per-tick mover overlay (~30s cap), CFG_CLR_ alias removal, LAY_KpiGrid
consolidation, PANEL_BODY_H re-measure, VirtualBook last-N ring, D6 FSM
replay on reattach, packed-int optimizer encoding.

## Phase authority
The single phase ladder lives in `docs/PHASE_LEDGER.md` — it reconciles the
three historical phase numbering schemes (overhaul plan, Fable roadmap, SSE
line). Consult it before claiming any phase is done or starting a new one.
Headline: restructure 0–5 done (P5 under a rewritten exit check with a CLOSED
sanctioned-residual list of EG_ readers — additions require a ledger edit in
the same commit); SSE Phase 6 closed; Phase 7 designed; ladder item D = the
R6 LONG RUN, which is NOW IN FLIGHT (kit shipped, owner executing).

## CURRENT STATE — the R6 long run (ladder item D) — READ THIS FIRST
Kit: `C:\NeelPrajna\repo\tests\longrun\` (README.md procedure,
PREDICTIONS.md pre-registration, NPSU_Strategies\TrendPullback_noBE.seq).
- Windows are FIXED: in-sample 2026.01.01–05.31 · OOS 2026.06.01–06.30 ·
  2026.07.01–22 is BURNED (examined 4x during Phase 6 testing — never OOS).
- Roster = six R6 statics + Phase 6 .seq files + TrendPullback_noBE
  (#37933dd4, BE=off arm of the clean BE A/B vs TrendPullback_Fibo
  #4bc2b282) − ZZ_BadGate removed for the run. Twins ON via
  InpSeq_UnifyStatic. Config = PHASE6_2_ALL_DRYRUN.ini + hand-set dates,
  every-tick.
- Claude's predictions P1–P8 are pre-registered in PREDICTIONS.md with
  confidence levels. Owner adds his own BEFORE starting. Never edit
  predictions after seeing data.
- Session protocol when results arrive: (1) verify ea_version + all hashes
  in the journal lines; (2) grade P1–P8/O* against IN-SAMPLE ONLY; (3)
  write RESULTS_insample.md conclusions + intended promotions; (4) only
  then request the OOS run; (5) flips between windows are recorded as
  unstable, never explained away. Ranking is survival-first (maxDD → worst
  streak → ranging weeks → PF, never ROI); n<30 on either arm of any
  comparison = "still open", no verdict.
- Likely first message in the new chat: long-run CSVs + tester HTML.
  Follow the protocol above. Do not skip prediction grading.

## How to start the session
If the owner brings long-run results: follow the CURRENT STATE protocol.
Otherwise ask what he wants to work on. Candidates: Phase 7a recorder,
6c unification (gate = twin books identical to source books),
SUniverseRow seq fields + sequence-state UI. Do not start coding until
he picks.
