#!/bin/bash
# guarded_commit.sh — run the deliverable guards, and commit ONLY if they pass.
#
# WHY THIS EXISTS. Twice in three days I pushed a commit while a guard was failing, because the
# workflow was `check_all; echo $?; git commit` -- which prints the failure and commits anyway. The
# guard did its job both times; I read its output after the push. Running a guard is not the same as
# reading it, and a check whose result does not gate anything is a check that depends on my attention
# at the moment I am least likely to have any.
#
# NOT a pre-commit hook, deliberately: a concurrent session shares this repo and a hook would block
# its commits too. This gates only my own commits, by being the thing I call instead of `git commit`.
#
# Usage:  scripts/guarded_commit.sh <<'MSG'
#         subject line
#
#         body
#         MSG
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python

msg="$(cat)"
[ -n "$msg" ] || { echo "guarded_commit: empty message, refusing" >&2; exit 2; }

echo "=== guards ==="
if ! "$PY" src/boombness/check_all.py; then
  echo >&2
  echo "guarded_commit: REFUSING TO COMMIT — deliverable guards failed (see above)." >&2
  echo "Fix the failure, or commit deliberately with git if the guard is wrong." >&2
  exit 1
fi

git add -A
printf '%s\n' "$msg" | git commit -q -F - && git push -q origin "$(git rev-parse --abbrev-ref HEAD)"
echo "=== committed and pushed ==="
