# =====================================================================
# T-006_place_estate_from_zip.ps1
# WHAT:    Places every remaining zip-corpus artifact (reference volumes,
#          diagram docx, Auto-Adopt audit, specs, corrected mockups, the
#          corrected docs-redesign tree, presentation .docx copies) into
#          this repository from the delivered working-set zip.
# BEFORE RUNNING (one manual step): put the downloaded
#          NeelPrajna_QRF_Working_Set_v2.zip  at:
#          F:\NeelPrajnaPro\ops\incoming\NeelPrajna_QRF_Working_Set_v2.zip
# WHY:     The connector cannot write binaries (.docx) and hand-writing
#          ~180KB of HTML/spec text is error-prone; the zip already holds
#          the verified corrected versions of everything.
# CHANGES: extracts into docs\reference_volumes, docs\specs,
#          docs\books\book-a-neelprajna\docs_redesign, docs\planning (docx),
#          docs\reviews (docx sources), docs\governance (HOW_THIS_DOC);
#          then git add/commit/push (stages ops\ whole - sweeps T-005.ps1).
#          NOTHING deleted; existing files not overwritten except identical
#          re-placements from the same corpus.
# OUTPUT:  ops\runlogs\T-006_place_estate_from_zip.log
# =====================================================================

$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$zip  = Join-Path $repo "ops\incoming\NeelPrajna_QRF_Working_Set_v2.zip"
$tmp  = Join-Path $repo "ops\incoming\_extract"
$log  = Join-Path $repo "ops\runlogs\T-006_place_estate_from_zip.log"
Start-Transcript -Path $log -Force
$failed = $false
Write-Host "=== T-006 estate placement === $(Get-Date -Format o)"

if (-not (Test-Path $zip)) {
    $dl = "C:\Users\giris\Downloads\NeelPrajna_QRF_Working_Set_v2.zip"
    if (Test-Path $dl) {
        Write-Host "Zip found in Downloads - copying to ops\incoming (Downloads copy left untouched)"
        Copy-Item $dl -Destination $zip -Force
    } else {
        Write-Host "ZIP NOT FOUND at $zip nor at $dl"
        Write-Host "Download NeelPrajna_QRF_Working_Set_v2.zip from the chat, then re-run."
        Write-Host "`nRESULT: FAILED - zip missing"
        Stop-Transcript; exit 1
    }
}

Write-Host "--- [1] extract ---"
if (Test-Path $tmp) { Rename-Item $tmp "$tmp.old_$(Get-Date -Format yyyyMMddHHmmss)" }
Expand-Archive -Path $zip -DestinationPath $tmp -Force
$root = Join-Path $tmp "NeelPrajna_QRF_Working_Set_v2"
if (-not (Test-Path $root)) { Write-Host "Extracted root missing"; $failed = $true }

if (-not $failed) {
    Write-Host "--- [2] place artifacts ---"
    $map = @(
        @{src="04_reference_volumes";              dst="docs\reference_volumes"},
        @{src="05_specs_and_ui";                   dst="docs\specs"},
        @{src="06_docs_redesign_corrected";        dst="docs\books\book-a-neelprajna\docs_redesign"},
        @{src="03_governance_standards\HOW_THIS_DOC_WAS_BUILT.md"; dst="docs\governance\HOW_THIS_DOC_WAS_BUILT.md"},
        @{src="07_np_planning\NP_INTEGRATION_EXECUTION_ROADMAP.docx";  dst="docs\planning\NP_INTEGRATION_EXECUTION_ROADMAP.docx"},
        @{src="07_np_planning\NP_INTEGRATION_VV_ACCEPTANCE_PLAN.docx"; dst="docs\planning\NP_INTEGRATION_VV_ACCEPTANCE_PLAN.docx"},
        @{src="07_np_planning\NP_JOINT_AUTOMATION_PLAN.docx";          dst="docs\planning\NP_JOINT_AUTOMATION_PLAN.docx"}
    )
    foreach ($m in $map) {
        $s = Join-Path $root $m.src; $d = Join-Path $repo $m.dst
        if (Test-Path $s) {
            if ((Get-Item $s) -is [System.IO.DirectoryInfo]) {
                New-Item -ItemType Directory -Force -Path $d | Out-Null
                Copy-Item "$s\*" -Destination $d -Recurse -Force
            } else {
                New-Item -ItemType Directory -Force -Path (Split-Path $d) | Out-Null
                Copy-Item $s -Destination $d -Force
            }
            Write-Host ("placed  {0}  ->  {1}" -f $m.src, $m.dst)
        } else { Write-Host ("MISSING IN ZIP: {0}" -f $m.src); $failed = $true }
    }

    Write-Host "--- [3] spot-verify the F-11 remedy (banners present) ---"
    $v12 = Join-Path $repo "docs\specs\mockups_console_corrected\qrf_research_console_mockup_v1.2.html"
    if ((Test-Path $v12) -and (Select-String -Path $v12 -Pattern "CORRECTION" -Quiet)) {
        Write-Host "OK: v1.2 mockup carries its correction banner"
    } else { Write-Host "BANNER CHECK FAILED on v1.2 mockup"; $failed = $true }

    Write-Host "--- [4] commit + push ---"
    Set-Location $repo
    git add docs ops 2>&1 | Out-String | Write-Host
    git commit -m "T-006: reference volumes, specs+corrected mockups, docs-redesign tree, docx presentation copies placed from verified working set" 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
    git push 2>&1 | Out-String | Write-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
    git log --oneline -2 2>&1 | Out-String | Write-Host
}

if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK" }
Stop-Transcript
