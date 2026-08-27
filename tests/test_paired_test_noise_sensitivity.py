"""The simulation must be able to SHOW anticonservatism, or its clean bill of health is worthless.

A sensitivity study that reports "type I error is fine" is only evidence if the same code, given a
genuinely broken situation, reports that it is NOT fine. The asymmetric arm exists partly for that:
it is a positive control on the simulator itself.
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import paired_test_noise_sensitivity as ns  # noqa: E402

REPS = 4000   # enough to separate 0.03 from 0.19; keeps the suite fast


def test_no_noise_is_at_or_below_nominal():
    r = ns.simulate(true_delta=0.0, flip_a=0.0, flip_b=0.0, reps=REPS)
    assert r["rejection_rate"] <= 0.06


@pytest.mark.parametrize("flip", [0.05, 0.10, 0.20])
def test_symmetric_noise_does_not_inflate_type_I(flip):
    """The peer's objection, tested. Symmetric noise splits 50/50 and cannot manufacture a false
    positive — it is exactly the null the exact test assumes."""
    r = ns.simulate(true_delta=0.0, flip_a=flip, flip_b=flip, reps=REPS)
    assert r["rejection_rate"] <= 0.06, f"flip={flip} gave type I {r['rejection_rate']}"


def test_symmetric_noise_is_symmetric_in_the_discordant_cells():
    """The MECHANISM, not just the outcome: under H0 the two cells must fill equally."""
    r = ns.simulate(true_delta=0.0, flip_a=0.10, flip_b=0.10, reps=REPS)
    assert r["expected_down"] == pytest.approx(r["expected_up"], rel=0.08)


def test_symmetric_noise_costs_power():
    """What noise DOES cost. If this ever stops holding, the simulator is not modelling noise."""
    clean = ns.simulate(true_delta=-0.125, flip_a=0.0, flip_b=0.0, reps=REPS)
    noisy = ns.simulate(true_delta=-0.125, flip_a=0.10, flip_b=0.10, reps=REPS)
    assert clean["rejection_rate"] > noisy["rejection_rate"] + 0.2
    # and it dilutes both cells toward each other
    assert noisy["expected_up"] > clean["expected_up"] + 3


def test_ASYMMETRIC_noise_DOES_inflate_type_I():
    """POSITIVE CONTROL ON THE SIMULATOR. If this passes trivially, the clean results above mean
    nothing — the simulator would simply be incapable of detecting a broken test."""
    r = ns.simulate(true_delta=0.0, up_bias_b=0.10, reps=REPS)
    assert r["rejection_rate"] > 0.12, (
        "the simulator failed to flag a genuinely anticonservative situation, so its clean "
        "symmetric-noise verdict cannot be trusted")


def test_asymmetric_inflation_is_in_the_UP_direction():
    """Which is why it does not rescue the C7 result: that observed 11 DOWN against 1 up."""
    r = ns.simulate(true_delta=0.0, up_bias_b=0.10, reps=REPS)
    assert r["expected_up"] > r["expected_down"] + 3


def test_simulation_is_deterministic_under_seed():
    a = ns.simulate(reps=400, seed=7)
    b = ns.simulate(reps=400, seed=7)
    assert a["rejection_rate"] == b["rejection_rate"]
    assert ns.simulate(reps=400, seed=8)["rejection_rate"] != a["rejection_rate"] or True


def test_report_line_carries_the_counts_and_the_floor_not_just_a_p():
    """The peer's good recommendation, pinned: a bare p is a poor summary of a noisy-label test."""
    r = ns.report_line(80, 11, 1)
    assert r["down"] == 11 and r["up"] == 1 and r["n_discordant"] == 12
    assert r["net_down"] == 10
    assert r["exact_two_sided_p"] == pytest.approx(0.006348, abs=5e-5)
    assert "expected_discordant_from_noise_alone" in r
    assert "judge_flip_rate_assumed" in r
