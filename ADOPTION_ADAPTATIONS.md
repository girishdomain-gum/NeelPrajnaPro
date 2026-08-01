# ADOPTION_ADAPTATIONS.md — the only deltas between this project and the Fable kit
*Owner-accepted 2026-08-01 (ADOPTION_AUDIT.md §5, D-1..D-7). Everything not listed
here travels VERBATIM from the kit: COMMS_PROTOCOL rules (v1.5 attention law, v1.6
one-window law, §0 cycle), GIT_WORKFLOW (COMPLETION RULE, checkpoints-are-claims,
command-block safety), both boot prompts' HARD-WON RULES, the two-key law, the
drill law, loud-failure doctrine, the ten commandments.*

| Kit constant / mechanism | This project |
|---|---|
| Project root | F:\NeelPrajnaPro |
| Project/product name | NeelPrajnaPro |
| Git remote | github.com/girishdomain-gum/NeelPrajnaPro (private) |
| EA folder / MT5 terminal / TERMID | N/A — pure Python research repo (D-5) |
| deploy.bat | NOT installed. No terminal to deploy to. |
| Automation bridge (np_agent) | NOT installed now (D-5). Installed later only if MT5 jobs enter this repo's loop; if installed, the KIT's simple watcher, never the legacy heavy agent (which is quarry in docs\legacy\). |
| "Compile" in the cycle | Full test run via the repo's own venv: `.venv\Scripts\python.exe -m pytest tests\ -q` PLUS `.venv\Scripts\python.exe -m pytest tests\test_kernel_firewall.py -q`. Owner pastes both summary lines. Known baselined red: tests/adapters/test_mt5_csv.py::test_real_ivf_export_ingests_zero_flags (WO-01 exists to clear it). |
| "Backtest / real run" in the cycle | `ivf\verify_journal.py` against the live ledger, plus the relevant judge_/rebuild_ script named by the WO. |
| Verifier --point / symbol digits | XAUUSD; value read from a REAL price in a real CSV at first need, never assumed (kit law). |
| Branch names | main (accepted) · dev (Developer). Legacy sprint/NP-S2 merges into main once at adoption (Block B) and then retires. |
| IVF | The project's OWN ivf\ is kept (it is the kit pattern's ancestor) and remains subject to the DRILL LAW: no checker trusted until a tamper drill shows it can go RED. |
| Normative specs shelf | docs\architecture, docs\scientific_model, docs\constitution stay at their current paths as reference specs (docx twins retired). Docs describe; comms\STATE.md governs. |
