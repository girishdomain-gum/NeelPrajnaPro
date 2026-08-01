# =====================================================================
# T-037_commit_np_s1_decision_records.ps1
# WHAT:    Commits and pushes the NP-S1 decision records and the ARO
#          ratification package, all of which are currently UNCOMMITTED
#          on the mainline working tree:
#            ops\DEVQ-01_NP-S1.md                       (DEVQ-01 record, Add. A+B)
#            ops\H07_evidenced_definition_annex_NP-S1.md (v1.1 ADR annex, Add. A+B)
#            ops\ARO_Architecture_Review_NP.md           (ARO review, 12 deliverables)
#            ops\NP-ADR-ARO_draft_v1.0.md                (ARO ADR draft)
#            ops\OWNER_PACKET_ARO_ratification.md        (Owner decision packet)
#          plus any other pending docs\ or ops\ changes.
#
# WHY:     The Developer session on branch claude/neelprajnapro-sprint-np-s1-a8171d
#          raised DEVQ-NP-001/002 asking questions the Owner had ALREADY ruled on,
#          because the ruling records were uncommitted and therefore invisible to
#          every branch and clone. That is the F-22 species at the record level.
#          Standing rule created by that event: a decision record is committed the
#          same day it is approved; an uncommitted decision is not yet a decision
#          the repository can defend. This script is that rule being honoured.
#
# NOTE:    Stages docs AND ops together (F-22 rule). The run log is committed in a
#          SEPARATE step after Stop-Transcript (F-20 rule) so the script does not
#          chase its own growing transcript and report a false FAILED.
#
# OUTPUT:  ops\runlogs\T-037_commit_np_s1_decision_records.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-037_commit_np_s1_decision_records.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-037 COMMIT NP-S1 DECISION RECORDS === $(Get-Date -Format o)"

Write-Host "--- [1] what is outstanding right now ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the five records exist before staging ---"
$files = @(
  "ops\DEVQ-01_NP-S1.md",
  "ops\H07_evidenced_definition_annex_NP-S1.md",
  "ops\ARO_Architecture_Review_NP.md",
  "ops\NP-ADR-ARO_draft_v1.0.md",
  "ops\OWNER_PACKET_ARO_ratification.md",
  "ops\NP-ADR-organization_and_roles_v1.0.md",
  "ops\NP-ADR-model_agnostic_roles_draft_v1.0.md"
)
foreach ($f in $files) {
  $p = Join-Path $repo $f
  if (Test-Path $p) { Write-Host ("OK:      " + $f) } else { Write-Host ("MISSING: " + $f); $failed = $true }
}

Write-Host "--- [3] verify the Owner ruling, the confirmed span, and the annex addenda are in the record ---"
$devq = Join-Path $repo "ops\DEVQ-01_NP-S1.md"
if (Select-String -Path $devq -Pattern "Span confirmed" -SimpleMatch -Quiet) { Write-Host "OK: span confirmation quoted in DEVQ-01" } else { Write-Host "MISSING: span confirmation"; $failed = $true }
if (Select-String -Path $devq -Pattern "DEVQ-01 RESOLVED" -SimpleMatch -Quiet) { Write-Host "OK: DEVQ-01 ruling recorded" } else { Write-Host "MISSING: DEVQ-01 ruling"; $failed = $true }
if (Select-String -Path $devq -Pattern "Addendum B" -SimpleMatch -Quiet) { Write-Host "OK: Addendum B (developer DEVQ reconciliation) present" } else { Write-Host "MISSING: Addendum B"; $failed = $true }
$annex = Join-Path $repo "ops\H07_evidenced_definition_annex_NP-S1.md"
if (Select-String -Path $annex -Pattern "Addendum C" -SimpleMatch -Quiet) { Write-Host "OK: annex Addendum C (placement correction) present - mainline and worktree copies match" } else { Write-Host "MISSING: annex Addendum C - copies diverge"; $failed = $true }

Write-Host "--- [4] stage docs AND ops together (F-22), commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-037: commit NP-S1 decision records - DEVQ-01 (span Owner-confirmed; definitional divergence resolved as v1.1-by-ADR) + H-07 evidenced-definition annex for the v1.1 ADR + ARO architecture review, NP-ADR draft and Owner ratification packet. Records were written and approved earlier the same day but left uncommitted, which is why the Developer session's DEVQ-NP-001/002 re-asked already-ruled questions. Standing rule: decision records are committed the same day they are approved" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [5] branch visibility check: can the Developer branch now see the records? ---"
git branch -a 2>&1 | Out-String | Write-Host
Write-Host "NOTE: the Developer session must rebase/merge mainline into"
Write-Host "      claude/neelprajnapro-sprint-np-s1-a8171d to inherit these records in git"
Write-Host "      (verbatim copies were already placed in its worktree ops\ by hand)."

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-S1 decision records are committed and pushed; the repository can now defend them" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-037_commit_np_s1_decision_records.log 2>&1 | Out-Null
git commit -m "T-037: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
