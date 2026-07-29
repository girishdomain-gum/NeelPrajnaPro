# OPS — the written-communication channel between Architect and Owner

*This folder is how commands travel. The Architect never asks the Owner to paste loose commands again; the Owner never reports results in prose again. Scripts in, logs out.*

## The protocol

1. **The Architect writes a script** into `F:\NeelPrajnaPro\ops\`, named `T-###_short_name.ps1` (### = the touch id from `docs\governance\HUMAN_TOUCH_LOG.md`). The Architect announces the exact path in chat.
2. **The Owner runs it** — one line, from any PowerShell window:
   ```powershell
   powershell -ExecutionPolicy Bypass -File F:\NeelPrajnaPro\ops\T-###_short_name.ps1
   ```
   (Right-click → "Run with PowerShell" also works.)
3. **The script writes its own transcript** to `ops\runlogs\T-###_short_name.log` — every command it ran and every output line. The Owner types nothing back.
4. **The Architect reads the log** through the Filesystem connector and verifies. The log file is the evidence; chat is only for decisions.

## Rules

- Scripts are **PowerShell (`.ps1`)**, never `.bat`. (Note for the record: `BootScript.bat` contained PowerShell syntax — `Copy-Item`, `#` comments — which a `.bat` interpreter cannot run. It worked because the Owner pasted the lines into PowerShell directly. `.ps1` removes that trap.)
- Every script starts with a WHAT/WHY/CHANGES header the Owner can read in ten seconds before running.
- Every script is **fail-loud**: it checks its own results and prints `RESULT: OK` or `RESULT: FAILED <reason>` as its final line.
- Scripts that only *read* say so in the header. Scripts that *change* anything list every change in the header. Scripts never delete; never touch reserves, the ledger, or anything in the permanently-human list.
- Every script run is a logged touch (ROUTINE-OP) in the HUMAN_TOUCH_LOG — the retro's job is to make this folder quieter over time. The standing automation path for this whole channel: once a Developer session runs inside this repo (NP-S1 onward), most future scripts become the Developer's work, not the Owner's.

## Index

| Script | Purpose | Status |
|---|---|---|
| T-004_verify_bootstrap.ps1 | Verify T-001 end-to-end (git remote, push state, history, tree counts, pause markers); tidy BootScript.bat into ops\; commit+push the ops channel | READY — run me |
