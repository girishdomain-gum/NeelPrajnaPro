# Owner Rulings — 2026-07-29 (recorded by the Architect from the Owner's words)

Status: RECORDED. These rulings were stated by the Owner (Girish) in the working session of 2026-07-29 and take effect immediately. Per the append-only convention, any change is a new dated ruling.

## R-1 — Pause of the legacy repositories
All work related to **F:\QRF** and **F:\NeelPrajna** is PAUSED. No new sprints, work orders, commits, or bridge jobs originate against them. They are sources for the one-time copy into F:\NeelPrajnaPro and, after that copy is verified, archives.
- F:\QRF → frozen archive (freeze marker added at bootstrap; no commits after the archive marker).
- F:\NeelPrajna → paused. The running Supervisor/agent may remain up or be shut down at the Owner's convenience; either way, no jobs are queued while the pause holds.

**Recorded implication (Architect):** the pause is fully compatible with Sprint NP-S1 (H-07), which is pure Python inside F:\NeelPrajnaPro. Sprint NP-S2 (the R6 long run) requires the MT5 lab; when we reach it, a **scoped unpause ruling** for the lab's bridge will be requested — nothing else in F:\NeelPrajna unpauses.

## R-2 — Single home
F:\NeelPrajnaPro (GitHub: girishdomain-gum/NeelPrajnaPro) is the single authoritative home for the scientific core and ALL documentation. Whatever is needed is copied in once; all new work happens here, from fresh, independently of the legacy trees.

## R-3 — Minimal human involvement, with a ledger
The Owner's involvement in **implementation, execution, and validation** is minimized to the floor the machine allows. Two standing consequences:
1. Every human touch — routine or governance — is logged in `HUMAN_TOUCH_LOG.md` (same directory) with its category and, for routine operations, the automation path that will remove it. The log is reviewed at every sprint retro; the ultimate goal on the record: **a human-free operational process.**
2. Governance touches (ratify, designate, α-budget, Go/No-Go, arm, unpause) are NOT minimized — per the Constitution they are permanently human — but they ARE logged, so the retrospective can verify that every remaining touch is judgment, not chores.

## R-4 — Bootstrap execution
The Owner will run the one-time bootstrap command block (REPO_BOOTSTRAP.md §3, extended with freeze markers) and paste the outputs back as verification evidence. This is logged as touch T-001.
