"""C6 and C7's script: cell sizes, both metrics, and the match ratio must always travel.

A manifest-coverage audit on 2026-08-26 found C6 (the refusal dose-response) and C7
(demonstration-specificity at n_examples=2) had NO reproduction command -- both were computed in a
shell heredoc. These tests pin the script that replaced them.
"""

from __future__ import annotations

import os

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "src", "boombness", "dose_breakdown.py")


def _src():
    return open(SRC).read()


def test_cell_size_and_margin_travel_per_dose():
    """At n=40 the margin is 2.1 rows; a per-dose number without its cell size is uninterpretable."""
    s = _src()
    assert '"margin_rows": round(marg, 2)' in s
    assert '"n": n,' in s
    assert '"CELL_SIZE_NOTE"' in s


def test_both_metrics_are_always_emitted():
    """C-12: ASR and refusal are separable, so an arm that moves one and not the other is the
    interesting case and must not be hidden by reporting only the one that moved."""
    s = _src()
    for k in ('"d_asr_rows"', '"d_refusal_rows"',
              '"d_asr_clears_margin"', '"d_refusal_clears_margin"'):
        assert k in s, k
    assert '"BOTH_METRICS_NOTE"' in s


def test_control_draw_match_ratio_is_carried():
    """R-24/R-26: an under-matched control showing no effect is an artifact of the under-matching."""
    s = _src()
    assert '"control_draw_match_ratio_min"' in s
    assert '"control_draw_match_ratio_mean"' in s


def test_monotonicity_is_reported_not_tested():
    """R-22 was refuted on Qwen3 by a pre-registered ENDPOINT rule, not by monotonicity."""
    s = _src()
    assert '"refusal_monotone_nondecreasing"' in s
    assert '"MONOTONICITY_NOTE"' in s and "NOT tested" in s


def test_margin_is_the_measured_one():
    assert "MARGIN_VS_BASELINE = 0.0521" in _src()
