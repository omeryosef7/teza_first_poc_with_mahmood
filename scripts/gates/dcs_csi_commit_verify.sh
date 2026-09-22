#!/bin/sh
# Commit + push, then VERIFY THE WRITE ACTUALLY HAPPENED. S-262.
#
# WHY THIS EXISTS. The sprint's standing rule is "verify every repo write". Every FILE write in this
# log is verified by line delta plus prefix md5 -- and COMMITS were not, because the commit command's
# own output was trusted. On 2026-09-23 a commit was cut short mid-hook: git had staged the file and
# written COMMIT_EDITMSG (2104 bytes), the working tree still held the entry, and NOTHING WAS
# COMMITTED. It reported nothing because the process ended before it could. The gap was found by
# checking HEAD at the start of the next tick, which is luck dressed as discipline.
#
# A commit is a repo write. This verifies it the same way a file write is verified: by reading the
# state back and comparing it to what was expected, rather than by believing the tool.
#
# usage:  dcs_csi_commit_verify.sh <message-file> [paths...]
set -eu
[ $# -ge 1 ] || { echo "usage: $0 <message-file> [paths...]" >&2; exit 2; }
MSG="$1"; shift
[ -s "$MSG" ] || { printf "REFUSING: message file %s is missing or empty\n" "$MSG" >&2; exit 2; }

BEFORE=$(git rev-parse HEAD)
if [ $# -gt 0 ]; then git add -A "$@"; fi

STAGED=$(git diff --cached --name-only | wc -l)
if [ "$STAGED" -eq 0 ]; then
  echo "REFUSING: nothing is staged -- a commit here would be empty and would report success" >&2
  exit 3
fi

# R23: `set -e` would abort here with git's own exit code, so the NAMED checks below were DEAD CODE
# (measured: a failing push gave rc=128 and git's generic error, never the rc=5 message). The statuses
# are captured explicitly so the named diagnostic is the thing the operator sees.
COMMIT_RC=0
git commit -q -F "$MSG" || COMMIT_RC=$?

AFTER=$(git rev-parse HEAD)
if [ "$BEFORE" = "$AFTER" ]; then
  echo "FAILED: HEAD did not move ($BEFORE). The commit did NOT happen (git commit rc=$COMMIT_RC)." >&2
  exit 4
fi
if [ "$COMMIT_RC" -ne 0 ]; then
  echo "FAILED: git commit exited $COMMIT_RC yet HEAD moved -- inspect before trusting $AFTER" >&2
  exit 4
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD)
PUSH_RC=0
git push -q origin "$BRANCH" || PUSH_RC=$?
if [ "$PUSH_RC" -ne 0 ]; then
  echo "FAILED: git push exited $PUSH_RC. The COMMIT LANDED LOCALLY ($AFTER) and is NOT on origin." >&2
  echo "  The working tree is clean and the entry is safe; re-run the push alone." >&2
  exit 5
fi

REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo NONE)
if [ "$REMOTE" != "$AFTER" ]; then
  echo "FAILED: push did not land. local $AFTER, origin $REMOTE" >&2
  exit 5
fi

DIRTY=$(git status --porcelain --untracked-files=no | wc -l)
echo "VERIFIED  HEAD $BEFORE -> $AFTER  |  origin matches  |  dirty tracked: $DIRTY  |  staged: $STAGED"
[ "$DIRTY" -eq 0 ] || echo "  NOTE: $DIRTY tracked file(s) still modified -- not part of this commit"
