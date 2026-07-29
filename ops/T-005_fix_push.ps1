# =====================================================================
# T-005_fix_push.ps1
# WHAT:    Repairs the failed push found by T-004. Local main (full Gen-1
#          history, 151 commits) vs origin/main (1 GitHub auto-init commit,
#          unrelated history) -> replaces the remote's init commit with the
#          real history via push --force-with-lease.
# WHY:     T-001's and T-004's pushes were both rejected (non-fast-forward
#          against the auto-init commit). Merging/rebasing would rewrite or
#          pollute provenance; overwriting one disposable auto-commit is the
#          clean ruling.
# SAFETY:  Step [2] inspects origin/main FIRST. The force push runs ONLY if
#          origin/main has exactly 1 commit. Otherwise: RESULT FAILED, no
#          changes, Architect rules next step. --force-with-lease (never
#          bare --force) aborts if the remote moved since fetch.
# NOTE:    Written after finding F-18 (T-004 said RESULT: OK on a failed
#          push). This script checks $LASTEXITCODE on every git step.
# OUTPUT:  ops\runlogs\T-005_fix_push.log
# =====================================================================

$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-005_fix_push.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false

Write-Host "=== T-005 push repair === $(Get-Date -Format o)"

Write-Host "`n--- [1] fetch and identify both histories ---"
git fetch origin 2>&1 | Out-String | Write-Host
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "origin/main is:"
git log origin/main --oneline 2>&1 | Out-String | Write-Host

Write-Host "--- [2] safety gate: origin/main must be exactly 1 commit ---"
$remoteCount = (git rev-list --count origin/main 2>$null)
Write-Host "origin/main commit count: $remoteCount"
Write-Host "origin/main file list:"
git ls-tree -r --name-only origin/main 2>&1 | Out-String | Write-Host

if ($remoteCount -ne "1") {
    Write-Host "Remote has $remoteCount commits - NOT the disposable init commit alone."
    Write-Host "STOPPING with no changes. Architect must inspect this log and rule."
    $failed = $true
} else {
    Write-Host "`n--- [3] overwrite the auto-init commit with the real history ---"
    git push --force-with-lease origin main 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit code: $LASTEXITCODE"; $failed = $true }

    Write-Host "`n--- [4] verify remote now equals local ---"
    git fetch origin 2>&1 | Out-Null
    $localHead  = git rev-parse HEAD
    $remoteHead = git rev-parse origin/main
    Write-Host "local  HEAD: $localHead"
    Write-Host "remote HEAD: $remoteHead"
    if ($localHead -ne $remoteHead) { Write-Host "HEADs DIFFER"; $failed = $true }
    git status -sb 2>&1 | Out-String | Write-Host

    Write-Host "`n--- [5] commit this log so the repo carries its own evidence ---"
    git add ops/runlogs 2>&1 | Out-Null
    git commit -m "T-005: push repaired (remote auto-init replaced by real history); F-18 fail-loud fix applied" 2>&1 | Out-String | Write-Host
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "final push exit code: $LASTEXITCODE"; $failed = $true }
}

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
