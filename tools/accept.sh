#!/usr/bin/env bash
# tools/accept.sh — WO-06 (S2, refs A-006): mechanizes GIT_WORKFLOW.md §4's
# accept ritual (dev -> main). Refuses to touch main unless the cited message
# id is an Architect REVIEW-RESULT containing APPROVED (comms\developer.md),
# the tree is clean, and cwd is the repo root — then executes §4 exactly, with
# set -e stop-on-first-error, and tees the COMPLETE log so the Owner's paste
# satisfies GIT_WORKFLOW.md's COMPLETION RULE unchanged.
#
# Usage: tools/accept.sh <Snn> <authorizing-msg-id> [--dry-run]
#
# --dry-run runs every guard and reports what WOULD happen, without touching
# git state at all (no checkout, no fetch-merge, no push) — used to drill the
# refusal paths per the project's drill law (no checker trusted until a
# tamper drill shows it can go RED).
#
# ACCEPT_REPO_ROOT overrides the expected repo root (default: /f/NeelPrajnaPro,
# the Owner's Git Bash path to F:\NeelPrajnaPro per GIT_WORKFLOW.md §2/§9).
# Exists ONLY so the drill tests can point this script at a disposable scratch
# repo instead of ever touching the real one — the Owner's real invocations
# never set it, so the wrong-cwd guard still enforces the real path for them.
set -euo pipefail

REPO_ROOT="${ACCEPT_REPO_ROOT:-/f/NeelPrajnaPro}"
DEVELOPER_INBOX="$REPO_ROOT/comms/developer.md"

usage() {
  echo "Usage: tools/accept.sh <Snn> <authorizing-msg-id> [--dry-run]" >&2
  exit 2
}

if [ "$#" -lt 2 ]; then
  usage
fi
SNN="$1"
MSG_ID="$2"
DRY_RUN=0
if [ "${3:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

refuse() {
  echo "REFUSED: $1" >&2
  exit 1
}

# --- guard: wrong cwd (checkpoint per GIT_WORKFLOW.md §2 command-block safety)
CWD="$(pwd)"
if [ "$CWD" != "$REPO_ROOT" ]; then
  refuse "must run from $REPO_ROOT, got $CWD"
fi

# --- guard: dirty tree --------------------------------------------------------
if [ -n "$(git -C "$REPO_ROOT" status --porcelain)" ]; then
  refuse "working tree is dirty — commit, stash, or investigate before accepting"
fi

# --- guard: authorizing id must be a REVIEW-RESULT containing APPROVED -------
if [ ! -f "$DEVELOPER_INBOX" ]; then
  refuse "$DEVELOPER_INBOX not found"
fi

BLOCK="$(awk -v id="$MSG_ID" '
  $0 == "---" {
    if (capturing) { exit }
    next
  }
  /^id: / {
    if ($2 == id) { capturing = 1 }
  }
  capturing { print }
' "$DEVELOPER_INBOX")"

if [ -z "$BLOCK" ]; then
  refuse "message id $MSG_ID not found in $DEVELOPER_INBOX"
fi

if ! printf '%s\n' "$BLOCK" | grep -q '^type: REVIEW-RESULT'; then
  refuse "$MSG_ID is not a REVIEW-RESULT message"
fi

if ! printf '%s\n' "$BLOCK" | grep -qw 'APPROVED'; then
  refuse "$MSG_ID's REVIEW-RESULT does not contain APPROVED"
fi

echo "AUTHORIZED: $MSG_ID is a REVIEW-RESULT containing APPROVED"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "DRY RUN: all guards passed — would accept $SNN citing $MSG_ID. No git commands run."
  exit 0
fi

# --- §4 merge ritual, executed exactly, logged completely -------------------
cd "$REPO_ROOT"
LOG="$REPO_ROOT/comms/accept_${SNN}.log"
{
  set -x
  git checkout main
  git pull origin main
  git fetch origin
  git merge --no-ff origin/dev -m "Accept ${SNN} - ${MSG_ID} APPROVED"
  git push origin main
  set +x
} 2>&1 | tee "$LOG"

echo "--- post-merge git log (paste this to the Architect, per COMPLETION RULE) ---"
git log --oneline -3
