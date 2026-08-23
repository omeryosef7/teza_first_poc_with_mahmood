"""The two realized-dose formulas, checked against brute force rather than against the algebra.

WHY BOTH METRICS EXIST (correction C-2). `cellmean_dose` returns a VARIANCE (squared) fraction. At
alpha = 1 the norm metric is exactly its square root -- a monotone transform -- so every rank and
isotonic argument in this repo has been metric-invariant BY ACCIDENT. Partial alpha is the first
place that invariance breaks:

    variance removed = frac * (1 - (1-alpha)^2)   ~ 2*alpha for small alpha
    norm removed     = alpha * sqrt(frac)         ~ alpha

At L12 the two disagree by roughly an order of magnitude in alpha about which arm is "dose-matched"
to the in-subspace controls, so recording one and not the other silently picks a side of an open
question.

TWO QUESTIONS, DELIBERATELY SEPARATED. Conflating them is what made the first two drafts of this
file fail:

  (A) IS THE CLOSED FORM RIGHT? Pure algebra, tested in float64 against a direct application of the
      hook. Tolerance 1e-9. `cellmean_dose` is NOT used here -- it casts to float32 internally, so
      including it would cap this test's precision at ~1e-6 and hide a real algebra error inside
      float noise.
  (B) DOES cellmean_dose COMPUTE frac CORRECTLY? Tested separately, at float32 tolerance, which is
      the precision that function actually offers.

Draft 1 used float32 for (A) and failed at alpha=0.056/0.08 -- the brute force forms
||M||^2 - ||M_after||^2, two terms agreeing to ~5 significant figures, so the subtraction loses most
of its precision (7.5e-6 relative in float32, 3e-15 in float64). The TEST was wrong, not the
formula, and the obvious reading of that failure is the opposite one.

Run:  python -m pytest tests/test_realized_dose.py -q
"""
import math
import os
import sys

import pytest

torch = pytest.importorskip("torch")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))

ALPHAS = [0.03, 0.056, 0.06, 0.08, 0.1, 0.3, 0.38, 0.6, 1.0]


def _cells(seed=0, n_cells=4, dim=16, layer=12):
    g = torch.Generator().manual_seed(seed)
    cells = {f"c{i}": {layer: torch.randn(dim, generator=g, dtype=torch.float64)}
             for i in range(n_cells)}
    d = torch.randn(dim, generator=g, dtype=torch.float64)
    return {"cell_means": cells, "d_surface": {layer: d}}, d, layer


def _centred(payload, layer):
    cm = payload["cell_means"]
    M = torch.stack([cm[c][layer].double().reshape(-1) for c in sorted(cm)])
    return M - M.mean(dim=0, keepdim=True)


def _frac64(M, d):
    """The variance fraction, in float64 — the reference (A) is measured against."""
    u = (d.double().reshape(-1) / d.double().reshape(-1).norm()).reshape(-1, 1)
    return float(((M @ u) ** 2).sum()) / float((M ** 2).sum())


def _brute_force(M, d, alpha):
    """Apply the real hook algebra h -> h - alpha*(h.u)u to every cell mean, and measure."""
    u = (d.double().reshape(-1) / d.double().reshape(-1).norm()).reshape(-1, 1)
    removed = alpha * (M @ u) @ u.T
    M_after = M - removed
    var_frac = float((M ** 2).sum() - (M_after ** 2).sum()) / float((M ** 2).sum())
    norm_frac = float(removed.norm()) / float(M.norm())
    return var_frac, norm_frac


# --------------------------------------------------------------------------- #
# (A) the closed forms, pure float64
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("alpha", ALPHAS)
def test_variance_closed_form_matches_brute_force(alpha):
    payload, d, layer = _cells(seed=3)
    M = _centred(payload, layer)
    frac = _frac64(M, d)
    bf_var, _ = _brute_force(M, d, alpha)
    assert math.isclose(frac * (1 - (1 - alpha) ** 2), bf_var, rel_tol=1e-9), (
        f"frac*(1-(1-alpha)^2) disagrees with brute force at alpha={alpha}")


@pytest.mark.parametrize("alpha", ALPHAS)
def test_norm_closed_form_matches_brute_force(alpha):
    payload, d, layer = _cells(seed=5)
    M = _centred(payload, layer)
    frac = _frac64(M, d)
    _, bf_norm = _brute_force(M, d, alpha)
    assert math.isclose(alpha * math.sqrt(frac), bf_norm, rel_tol=1e-9), (
        f"alpha*sqrt(frac) disagrees with brute force at alpha={alpha}")


# --------------------------------------------------------------------------- #
# (B) cellmean_dose itself, at the precision it actually offers
# --------------------------------------------------------------------------- #
def test_cellmean_dose_agrees_with_the_float64_reference():
    from insubspace_null_test import cellmean_dose
    payload, d, layer = _cells(seed=3)
    M = _centred(payload, layer)
    assert math.isclose(cellmean_dose(payload, layer, d), _frac64(M, d), rel_tol=1e-5), (
        "cellmean_dose disagrees with a float64 recomputation by more than float32 noise")


# --------------------------------------------------------------------------- #
# C-2: the two metrics are not interchangeable below alpha=1
# --------------------------------------------------------------------------- #
def test_the_two_metrics_are_NOT_monotone_equivalent_at_partial_alpha():
    """THE POINT OF C-2. If this ever passes trivially, the ladder has stopped being informative."""
    payload, d, layer = _cells(seed=7)
    M = _centred(payload, layer)
    frac = _frac64(M, d)
    alphas = (0.05, 0.1, 0.3, 0.6, 1.0)
    ratios = [frac * (1 - (1 - a) ** 2) / (a * math.sqrt(frac)) for a in alphas]
    # var/norm = sqrt(frac)*(2-alpha), so the ratio DECREASES in alpha. An earlier draft asserted
    # the opposite direction; the algebra settled it, not the code.
    for a, r in zip(alphas, ratios):
        assert math.isclose(r, math.sqrt(frac) * (2 - a), rel_tol=1e-12)
    assert ratios == sorted(ratios, reverse=True), ratios
    assert ratios[0] > 1.5 * ratios[-1], (
        "variance/norm ratio barely moved across alpha; the two metrics would then be effectively "
        "interchangeable and C-2's warning would not apply")


def test_at_alpha_one_the_metrics_ARE_equivalent():
    """The historical accident that hid the problem for the whole sprint."""
    payload, d, layer = _cells(seed=11)
    M = _centred(payload, layer)
    frac = _frac64(M, d)
    assert math.isclose(1.0 * math.sqrt(frac), math.sqrt(frac * (1 - (1 - 1.0) ** 2)), rel_tol=1e-12)


# --------------------------------------------------------------------------- #
# The real numbers Gate DOSE will be argued from
# --------------------------------------------------------------------------- #
def test_real_L12_payload_reproduces_the_committed_figures():
    from insubspace_null_test import cellmean_dose
    fit = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "boombness",
                       "extract_boombness", "full_20260816_185942_1008673",
                       "directions_fit_dev.pt")
    if not os.path.exists(fit):
        pytest.skip("fit payload not present")
    pl = torch.load(fit, map_location="cpu", weights_only=False)
    frac = cellmean_dose(pl, 12, pl["d_surface"][12])
    assert math.isclose(frac, 0.820443, rel_tol=1e-5), frac
    # the two arms Gate DOSE turns on, in VARIANCE units
    assert math.isclose(frac * (1 - (1 - 0.08) ** 2), 0.126020, rel_tol=1e-4)   # above the L12 band
    assert math.isclose(frac * (1 - (1 - 0.06) ** 2), 0.095500, rel_tol=1e-4)   # inside it
    # and in NORM units, where alpha=0.30 is the matched arm instead
    assert math.isclose(0.30 * math.sqrt(frac), 0.271735, rel_tol=1e-4)
    assert math.isclose(0.08 * math.sqrt(frac), 0.072463, rel_tol=1e-4)


def test_the_L12_control_band_edges_are_what_C1_claims():
    """0.13 is L10's ceiling. L12's band is 0.0594-0.1202, and that is what the arms are matched to."""
    import json
    art = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "boombness",
                       "insubspace_null_full24.json")
    if not os.path.exists(art):
        pytest.skip("artifact not present")
    d = json.load(open(art))
    doses = {L: {k: v for k, v in d["layers"][L]["dose_cellmean_frac"].items() if k != "ARM"}
             for L in ("L6", "L8", "L10", "L12")}
    l12 = sorted(doses["L12"].values())
    assert len(l12) == 24
    assert math.isclose(l12[0], 0.0593825775943842, rel_tol=1e-9)
    assert math.isclose(l12[-1], 0.120174685705822, rel_tol=1e-9)
    # the "<= 0.13" everyone quoted is L10's, not L12's
    assert math.isclose(max(doses["L10"].values()), 0.13155342189253746, rel_tol=1e-9)
    assert max(doses["L10"].values()) > l12[-1]
