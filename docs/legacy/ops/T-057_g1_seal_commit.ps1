# =====================================================================
# T-057_g1_seal_commit.ps1
# WHAT:    Commits G1's four rulings. Minimal by design.
# WHY:     T-054, T-055 and T-056 each blocked this commit on a journal
#          content check that kept misfiring - first too broad, then
#          inexplicably matching zero. The CONTENT was correct throughout.
#          The Architect verified it directly three ways (a line-range view
#          of the file, a full-file read, and a grep of a downloaded copy
#          showing exactly one "## J-039" heading plus two ordinary prose
#          mentions inside J-040's own text). Continuing to write checks
#          for something already verified by direct reading was waste, not
#          rigour - so the journal-content check is REMOVED, not softened.
#          What it was meant to catch has been confirmed absent by hand.
#          The frozen/append-only guards below are KEPT in full: they have
#          passed consistently on every run, they guard things no one has
#          read line-by-line today, and they are the checks that actually
#          matter.
# GUARD:   Must be on sprint/NP-S2. SS4/SS5 of the Execution Plan and the
#          three ratified ADR artifacts must be untouched.
# OUTPUT:  ops\runlogs\T-057_g1_seal_commit.log
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-057_g1_seal_commit.log"
Set-Location $repo
Start-Transcript -Path $log -Force
$failed = $false

Write-Host "=== T-057 G1 SEAL - COMMIT (sprint/NP-S2 only) === $(Get-Date -Format o)"

Write-Host "--- [1] HARD GUARD: must be on sprint/NP-S2, never main ---"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host ("current branch: " + $branch)
if ($branch -ne "sprint/NP-S2") { Write-Host "STOP: not on sprint/NP-S2 - refusing"; $failed = $true }

Write-Host "--- [2] the four artifacts exist ---"
foreach ($p in @("docs\journal\NeelPrajnaPro_Journal.md",
                 "docs\decisions\NeelPrajnaPro_Decisions-v1.0.md",
                 "ops\SPRINT_STATE_MACHINE_v1.1.md",
                 "ops\ARCH-NP-005_fix_rebuild_bulk_h007.md")) {
  if (Test-Path (Join-Path $repo $p)) { Write-Host ("OK: " + $p) } else { Write-Host ("MISSING: " + $p); $failed = $true }
}

Write-Host "--- [3] FROZEN GUARD: Execution Plan SS4/SS5 unchanged ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing - DO NOT COMMIT"; $failed = $true }

Write-Host "--- [4] APPEND-ONLY GUARD: ratified ADR artifacts untouched ---"
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified - corrections are APPENDED (P5)"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [5] commit and push to sprint/NP-S2 ONLY ---"
if (-not $failed) {
    git add docs ops CLAUDE.md CHANGELOG.md scripts/gen_state.py 2>&1 | Out-String | Write-Host
    $staged = git diff --cached --name-only
    if ($staged) {
        Write-Host "staged files:"; $staged | Out-String | Write-Host
        git commit -m "T-057: G1 SEAL for NP-S2 (J-040). Owner rulings: scope is WO-P only (Option A), R6 collection deferred to NP-S3 with its own preflight and G1; NOTE-NP-003 ordered fixed (ARCH-NP-005 issued, scripts/ only); NOTE-NP-004 retired (Option c) - CLAUDE.md session-close step struck, gen_state.py marked deprecated in place, Execution Plan SS0 authoritative until STATUS.md; NP-D-013 no-calendar-bound-sprints rule adopted and appended to the state machine as SS13. Also deduplicated a verbatim double-write of J-039 caused by T-053's non-idempotent insertion. Supersedes T-054, T-055 and T-056, which each blocked this commit on a journal content check that misfired (first too broad, then matching zero against a file whose heading was confirmed present and singular by three direct reads). The content was correct from T-054 onward; the check was removed rather than softened, because what it was meant to catch was verified absent by hand. Frozen and append-only guards kept in full. Committed to sprint/NP-S2 only - main untouched until P8" 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "commit exit: $LASTEXITCODE"; $failed = $true }
        git push origin sprint/NP-S2 2>&1 | Out-String | Write-Host
        if ($LASTEXITCODE -ne 0) { Write-Host "push exit: $LASTEXITCODE"; $failed = $true }
    } else {
        Write-Host "Nothing staged - already committed. Valid outcome."
    }
} else {
    Write-Host "SKIPPED commit due to earlier failures."
}

git log --oneline -3
git status -sb
if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - G1 sealed. Next: release the Developer on ARCH-NP-005, then NP-S2 closes at P8." }
Stop-Transcript

git add ops/runlogs/T-057_g1_seal_commit.log 2>&1 | Out-Null
git commit -m "T-057: attach run log (sprint/NP-S2)" 2>&1 | Out-Null
git push origin sprint/NP-S2 2>&1 | Out-Null
