#!/usr/bin/env bash
# tools/run_job.sh — the ONE line the Owner ever types:  ./tools/run_job.sh
#
# No arguments, no paths, no job numbers. The ARCHITECT writes
# comms/jobs/pending/<id>.job; the Owner runs this constant line; the
# Architect reads comms/jobs/done/<id>.log himself.
#
# Design after reference/comms_v1 WO-09's runner (previous era), re-implemented
# for the fresh-start era. Its guards are kept because each was earned:
#   - WRONG CWD refuses (checkpoints are claims).
#   - EMPTY PENDING refuses loudly — zero results is never a quiet success.
#   - WHITELIST: every command line is checked BEFORE anything executes; one
#     bad line refuses the WHOLE job, naming it. Nothing outside the job file
#     is ever evaluated.
#   - REFS GUARD: the job must cite an authorizing message id that really
#     exists in comms/. An unauthorised job cannot run.
#   - STOP ON FIRST FAILURE; the log is still written, the job still moves.
#   - The log always ends RESULT: OK or RESULT: FAILED at line N. A log with
#     no RESULT line means the job died and is treated as FAILED.
#
# JOB FILE FORMAT (exact):
#   line 1: id: JOB-<nnn>
#   line 2: refs: <authorizing message id, must exist in comms/>
#   line 3: type: git|test|admin
#   line 4: (blank)
#   line 5+: command lines, executed top to bottom. Lines starting with #
#            are comments and are not executed.
set -uo pipefail

REPO_ROOT="${RUN_JOB_REPO_ROOT:-/f/NeelPrajnaPro}"
PENDING_DIR="$REPO_ROOT/comms/jobs/pending"
DONE_DIR="$REPO_ROOT/comms/jobs/done"
LOG_MIRROR="/f/NeelPrajnaProData/joblogs"

refuse() {
  echo "REFUSED: $1" >&2
  exit 1
}

CWD="$(pwd)"
if [ "$CWD" != "$REPO_ROOT" ]; then
  refuse "must be run from $REPO_ROOT, got $CWD"
fi

mkdir -p "$PENDING_DIR" "$DONE_DIR" "$LOG_MIRROR"

shopt -s nullglob
PENDING_FILES=("$PENDING_DIR"/*.job)
shopt -u nullglob
if [ "${#PENDING_FILES[@]}" -eq 0 ]; then
  refuse "no pending jobs in $PENDING_DIR — nothing to do"
fi

# oldest pending job first
JOB_FILE=""
OLDEST=""
for f in "${PENDING_FILES[@]}"; do
  t="$(stat -c %Y "$f")"
  if [ -z "$OLDEST" ] || [ "$t" -lt "$OLDEST" ]; then
    OLDEST="$t"; JOB_FILE="$f"
  fi
done

JOB_ID="$(sed -n '1p' "$JOB_FILE")";  JOB_ID="${JOB_ID#id: }"
REFS_ID="$(sed -n '2p' "$JOB_FILE")"; REFS_ID="${REFS_ID#refs: }"
JOB_TYPE="$(sed -n '3p' "$JOB_FILE")"; JOB_TYPE="${JOB_TYPE#type: }"

[ -n "$JOB_ID" ]  || refuse "$JOB_FILE: missing 'id:' line"
[ -n "$REFS_ID" ] || refuse "$JOB_ID: missing 'refs:' line"

# the authorizing id must really exist somewhere in comms/
if ! grep -rqxF "id: $REFS_ID" "$REPO_ROOT/comms" 2>/dev/null; then
  refuse "$JOB_ID: authorizing id '$REFS_ID' not found in comms/ — unauthorised job"
fi

COMMANDS=(); LINENOS=(); LNUM=0
while IFS= read -r LINE || [ -n "$LINE" ]; do
  LNUM=$((LNUM + 1))
  [ "$LNUM" -le 4 ] && continue
  [ -z "$LINE" ] && continue
  case "$LINE" in '#'*) continue ;; esac
  COMMANDS+=("$LINE"); LINENOS+=("$LNUM")
done < "$JOB_FILE"

[ "${#COMMANDS[@]}" -gt 0 ] || refuse "$JOB_ID: no command lines found"

# whitelist — ALL lines checked before ANY line runs
for CMD in "${COMMANDS[@]}"; do
  case "$CMD" in
    "git "*|"uv "*|"pytest "*|"ruff "*|"ls "*|"cat "*|"mkdir "*|"tools/"*) ;;
    *) refuse "$JOB_ID: non-whitelisted command line: $CMD" ;;
  esac
done

echo "PROCESSING: $JOB_ID (refs $REFS_ID, type $JOB_TYPE)"
echo "--- job file ---"; cat "$JOB_FILE"; echo "--- end job file ---"; echo

LOG="$DONE_DIR/${JOB_ID}.log"
{
  echo "JOB $JOB_ID (refs $REFS_ID, type $JOB_TYPE)"
  echo "STARTED: $(date '+%Y-%m-%d %H:%M:%S')"
  echo
  FAILED=0
  for i in "${!COMMANDS[@]}"; do
    CMD="${COMMANDS[$i]}"; LN="${LINENOS[$i]}"
    echo "+ $CMD"
    if ! bash -c "$CMD"; then
      echo
      echo "RESULT: FAILED at line $LN"
      echo "NOTHING after this line was run."
      FAILED=1
      break
    fi
    echo
  done
  [ "$FAILED" -eq 0 ] && echo "RESULT: OK"
  echo "FINISHED: $(date '+%Y-%m-%d %H:%M:%S')"
} 2>&1 | tee "$LOG"

mv "$JOB_FILE" "$DONE_DIR/${JOB_ID}.job"
cp "$LOG" "$LOG_MIRROR/${JOB_ID}_$(date +%Y%m%d_%H%M%S).log"

echo
echo "LOG WRITTEN: comms/jobs/done/${JOB_ID}.log"

grep -q '^RESULT: OK$' "$LOG" && exit 0 || exit 1
