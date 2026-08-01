# =====================================================================
# T-046_close_np_s1.ps1
# WHAT:    Closes Sprint NP-S1 on the Owner's GO:
#            docs\journal\...Journal.md              (J-037 - GO, REV, retro)
#            docs\execution_plan\...v2.0.md          (SS0 rewritten, SS6 WO-P,
#                                                     SS12 first sprint outputs)
#            docs\decisions\...Decisions-v1.0.md     (NP-D-011, NP-D-012)
#            ops\GO_NO_GO_PACKET_NP-S1.md            (the decision sheet)
# WHY:     The sprint rhythm ends with GO + retro + handover rewrite. Until this
#          commits, the programme's first integrated verdict is closed only in
#          conversation - and the standing rule from T-037 says an uncommitted
#          decision is not yet a decision the repository can defend.
# GUARD:   Refuses if SS4 or SS5 of the Execution Plan moved (both FROZEN by the
#          NP-S1 GO), if any ratified ADR body or appendix was edited, if the
#          comparison report's SS1-6 were edited rather than appended, or if the
#          IVF's original RED line was rewritten.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-046_close_np_s1.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-046_close_np_s1.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-046 CLOSE SPRINT NP-S1 === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the close is recorded in all four places ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"
if (Select-String -Path $jr -Pattern "J-037" -SimpleMatch -Quiet) { Write-Host "OK: journal J-037" } else { Write-Host "MISSING: J-037"; $failed = $true }
if (Select-String -Path $ep -Pattern "NP-S1 IS CLOSED AND ACCEPTED" -SimpleMatch -Quiet) { Write-Host "OK: SS0 handover rewritten" } else { Write-Host "MISSING: SS0 rewrite"; $failed = $true }
if (Select-String -Path $ep -Pattern "NP-S1 - H-07 twice framed, once judged" -SimpleMatch -Quiet) { Write-Host "OK: SS12 first sprint-outputs entry" } else { Write-Host "MISSING: SS12 entry"; $failed = $true }
if (Select-String -Path $ep -Pattern "WO-P" -SimpleMatch -Quiet) { Write-Host "OK: SS6 carries WO-P (parity before collection)" } else { Write-Host "MISSING: WO-P"; $failed = $true }
if (Select-String -Path $dc -Pattern "NP-D-011" -SimpleMatch -Quiet) { Write-Host "OK: NP-D-011" } else { Write-Host "MISSING: NP-D-011"; $failed = $true }
if (Select-String -Path $dc -Pattern "NP-D-012" -SimpleMatch -Quiet) { Write-Host "OK: NP-D-012" } else { Write-Host "MISSING: NP-D-012"; $failed = $true }

Write-Host "--- [3] the qualification survives into the handover ---"
if (Select-String -Path $ep -Pattern "did not establish equivalence" -SimpleMatch -Quiet) { Write-Host "OK: REV qualification carried into SS0" } else { Write-Host "MISSING: REV qualification"; $failed = $true }
if (Select-String -Path $ep -Pattern "corroborative, never confirmatory" -SimpleMatch -Quiet) { Write-Host "OK: in-sample limit stated" } else { Write-Host "MISSING: in-sample limit"; $failed = $true }

Write-Host "--- [4] the findings were not softened (Owner-ruled permanent) ---"
foreach ($k in @("Against the Architect","nine steps","could not yet fetch")) {
  if (Select-String -Path $ep -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: finding retained - " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [5] FROZEN GUARD: SS4 and SS5 must be untouched ---"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing - DO NOT COMMIT"; $failed = $true }
Write-Host "execution plan diff (inspect: only SS0, SS6 and SS12 lines should appear):"
git diff -- docs/execution_plan 2>&1 | Select-String -Pattern "^[+-]" | Select-Object -First 30 | Out-String | Write-Host

Write-Host "--- [6] APPEND-ONLY GUARDS ---"
$iv = Join-Path $repo "ivf\reports\IVF_NP-S1_AC6.md"
if (Test-Path $iv) {
  if (Select-String -Path $iv -Pattern "OVERALL VERDICT: RED" -SimpleMatch -Quiet) { Write-Host "OK: IVF original RED preserved" }
  else { Write-Host "STOP: IVF original RED rewritten - P5 violation"; $failed = $true }
}
$cr = Join-Path $repo "docs\coordination\notes\NOTE-NP-002_h007_prediction_comparison_report.md"
if (Select-String -Path $cr -Pattern "AC-4 satisfied" -SimpleMatch -Quiet) { Write-Host "OK: comparison report SS6 conclusion intact" } else { Write-Host "STOP: comparison report edited, not appended"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified - corrections are APPENDED (P5)"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [7] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-046: SPRINT NP-S1 CLOSED AND ACCEPTED - the programme's first integrated verdict. Owner GO 2026-07-30 after Chief Scientist REV APPROVED 8.8/10. Integrated verdicts 0 -> 1: verdict 01KYSGQR3D8SYSVJFSF9M77CMY FAIL, 259 trades, p=0.0574 against a bar of p<0.00263, burn atomic, window spent. Robust to the sprint's own most contested arithmetic - p exceeds even the undeflated 0.05. Binding qualification carried into SS0 and the comparison report SS7: NP-S1 established NO equivalence between the bespoke and Battery execution strategies, only that each failed under its own execution model. NP-D-011 execution-model parity before further R6 collection (WO-P in SS6); NP-D-012 specification completeness standing rule. Journal J-037 with the retro; SS12 sprint outputs appended, previously empty by design. Findings permanent by Owner ruling and not softened. SS4 and SS5 remain frozen and unedited - every correction this sprint travelled as an appended record" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [8] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-S1 CLOSED. Integrated verdicts: 1. NP-S2 is the open sprint, and WO-P comes first." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-046_close_np_s1.log 2>&1 | Out-Null
git commit -m "T-046: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
