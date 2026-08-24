"""The dose metric the HOOK actually implements (C-6).

WHY THIS FILE EXISTS. `cellmean_dose` measures a direction against the CENTRED cell means -- the
cross-cell contrast. `AllPositionProjectOut` subtracts alpha*(h.u)u from the real, UN-CENTRED residual
at every position and every decode step. The two differ by the grand mean.

That is not academic. R-AG reported two arms as "dose-matched to 1.17x" on the centred metric. On the
single cell those runs generated from (natural_doublespeak = cell C) they remove 8.31% and 54.84% of
||m_C||, a 6.60x gap, because cos(grand_mean, W)=0.389 against cos(grand_mean, N)=0.140. The centred
metric could not see it, so a dose confound of exactly the kind this phase had already retracted three
times (6.83x, 24.79x, 14.05x) was reported as its ABSENCE.

Run:  python -m pytest tests/test_cell_residual_dose.py -q
"""
import math
import os
import sys

import pytest

torch = pytest.importorskip("torch")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _payload(seed=0, dim=32, layer=14):
    g = torch.Generator().manual_seed(seed)
    cells = {c: {layer: torch.randn(dim, generator=g)} for c in ("A", "B", "C", "E")}
    return {"cell_means": cells}, layer


def test_it_measures_the_UNCENTRED_residual_not_the_contrast():
    """THE POINT. A direction parallel to the grand mean has ~zero CENTRED dose and large real dose."""
    from score_behavior import cell_residual_frac_removed
    from insubspace_null_test import cellmean_dose
    pl, L = _payload()
    M = torch.stack([pl["cell_means"][c][L] for c in ("A", "B", "C", "E")])
    g = M.mean(0)
    pl["d_surface"] = {L: g.clone()}
    centred = cellmean_dose(pl, L, g)
    real = cell_residual_frac_removed(pl, L, g, 1.0, ["C"])["C"]
    assert centred < 0.10, f"grand-mean direction should have small CENTRED dose, got {centred}"
    assert real > 0.30, f"grand-mean direction must have LARGE real dose, got {real}"
    assert real > 5 * centred, (
        "the two metrics no longer diverge on a grand-mean direction; this test has stopped "
        "exercising the C-6 failure")


def test_alpha_scales_it_linearly():
    """project_out removes alpha*(h.u)u, so the fraction is linear in alpha -- unlike the variance
    metric, which goes as 1-(1-alpha)^2."""
    from score_behavior import cell_residual_frac_removed
    pl, L = _payload(seed=3)
    d = pl["cell_means"]["A"][L] + pl["cell_means"]["B"][L]
    full = cell_residual_frac_removed(pl, L, d, 1.0, ["C"])["C"]
    half = cell_residual_frac_removed(pl, L, d, 0.5, ["C"])["C"]
    assert math.isclose(half, 0.5 * full, rel_tol=1e-9), (half, full)


def test_it_is_normalization_invariant():
    """The stored direction need not be unit norm -- the hook normalizes."""
    from score_behavior import cell_residual_frac_removed
    pl, L = _payload(seed=5)
    d = pl["cell_means"]["A"][L]
    a = cell_residual_frac_removed(pl, L, d, 1.0, ["C"])["C"]
    b = cell_residual_frac_removed(pl, L, d * 7.3, 1.0, ["C"])["C"]
    # TOLERANCE 1e-6, NOT 1e-9. The cell means are float32, so `d * 7.3` rounds before the helper
    # casts to float64; the observed relative difference is 3.0e-08, which is float32 noise and not
    # a normalization error. The first draft asserted 1e-9 and went red -- the TEST was wrong, the
    # code was right, and the obvious reading of that failure is the opposite one.
    assert math.isclose(a, b, rel_tol=1e-6), (a, b)


def test_only_the_requested_cells_are_reported():
    from score_behavior import cell_residual_frac_removed
    pl, L = _payload(seed=7)
    d = pl["cell_means"]["C"][L]
    got = cell_residual_frac_removed(pl, L, d, 1.0, ["C"])
    assert set(got) == {"C"}
    assert math.isclose(got["C"], 1.0, rel_tol=1e-6), \
        "a direction parallel to m_C must remove 100% of m_C"


def test_missing_cells_are_skipped_not_crashed():
    from score_behavior import cell_residual_frac_removed
    pl, L = _payload(seed=9)
    got = cell_residual_frac_removed(pl, L, pl["cell_means"]["A"][L], 1.0, ["A", "NOPE"])
    assert set(got) == {"A"}


def test_it_is_wired_into_the_dose_record():
    """A metric computed but not recorded is how C-6 happened."""
    src = open(os.path.join(ROOT, "src", "boombness", "score_behavior.py")).read()
    assert '_rec["cell_residual_frac_removed"] = cell_residual_frac_removed(' in src, \
        "the real-dose metric is no longer emitted into the run's dose record"


def test_the_real_R_AG_numbers_reproduce():
    """The retraction's own figures, pinned so C-6 cannot be quietly un-retracted."""
    from score_behavior import cell_residual_frac_removed
    bb = os.path.join(ROOT, "outputs", "boombness", "extract_boombness",
                      "x2fit_basket_bomb_20260823_204217_239421", "directions_fit_dev.pt")
    fN = os.path.join(ROOT, "outputs", "boombness", "extract_boombness",
                      "fitN_concept", "directions_fit_dev.pt")
    fW = os.path.join(ROOT, "outputs", "boombness", "extract_boombness",
                      "fitW_codeword", "directions_fit_dev.pt")
    if not all(os.path.exists(x) for x in (bb, fN, fW)):
        pytest.skip("fits not present")
    pl = torch.load(bb, map_location="cpu", weights_only=False)
    N = torch.load(fN, map_location="cpu", weights_only=False)["d_surface"][14]
    W = torch.load(fW, map_location="cpu", weights_only=False)["d_surface"][14]
    dn = cell_residual_frac_removed(pl, 14, N, 1.0, ["C"])["C"]
    dw = cell_residual_frac_removed(pl, 14, W, 1.0, ["C"])["C"]
    assert math.isclose(dn, 0.0831, abs_tol=5e-4), dn
    assert math.isclose(dw, 0.5484, abs_tol=5e-4), dw
    assert dw / dn > 6.0, f"the retracted 6.6x gap is gone: {dw / dn}"
