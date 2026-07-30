# =====================================================================
# T-035_align_box_column.ps1
# WHAT:    Commits finding F-24 and its correction: Architecture, Vision
#          and Execution Plan aligned to ONE canonical box column.
#          Files edited on disk by the Architect:
#            docs\architecture\...-v1.0.md   (new §A.1 12-row box table;
#                                             §8 and Part C captions)
#            docs\vision\...-v1.0.md         (delivery table -> same 12 rows)
#            docs\execution_plan\...-v2.0.md (row refs on every sprint;
#                                             NP-S7/S8 box lines added)
#            docs\journal\NeelPrajnaPro_Journal.md  (entry J-032)
# WHY:     Architecture Part A and Vision were written when the plan ended
#          at NP-S4 and described later work as "rulings" not builds.
#          Plan v2.0 schedules them as sprints. Owner ruled: everything
#          aligns to the architecture box column.
# NOTE:    Constitution §7.2 clarification (no requirement changed), not a
#          §7.3 amendment. Owner approved before application.
# OUTPUT:  ops\runlogs\T-035_align_box_column.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-035_align_box_column.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-035 align all docs to the architecture box column === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before the sweep ---"
git status -s 2>&1 | Out-String | Write-Host
git diff --stat 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the alignment landed in all four files ---"
$arch = Join-Path $repo "docs\architecture\NeelPrajnaPro_Architecture-v1.0.md"
$vis  = Join-Path $repo "docs\vision\NeelPrajnaPro_Vision-v1.0.md"
$ep   = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr   = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
if (Select-String -Path $arch -Pattern "A.1 The box column" -SimpleMatch -Quiet) { Write-Host "OK: architecture carries the canonical box table" } else { Write-Host "MISSING: architecture box table"; $failed = $true }
if (Select-String -Path $vis  -Pattern "identical to" -SimpleMatch -Quiet) { Write-Host "OK: vision points at the architecture spine" } else { Write-Host "MISSING: vision alignment note"; $failed = $true }
if (Select-String -Path $ep   -Pattern "row 11 Surface" -SimpleMatch -Quiet) { Write-Host "OK: execution plan NP-S7 cites row 11" } else { Write-Host "MISSING: NP-S7 box row"; $failed = $true }
if (Select-String -Path $ep   -Pattern "row 12 Surface" -SimpleMatch -Quiet) { Write-Host "OK: execution plan NP-S8 cites row 12" } else { Write-Host "MISSING: NP-S8 box row"; $failed = $true }
if (Select-String -Path $jr   -Pattern "J-032" -SimpleMatch -Quiet) { Write-Host "OK: journal carries J-032 (F-24)" } else { Write-Host "MISSING: journal J-032"; $failed = $true }

Write-Host "--- [3] confirm the stale NP-S4 pointers are gone ---"
if (Select-String -Path $arch -Pattern "consumption ruled NP-S4" -SimpleMatch -Quiet) { Write-Host "STALE POINTER STILL PRESENT in architecture"; $failed = $true } else { Write-Host "OK: architecture free of the stale Diagram-3 caption" }
if (Select-String -Path $vis  -Pattern "NP-S3/S4" -SimpleMatch -Quiet) { Write-Host "STALE POINTER STILL PRESENT in vision"; $failed = $true } else { Write-Host "OK: vision free of the stale NP-S3/S4 mapping" }

Write-Host "--- [4] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-035: finding F-24 - Architecture/Vision/Execution Plan were out of sync (box-to-sprint pointers stale from Plan v1.0). Owner ruled: align everything to the architecture box column. Architecture gains canonical 12-row table SA.1 (spine); Vision and Execution Plan use its exact rows; surfaces (Console NP-S7, Book A dashboard NP-S8) enumerated for the first time. Constitution S7.2 clarification - no requirement changed" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "--- [5] confirm clean tree ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [6] KNOWN OPEN ITEM (not a failure) ---"
Write-Host "The Architecture docx twin now diverges from its md (Part A prose -> table)."
Write-Host "Under the twin rule that is a finding until the docx is rebuilt. Recorded in J-032."

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - all three documents aligned to one box column" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-035_align_box_column.log 2>&1 | Out-Null
git commit -m "T-035: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
