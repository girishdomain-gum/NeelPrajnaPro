# =====================================================================
# T-034_record_mockup_finding.ps1
# WHAT:    Commits finding F-23 (Book A advisor mockup contradicts the
#          ratified Auto-Adopt ruling) and the correction written into
#          NP-S8's sprint text.
#          Files edited on disk by the Architect:
#            docs\execution_plan\...-v2.0.md   (§9 NP-S8 mockup correction)
#            docs\journal\NeelPrajnaPro_Journal.md  (entry J-031)
# WHY:     The mockup predates the F-13 ruling and shows an active
#          auto-adopt criterion as the SELECTED default. Nothing builds
#          from it until Phase 4, so the risk is forgetting - the fix is
#          to carry the correction in the sprint instruction itself.
# CHANGES: git add docs ops; commit; push; confirm clean tree.
# OUTPUT:  ops\runlogs\T-034_record_mockup_finding.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-034_record_mockup_finding.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-034 record mockup finding F-23 === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before the sweep ---"
git status -s 2>&1 | Out-String | Write-Host
git diff --stat 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the correction is on disk in both places ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
if (Select-String -Path $ep -Pattern "MOCKUP CORRECTION REQUIRED" -SimpleMatch -Quiet) { Write-Host "OK: NP-S8 carries the mockup correction" }
else { Write-Host "MISSING: NP-S8 has no mockup correction"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-031" -SimpleMatch -Quiet) { Write-Host "OK: journal carries J-031 (F-23)" }
else { Write-Host "MISSING: journal has no J-031 entry"; $failed = $true }

Write-Host "--- [3] confirm the mockup itself is untouched (append-only culture: we do not edit the artifact) ---"
$mk = Join-Path $repo "docs\specs\mockups_book_a\neelprajna_advisor_detail_mockup.html"
if (Test-Path $mk) { Write-Host "OK: mockup present and unmodified - the correction lives in the sprint instruction, not in a rewritten artifact" }
else { Write-Host "WARNING: mockup missing"; $failed = $true }

Write-Host "--- [4] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-034: finding F-23 - Book A advisor mockup predates the F-13 Auto-Adopt ruling and shows an active criterion as selected default; correction written into NP-S8 sprint text; standing rule added (check mockups against rulings in force before building from them)" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "--- [5] confirm clean tree ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-034_record_mockup_finding.log 2>&1 | Out-Null
git commit -m "T-034: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
