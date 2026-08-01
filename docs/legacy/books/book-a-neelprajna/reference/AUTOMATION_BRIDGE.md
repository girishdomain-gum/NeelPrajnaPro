# AUTOMATION BRIDGE — how Claude executes work on this machine

- Status: shipped 2026-07-23. Needs one-time owner setup (§3), then the
  human loop shrinks to "keep one window open".
- Components: `tools/np_agent.py` (the watcher), `tools/np_agent_start.bat`
  (double-click launcher), `C:\NeelPrajna\bridge\` (the mailbox).

## 1. The problem it solves

The Filesystem connector lets Claude read and write files on this machine
but cannot EXECUTE programs. Compiling (metaeditor64.exe) and backtesting
(terminal64.exe) are executions. Until now that meant: Claude writes code →
owner runs deploy.bat → owner presses F7 → owner runs the tester → owner
uploads results. Four human steps per iteration.

The bridge replaces those with a mailbox. Claude writes a small job file;
the watcher executes it; Claude reads the logs and reports back from the
results folder. The owner's job becomes: start the watcher, leave it
running.

    Claude ──writes──▶ bridge\jobs\<id>.json
                              │
                        np_agent.py (owner's machine, always running)
                              │ executes WHITELISTED action
                              ▼
    Claude ◀──reads─── bridge\results\<id>.status.json + logs + reports

## 2. The security model (deliberate, do not weaken)

- **Three job types exist**: `deploy`, `compile`, `backtest`. There is no
  "run this command" job and there must never be one — a file-writing
  attacker (or a confused Claude) must not be able to execute arbitrary
  programs by writing a file.
- Executable paths are fixed in the script's CONFIG, not supplied by jobs.
- Backtest ini paths must resolve inside `C:\NeelPrajna\repo`; anything
  else is refused.
- **The human-only list** (the agent cannot do these, by design):
  - attaching the EA to any live chart
  - arming `InpSeq_LiveApply` or any real-trading switch
  - any order, position, or account action
  - deleting data
  The two-key philosophy from Phase 6b extends here: automation may
  build and measure; only the owner arms.

## 3. One-time setup (owner, ~10 minutes)

1. Check Python runs: `python --version` in a terminal (3.8+).
2. Open `tools\np_agent.py`, review the CONFIG block:
   - `TERMINAL_EXE` / `METAEDITOR` — confirm the install path.
   - **IMPORTANT**: point `TERMINAL_EXE` at a terminal you do NOT keep
     live charts on. Automated tester runs use `ShutdownTerminal=1`,
     which closes that terminal when the test ends. The second terminal
     install (the E92643… one) is the natural choice; update the path if
     its terminal64.exe lives elsewhere.
3. Double-click `tools\np_agent_start.bat`. First lines will warn if any
   configured path does not exist.
4. Tell Claude "bridge is up". Claude verifies by reading
   `bridge\results\heartbeat.json` (updated every 5 s).

## 4. What a session looks like now

    Claude: writes code to the repo
    Claude: writes bridge\jobs\001_deploy.json    → agent runs deploy.bat
    Claude: writes bridge\jobs\002_compile.json   → agent compiles, parses
            "N errors, M warnings" into 002.status.json
    Claude: reads the log; if errors → fixes code → repeat (no human)
    Claude: writes bridge\jobs\003_backtest.json  {"ini": "tests/...",
            "from": "2026.01.01", "to": "2026.05.31"}
    agent:  runs the tester headless (hours for long runs), harvests the
            HTML report + fresh NPSU_*/NP_* CSVs into bridge\results\
    Claude: reads them and writes the analysis

The compile loop — historically the slowest human round-trip — becomes
fully autonomous. The owner reviews conclusions, not mechanics.

## 5. Honest limits

- **Tester visual mode, chart attachment, UI sign-off** stay human — they
  need eyes on a screen.
- **Long backtests occupy the automation terminal** for hours; one job at
  a time, queued in filename order.
- **Report harvesting is heuristic** (newest files matching the run id /
  recent NPSU CSVs). If a report fails to appear in results\, it is in the
  automation terminal's data folder — Claude can read it there directly.
- **The heartbeat is the truth.** If heartbeat.json is stale, the watcher
  is down and Claude must fall back to the manual loop and say so, not
  silently queue jobs into a dead mailbox.
- The compile log regex expects MetaEditor's "N errors, M warnings"
  summary line; if MetaQuotes changes the format, update `do_compile`.

## 6. Failure etiquette (for Claude)

- Always check `<id>.status.json` before claiming a step succeeded.
- Compile gate stays 0 errors / 0 warnings — the agent reports numbers,
  the standard is unchanged.
- If a job fails twice for environmental reasons (paths, terminal busy),
  stop and tell the owner what to check rather than hammering the queue.
