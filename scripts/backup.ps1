<#
.SYNOPSIS
    QRF backup - commit the repo and mirror the ledger to a second location.

.DESCRIPTION
    ARCH-001 deliverable. Two independent durability steps:
      1. git add/commit (and push, once the Owner has added a remote).
      2. robocopy datastore/journal/ to a configurable second path - an
         off-repo copy of THE ledger (datastore/journal/ is the tracked root
         of trust; bulk/ and index/ are rebuildable and not mirrored here).

    Push is skipped gracefully when no remote is configured (Session 0 leaves
    the remote to the Owner). Nothing here is destructive.

.PARAMETER BackupPath
    Destination directory for the journal mirror. Defaults to the QRF_BACKUP
    environment variable, else <repo>\..\QRF_backup.

.PARAMETER Message
    Commit message. Defaults to a timestamped "backup:" message.

.PARAMETER NoCommit
    Skip the git commit/push step (mirror only).

.EXAMPLE
    powershell -File scripts/backup.ps1 -BackupPath D:\backups\qrf
#>
[CmdletBinding()]
param(
    [string]$BackupPath = "",
    [string]$Message = "",
    [switch]$NoCommit
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Journal = Join-Path $RepoRoot "datastore\journal"

if (-not $Message) {
    $Message = "backup: " + (Get-Date -Format 'yyyy-MM-dd HH:mm')
}
if (-not $BackupPath) {
    $BackupPath = $env:QRF_BACKUP
}
if (-not $BackupPath) {
    $BackupPath = Join-Path (Split-Path -Parent $RepoRoot) "QRF_backup"
}

Write-Host "QRF backup"
Write-Host "  repo:     $RepoRoot"
Write-Host "  journal:  $Journal"
Write-Host "  mirror:   $BackupPath"

# --- 1. git commit (+ push if a remote exists) -------------------------------
if (-not $NoCommit) {
    Push-Location $RepoRoot
    try {
        git add -A
        # Commit only if there is something staged.
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            git commit -m $Message
            Write-Host "  committed: $Message"
        } else {
            Write-Host "  commit:    nothing to commit"
        }

        $remotes = @(git remote)
        if ($remotes.Count -gt 0) {
            $branch = (git rev-parse --abbrev-ref HEAD).Trim()
            git push origin $branch
            Write-Host "  pushed:    origin/$branch"
        } else {
            Write-Host "  push:      SKIPPED - no git remote configured yet (Owner adds it)"
        }
    } finally {
        Pop-Location
    }
}

# --- 2. mirror the journal ---------------------------------------------------
if (-not (Test-Path $Journal)) {
    Write-Warning "journal directory not found: $Journal - nothing to mirror"
    exit 0
}
New-Item -ItemType Directory -Force -Path $BackupPath | Out-Null

# robocopy exit codes 0-7 are success (8+ are failures).
robocopy $Journal $BackupPath /MIR /R:2 /W:2 /NP /NDL | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    Write-Error "robocopy failed (exit $rc)"
    exit $rc
}
Write-Host "  mirrored:  journal -> $BackupPath (robocopy rc=$rc)"
Write-Host "done."
