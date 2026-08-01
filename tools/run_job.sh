#!/usr/bin/env bash
# tools/run_job.sh — WO-09 (S3, refs A-009): the file-based job runner. Ends
# Owner copy-paste relaying: the Architect writes comms\jobs\pending\<id>.job,
# the Owner runs this ONE constant line, the Architect reads
# comms\jobs\done\<id>.log himself. No daemon, no live socket.
#
# JOB FILE FORMAT (plain text), exactly:
#   line 1: id: JOB-<nnn>
#   line 2: refs: <authorizing message id, must exist in comms\developer.md>
#   line 3: type: git_block|pytest|accept
#   line 4: (blank)
#   line 5+: command lines, one per line, executed top to bottom
#
# WHITELIST (strict, per the bridge's law): every command line must start
# with "git ", ".venv/Scripts/python.exe ", or "tools/accept.sh " — anything
# else REFUSES THE WHOLE JOB loudly, before executing anything, naming the
# offending line. No eval of anything outside the job file.
#
# Usage: tools/run_job.sh — no arguments. Picks the OLDEST pending job (by
# file modification time), executes it, tees COMPLETE output (stdout+stderr,
# every command echoed) to comms\jobs\done\<id>.log, moves the .job file to
# done\ beside its log. On any failing command line: stop immediately, still
# write the log, still move the job, append "RESULT: FAILED at line N" to
# the log. On success: append "RESULT: OK". Exit code mirrors the result.
#
# RUN_JOB_REPO_ROOT overrides the expected repo root — exists ONLY so the
# drill tests can point this script at a disposable scratch repo instead of
# ever touching the real one; the Owner's real invocations never set it, so
# the wrong-cwd guard still enforces the real F:\NeelPrajnaPro path for them.
set -euo pipefail

REPO_ROOT="${RUN_JOB_REPO_ROOT:-/f/NeelPrajnaPro}"
DEVELOPER_INBOX="$REPO_ROOT/comms/developer.md"
PENDING_DIR="$REPO_ROOT/comms/jobs/pending"
DONE_DIR="$REPO_ROOT/comms/jobs/done"

refuse() {
  echo "REFUSED: $1" >&2
  exit 1
}

# --- guard: wrong cwd (checkpoint per GIT_WORKFLOW.md §2 command-block safety)
CWD="$(pwd)"
if [ "$CWD" != "$REPO_ROOT" ]; then
  refuse "must run from $REPO_ROOT, got $CWD"
fi

mkdir -p "$PENDING_DIR" "$DONE_DIR"

# --- guard: pending is empty (loud — zero results is never a quiet success) --
shopt -s nullglob
PENDING_FILES=("$PENDING_DIR"/*.job)
shopt -u nullglob
if [ "${#PENDING_FILES[@]}" -eq 0 ]; then
  refuse "no pending jobs in $PENDING_DIR"
fi

# --- pick the OLDEST pending job by modification time -------------------------
JOB_FILE=""
OLDEST_TIME=""
for f in "${PENDING_FILES[@]}"; do
  t="$(stat -c %Y "$f")"
  if [ -z "$OLDEST_TIME" ] || [ "$t" -lt "$OLDEST_TIME" ]; then
    OLDEST_TIME="$t"
    JOB_FILE="$f"
  fi
done

# --- parse the job file's fixed header ----------------------------------------
ID_LINE="$(sed -n '1p' "$JOB_FILE")"
REFS_LINE="$(sed -n '2p' "$JOB_FILE")"
TYPE_LINE="$(sed -n '3p' "$JOB_FILE")"
JOB_ID="${ID_LINE#id: }"
REFS_ID="${REFS_LINE#refs: }"
JOB_TYPE="${TYPE_LINE#type: }"

if [ -z "$JOB_ID" ]; then
  refuse "$JOB_FILE: missing id: line"
fi

# --- guard: refs id must exist in comms\developer.md --------------------------
if [ ! -f "$DEVELOPER_INBOX" ]; then
  refuse "$DEVELOPER_INBOX not found"
fi
if ! grep -qxF "id: $REFS_ID" "$DEVELOPER_INBOX"; then
  refuse "$JOB_ID: refs id $REFS_ID not found in $DEVELOPER_INBOX"
fi

# --- collect command lines (line 5+), keeping real file line numbers ---------
# (named LNUM, not LINENO — LINENO is bash's own read-only-in-effect special
# variable tracking the SCRIPT's current line; assigning to it silently does
# nothing useful and was drilled out as a real bug during WO-09 development)
COMMANDS=()
LINENOS=()
LNUM=0
while IFS= read -r LINE || [ -n "$LINE" ]; do
  LNUM=$((LNUM + 1))
  if [ "$LNUM" -le 4 ]; then
    continue
  fi
  if [ -z "$LINE" ]; then
    continue
  fi
  COMMANDS+=("$LINE")
  LINENOS+=("$LNUM")
done < "$JOB_FILE"

if [ "${#COMMANDS[@]}" -eq 0 ]; then
  refuse "$JOB_ID: no command lines found"
fi

# --- guard: whitelist — check ALL lines BEFORE executing anything ------------
for CMD in "${COMMANDS[@]}"; do
  case "$CMD" in
    "git "* | ".venv/Scripts/python.exe "* | "tools/accept.sh "*) ;;
    *) refuse "$JOB_ID: non-whitelisted command line: $CMD" ;;
  esac
done

echo "PROCESSING: $JOB_ID (refs $REFS_ID, type $JOB_TYPE)"
echo "--- job file content ---"
cat "$JOB_FILE"
echo "--- end job file content ---"

LOG="$DONE_DIR/${JOB_ID}.log"
{
  echo "JOB $JOB_ID (refs $REFS_ID, type $JOB_TYPE)"
  FAILED=0
  for i in "${!COMMANDS[@]}"; do
    CMD="${COMMANDS[$i]}"
    LN="${LINENOS[$i]}"
    echo "+ $CMD"
    if ! bash -c "$CMD"; then
      echo "RESULT: FAILED at line $LN"
      FAILED=1
      break
    fi
  done
  if [ "$FAILED" -eq 0 ]; then
    echo "RESULT: OK"
  fi
} 2>&1 | tee "$LOG"

mv "$JOB_FILE" "$DONE_DIR/${JOB_ID}.job"

if grep -q '^RESULT: OK$' "$LOG"; then
  exit 0
else
  exit 1
fi
