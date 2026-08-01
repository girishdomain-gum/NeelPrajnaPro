# =====================================================================
# T-033_record_window_designation.ps1
# WHAT:    Commits the Owner's H-07 window designation to the permanent
#          record. Edits already written to disk by the Architect:
#            docs\execution_plan\...-v2.0.md   (§0 state, §4 preconditions)
#            docs\journal\NeelPrajnaPro_Journal.md  (entry J-030)
# WHY:     Designation is a typed-phrase power under P8 / Constitution §6.
#          Until it is in git history, the ledger's record of the ceremony
#          is incomplete and a fresh clone would not show it happened.
# CHANGES: git add docs ops; commit; push; confirm clean tree.
# OUTPUT:  ops\runlogs\T-033_record_window_designation.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-033_record_window_designation.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-033 record H-07 window designation === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before the sweep ---"
git status -s 2>&1 | Out-String | Write-Host
git diff --stat 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the designation text is on disk in both places ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
if (Select-String -Path $ep -Pattern "designated TRAINING" -SimpleMatch -Quiet) { Write-Host "OK: execution plan carries the designation" }
else { Write-Host "MISSING: execution plan has no designation"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-030" -SimpleMatch -Quiet) { Write-Host "OK: journal carries J-030" }
else { Write-Host "MISSING: journal has no J-030 entry"; $failed = $true }
if (Select-String -Path $ep -Pattern "ALL MET" -SimpleMatch -Quiet) { Write-Host "OK: preconditions marked all-met" }
else { Write-Host "WARNING: preconditions not marked all-met"; $failed = $true }

Write-Host "--- [3] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-033: OWNER RULING recorded - H-07 window designated TRAINING (typed-phrase power, P8 / Constitution S6); scope-based per method (b), Developer must echo resolved span for confirmation before seal; ALL NP-S1 preconditions now met - awaiting only Go/No-Go" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "--- [4] confirm clean tree ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - all NP-S1 preconditions met" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-033_record_window_designation.log 2>&1 | Out-Null
git commit -m "T-033: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
