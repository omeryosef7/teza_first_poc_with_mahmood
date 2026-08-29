"""Guard tests for `paired_equivalence`. RBD sprint, 2026-08-29.

§22 says the point of independent verification is "to detect the same bug twice, not reproduce it
twice", so the central test here does NOT re-derive Newcombe's algebra -- retyping the formula would
reproduce a transcription error rather than catch it. Instead the interval is checked by
**Monte-Carlo coverage**: simulate paired binary data at a known true delta and confirm the nominal
95% interval covers it about 95% of the time. A mis-transcribed interval fails coverage; a correctly
transcribed one passes regardless of whether the test author can do the algebra.

The property the module exists to enforce is pinned explicitly in
`test_a_large_mcnemar_p_does_NOT_make_it_equivalent`: that is the failure mode
(`"equivalent_within_margin": gap <= MARGIN`) this module replaces.
"""
from __future__ import annotations

import math
import os
import random
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import paired_equivalence as pe  # noqa: E402


def _pairs(n11, n10, n01, n00, clusters=1):
    rows = []
    spec = [(1, 1)] * n11 + [(1, 0)] * n10 + [(0, 1)] * n01 + [(0, 0)] * n00
    for i, (b, a) in enumerate(spec):
        rows.append({"base": b, "arm": a, "domain": f"d{i % clusters}"})
    return rows


# --------------------------------------------------------------------------- #
# 1. Normal quantile and Wilson
# --------------------------------------------------------------------------- #
def test_z_matches_the_standard_values():
    assert pe._z(0.05) == pytest.approx(1.959963985, abs=1e-6)
    assert pe._z(0.10) == pytest.approx(1.644853627, abs=1e-6)
    assert pe._z(0.01) == pytest.approx(2.575829304, abs=1e-6)


def test_wilson_is_defined_at_the_boundaries_where_wald_is_not():
    lo, hi = pe.wilson(0, 48)
    assert lo == 0.0 and 0.0 < hi < 0.15
    lo, hi = pe.wilson(48, 48)
    assert hi == 1.0 and 0.85 < lo < 1.0


def test_wilson_contains_the_point_estimate_and_narrows_with_n():
    for n in (10, 100, 1000):
        lo, hi = pe.wilson(n // 2, n)
        assert lo < 0.5 < hi
    w = [pe.wilson(n // 2, n)[1] - pe.wilson(n // 2, n)[0] for n in (10, 100, 1000)]
    assert w[0] > w[1] > w[2]


# --------------------------------------------------------------------------- #
# 2. Newcombe arithmetic and symmetry
# --------------------------------------------------------------------------- #
def test_delta_arithmetic():
    r = pe.newcombe_paired_ci(n11=40, n10=5, n01=1, n00=2)
    assert r["n"] == 48
    assert r["p_base"] == pytest.approx(45 / 48)
    assert r["p_arm"] == pytest.approx(41 / 48)
    assert r["delta"] == pytest.approx((1 - 5) / 48)
    assert r["lo"] < r["delta"] < r["hi"]


def test_swapping_the_arms_flips_the_interval():
    a = pe.newcombe_paired_ci(40, 5, 1, 2)
    b = pe.newcombe_paired_ci(40, 1, 5, 2)   # n10 and n01 exchanged
    assert b["delta"] == pytest.approx(-a["delta"])
    assert b["lo"] == pytest.approx(-a["hi"], abs=1e-12)
    assert b["hi"] == pytest.approx(-a["lo"], abs=1e-12)


def test_zero_discordance_gives_a_zero_delta_and_a_finite_interval():
    r = pe.newcombe_paired_ci(45, 0, 0, 3)
    assert r["delta"] == 0.0
    assert r["lo"] < 0.0 < r["hi"]


def test_the_degenerate_margin_uses_phi_zero_rather_than_dividing_by_zero():
    """48/48 under both arms is a REAL observed cell in this project."""
    r = pe.newcombe_paired_ci(48, 0, 0, 0)
    assert r["phi"] == 0.0
    assert math.isfinite(r["lo"]) and math.isfinite(r["hi"])


def test_more_loss_moves_the_lower_bound_down():
    los = [pe.newcombe_paired_ci(48 - k, k, 0, 0)["lo"] for k in (0, 2, 5, 10)]
    assert los == sorted(los, reverse=True), los


# --------------------------------------------------------------------------- #
# 3. INDEPENDENT VERIFICATION: Monte-Carlo coverage (does not re-derive the formula)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("p_base,p_flip_down,p_flip_up", [
    (0.90, 0.05, 0.05),   # true delta 0
    (0.90, 0.10, 0.02),   # true delta negative
    (0.60, 0.05, 0.15),   # true delta positive
])
def test_newcombe_coverage_is_about_95_percent(p_base, p_flip_down, p_flip_up):
    rng = random.Random(20260829)
    n, reps = 60, 1500
    covered = 0
    for _ in range(reps):
        n11 = n10 = n01 = n00 = 0
        for _ in range(n):
            b = 1 if rng.random() < p_base else 0
            if b == 1:
                a = 0 if rng.random() < p_flip_down else 1
            else:
                a = 1 if rng.random() < p_flip_up else 0
            if b and a:
                n11 += 1
            elif b and not a:
                n10 += 1
            elif not b and a:
                n01 += 1
            else:
                n00 += 1
        true_delta = (p_base * (1 - p_flip_down) + (1 - p_base) * p_flip_up) - p_base
        r = pe.newcombe_paired_ci(n11, n10, n01, n00)
        if r["lo"] <= true_delta <= r["hi"]:
            covered += 1
    cov = covered / reps
    # Newcombe is designed to be conservative; it must not UNDER-cover, and must not be vacuous.
    assert 0.93 <= cov <= 0.999, f"coverage {cov:.3f} at delta={true_delta:+.4f}"


def test_the_coverage_test_can_fail():
    """Anti-vacuity: a deliberately too-narrow interval must NOT reach 95% coverage."""
    rng = random.Random(7)
    n, reps, covered = 60, 800, 0
    for _ in range(reps):
        n11 = n10 = n01 = n00 = 0
        for _ in range(n):
            b = 1 if rng.random() < 0.9 else 0
            a = 0 if (b and rng.random() < 0.05) else (1 if b else (1 if rng.random() < 0.05 else 0))
            if b and a:
                n11 += 1
            elif b and not a:
                n10 += 1
            elif not b and a:
                n01 += 1
            else:
                n00 += 1
        r = pe.newcombe_paired_ci(n11, n10, n01, n00)
        d, mid = (r["hi"] - r["lo"]) / 2.0, r["delta"]
        narrow_lo, narrow_hi = mid - d * 0.2, mid + d * 0.2   # 5x too narrow
        if narrow_lo <= 0.0 <= narrow_hi:
            covered += 1
    assert covered / reps < 0.90, "a 5x-too-narrow interval still covered -- test is vacuous"


# --------------------------------------------------------------------------- #
# 4. McNemar exact, on hand-computable cases
# --------------------------------------------------------------------------- #
def test_mcnemar_exact_hand_cases():
    assert pe.mcnemar_exact(0, 0) == 1.0
    assert pe.mcnemar_exact(5, 0) == pytest.approx(2 * 1 / 32)      # 2*C(5,0)/2^5
    assert pe.mcnemar_exact(4, 1) == pytest.approx(2 * (1 + 5) / 32)  # 2*(C(5,0)+C(5,1))/2^5
    assert pe.mcnemar_exact(3, 3) == 1.0
    assert pe.mcnemar_exact(1, 5) == pe.mcnemar_exact(5, 1)


# --------------------------------------------------------------------------- #
# 5. THE POINT OF THE MODULE
# --------------------------------------------------------------------------- #
def test_a_large_mcnemar_p_does_NOT_make_it_equivalent():
    """8 pairs, zero discordance: p = 1.0, and equivalence is still UNRESOLVABLE.

    This is the exact inference the module replaces -- "we did not detect a difference, therefore
    there is none". At n=8 no outcome could establish equivalence at a 0.10 margin.
    """
    v = pe.paired_equivalence(_pairs(7, 0, 0, 1), margin=0.10)
    assert v["mcnemar_p_two_sided"] == 1.0
    assert v["can_establish_equivalence"] is False
    assert v["VERDICT"] == "UNRESOLVABLE_AT_THIS_N"
    assert v["VERDICT"] != "EQUIVALENT"


def test_capability_is_reported_before_the_verdict_can_be_positive():
    small = pe.paired_equivalence(_pairs(20, 0, 0, 0), margin=0.10)
    big = pe.paired_equivalence(_pairs(400, 0, 0, 0), margin=0.10)
    assert small["can_establish_equivalence"] is False
    assert big["can_establish_equivalence"] is True
    assert big["VERDICT"] == "EQUIVALENT"


def test_a_real_drop_is_not_called_equivalent():
    v = pe.paired_equivalence(_pairs(200, 100, 0, 100), margin=0.10)
    assert v["delta"] < -0.10
    assert v["VERDICT"] == "WORSE_THAN_MARGIN"


def test_a_point_estimate_inside_the_margin_with_a_crossing_interval_does_not_pass():
    """delta is inside the margin, but the interval is not. This must NOT read as equivalent."""
    v = pe.paired_equivalence(_pairs(80, 6, 2, 12), margin=0.10)
    assert -0.10 < v["delta"] < 0.0
    assert v["binding_lo"] < -0.10
    assert v["VERDICT"] == "NOT_ESTABLISHED"


# --------------------------------------------------------------------------- #
# 6. Conservatism of the binding interval, and clustering
# --------------------------------------------------------------------------- #
def test_the_binding_bound_is_the_MOST_CONSERVATIVE_of_the_available_intervals():
    rows = _pairs(300, 20, 15, 65, clusters=6)
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=600)
    assert v["cluster_bootstrap"] is not None
    assert v["binding_lo"] == min(v["newcombe"]["lo"], v["cluster_bootstrap"]["lo"])
    assert v["binding_interval"] in ("newcombe", "cluster_bootstrap")


def test_cluster_bootstrap_reports_its_own_k():
    rows = _pairs(100, 10, 10, 40, clusters=5)
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=400)
    assert v["n_clusters"] == 5
    assert v["cluster_bootstrap"]["n_rows"] == 160


def test_bootstrap_is_deterministic_under_a_fixed_seed():
    rows = _pairs(100, 10, 10, 40, clusters=5)
    a = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"],
                              n_boot=400, seed=1)
    b = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"],
                              n_boot=400, seed=1)
    assert a["binding_lo"] == b["binding_lo"]


# --------------------------------------------------------------------------- #
# 7. Refusals
# --------------------------------------------------------------------------- #
def test_REFUSES_a_non_positive_margin():
    with pytest.raises(ValueError):
        pe.paired_equivalence(_pairs(10, 0, 0, 0), margin=0.0)
    with pytest.raises(ValueError):
        pe.paired_equivalence(_pairs(10, 0, 0, 0), margin=-0.1)


def test_REFUSES_a_non_binary_outcome():
    rows = _pairs(5, 0, 0, 0)
    rows[0]["arm"] = 0.5
    with pytest.raises(ValueError) as e:
        pe.paired_equivalence(rows, margin=0.10)
    assert "not 0 or 1" in str(e.value)


def test_REFUSES_an_empty_population():
    with pytest.raises(ValueError):
        pe.paired_equivalence([], margin=0.10)
    with pytest.raises(ValueError):
        pe.newcombe_paired_ci(0, 0, 0, 0)


def test_summary_names_the_capability_and_the_binding_interval():
    v = pe.paired_equivalence(_pairs(400, 0, 0, 0), margin=0.10)
    s = v.summary()
    assert "EQUIVALENT" in s and "capable=True" in s and "newcombe" in s
