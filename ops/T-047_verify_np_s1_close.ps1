# =====================================================================
# T-047_verify_np_s1_close.ps1
# WHAT:    Corrected re-verification of the NP-S1 close, and commits the
#          finding record for T-046's false negative:
#            docs\journal\...Journal.md   (J-038)
# WHY:     T-046 reported RESULT: FAILED on one check that searched for an
#          ASCII hyphen where the document carries an em-dash. The content it
#          committed (39059c7) was correct; the RESULT line was not. Per P5 the
#          old log stands unedited; this script re-verifies honestly and the
#          journal records the finding.
# RULE APPLIED (new, J-038): a verification pattern is copied from the artifact
#          it verifies, never retyped - and an ASCII-only script matches on an
#          ASCII-safe SUBSTRING rather than on punctuation it cannot reproduce.
#          Every pattern below is punctuation-free by construction.
# OUTPUT:  ops\runlogs\T-047_verify_np_s1_close.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-047_verify_np_s1_close.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-047 VERIFY NP-S1 CLOSE (corrected) === $(Get-Date -Format o)"

$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"

Write-Host "--- [1] SS12 sprint-outputs entry - ASCII-safe substrings only ---"
foreach ($k in @("twice framed, once judged","GO record (Owner, verbatim)","The four discoveries worth more than the verdict","integrated verdicts 1")) {
  if (Select-String -Path $ep -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
Write-Host "--- [1b] the placeholder is gone ---"
if (Select-String -Path $ep -Pattern "none yet" -SimpleMatch -Quiet) { Write-Host "STOP: SS12 placeholder still present"; $failed = $true }
else { Write-Host "OK: SS12 placeholder removed" }

Write-Host "--- [2] SS0 handover, SS6 WO-P, decisions ---"
foreach ($p in @(@($ep,"CLOSED AND ACCEPTED"),@($ep,"NP-S2 IS THE OPEN SPRINT"),@($ep,"EXECUTION-MODEL PARITY"),@($jr,"J-037"),@($jr,"J-038"),@($dc,"NP-D-011"),@($dc,"NP-D-012"))) {
  if (Select-String -Path $p[0] -Pattern $p[1] -SimpleMatch -Quiet) { Write-Host ("OK: " + $p[1]) } else { Write-Host ("MISSING: " + $p[1]); $failed = $true }
}

Write-Host "--- [3] FROZEN GUARD: SS4 and SS5 still untouched ---"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }

Write-Host "--- [4] T-046's own log is unedited (P5 - the FAILED line stands) ---"
$t46 = Join-Path $repo "ops\runlogs\T-046_close_np_s1.log"
if (Select-String -Path $t46 -Pattern "RESULT: FAILED" -SimpleMatch -Quiet) { Write-Host "OK: T-046 log preserved with its FAILED line - corrected by record, not by rewrite" }
else { Write-Host "STOP: T-046's log was altered - P5 violation"; $failed = $true }

Write-Host "--- [5] the close commit is on origin ---"
git fetch origin 2>&1 | Out-String | Write-Host
git log --oneline -1 origin/main 2>&1 | Out-String | Write-Host
git status -sb 2>&1 | Out-String | Write-Host

Write-Host "--- [6] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-047: corrected re-verification of the NP-S1 close. T-046 reported RESULT: FAILED on a false negative - its check searched for an ASCII hyphen where the document carries an em-dash, so it missed an SS12 entry that was present, correct and committed at 39059c7. Journal J-038 records the finding against the Architect (F-18 species, and J-037 retro item (d) recurring inside the commit that recorded it). New standing rule: a verification pattern is copied from the artifact it verifies, never retyped; an ASCII-only script matches on an ASCII-safe substring. T-046's log stands unedited with its FAILED line - corrected by record, not by rewrite (P5). The sprint close itself is unaffected: NP-S1 is closed and accepted" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-S1's close verified correctly. T-046's FAILED line was a false negative, now recorded as J-038." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-047_verify_np_s1_close.log 2>&1 | Out-Null
git commit -m "T-047: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
