"""Guards for the two defects fixed in analyze_steering.py on 2026-08-18.

Both tests FAIL against the pre-fix module (loaded from git HEAD via
`git show HEAD:src/boombness/analyze_steering.py`) and PASS against the working tree, which is the
only evidence that either guard can actually fire:

  T2  — the print loop read `r['wilson95']` while the row dict wrote `wilson95_IID_UNDERSTATES`,
        an unconditional KeyError on the baseline row that aborted the script before the coherence
        gate, the contrasts, the band, the sign test and the JSON write.
  T2b — `require_done` was enforced on `--baseline` only, so a truncated INTERVENTION arm (no
        DONE.json) was analysed and reported silently.

Run:
  /home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python -m pytest \
      tests/test_analyze_steering.py -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile

import pytest

# PRE-FIX BASELINE, PINNED (2026-08-18). These tests demonstrate the defect by loading the version
# of the module that had it. They originally used `git show HEAD:...`, which is self-invalidating:
# the moment the fix is committed, HEAD *contains* the fix and the "this must fail pre-fix"
# assertions stop holding. That turned three green tests red with no code regression -- a test that
# silently changes what it asserts as the branch moves is worse than no test. The baseline is now
# pinned to the commit that introduced the fix, minus one.
PREFIX_BASELINE = "a8251ffa~1"


REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src", "boombness")
DOMAINS = ["d0", "d1", "d2", "d3", "d4", "d5"]


def _load(path: str, name: str):
    """Import a copy of analyze_steering by path, with src/boombness on sys.path."""
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def prefix_module(tmp_path_factory):
    p = tmp_path_factory.mktemp("prefix") / "old_analyze_steering.py"
    with open(p, "w") as f:
        subprocess.run(["git", "show", f"{PREFIX_BASELINE}:src/boombness/analyze_steering.py"],
                       cwd=REPO, stdout=f, check=True)
    return _load(str(p), "old_analyze_steering")


@pytest.fixture(scope="module")
def fixed_module():
    return _load(os.path.join(SRC, "analyze_steering.py"), "new_analyze_steering")


def _make_run(root: str, tag: str, *, done: bool = True, shift: float = 0.0, n: int = 60):
    d = os.path.join(root, f"{tag}_20260818_000000_1")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for i in range(n):
            # domain-correlated scores: with an iid score pattern every domain has an
            # identical mix, the cluster bootstrap has zero spread, and the width ratio
            # is undefined rather than informative.
            s = max(0.0, min(1.0, ((i % 10) / 10.0) * (0.4 + 0.2 * (i % 6)) + shift))
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "strongreject_score": s, "refused": s < 0.2,
                                "domain": DOMAINS[i % len(DOMAINS)]}) + "\n")
    with open(os.path.join(d, "config.json"), "w") as f:
        json.dump({"args": {}}, f)
    if done:
        with open(os.path.join(d, "DONE.json"), "w") as f:
            json.dump({"ok": True}, f)
    return d


def _run(mod, base, arms, out, extra=()):
    argv = ["analyze_steering", "--baseline", base, "--arms", *arms,
            "--out", out, "--allow-missing-coherence", *extra]
    old = sys.argv
    sys.argv = argv
    try:
        return mod.main()
    finally:
        sys.argv = old


def test_T2_print_loop_key_and_json_written(prefix_module, fixed_module, capsys):
    """Pre-fix: KeyError('wilson95') and no JSON. Post-fix: JSON written, both CIs printed."""
    with tempfile.TemporaryDirectory() as root:
        base = _make_run(root, "base")
        arms = [_make_run(root, "steer_a025", shift=-0.1),
                _make_run(root, "steer_neg_a025", shift=-0.05)]

        out_old = os.path.join(root, "old.json")
        with pytest.raises(KeyError) as ei:
            _run(prefix_module, base, arms, out_old)
        assert "wilson95" in str(ei.value)
        assert not os.path.exists(out_old), "pre-fix must never reach the JSON write"

        out_new = os.path.join(root, "new.json")
        assert _run(fixed_module, base, arms, out_new) == 0
        printed = capsys.readouterr().out
        assert os.path.exists(out_new)
        rep = json.load(open(out_new))
        assert {r["arm"] for r in rep["rows"]} == {"baseline", "steer_a025", "steer_neg_a025"}
        for r in rep["rows"]:
            assert "wilson95_IID_UNDERSTATES" in r and "ci95_domain_clustered" in r
            assert r["ci_width_ratio_clustered_over_iid"] > 0
        # the iid interval must never be shown as if it were the clustered one
        assert "domain-clustered" in printed and "UNDERSTATES" in printed


def test_T2b_require_done_enforced_on_intervention_arms(prefix_module, fixed_module):
    """An arm with no DONE.json must stop the run. Pre-fix it was analysed and reported."""
    with tempfile.TemporaryDirectory() as root:
        base = _make_run(root, "base")
        arms = [_make_run(root, "steer_a025", shift=-0.1, done=False),
                _make_run(root, "steer_neg_a025", shift=-0.05)]

        out_new = os.path.join(root, "new.json")
        with pytest.raises(SystemExit) as ei:
            _run(fixed_module, base, arms, out_new)
        assert "no DONE.json" in str(ei.value)
        assert not os.path.exists(out_new)

        # pre-fix: the missing DONE.json raised nothing; it died later, on the T2 KeyError,
        # i.e. the truncated arm was loaded and scored without complaint.
        with pytest.raises(KeyError):
            _run(prefix_module, base, arms, os.path.join(root, "old.json"))
