# =====================================================================
# T-044_hc_passed_issue_rev.ps1
# WHAT:    Records the Owner's HC PASS and issues the sprint-level REV brief:
#            docs\journal\...Journal.md        (J-036)
#            ops\REV_BRIEF_NP-S1.md            (five adversarial questions)
# WHY:     REV is the last review before the Owner's Go/No-Go. The Chief
#          Scientist reviews from the repository, so the brief and everything
#          it indexes must be fetchable before the review begins.
# GUARD:   Refuses if the Execution Plan's frozen SS4/SS5 markers moved, if any
#          ratified ADR body or appendix was edited (all corrections are
#          APPENDED under P5), or if the IVF report's original RED line was
#          rewritten.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-044_hc_passed_issue_rev.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-044_hc_passed_issue_rev.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-044 HC PASSED + ISSUE REV BRIEF === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] HC pass and REV brief are on record ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$rv = Join-Path $repo "ops\REV_BRIEF_NP-S1.md"
if (Select-String -Path $jr -Pattern "J-036" -SimpleMatch -Quiet) { Write-Host "OK: journal J-036" } else { Write-Host "MISSING: J-036"; $failed = $true }
if (Select-String -Path $jr -Pattern "HC passed. Proceed to REV" -SimpleMatch -Quiet) { Write-Host "OK: Owner HC wording recorded verbatim" } else { Write-Host "MISSING: HC wording"; $failed = $true }
if (Test-Path $rv) { Write-Host "OK: REV brief present" } else { Write-Host "MISSING: REV brief"; $failed = $true }

Write-Host "--- [3] the REV brief names the sprint's weaknesses, not just its wins ---"
foreach ($k in @("trade rule was substituted","text-code fidelity","inflationary","sign disagreement","against me")) {
  if (Select-String -Path $rv -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [4] the IVF's original RED is still present (SS7 is an append, not an edit) ---"
$iv = Join-Path $repo "ivf\reports\IVF_NP-S1_AC6.md"
if (Test-Path $iv) {
  if (Select-String -Path $iv -Pattern "OVERALL VERDICT: RED" -SimpleMatch -Quiet) { Write-Host "OK: original RED preserved" }
  else { Write-Host "STOP: the IVF report no longer records its original RED - P5 violation"; $failed = $true }
} else { Write-Host "NOTE: IVF report not yet merged to this branch - run T-043 first"; $failed = $true }

Write-Host "--- [5] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
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
    git commit -m "T-044: Owner HC PASSED - 'HC passed. Proceed to REV.' Journal J-036 records AC-6 closing GREEN after a correct RED: the recount gap was a real P6 defect (two faithful readers of the sealed text produced different event sets), localized to pool formation (pivots agreed exactly at 3,099), pinned by Appendix B, and re-derived exact at 3,099/465/325 with no tuning. Root causes B.3 (suppression compared the pivot's raw price, not the candidate pool's computed level) and B.4 (unflagged per-bar ordering) - NOT B.5, which the Architect had named and which was correct. Lesson recorded: disclosing assumptions is insufficient unless disclosed at the granularity where two implementers could differ. Limitation permanent: text-code fidelity, not independent code correctness. REV brief issued with five adversarial questions, the first being that the audited engine could not express the evidenced stop/target, so the Battery judged sweep-then-hold-12-bars and the comparison runs between two instruments on different strategies" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [7] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - HC recorded, REV brief issued. Relay to the Chief Scientist; then Go/No-Go." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-044_hc_passed_issue_rev.log 2>&1 | Out-Null
git commit -m "T-044: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
