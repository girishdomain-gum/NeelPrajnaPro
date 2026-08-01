# =====================================================================
# T-053_wo_p_complete_sync_and_record.ps1
# WHAT:    (1) Syncs local sprint/NP-S2 to origin (it was one merge behind -
#          the Developer's branch was cut from main, not from sprint/NP-S2,
#          and its work reached origin/sprint/NP-S2 without ever touching this
#          local checkout). (2) Records WO-P's completion in the journal.
#          (3) Commits and pushes to sprint/NP-S2 ONLY.
# WHY:     T-051's trailing block committed to MAIN mid-sprint, breaking the
#          "main untouched until P8" rule on its first day of existence. This
#          script corrects course: everything from here lands on the sprint
#          branch, nothing on main, until the P8 merge.
# NUMBERING NOTE: the Developer independently used "T-052" as a commit-message
#          prefix on ITS OWN branch, unaware of this session's own numbering -
#          a small live instance of the collision WO-Q's centralized numbering
#          exists to prevent. This script is T-053 to avoid stepping on it.
#          No collision actually occurred (different branches).
# GUARD:   Refuses to run if the current branch is main - this script must
#          operate on sprint/NP-S2 only. Refuses if SS4/SS5 of the Execution
#          Plan moved, or if any ratified ADR body/appendix was edited.
# OUTPUT:  ops\runlogs\T-053_wo_p_complete_sync_and_record.log  (committed to
#          sprint/NP-S2, NOT main - deliberate deviation from the T-037..T-051
#          pattern, per the branch model)
# =====================================================================
$ErrorActionPreference = "Continue"
$repo = "F:\NeelPrajnaPro"
$log  = Join-Path $repo "ops\runlogs\T-053_wo_p_complete_sync_and_record.log"
Set-Location $repo

Write-Host "=== T-053 WO-P COMPLETE: SYNC + RECORD (sprint/NP-S2 only) === $(Get-Date -Format o)"
Write-Host "--- [0] sync local sprint/NP-S2 to origin first ---"
git fetch origin
git checkout sprint/NP-S2
git merge origin/sprint/NP-S2 --ff-only
if ($LASTEXITCODE -ne 0) {
    Write-Host "STOP: fast-forward failed - local sprint/NP-S2 has diverged from origin."
    Write-Host "Do not proceed; this needs manual inspection before any commit."
    exit 1
}
Write-Host "OK: local sprint/NP-S2 now matches origin"
git log --oneline -3
git status -sb

Start-Transcript -Path $log -Force
$failed = $false

Write-Host "--- [1] HARD GUARD: must not be on main ---"
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
Write-Host ("current branch: " + $branch)
if ($branch -ne "sprint/NP-S2") { Write-Host "STOP: not on sprint/NP-S2 - refusing to proceed"; $failed = $true }

Write-Host "--- [2] confirm the Developer's WO-P work is visible here ---"
$eng = Join-Path $repo "qrf\trading\simulator\engine.py"
if (Select-String -Path $eng -Pattern "event_stop_column" -SimpleMatch -Quiet) { Write-Host "OK: WO-P engine changes visible on this branch" }
else { Write-Host "STOP: WO-P changes not visible - sync did not work as expected"; $failed = $true }

Write-Host "--- [3] write the journal entry (J-039) ---"
$jr = Join-Path $repo "docs\journal\NeelPrajnaPro_Journal.md"
$anchor = "**The documentation phase of this programme ends here. What follows is evidence.**"
$entry = @"
$anchor

## J-039 - 2026-07-31 - WO-P COMPLETE - execution-model parity, Sprint NP-S2
Owner confirmed CI green on origin/sprint/NP-S2 for the Developer's WO-P commits.
Independent verification attempted from this session (GitHub Actions API) returned
403 - unauthenticated rate limit exhausted; no credential entry was made, per the
standing prohibition on handling tokens. The Owner's confirmation is the record
here - a legitimate division of labour, not a gap papered over.

What shipped. ExecutionSpec gains event_stop_column (per-trade stop, sourced from
one of the kernel's three float64 EventFrame columns - level, zone_hi, zone_lo)
and target_r_multiple (R-multiple target, computed from realized risk). Both
resolve to a per-trade EFFECTIVE stop_offset/target_offset once, at entry, inside
EventEngine.simulate, then flow through the UNMODIFIED fills.resolve_exit.
Verified by this session's own direct read of engine.py: when neither new field
is set, the effective values equal the legacy scalars with ZERO arithmetic - so
AC-1 (byte-identical reproduction of every existing sealed verdict) holds BY
CONSTRUCTION, not merely by test. engine_version s5.1 -> s5.2. Registration
validation refuses all three AC-5 cases plus two additional mutual-exclusivity
guards the Developer identified as implied by Section 4.5's own framing. AC-1
through AC-7 all evidenced with passing tests, cited in the handover's Section 7.

Two real, pre-existing gaps found and left alone - correctly. scripts/rebuild_bulk.py
has no dispatch entry for the h007 lineage (NOTE-NP-003) - outside WO-P's
qrf/**+tests/** scope, worked around in-test rather than fixed. NOTE-NP-004
traces back to this Architect's own T-009 restructuring, several hundred commits
ago in this same session: docs/handover/AI_PROJECT_STATE.md was archived to
docs/archive/gen1/ and nothing since recreated a live file at the path
scripts/gen_state.py still targets - meaning CLAUDE.md's session-close step has
been silently unrunnable since T-009, and every session between then and this
one either skipped it or never noticed. The Developer refused to hand-write
around it, correctly citing that doing so would violate the very rule ("only
sanctioned way to touch this file") the step depends on. Finding recorded
against the Architect, spanning the whole session to date.

A second self-caught deviation, from this Architect, on the branch model's first
real day. T-051's trailing block - following the T-037-T-050 pattern of always
finishing on main - committed the run-log attach to MAIN, mid-sprint, directly
contradicting the "main untouched until P8" rule sealed in
SPRINT_STATE_MACHINE_v1.1.md the same day. The rule was broken on its first
opportunity to apply it. Corrected from this point forward - this entry and its
commit land on sprint/NP-S2 only; T-051 itself stands unedited, per P5.

A live near-collision, worth naming rather than fixing with new design: the
Developer's own second commit used the message prefix "T-052" - independently,
unaware of this session's own T-numbering sequence. No actual collision occurred
(different branches, no shared registry), but it is a small, concrete instance
of the numbering-discipline gap WO-Q's centralized allocation exists to close.
No action taken; noted for whenever that ladder is built.

Sprint state: WO-P (the gating deliverable) is COMPLETE. The G1 scope decision -
narrow to WO-P only, or seal all four decisions for the full three-track scope -
remains OPEN and is unaffected by WO-P's completion. NOTE-NP-003 and NOTE-NP-004
await disposition (recommended, not yet actioned): a small follow-up fix for the
former; for the latter, either restore a live handover file seeded from the
archived Gen-1 prose, or repoint gen_state.py and CLAUDE.md - Owner's call, since
it touches a file CLAUDE.md calls normative.
"@
$content = Get-Content $jr -Raw
if ($content -notmatch [regex]::Escape($anchor)) { Write-Host "STOP: anchor line not found - cannot insert J-039"; $failed = $true }
else {
    $newContent = $content -replace [regex]::Escape($anchor), $entry
    Set-Content -Path $jr -Value $newContent -NoNewline
    if (Select-String -Path $jr -Pattern "J-039" -SimpleMatch -Quiet) { Write-Host "OK: J-039 written" } else { Write-Host "STOP: J-039 write failed verification"; $failed = $true }
}

Write-Host "--- [4] FROZEN GUARDS ---"
$ep = Join-Path $repo "docs\execution_plan\NeelPrajnaPro_Execution_Plan-v2.0.md"
$s4 = Select-String -Path $ep -Pattern "SEALED 2026-07-30 by Owner GO" -SimpleMatch -Quiet
$s5 = Select-String -Path $ep -Pattern "H-07 SEALED MECHANICAL DEFINITION v1.0" -SimpleMatch -Quiet
if ($s4 -and $s5) { Write-Host "OK: SS4 seal line and SS5 heading intact" } else { Write-Host "STOP: frozen markers missing"; $failed = $true }
foreach ($f in @("ops/NP-ADR-H07_definition_v1.1_draft_v2.0.md","ops/NP-ADR-008_APPENDIX-A_provenance_correction.md","ops/NP-ADR-008_APPENDIX-B_pinned_detector_mechanics.md")) {
  $d = git diff --stat HEAD -- $f 2>&1 | Out-String
  if ($d.Trim()) { Write-Host ("STOP: " + $f + " modified"); Write-Host $d; $failed = $true }
  else { Write-Host ("OK: untouched - " + $f) }
}

Write-Host "--- [5] commit and push to sprint/NP-S2 ONLY - never main ---"
if (-not $failed) {
    git add docs/journal/NeelPrajnaPro_Journal.md 2>&1 | Out-String | Write-Host
    git commit -m "T-053: J-039 - WO-P complete (execution-model parity). CI confirmed by Owner. AC-1 verified by direct read to hold by construction. Two pre-existing gaps documented (NOTE-NP-003 rebuild_bulk.py, NOTE-NP-004 gen_state.py target missing since this session's own T-009). Two self-caught findings: T-051 committed to main mid-sprint against the branch model's own first rule; T-052 numbering near-collision with the Developer's independent commit. G1 scope decision remains open. Committed to sprint/NP-S2 ONLY per the branch model - main stays untouched until P8" 2>&1 | Out-String | Write-Host
    git push origin sprint/NP-S2 2>&1 | Out-String | Write-Host
} else {
    Write-Host "SKIPPED commit due to earlier failures."
}

git log --oneline -3
git status -sb
if ($failed) { Write-Host "`nRESULT: FAILED - see sections above" } else { Write-Host "`nRESULT: OK - J-039 recorded on sprint/NP-S2 only. main untouched, as designed." }
Stop-Transcript

git add ops/runlogs/T-053_wo_p_complete_sync_and_record.log 2>&1 | Out-Null
git commit -m "T-053: attach run log (sprint/NP-S2)" 2>&1 | Out-Null
git push origin sprint/NP-S2 2>&1 | Out-Null
