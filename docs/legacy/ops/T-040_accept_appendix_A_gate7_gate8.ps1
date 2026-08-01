# =====================================================================
# T-040_accept_appendix_A_gate7_gate8.ps1
# WHAT:    Commits the Owner's acceptance of NP-ADR-008 Appendix A
#          (Gate 7 / Gate 8 provenance correction, Constitution SS7.2):
#            ops\NP-ADR-008_APPENDIX-A_provenance_correction.md  (ACCEPTED header)
#            docs\journal\...Journal.md                          (J-035)
# WHY:     The Developer is halted behind DEVQ-NP-003 and DEVQ-NP-004 and
#          must be able to FETCH the answers, not be told about them. The
#          T-037 lesson: an uncommitted decision is not yet a decision the
#          repository can defend - and this session has now caused that
#          failure twice.
# GUARD:   Refuses if SS5 v1.0's frozen text or SS4's seal line moved. Appendix A
#          is an APPENDED correction (P5); the ratified ADR body is not edited.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-040_accept_appendix_A_gate7_gate8.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-040_accept_appendix_A_gate7_gate8.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-040 ACCEPT APPENDIX A (Gate 7 / Gate 8) === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] acceptance and journal entry are present ---"
$ax = Join-Path $repo "ops\NP-ADR-008_APPENDIX-A_provenance_correction.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
if (Test-Path $ax) { Write-Host "OK: appendix A exists" } else { Write-Host "MISSING: appendix A"; $failed = $true }
if (Select-String -Path $ax -Pattern "ACCEPTED 2026-07-30" -SimpleMatch -Quiet) { Write-Host "OK: acceptance header" } else { Write-Host "MISSING: acceptance header"; $failed = $true }
if (Select-String -Path $ax -Pattern "was Gate 8" -SimpleMatch -Quiet) { Write-Host "OK: the verbatim T3 header quote is on record" } else { Write-Host "MISSING: T3 quote"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-035" -SimpleMatch -Quiet) { Write-Host "OK: journal J-035" } else { Write-Host "MISSING: J-035"; $failed = $true }

Write-Host "--- [3] the 17 roster answer is on record ---"
if (Select-String -Path $ax -Pattern "H-01" -SimpleMatch -Quiet) { Write-Host "OK: roster answer present (H-01..H-06, H-08..H-18)" } else { Write-Host "MISSING: roster answer"; $failed = $true }

Write-Host "--- [4] FROZEN GUARD: NP-ADR-008 body and Execution Plan SS4/SS5 unchanged ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing - DO NOT COMMIT"; $failed = $true }
$adrDiff = git diff --stat -- ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md 2>&1 | Out-String
if ($adrDiff.Trim()) { Write-Host "STOP: the ratified ADR body was modified - Appendix A must be APPENDED, not an edit"; Write-Host $adrDiff; $failed = $true }
else { Write-Host "OK: ratified ADR body untouched (correction is appended, per P5)" }

Write-Host "--- [5] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-040: OWNER OK (SS7.2 clarification) - NP-ADR-008 Appendix A accepted. T3_SweepFVGGate.mqh header says 'was Gate 8': SS5 v1.0 is a hybrid - Gate 7's absorbed pool engine plus Gate 8's mandatory MSS/FVG chain - so the seven divergences are largely cross-hypothesis, not cross-version. kb.json shows H-07 = equal-high/low sweep + reclose (no MSS) with v1.1's exact parameters, so the Python implements H-07 as defined; H-07's MQL5 original is deleted and unrecoverable. Nothing ratified changed; no re-registration. DEVQ-NP-003 resolved (the 17 = H-01..H-06, H-08..H-18; counting is not selecting), DEVQ-NP-004 resolved. Journal J-035" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - Appendix A accepted and on the record. The Developer may register the 17 and proceed." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-040_accept_appendix_A_gate7_gate8.log 2>&1 | Out-Null
git commit -m "T-040: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
