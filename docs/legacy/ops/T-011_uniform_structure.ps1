# =====================================================================
# T-011_uniform_structure.ps1
# WHAT:    Executes structure-law v2.0: one folder per thing, synced
#          basenames for md/docx twins. All moves are git mv (history
#          preserved). NOTHING deleted.
# CHANGES: root canonical .md files -> their thing-folders with
#          NeelPrajnaPro_<Thing>-v1.0.md names; ARCHITECTURE.md joins its
#          docx twin in architecture\ under the same basename; JOURNAL ->
#          journal\NeelPrajnaPro_Journal.md; commit + push.
#          After this run the Architect patches cross-references (paths
#          inside docs) via the connector - expected and announced.
# OUTPUT:  ops\runlogs\T-011_uniform_structure.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-011_uniform_structure.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
function MV($src,$dst){
    if (Test-Path (Join-Path $repo $src)) {
        $dstDir = Split-Path (Join-Path $repo $dst)
        if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Force -Path $dstDir | Out-Null }
        git mv $src $dst 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "git mv FAILED: $src"; $script:failed = $true } else { Write-Host "moved $src -> $dst" }
    } else { Write-Host "skip (absent): $src" }
}
Write-Host "=== T-011 uniform structure === $(Get-Date -Format o)"

Write-Host "--- [1] twins united: architecture ---"
MV "docs/ARCHITECTURE.md"            "docs/architecture/NeelPrajnaPro_Architecture-v1.0.md"

Write-Host "--- [2] canonical roots -> thing-folders, synced names ---"
MV "docs/VISION.md"                  "docs/vision/NeelPrajnaPro_Vision-v1.0.md"
MV "docs/CONSTITUTION.md"            "docs/constitution/NeelPrajnaPro_Constitution-v1.0.md"
MV "docs/SCIENTIFIC_MODEL.md"        "docs/scientific_model/NeelPrajnaPro_Scientific_Model-v1.0.md"
MV "docs/EXECUTION_PLAN.md"          "docs/execution_plan/NeelPrajnaPro_Execution_Plan-v1.0.md"
MV "docs/VV_PLAN.md"                 "docs/vv_plan/NeelPrajnaPro_VV_Plan-v1.0.md"
MV "docs/AUTOMATION.md"              "docs/automation/NeelPrajnaPro_Automation-v1.0.md"
MV "docs/ROLES_AND_COMMUNICATION.md" "docs/roles/NeelPrajnaPro_Roles_And_Communication-v1.0.md"
MV "docs/WRITING_STANDARD.md"        "docs/writing_standard/NeelPrajnaPro_Writing_Standard-v1.0.md"
MV "docs/JOURNAL.md"                 "docs/journal/NeelPrajnaPro_Journal.md"

Write-Host "--- [3] verify: root holds only README + THE_ONE_PAGE; every thing-folder = one basename ---"
$rootMd = Get-ChildItem "$repo\docs" -File | Select-Object -ExpandProperty Name
Write-Host "root files: $($rootMd -join ', ')"
if (($rootMd | Where-Object { $_ -notin @("README.md","THE_ONE_PAGE.md") }).Count -gt 0) { Write-Host "UNEXPECTED root files"; $failed = $true }
foreach ($f in @("vision","constitution","scientific_model","architecture","execution_plan","vv_plan","automation","roles","writing_standard","journal","decisions","research","reports","reference")) {
    $bases = Get-ChildItem "$repo\docs\$f" -File -ErrorAction SilentlyContinue | ForEach-Object { $_.BaseName } | Sort-Object -Unique
    $n = ($bases | Measure-Object).Count
    Write-Host ("docs\{0,-17} basenames: {1} (must be 1)" -f $f, $n)
    if ($n -ne 1) { $failed = $true }
}

Write-Host "--- [4] commit + push ---"
git add -A docs ops 2>&1 | Out-String | Write-Host
git commit -m "T-011: uniform structure law v2.0 - one folder per thing, synced md/docx twin basenames, history preserved via git mv" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
