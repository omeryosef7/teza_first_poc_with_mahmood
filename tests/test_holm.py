"""Holm family-size guard for reanalyze_corrected.py (audit T6c).

PRE-FIX BEHAVIOUR: `reanalyze_corrected.holm()` took only the p-values it was handed and set
m = len(pvals). `main()` handed it the ~10 layers from `--layers`, while the module docstring said
"32 layers were tested" and the emitted JSON recorded neither m nor the rule that chose it. Code and
prose disagreed, and the report leaned on the resulting `holm_rejected` flags ("True only at L4 and
L31") as its multiplicity backstop for claims about a mid band that had been selected by eye out of
all 32 available layers.

OBSERVABLE CONSEQUENCE: the family size is not recoverable from the artifact, and it changes
answers. On the committed d_surface|cos run, L4's p = 0.001631 clears alpha/9 = 0.005556 at m=10 and
fails alpha/31 = 0.001613 under the audit's m=32 reading, so a single undocumented default decides
whether the strongest mid-profile claim's anchor layer is significant at all.

These tests fail against HEAD:src/boombness/reanalyze_corrected.py -- `holm()` there has no `m`
parameter (TypeError) and there is no `holm_table` or `available_layers` at all.
"""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src", "boombness")
sys.path.insert(0, SRC)

import reanalyze_corrected as rc  # noqa: E402

# PRE-FIX BASELINE, PINNED (2026-08-18). These tests demonstrate the defect by loading the version
# of the module that had it. They originally used `git show HEAD:...`, which is self-invalidating:
# the moment the fix is committed, HEAD *contains* the fix and the "this must fail pre-fix"
# assertions stop holding. That turned three green tests red with no code regression -- a test that
# silently changes what it asserts as the branch moves is worse than no test. The baseline is now
# pinned to the commit that introduced the fix, minus one.
PREFIX_BASELINE = "a8251ffa~1"



# A synthetic p-vector with a hand-checked Holm answer at two family sizes.
#   sorted: 0.001, 0.004, 0.020, 0.300
#   m = 4 : thresholds .05/4=.0125, .05/3=.01667, .05/2=.025, .05/1=.05
#           -> .001<=.0125 rej; .004<=.01667 rej; .020<=.025 rej; .300>.05 stop  => A,B,C
#   m = 20: thresholds .05/20=.0025, .05/19=.002632, ...
#           -> .001<=.0025 rej; .004>.002632 stop                                 => A only
PV = {"A": 0.001, "B": 0.004, "C": 0.020, "D": 0.300}


def test_default_family_is_the_pvector_and_matches_hand_computation():
    assert rc.holm(PV) == {"A": True, "B": True, "C": True, "D": False}


def test_explicit_family_size_changes_the_answer():
    # The whole point of T6c: same p-values, different m, different conclusion.
    assert rc.holm(PV, m=4) == {"A": True, "B": True, "C": True, "D": False}
    assert rc.holm(PV, m=20) == {"A": True, "B": False, "C": False, "D": False}


def test_thresholds_and_ranks_are_recorded_not_just_the_decision():
    tab = rc.holm_table(PV, m=20)
    assert tab["A"]["rank"] == 1 and tab["B"]["rank"] == 2
    assert tab["A"]["thr"] == pytest.approx(0.05 / 20)
    assert tab["B"]["thr"] == pytest.approx(0.05 / 19)
    assert all(v["m"] == 20 for v in tab.values())


def test_step_down_stops_at_the_first_failure():
    # C would clear its own threshold at m=4 (.020 <= .025) but B must not block it; whereas at
    # m=20 B fails and C is barred even though .020 <= .05/18.
    tab = rc.holm_table(PV, m=20)
    assert tab["C"]["p"] <= tab["C"]["thr"] * 20      # C clears alpha/18 on its own ...
    assert rc.holm(PV, m=20)["C"] is False            # ... but B's failure bars it
    assert rc.holm(PV, m=4)["C"] is True


def test_family_smaller_than_the_pvector_is_refused():
    # m < len(pvals) is incoherent: you cannot test 4 hypotheses in a family of 2.
    with pytest.raises(ValueError):
        rc.holm(PV, m=2)


def test_available_layers_finds_every_layer_column_for_the_metric():
    rows = [{"d_surface|L0|cos": 0.1, "d_surface|L7|cos": 0.2, "d_surface|L7|proj": 9.0,
             "d_naive|L3|cos": 0.5, "domain": "x"},
            {"d_surface|L12|cos": 0.3}]
    assert rc.available_layers(rows, "d_surface", "cos") == [0, 7, 12]
    assert rc.available_layers(rows, "d_naive", "cos") == [3]


def test_prefix_holm_cannot_express_a_family_size():
    """Load HEAD's version and show it has no way to say m -- the defect, executed."""
    old = os.path.join(os.environ.get("TMPDIR", "/tmp"), "old_reanalyze_corrected_for_test.py")
    repo = os.path.dirname(HERE)
    with open(old, "w") as f:
        subprocess.run(["git", "show", f"{PREFIX_BASELINE}:src/boombness/reanalyze_corrected.py"],
                       cwd=repo, stdout=f, check=True)
    import importlib.util
    spec = importlib.util.spec_from_file_location("old_rc", old)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.holm(PV) == {"A": True, "B": True, "C": True, "D": False}
    with pytest.raises(TypeError):
        mod.holm(PV, m=20)          # pre-fix: family size is not expressible
    assert not hasattr(mod, "holm_table")
    assert not hasattr(mod, "available_layers")
