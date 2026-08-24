#!/bin/bash
# Installs a pre-commit hook that BLOCKS a commit when check_all.py is red.
#
# WHY (2026-08-24). The standing rule is "run check_all.py before each commit". I ran it, it printed
#   [check-all] 1 of 6 guards FAILED: retraction_sweep
# and I committed anyway -- the shell lines were newline-separated rather than &&-chained, so nothing
# gated the commit on the exit status. Running a guard whose result you ignore is worse than not
# running it: it produces a log line that looks like diligence.
#
# The hook is NOT versioned by git (.git/hooks is local), which is why this installer is, so the
# protection is reproducible for anyone on the branch rather than living only in my working copy.
#
# Escape hatch: `git commit --no-verify` still works, deliberately -- a hook that cannot be bypassed
# gets uninstalled the first time it is wrong. Bypassing is then a visible, deliberate act.
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$R/.git/hooks/pre-commit"
mkdir -p "$R/.git/hooks"
cat > "$HOOK" <<'HOOKEOF'
#!/bin/bash
# Auto-installed by scripts/install_commit_guard.sh -- blocks commits while check_all.py is red.
set -uo pipefail
R="$(git rev-parse --show-toplevel)"
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
[ -x "$PY" ] || PY=python
echo "[pre-commit] running check_all.py ..."
OUT="$("$PY" "$R/src/boombness/check_all.py" 2>&1)" ; RC=$?
echo "$OUT" | tail -3
if [ $RC -ne 0 ]; then
  echo "[pre-commit] REFUSING: check_all.py exited $RC. Fix the guard, or use --no-verify deliberately." >&2
  exit 1
fi
exit 0
HOOKEOF
chmod +x "$HOOK"
echo "[install] pre-commit hook installed at $HOOK"
