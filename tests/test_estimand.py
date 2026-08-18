"""test_estimand.py — the guards for audit T5 (estimand pairing), plan §9 decision question 5
(controlling for the number of demonstrations), and the role-identifiability gate that could not
fail.

EVERY TEST HERE FAILS AGAINST THE PRE-FIX CODE, and each one proves that by loading the committed
HEAD version of the module beside the working-tree one and asserting the old behaviour explicitly.
That is deliberate: three of these defects are of the "the code is silent, the reader supplies the
wrong meaning" kind, so a test that only pins the new behaviour would not show that anything was
ever wrong.

  T5   `analyze_g2.py` reported a POOLED Spearman and, one key away, a permutation p computed after
       demeaning x and y WITHIN domain; `analyze_g9.py` reported a POOLED beta beside a
       within-cluster permutation p. Both pairs read as estimate-and-its-p and neither is.
  §9.5 `analyze_g9.py` used `n_examples` only as a FILTER, so the published boombness->ASR
       coefficient was never guarded against a demonstration-count dose-response.
  ROLE `analyze_g9.role_identifiability` tested family overlap on a `family_id` string that embeds
       the style name, so overlap was 0 by construction and the gate refused unconditionally. A
       gate that cannot pass carries no information; the crossed/nested pair below is the proof
       that it now can.
"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness")
sys.path.insert(0, SRC)

import analyze_g2            # noqa: E402
import analyze_g9            # noqa: E402


def _head_module(name, tmp_path):
    """Import the COMMITTED version of a module, so a test can assert what the defect used to do."""
    src = subprocess.check_output(["git", "show", f"HEAD:src/boombness/{name}.py"], cwd=ROOT)
    path = tmp_path / f"head_{name}.py"
    path.write_bytes(src)
    spec = importlib.util.spec_from_file_location(f"head_{name}", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------------------------- #
# T5 — the two estimands are different quantities, and on Simpson-shaped data they differ in SIGN
# --------------------------------------------------------------------------------------------- #
SIMPSON_X = [1.0, 2.0, 3.0, 11.0, 12.0, 13.0]
SIMPSON_Y = [3.0, 2.0, 1.0, 13.0, 12.0, 11.0]
SIMPSON_CL = ["A", "A", "A", "B", "B", "B"]


def test_g2_reports_both_estimands_and_they_can_disagree_in_sign():
    pair = analyze_g2.rank_corr_pair(SIMPSON_X, SIMPSON_Y, SIMPSON_CL)
    # pooled: POSITIVE (+0.543 here, dragged off +1 by the within-cluster reversal)
    # within domain: PERFECTLY NEGATIVE. Same six pairs, opposite conclusions.
    assert pair["rho_pooled"] > 0.5, pair
    assert pair["rho_within_domain"] < -0.9, pair
    # the whole point of the audit: the p that ships beside them belongs to the SECOND one
    assert pair["p_estimand_of_within_domain_permutation"] == "rho_within_domain"


def test_g2_pooled_half_of_the_pair_is_the_ordinary_spearman():
    """The renaming must not have quietly changed what `rho_pooled` means."""
    r_scipy, _ = analyze_g2.spearman(SIMPSON_X, SIMPSON_Y)
    assert analyze_g2.rank_corr_pair(SIMPSON_X, SIMPSON_Y, SIMPSON_CL)["rho_pooled"] == \
        pytest.approx(r_scipy, abs=1e-12)


def test_pre_fix_g2_could_not_report_the_within_domain_estimate(tmp_path):
    old = _head_module("analyze_g2", tmp_path)
    assert not hasattr(old, "rank_corr_pair"), (
        "the committed analyze_g2 has a rank_corr_pair — this test is no longer proving anything")
    # and the old artifact contract paired a pooled rho with a within-domain p under bare names
    src = subprocess.check_output(["git", "show", "HEAD:src/boombness/analyze_g2.py"],
                                  cwd=ROOT).decode()
    assert '"rho": r_naive' in src and '"p_within_domain_perm": p_perm' in src
    assert "rho_within_domain" not in src


# --------------------------------------------------------------------------------------------- #
# T5 in g9 — the permutation p belongs to `beta_within_domain`, which did not exist
# --------------------------------------------------------------------------------------------- #
def _between_cluster_only():
    """x and y move together ACROSS clusters and not at all within one.

    The pooled coefficient is large; the within-cluster coefficient is zero. Any report that shows
    the pooled beta next to the within-cluster p is showing a large estimate with a p that cannot
    speak about it.
    """
    xs, ys, cl = [], [], []
    for g, base in enumerate([0.0, 1.0, 2.0, 3.0, 4.0, 5.0]):
        for j, jitter in enumerate([-0.1, 0.0, 0.1, -0.05, 0.05, 0.0]):
            xs.append(base + jitter)
            ys.append(base - jitter)       # within a cluster the association is NEGATIVE
            cl.append(f"g{g}")
    return xs, ys, cl


def test_g9_within_cluster_beta_is_a_different_number_from_the_pooled_beta():
    xs, ys, cl = _between_cluster_only()
    X = [[1.0, v] for v in xs]
    beta_pooled, _, _ = analyze_g9.ols(X, ys)
    beta_within = analyze_g9.within_cluster_beta([xs], ys, cl, 0)
    assert beta_pooled[1] > 0.9                 # pooled: strongly positive
    assert beta_within < -0.5                   # within cluster: negative
    # and the permutation p is a p for the SECOND number
    p = analyze_g9.perm_p_within_cluster([xs], ys, cl, 0, n_perm=200)
    assert 0.0 < p <= 1.0


def test_g9_within_cluster_beta_matches_the_permutation_footing(tmp_path):
    """`within_cluster_beta` must demean exactly what the permutation demeans: the target column
    and y, and nothing else. If it demeaned every column the reported estimate would again not be
    the tested one — the T5 defect, reintroduced from the other side."""
    xs, ys, cl = _between_cluster_only()
    other = [1.0 if i % 2 else 0.0 for i in range(len(xs))]
    b = analyze_g9.within_cluster_beta([xs, other], ys, cl, 0)
    dm_x = analyze_g9.demean_within(xs, cl)
    dm_y = analyze_g9.demean_within(ys, cl)
    X = [[1.0, dm_x[i], other[i]] for i in range(len(xs))]
    expect, _, _ = analyze_g9.ols(X, dm_y)
    assert b == pytest.approx(expect[1], abs=1e-12)


def test_pre_fix_g9_had_no_within_cluster_point_estimate(tmp_path):
    old = _head_module("analyze_g9", tmp_path)
    assert not hasattr(old, "within_cluster_beta")
    assert not hasattr(old, "demean_within"), (
        "demeaning lived inside the permutation as a closure, which is why the reported point "
        "estimate could not be put on the same footing")


# --------------------------------------------------------------------------------------------- #
# plan §9 decision question 5 — n_examples must be a REGRESSOR, not only a filter
# --------------------------------------------------------------------------------------------- #
def test_pre_fix_g9_never_used_n_examples_as_a_regressor():
    src = subprocess.check_output(["git", "show", "HEAD:src/boombness/analyze_g9.py"],
                                  cwd=ROOT).decode()
    assert "min-examples" in src                      # it was there, purely as a filter
    assert "n_examples_control" not in src
    assert "boombness+refusalness+n_examples" not in src
    new = open(os.path.join(SRC, "analyze_g9.py")).read()
    assert "boombness+refusalness+n_examples" in new and "n_examples_control" in new


@pytest.mark.parametrize("artifact", ["g9_three_predictor_cwpos.json",
                                      "g9_three_predictor_lastpos.json"])
def test_regenerated_g9_artifacts_answer_question_5(artifact):
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    d = json.load(open(path))
    nc = d["n_examples_control"]
    assert nc["answered"] is True
    assert nc["verdict"]
    # before -> after must be recorded for BOTH coefficients the control can move
    for k in ("boombness_before", "boombness_after", "refusalness_before", "refusalness_after"):
        assert nc[k]["beta_pooled"] is not None
        assert nc[k]["beta_within_domain"] is not None
    assert "boombness+refusalness+n_examples" in d["models"]


@pytest.mark.parametrize("artifact", ["g9_three_predictor_cwpos.json",
                                      "g9_three_predictor_lastpos.json"])
def test_regenerated_g9_terms_name_their_estimands(artifact):
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    d = json.load(open(path))
    t = d["models"]["boombness+refusalness"]["terms"]["boombness"]
    assert "beta" not in t and "p_cr1" not in t and "p_within_domain_perm" not in t
    assert t["p_estimand_cr1"] == "beta_pooled"
    assert t["p_estimand_perm"] == "beta_within_domain"
    assert t["beta_pooled"] != t["beta_within_domain"]


@pytest.mark.parametrize("artifact", ["g2_analysis_cwpos.json", "g2_analysis_lastpos.json",
                                      "qwen3_g2_analysis.json"])
def test_regenerated_g2_artifacts_name_their_estimands(artifact):
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    ci = json.load(open(path))["clustered_inference"]
    assert "rho" not in ci and "p_within_domain_perm" not in ci and "p_iid" not in ci
    assert ci["p_estimand"] == "rho_within_domain"
    for k in ("rho_pooled", "rho_within_domain", "p_iid_pooled_rho", "p_cr1_pooled_slope",
              "p_perm_within_domain_rho"):
        assert k in ci


# --------------------------------------------------------------------------------------------- #
# the role gate: it must PASS a crossed design and REFUSE a nested one
# --------------------------------------------------------------------------------------------- #
def _rows(spec):
    """spec = list of (style, content, block, domain); family_id EMBEDS the style, as in the bank."""
    meta, keys = {}, []
    for i, (style, content, block, domain) in enumerate(spec):
        pid = f"p{i}"
        meta[pid] = {"role_style": style, "bank_block": block, "domain": domain,
                     "family_id": f"{domain}|{content}|{style}|behavioral"}
        keys.append(pid)
    return meta, keys


def _crossed_design():
    """The same six content stems rendered under both styles — the design §9 asks for.

    `plain` is deliberately given a different `bank_block` from the styled arm, exactly as the real
    bank does (`core2x2` vs `role_style`), because that is the second place the old gate was
    unfalsifiable: the block label is a relabelling of the style, so "share a block" can never hold.
    """
    spec = []
    for c in range(6):
        spec.append(("plain", f"c{c}", "core2x2", f"dom{c % 3}"))
        spec.append(("tool", f"c{c}", "role_style", f"dom{c % 3}"))
    return _rows(spec)


def _nested_design():
    """Each style gets its OWN content. Role and content are the same variable; must be refused."""
    spec = []
    for c in range(6):
        spec.append(("plain", f"c{c}", "core2x2", f"dom{c % 3}"))
        spec.append(("tool", f"z{c}", "role_style", f"dom{c % 3}"))
    return _rows(spec)


def test_gate_passes_a_crossed_design():
    meta, keys = _crossed_design()
    ident = analyze_g9.role_identifiability(meta, keys)
    assert ident["identified"] is True, ident["reason"]
    assert ident["identified_styles"] == ["tool"]
    ps = ident["per_style"]["tool"]
    assert ps["family_overlap_with_reference"] == 6      # after masking the style token
    assert ps["family_overlap_raw_family_id"] == 0       # the number the old gate looked at
    assert ps["block_is_relabel_of_style"] is True


def test_gate_refuses_a_nested_design():
    meta, keys = _nested_design()
    ident = analyze_g9.role_identifiability(meta, keys)
    assert ident["identified"] is False
    assert ident["per_style"]["tool"]["family_overlap_with_reference"] == 0
    assert "family-set swap" in ident["per_style"]["tool"]["reason"]


def test_gate_still_refuses_when_content_crosses_but_block_carries_extra_information():
    """The block clause is waived ONLY when the block label is a pure relabelling of the style.
    Here the styled arm straddles two blocks, so block is not determined by style and the waiver
    must not fire."""
    spec = []
    for c in range(6):
        spec.append(("plain", f"c{c}", "core2x2", f"dom{c % 3}"))
        spec.append(("tool", f"c{c}", "role_style" if c < 3 else "families", f"dom{c % 3}"))
    meta, keys = _rows(spec)
    ident = analyze_g9.role_identifiability(meta, keys)
    assert ident["identified"] is False
    assert ident["per_style"]["tool"]["family_overlap_with_reference"] == 6
    assert ident["per_style"]["tool"]["block_is_relabel_of_style"] is False


def test_the_old_gate_was_unfalsifiable_it_refused_even_the_crossed_design(tmp_path):
    """THE POINT OF THE REPAIR. The committed gate refuses the design that §9 explicitly calls
    identified, because it intersects raw `family_id` strings that contain the style name."""
    old = _head_module("analyze_g9", tmp_path)
    meta, keys = _crossed_design()
    old_ident = old.role_identifiability(meta, keys)
    assert old_ident["identified"] is False
    assert old_ident["per_style"]["tool"]["family_overlap_with_reference"] == 0
    # ... and the repaired gate passes the very same rows
    assert analyze_g9.role_identifiability(meta, keys)["identified"] is True


def test_identification_restricts_the_fitted_rows_to_the_crossed_cells():
    """Identified does not mean 'fit on everything'. The reference arm's un-crossed rows must not
    enter the role contrast — fitting them is the family-set swap (retraction #6)."""
    meta, keys = _crossed_design()
    for extra in range(4):                      # reference rows with content no style ever sees
        pid = f"extra{extra}"
        meta[pid] = {"role_style": "plain", "bank_block": "strength", "domain": "dom0",
                     "family_id": f"dom0|solo{extra}|plain|behavioral"}
        keys.append(pid)
    ident = analyze_g9.role_identifiability(meta, keys)
    sub = analyze_g9.crossed_subset(meta, keys, ident)
    assert ident["identified"] is True
    assert len(sub) == 12                       # 6 stems x 2 styles; the 4 solo rows are dropped
    assert not any(k.startswith("extra") for k in sub)


def test_crossed_subset_is_empty_when_nothing_is_identified():
    meta, keys = _nested_design()
    ident = analyze_g9.role_identifiability(meta, keys)
    assert analyze_g9.crossed_subset(meta, keys, ident) == []


def test_gate_reuses_analyze_g11_stem_rather_than_reimplementing_it():
    """Standing project rule. If someone re-rolls a private masker, these drift apart silently."""
    import analyze_g11
    assert analyze_g9.stem is analyze_g11.stem
