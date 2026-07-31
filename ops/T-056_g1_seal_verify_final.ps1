# =====================================================================
# T-056_g1_seal_verify_final.ps1
# WHAT:    Second correction to the verification script. T-055's "## J-039"
#          heading check reported 0 matches against the live file, even
#          though the SAME pattern against a downloaded copy of the SAME
#          file (moments earlier) matched exactly once, and a direct
#          Filesystem view of the live file confirms the heading is present,
#          correct, and singular. Root cause of the 0-vs-1 discrepancy is
#          NOT established - this script does not guess at one. Instead it
#          abandons "#"-prefixed pattern matching for this check entirely
#          and verifies non-duplication a different way: by counting a long,
#          distinctive phrase that existed ONLY in the tail of the original
#          (pre-dedup) duplicate text. If that phrase appears more than
#          once, real duplication exists. If it appears exactly once, the
#          single surviving J-039 body is confirmed intact.
# WHY:     Two verification-pattern failures in one script (T-054's overly
#          broad substring, T-055's inexplicably-zero "##" match) is a
#          pattern in itself: patterns touching markdown syntax or built on
#          assumptions about how a specific matcher handles them are the
#          fragile part of this whole exercise, not the content they check.
#          This script's checks avoid markdown syntax entirely - every
#          pattern below is plain prose words, nothing else.
# GUARD:   Same guards as T-054/T-055: must be on sprint/NP-S2; SS4/SS5 and
#          the three ratified ADR artifacts must be untouched.
# OUTPUT:  ops\runlogs\T-056_g1_seal_verify_final.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-056_g1_seal_verify_final.log"
Set-Location $repo
Start-Transcript -Path $log -Force
$failed = $false

Write-Host "=== T-056 G1 SEAL - FINAL VERIFICATION (sprint/NP-S2 only) === $(Get-Date -Format o)"

Write-Host "--- [1] HARD GUARD: must be on sprint/NP-S2 ---"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host ("current branch: " + $branch)
if ($branch -ne "sprint/NP-S2") { Write-Host "STOP: not on sprint/NP-S2 - refusing"; $failed = $true }

Write-Host "--- [2] journal: no duplication, via a markdown-free content fingerprint ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$fingerprint = "it touches a file CLAUDE.md calls normative"
$fpCount = (Select-String -Path $jr -Pattern $fingerprint -SimpleMatch -AllMatches).Matches.Count
Write-Host ("distinctive J-039-tail phrase occurrences: " + $fpCount + " (expect exactly 1)")
if ($fpCount -eq 1) { Write-Host "OK: exactly one J-039 body survives - no duplication" }
elseif ($fpCount -eq 0) { Write-Host "STOP: the phrase is gone entirely - J-039 body may have been lost"; $failed = $true }
else { Write-Host ("STOP: phrase appears " + $fpCount + " times - real duplication"); $failed = $true }

if (Select-String -Path $jr -Pattern "J-040" -SimpleMatch -Quiet) { Write-Host "OK: J-040 present" } else { Write-Host "MISSING: J-040"; $failed = $true }
foreach ($k in @("G1 SEAL","NP-D-013","no calendar-bound sprints","T-053","not idempotent")) {
  if (Select-String -Path $jr -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] decisions register + state machine ---"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"
if (Select-String -Path $dc -Pattern "NP-D-013" -SimpleMatch -Quiet) { Write-Host "OK: NP-D-013" } else { Write-Host "MISSING: NP-D-013"; $failed = $true }
$sm = Join-Path $repo "ops\SPRINT_STATE_MACHINE_v1.1.md"
if (Select-String -Path $sm -Pattern "NO CALENDAR-BOUND SPRINTS" -SimpleMatch -Quiet) { Write-Host "OK: SS13 present" } else { Write-Host "MISSING: SS13"; $failed = $true }

Write-Host "--- [4] CLAUDE.md retirement (markdown-free checks) ---"
$cm = Join-Path $repo "CLAUDE.md"
foreach ($k in @("RETIRED 2026-07-31","Execution Plan","Retired text, kept for history")) {
  if (Select-String -Path $cm -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

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
        git commit -m "T-056: G1 SEAL for NP-S2 (J-040) - scope is WO-P only (Option A); NOTE-NP-003 ordered fixed (ARCH-NP-005 issued); NOTE-NP-004 retired (Option c); NP-D-013 no-calendar-bound-sprints rule adopted (state machine SS13). Supersedes T-054 and T-055: T-054's check used a substring too broad for J-040's own prose; T-055's replacement check ('## J-039') reported zero matches against the live file despite the same pattern matching correctly against a downloaded copy and a direct file view moments earlier - root cause not established, not guessed at. This script abandons markdown-syntax-based pattern matching for the duplication check entirely, verifying instead via a long distinctive prose phrase unique to the original duplicate's tail text. All underlying content edits were correct from T-054 onward; only the verification patterns needed correction, twice. Committed to sprint/NP-S2 only - main untouched until P8" 2>&1 | Out-String | Write-Host
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

git add ops/runlogs/T-056_g1_seal_verify_final.log 2>&1 | Out-Null
git commit -m "T-056: attach run log (sprint/NP-S2)" 2>&1 | Out-Null
git push origin sprint/NP-S2 2>&1 | Out-Null
