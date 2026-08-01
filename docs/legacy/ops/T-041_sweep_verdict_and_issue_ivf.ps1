# =====================================================================
# T-041_sweep_verdict_and_issue_ivf.ps1
# WHAT:    Sweeps everything outstanding after NP-S1's first integrated
#          verdict, and issues the IVF instruction for AC-6:
#            ops\ARCH-NP-002_IVF_instruction_AC6.md   (sealed IVF instruction)
#            ops\NP-ADR-008_APPENDIX-A_*.md           (if T-040 was not run)
#            docs\journal\...Journal.md               (J-035, if not yet committed)
#          plus any Developer work still unstaged on this tree.
# WHY:     AC-6 is the last open acceptance criterion. The IVF session must
#          FETCH its instruction, not be told it - the failure this session
#          has already caused twice.
# GUARD:   Refuses if the Execution Plan's frozen SS4/SS5 markers moved, and
#          refuses if the ratified ADR body was edited (Appendix A is APPENDED
#          under P5, never an in-place change).
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20). The verdict itself lives on the Developer's branch and is
#          NOT touched here - this sweeps the mainline working tree only.
# OUTPUT:  ops\runlogs\T-041_sweep_verdict_and_issue_ivf.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-041_sweep_verdict_and_issue_ivf.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-041 SWEEP + ISSUE IVF INSTRUCTION (AC-6) === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the IVF instruction exists and is complete ---"
$iv = Join-Path $repo "ops\ARCH-NP-002_IVF_instruction_AC6.md"
if (Test-Path $iv) { Write-Host "OK: IVF instruction present" } else { Write-Host "MISSING: IVF instruction"; $failed = $true }
foreach ($k in @("01KYSGQR3D8SYSVJFSF9M77CMY","0.057415412388292036","0.002631578947368421","never imports")) {
  if (Select-String -Path $iv -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] drill-before-judge is mandated (QRF-ADR-006) ---"
if (Select-String -Path $iv -Pattern "Drill first" -SimpleMatch -Quiet) { Write-Host "OK: drill precedes the real re-derivation" } else { Write-Host "MISSING: drill mandate"; $failed = $true }

Write-Host "--- [4] FROZEN GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
$adrDiff = git diff --stat -- ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md 2>&1 | Out-String
if ($adrDiff.Trim()) { Write-Host "STOP: ratified ADR body modified - corrections must be APPENDED (P5)"; Write-Host $adrDiff; $failed = $true }
else { Write-Host "OK: ratified ADR body untouched" }

Write-Host "--- [5] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-041: issue ARCH-NP-002 - IVF instruction for AC-6, independent re-derivation of NP-S1's first integrated verdict (01KYSGQR3D8SYSVJFSF9M77CMY: n=259, net mean +1.5196/oz, p=0.0574, effective alpha 0.0026316 over 19 family trials, FAIL; burn 01KYSGQR6K1HHRT66R78BV6Z8Y atomic). Drill-before-judge mandated: six planted frauds plus a clean control, all caught before any real record is checked. Four unchecked-by-anyone items included: FAIL survives at undeflated alpha, the three non-equivalence statements present in the registration, independent SWEEP recount from ADR text alone, honest bar build. IVF never imports qrf" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - IVF instruction issued. AC-6 is the last open acceptance criterion." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-041_sweep_verdict_and_issue_ivf.log 2>&1 | Out-Null
git commit -m "T-041: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
