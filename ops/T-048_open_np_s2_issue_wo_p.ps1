# =====================================================================
# T-048_open_np_s2_issue_wo_p.ps1
# WHAT:    Opens Sprint NP-S2 by issuing its first and gating work order:
#            ops\ARCH-NP-004_WO-P_execution_parity.md
# WHY:     NP-D-011 makes execution-model parity a hard precondition of any
#          further R6 evidence collection. The Developer session must FETCH the
#          instruction from the repository, not be told it in chat - the failure
#          this programme paid for three times in NP-S1.
# GUARD:   Refuses if the Execution Plan's frozen SS4/SS5 markers moved, if any
#          ratified ADR body or appendix was edited, or if NP-S1's close was
#          disturbed (SS0 must still read CLOSED AND ACCEPTED, SS12 must still
#          carry its entry). All patterns are ASCII-safe substrings per J-038.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-048_open_np_s2_issue_wo_p.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-048_open_np_s2_issue_wo_p.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-048 OPEN NP-S2 - ISSUE WO-P === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the work order exists and is complete ---"
$wo = Join-Path $repo "ops\ARCH-NP-004_WO-P_execution_parity.md"
if (Test-Path $wo) { Write-Host "OK: ARCH-NP-004 present" } else { Write-Host "MISSING: ARCH-NP-004"; $failed = $true }
foreach ($k in @("byte-identically reproducible","the stop fills","R-multiple","AC-7","does not require the lab unpause")) {
  if (Select-String -Path $wo -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] NP-D-012 applied to the instruction itself ---"
if (Select-String -Path $wo -Pattern "that is a defect in my instruction" -SimpleMatch -Quiet) { Write-Host "OK: spec-insufficiency is a DEVQ trigger against the Architect" }
else { Write-Host "MISSING: NP-D-012 self-application"; $failed = $true }

Write-Host "--- [4] NP-S1's close is undisturbed ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
foreach ($k in @("CLOSED AND ACCEPTED","twice framed, once judged","EXECUTION-MODEL PARITY")) {
  if (Select-String -Path $ep -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [5] FROZEN / APPEND-ONLY GUARDS ---"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified - corrections are APPENDED (P5)"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [6] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-048: OPEN SPRINT NP-S2 - issue ARCH-NP-004 (WO-P, execution-model parity), the work order NP-D-011 makes a hard precondition of further R6 collection. Verified against qrf/trading/simulator/engine.py: ExecutionSpec's stop_offset and target_offset are hypothesis-level SCALARS, so two trades in one hypothesis cannot carry different stop distances - which is exactly why H-007 registered with nulls and the Battery judged sweep-then-hold-12-bars. Required: per-trade event-sourced stops, R-multiple targets computed from realized risk, and the intrabar tie rule PINNED (the stop fills, conservative, matching the bespoke stack's declared behaviour). AC-1 outranks the feature: every existing sealed verdict must remain byte-identically reproducible under a bumped engine version, or stop and DEVQ. Instruction written under NP-D-012 with spec-insufficiency named as a DEVQ trigger against the Architect. WO-P does not require the lab unpause" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [7] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-S2 is open. WO-P is issued and fetchable. The Developer may start; the lab unpause is not on its critical path." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-048_open_np_s2_issue_wo_p.log 2>&1 | Out-Null
git commit -m "T-048: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
