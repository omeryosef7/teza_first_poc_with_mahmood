"""The pre-commit guard must actually block a red check_all (process failure, 2026-08-24).

WHAT HAPPENED. The standing rule is "run check_all.py before each commit". I ran it, it printed
`[check-all] 1 of 6 guards FAILED: retraction_sweep`, and I committed anyway: the shell lines were
newline-separated rather than &&-chained, so nothing gated the commit on the exit status. Running a
guard whose result you ignore is worse than not running it -- it emits a log line that looks like
diligence.

scripts/install_commit_guard.sh installs a .git/hooks/pre-commit that refuses while check_all is red.
The hook itself cannot be versioned (.git/hooks is local), so the INSTALLER is versioned and these
tests pin its behaviour.

VERIFIED BY MUTATION, not by inspection: a retracted figure was planted in a deliverable, check_all
went red, `git commit` was attempted and the hook refused with
`[pre-commit] REFUSING: check_all.py exited 1`, and the tree was then restored to green.

Run:  python -m pytest tests/test_commit_guard.py -q
"""
import os
import re
import subprocess

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER = os.path.join(ROOT, "scripts", "install_commit_guard.sh")
HOOK = os.path.join(ROOT, ".git", "hooks", "pre-commit")


def test_installer_exists_and_is_valid_shell():
    assert os.path.exists(INSTALLER), "the commit-guard installer is gone"
    r = subprocess.run(["bash", "-n", INSTALLER], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_installed_hook_is_executable():
    if not os.path.exists(HOOK):
        pytest.skip("hook not installed in this checkout; run scripts/install_commit_guard.sh")
    assert os.access(HOOK, os.X_OK), "the hook exists but is not executable, so git silently skips it"


def test_hook_runs_check_all_and_exits_nonzero_on_failure():
    """THE REGRESSION TEST. Remove the `exit 1` and this goes red."""
    if not os.path.exists(HOOK):
        pytest.skip("hook not installed")
    s = open(HOOK).read()
    assert "check_all.py" in s, "the hook no longer runs check_all"
    assert re.search(r"RC\s*-ne\s*0", s), "the hook no longer branches on check_all's exit status"
    i = s.index("RC")
    assert "exit 1" in s[i:], "the hook no longer FAILS the commit when check_all is red"


def test_hook_captures_the_exit_status_correctly():
    """`set -e` plus command substitution is how an exit status gets silently lost."""
    if not os.path.exists(HOOK):
        pytest.skip("hook not installed")
    s = open(HOOK).read()
    assert "set -uo pipefail" in s, (
        "the hook uses `set -e`; with `OUT=$(...)` that aborts before RC is read, so a red "
        "check_all would exit 0 through the hook and the commit would proceed")
    assert "RC=$?" in s, "the hook does not capture check_all's exit status at all"


def test_bypass_is_documented_and_deliberate():
    """A hook that cannot be bypassed gets uninstalled the first time it is wrong."""
    s = open(INSTALLER).read()
    assert "--no-verify" in s, "the escape hatch is undocumented; that is how guards get deleted"


def test_installer_explains_why_it_exists():
    """This repo's guards carry their failure story; one that does not gets removed as noise."""
    s = open(INSTALLER).read()
    assert "check_all" in s and ("committed anyway" in s or "ignore" in s), \
        "the installer no longer records the failure it exists to prevent"


# ---------------------------------------------------------------------------------------------
# §24.2 — the hook's file ORDER must agree with the full suite's, and the DEPLOYED hook must
# carry every file the installer lists.
# ---------------------------------------------------------------------------------------------

def _guard_tests_from(text):
    m = re.search(r'GUARD_TESTS="([^"]+)"', text, re.S)
    assert m, "GUARD_TESTS not found -- the installer's shape changed"
    return m.group(1).split()


def _installer_text():
    return open(os.path.join(ROOT, "scripts", "install_commit_guard.sh"), encoding="utf-8").read()


def test_GUARD_TESTS_is_sorted_so_hook_order_matches_suite_order():
    """⛔ THE BUG THIS PINS. pytest runs the full suite alphabetically. This list previously ran in
    append order, and the two disagreed: a contamination bug in test_guard_wiring.py failed 4 tests
    under `pytest tests/` while the hook reported 257 passed, because the hook happened to run the
    victim BEFORE the polluter. A green hook was not evidence of a green suite."""
    files = _guard_tests_from(_installer_text())
    assert files == sorted(files), (
        "GUARD_TESTS is not sorted, so the hook can pass an ordering-sensitive failure that "
        f"`pytest tests/` fails. Out of order at: {next(a for a, b in zip(files, sorted(files)) if a != b)}")


def test_every_listed_guard_test_actually_exists():
    """A path typo would silently shrink the hook's coverage -- pytest would still exit 0 on the
    rest, so the loss is invisible exactly like the ordering bug was."""
    missing = [f for f in _guard_tests_from(_installer_text())
               if not os.path.isfile(os.path.join(ROOT, f))]
    assert missing == [], f"the hook lists files that do not exist: {missing}"


def test_the_DEPLOYED_hook_carries_every_file_the_installer_lists():
    """The installer is the source of truth, and the file says so -- but nothing checked it. Both
    sessions have edited the deployed hook directly, and a re-install would drop those edits."""
    hook = os.path.join(ROOT, ".git", "hooks", "pre-commit")
    if not os.path.isfile(hook):
        pytest.skip("no pre-commit hook installed in this checkout")
    deployed = open(hook, encoding="utf-8").read()
    absent = [f for f in _guard_tests_from(_installer_text()) if f not in deployed]
    assert absent == [], (
        f"the deployed hook is missing {absent} -- re-run scripts/install_commit_guard.sh")
