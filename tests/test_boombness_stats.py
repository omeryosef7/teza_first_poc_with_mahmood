"""Regression tests for the sprint's statistical primitives.

STANDING RULE (project): a guard that has never been tested against a case it should fail is not a
guard. Each test below is written so that it FAILS against the code as it stood before its fix, and
the header of each records the exact pre-fix value it would have produced.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))

from scipy import stats as _sp  # the reference; analysis env has it, login shell does not

import analyze_g8


def test_t_sf_matches_scipy_including_the_small_t_region():
    """External critique finding 4. Pre-fix, t_sf(0.01138, 5) = 0.76548 against a truth of 0.99136 --
    the value published in g9_three_predictor_lastpos.json. Error is always anticonservative."""
    for df in (2, 3, 4, 5, 9, 30, 100):
        for t in (0.0, 1e-6, 1e-4, 0.01138, 0.05, 0.08, 0.2, 0.5, 1.0, 1.464, 1.69, 2.0, 3.0, 8.0):
            got = analyze_g8.t_sf(t, df)
            want = 2.0 * _sp.t.sf(abs(t), df)
            assert abs(got - want) <= 1e-10 + 1e-9 * want, (t, df, got, want)


def test_t_sf_never_below_the_normal_reference():
    """The impossibility that exposed the bug from the artifact alone: t has heavier tails than the
    normal, so p_t >= p_normal for every t. The published pair 0.7656 < 0.9909 violated this."""
    for df in (2, 5, 9, 30):
        for i in range(400):
            t = i * 0.02
            p_t = analyze_g8.t_sf(t, df)
            p_n = math.erfc(abs(t) / math.sqrt(2.0))
            assert p_t >= p_n - 1e-12, (t, df, p_t, p_n)


def test_betainc_fallback_is_correct_without_scipy():
    """The fallback is what runs if scipy is ever absent, so it gets the same bar, not a weaker one.
    Pre-fix the fallback lacked the I_x(a,b) = 1 - I_{1-x}(b,a) transform."""
    for df in (2, 3, 5, 9, 30):
        for t in (1e-4, 0.01138, 0.08, 0.5, 1.5, 3.0):
            x = df / (df + t * t)
            got = analyze_g8._betainc(df / 2.0, 0.5, x)
            want = 2.0 * _sp.t.sf(abs(t), df)
            assert abs(got - want) <= 1e-9 * max(want, 1e-12) + 1e-12, (t, df, got, want)


def test_t_crit_matches_scipy():
    """Pre-fix this was hardcoded with a NORMAL 2.0 fallback for any df outside {5, 4}."""
    for df in (1, 2, 3, 4, 5, 9, 30, 120):
        assert abs(analyze_g8.t_crit(df) - _sp.t.ppf(0.975, df)) < 1e-9, df
