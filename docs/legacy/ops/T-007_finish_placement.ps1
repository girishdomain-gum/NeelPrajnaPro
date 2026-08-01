# =====================================================================
# T-007_finish_placement.ps1
# WHAT:    (1) Places the three current NP planning .docx from
#              Downloads\NP_planning_docx.zip into docs\planning\
#          (2) Fixes finding F-19: untracks the ops\incoming scratch area
#              (zip + extracted tree, incl. a stale pre-rename ARCH-011
#              copy) and adds a .gitignore so scratch never enters git
#              again. Files stay ON DISK; only git tracking is removed.
# BEFORE:  download NP_planning_docx.zip from the chat (goes to Downloads
#          automatically - the script fetches it from there).
# CHANGES: docs\planning\*.docx added; ops\incoming untracked+ignored;
#          one commit; push. NOTHING deleted from disk.
# OUTPUT:  ops\runlogs\T-007_finish_placement.log
# =====================================================================

$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-007_finish_placement.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-007 finish placement + F-19 fix === $(Get-Date -Format o)"

Write-Host "--- [1] fetch current planning docx zip ---"
$dl = "C:\Users\giris\Downloads\NP_planning_docx.zip"
$inc = Join-Path $repo "ops\incoming\NP_planning_docx.zip"
if (Test-Path $dl) { Copy-Item $dl -Destination $inc -Force }
if (-not (Test-Path $inc)) {
    Write-Host "NP_planning_docx.zip not found in Downloads or ops\incoming."
    Write-Host "`nRESULT: FAILED - docx zip missing"
    Stop-Transcript; exit 1
}
$t = Join-Path $repo "ops\incoming\_docx"
Expand-Archive -Path $inc -DestinationPath $t -Force
foreach ($f in @("NP_INTEGRATION_EXECUTION_ROADMAP.docx","NP_INTEGRATION_VV_ACCEPTANCE_PLAN.docx","NP_JOINT_AUTOMATION_PLAN.docx")) {
    $s = Join-Path $t $f
    if (Test-Path $s) { Copy-Item $s -Destination (Join-Path $repo "docs\planning\$f") -Force; Write-Host "placed docs\planning\$f" }
    else { Write-Host "MISSING: $f"; $failed = $true }
}

Write-Host "--- [2] F-19 fix: untrack scratch, ignore forever ---"
Add-Content -Path (Join-Path $repo ".gitignore") -Value "`n# ops scratch area - never tracked (F-19 standing rule)`nops/incoming/"
git rm -r --cached "ops/incoming" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "git rm --cached exit: $LASTEXITCODE"; $failed = $true }
Write-Host "(files remain on disk; only tracking removed)"

Write-Host "--- [3] commit + push ---"
git add .gitignore docs/planning ops/runlogs 2>&1 | Out-String | Write-Host
git commit -m "T-007: current NP planning docx placed; F-19 fix - ops/incoming scratch untracked and gitignored (stale ARCH-011 extract removed from tracking)" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
