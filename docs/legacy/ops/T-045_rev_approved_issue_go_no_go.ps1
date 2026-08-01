# =====================================================================
# T-045_rev_approved_issue_go_no_go.ps1
# WHAT:    Records the Chief Scientist REV (APPROVED 8.8/10, GO with
#          qualification), applies its mandated scope narrowing, and issues
#          the Owner's Go/No-Go packet:
#            docs\coordination\notes\NOTE-NP-002_*.md  (SS7 appended, SS1-6 unedited)
#            ops\REV_BRIEF_NP-S1.md                    (the brief reviewed)
#            ops\GO_NO_GO_PACKET_NP-S1.md              (the Owner's decision sheet)
# WHY:     The REV's qualification is binding on every downstream citation of
#          this result. It must be in the repository before the Owner rules,
#          not carried in chat.
# GUARD:   Refuses if the comparison report's SS1-6 were edited rather than
#          appended, if any ratified ADR body or appendix moved, if the
#          Execution Plan's frozen SS4/SS5 markers vanished, or if the IVF's
#          original RED line was rewritten.
# NOTE:    Stages docs AND ops (F-22). Run log committed after Stop-Transcript
#          (F-20).
# OUTPUT:  ops\runlogs\T-045_rev_approved_issue_go_no_go.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-045_rev_approved_issue_go_no_go.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-045 REV APPROVED + GO/NO-GO PACKET === $(Get-Date -Format o)"

Write-Host "--- [1] outstanding before commit ---"
git status -s 2>&1 | Out-String | Write-Host

Write-Host "--- [2] the REV's mandated narrowing is in the comparison report ---"
$cr = Join-Path $repo "docs\coordination\notes\NOTE-NP-002_h007_prediction_comparison_report.md"
foreach ($k in @("REV-MANDATED SCOPE NARROWING","neither framework produced statistically significant evidence","differed materially in execution model","independent reimplementation without consulting source code")) {
  if (Select-String -Path $cr -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] APPEND-ONLY: the report's own conclusion must survive unedited ---"
if (Select-String -Path $cr -Pattern "AC-4 satisfied" -SimpleMatch -Quiet) { Write-Host "OK: SS6 conclusion intact (SS7 is an append)" } else { Write-Host "STOP: SS6 conclusion missing - the report was edited, not appended"; $failed = $true }

Write-Host "--- [4] Go/No-Go packet present and honest ---"
$gp = Join-Path $repo "ops\GO_NO_GO_PACKET_NP-S1.md"
if (Test-Path $gp) { Write-Host "OK: packet present" } else { Write-Host "MISSING: packet"; $failed = $true }
foreach ($k in @("8.8","corroborative, never confirmatory","Against the Architect","was Gate 8","undeflated")) {
  if (Select-String -Path $gp -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [5] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
$iv = Join-Path $repo "ivf\reports\IVF_NP-S1_AC6.md"
if (Test-Path $iv) {
  if (Select-String -Path $iv -Pattern "OVERALL VERDICT: RED" -SimpleMatch -Quiet) { Write-Host "OK: IVF original RED preserved" }
  else { Write-Host "STOP: IVF original RED rewritten - P5 violation"; $failed = $true }
}
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
    git commit -m "T-045: Chief Scientist REV APPROVED (8.8/10, GO with qualification). Binding narrowing appended to the comparison report as SS7: the comparison is same detector definition + DIFFERENT execution rules, and NP-S1 established no equivalence between the bespoke and Battery execution strategies - only that each, under its own execution model, failed to find statistically significant support over the designated window. Canonical claim to be quoted not paraphrased. CS added a structural finding converging independently with Appendix B.9: specifications must permit independent reimplementation without consulting source code. CS recommends NP-S2 build execution-model parity (variable stops/targets) BEFORE collecting more evidence. Owner Go/No-Go packet issued with three decisions: GO, execution-parity-first, and adoption of the specification-completeness rule" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

Write-Host "--- [7] tree state after commit ---"
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - REV recorded, narrowing applied, Go/No-Go packet on the record. The Owner's move." }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-045_rev_approved_issue_go_no_go.log 2>&1 | Out-Null
git commit -m "T-045: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
