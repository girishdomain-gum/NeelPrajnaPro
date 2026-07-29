# ============ T-001 : one-time bootstrap (logged in HUMAN_TOUCH_LOG.md) ============

# 1. QRF scientific core comes forward, history included (NO /MIR - never use it here)
robocopy F:\QRF F:\NeelPrajnaPro /E /XD .venv .pytest_cache .ruff_cache __pycache__ /XF *.pyc
# robocopy exit codes 1-3 = SUCCESS. 8+ = error: stop and read.

# 2. Book-A references from the paused NeelPrajna repo
robocopy F:\NeelPrajna\repo\docs F:\NeelPrajnaPro\docs\books\book-a-neelprajna\reference /E
Copy-Item F:\NeelPrajna\repo\HANDOVER.md,F:\NeelPrajna\repo\CHANGELOG.md,F:\NeelPrajna\repo\NPSU_Design_Doc_v1.6.md,F:\NeelPrajna\repo\NPSU_PostValidation_Guide_v1.0.md -Destination F:\NeelPrajnaPro\docs\books\book-a-neelprajna\
Copy-Item F:\NeelPrajna\lab\SUPERVISOR_CONTRACT.md -Destination F:\NeelPrajnaPro\docs\books\book-a-neelprajna\

# 3. Pause/freeze markers in BOTH legacy repos (after the copy, so they don't travel)
Set-Content F:\QRF\PAUSED.md "# ARCHIVED 2026-07-29 - all work continues at F:\NeelPrajnaPro (github.com/girishdomain-gum/NeelPrajnaPro). No commits here after this marker. Ruling: OWNER_RULINGS_2026-07-29.md R-1."
Set-Content F:\NeelPrajna\repo\PAUSED.md "# PAUSED 2026-07-29 - no new work orders or bridge jobs while the pause holds. Scoped unpause required for the R6 lab work (NP-S2). Ruling: OWNER_RULINGS_2026-07-29.md R-1."

# 4. Re-point and push (full Gen-1 history goes to the new remote)
cd F:\NeelPrajnaPro
git remote set-url origin https://github.com/girishdomain-gum/NeelPrajnaPro.git
git add -A
git status
# STOP AND READ: staged list should show docs/charter, docs/planning, docs/reviews,
# docs/governance, docs/books, REPO_BOOTSTRAP.md - and NOTHING deleted.
git commit -m "BOOTSTRAP T-001: NeelPrajnaPro - QRF core forward (history preserved) + charter v2.0 estate + NP planning + governance + Book-A references; legacy repos paused"
git push -u origin main
git log --oneline -5