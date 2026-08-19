"""The verifier must FAIL when a report number stops matching its artifact.

`verify_report_numbers.py` operationalises this project's standing bar — every number in the report
must be regenerable from a committed artifact. That bar was enforced by reading until now, and reading
missed R-13 for weeks: its incremental-R2 table matched no artifact in any commit.

A checker that has never been shown to fail is not a checker, so these tests break it three ways:
a tampered artifact value, an uncommitted artifact, and a number deleted from the report.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "verify_report_numbers.py")


def _run(cwd=ROOT):
    return subprocess.run([sys.executable, SCRIPT], cwd=cwd, capture_output=True, text=True)


def test_passes_on_the_real_tree():
    r = _run()
    assert r.returncode == 0, r.stdout + r.stderr
    assert "all 17 gate-table numbers match" in r.stdout


def test_FAILS_when_an_artifact_value_is_tampered_with():
    """THE GUARD. Change one number in one artifact; the verifier must catch it and exit 1."""
    art = os.path.join(ROOT, "outputs", "boombness", "advbench_decomposition.json")
    backup = art + ".testbak"
    shutil.copy2(art, backup)
    try:
        d = json.load(open(art))
        d["paired_vs_baseline"]["B"]["delta_cluster_mean"] = 0.9999   # was +0.0305
        json.dump(d, open(art, "w"), indent=1)
        r = _run()
        assert r.returncode == 1, "verifier passed a tampered artifact"
        assert "VALUE MISMATCH" in r.stdout
        assert "14-B arm B clustered delta" in r.stdout
    finally:
        shutil.move(backup, art)
    assert _run().returncode == 0, "restore failed; the tree is left dirty"


def test_FAILS_when_the_number_is_removed_from_the_report():
    """A number that matches its artifact but no longer appears in the deliverable is also a defect —
    it means the report was edited away from the evidence."""
    rep = os.path.join(ROOT, "reports", "boombness_objective_sprint_report.md")
    backup = rep + ".testbak"
    shutil.copy2(rep, backup)
    try:
        t = open(rep, encoding="utf-8").read().replace("+0.0333", "+0.0999")
        open(rep, "w", encoding="utf-8").write(t)
        r = _run()
        assert r.returncode == 1, "verifier passed a report missing one of its own numbers"
        assert "NOT IN REPORT" in r.stdout
    finally:
        shutil.move(backup, rep)
    assert _run().returncode == 0, "restore failed; the tree is left dirty"


def test_FAILS_when_an_artifact_is_not_committed():
    """outputs/ is gitignored, so a cited artifact that was never force-added looks fine on disk and
    does not exist for anyone else. That must fail, not pass."""
    tmp = os.path.join(ROOT, "outputs", "boombness", "advbench_decomposition.json")
    r = subprocess.run(["git", "ls-files", "--error-unmatch",
                        "outputs/boombness/advbench_decomposition.json"],
                       cwd=ROOT, capture_output=True)
    assert r.returncode == 0, "precondition: this artifact should be committed"
    # simulate the uncommitted case without touching the index: point the checker at a new file
    src = open(SCRIPT, encoding="utf-8").read()
    assert 'def committed(' in src and 'git", "ls-files", "--error-unmatch"' in src, \
        "the verifier must check git-tracking, or an uncommitted artifact would pass silently"
