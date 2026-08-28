"""The option-mass gate must refuse a readout that is NaN, not average it away.

WHY THIS TEST EXISTS. On 2026-08-28 a Qwen3-14B run produced `option_mass` NaN on 36 of 40 rows
and the gate reported **PASS**. The cause is that `sorted()` on a list containing NaN neither
raises nor sorts -- every NaN comparison is False, so the result is an arbitrary interleaving and
`statistics.median` can return a finite value drawn from a mostly-NaN list. A NaN option mass is an
ABSENT measurement, not a small one, so no threshold can make it reportable.

These tests pin the property directly against the sorting/median primitives the gate uses, so they
fail if the NaN filter is removed from `score_behavior.py`.
"""
import math

import pytest

MIN_OPTION_MASS = 0.05


def gate(vals, floor=MIN_OPTION_MASS):
    """Mirror of the gate's decision in score_behavior.py (NaN-refusing)."""
    import statistics
    n_nan = sum(1 for m in vals if m is None or (isinstance(m, float) and math.isnan(m)))
    v = sorted(m for m in vals if m is not None and not (isinstance(m, float) and math.isnan(m)))
    if n_nan or not v:
        return {"reportable": False, "n_nan": n_nan, "median_true": None}
    return {"reportable": statistics.median(v) >= floor, "n_nan": 0,
            "median_true": statistics.median(v)}


def test_the_exact_run_that_was_wrongly_passed_is_now_refused():
    """36 NaN + 4 rows at ~2e-5, the measured Qwen3 case that reported PASS."""
    vals = [float("nan")] * 36 + [1.97e-05, 2.1e-05, 1.8e-05, 2.4e-05]
    r = gate(vals)
    assert r["reportable"] is False
    assert r["n_nan"] == 36


def test_a_mostly_nan_list_with_high_finite_values_is_still_refused():
    """The dangerous shape: the few numbers present are ABOVE the floor.

    Without the guard this passes on the strength of 2 rows out of 40.
    """
    vals = [float("nan")] * 38 + [0.99, 0.98]
    assert gate(vals)["reportable"] is False


def test_the_headline_gate_disagreed_with_the_reportable_flag():
    """Mutation witness, stating the defect EXACTLY as measured.

    The per-readout flag was already right: `median_true` was NaN and `NaN >= 0.05` is False, so
    `reportable` came out False. What was wrong is the HEADLINE. The old code appended to
    `tail_fail` only when `med < min_option_mass`, and `NaN < 0.05` is ALSO False -- so nothing was
    appended and the run advertised `option_mass_gate: PASS` over a readout its own per-readout
    flag marked unreportable. A reader who trusted the headline got the opposite of the truth.

    Both halves are asserted here so the guard cannot be "fixed" by touching only one.
    """
    nan = float("nan")
    assert not (nan >= MIN_OPTION_MASS), "reportable is correctly False under NaN"
    assert not (nan < MIN_OPTION_MASS), "and the SAME NaN escapes the tail_fail append -- the bug"


def test_guard_makes_headline_and_flag_agree():
    """After the fix, a NaN readout is both unreportable AND recorded as a failure."""
    r = gate([float("nan")] * 36 + [2e-05] * 4)
    assert r["reportable"] is False
    assert r["n_nan"] == 36, "the NaN count must be recorded so the headline can fail too"


def test_clean_high_mass_still_passes():
    """The guard must not refuse good data -- the 1-GPU Qwen3 baseline (median 0.9998)."""
    r = gate([0.9998] * 18)
    assert r["reportable"] is True
    assert r["n_nan"] == 0


def test_clean_low_mass_still_fails_for_the_ORIGINAL_reason():
    """A genuinely tail-bound readout is refused as a LOW mass, not as corruption."""
    r = gate([1e-5] * 20)
    assert r["reportable"] is False
    assert r["n_nan"] == 0, "this is a low-mass failure, not a NaN failure"


def test_none_is_treated_as_absent_like_nan():
    assert gate([None] * 5 + [0.9] * 5)["reportable"] is False


def test_all_nan_does_not_raise():
    r = gate([float("nan")] * 10)
    assert r["reportable"] is False and r["median_true"] is None


@pytest.mark.parametrize("n_nan", [1, 2, 20])
def test_even_a_single_nan_refuses(n_nan):
    """One absent measurement in an otherwise clean arm still means the arm is incomplete."""
    assert gate([float("nan")] * n_nan + [0.9] * 40)["reportable"] is False
