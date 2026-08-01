# =====================================================================
# T-016_place_scientific_model_docx.ps1
# WHAT:    Places the newly built Scientific Model whiteboard docx as the
#          twin of docs\scientific_model\NeelPrajnaPro_Scientific_Model-v1.0.md
#          (same folder, same basename, per the architecture twin pattern).
# BEFORE:  download NeelPrajnaPro_Scientific_Model-v1.0.docx from the chat
#          (script fetches it from Downloads itself).
# CHANGES: places the one docx; verifies the folder now holds exactly one
#          basename (md + docx, same name); commits + pushes.
# OUTPUT:  ops\runlogs\T-016_place_scientific_model_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-016_place_scientific_model_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-016 place Scientific Model docx twin === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Scientific_Model-v1.0.docx"
$dst = Join-Path $repo "docs\scientific_model\NeelPrajnaPro_Scientific_Model-v1.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Scientific_Model-v1.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\scientific_model\NeelPrajnaPro_Scientific_Model-v1.0.docx"

Write-Host "--- [2] verify twin invariant: exactly one basename in the folder ---"
$bases = Get-ChildItem "$repo\docs\scientific_model" -File | ForEach-Object { $_.BaseName } | Sort-Object -Unique
Write-Host "basenames found: $($bases -join ', ')"
if (($bases | Measure-Object).Count -ne 1) { Write-Host "INVARIANT VIOLATED - expected exactly 1 basename"; $failed = $true }
$files = Get-ChildItem "$repo\docs\scientific_model" -File | Select-Object -ExpandProperty Name
Write-Host "files: $($files -join ', ')"
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (md + docx twin)"; $failed = $true }

Write-Host "--- [3] commit + push ---"
git add docs 2>&1 | Out-String | Write-Host
git commit -m "T-016: Scientific Model docx twin placed (whiteboard render, 7 diagrams, per HOW_THIS_DOC_WAS_BUILT.md; same basename+folder as the md master)" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

# F-20 fix: commit the transcript AFTER it's closed, in its own step
Set-Location $repo
git add ops/runlogs/T-016_place_scientific_model_docx.log 2>&1 | Out-Null
git commit -m "T-016: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
