# =====================================================================
# T-023_sweep_ops_scripts.ps1
# WHAT:    Fixes finding F-22: T-016 through T-022's .ps1 scripts were
#          never committed to git (only their run logs were — the commit
#          step in each staged "docs" but never "ops"). Sweeps every
#          untracked ops/*.ps1 file into one commit.
# CHANGES: git add ops (whole folder, catches any untracked .ps1 or .log);
#          one commit; push.
# OUTPUT:  ops\runlogs\T-023_sweep_ops_scripts.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-023_sweep_ops_scripts.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-023 sweep untracked ops scripts (F-22 fix) === $(Get-Date -Format o)"

Write-Host "--- [1] show what's untracked before the sweep ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] stage everything under ops (scripts + any stray logs) ---"
git add ops 2>&1 | Out-String | Write-Host
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [3] commit + push (only if there is something staged) ---"
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-023: sweep untracked ops scripts (F-22 fix) - T-016..T-022 placement scripts committed; template updated so future scripts stage ops+docs together" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - ops was already fully tracked. This is a valid outcome, not a failure."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-023_sweep_ops_scripts.log 2>&1 | Out-Null
git commit -m "T-023: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
