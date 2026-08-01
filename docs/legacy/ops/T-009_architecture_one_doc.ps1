# =====================================================================
# T-009_architecture_one_doc.ps1
# WHAT:    Executes the Owner's architecture-folder ruling:
#          (1) fetches NeelPrajnaPro_Architecture-v1.0.docx from Downloads
#              into docs\architecture\ (the folder's ONE document)
#          (2) git-mv's the existing docs\architecture contents (Gen-1/Gen-2
#              QRF architecture docs) to docs\archive\gen1\architecture\
#          (3) applies the same law recursively: moves the remaining Gen-1
#              working trees (adr, coordination, handover, implementation,
#              method, reference, reports, research, planning) under
#              docs\archive\gen1\  — records preserved whole, docs root clean
#          (4) housekeeping: gitignore Word lock files (~$*), untrack the one
#              committed lock file, sweep ops scripts
#          (5) commit + push. NOTHING deleted; git mv preserves history.
# BEFORE:  download NeelPrajnaPro_Architecture-v1.0.docx from the chat
#          (script fetches it from Downloads itself).
# OUTPUT:  ops\runlogs\T-009_architecture_one_doc.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-009_architecture_one_doc.log"
Start-Transcript -Path $log -Force
Set-Location $repo
$failed = $false
function MV($src,$dst){
    if (Test-Path (Join-Path $repo $src)) {
        git mv $src $dst 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "git mv FAILED: $src"; $script:failed = $true } else { Write-Host "moved $src -> $dst" }
    } else { Write-Host "skip (absent): $src" }
}
Write-Host "=== T-009 architecture one-doc + recursive law === $(Get-Date -Format o)"

Write-Host "--- [1] fetch the one architecture doc ---"
$dl = "C:\Users\giris\Downloads\NeelPrajnaPro_Architecture-v1.0.docx"
$dst = Join-Path $repo "docs\architecture\NeelPrajnaPro_Architecture-v1.0.docx"
if (-not (Test-Path $dl)) { Write-Host "NOT FOUND in Downloads: NeelPrajnaPro_Architecture-v1.0.docx"; Write-Host "`nRESULT: FAILED - docx missing"; Stop-Transcript; exit 1 }

Write-Host "--- [2] archive the folder's existing contents first ---"
New-Item -ItemType Directory -Force -Path "$repo\docs\archive\gen1\architecture" | Out-Null
Get-ChildItem "$repo\docs\architecture" -File | ForEach-Object {
    MV ("docs/architecture/" + $_.Name) ("docs/archive/gen1/architecture/" + $_.Name)
}
Copy-Item $dl -Destination $dst -Force
Write-Host "placed docs\architecture\NeelPrajnaPro_Architecture-v1.0.docx (the folder's ONE document)"

Write-Host "--- [3] recursive law: Gen-1 working trees -> docs\archive\gen1\ ---"
foreach ($d in @("adr","coordination","handover","implementation","method","reference","reports","research","planning")) {
    MV ("docs/" + $d) ("docs/archive/gen1/" + $d)
}

Write-Host "--- [4] housekeeping ---"
Add-Content -Path "$repo\.gitignore" -Value "`n# Word lock files`n~`$*`ndocs/**/~`$*"
git rm --cached "docs/reference_volumes/~`$elPrajna_Architecture_Diagrams_CORRECTED.docx" 2>&1 | Out-String | Write-Host
Write-Host "(lock file untracked; remains on disk until Word releases it)"

Write-Host "--- [5] verify ---"
$archCount = (Get-ChildItem "$repo\docs\architecture" -File | Measure-Object).Count
Write-Host "docs\architecture file count: $archCount (must be 1)"
if ($archCount -ne 1) { $failed = $true }
if (-not (Test-Path $dst)) { Write-Host "MISSING one-doc"; $failed = $true }

Write-Host "--- [6] commit + push ---"
git add -A 2>&1 | Out-String | Write-Host
git commit -m "T-009: architecture folder = ONE doc (NeelPrajnaPro_Architecture-v1.0.docx); Gen-1 trees archived under docs/archive/gen1; lock files gitignored" 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
git push 2>&1 | Out-String | Write-Host
if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
git log --oneline -2 2>&1 | Out-String | Write-Host

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
