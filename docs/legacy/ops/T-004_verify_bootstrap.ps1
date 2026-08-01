# =====================================================================
# T-004_verify_bootstrap.ps1
# WHAT:    Verifies bootstrap T-001 end-to-end and commits the ops channel.
# WHY:     The Architect can read files but cannot run git; this script
#          produces the evidence (transcript) the connector can read.
# CHANGES: (1) moves BootScript.bat from repo root into ops\ (history kept)
#          (2) git add/commit/push of ops\, docs\governance updates, and
#              the moved script. NOTHING is deleted. Read-only otherwise.
# OUTPUT:  ops\runlogs\T-004_verify_bootstrap.log
# =====================================================================

$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-004_verify_bootstrap.log"
Start-Transcript -Path $log -Force

Write-Host "=== T-004 bootstrap verification === $(Get-Date -Format o)"
Set-Location $repo

Write-Host "`n--- [1/7] git identity of this tree ---"
git remote -v
git branch --show-current
git log --oneline -8

Write-Host "`n--- [2/7] push state vs origin ---"
git fetch origin 2>&1 | Out-Host
git status -sb
$ahead = git rev-list --count "origin/main..HEAD" 2>$null
$behind = git rev-list --count "HEAD..origin/main" 2>$null
Write-Host "Commits ahead of origin/main: $ahead   behind: $behind"

Write-Host "`n--- [3/7] tree counts (copied core) ---"
foreach ($d in @("qrf","ivf","tests","configs","hypotheses","datastore","scripts","docs")) {
    $n = (Get-ChildItem -Path (Join-Path $repo $d) -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    Write-Host ("{0,-12} {1,6} files" -f $d, $n)
}

Write-Host "`n--- [4/7] excluded junk should be absent ---"
foreach ($d in @(".venv",".pytest_cache",".ruff_cache")) {
    $p = Join-Path $repo $d
    if (Test-Path $p) { Write-Host "WARNING: $d PRESENT (should have been excluded)" } else { Write-Host "OK: $d absent" }
}

Write-Host "`n--- [5/7] pause markers in legacy repos ---"
foreach ($m in @("F:\QRF\PAUSED.md","F:\NeelPrajna\repo\PAUSED.md")) {
    if (Test-Path $m) { Write-Host "OK: $m"; Get-Content $m | Select-Object -First 1 | Out-Host }
    else { Write-Host "MISSING: $m" }
}

Write-Host "`n--- [6/7] tidy: BootScript.bat root -> ops\ ---"
if (Test-Path "$repo\BootScript.bat") {
    git mv BootScript.bat ops\T-001_BootScript_as_run.bat 2>&1 | Out-Host
    Write-Host "Moved to ops\T-001_BootScript_as_run.bat (preserved as the T-001 record)"
} else { Write-Host "BootScript.bat not at root (already tidied?)" }

Write-Host "`n--- [7/7] commit + push the ops channel ---"
git add ops docs/governance 2>&1 | Out-Host
git status -s
git commit -m "T-004: ops written-communication channel + bootstrap verification; T-001 script preserved" 2>&1 | Out-Host
git push 2>&1 | Out-Host
git log --oneline -3

$fail = @()
if (-not (Test-Path "$repo\qrf"))  { $fail += "qrf/ missing" }
if (-not (Test-Path "$repo\.git")) { $fail += ".git missing" }
if (-not (Test-Path "F:\QRF\PAUSED.md")) { $fail += "QRF pause marker missing" }
if ($fail.Count -eq 0) { Write-Host "`nRESULT: OK" } else { Write-Host "`nRESULT: FAILED $($fail -join '; ')" }
Stop-Transcript
