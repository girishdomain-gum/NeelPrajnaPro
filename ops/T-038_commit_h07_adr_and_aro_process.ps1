# =====================================================================
# T-038_commit_h07_adr_and_aro_process.ps1
# WHAT:    Commits and pushes the three records written since the PR #1
#          merge (cdbb71c):
#            ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md  (the v1.1 ADR draft)
#            ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md       (M1-M7 findings)
#            ops\ARO_Execution_Process_v1.0.md             (WO workflow design)
# WHY:     Standing rule from T-037: a decision record is committed the same
#          day it is approved. These three are what the Chief Scientist review
#          and the Owner ratification will be conducted against, so they must
#          be fetchable by any session or reviewer, not live in one tree.
# NOTE:    Stages docs AND ops together (F-22). Run log committed AFTER
#          Stop-Transcript (F-20) so the script cannot chase its own transcript.
# OUTPUT:  ops\runlogs\T-038_commit_h07_adr_and_aro_process.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-038_commit_h07_adr_and_aro_process.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-038 COMMIT H-07 v1.1 ADR + PRE-RATIFICATION REVIEW + ARO PROCESS === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the three records exist ---"
$files = @(
  "ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md",
  "ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md",
  "ops\ARO_Execution_Process_v1.0.md",
  "ops\ARO_Execution_Process_v2.0.md",
  "ops\REPOSITORY_AUTONOMY_v3.0.md"
)
foreach ($f in $files) {
  $p = Join-Path $repo $f
  if (Test-Path $p) { Write-Host ("OK:      " + $f) } else { Write-Host ("MISSING: " + $f); $failed = $true }
}

Write-Host "--- [3] verify the review's mandatory-issue block is present ---"
$rev = Join-Path $repo "ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md"
foreach ($m in @("M1","M2","M3","M4","M5","M6","M7")) {
  if (Select-String -Path $rev -Pattern ("**" + $m + " ") -SimpleMatch -Quiet) { Write-Host ("OK: " + $m + " recorded") }
  else { Write-Host ("MISSING: " + $m); $failed = $true }
}

Write-Host "--- [4] confirm no frozen document was touched in this working tree ---"
$frozen = git diff --cached --name-only 2>&1
$touched = git status -s 2>&1 | Out-String
if ($touched -match "docs/execution_plan" -or $touched -match "docs/constitution") {
  Write-Host "STOP: a frozen document appears modified - inspect before committing"; $failed = $true
} else { Write-Host "OK: no frozen document modified (execution_plan / constitution clean)" }

Write-Host "--- [5] stage docs AND ops together (F-22), commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-038: H-07 SS5 v1.1 ADR draft + pre-ratification review (M1-M7) + ARO execution process v2.0 repository-first (pull queues, git-lease claiming, role mailboxes, handover package, Owner three-verb model; v1.0 superseded) + repository autonomy layer v3.0 (boot spec, generated manifests by reference-not-restatement, discovery, recovery, state model, multi-session rules)" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - ADR draft, review and ARO process committed and pushed; ready for Chief Scientist review" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-038_commit_h07_adr_and_aro_process.log 2>&1 | Out-Null
git commit -m "T-038: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
