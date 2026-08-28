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

# GUARD TESTS. check_all runs the guards; it does NOT run the tests that prove the guards can FAIL.
# A guard whose refusal branch has been broken still exits 0 on a clean corpus, so the hook was
# green on exactly the mutants this sprint kept finding: a NaN filter removed, a proximity window
# widened to the whole document, an attrition check disabled. Both sessions found the same gap in
# their own hooks on 2026-08-28 -- pytest gates nothing at commit time.
#
# Only the GUARD test files run here, not the full suite: 140 tests in ~1.4s against ~11 minutes,
# and a hook slow enough to skip is a hook that gets skipped.
GUARD_TESTS="tests/test_cited_artifact_check.py tests/test_ledger_propagation_check.py
             tests/test_option_mass_nan_guard.py tests/test_margin_exposure.py
             tests/test_intervention_liveness.py tests/test_asr_protocol.py
             tests/test_fcslots_preset.py tests/test_clustered_stats.py
             tests/test_my_ledger_propagation.py tests/test_my_cited_artifacts.py
             tests/test_cautioned_figures.py"
# NOTE: this list spans BOTH concurrent sessions deliberately. The three tests above were
# added to the DEPLOYED hook directly by the other session; the installer had only the first
# eight, so re-running it would have silently dropped them and restored the state in which
# that session's deliverables were unguarded at commit time. The installer is the source of
# truth and must therefore carry every guard the hook runs.
echo "[pre-commit] running guard tests ..."
# shellcheck disable=SC2086
TOUT="$(cd "$R" && "$PY" -m pytest $GUARD_TESTS -q 2>&1)" ; TRC=$?
echo "$TOUT" | tail -2
if [ $TRC -ne 0 ]; then
  echo "[pre-commit] REFUSING: a guard TEST failed -- a guard may no longer be able to fail." >&2
  exit 1
fi
exit 0
HOOKEOF
chmod +x "$HOOK"
echo "[install] pre-commit hook installed at $HOOK"
