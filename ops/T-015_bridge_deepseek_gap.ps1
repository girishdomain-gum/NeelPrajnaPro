# =====================================================================
# T-015_bridge_deepseek_gap.ps1
# WHAT:    Commits the gap-bridging pass the Architect performed via
#          connector: 7 stale cross-references fixed (decisions,
#          execution_plan, reference x3, vv_plan x2); NB-6
#          Interpretation-Lock drill added to VV_Plan (5->6 classes);
#          "failure blast radius" framing added to Architecture Part A;
#          journal J-015 recording the full six-document review verdict.
# WHY:     Deep review of 6 external docs (4 DeepSeek roadmap/whiteboard/
#          IVF + 2 platform-architecture/scientific-model drafts) found:
#          ~80% independent convergence (no gap), 2 places where OUR docs
#          are already ahead (F-9 wick bug, F-2/F-15 unsealed-loop line -
#          both already fixed here, not backported), 2 small genuine
#          additions (adopted), 1 real scope conflict (full component-
#          absorption roadmap - held for Owner ruling, NOT adopted).
# CHANGES: docs only (5 files) + this script + its log. NOTHING deleted.
# OUTPUT:  ops\runlogs\T-015_bridge_deepseek_gap.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-015_bridge_deepseek_gap.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-015 bridge DeepSeek gap === $(Get-Date -Format o)"

Write-Host "--- [1] spot-check the changes landed ---"
$checks = @(
    @{f="docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"; pat="docs\\vision\\ master"},
    @{f="docs\execution_plan\NeelPrajnaPro_Execution_Plan-v1.0.md"; pat="journal master"},
    @{f="docs\reference\NeelPrajnaPro_Reference-v1.0.md"; pat="docs\\scientific_model\\ master"},
    @{f="docs\vv_plan\NeelPrajnaPro_VV_Plan-v1.0.md"; pat="NB-6"},
    @{f="docs\architecture\NeelPrajnaPro_Architecture-v1.0.md"; pat="Failure asymmetry"},
    @{f="docs\journal\NeelPrajnaPro_Journal.md"; pat="J-015"}
)
foreach ($c in $checks) {
    if (Select-String -Path (Join-Path $repo $c.f) -Pattern $c.pat -Quiet -SimpleMatch) {
        Write-Host "OK: $($c.f) contains '$($c.pat)'"
    } else { Write-Host "MISSING in $($c.f): $($c.pat)"; $failed = $true }
}

Write-Host "--- [2] commit + push ---"
git add docs ops 2>&1 | Out-String | Write-Host
git commit -m "T-015: bridge DeepSeek 6-doc review - NB-6 Interpretation-Lock added, failure-asymmetry framing added, 7 stale cross-refs fixed; full-component-absorption roadmap held for Owner ruling (not adopted)" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

# F-20 fix: commit the transcript AFTER it's closed, in its own step
Set-Location $repo
git add ops/runlogs/T-015_bridge_deepseek_gap.log 2>&1 | Out-Null
git commit -m "T-015: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
