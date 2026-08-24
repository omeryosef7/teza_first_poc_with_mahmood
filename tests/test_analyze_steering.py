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


# The 2026-08-20 TOPICALITY GATE (R-13) reads `summary.json["goal_topicality"]` from every arm's
# run directory and treats a MISSING assessment as fatal -- "not assessed is not the same as
# passed", the same lesson the coherence gate above it had to learn. This fixture was written
# 2026-08-18 and emitted no `summary.json` at all, so every arm it built looked unassessed and the
# fixed module exited before the JSON write that T2 exists to check.
#
# THE GATE IS CORRECT AND IS NOT TOUCHED. The FIXTURE is what was out of date: a synthetic arm that
# declines to say whether its generations were on topic is exactly the input the gate must refuse.
# `_make_run` now writes the summary the real judge writes (scalar fields only), so T2 clears the
# gate ON THE MERITS rather than by passing --allow-missing-topicality, and
# `test_T3_the_topicality_gate_is_still_fatal_when_the_assessment_is_absent` keeps the refusal path
# under test by building an arm that omits it.
_SENTINEL = object()


def _topicality_summary(median: float = 0.5, n_applicable: int = 60, frac_zero: float = 0.0):
    """The shape `judge_boombness._topicality_summary` writes. Scalars only, no prompt text."""
    return {"n_applicable": n_applicable, "median": median, "mean": median,
            "frac_zero": frac_zero}


def _make_run(root: str, tag: str, *, done: bool = True, shift: float = 0.0, n: int = 60,
              topicality=_SENTINEL):
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
    # `topicality=None` means "this run wrote no assessment", i.e. a pre-R-13 judge run: no
    # summary.json is written at all, which is the case the gate must refuse.
    t = _topicality_summary() if topicality is _SENTINEL else topicality
    if t is not None:
        with open(os.path.join(d, "summary.json"), "w") as f:
            json.dump({"goal_topicality": t}, f)
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
        # ...and the run got past the R-13 topicality gate because it was ASSESSED, not because
        # the gate was waived: no --allow-missing-topicality is passed anywhere in _run.
        for r in rep["rows"]:
            assert r["topicality"] is not None, r["arm"]


def test_T3_the_topicality_gate_is_still_fatal_when_the_assessment_is_absent(fixed_module):
    """R-13, 2026-08-20. The fixture above now SATISFIES this gate, so the gate itself needs its
    own case or the fixture repair would have silently disarmed it: an arm whose run wrote no
    `goal_topicality` must stop the report, and must not write JSON. Absent is not pass."""
    with tempfile.TemporaryDirectory() as root:
        base = _make_run(root, "base")
        arms = [_make_run(root, "steer_a025", shift=-0.1, topicality=None),
                _make_run(root, "steer_neg_a025", shift=-0.05)]
        out = os.path.join(root, "new.json")
        with pytest.raises(SystemExit) as ei:
            _run(fixed_module, base, arms, out)
        assert "goal-topicality" in str(ei.value) and "steer_a025" in str(ei.value)
        assert not os.path.exists(out)
        # and the documented override still works, so the gate is a refusal-by-default, not a wall
        assert _run(fixed_module, base, arms, out, extra=("--allow-missing-topicality",)) == 0
        assert os.path.exists(out)


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
