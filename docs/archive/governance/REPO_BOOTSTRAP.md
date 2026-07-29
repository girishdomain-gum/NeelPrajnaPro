# NeelPrajnaPro — Repository Bootstrap & Migration Manifest
*Fable (Architect) · 2026-07-29 · Remote: https://github.com/girishdomain-gum/NeelPrajnaPro*

F:\NeelPrajnaPro is the single home of the joint NeelPrajna × QRF programme: the scientific core (Kernel, ledger, IVF, tests) carried forward from F:\QRF, plus the entire documentation estate. All new docs are written here and only here.

## 1. The one rule that prevents two-clock drift ⚖ (Owner ratification required)

**On cutover, exactly one repository is authoritative for the scientific core.** Recommended ruling:
- **F:\NeelPrajnaPro** — authoritative for: Kernel code, ledger/datastore, hypotheses, configs, IVF, tests, and ALL documentation (charter, planning, reviews, governance, Book-A references).
- **F:\QRF** — becomes a **frozen read-only archive** the moment the copy below is verified and pushed. No commits, ever again. Its value is provenance.
- **F:\NeelPrajna** — remains **live and authoritative for execution only**: the MQL5 EA repo, the bridge, the lab/Supervisor. It is NOT copied wholesale — moving the live automation would break machine-path configs and the running Supervisor for no scientific gain. Its docs are copied here as read-only references (Book A).

My recorded recommendation, per the Dissent Charter: copy the QRF tree **including `.git`** so ten sprints of history, GO/REV records, and the hash-chained journal's provenance travel with the code. A fresh-history repo would orphan the evidence trail. If you rule otherwise, my recommendation is on the record.

## 2. Copy manifest

| From | What | To | Why |
|---|---|---|---|
| F:\QRF | Entire tree incl. `.git`, `qrf/`, `ivf/`, `tests/`, `configs/`, `hypotheses/`, `datastore/`, `docs/`, `scripts/`, `dashboard/`, root files | F:\NeelPrajnaPro\ (root) | The Kernel and its evidence come forward whole — never cherry-picked |
| F:\QRF | EXCLUDE: `.venv`, `.pytest_cache`, `.ruff_cache`, `__pycache__` | — | Recreated locally; never versioned |
| F:\NeelPrajna\repo\docs | Entire docs tree | docs\books\book-a-neelprajna\reference\ | Book-A design record (ADRs, phase ledger, automation docs) as read-only reference |
| F:\NeelPrajna\repo | HANDOVER.md, CHANGELOG.md, NPSU_Design_Doc_v1.6.md, NPSU_PostValidation_Guide_v1.0.md | docs\books\book-a-neelprajna\ | Book-A front-door documents |
| F:\NeelPrajna\lab | SUPERVISOR_CONTRACT.md | docs\books\book-a-neelprajna\ | The signed trust-anchor constitution |
| (this session) | Charter v2.0 estate, ARCH-NP-001, planning docs, reviews, governance addendum | docs\charter, docs\planning, docs\reviews, docs\governance | Already written in place by the Architect |
| Delivered zip (NeelPrajna_QRF_Working_Set_v2.zip) | The four .docx presentation copies + corrected console mockups + reference volumes (.docx) | docs\planning\ and docs\reviews\reference_volumes\ | Binary files — the Filesystem connector writes text only; drop these in by hand |

**Never copied:** the retired bespoke research stack's outputs as evidence; the pre-correction document versions; the mangled part2 mockups.

## 3. Owner commands (one pasteable block, PowerShell)

```powershell
# --- 1. QRF scientific core comes forward, history included ---
robocopy F:\QRF F:\NeelPrajnaPro /E /XD .venv .pytest_cache .ruff_cache __pycache__ /XF *.pyc
# Expected: exit code 1-3 is SUCCESS for robocopy (files copied). 8+ is an error - stop and read the log.
# NOTE: /MIR is deliberately absent and must never be used here - it would delete the docs already written.

# --- 2. Book-A references ---
robocopy F:\NeelPrajna\repo\docs F:\NeelPrajnaPro\docs\books\book-a-neelprajna\reference /E
Copy-Item F:\NeelPrajna\repo\HANDOVER.md,F:\NeelPrajna\repo\CHANGELOG.md,F:\NeelPrajna\repo\NPSU_Design_Doc_v1.6.md,F:\NeelPrajna\repo\NPSU_PostValidation_Guide_v1.0.md -Destination F:\NeelPrajnaPro\docs\books\book-a-neelprajna\
Copy-Item F:\NeelPrajna\lab\SUPERVISOR_CONTRACT.md -Destination F:\NeelPrajnaPro\docs\books\book-a-neelprajna\

# --- 3. Re-point and push (full Gen-1 history goes to the new remote) ---
cd F:\NeelPrajnaPro
git remote set-url origin https://github.com/girishdomain-gum/NeelPrajnaPro.git
git add -A
git status
# STOP AND READ: the staged list should show docs/charter, docs/planning, docs/reviews,
# docs/governance, docs/books, REPO_BOOTSTRAP.md and Book-A references - and NOTHING deleted.
git commit -m "BOOTSTRAP: NeelPrajnaPro - QRF core forward (history preserved) + charter v2.0 estate + NP planning + Book-A references"
git push -u origin main
```

After the push, paste `git log --oneline -5` and the robocopy summary lines back to the Architect — that output is the verification evidence, per protocol.

## 4. Post-bootstrap actions (Architect executes on your Go)

1. Freeze note appended to F:\QRF\README.md and a final commit there: "ARCHIVED — continued at NeelPrajnaPro" (one line, Owner-pushed).
2. WO-A documentation truth pass runs HERE now (AUTOMATION_BRIDGE reality, AI_PROJECT_STATE hand rows, README/CHANGELOG fold-in) — paths updated to F:\NeelPrajnaPro where they name the Kernel's home.
3. CLAUDE.md / boot prompts updated so every fresh session boots from this repo's docs\ tree first.
4. Path references inside carried-forward docs: originals stay untouched (append-only); this file is the authoritative old→new path mapping (F:\QRF → F:\NeelPrajnaPro for the scientific core; F:\NeelPrajna unchanged for execution).

*Anchor: one home for the truth, one home for the hands, and an archive that never lies about where either came from.*
