# =====================================================================
# T-013_root_cleanup.ps1
# WHAT:    Commits the root cleanup the Architect performed via connector:
#          Gen-1 S2 CSV artifacts -> docs\archive\gen1\artifacts\;
#          REPO_BOOTSTRAP.md -> docs\archive\governance\;
#          root README.md rewritten as the NeelPrajnaPro front door.
# CHANGES: git add/commit/push only; verifies root file set first.
# OUTPUT:  ops\runlogs\T-013_root_cleanup.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-013_root_cleanup.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
Write-Host "=== T-013 root cleanup === $(Get-Date -Format o)"

Write-Host "--- [1] verify root holds only the expected repo files ---"
$expected = @(".gitattributes",".gitignore","CHANGELOG.md","CLAUDE.md","CONTRIBUTING.md","pyproject.toml","README.md","uv.lock")
$rootFiles = Get-ChildItem $repo -File | Select-Object -ExpandProperty Name
Write-Host "root files: $($rootFiles -join ', ')"
$unexpected = $rootFiles | Where-Object { $_ -notin $expected }
if ($unexpected) { Write-Host "UNEXPECTED at root: $($unexpected -join ', ')"; $failed = $true }
foreach ($m in @("docs\archive\gen1\artifacts\IVF_S2_XAUUSD_PERIOD_H1.csv","docs\archive\gen1\artifacts\s2_events.csv","docs\archive\governance\REPO_BOOTSTRAP.md")) {
    if (Test-Path (Join-Path $repo $m)) { Write-Host "OK archived: $m" } else { Write-Host "MISSING: $m"; $failed = $true }
}

Write-Host "--- [2] commit + push ---"
git add -A 2>&1 | Out-String | Write-Host
git commit -m "T-013: root cleanup - Gen-1 S2 CSV artifacts and REPO_BOOTSTRAP archived (provenance preserved); README rewritten as NeelPrajnaPro front door" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
