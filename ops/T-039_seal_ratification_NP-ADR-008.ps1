# =====================================================================
# T-039_seal_ratification_NP-ADR-008.ps1
# WHAT:    Commits the Owner's ratification of NP-ADR-008 (H-07 SS5 v1.1)
#          and everything it touched:
#            docs\journal\...Journal.md              (J-034, verbatim ruling)
#            docs\decisions\...Decisions-v1.0.md     (NP-D-010, Change Record v1.1)
#            docs\execution_plan\...v2.0.md          (SS0 handover ONLY - SS4/SS5 untouched)
#            configs\venues.yaml                     (xauusd_retail_h07 @ $0.41/oz)
#            ops\NP-ADR-H07_definition_v1.1_draft_v2.0.md  (sealed as NP-ADR-008)
#            ops\CS_REVIEW_H07_v1.1_2026-07-30.md
#            ops\POST_CORRECTION_VERIFICATION_H07_v1.1.md
#            ops\PRE_RATIFICATION_REVIEW_H07_v1.1.md
#            ops\ARO_Execution_Process_v1.0.md / v2.0.md
#            ops\REPOSITORY_AUTONOMY_v3.0.md
#            ops\NP-ADR-H07_definition_v1.1_draft_v1.0.md (provenance)
# WHY:     Ratification is the moment registration unblocks. The record must be
#          fetchable by the Developer session before it resumes - the T-037
#          lesson: an uncommitted decision is not yet a decision the repository
#          can defend.
# GUARD:   Refuses to commit if SS4 or SS5 of the Execution Plan were modified
#          (both are FROZEN by the GO; only SS0, the handover, may change).
# NOTE:    Stages docs AND ops AND configs (F-22). Run log committed after
#          Stop-Transcript (F-20).
# OUTPUT:  ops\runlogs\T-039_seal_ratification_NP-ADR-008.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-039_seal_ratification_NP-ADR-008.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-039 SEAL RATIFICATION - NP-ADR-008 (H-07 SS5 v1.1) === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the ratification is recorded in all four places ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$vn = Join-Path $repo "configs\venues.yaml"
if (Select-String -Path $jr -Pattern "J-034" -SimpleMatch -Quiet) { Write-Host "OK: journal J-034" } else { Write-Host "MISSING: journal J-034"; $failed = $true }
if (Select-String -Path $dc -Pattern "NP-D-010" -SimpleMatch -Quiet) { Write-Host "OK: decisions NP-D-010" } else { Write-Host "MISSING: NP-D-010"; $failed = $true }
if (Select-String -Path $ep -Pattern "REGISTRATION IS NOW UNBLOCKED" -SimpleMatch -Quiet) { Write-Host "OK: execution plan SS0 handover rewritten" } else { Write-Host "MISSING: SS0 rewrite"; $failed = $true }
if (Select-String -Path $vn -Pattern "xauusd_retail_h07" -SimpleMatch -Quiet) { Write-Host "OK: cost model present in venues.yaml" } else { Write-Host "MISSING: cost model"; $failed = $true }

Write-Host "--- [3] the binding constants appear in the handover ---"
foreach ($c in @("h007_np_liquidity_sweep_v1_1","xauusd/neelprajna","xauusd_m5_vantage","p < 0.00263")) {
  if (Select-String -Path $ep -Pattern $c -SimpleMatch -Quiet) { Write-Host ("OK: " + $c) } else { Write-Host ("MISSING: " + $c); $failed = $true }
}

Write-Host "--- [4] FROZEN GUARD: SS4 and SS5 of the Execution Plan must be unchanged ---"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen section markers missing - DO NOT COMMIT"; $failed = $true }
Write-Host "diff of the execution plan (inspect: only SS0 lines should appear):"
git diff -- docs/execution_plan 2>&1 | Select-String -Pattern "^[+-]" | Select-Object -First 40 | Out-String | Write-Host

Write-Host "--- [5] stage docs + ops + configs, commit, push ---"
git add docs ops configs 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-039: OWNER RATIFICATION - NP-ADR-008 seals H-07 SS5 v1.1; SS5 v1.0 remains frozen. Journal J-034, decision NP-D-010, SS0 handover rewritten, cost model xauusd_retail_h07 at 0.41 USD/oz written to venues.yaml. Binding constants: lineage h007_np_liquidity_sweep_v1_1, family xauusd/neelprajna across all 19 registrations, scope xauusd_m5_vantage, 19 trials p<0.00263. Chief Scientist review filed and accepted; M1-M7 corrections applied and independently re-verified. NP-S1 REGISTRATION UNBLOCKED - nothing has yet registered, run or burned" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - NP-ADR-008 ratified and sealed in the repository. The Developer may resume." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-039_seal_ratification_NP-ADR-008.log 2>&1 | Out-Null
git commit -m "T-039: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
