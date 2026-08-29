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
def test_the_envelope_takes_BOTH_bounds_in_the_conservative_direction():
    rows = _pairs(300, 20, 15, 65, clusters=6)
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=600)
    assert v["cluster_bootstrap"] is not None
    assert v["binding_lo"] == min(i["lo"] for i in v["intervals"].values())
    assert v["binding_hi"] == max(i["hi"] for i in v["intervals"].values())


def test_cluster_bootstrap_reports_its_own_k():
    rows = _pairs(100, 10, 10, 40, clusters=5)
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=400)
    assert v["n_clusters"] == 5
    assert v["cluster_bootstrap"]["n_rows"] == 160


def _heterogeneous(clusters=6):
    """Clusters with DIFFERENT compositions, so the bootstrap actually has something to resample.

    `_pairs(..., clusters=k)` assigns d{i%k} over a spec list sorted by cell type, which gives
    every cluster an identical composition and a bootstrap CI of width exactly 0.0 -- a test built
    on it cannot detect a seed bug, or any bootstrap bug at all.
    """
    rows = []
    comps = [(20, 0, 0, 0), (5, 10, 0, 5), (18, 1, 1, 0), (2, 12, 4, 2),
             (15, 2, 3, 0), (0, 15, 5, 0)][:clusters]
    for di, (a, b, c, d) in enumerate(comps):
        for x, y in [(1, 1)] * a + [(1, 0)] * b + [(0, 1)] * c + [(0, 0)] * d:
            rows.append({"base": x, "arm": y, "domain": f"d{di}"})
    return rows


def test_the_cluster_bootstrap_is_actually_EXERCISED_by_these_fixtures():
    """Anti-vacuity: a zero-width bootstrap makes every bootstrap test meaningless."""
    rows = _heterogeneous()
    cl = pe.cluster_bootstrap_delta_ci(rows, lambda r: r["domain"], n_boot=800, seed=3)
    assert cl["hi"] - cl["lo"] > 0.02, f"bootstrap width {cl['hi'] - cl['lo']} is degenerate"
    assert cl["n_clusters"] == 6


def test_bootstrap_is_deterministic_under_a_fixed_seed_AND_varies_without_one():
    """Asserts on the BOOTSTRAP's own bounds, not on binding_lo.

    The previous version asserted `binding_lo`, which on its fixture was always Newcombe's -- so
    no bootstrap output was ever compared and a fresh random seed on every call left it passing.
    """
    rows = _heterogeneous()
    a = pe.cluster_bootstrap_delta_ci(rows, lambda r: r["domain"], n_boot=500, seed=1)
    b = pe.cluster_bootstrap_delta_ci(rows, lambda r: r["domain"], n_boot=500, seed=1)
    c = pe.cluster_bootstrap_delta_ci(rows, lambda r: r["domain"], n_boot=500, seed=2)
    assert (a["lo"], a["hi"]) == (b["lo"], b["hi"])
    assert (a["lo"], a["hi"]) != (c["lo"], c["hi"]), "different seeds gave identical draws"


def test_the_bootstrap_can_be_the_BINDING_interval():
    """The min()/max() selection through the bootstrap branch must be exercised."""
    rows = _heterogeneous()
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=800)
    assert "cluster_bootstrap" in v["intervals"]
    assert v["binding_lo_from"] in ("newcombe", "cluster_bootstrap")
    assert v["binding_hi_from"] in ("newcombe", "cluster_bootstrap")
    assert v["binding_lo"] <= v["intervals"]["cluster_bootstrap"]["lo"]
    assert v["binding_hi"] >= v["intervals"]["cluster_bootstrap"]["hi"]


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


def test_summary_names_the_capability_and_where_each_bound_came_from():
    v = pe.paired_equivalence(_pairs(400, 0, 0, 0), margin=0.10)
    s = v.summary()
    assert "EQUIVALENT" in s and "capable=True" in s and "lo from newcombe" in s and "3/n=" in s


# --------------------------------------------------------------------------- #
# 8. Regressions for the 2026-08-29 deep review (RBD-DR-002)
# --------------------------------------------------------------------------- #
def test_a_DECISIVE_negative_is_reported_even_when_equivalence_was_unattainable():
    """delta = -1.0 at p = 0.0078 was reported as UNRESOLVABLE_AT_THIS_N.

    "Could equivalence have been established?" and "was a difference established?" are
    orthogonal; gating the second on the first discards a decisive result.
    """
    v = pe.paired_equivalence(_pairs(0, 8, 0, 0), margin=0.10)
    assert v["delta"] == -1.0
    assert v["can_establish_equivalence"] is False
    assert v["VERDICT"] == "WORSE_THAN_MARGIN"
    assert v["mcnemar_p_two_sided"] < 0.01


@pytest.mark.parametrize("n,expect_can", [(8, False), (20, False), (30, False),
                                          (40, True), (160, True), (400, True)])
def test_capability_is_a_function_of_n_ALONE(n, expect_can):
    """It must not swing on the observed cell pattern.

    The first version evaluated Newcombe at zero discordance with the OBSERVED marginals, which
    sits at phi = 1 whenever n00 > 0: n=20 with n00=4 read CAPABLE while n=20 with n00=0 read
    incapable. Rule of three, 3/n < margin, is a property of the design.
    """
    for n00 in (0, n // 4, n // 2):
        v = pe.paired_equivalence(_pairs(n - n00, 0, 0, n00), margin=0.10)
        assert v["can_establish_equivalence"] is expect_can, (n, n00, v["rule_of_three_bound"])
        assert v["rule_of_three_bound"] == pytest.approx(3.0 / n)


def test_mcnemar_does_not_overflow_on_large_discordance():
    """2.0 ** m overflows at m ~ 1024, and so does 2.0 * tail for an exact integer tail."""
    assert pe.mcnemar_exact(600, 600) == pytest.approx(1.0)
    assert 0.0 <= pe.mcnemar_exact(1200, 0) <= 1.0
    assert pe.mcnemar_exact(5, 0) == pytest.approx(0.0625)


def test_mcnemar_REFUSES_negative_counts():
    with pytest.raises(ValueError):
        pe.mcnemar_exact(-1, 3)


def test_the_envelope_prevents_a_WORSE_verdict_that_a_cluster_interval_contradicts():
    """Reading `hi` off the lo-winning interval let WORSE_THAN_MARGIN fire while the
    cluster-respecting interval still contained zero."""
    rows = []
    for di, (a, b, c, d) in enumerate([(5, 20, 3, 25), (16, 25, 8, 8), (0, 12, 12, 6)]):
        for x, y in [(1, 1)] * a + [(1, 0)] * b + [(0, 1)] * c + [(0, 0)] * d:
            rows.append({"base": x, "arm": y, "domain": f"d{di}"})
    v = pe.paired_equivalence(rows, margin=0.10, cluster_key=lambda r: r["domain"], n_boot=2000)
    assert v["intervals"]["cluster_bootstrap"]["hi"] >= 0.0
    assert v["binding_hi"] >= 0.0
    assert v["VERDICT"] != "WORSE_THAN_MARGIN"


@pytest.mark.parametrize("p_base,p_flip_down,p_flip_up,n", [(0.98, 0.01, 0.01, 48),
                                                            (0.50, 0.02, 0.02, 20)])
def test_coverage_ALSO_holds_in_the_near_ceiling_regime(p_base, p_flip_down, p_flip_up, n):
    """The module's stated regime is 45/48 and 48/48; the original coverage cells never sampled
    it, so a collapse there would have escaped."""
    rng = random.Random(4242)
    reps, covered = 800, 0
    for _ in range(reps):
        n11 = n10 = n01 = n00 = 0
        for _ in range(n):
            b = 1 if rng.random() < p_base else 0
            a = (0 if rng.random() < p_flip_down else 1) if b else \
                (1 if rng.random() < p_flip_up else 0)
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
    assert covered / reps >= 0.93, f"coverage {covered / reps:.3f} in the near-ceiling regime"
