# =====================================================================
# T-042_appendix_B_and_ivf_recheck.ps1
# WHAT:    Commits the response to the IVF's RED on AC-6:
#            ops\NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md
#            ops\ARCH-NP-003_IVF_recheck_instruction.md
# WHY:     The IVF returned RED on two of the four unchecked items: the three
#          non-equivalence statements are not byte-verbatim, and an independent
#          recount from the sealed text produced 331 sweeps against 325. The
#          first is dispositioned (accept as-is; re-registration would orphan
#          the verdict and spend two more family trials). The second is a real
#          P6 gap - two faithful readers of the normative text produced
#          different event sets - and is closed by pinning the mechanics the
#          text left unstated. The IVF must FETCH both, not be told them.
# GUARD:   Refuses if the ratified ADR body, its Appendix A, the Execution
#          Plan's frozen SS4/SS5, or the IVF's original report were modified -
#          all corrections here are APPENDED under P5, never edits.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-042_appendix_B_and_ivf_recheck.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-042_appendix_B_and_ivf_recheck.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-042 APPENDIX B + IVF RE-CHECK (AC-6 RED response) === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] both artifacts exist and carry their load-bearing content ---"
$b  = Join-Path $repo "ops\NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md"
$r  = Join-Path $repo "ops\ARCH-NP-003_IVF_recheck_instruction.md"
if (Test-Path $b) { Write-Host "OK: Appendix B present" } else { Write-Host "MISSING: Appendix B"; $failed = $true }
if (Test-Path $r) { Write-Host "OK: re-check instruction present" } else { Write-Host "MISSING: re-check instruction"; $failed = $true }
foreach ($k in @("ANCHORED on the newest pivot","p+1 and p+2","3,099 pivots","465 pools","325 sweeps")) {
  if (Select-String -Path $b -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: pinned - " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
if (Select-String -Path $r -Pattern "Do not tune to reach 325" -SimpleMatch -Quiet) { Write-Host "OK: anti-tuning clause present" } else { Write-Host "MISSING: anti-tuning clause"; $failed = $true }

Write-Host "--- [3] the RED is preserved, not softened ---"
$iv = Join-Path $repo "ivf\reports\IVF_NP-S1_AC6.md"
if (Test-Path $iv) {
  if (Select-String -Path $iv -Pattern "OVERALL VERDICT: RED" -SimpleMatch -Quiet) { Write-Host "OK: original IVF RED still stands in its report" }
  else { Write-Host "STOP: the IVF report no longer records RED - it must not be edited"; $failed = $true }
} else { Write-Host "NOTE: IVF report not on this branch yet (lives on the IVF branch) - not an error" }

Write-Host "--- [4] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md")) {
  $d = git diff --stat -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " was modified - corrections must be APPENDED (P5)"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [5] stage docs + ops, commit, push ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-042: respond to the IVF RED on AC-6. Appendix B pins the detector mechanics NP-ADR-008 SS3 left unstated - anchored (non-transitive) pool membership, entire suppression by active pools only, sweep-checks-before-pool-formation ordering, and reclose testable at p, p+1 AND p+2 - after localizing the 331-vs-325 gap to pool formation (pivots agreed exactly at 3,099; pools differed by 11). Target for re-derivation: 3,099 pivots / 465 pools / 325 sweeps. B.7 accepts the registration wording as-is (re-registration would orphan the verdict and spend two more trials); finding recorded against the Architect for requiring verbatim text without supplying it. B.9 opens a standing rule after the day's third instance of a normative text unable to reproduce its own output without reading code. ARCH-NP-003 re-checks only SS3.2 and SS3.3; the drill, the chain re-derivation and SS3.1/SS3.4 stand" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [6] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - Appendix B and the re-check instruction are on the record. AC-6 remains RED until the IVF re-check closes it." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-042_appendix_B_and_ivf_recheck.log 2>&1 | Out-Null
git commit -m "T-042: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
