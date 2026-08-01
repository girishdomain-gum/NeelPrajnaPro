# =====================================================================
# T-012_commit_uniform_structure.ps1
# WHAT:    Commits the uniform-structure moves the Architect completed via
#          the connector (T-011's script failed on directory creation; the
#          moves are already done on disk). git add -A detects them as
#          renames; verifies the invariant; pushes.
# CHANGES: git add/commit/push only. NOTHING moved or deleted by this script.
# OUTPUT:  ops\runlogs\T-012_commit_uniform_structure.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-012_commit_uniform_structure.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-012 commit uniform structure === $(Get-Date -Format o)"

Write-Host "--- [1] invariant: root = README + THE_ONE_PAGE; every thing-folder = one basename ---"
$rootMd = Get-ChildItem "$repo\docs" -File | Select-Object -ExpandProperty Name
Write-Host "root files: $($rootMd -join ', ')"
if (($rootMd | Where-Object { $_ -notin @("README.md","THE_ONE_PAGE.md") }).Count -gt 0) { Write-Host "UNEXPECTED root files"; $failed = $true }
foreach ($f in @("vision","constitution","scientific_model","architecture","execution_plan","vv_plan","automation","roles","writing_standard","journal","decisions","research","reports","reference")) {
    $bases = Get-ChildItem "$repo\docs\$f" -File -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName } | Sort-Object -Unique
    $n = ($bases | Measure-Object).Count
    Write-Host ("docs\{0,-17} basenames: {1} (must be 1)" -f $f, $n)
    if ($n -ne 1) { $failed = $true }
}

Write-Host "--- [2] commit + push (renames auto-detected) ---"
git add -A 2>&1 | Out-String | Write-Host
git commit -m "T-012: uniform structure v2.0 complete - all masters in thing-folders with synced basenames (moves by Architect via connector after T-011 script path failure); cross-references patched" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host
git status -s 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
