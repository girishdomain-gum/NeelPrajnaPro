# =====================================================================
# T-054_g1_seal_and_retirements.ps1
# WHAT:    Commits G1's four rulings, entirely on sprint/NP-S2:
#          - deduplicated J-039 + new J-040 (G1 SEAL: scope=A, NOTE-NP-003
#            fix ordered, NOTE-NP-004 retired, NP-D-013 adopted)
#          - NP-D-013 in the Decisions register
#          - SS13 appended to SPRINT_STATE_MACHINE_v1.1.md
#          - CLAUDE.md: session-close gen_state.py step retired, boot step 3
#            repointed to Execution Plan SS0
#          - scripts/gen_state.py: deprecation header (script left in place)
#          - CHANGELOG.md: one-line retirement entry
#          - NOTE-NP-004: disposition appended
#          - ops/ARCH-NP-005_fix_rebuild_bulk_h007.md: the NOTE-NP-003 fix
#            instruction for a fresh Developer session
# WHY:     Every content edit was already made directly (via the Filesystem
#          connector) BEFORE this script runs. This script only VERIFIES each
#          edit landed, checks the frozen/append-only guards, and commits.
# IDEMPOTENCY FIX (the finding this script exists to correct): T-053's journal
#          insertion had no guard against re-insertion and wrote J-039 twice.
#          This script checks for J-040's own heading BEFORE treating the
#          journal as ready to commit, and the underlying edit already
#          deduplicated J-039 - so re-running this script is safe: if nothing
#          changed, git has nothing to stage, and it says so honestly.
# GUARD:   Refuses if not on sprint/NP-S2. Refuses if SS4/SS5 of the Execution
#          Plan moved, or any ratified ADR body/appendix was edited.
# OUTPUT:  ops\runlogs\T-054_g1_seal_and_retirements.log  (committed to
#          sprint/NP-S2 only - never main, per the branch model)
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-054_g1_seal_and_retirements.log"
Set-Location $repo
Start-Transcript -Path $log -Force
$failed = $false

Write-Host "=== T-054 G1 SEAL + RETIREMENTS (sprint/NP-S2 only) === $(Get-Date -Format o)"

Write-Host "--- [1] HARD GUARD: must be on sprint/NP-S2, never main ---"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host ("current branch: " + $branch)
if ($branch -ne "sprint/NP-S2") { Write-Host "STOP: not on sprint/NP-S2 - refusing"; $failed = $true }

Write-Host "--- [2] journal: deduplicated J-039, new J-040 present ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$j039count = (Select-String -Path $jr -Pattern "J-039 " -AllMatches).Matches.Count
Write-Host ("J-039 heading occurrences: " + $j039count + " (expect 1)")
if ($j039count -ne 1) { Write-Host "STOP: J-039 duplication not resolved as expected"; $failed = $true }
if (Select-String -Path $jr -Pattern "J-040" -SimpleMatch -Quiet) { Write-Host "OK: J-040 present" } else { Write-Host "MISSING: J-040"; $failed = $true }
foreach ($k in @("G1 SEAL","NP-D-013","no calendar-bound sprints","T-053","not idempotent")) {
  if (Select-String -Path $jr -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}

Write-Host "--- [3] decisions register: NP-D-013 ---"
$dc = Join-Path $repo "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md"
if (Select-String -Path $dc -Pattern "NP-D-013" -SimpleMatch -Quiet) { Write-Host "OK: NP-D-013" } else { Write-Host "MISSING: NP-D-013"; $failed = $true }

Write-Host "--- [4] state machine SS13 ---"
$sm = Join-Path $repo "ops\SPRINT_STATE_MACHINE_v1.1.md"
if (Select-String -Path $sm -Pattern "NO CALENDAR-BOUND SPRINTS" -SimpleMatch -Quiet) { Write-Host "OK: SS13 present" } else { Write-Host "MISSING: SS13"; $failed = $true }

Write-Host "--- [5] CLAUDE.md retirement ---"
$cm = Join-Path $repo "CLAUDE.md"
foreach ($k in @("RETIRED 2026-07-31","Execution Plan","no longer applies")) {
  if (Select-String -Path $cm -Pattern $k -SimpleMatch -Quiet) { Write-Host ("OK: " + $k) } else { Write-Host ("MISSING: " + $k); $failed = $true }
}
if (Select-String -Path $cm -Pattern "the ONLY sanctioned way to touch" -SimpleMatch -Quiet) { Write-Host "STOP: old unretired session-close text still present verbatim (unexpected)"; $failed = $true }
else { Write-Host "OK: old session-close instruction is not live (retired text is quoted only as history)" }

Write-Host "--- [6] gen_state.py deprecation header ---"
$gs = Join-Path $repo "scripts\gen_state.py"
if (Select-String -Path $gs -Pattern "DEPRECATED 2026-07-31" -SimpleMatch -Quiet) { Write-Host "OK: deprecation header present" } else { Write-Host "MISSING: deprecation header"; $failed = $true }

Write-Host "--- [7] CHANGELOG + NOTE-NP-004 disposition ---"
$ch = Join-Path $repo "CHANGELOG.md"
if (Select-String -Path $ch -Pattern "NP-S2" -SimpleMatch -Quiet) { Write-Host "OK: CHANGELOG entry" } else { Write-Host "MISSING: CHANGELOG entry"; $failed = $true }
$n4 = Join-Path $repo "docs\coordination\notes\NOTE-NP-004_gen_state_target_missing_since_t009.md"
if (Select-String -Path $n4 -Pattern "Disposition" -SimpleMatch -Quiet) { Write-Host "OK: NOTE-NP-004 disposition appended" } else { Write-Host "MISSING: NOTE-NP-004 disposition"; $failed = $true }

Write-Host "--- [8] ARCH-NP-005 (NOTE-NP-003 fix instruction) ---"
$a5 = Join-Path $repo "ops\ARCH-NP-005_fix_rebuild_bulk_h007.md"
if (Test-Path $a5) { Write-Host "OK: ARCH-NP-005 present" } else { Write-Host "MISSING: ARCH-NP-005"; $failed = $true }

Write-Host "--- [9] FROZEN / APPEND-ONLY GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4/SS5 intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [10] commit and push to sprint/NP-S2 ONLY ---"
if (-not $failed) {
    git add docs ops CLAUDE.md CHANGELOG.md scripts/gen_state.py 2>&1 | Out-String | Write-Host
    $staged = git diff --cached --name-only
    if ($staged) {
        Write-Host "staged files:"; $staged | Out-String | Write-Host
        git commit -m "T-054: G1 SEAL for NP-S2 (J-040) - scope is WO-P only (Option A); NOTE-NP-003 ordered fixed (ARCH-NP-005 issued); NOTE-NP-004 retired (Option c) - CLAUDE.md session-close step struck, gen_state.py marked deprecated in place, Execution Plan SS0 authoritative until STATUS.md; NP-D-013 no-calendar-bound-sprints rule adopted and appended to the state machine as SS13. Also: deduplicated a verbatim double-write of J-039 caused by T-053's non-idempotent insertion (self-caught finding, recorded in J-040); journal-insertion scripts must now check for their own heading before inserting. Committed to sprint/NP-S2 only - main untouched until P8" 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
        git push origin sprint/NP-S2 2>&1 | Out-String | Write-Host
    } else {
        Write-Host "Nothing staged - all edits already committed. Valid outcome (idempotent re-run)."
    }
} else {
    Write-Host "SKIPPED commit due to earlier failures."
}

git log --oneline -3
git status -sb
if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - G1 sealed, both notes dispositioned, NP-D-013 adopted. Next: release a fresh Developer on ARCH-NP-005, then close NP-S2 at P8." }
Stop-Transcript

git add ops/runlogs/T-054_g1_seal_and_retirements.log 2>&1 | Out-Null
git commit -m "T-054: attach run log (sprint/NP-S2)" 2>&1 | Out-Null
git push origin sprint/NP-S2 2>&1 | Out-Null
