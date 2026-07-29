# =====================================================================
# T-018_place_execution_plan_docx.ps1
# WHAT:    Places the Execution Plan whiteboard docx as the twin of
#          docs\execution_plan\NeelPrajnaPro_Execution_Plan-v1.0.md.
# BEFORE:  download NeelPrajnaPro_Execution_Plan-v1.0.docx from the chat.
# CHANGES: places the one docx; verifies the folder now holds exactly one
#          basename (md + docx, same name); commits + pushes.
# OUTPUT:  ops\runlogs\T-018_place_execution_plan_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-018_place_execution_plan_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-018 place Execution Plan docx twin === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Execution_Plan-v1.0.docx"
$dst = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v1.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Execution_Plan-v1.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\execution_plan\NeelPrajnaPro_Execution_Plan-v1.0.docx"

Write-Host "--- [2] verify twin invariant ---"
$bases = Get-ChildItem "$repo\docs\execution_plan" -File | ForEach-Object { $_.BaseName } | Sort-Object -Unique
$files = Get-ChildItem "$repo\docs\execution_plan" -File | Select-Object -ExpandProperty Name
Write-Host "basenames: $($bases -join ', ')"
Write-Host "files: $($files -join ', ')"
if (($bases | Measure-Object).Count -ne 1) { Write-Host "INVARIANT VIOLATED"; $failed = $true }
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (md + docx twin)"; $failed = $true }

Write-Host "--- [3] commit + push ---"
git add docs 2>&1 | Out-String | Write-Host
git commit -m "T-018: Execution Plan docx twin placed (whiteboard render, 4 diagrams, per HOW_THIS_DOC_WAS_BUILT.md)" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-018_place_execution_plan_docx.log 2>&1 | Out-Null
git commit -m "T-018: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
