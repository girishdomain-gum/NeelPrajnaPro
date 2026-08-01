# =====================================================================
# T-014_commit_relocation.ps1
# WHAT:    Commits the phase6_examples relocation the Architect performed
#          via connector: docs\books\...\plans\phase6_examples\ ->
#          qrf\trading\concepts\neelprajna\reference_configs\ (8 files,
#          incl. its own README with an appended relocation note).
# WHY:     Full docs\ tree survey found these were code/config artifacts
#          (.idea/.seq/.set) misplaced under docs\, not documentation.
# CHANGES: git add/commit/push only. NOTHING deleted; move already done.
# NOTE:    Per F-20's standing rule, this script commits its OWN log in a
#          separate step after Stop-Transcript, avoiding the false-negative
#          RESULT seen in T-013.
# OUTPUT:  ops\runlogs\T-014_commit_relocation.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-014_commit_relocation.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-014 commit relocation === $(Get-Date -Format o)"

Write-Host "--- [1] verify relocation ---"
$dst = "$repo\qrf\trading\concepts\neelprajna\reference_configs"
$n = (Get-ChildItem $dst -File -ErrorAction SilentlyContinue | Measure-Object).Count
Write-Host "reference_configs file count: $n (expect 8)"
if ($n -ne 8) { $failed = $true }
if (Test-Path "$repo\docs\books\book-a-neelprajna\reference\plans\phase6_examples") { Write-Host "OLD PATH STILL EXISTS"; $failed = $true } else { Write-Host "OK: old path gone" }

Write-Host "--- [2] commit + push (docs + qrf only; log committed separately below) ---"
git add docs qrf 2>&1 | Out-String | Write-Host
git commit -m "T-014: relocate phase6_examples (.idea/.seq/.set) from docs\books to qrf\trading\concepts\neelprajna\reference_configs - code artifacts, not documentation" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

# F-20 fix: commit the transcript AFTER it's closed, in its own step
Set-Location $repo
git add ops/runlogs/T-014_commit_relocation.log 2>&1 | Out-Null
git commit -m "T-014: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
