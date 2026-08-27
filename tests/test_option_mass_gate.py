"""The option-mass gate must read the TRUE median, not the upper-middle element.

`v[len(v)//2]` is >= the true median by construction, so a gate built on it is biased TOWARD
PASSING. Every historical BELOW-GATE verdict is therefore safe a fortiori; the exposure was always
near-threshold PASSes. Measured on p5A_main (semantic_one_word, n=96): v[48] = 0.042891 against a
true median of 0.040421 — a 6% upward bias on a threshold statistic.

`median` is deliberately NOT changed: it appears in every historical summary.json and mutating it
would move published values retroactively. These tests pin both halves — the old field survives, and
the gate stops using it.
"""

from __future__ import annotations

import os
import re
import statistics

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "score_behavior.py")


def _src():
    return open(SRC).read()


def test_the_gate_reads_median_true_not_the_upper_middle():
    s = _src()
    assert '"reportable": med_true >= args.min_option_mass' in s, \
        "the gate must be computed from the true median"
    assert '"reportable": med >= args.min_option_mass' not in s, \
        "the upper-middle gate is still present"


def test_the_published_median_field_is_preserved():
    """Mutating `median` would move every historical summary.json's reported value."""
    s = _src()
    assert '"median": med,' in s
    assert "med = v[len(v) // 2]" in s, "the upper-middle computation must survive for continuity"


def test_median_true_is_emitted_alongside():
    s = _src()
    assert '"median_true": med_true' in s
    assert "med_true = statistics.median(v)" in s
    assert "median_note" in s, "the two fields must carry an explanation of which is which"


def test_upper_middle_is_never_below_the_true_median():
    """The asymmetry that makes every historical BELOW verdict safe a fortiori."""
    for vals in ([0.01, 0.02], [0.01, 0.02, 0.03], [0.0, 0.04, 0.05, 0.9],
                 [0.1] * 7, [0.001, 0.049, 0.051, 0.99]):
        v = sorted(vals)
        assert v[len(v) // 2] >= statistics.median(v)


def test_the_bias_can_change_a_verdict_at_the_boundary():
    """A concrete case the OLD gate would have wrongly passed — which is why this was worth fixing
    even though 0 verdicts flip on today's corpus."""
    v = sorted([0.01, 0.049, 0.051, 0.9])
    assert statistics.median(v) == 0.05                # true median exactly at the floor
    assert v[len(v) // 2] == 0.051                     # upper-middle above it
    v2 = sorted([0.01, 0.048, 0.051, 0.9])
    assert statistics.median(v2) < 0.05 <= v2[len(v2) // 2]   # true FAILS, upper-middle PASSES


def test_statistics_is_imported():
    assert re.search(r"^import statistics$", _src(), re.M)
