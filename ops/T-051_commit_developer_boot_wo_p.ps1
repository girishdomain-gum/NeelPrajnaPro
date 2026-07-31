# =====================================================================
# T-051_commit_developer_boot_wo_p.ps1
# WHAT:    Commits ops\DEVELOPER_BOOT_WO-P.md - the paste-ready instruction
#          for the Developer session picking up WO-P.
# WHY:     Written after T-050 ran; no script has swept it yet. It references
#          sprint/NP-S2 by name and must be fetchable from that branch before
#          any session is handed it, or this becomes the same failure this
#          entire day has been catching in others.
# NOTE:    Committed to BOTH main (so it's discoverable) and merged into
#          sprint/NP-S2 (so the Developer's own branch carries it without a
#          separate fetch-from-main step).
# OUTPUT:  ops\runlogs\T-051_commit_developer_boot_wo_p.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-051_commit_developer_boot_wo_p.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-051 COMMIT DEVELOPER BOOT (WO-P) === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the boot file exists and references the right branch ---"
$bf = Join-Path $repo "ops\DEVELOPER_BOOT_WO-P.md"
if (Test-Path $bf) { Write-Host "OK: boot file present" } else { Write-Host "MISSING: boot file"; $failed = $true }
foreach ($k in @("sprint/NP-S2","ARCH-NP-004_WO-P_execution_parity.md","AC-1 outranks the feature","HANDOVER.md")) {
  if (Select-String -Path $bf -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] commit to main first (discoverability) ---"
git checkout main 2>&1 | Out-String | Write-Host
git add ops/DEVELOPER_BOOT_WO-P.md 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-051: commit Developer boot instruction for WO-P, referencing sprint/NP-S2 by name" 2>&1 | Out-String | Write-Host
    git push origin main 2>&1 | Out-String | Write-Host
} else { Write-Host "Nothing staged on main - already committed there." }

Write-Host "--- [4] merge into sprint/NP-S2 so the Developer's own branch carries it ---"
git fetch origin 2>&1 | Out-String | Write-Host
git checkout sprint/NP-S2 2>&1 | Out-String | Write-Host
git merge main -m "T-051: bring Developer boot instruction onto sprint/NP-S2" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "merge exit: $LASTEXITCODE - inspect for conflicts before proceeding"; $failed = $true }
git push origin sprint/NP-S2 2>&1 | Out-String | Write-Host

Write-Host "--- [5] confirm the boot file is present ON sprint/NP-S2 ---"
if (Test-Path $bf) { Write-Host "OK: boot file present on sprint/NP-S2 working tree" } else { Write-Host "STOP: boot file missing after merge"; $failed = $true }

Write-Host "--- [6] verify origin/sprint/NP-S2 matches local ---"
git log --oneline -1 origin/sprint/NP-S2 2>&1 | Out-String | Write-Host
git log --oneline -1 sprint/NP-S2 2>&1 | Out-String | Write-Host
git status -sb 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - the boot instruction is on both main and sprint/NP-S2, and origin matches local. The Developer session may now be released." }
Stop-Transcript

Set-Location $repo
git checkout main 2>&1 | Out-Null
git add ops/runlogs/T-051_commit_developer_boot_wo_p.log 2>&1 | Out-Null
git commit -m "T-051: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
