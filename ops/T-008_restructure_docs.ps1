# =====================================================================
# T-008_restructure_docs.ps1
# WHAT:    Executes the Owner's "one doc per thing" ruling: git-mv renames
#          the charter docs to canonical root names (history preserved),
#          moves superseded granular docs into docs\archive\, commits, pushes.
# WHY:     Too many documents was a real problem (Owner, 2026-07-29).
#          After this: 11 canonical docs (docs\README.md), shelves, one journal.
# CHANGES: git mv only (history-preserving renames/moves). NOTHING deleted.
# OUTPUT:  ops\runlogs\T-008_restructure_docs.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-008_restructure_docs.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
function MV($src,$dst){
    if (Test-Path (Join-Path $repo $src)) {
        git mv $src $dst 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "git mv FAILED: $src"; $script:failed = $true }
        else { Write-Host "moved $src -> $dst" }
    } else { Write-Host "skip (absent): $src" }
}
Write-Host "=== T-008 docs restructure === $(Get-Date -Format o)"

Write-Host "--- [1] canonical renames (charter -> root) ---"
MV "docs/charter/NEELPRAJNA_CONSTITUTION_v2.0.md"                       "docs/CONSTITUTION.md"
MV "docs/charter/NEELPRAJNA_SCIENTIFIC_MODEL_v2.0.md"                    "docs/SCIENTIFIC_MODEL.md"
MV "docs/charter/NEELPRAJNA_PLATFORM_INTEGRATION_ARCHITECTURE_v2.0.md"   "docs/ARCHITECTURE.md"
MV "docs/planning/NP_INTEGRATION_VV_ACCEPTANCE_PLAN.md"                  "docs/VV_PLAN.md"
MV "docs/planning/NP_JOINT_AUTOMATION_PLAN.md"                           "docs/AUTOMATION.md"
MV "docs/governance/ROLES_COMMUNICATION_EXPRESSION.md"                   "docs/ROLES_AND_COMMUNICATION.md"
MV "docs/governance/TEACHING_AND_KNOWLEDGE_TRANSFER_STANDARD-v5.md"      "docs/WRITING_STANDARD.md"

Write-Host "--- [2] archive superseded granular docs (absorbed by EXECUTION_PLAN / JOURNAL) ---"
New-Item -ItemType Directory -Force -Path "$repo\docs\archive\planning","$repo\docs\archive\governance","$repo\docs\archive\reviews","$repo\docs\archive\charter" | Out-Null
MV "docs/planning/NP_INTEGRATION_EXECUTION_ROADMAP.md"        "docs/archive/planning/NP_INTEGRATION_EXECUTION_ROADMAP.md"
MV "docs/planning/ARCH-NP-001_H07_Integration_Sprint.md"      "docs/archive/planning/ARCH-NP-001_H07_Integration_Sprint.md"
MV "docs/planning/H07_SEALED_MECHANICAL_DEFINITION_v1.0.md"   "docs/archive/planning/H07_SEALED_MECHANICAL_DEFINITION_v1.0.md"
MV "docs/planning/NP_INTEGRATION_EXECUTION_ROADMAP.docx"      "docs/archive/planning/NP_INTEGRATION_EXECUTION_ROADMAP.docx"
MV "docs/planning/NP_INTEGRATION_VV_ACCEPTANCE_PLAN.docx"     "docs/archive/planning/NP_INTEGRATION_VV_ACCEPTANCE_PLAN.docx"
MV "docs/planning/NP_JOINT_AUTOMATION_PLAN.docx"              "docs/archive/planning/NP_JOINT_AUTOMATION_PLAN.docx"
MV "docs/governance/OWNER_RULINGS_2026-07-29.md"              "docs/archive/governance/OWNER_RULINGS_2026-07-29.md"
MV "docs/governance/RATIFICATION_RECORD_2026-07-29.md"        "docs/archive/governance/RATIFICATION_RECORD_2026-07-29.md"
MV "docs/governance/HUMAN_TOUCH_LOG.md"                       "docs/archive/governance/HUMAN_TOUCH_LOG.md"
MV "docs/governance/CORRECTIONS_LOG_2026-07-29.md"            "docs/archive/governance/CORRECTIONS_LOG_2026-07-29.md"
MV "docs/governance/CORRECTIONS_LOG_ADDENDUM_2026-07-29.md"   "docs/archive/governance/CORRECTIONS_LOG_ADDENDUM_2026-07-29.md"
MV "docs/governance/HOW_THIS_DOC_WAS_BUILT.md"                "docs/archive/governance/HOW_THIS_DOC_WAS_BUILT.md"
MV "docs/reviews/REV-DeepSeek-Estate_Fable_2026-07-29.md"     "docs/archive/reviews/REV-DeepSeek-Estate_Fable_2026-07-29.md"
MV "docs/reviews/REV-Full-Backup-Corpus_Fable_2026-07-29.md"  "docs/archive/reviews/REV-Full-Backup-Corpus_Fable_2026-07-29.md"
MV "docs/charter/README_ESTATE_v2.md"                         "docs/archive/charter/README_ESTATE_v2.md"
MV "docs/handover/ARCHITECT_HANDOVER_NP.md"                   "docs/archive/governance/ARCHITECT_HANDOVER_NP.md"

Write-Host "--- [3] verify canonical set present ---"
$canon = @("THE_ONE_PAGE.md","VISION.md","CONSTITUTION.md","SCIENTIFIC_MODEL.md","ARCHITECTURE.md","EXECUTION_PLAN.md","VV_PLAN.md","AUTOMATION.md","ROLES_AND_COMMUNICATION.md","WRITING_STANDARD.md","JOURNAL.md","README.md")
foreach ($c in $canon) {
    if (Test-Path "$repo\docs\$c") { Write-Host "OK  docs\$c" } else { Write-Host "MISSING docs\$c"; $failed = $true }
}

Write-Host "--- [4] commit + push ---"
git add -A docs ops 2>&1 | Out-String | Write-Host
git commit -m "T-008: one-doc-per-thing restructure (Owner ruling) - canonical set at docs root, granular docs archived, git history preserved via mv" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
