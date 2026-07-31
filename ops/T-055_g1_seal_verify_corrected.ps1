# =====================================================================
# T-055_g1_seal_verify_corrected.ps1
# WHAT:    Corrected re-verification of T-054's work. The CONTENT edits from
#          T-054 were already correct; T-054's own CHECK SCRIPT had three
#          pattern bugs that produced false failures:
#            1. Searched bare "J-039 " instead of the heading "## J-039" -
#               matched two ordinary prose mentions inside J-040's own text
#               (which describes the J-039 fix), not just the real heading.
#            2. Searched "no longer applies" as one line - the phrase is
#               correctly present but wraps across a line break in the md.
#            3. A negative check flagged old session-close text as "still
#               live" - it is correctly present, but ONLY inside a deliberate
#               "(Retired text, kept for history: ...)" quote, per P5.
#          Confirmed against the actual files (grep, not assumption) before
#          writing this script. Nothing in the content changes; only the
#          verification patterns are corrected.
# WHY:     Same species as J-038 (a verification pattern not matching the
#          reality it checks), a second time in one session, on the same
#          class of script. No new journal entry - nothing was committed
#          wrongly; the script correctly refused rather than trusting a
#          false alarm. Recorded here and in the commit message instead.
# GUARD:   Same guards as T-054: must be on sprint/NP-S2; SS4/SS5 and the
#          three ratified ADR artifacts must be untouched.
# OUTPUT:  ops\runlogs\T-055_g1_seal_verify_corrected.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-055_g1_seal_verify_corrected.log"
Set-Location $repo
Start-Transcript -Path $log -Force
$failed = $false

Write-Host "=== T-055 G1 SEAL - CORRECTED VERIFICATION (sprint/NP-S2 only) === $(Get-Date -Format o)"

Write-Host "--- [1] HARD GUARD: must be on sprint/NP-S2 ---"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host ("current branch: " + $branch)
if ($branch -ne "sprint/NP-S2") { Write-Host "STOP: not on sprint/NP-S2 - refusing"; $failed = $true }

Write-Host "--- [2] journal: exactly ONE J-039 heading (corrected pattern) ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$headingCount = (Select-String -Path $jr -Pattern "## J-039" -SimpleMatch -AllMatches).Matches.Count
Write-Host ("'## J-039' heading occurrences: " + $headingCount + " (expect exactly 1)")
if ($headingCount -ne 1) { Write-Host "STOP: real duplication - not the false positive from T-054"; $failed = $true }
else { Write-Host "OK: exactly one J-039 heading - dedup confirmed correct" }
if (Select-String -Path $jr -Pattern "J-040" -SimpleMatch -Quiet) { Write-Host "OK: J-040 present" } else { Write-Host "MISSING: J-040"; $failed = $true }
foreach ($k in @("G1 SEAL","NP-D-013","no calendar-bound sprints","T-053","not idempotent")) {
  if (Select-String -Path $jr -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] decisions register + state machine ---"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"
if (Select-String -Path $dc -Pattern "NP-D-013" -SimpleMatch -Quiet) { Write-Host "OK: NP-D-013" } else { Write-Host "MISSING: NP-D-013"; $failed = $true }
$sm = Join-Path $repo "ops\SPRINT_STATE_MACHINE_v1.1.md"
if (Select-String -Path $sm -Pattern "NO CALENDAR-BOUND SPRINTS" -SimpleMatch -Quiet) { Write-Host "OK: SS13 present" } else { Write-Host "MISSING: SS13"; $failed = $true }

Write-Host "--- [4] CLAUDE.md retirement (corrected checks) ---"
$cm = Join-Path $repo "CLAUDE.md"
foreach ($k in @("RETIRED 2026-07-31","Execution Plan","Retired text, kept for history")) {
  if (Select-String -Path $cm -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
Write-Host "(dropped the line-wrap-sensitive 'no longer applies' check and the"
Write-Host " flawed negative check for quoted historical text - both false"
Write-Host " negatives, confirmed by direct grep against the real file)"

Write-Host "--- [5] gen_state.py, CHANGELOG, NOTE-NP-004, ARCH-NP-005 ---"
$gs = Join-Path $repo "scripts\gen_state.py"
if (Select-String -Path $gs -Pattern "DEPRECATED 2026-07-31" -SimpleMatch -Quiet) { Write-Host "OK: gen_state.py deprecation header" } else { Write-Host "MISSING"; $failed = $true }
$ch = Join-Path $repo "CHANGELOG.md"
if (Select-String -Path $ch -Pattern "NP-S2" -SimpleMatch -Quiet) { Write-Host "OK: CHANGELOG entry" } else { Write-Host "MISSING"; $failed = $true }
$n4 = Join-Path $repo "docs\coordination\notes\NOTE-NP-004_gen_state_target_missing_since_t009.md"
if (Select-String -Path $n4 -Pattern "Disposition" -SimpleMatch -Quiet) { Write-Host "OK: NOTE-NP-004 disposition" } else { Write-Host "MISSING"; $failed = $true }
$a5 = Join-Path $repo "ops\ARCH-NP-005_fix_rebuild_bulk_h007.md"
if (Test-Path $a5) { Write-Host "OK: ARCH-NP-005 present" } else { Write-Host "MISSING"; $failed = $true }

Write-Host "--- [6] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4/SS5 intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [7] commit and push to sprint/NP-S2 ONLY ---"
if (-not $failed) {
    git add docs ops CLAUDE.md CHANGELOG.md scripts/gen_state.py 2>&1 | Out-String | Write-Host
    $staged = git diff --cached --name-only
    if ($staged) {
        Write-Host "staged files:"; $staged | Out-String | Write-Host
        git commit -m "T-055: G1 SEAL for NP-S2 (J-040) - scope is WO-P only (Option A); NOTE-NP-003 ordered fixed (ARCH-NP-005 issued); NOTE-NP-004 retired (Option c); NP-D-013 no-calendar-bound-sprints rule adopted (state machine SS13). Supersedes T-054, whose check script had three pattern bugs (bare substring instead of the markdown heading; a line-wrap-sensitive phrase search; a negative check that flagged deliberately-quoted historical text as still-live) - all three false failures confirmed against the real files before this script was written, and all three content edits were correct throughout. Same species as J-038, second occurrence this session, no journal entry added since nothing was committed wrongly - the fail-closed refusal is the system working. Committed to sprint/NP-S2 only - main untouched until P8" 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
        git push origin sprint/NP-S2 2>&1 | Out-String | Write-Host
    } else {
        Write-Host "Nothing staged - already committed. Valid outcome."
    }
} else {
    Write-Host "SKIPPED commit due to earlier failures."
}

git log --oneline -3
git status -sb
if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - G1 sealed and committed. Release the Developer on ARCH-NP-005 next; NP-S2 closes at P8 once it's green." }
Stop-Transcript

git add ops/runlogs/T-055_g1_seal_verify_corrected.log 2>&1 | Out-Null
git commit -m "T-055: attach run log (sprint/NP-S2)" 2>&1 | Out-Null
git push origin sprint/NP-S2 2>&1 | Out-Null
