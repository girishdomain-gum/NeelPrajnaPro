# =====================================================================
# T-032_sweep_ruling_edits.ps1
# WHAT:    Commits the Architect's connector edits recording the Owner's
#          alpha-budget ruling, which were NOT picked up by T-031's commit
#          (that commit showed 3 files, all new creates - no modifications).
#          Affected files, verified present on disk:
#            docs\execution_plan\...-v2.0.md   (§0 current state, §4 preconditions)
#            docs\journal\NeelPrajnaPro_Journal.md  (entry J-029)
# WHY:     The ruling is recorded on disk but not in git history. Until it
#          is committed, a fresh clone would not show that the alpha-budget
#          was set - and the ledger's own record would be incomplete.
# CHANGES: git add docs ops; commit; push. Prints the diff summary first
#          so the log shows exactly what was outstanding.
# OUTPUT:  ops\runlogs\T-032_sweep_ruling_edits.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-032_sweep_ruling_edits.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-032 sweep Owner-ruling edits === $(Get-Date -Format o)"

Write-Host "--- [1] what is outstanding before the sweep ---"
git status -s 2>&1 | Out-String | Write-Host
Write-Host "diff stat:"
git diff --stat 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the ruling text is actually on disk ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
if (Select-String -Path $ep -Pattern "alpha-budget = 0.05" -SimpleMatch -Quiet) { Write-Host "OK: execution plan carries the ruling" }
elseif (Select-String -Path $ep -Pattern "0.05" -SimpleMatch -Quiet) { Write-Host "OK: execution plan carries 0.05 (unicode alpha)" }
else { Write-Host "MISSING: execution plan has no alpha-budget ruling"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-029" -SimpleMatch -Quiet) { Write-Host "OK: journal carries J-029" }
else { Write-Host "MISSING: journal has no J-029 entry"; $failed = $true }

Write-Host "--- [3] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-032: record Owner ruling - neelprajna family alpha-budget = 0.05 (per-claim bar at 18 trials: p < 0.0028); window-designation method (b) selected, designation line still open; journal J-029" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - the edits were already committed by an earlier run. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "--- [4] confirm clean tree ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-032_sweep_ruling_edits.log 2>&1 | Out-Null
git commit -m "T-032: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
