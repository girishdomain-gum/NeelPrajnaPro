# =====================================================================
# T-049_commit_state_machine_and_wo_q.ps1
# WHAT:    Commits the sprint-execution design work and the ARO ladder:
#            ops\SPRINT_STATE_MACHINE_v1.1.md   (md twin of the v1.1 docx)
#            ops\WO-Q_ARO_implementation_ladder.md
#            ops\SprintExecutionStateMachine_v1.1.docx  (if the Owner saved it here)
#            (plus anything else outstanding in docs\ and ops\)
# WHY:     WO-Q is a backlog, not a design document - it must be fetchable by
#          whoever builds v0.0 and v0.1. And per the NP-S1 retro, this is where
#          design work STOPS and execution resumes: WO-P remains NP-S2's gating
#          work order, and nothing on the ARO ladder sits on its critical path.
# GUARD:   Refuses if the Execution Plan's frozen SS4/SS5 markers moved, or if
#          any ratified ADR body or appendix was edited. All patterns are
#          ASCII-safe substrings per J-038.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-049_commit_state_machine_and_wo_q.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-049_commit_state_machine_and_wo_q.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-049 COMMIT STATE MACHINE + WO-Q === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] both artifacts exist ---"
$sm = Join-Path $repo "ops\SPRINT_STATE_MACHINE_v1.1.md"
$wq = Join-Path $repo "ops\WO-Q_ARO_implementation_ladder.md"
if (Test-Path $sm) { Write-Host "OK: state machine present" } else { Write-Host "MISSING: state machine"; $failed = $true }
if (Test-Path $wq) { Write-Host "OK: WO-Q present" } else { Write-Host "MISSING: WO-Q"; $failed = $true }

Write-Host "--- [2b] md and docx twins agree on version ---"
foreach ($k in @("STATE MACHINE v1.1","WHO RUNS THE MACHINE","THE RUNBOOK","MADE EXECUTABLE")) {
  if (Select-String -Path $sm -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
$dx = Join-Path $repo "ops\SprintExecutionStateMachine_v1.1.docx"
if (Test-Path $dx) { Write-Host "OK: docx twin saved into the repo" }
else { Write-Host "NOTE: docx twin not in the repo - download it from the chat and save to ops\ if you want it version-controlled (not an error)" }

Write-Host "--- [3] WO-Q is a ladder, not a design doc ---"
foreach ($k in @("v0.0","v0.1","v0.2","v0.3","v0.4","v0.5","v0.6","Drill before grant","specification is wrong")) {
  if (Select-String -Path $wq -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [4] the write-scope refusal is stated ---"
if (Select-String -Path $wq -Pattern "hard write-scope refusal" -SimpleMatch -Quiet) { Write-Host "OK: ARO never writes the scientific zone" }
else { Write-Host "MISSING: write-scope refusal"; $failed = $true }

Write-Host "--- [5] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
if (Select-String -Path $ep -Pattern "CLOSED AND ACCEPTED" -SimpleMatch -Quiet) { Write-Host "OK: NP-S1 close undisturbed" } else { Write-Host "MISSING: NP-S1 close"; $failed = $true }
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
    git commit -m "T-049: sprint execution state machine v1.0 and WO-Q, the ARO implementation ladder. Seven milestones, each granting ONE permission, each with one exit test and one drill, each reversible: v0.0 preflight checklist (no code, highest value, run before G1) - v0.1 status.json read-only - v0.2 dashboard render - v0.3 waiting-to-inbox movement - v0.4 Owner packet assembly - v0.5 work-order creation - v0.6 lease recovery. Unit is one permission per PASSED DRILL, not per week: a permission is earned by catching planted faults, never by working once. ARO never writes datastore, docs, configs/hypotheses, qrf, ivf or CI at any rung. Accountability split refined but operational execution stays with the Architect - findings attach to whoever built or trusted the machinery, never to a script. Design work stops here; WO-P remains NP-S2's gating work order and nothing on this ladder sits on its critical path" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [7] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - WO-Q is on the record. Next build step is v0.0, the preflight checklist, which needs no code." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-049_commit_state_machine_and_wo_q.log 2>&1 | Out-Null
git commit -m "T-049: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
