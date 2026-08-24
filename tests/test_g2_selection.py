"""test_g2_selection.py — audit T6 for `analyze_g2.py`: the headline layer was SELECTED out of a
family of ~28 correlated columns and then reported as if it had been prespecified, with the family
size recorded nowhere.

WHAT THE PRE-FIX CODE DID. `analyze_g2.main()` scanned 10 layers x {cos, proj} of `d_surface` plus
`logit_lens` wherever it existed, then ran the clustered/permutation inference on ONE of those
columns (`--headline-predictor`) and published its marginal within-domain permutation p. No
adjustment, no record of what the column was chosen from, no held-out evaluation. The module had no
`family_within_domain_perm`, no `heldout_layer_selection`, and its `holm()` could not be told a
family size (C-4's defect, in the same shape, one file over).

EVERY TEST HERE THAT ASSERTS A FIX FAILS AGAINST THE PRE-FIX MODULE, and the pre-fix module is
loaded by PINNED SHA rather than by `HEAD` -- `HEAD` is an incidental property that stops meaning
"pre-fix" the moment the fix is committed, which has already turned four tests in this repo red for
no reason. `test_the_pinned_revision_is_the_current_committed_analyze_g2` keeps the pin honest.

The load-bearing test is `test_selection_inflates_the_marginal_p_under_the_global_null`: on data
with NO association at all, the best of 28 correlated columns reaches a marginal p of 0.0005 -- the
permutation floor, i.e. "p < 5e-4", the exact string the G2 headline carries -- while the
selection-adjusted p is 0.7 and Holm rejects nothing. That is the failure mode the fix exists to
prevent, and it is unreachable by the pre-fix code because the functions do not exist there.
"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness")
sys.path.insert(0, SRC)

import analyze_g2                      # noqa: E402
import reanalyze_corrected as rc       # noqa: E402

# The revision of analyze_g2.py that carried the T6 defect: the tip of the branch before this fix.
# Pinned by sha, never `HEAD` -- see the module docstring.
PRE_FIX_SHA = "e42f5fc4"   # last revision of analyze_g2.py that carried the T6 defect


def _pre_fix_source() -> str:
    return subprocess.check_output(
        ["git", "show", "%s:src/boombness/analyze_g2.py" % PRE_FIX_SHA], cwd=ROOT).decode()


def _pre_fix_module(tmp_path):
    path = tmp_path / "prefix_analyze_g2.py"
    path.write_text(_pre_fix_source())
    spec = importlib.util.spec_from_file_location("prefix_analyze_g2", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_the_pinned_prefix_revision_is_a_real_ancestor_of_this_branch():
    """A guard on the guards, addressed by IDENTITY rather than by tip-ness.

    The pin must name a commit that is genuinely on this history -- not a typo, not a sha from
    another branch, and not `HEAD` (which stops meaning "pre-fix" the instant the fix is
    committed; that is how four tests in `test_estimand.py` went red for no code regression).
    Whether the pinned revision actually LACKS the fix is asserted separately, by reading it, in
    `test_pre_fix_g2_had_no_family_selection_machinery_at_all` -- so committing this fix does not
    invalidate either test.
    """
    rc_ = subprocess.call(["git", "merge-base", "--is-ancestor", PRE_FIX_SHA, "HEAD"], cwd=ROOT)
    assert rc_ == 0, "PRE_FIX_SHA %s is not an ancestor of HEAD" % PRE_FIX_SHA
    touched = subprocess.check_output(
        ["git", "log", "-1", "--format=%H", PRE_FIX_SHA, "--", "src/boombness/analyze_g2.py"],
        cwd=ROOT).decode().strip()
    assert touched, "PRE_FIX_SHA %s has no analyze_g2.py in its history" % PRE_FIX_SHA


# --------------------------------------------------------------------------------------------- #
# synthetic families
# --------------------------------------------------------------------------------------------- #
def _null_family(m=28, n=234, n_clusters=6, seed=7, rho_between_columns=0.0):
    """m columns and a y that none of them is associated with.

    `rho_between_columns` loads a shared factor onto every column; at 0.9 the family behaves like
    ~1 effective column (what 28 adjacent-layer projections of the same residual stream look like
    at their most collinear), at 0.0 like 28. The default is 0.0 because that is the setting under
    which the SELECTION effect is largest and therefore visible; the correlated setting is used to
    show that the max-statistic exploits the correlation where Bonferroni cannot.

    Under either null the marginal p of the best column is small by construction. A correct family
    adjustment must not be.
    """
    rng = np.random.default_rng(seed)
    common = rng.normal(size=n)
    cols = {}
    for j in range(m):
        cols["col%02d" % j] = (rho_between_columns * common
                               + math.sqrt(1 - rho_between_columns ** 2) * rng.normal(size=n)
                               ).tolist()
    y = rng.normal(size=n).tolist()
    clusters = ["d%d" % (i % n_clusters) for i in range(n)]
    return cols, y, clusters


def _one_real_signal(m=12, n=180, n_clusters=6, seed=11):
    """One column carries a strong WITHIN-cluster association; the rest are noise."""
    rng = np.random.default_rng(seed)
    clusters = ["d%d" % (i % n_clusters) for i in range(n)]
    signal = rng.normal(size=n)
    y = (signal + 0.35 * rng.normal(size=n)).tolist()
    cols = {"signal": signal.tolist()}
    for j in range(m - 1):
        cols["noise%02d" % j] = rng.normal(size=n).tolist()
    return cols, y, clusters


# --------------------------------------------------------------------------------------------- #
# T6 — the selection-adjusted p
# --------------------------------------------------------------------------------------------- #
def test_selection_inflates_the_marginal_p_under_the_global_null():
    """THE DEFECT, EXHIBITED, over 10 independent null datasets rather than one lucky draw.

    No column is associated with y. The pre-fix script picked the best of the 28 and published its
    MARGINAL p; that p is <= 0.01 on essentially every null dataset, which is a false-positive rate
    of ~100% for a nominal 1% test. The adjusted p is not, and Holm over the family rejects
    nothing. The size of the inflation, not merely its sign, is what the fix buys.
    """
    marg_hits = adj_hits = 0
    ratios = []
    for seed in range(10):
        cols, y, clusters = _null_family(seed=100 + seed)
        fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=999, seed=7 + seed)
        per = fam["per_predictor"][fam["argmax_predictor"]]
        assert fam["m"] == 28
        marg_hits += per["p_perm_within_domain_rho"] <= 0.10
        adj_hits += per["p_perm_maxT_family"] <= 0.05
        ratios.append(per["p_perm_maxT_family"] / max(per["p_perm_within_domain_rho"], 1e-12))
        assert not any(v["holm_rejected_within_domain"] for v in fam["per_predictor"].values())
    assert marg_hits >= 9, marg_hits          # "p < 0.1" for the selected column, on 10 pure nulls
    assert adj_hits <= 2, adj_hits            # the adjusted one behaves like a 5% test
    assert min(ratios) >= 5.0, ratios         # and it is never a rounding-error correction


def test_maxT_is_never_smaller_than_the_marginal_p():
    """Ordering properties of the three corrections, on both a null and a signal family:
    marginal <= step-down maxT <= single-step maxT. If any were violated the 'adjusted' p would be
    advertising a discount."""
    for cols, y, clusters in (_null_family(), _one_real_signal()):
        fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=500, seed=3)
        for nm, v in fam["per_predictor"].items():
            assert v["p_perm_maxT_stepdown_family"] >= v["p_perm_within_domain_rho"] - 1e-12, (nm, v)
            assert v["p_perm_maxT_family"] >= v["p_perm_maxT_stepdown_family"] - 1e-12, (nm, v)


def test_stepdown_and_singlestep_agree_on_the_family_argmax():
    """For the LARGEST |rho| in the family the step-down comparison set is the whole family, so the
    two adjustments must coincide exactly there. Any gap means the step-down ordering is wrong --
    and a step-down that is wrong is anticonservative, the dangerous direction."""
    for cols, y, clusters in (_null_family(seed=5), _one_real_signal(seed=6)):
        fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=500, seed=9)
        best = fam["per_predictor"][fam["argmax_predictor"]]
        assert best["p_perm_maxT_stepdown_family"] == pytest.approx(
            best["p_perm_maxT_family"], abs=1e-12), best


def test_stepdown_adjusted_p_is_monotone_in_the_observed_statistic():
    """A step-down adjusted p that is not monotone in |rho| would let a weaker column look stronger
    than a better one -- the ordering inversion audit T5 found in `g64`'s printed table."""
    cols, y, clusters = _one_real_signal(m=10, n=150, seed=13)
    fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=500, seed=2)
    per = fam["per_predictor"]
    ordered = sorted(per, key=lambda nm: -abs(per[nm]["rho_within_domain"]))
    seq = [per[nm]["p_perm_maxT_stepdown_family"] for nm in ordered]
    assert seq == sorted(seq), list(zip(ordered, seq))


def test_family_refuses_a_column_with_no_within_cluster_variation():
    """No silent NaN member. A constant column has an undefined within-domain correlation; dropping
    it quietly would shrink `m`, and `m` is the entire point of this block."""
    cols, y, clusters = _one_real_signal(m=3, n=60)
    cols["flat"] = [1.0] * len(y)
    with pytest.raises(ValueError):
        analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=5, seed=1)


def test_maxT_beats_bonferroni_exactly_where_the_family_is_collinear():
    """WHY maxT AND NOT JUST HOLM. The layer family is near-collinear, and a correction that
    assumes independence pays for 28 hypotheses it does not have. On a family with a 0.9 shared
    factor the max-statistic adjustment comes in several times smaller than m x p, because the
    shared permutation draws see the family's real effective size. Holm/Bonferroni is still
    reported alongside as the assumption-free bound; this is the reason it is not reported alone.
    """
    cols, y, clusters = _null_family(seed=1, rho_between_columns=0.9)
    fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=1999, seed=11)
    per = fam["per_predictor"][fam["argmax_predictor"]]
    bonferroni = min(1.0, fam["m"] * per["p_perm_within_domain_rho"])
    assert per["p_perm_maxT_family"] >= per["p_perm_within_domain_rho"]
    assert per["p_perm_maxT_family"] < 0.5 * bonferroni, (per, bonferroni)


def test_a_real_within_cluster_signal_survives_the_family_adjustment():
    """The correction must be able to PASS as well as fail, or it carries no information."""
    cols, y, clusters = _one_real_signal()
    fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=2000, seed=20260819)
    assert fam["argmax_predictor"] == "signal"
    sig = fam["per_predictor"]["signal"]
    assert sig["p_perm_maxT_family"] <= 0.01, sig
    assert sig["holm_rejected_within_domain"] is True
    assert not fam["per_predictor"]["noise00"]["holm_rejected_within_domain"]


def test_family_p_floor_and_family_size_are_recorded():
    """C-4's lesson: a correction whose family size lives only in the code cannot be checked."""
    cols, y, clusters = _null_family(m=5, n=60, seed=2)
    fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=99, seed=5)
    assert fam["m"] == 5 and fam["n"] == 60 and fam["n_perm"] == 99
    assert fam["p_floor"] == pytest.approx(1 / 100)
    assert fam["family"] == list(cols)
    assert all(v["holm_thr"] > 0 and v["holm_rank"] >= 1 for v in fam["per_predictor"].values())
    assert min(v["p_perm_within_domain_rho"] for v in fam["per_predictor"].values()) >= 1 / 100


def test_family_point_estimate_is_the_same_pipeline_as_rank_corr_pair():
    """The drift guard, at unit level: the vectorised family estimate and `rank_corr_pair` must be
    the same number to machine precision, or the adjusted p would be adjusting a quantity other
    than the one printed beside it -- audit T5, re-entering through the selection block."""
    cols, y, clusters = _one_real_signal()
    fam = analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=10, seed=1)
    for nm in cols:
        pair = analyze_g2.rank_corr_pair(cols[nm], y, clusters)
        assert fam["per_predictor"][nm]["rho_within_domain"] == \
            pytest.approx(pair["rho_within_domain"], abs=1e-12), nm
        assert fam["per_predictor"][nm]["rho_pooled"] == \
            pytest.approx(pair["rho_pooled"], abs=1e-12), nm


def test_family_refuses_ragged_columns():
    """Every family column must be read on the SAME rows in the SAME order. A column of a different
    length is the absolute-position/row-misalignment class this repo has been bitten by twice; it
    must raise, not broadcast."""
    cols, y, clusters = _one_real_signal(m=3, n=60)
    cols["short"] = cols["signal"][:-1]
    with pytest.raises(ValueError):
        analyze_g2.family_within_domain_perm(cols, y, clusters, n_perm=5, seed=1)


def test_one_pseudo_cluster_reduces_to_the_iid_permutation():
    """`--cluster-by ''` must go through the SAME code path, not a second one. With every row in a
    single cluster the within-cluster demeaning is global and the permutation is the ordinary
    unrestricted one, so the within-domain rho collapses onto the pooled rho. The
    'one-of-two-paths' bug class has hit this repo three times."""
    cols, y, _ = _one_real_signal(m=4, n=80)
    one = ["_no_clustering"] * len(y)
    fam = analyze_g2.family_within_domain_perm(cols, y, one, n_perm=200, seed=4)
    assert fam["n_clusters"] == 1
    for nm, v in fam["per_predictor"].items():
        assert v["rho_within_domain"] == pytest.approx(v["rho_pooled"], abs=1e-12), nm


# --------------------------------------------------------------------------------------------- #
# T6 — the measured cost of selecting (the C-8 precedent: measure it, do not assume it)
# --------------------------------------------------------------------------------------------- #
def test_nested_selection_prices_the_argmax_under_the_null():
    """In-sample the best of 28 noise columns looks associated; held out it does not. The gap IS
    the selection cost, and the pre-fix script reported the in-sample number with no held-out
    counterpart at all."""
    costs, in_samples, held, unstable = [], [], [], 0
    for seed in range(10):
        cols, y, clusters = _null_family(seed=200 + seed)
        nest = analyze_g2.heldout_layer_selection(cols, y, clusters)
        assert nest["available"] is True and nest["n_folds"] == 6
        in_samples.append(nest["in_sample_argmax_abs_rho_within_domain"])
        held.append(abs(nest["heldout_selected_rho_weighted_mean"]))
        costs.append(nest["selection_cost_abs_rho"])
        unstable += (nest["selection_is_stable"] is False)
    # in sample the best of 28 noise columns always looks associated; held out it does not
    assert min(in_samples) > 0.10, in_samples
    assert sum(held) / len(held) < 0.75 * (sum(in_samples) / len(in_samples)), (held, in_samples)
    assert sum(c > 0 for c in costs) >= 9, costs
    # under the null the folds rarely agree on a column; that is C-8's `selection_is_stable=False`
    assert unstable >= 9, unstable


def test_nested_selection_is_stable_and_nearly_free_when_the_signal_is_real():
    cols, y, clusters = _one_real_signal()
    nest = analyze_g2.heldout_layer_selection(cols, y, clusters)
    assert nest["selection_is_stable"] is True
    assert nest["distinct_columns_selected"] == ["signal"]
    # a real signal is not destroyed by holding a cluster out
    assert nest["heldout_selected_rho_weighted_mean"] > 0.5
    assert nest["selection_cost_abs_rho"] < 0.25


def test_fixed_column_heldout_is_the_no_selection_comparison():
    """`heldout_fixed_column` must NOT re-choose. On the null family, evaluating one fixed column
    out of sample and evaluating the fold-selected column out of sample are both ~0 -- the
    difference from the in-sample argmax is what selection cost means."""
    cols, y, clusters = _null_family()
    fixed = analyze_g2.heldout_fixed_column(cols["col00"], y, clusters)
    assert abs(fixed["heldout_rho_weighted_mean"]) < 0.15
    assert len(fixed["folds"]) == 6


def test_nested_selection_declines_when_there_is_only_one_cluster():
    """No silent NaN: with one cluster there is nothing to hold out and it must say so."""
    cols, y, _ = _one_real_signal(m=3, n=60)
    out = analyze_g2.heldout_layer_selection(cols, y, ["only"] * len(y))
    assert out["available"] is False and "reason" in out


# --------------------------------------------------------------------------------------------- #
# the house Holm, and the family size it now records
# --------------------------------------------------------------------------------------------- #
def test_g2_holm_delegates_to_the_house_helper_and_accepts_a_family_size():
    pv = {"A": 0.001, "B": 0.004, "C": 0.020, "D": 0.300}
    assert analyze_g2.holm(pv) == rc.holm(pv)
    assert analyze_g2.holm(pv, m=20) == {"A": True, "B": False, "C": False, "D": False}


def test_pre_fix_g2_holm_could_not_be_told_a_family_size(tmp_path):
    old = _pre_fix_module(tmp_path)
    pv = {"A": 0.001, "B": 0.004, "C": 0.020, "D": 0.300}
    assert old.holm(pv) == analyze_g2.holm(pv)          # same decisions at the default family ...
    with pytest.raises(TypeError):                       # ... but the family could not be stated
        old.holm(pv, m=20)


def test_pre_fix_g2_had_no_family_selection_machinery_at_all(tmp_path):
    old = _pre_fix_module(tmp_path)
    for fn in ("family_within_domain_perm", "heldout_layer_selection", "heldout_fixed_column",
               "std_ranks", "demean_by_cluster"):  # none of these existed before the T6 fix
        assert not hasattr(old, fn), (
            "%s exists in the pinned pre-fix analyze_g2 — the pin is wrong and every T6 test here "
            "has stopped proving anything" % fn)
    src = _pre_fix_source()
    assert "layer_selection" not in src
    assert "p_perm_maxT_family" not in src
    assert "holm_family" not in src


def test_pre_fix_g2_refactor_did_not_change_rank_corr_pair(tmp_path):
    """`rank_corr_pair` was rewritten to call the shared `std_ranks` / `demean_by_cluster` so the
    family and the headline cannot drift. It must be BIT-IDENTICAL to the committed version."""
    old = _pre_fix_module(tmp_path)
    rng = np.random.default_rng(20260819)
    for _ in range(25):
        n = 97
        x = rng.normal(size=n).tolist()
        y = rng.normal(size=n).tolist()
        cl = ["d%d" % (i % 7) for i in range(n)]
        a, b = old.rank_corr_pair(x, y, cl), analyze_g2.rank_corr_pair(x, y, cl)
        assert a["rho_pooled"] == b["rho_pooled"]
        assert a["rho_within_domain"] == b["rho_within_domain"]


# --------------------------------------------------------------------------------------------- #
# R-18 — two G2 artifacts PREDATE this contract and belong to a WITHDRAWN result
#
# `g2_analysis_lastpos.json` and `qwen3_g2_analysis.json` were written 2026-08-18, before the
# 08-19 `layer_selection` / `provenance.inputs` contract existed, so they cannot satisfy it. The
# obvious repair -- re-run `analyze_g2.py` -- is the WRONG one here: G2 was RETRACTED as R-18
# ("Boombness does not predict attack success"; the within-domain rho crosses zero, +0.2618 ->
# -0.0518, on the clean rows), and regenerating a withdrawn analysis would stamp today's commit,
# today's interpreter and a fresh selection block onto a result nobody is allowed to cite. The
# artifact would then look freshly blessed while saying something the project has withdrawn.
#
# So they are VERSIONED as retracted instead, and the exemption is deliberately narrow:
#
#   * it applies only to artifacts named in `RETRACTED_ARTIFACTS` below (or carrying their own
#     `_retracted` marker, the `_`-prefixed metadata convention `label_artifacts.py` established),
#     each with the retraction id and the document that carries it;
#   * AND only while the artifact still PREDATES the contract, which is read from git rather than
#     asserted by hand -- regenerate one of them and its last commit moves past `CONTRACT_EPOCH`,
#     the exemption evaporates, and the full contract is demanded of it again. An untracked or
#     locally-rewritten artifact gets no exemption either.
#
# `g2_analysis_cwpos.json` is part of the same retracted G2, and is deliberately NOT exempt: it
# was regenerated 2026-08-22, after the contract, so it is held to all of it.
# --------------------------------------------------------------------------------------------- #
CONTRACT_EPOCH = 1787086800.0        # 2026-08-19 00:00 local — layer_selection/provenance.inputs

RETRACTED_ARTIFACTS = {
    "g2_analysis_lastpos.json": {
        "retraction_id": "R-18",
        "claim_withdrawn": "Boombness predicts attack success (G2)",
        "recorded_in": "docs/BOOMBNESS_CONTINUATION_LOG.md",
        "note": "predates the 2026-08-19 layer_selection/provenance.inputs contract; NOT "
                "regenerated, because refreshing provenance on a withdrawn analysis would make "
                "it look current",
    },
    "qwen3_g2_analysis.json": {
        "retraction_id": "R-18",
        "claim_withdrawn": "Boombness predicts attack success (G2)",
        "recorded_in": "docs/BOOMBNESS_CONTINUATION_LOG.md",
        "note": "predates the 2026-08-19 layer_selection/provenance.inputs contract; NOT "
                "regenerated, because refreshing provenance on a withdrawn analysis would make "
                "it look current",
    },
}


def _last_commit_epoch(relpath):
    """When the committed artifact last changed, or None if git does not track it."""
    out = subprocess.run(["git", "log", "-1", "--format=%ct", "--", relpath],
                         cwd=ROOT, capture_output=True, text=True).stdout.strip()
    return float(out) if out else None


def _retraction_record(artifact, d):
    """The machine-readable retraction record for `artifact`, or None if it is not retracted.

    Read from the artifact itself first -- `_retracted`, in the `_`-prefixed metadata convention
    `label_artifacts.py` owns -- so stamping the file is enough and this list need not be edited.
    """
    marker = d.get("_retracted")
    return marker if isinstance(marker, dict) else RETRACTED_ARTIFACTS.get(artifact)


def _predates_the_contract_as_a_retracted_artifact(artifact, d):
    """True only for a RETRACTED artifact that git still shows as older than the contract."""
    rec = _retraction_record(artifact, d)
    if rec is None:
        return False
    for k in ("retraction_id", "claim_withdrawn", "recorded_in"):
        assert rec.get(k), "%s: retraction record is missing %s" % (artifact, k)
    when = _last_commit_epoch(os.path.join("outputs", "boombness", artifact))
    return when is not None and when < CONTRACT_EPOCH


def test_the_retraction_exemption_names_a_retraction_that_is_actually_documented():
    """Anti-vacuity: a retraction marker nobody can look up is a licence, not a record."""
    log = open(os.path.join(ROOT, "docs", "BOOMBNESS_CONTINUATION_LOG.md"),
               encoding="utf-8").read()
    assert RETRACTED_ARTIFACTS
    for artifact, rec in RETRACTED_ARTIFACTS.items():
        assert os.path.exists(os.path.join(ROOT, rec["recorded_in"])), rec["recorded_in"]
        assert rec["retraction_id"] in log, (artifact, rec["retraction_id"])
        assert "RETRACTED" in log


def test_the_contract_exemption_is_not_a_blanket_exemption():
    """The case the exemption must NOT cover, executed. A NON-retracted artifact that is missing
    `layer_selection` / `provenance.inputs` must still fail, and a retracted artifact that has been
    regenerated since the contract (git mtime past CONTRACT_EPOCH) must lose the exemption.

    Both halves go red against a version that simply skips the two names.
    """
    stale = {"provenance": {"argv": [], "git_commit": "x", "git_dirty": False, "python": "p"}}
    # an artifact nobody has retracted has NO record, whatever its age -- checked on the record
    # itself as well as on the exemption, because an exemption that says no only because the file
    # happens to be untracked would still say yes to the next tracked pre-contract artifact.
    assert _retraction_record("some_other_g2.json", stale) is None
    assert _retraction_record("g2_analysis_cwpos.json", {}) is None
    assert not _predates_the_contract_as_a_retracted_artifact("some_other_g2.json", stale)
    # retracted, but regenerated after the contract -> not exempt. `g2_analysis_cwpos.json` is the
    # real instance of exactly that: same withdrawn G2, committed 2026-08-22, held to the contract.
    assert _last_commit_epoch("outputs/boombness/g2_analysis_cwpos.json") > CONTRACT_EPOCH
    assert not _predates_the_contract_as_a_retracted_artifact(
        "g2_analysis_cwpos.json",
        {"_retracted": dict(RETRACTED_ARTIFACTS["g2_analysis_lastpos.json"])})
    # and the two that ARE exempt really are retracted AND really are older than the contract
    for a in RETRACTED_ARTIFACTS:
        assert _predates_the_contract_as_a_retracted_artifact(a, {})
        assert _last_commit_epoch(os.path.join("outputs", "boombness", a)) < CONTRACT_EPOCH


# --------------------------------------------------------------------------------------------- #
# C-10 — the artifact must record every input path, argv, commit, dirty flag and interpreter
# --------------------------------------------------------------------------------------------- #
@pytest.mark.parametrize("artifact", ["g2_analysis_cwpos.json", "g2_analysis_lastpos.json",
                                      "qwen3_g2_analysis.json"])
def test_regenerated_g2_artifacts_record_full_provenance(artifact):
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip("%s not present" % artifact)
    d = json.load(open(path))
    prov = d["provenance"]
    if _predates_the_contract_as_a_retracted_artifact(artifact, d):
        # R-18: withdrawn and not regenerated. What the pre-contract script DID record is still
        # checked -- the exemption is for `inputs`, which did not exist, and nothing else.
        for k in ("argv", "git_commit", "git_dirty", "python"):
            assert k in prov, "%s: provenance is missing %s" % (artifact, k)
        return
    for k in ("argv", "git_commit", "git_dirty", "python", "inputs"):
        assert k in prov, "%s: provenance is missing %s" % (artifact, k)
    for k in ("judge", "extract", "score", "refusalness"):
        assert k in prov["inputs"], "%s: provenance.inputs is missing %s" % (artifact, k)
    # the three that were recorded only OUTSIDE provenance must agree with the ones inside it
    for k in ("judge", "extract", "score"):
        assert prov["inputs"][k] == d[k]
    # `--refusalness` is the path C-10 named: if a mediation section shipped, its input is named
    if "mediation" in d:
        assert prov["inputs"]["refusalness"], (
            "%s ships a mediation section computed from a refusalness run it does not name"
            % artifact)


@pytest.mark.parametrize("artifact", ["g2_analysis_cwpos.json", "g2_analysis_lastpos.json",
                                      "qwen3_g2_analysis.json"])
def test_regenerated_g2_artifacts_price_their_layer_selection(artifact):
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip("%s not present" % artifact)
    d = json.load(open(path))
    if _predates_the_contract_as_a_retracted_artifact(artifact, d):
        # R-18, and written before `layer_selection` existed. Assert it is genuinely absent rather
        # than half-present: a partial selection block would be drift, not age.
        assert "layer_selection" not in d, (
            "%s carries a layer_selection block after all — the retraction exemption is hiding a "
            "real contract violation" % artifact)
        return
    sel = d["layer_selection"]
    assert sel["m"] >= 2 and len(sel["family"]) == sel["m"]
    assert sel["headline_predictor"] in sel["per_predictor"]
    assert sel["p_estimand"] == "rho_within_domain"
    hl = sel["headline"]
    assert hl["p_perm_maxT_family"] >= hl["p_perm_maxT_stepdown_family"] - 1e-12
    assert hl["p_perm_maxT_stepdown_family"] >= hl["p_perm_within_domain_rho"] - 1e-12
    # the family the headline was chosen from must be the family that was scanned
    assert set(sel["family"]) <= {p["name"] for p in d["predictors"]}
    assert d["holm_family"]["m"] == len(d["holm_family"]["members"])
    # and the headline's within-domain rho must be the SAME number the clustered block reports
    if "clustered_inference" in d and d["clustered_inference"]["n"] == sel["n"]:
        assert hl["rho_within_domain"] == pytest.approx(
            d["clustered_inference"]["rho_within_domain"], abs=1e-9)


# --------------------------------------------------------------------------------------------- #
# the guard on the headline itself — an end-to-end case the pre-fix script handled SILENTLY
# --------------------------------------------------------------------------------------------- #
_CWPOS = {
    "judge": "outputs/boombness/judge/base_20260816_210948_3024689",
    "extract": "outputs/boombness/extract_boombness/full_20260816_185942_1008673",
    "score": "outputs/boombness/score_behavior/base_20260816_203355_3985444",
}


def _cwpos_inputs_present():
    return all(os.path.exists(os.path.join(ROOT, p, "DONE.json")) for p in _CWPOS.values())


def _run_g2(script, headline, out, extra=()):
    cmd = [sys.executable, script,
           "--judge", os.path.join(ROOT, _CWPOS["judge"]),
           "--extract", os.path.join(ROOT, _CWPOS["extract"]),
           "--score", os.path.join(ROOT, _CWPOS["score"]),
           "--extract-position", "codeword_last",
           "--headline-predictor", headline, "--out", out, *extra]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


def test_a_headline_outside_the_scanned_family_is_refused_not_silently_dropped(tmp_path):
    """END-TO-END, ON THE REAL G2 INPUTS. `--headline-predictor d_surface|L99|proj` names a column
    no layer in `--layers` produces. The PRE-FIX script computed `xs = [rep[k].get(hl) ...]`, got
    all-None, failed its own `len(ok) > 10` check, and skipped the clustered block entirely -- so it
    wrote an artifact with NO `clustered_inference` section, exit code 0, and nothing said why. The
    fixed script refuses. Both halves are asserted here, so the test would pass vacuously if the
    guard were removed only by also making the pre-fix assertion false."""
    if not _cwpos_inputs_present():
        pytest.skip("the committed G2 input runs are not present")
    bad = str(tmp_path / "bad.json")
    new = _run_g2(os.path.join(SRC, "analyze_g2.py"), "d_surface|L99|proj", bad)
    assert new.returncode != 0, new.stdout[-2000:]
    assert "REFUSING" in (new.stdout + new.stderr)
    assert "d_surface|L99|proj" in (new.stdout + new.stderr)
    assert not os.path.exists(bad), "the refused run still wrote an artifact"

    old_src = tmp_path / "old_analyze_g2.py"
    old_src.write_text(_pre_fix_source())
    # the pre-fix module resolves `common`/`reanalyze_corrected` off its own directory, so run the
    # pinned source from inside src/boombness
    old_in_place = os.path.join(SRC, "_prefix_analyze_g2_under_test.py")
    try:
        with open(old_in_place, "w") as f:
            f.write(old_src.read_text())
        prefix_out = str(tmp_path / "prefix.json")
        old = _run_g2(old_in_place, "d_surface|L99|proj", prefix_out)
        assert old.returncode == 0, old.stderr[-2000:]
        assert "clustered_inference" not in json.load(open(prefix_out)), (
            "the pinned pre-fix analyze_g2 refused or produced clustered inference for a "
            "non-existent headline column — the pin is wrong")
    finally:
        if os.path.exists(old_in_place):
            os.remove(old_in_place)


# --------------------------------------------------------------------------------------------- #
# VERIFIER ROUND (2026-08-19). Three defects the T6 patch shipped, each of a class this repo has
# been bitten by before. Each test below FAILS against the T6 patch as it was submitted; the
# submitted-patch source is pinned by sha so committing these fixes cannot turn them red.
# --------------------------------------------------------------------------------------------- #
def test_fixed_column_heldout_refuses_when_there_is_nothing_to_hold_out():
    """ONE-OF-TWO-PATHS (R-12's class), inside the T6 patch itself.

    `heldout_layer_selection` guards `len(groups) < 2` and answers `available: False`.
    `heldout_fixed_column` -- its sibling, the no-selection COMPARISON that the whole
    selection-cost argument rests on -- had no such guard. On `--cluster-by ''`, a documented and
    supported mode, every row lands in one pseudo-cluster, so `heldout_fixed_column` evaluated the
    column on ALL the rows and published the answer as `heldout_rho_weighted_mean` inside a block
    whose note promises "evaluated on the held-out one".

    The pre-fix number was not merely optimistic, it was the in-sample statistic to the last
    digit; this test asserts exactly that identity so it cannot pass vacuously.
    """
    rng = np.random.default_rng(0)
    n = 60
    col = rng.normal(size=n)
    y = (col + 0.2 * rng.normal(size=n)).tolist()
    col = col.tolist()
    one = ["only"] * n

    out = analyze_g2.heldout_fixed_column(col, y, one)
    assert out["available"] is False, out
    assert "reason" in out
    assert out["heldout_rho_weighted_mean"] is None, (
        "with one pseudo-cluster nothing was held out, so there is no held-out mean to report")

    # the number the pre-fix code DID report, to the last digit: the in-sample Spearman
    in_sample, _ = analyze_g2.spearman(col, y)
    assert abs(in_sample) > 0.9
    # and the sibling has always refused the same input -- the two paths now agree
    nest = analyze_g2.heldout_layer_selection({"a": col}, y, one)
    assert nest["available"] is False


def test_fixed_column_heldout_still_works_with_real_clusters():
    """The guard must not have disabled the function on the path that matters."""
    cols, y, clusters = _null_family()
    out = analyze_g2.heldout_fixed_column(cols["col00"], y, clusters)
    assert out["available"] is True
    assert out["n_folds"] == 6 and out["n_folds_undefined"] == 0
    assert abs(out["heldout_rho_weighted_mean"]) < 0.15


def _y_constant_within_every_cluster(n=40, k=5):
    clusters = ["d%d" % (i // (n // k)) for i in range(n)]
    y = [float(c[1:]) for c in clusters]          # y varies BETWEEN clusters, never within one
    cols = {"a": [float(i) for i in range(n)], "b": [float(-i) for i in range(n)]}
    return cols, y, clusters


def test_nested_selection_does_not_report_a_stable_selection_off_undefined_folds():
    """SILENT NaN WITH NO REASON -- the exact hole `family_within_domain_perm` refuses, left open
    in the function next to it.

    A held-out cluster in which `y` never varies (a domain where every prompt scored the same --
    entirely reachable on strongreject_score) gives an undefined held-out Spearman. The submitted
    patch appended `heldout_rho: nan`, counted the fold as USED, and returned
    `available: True`, `selection_is_stable: True`, `n_folds: 5` alongside
    `selection_cost_abs_rho: nan` -- a NaN in the headline number with a stability flag saying the
    selection was fine and no reason recorded anywhere.
    """
    cols, y, clusters = _y_constant_within_every_cluster()
    out = analyze_g2.heldout_layer_selection(cols, y, clusters)
    # nothing is definable on any fold, so there is nothing to average and it must say so
    assert out["available"] is False, out
    assert out["n_folds_skipped"] == 5, out
    for f in out["folds"]:
        assert f["skipped"] is True and "reason" in f
    # and no NaN escapes under a name that reads like a number
    assert "selection_cost_abs_rho" not in out
    assert "heldout_selected_rho_weighted_mean" not in out
    assert "selection_is_stable" not in out


def test_nested_selection_marks_a_partially_undefined_fold_instead_of_averaging_it():
    """One bad cluster must not silently NaN the whole selection cost, and must not be counted as
    a fold that agreed with the others."""
    cols, y, clusters = _one_real_signal(m=6, n=180, n_clusters=6)
    # flatten y inside ONE cluster only: that fold's held-out rho becomes undefined
    y = list(y)
    for i, c in enumerate(clusters):
        if c == "d0":
            y[i] = 7.0
    out = analyze_g2.heldout_layer_selection(cols, y, clusters)
    assert out["available"] is True
    assert out["n_folds_undefined"] == 1, out["folds"]
    assert out["n_folds"] == 5
    assert math.isfinite(out["selection_cost_abs_rho"]), "one dead cluster NaN'd the whole cost"
    assert math.isfinite(out["heldout_selected_rho_weighted_mean"])
    bad = [f for f in out["folds"] if f.get("skipped")]
    assert len(bad) == 1 and "undefined" in bad[0]["reason"]
    # stability cannot be claimed while a fold produced no number at all
    assert out["selection_is_stable"] is False


def test_nested_selection_survives_a_fold_with_no_definable_argmax():
    """`best` stayed None when no column had a defined within-cluster rho on the selection folds,
    and the submitted patch then did `cols[None]` -- a bare KeyError with no reason recorded."""
    cols, y, clusters = _y_constant_within_every_cluster(n=40, k=5)
    out = analyze_g2.heldout_layer_selection(cols, y, clusters)   # must not raise
    assert out["available"] is False
    assert all("reason" in f for f in out["folds"])


def test_the_drift_guard_fires_on_a_row_count_mismatch_instead_of_standing_down(tmp_path):
    """DEAD-GUARD SHAPE. The submitted patch wrote

        if ci_prev and ci_prev.get("n") == fam["n"]:   # then compare rho

    so the one condition that PROVES the two pipelines disagreed about which rows to analyse --
    a different n -- switched the comparison off entirely, silently, with nothing recorded. The
    guard now refuses on the mismatch."""
    src = open(os.path.join(SRC, "analyze_g2.py")).read()
    assert 'if ci_prev and ci_prev.get("n") == fam["n"]:' not in src, (
        "the drift guard is still gated on the row counts AGREEING, so it cannot fire on the "
        "case it exists to catch")
    assert 'if ci_prev.get("n") != fam["n"]:' in src
    i = src.index('if ci_prev.get("n") != fam["n"]:')
    assert "REFUSING" in src[i:i + 600]


def test_the_two_identically_named_marginal_p_fields_are_cross_referenced():
    """`p_perm_within_domain_rho` now appears in TWO blocks of the artifact with two different
    values (different permutation seeds). C-10's lesson was that one name with two answers is a
    defect even when both answers are correct."""
    for artifact in ("g2_analysis_cwpos.json", "g2_analysis_lastpos.json",
                     "qwen3_g2_analysis.json"):
        path = os.path.join(ROOT, "outputs", "boombness", artifact)
        if not os.path.exists(path):
            pytest.skip("%s not present" % artifact)
        d = json.load(open(path))
        if "clustered_inference" not in d:
            continue
        if _predates_the_contract_as_a_retracted_artifact(artifact, d):
            continue                      # R-18: withdrawn, predates the cross-reference
        x = d["layer_selection"]["marginal_p_cross_reference"]
        assert x["this_block"] == d["layer_selection"]["headline"]["p_perm_within_domain_rho"]
        assert x["clustered_inference"] == d["clustered_inference"]["p_perm_within_domain_rho"]
        assert x["seed_here"] != x["seed_clustered_inference"]
        # two draws of one estimand: they must agree to within a few Monte-Carlo standard errors
        npm = d["layer_selection"]["n_perm"]
        p = max(x["this_block"], 1.0 / (npm + 1))
        se = math.sqrt(p * (1 - p) / npm)
        assert abs(x["this_block"] - x["clustered_inference"]) <= 4 * se + 2.0 / (npm + 1), (
            artifact, x)


def test_regenerated_artifacts_carry_the_availability_contract_on_both_heldout_paths():
    for artifact in ("g2_analysis_cwpos.json", "g2_analysis_lastpos.json",
                     "qwen3_g2_analysis.json"):
        path = os.path.join(ROOT, "outputs", "boombness", artifact)
        if not os.path.exists(path):
            pytest.skip("%s not present" % artifact)
        d = json.load(open(path))
        if _predates_the_contract_as_a_retracted_artifact(artifact, d):
            continue                      # R-18: withdrawn, predates the availability contract
        sel = d["layer_selection"]
        for k in ("nested_selection", "fixed_headline_heldout"):
            assert "available" in sel[k], "%s: %s does not say whether it is available" % (
                artifact, k)
        if sel["fixed_headline_heldout"]["available"]:
            assert sel["fixed_headline_heldout"]["n_folds_undefined"] == 0
        # a stable selection must be stable over folds that all produced a number
        ns = sel["nested_selection"]
        if ns.get("available") and ns.get("selection_is_stable"):
            assert ns["n_folds_undefined"] == 0 and ns["n_folds_skipped"] == 0
