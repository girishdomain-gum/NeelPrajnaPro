# =====================================================================
# T-030_execution_plan_v2.ps1
# WHAT:    Version transition for the Execution Plan per the structure law
#          (only the current version lives in a thing-folder; priors archive).
#          v1.0 md AND its docx twin both move to archive together - the
#          docx twin is stale the moment v2.0 exists, and leaving it beside
#          v2.0 would be a divergence finding under the twin rule.
# WHY:     Owner found v1.0 out of sync with the ratified architecture:
#          it planned NP-S1..S4 only and never showed how the two-organ
#          destination gets built. v2.0 adds the destination statement,
#          the component map, and Phases 3-5 (Contract v2, Knowledge Graph,
#          both dashboards, Pattern Evolution).
# CHANGES: git mv of v1.0 md+docx to docs\archive\execution_plan\;
#          v2.0 md already written by the Architect via connector;
#          commit docs+ops together; push.
# NOTE:    After this run docs\execution_plan\ holds exactly ONE file
#          (v2.0 md). Its docx twin is a separate build - the folder is
#          honestly twin-less until then rather than carrying a stale one.
# OUTPUT:  ops\runlogs\T-030_execution_plan_v2.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-030_execution_plan_v2.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-030 Execution Plan v1.0 -> v2.0 === $(Get-Date -Format o)"

Write-Host "--- [1] verify v2.0 exists before archiving v1.0 ---"
$v2 = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
if (-not (Test-Path $v2)) {
    Write-Host "v2.0 NOT FOUND - refusing to archive v1.0 with no successor in place"
    Write-Host "`nRESULT: FAILED - successor missing"
    Stop-Transcript; exit 1
}
Write-Host "OK: v2.0 present"

Write-Host "--- [2] archive v1.0 md + its now-stale docx twin ---"
New-Item -ItemType Directory -Force -Path "$repo\docs\archive\execution_plan" | Out-Null
foreach ($f in @("NeelPrajnaPro_Execution_Plan-v1.0.md","NeelPrajnaPro_Execution_Plan-v1.0.docx")) {
    $src = "docs/execution_plan/$f"
    if (Test-Path (Join-Path $repo $src)) {
        git mv $src "docs/archive/execution_plan/$f" 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "git mv FAILED: $f"; $failed = $true } else { Write-Host "archived $f" }
    } else { Write-Host "skip (absent): $f" }
}

Write-Host "--- [3] verify folder now holds exactly the v2.0 master ---"
$files = Get-ChildItem "$repo\docs\execution_plan" -File | Select-Object -ExpandProperty Name
Write-Host "files: $($files -join ', ')"
if ($files.Count -ne 1) { Write-Host "expected exactly 1 file (v2.0 md; docx twin pending separate build)"; $failed = $true }
if ($files -notcontains "NeelPrajnaPro_Execution_Plan-v2.0.md") { Write-Host "v2.0 md not the resident master"; $failed = $true }

Write-Host "--- [4] commit docs + ops together ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-030: Execution Plan v2.0 - full path to the ratified architecture (component map + Phases 3-5: Contract v2, Knowledge Graph, both dashboards, Pattern Evolution); v1.0 md+docx archived; NP-S1 and H-07 sealed definition carried forward verbatim" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-030_execution_plan_v2.log 2>&1 | Out-Null
git commit -m "T-030: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
