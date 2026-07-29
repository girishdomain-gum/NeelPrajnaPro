# =====================================================================
# T-029_place_journal_docx.ps1
# WHAT:    Places the Journal whiteboard docx as the twin of
#          docs\journal\NeelPrajnaPro_Journal.md. FOURTEENTH AND FINAL
#          docx twin of this project.
# BEFORE:  download NeelPrajnaPro_Journal-v1.0.docx from the chat.
# CHANGES: places the one docx; verifies invariant; commits docs+ops together.
# OUTPUT:  ops\runlogs\T-029_place_journal_docx.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-029_place_journal_docx.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-029 place Journal docx twin (FINAL) === $(Get-Date -Format o)"

Write-Host "--- [1] fetch from Downloads ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Journal-v1.0.docx"
$dst = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal-v1.0.docx"
if (-not (Test-Path $dl)) {
    Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Journal-v1.0.docx"
    Write-Host "`nRESULT: FAILED - docx missing"
    Stop-Transcript; exit 1
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\journal\NeelPrajnaPro_Journal-v1.0.docx"

Write-Host "--- [2] verify journal twin (basenames differ by design: log has no version, docx does) ---"
$files = Get-ChildItem "$repo\docs\journal" -File | Select-Object -ExpandProperty Name
Write-Host "files: $($files -join ', ')"
if ($files.Count -ne 2) { Write-Host "expected exactly 2 files (NeelPrajnaPro_Journal.md + the v1.0 docx twin)"; $failed = $true }
if (-not (Test-Path "$repo\docs\journal\NeelPrajnaPro_Journal.md")) { Write-Host "md master missing"; $failed = $true }
if (-not (Test-Path $dst)) { Write-Host "docx twin missing"; $failed = $true }

Write-Host "--- [3] commit docs + ops together ---"
git add docs ops 2>&1 | Out-String | Write-Host
$staged = git diff --cached --name-only
if ($staged) {
    git commit -m "T-029: Journal docx twin placed (whiteboard render, 3 diagrams) - FOURTEENTH AND FINAL docx twin, all thing-folders with genuine content now covered" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
} else {
    Write-Host "Nothing staged - already committed. Valid outcome."
}
git log --oneline -3 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - DOCX-TWIN PROJECT COMPLETE (14/14)" }
Stop-Transcript

Set-Location $repo
git add ops/runlogs/T-029_place_journal_docx.log 2>&1 | Out-Null
git commit -m "T-029: attach run log" 2>&1 | Out-Null
git push 2>&1 | Out-Null
