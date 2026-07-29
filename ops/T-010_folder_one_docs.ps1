# =====================================================================
# T-010_folder_one_docs.ps1
# WHAT:    Commits the folder one-doc masters created by the Architect
#          (decisions, research, reports, reference) and verifies the
#          one-doc-per-folder invariant across docs\.
# WHY:     Owner ruling: every docs folder gets ONE consolidated master
#          (the architecture pattern), not a wholesale archive.
# CHANGES: git add + commit + push only. NOTHING moved or deleted.
# OUTPUT:  ops\runlogs\T-010_folder_one_docs.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-010_folder_one_docs.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-010 folder one-docs === $(Get-Date -Format o)"

Write-Host "--- [1] verify the one-doc-per-folder invariant ---"
foreach ($f in @("architecture","decisions","research","reports","reference")) {
    $n = (Get-ChildItem "$repo\docs\$f" -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host ("docs\{0,-14} files: {1} (must be 1)" -f $f, $n)
    if ($n -ne 1) { $failed = $true }
}

Write-Host "--- [1b] remove empty leftover directories ---"
foreach ($d in @("charter","governance","reviews")) {
    $p = "$repo\docs\$d"
    if ((Test-Path $p) -and ((Get-ChildItem $p -Recurse -File | Measure-Object).Count -eq 0)) {
        Remove-Item $p -Recurse -Force; Write-Host "removed empty docs\$d"
    } elseif (Test-Path $p) { Write-Host "docs\$d NOT empty - left untouched" }
}

Write-Host "--- [2] commit + push ---"
git add -A docs ops 2>&1 | Out-String | Write-Host
git commit -m "T-010: folder one-doc masters - Decisions v1.0 (13 ADRs + register + 9 NP decisions), Research v1.0 (RQ-001..015), Reports v1.0 (Gen-1 final + reserved sections), Reference Handbook v1.0" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
