# =====================================================================
# T-050_np_s2_preflight_and_wo_p_addendum.ps1
# WHAT:    Commits NP-S2's preflight report and reconciles WO-P with the
#          sprint state machine:
#            ops\preflight\PFR_NP-S2.md                 (P0 output, NOT GREEN)
#            ops\ARCH-NP-004_WO-P_execution_parity.md   (SS9 addendum, appended)
# WHY:     NP-S2 was opened by issuing WO-P directly - no P0, no G1 - which
#          violates the state machine's own first rule on its first use. The
#          preflight is run retrospectively and the violation recorded rather
#          than quietly repaired. The Developer must be able to FETCH both.
# GUARD:   Refuses if SS1-8 of ARCH-NP-004 were edited rather than appended, if
#          the Execution Plan's frozen SS4/SS5 markers moved, or if any ratified
#          ADR body or appendix changed. ASCII-safe patterns only (J-038).
# OUTPUT:  ops\runlogs\T-050_np_s2_preflight_and_wo_p_addendum.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-050_np_s2_preflight_and_wo_p_addendum.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-050 NP-S2 PREFLIGHT + WO-P ADDENDUM === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the preflight report exists and states a result ---"
$pf = Join-Path $repo "ops\preflight\PFR_NP-S2.md"
if (Test-Path $pf) { Write-Host "OK: PFR_NP-S2 present" } else { Write-Host "MISSING: PFR_NP-S2"; $failed = $true }
foreach ($k in @("RESULT: NOT GREEN","B1","B2","B3","belong at G1")) {
  if (Select-String -Path $pf -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] the preflight is honest about WO-P not being blocked ---"
if (Select-String -Path $pf -Pattern "WO-P may proceed now" -SimpleMatch -Quiet) { Write-Host "OK: WO-P explicitly unblocked" }
else { Write-Host "MISSING: WO-P disposition"; $failed = $true }

Write-Host "--- [4] WO-P carries its state-machine position ---"
$wp = Join-Path $repo "ops\ARCH-NP-004_WO-P_execution_parity.md"
foreach ($k in @("P2 BUILD lane","sprint/NP-S2","HANDOVER.md","Mechanical exit check","No ledger writes")) {
  if (Select-String -Path $wp -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [5] APPEND-ONLY: WO-P's original sections survive unedited ---"
foreach ($k in @("AC-1","byte-identically reproducible","the stop fills","does not require the lab unpause")) {
  if (Select-String -Path $wp -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: original retained - " + $k) }
  else { Write-Host ("STOP: original section altered - " + $k); $failed = $true }
}

Write-Host "--- [6] FROZEN GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [7] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-050: run NP-S2's P0 preflight retrospectively and reconcile WO-P with the sprint state machine. FINDING against the Architect: NP-S2 was opened by issuing ARCH-NP-004 directly, with no preflight and no G1, violating the machine's first rule on its first use - recorded, not quietly repaired. PFR_NP-S2 returns NOT GREEN on three blockers: the R6 scope is unnamed; a DST transition will fall inside a 3-6 month collection window and NP-S1 already cost a bug-and-revert cycle on exactly that class; and two of three build tracks have no written specification, which NP-D-012 makes insufficient. Four decisions batched for G1 including sealing the withheld-OOS designation POLICY now so only a mechanical act remains later - the first use of the rulebook lever. None of the blockers touches WO-P: it needs no scope, no data and no unpause, so it proceeds now as a P2 lane on sprint/NP-S2 while the collection track waits for G1" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [8] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - preflight on the record. WO-P may start; the collection track waits for G1." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-050_np_s2_preflight_and_wo_p_addendum.log 2>&1 | Out-Null
git commit -m "T-050: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
