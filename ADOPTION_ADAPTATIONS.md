# ADOPTION_ADAPTATIONS.md — the only deltas between this project and the Fable kit
*Owner-accepted 2026-08-01 (ADOPTION_AUDIT.md §5, D-1..D-7). Everything not listed
here travels VERBATIM from the kit: COMMS_PROTOCOL rules (v1.5 attention law, v1.6
one-window law, §0 cycle), GIT_WORKFLOW (COMPLETION RULE, checkpoints-are-claims,
command-block safety), both boot prompts' HARD-WON RULES, the two-key law, the
drill law, loud-failure doctrine, the ten commandments.*
*rev 2 (2026-08-01): compile line's `-q` removed — it re-introduced incident I-02
(pyproject addopts already supplies -q; stacking suppresses the summary line).
Caught by the Developer, D-006. Rule: NO extra -q, ever.*

| Kit constant / mechanism | This project |
|---|---|
| Project root | F:\NeelPrajnaPro |
| Project/product name | NeelPrajnaPro |
| Git remote | github.com/girishdomain-gum/NeelPrajnaPro (private) |
| EA folder / MT5 terminal / TERMID | N/A — pure Python research repo (D-5) |
| deploy.bat | NOT installed. No terminal to deploy to. |
| Automation bridge (np_agent) | NOT installed now (D-5). Installed later only if MT5 jobs enter this repo's loop; if installed, the KIT's simple watcher, never the legacy heavy agent (quarry in docs\legacy\). |
| "Compile" in the cycle | Full test run via the repo's own venv, NO extra -q flags: `.venv\Scripts\python.exe -m pytest tests\` THEN `.venv\Scripts\python.exe -m pytest tests\test_kernel_firewall.py`. Owner pastes both summary lines verbatim. Baseline: "884 passed, 1 warning" / "8 passed". |
| "Backtest / real run" in the cycle | `ivf\verify_journal.py datastore\journal\journal.jsonl` plus the relevant judge_/rebuild_ script named by the WO. |
| Verifier --point / symbol digits | XAUUSD; value read from a REAL price in a real CSV at first need, never assumed (kit law). |
| Branch names | main (accepted) · dev (Developer). Legacy pointers (claude/*, maint/*, sprint/NP-S2) retired; cleanup is WO-04, Architect-block only. |
| IVF | The project's OWN ivf\ is kept and remains subject to the DRILL LAW: no checker trusted until a tamper drill shows it can go RED (verifier + firewall drilled 2026-08-01, both RED-then-GREEN). |
| Normative specs shelf | docs\architecture, docs\scientific_model, docs\constitution stay at their current paths as reference specs (.md only; docx twins retired). Docs describe; comms\STATE.md governs. |
