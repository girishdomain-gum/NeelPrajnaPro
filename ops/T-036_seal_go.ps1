# =====================================================================
# T-036_seal_go.ps1
# WHAT:    Commits the Owner's GO on Sprint NP-S1 and the Developer boot
#          artifact. Files edited/created on disk by the Architect:
#            docs\execution_plan\...-v2.0.md   (§0 rewritten to IN FLIGHT;
#                                               §4 marked SEALED + GO record)
#            docs\journal\NeelPrajnaPro_Journal.md  (entry J-033)
#            ops\DEVELOPER_BOOT_NP-S1.md       (paste-ready boot prompt)
# WHY:     GO seals ARCH-NP-001. The instruction text is frozen from this
#          commit forward - any later change requires a new ARCH, not an
#          edit. The commit is therefore the seal's own timestamp.
# OUTPUT:  ops\runlogs\T-036_seal_go.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-036_seal_go.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-036 SEAL GO - Sprint NP-S1 === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before the seal ---"
git status -s 2>&1 | Out-String | Write-Host
git diff --stat 2>&1 | Out-String | Write-Host

Write-Host "--- [2] verify the GO is recorded in all three places ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$bp = Join-Path $repo "ops\DEVELOPER_BOOT_NP-S1.md"
if (Select-String -Path $ep -Pattern "SEALED AND IN FLIGHT" -SimpleMatch -Quiet) { Write-Host "OK: execution plan S0 marks the sprint in flight" } else { Write-Host "MISSING: S0 not updated"; $failed = $true }
if (Select-String -Path $ep -Pattern "GO RECORD" -SimpleMatch -Quiet) { Write-Host "OK: execution plan S4 carries the GO record" } else { Write-Host "MISSING: S4 GO record"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-033" -SimpleMatch -Quiet) { Write-Host "OK: journal carries J-033" } else { Write-Host "MISSING: journal J-033"; $failed = $true }
if (Test-Path $bp) { Write-Host "OK: developer boot prompt present" } else { Write-Host "MISSING: boot prompt"; $failed = $true }

Write-Host "--- [3] verify the blocking first obligation appears in all three ---"
$n = 0
foreach ($f in @($ep, $jr, $bp)) {
    if (Select-String -Path $f -Pattern "confirmation" -SimpleMatch -Quiet) { $n++ }
}
Write-Host "span-confirmation obligation present in $n of 3 documents (must be 3)"
if ($n -ne 3) { $failed = $true }

Write-Host "--- [4] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-036: OWNER GO - Sprint NP-S1 sealed and in flight. ARCH-NP-001 sealed with the H-07 mechanical definition; instruction text frozen from this commit. All six preconditions met and recorded. Developer boot prompt created at ops/DEVELOPER_BOOT_NP-S1.md. Blocking first obligation: resolve the H-07 export span and present it to the Owner before anything registers, runs or burns" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host
Write-Host "--- [5] confirm clean tree ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-S1 SEALED. Documentation phase closed; evidence phase begins." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-036_seal_go.log 2>&1 | Out-Null
git commit -m "T-036: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
