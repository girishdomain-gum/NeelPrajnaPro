# =====================================================================
# T-031_place_execution_plan_v2_docx.ps1
# WHAT:    Places the Execution Plan v2.0 whiteboard docx as the twin of
#          docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md,
#          restoring the folder to md+docx after T-030 left it twin-less.
# BEFORE:  download NeelPrajnaPro_Execution_Plan-v2.0.docx from the chat.
# CHANGES: places the one docx; verifies invariant; commits docs+ops.
# OUTPUT:  ops\runlogs\T-031_place_execution_plan_v2_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-031_place_execution_plan_v2_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-031 place Execution Plan v2.0 docx twin === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Execution_Plan-v2.0.docx"
$dst = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Execution_Plan-v2.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.docx"

Write-Host "--- [2] verify twin invariant restored ---"
$bases = Get-ChildItem "$repo\docs\execution_plan" -File | ForEach-Object { $_.BaseName } | Sort-Object -Unique
$files = Get-ChildItem "$repo\docs\execution_plan" -File | Select-Object -ExpandProperty Name
Write-Host "basenames: $($bases -join ', ')"
Write-Host "files: $($files -join ', ')"
if (($bases | Measure-Object).Count -ne 1) { Write-Host "INVARIANT VIOLATED"; $failed = $true }
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (v2.0 md + docx twin)"; $failed = $true }

Write-Host "--- [3] commit docs + ops together ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-031: Execution Plan v2.0 docx twin placed (5 diagrams: five-phase ladder, component map, TARGET-to-BUILT ladder, Owner's three typed lines, H-07 event chain)" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else { Write-Host "Nothing staged - already committed. Valid outcome." }
git log --oneline -3 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-031_place_execution_plan_v2_docx.log 2>&1 | Out-Null
git commit -m "T-031: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
