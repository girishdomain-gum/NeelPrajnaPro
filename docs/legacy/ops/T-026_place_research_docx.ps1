# =====================================================================
# T-026_place_research_docx.ps1
# WHAT:    Places the Research whiteboard docx as the twin of
#          docs\research\NeelPrajnaPro_Research-v1.0.md.
# BEFORE:  download NeelPrajnaPro_Research-v1.0.docx from the chat.
# CHANGES: places the one docx; verifies invariant; commits docs+ops together.
# OUTPUT:  ops\runlogs\T-026_place_research_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-026_place_research_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-026 place Research docx twin === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Research-v1.0.docx"
$dst = Join-Path $repo "docs\research\NeelPrajnaPro_Research-v1.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Research-v1.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\research\NeelPrajnaPro_Research-v1.0.docx"

Write-Host "--- [2] verify twin invariant ---"
$bases = Get-ChildItem "$repo\docs\research" -File | ForEach-Object { $_.BaseName } | Sort-Object -Unique
$files = Get-ChildItem "$repo\docs\research" -File | Select-Object -ExpandProperty Name
Write-Host "basenames: $($bases -join ', ')"
Write-Host "files: $($files -join ', ')"
if (($bases | Measure-Object).Count -ne 1) { Write-Host "INVARIANT VIOLATED"; $failed = $true }
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (md + docx twin)"; $failed = $true }

Write-Host "--- [3] commit docs + ops together ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-026: Research docx twin placed (whiteboard render, 3 diagrams) - tenth and final planned docx twin" 2>&1 | Out-String | Write-Host
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
git add ops/runlogs/T-026_place_research_docx.log 2>&1 | Out-Null
git commit -m "T-026: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
