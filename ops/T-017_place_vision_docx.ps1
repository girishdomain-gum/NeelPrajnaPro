# =====================================================================
# T-017_place_vision_docx.ps1
# WHAT:    Places the Vision whiteboard docx as the twin of
#          docs\vision\NeelPrajnaPro_Vision-v1.0.md (same folder, same
#          basename, per the Architecture/Scientific Model twin pattern).
# BEFORE:  download NeelPrajnaPro_Vision-v1.0.docx from the chat
#          (script fetches it from Downloads itself).
# CHANGES: places the one docx; verifies the folder now holds exactly one
#          basename (md + docx, same name); commits + pushes.
# OUTPUT:  ops\runlogs\T-017_place_vision_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-017_place_vision_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-017 place Vision docx twin === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Vision-v1.0.docx"
$dst = Join-Path $repo "docs\vision\NeelPrajnaPro_Vision-v1.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Vision-v1.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\vision\NeelPrajnaPro_Vision-v1.0.docx"

Write-Host "--- [2] verify twin invariant: exactly one basename, exactly two files ---"
$bases = Get-ChildItem "$repo\docs\vision" -File | ForEach-Object { $_.BaseName } | Sort-Object -Unique
$files = Get-ChildItem "$repo\docs\vision" -File | Select-Object -ExpandProperty Name
Write-Host "basenames: $($bases -join ', ')"
Write-Host "files: $($files -join ', ')"
if (($bases | Measure-Object).Count -ne 1) { Write-Host "INVARIANT VIOLATED - expected exactly 1 basename"; $failed = $true }
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (md + docx twin)"; $failed = $true }

Write-Host "--- [3] commit + push ---"
git add docs 2>&1 | Out-String | Write-Host
git commit -m "T-017: Vision docx twin placed (whiteboard render, 4 diagrams, per HOW_THIS_DOC_WAS_BUILT.md; same basename+folder as the md master)" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-017_place_vision_docx.log 2>&1 | Out-Null
git commit -m "T-017: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
