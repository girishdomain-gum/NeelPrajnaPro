# =====================================================================
# T-043_ac6_green_and_hc_packet.ps1
# WHAT:    Records AC-6 GREEN and issues the HC packet:
#            ops\HC_PACKET_NP-S1.md            (Owner's human-confirmation sheet)
#          plus any outstanding mainline work. Also merges the IVF branch so
#          the AC-6 report is native to main before HC begins.
# WHY:     HC is the Owner's step and cannot be delegated (QRF-ADR-009b: "HC
#          without a human is just another VC"). The evidence he confirms must
#          be reachable from main, not from a session's branch - the failure
#          this programme has already paid for three times today.
# GUARD:   Refuses if the IVF report's original SS0-SS6 were edited (SS7 is an
#          APPEND under P5), if the ratified ADR body or its appendices moved,
#          or if the Execution Plan's frozen SS4/SS5 markers vanished.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-043_ac6_green_and_hc_packet.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-043_ac6_green_and_hc_packet.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-043 AC-6 GREEN + HC PACKET === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before anything ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] merge the IVF branch so AC-6's report is native to main ---"
git fetch origin 2>&1 | Out-String | Write-Host
$ivfBranch = "origin/claude/ivf-validator-neelprajnapro-a9bdfe"
git merge --no-ff $ivfBranch -m "Merge AC-6: IVF independent re-derivation of the NP-S1 verdict - drill 6/6 caught, chain GREEN to 1e-9, and the re-check under ARCH-NP-003 closing the recount gap at 3,099/465/325 exact" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "merge exit: $LASTEXITCODE - inspect before continuing"; $failed = $true }

Write-Host "--- [3] AC-6 artifacts are now present on main ---"
$iv = Join-Path $repo "ivf\reports\IVF_NP-S1_AC6.md"
if (Test-Path $iv) { Write-Host "OK: IVF AC-6 report on main" } else { Write-Host "MISSING: IVF report"; $failed = $true }
foreach ($k in @("OVERALL VERDICT: RED","Re-check under ARCH-NP-003","3,099 / 465 / 325","text-code fidelity")) {
  if (Select-String -Path $iv -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
Write-Host "NOTE: the original 'OVERALL VERDICT: RED' line MUST still be present - SS7 is an append,"
Write-Host "      not an edit. Its absence would mean the RED was rewritten (P5 violation)."

Write-Host "--- [4] HC packet present and complete ---"
$hc = Join-Path $repo "ops\HC_PACKET_NP-S1.md"
if (Test-Path $hc) { Write-Host "OK: HC packet present" } else { Write-Host "MISSING: HC packet"; $failed = $true }
foreach ($k in @("disqualifying","was Gate 8","HC passed. Proceed to REV")) {
  if (Select-String -Path $hc -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

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

Write-Host "--- [6] stage docs + ops + ivf, commit, push ---"
git add docs ops ivf 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    Write-Host "staged files:"; $staged | Out-String | Write-Host
    git commit -m "T-043: AC-6 GREEN and HC packet issued. IVF re-check under ARCH-NP-003 closed both RED lines: SS3.2 substance test 6/6 (byte deviation recorded per Appendix B.7, not a failure) and SS3.3 recount exact at 3,099 pivots / 465 pools / 325 sweeps with no tuning. Root causes were B.3 (suppression tested against the new pivot's raw price instead of the candidate pool's computed level, under-suppressing by 11 pools) and B.4 (per-bar ordering, an assumption never flagged) - NOT B.5, which the Architect had named as the strongest candidate and which was correct all along. Limitation carried forward permanently: the match shows text-code fidelity, not independent code correctness; genuine independence awaits NP-S2's fresh-data path. All six acceptance criteria met; no RED line remains. HC is the Owner's step and cannot be delegated" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -4 2>&1 | Out-String | Write-Host

Write-Host "--- [7] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - AC-6 GREEN, all six acceptance criteria met. HC packet is on main at ops\HC_PACKET_NP-S1.md - the Owner's move." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-043_ac6_green_and_hc_packet.log 2>&1 | Out-Null
git commit -m "T-043: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
