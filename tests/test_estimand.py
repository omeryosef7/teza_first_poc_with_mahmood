"""test_estimand.py — the guards for audit T5 (estimand pairing), plan §9 decision question 5
(controlling for the number of demonstrations), and the role-identifiability gate that could not
fail.

EVERY TEST HERE FAILS AGAINST THE PRE-FIX CODE, and each one proves that by loading the PRE-FIX
revision of the module -- pinned by sha in `PRE_FIX_SHA`, never `HEAD` -- beside the working-tree
one and asserting the old behaviour explicitly. That is deliberate: three of these defects are of
the "the code is silent, the reader supplies the wrong meaning" kind, so a test that only pins the
new behaviour would not show that anything was ever wrong.

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


# The pre-fix revision of each module, PINNED BY SHA -- never `HEAD`.
#
# The `test_pre_fix_*` tests originally read `HEAD:src/boombness/<mod>.py`. `HEAD` is an
# INCIDENTAL PROPERTY: it means "pre-fix" only until the fix is committed, and the moment it
# was (e42f5fc4) all four of them went red against their own subject. That is exactly the trap the standing project rule names --
# pin the pre-fix revision by sha, or committing the fix turns its own test red -- and it had
# already sprung. Addressed by identity now: the last revision of each file before the fix commit,
# named explicitly, with `test_the_pinned_revisions_really_are_the_parents_of_the_fix_commit`
# checking that the pin still IS that revision.
#
#   e42f5fc4  the commit that landed the T5 / n_examples / role-gate fixes in BOTH files
#   50360b74  its predecessor for analyze_g9.py  (last revision carrying the defects)
#   b093e50d  its predecessor for analyze_g2.py  (last revision carrying the defects)
#   6101cdcf  the commit that made analyze_g8.t_sf scipy-backed (T4)
#   dd158330  its predecessor for analyze_g8.py -- the `t_sf` that published 0.7656
#
# `FIX_COMMIT_OF` maps the module to the commit that fixed it, so the ancestry guard below can
# check every pin against the right fix rather than assuming one commit fixed everything.
FIX_COMMIT_OF = {"analyze_g9": "e42f5fc4", "analyze_g2": "e42f5fc4", "analyze_g8": "6101cdcf"}
PRE_FIX_SHA = {"analyze_g9": "50360b74", "analyze_g2": "b093e50d", "analyze_g8": "dd158330"}


def _pre_fix_source(name):
    """The text of the module AS IT WAS BEFORE THE FIX. Pinned by sha, not by HEAD."""
    return subprocess.check_output(
        ["git", "show", "%s:src/boombness/%s.py" % (PRE_FIX_SHA[name], name)], cwd=ROOT).decode()


def _pre_fix_module(name, tmp_path):
    """Import the PRE-FIX version of a module, so a test can assert what the defect used to do."""
    path = tmp_path / ("prefix_%s.py" % name)
    path.write_text(_pre_fix_source(name))
    spec = importlib.util.spec_from_file_location("prefix_%s" % name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_the_pinned_revisions_really_are_the_parents_of_the_fix_commit():
    """A guard on the guards. If PRE_FIX_SHA is ever repointed at a revision that already contains
    the fix, every `test_pre_fix_*` below silently stops proving anything -- which is precisely how
    the HEAD-pinned version of this file died. Checked by identity, against the fix commit."""
    for name, sha in PRE_FIX_SHA.items():
        parent = subprocess.check_output(
            ["git", "rev-list", "-1", FIX_COMMIT_OF[name] + "^", "--",
             "src/boombness/%s.py" % name], cwd=ROOT).decode().strip()
        resolved = subprocess.check_output(["git", "rev-parse", sha], cwd=ROOT).decode().strip()
        assert resolved == parent, (
            "%s: PRE_FIX_SHA %s is not the last revision before the fix (%s)" % (name, sha, parent))


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
    old = _pre_fix_module("analyze_g2", tmp_path)
    assert not hasattr(old, "rank_corr_pair"), (
        "the committed analyze_g2 has a rank_corr_pair — this test is no longer proving anything")
    # and the old artifact contract paired a pooled rho with a within-domain p under bare names
    src = _pre_fix_source("analyze_g2")
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
    old = _pre_fix_module("analyze_g9", tmp_path)
    assert not hasattr(old, "within_cluster_beta")
    assert not hasattr(old, "demean_within"), (
        "demeaning lived inside the permutation as a closure, which is why the reported point "
        "estimate could not be put on the same footing")


# --------------------------------------------------------------------------------------------- #
# plan §9 decision question 5 — n_examples must be a REGRESSOR, not only a filter
# --------------------------------------------------------------------------------------------- #
def test_pre_fix_g9_never_used_n_examples_as_a_regressor():
    src = _pre_fix_source("analyze_g9")
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
    old = _pre_fix_module("analyze_g9", tmp_path)
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


# --------------------------------------------------------------------------------------------- #
# C-2 / T4 — every clustered p in the committed g9 artifacts must reproduce scipy from its own
# (t, df). This is the ONE place in the sprint where the pre-fix `t_sf` actually corrupted a
# published number, so it gets a test that names the casualty.
# --------------------------------------------------------------------------------------------- #
# The two g9 artifacts that exist today. This is an ANCHOR, not the enumeration: it exists only so
# that a discovery function which silently returns nothing cannot make every test below vacuously
# green (the empty-collection short circuit is one of this project's named bug classes). The
# enumeration itself is `g9_artifacts()`, which discovers by identity.
G9_ARTIFACTS_KNOWN = ["g9_three_predictor_cwpos.json", "g9_three_predictor_lastpos.json"]

OUTDIR = os.path.join(ROOT, "outputs", "boombness")


def _is_g9_artifact(obj):
    """Is this JSON object something `analyze_g9.py` produced? Asked by IDENTITY, two ways.

    A hand-maintained filename list is an INCIDENTAL PROPERTY: the third g9 artifact would simply
    not be in it, and every test keyed on the list would stay green while shipping a number with no
    committed recipe. That is the shape of all six dead guards in this project.

    Primary identity: the artifact's own provenance says which script wrote it. Fallback for the
    pre-provenance artifacts (which is exactly the C-10 hole): the structural signature that only
    this script emits -- plan section 9 together with the role-identifiability block. Nothing else
    under outputs/boombness/ carries either, checked over all 35 committed analysis JSONs.
    """
    if not isinstance(obj, dict):
        return False
    argv = (obj.get("provenance") or {}).get("argv") or []
    if argv and os.path.basename(str(argv[0])) == "analyze_g9.py":
        return True
    return str(obj.get("plan_section")) == "9" and "role_identifiability" in obj


def g9_artifacts():
    """Every g9 artifact present on disk OR tracked in git, discovered by identity.

    A tracked artifact that is missing from the working tree is read out of git rather than
    skipped: a committed number whose file has been deleted still needs a committed recipe, and
    dropping it here would be a silent skip -- the thing this project's ledger rule forbids.
    """
    names = set(os.listdir(OUTDIR)) if os.path.isdir(OUTDIR) else set()
    tracked = {os.path.basename(t) for t in
               subprocess.check_output(["git", "ls-files", "outputs/boombness"],
                                       cwd=ROOT).decode().split()
               if os.path.dirname(t) == "outputs/boombness"}
    found = []
    for name in sorted(names | tracked):
        if not name.endswith(".json"):
            continue
        path = os.path.join(OUTDIR, name)
        try:
            if os.path.isfile(path):
                obj = json.load(open(path))
            else:
                obj = json.loads(subprocess.check_output(
                    ["git", "show", "HEAD:outputs/boombness/" + name], cwd=ROOT).decode())
        except (ValueError, OSError, subprocess.CalledProcessError):
            continue
        if _is_g9_artifact(obj):
            found.append(name)
    return found


# parametrisation is over the DISCOVERED set, so a new g9 artifact is covered by every test below
# the moment it lands, rather than the moment somebody remembers to edit a list.
G9_ARTIFACTS = g9_artifacts() or list(G9_ARTIFACTS_KNOWN)

# the single published casualty, from the continuation log's C-2 sweep of all 726 artifacts
C2_CASUALTY = {"artifact": "g9_three_predictor_lastpos.json",
               "model": "boombness+refusalness", "term": "refusalness",
               "t": 0.011383535164266073, "df": 5,
               "published_before_the_fix": 0.7656066841105736}


def test_g9_delegates_its_t_reference_to_the_fixed_analyze_g8():
    """g9 has no t distribution of its own; it imports analyze_g8's. If that import ever breaks or
    is quietly re-rolled locally, g9's clustered p-values silently stop being scipy-backed."""
    from scipy import stats as st
    import analyze_g8
    assert analyze_g9.t_sf_2sided.__module__ == "analyze_g9"
    for t, df in [(0.0, 5), (0.01138, 5), (0.08, 5), (1.0, 5), (1.464, 5), (2.571, 5),
                  (0.001, 3), (5.0, 233)]:
        assert analyze_g9.t_sf_2sided(t, df) == pytest.approx(2 * st.t.sf(abs(t), df), rel=1e-12)
        assert analyze_g8.t_sf(abs(t), df) == pytest.approx(2 * st.t.sf(abs(t), df), rel=1e-12)


def test_pre_fix_t_reference_really_did_corrupt_the_one_published_p(tmp_path):
    """FAILS AGAINST THE PRE-FIX CODE by construction: it loads the pre-fix `t_sf` and shows it
    returning the number that was published, which the fixed code does not return."""
    old = _pre_fix_module("analyze_g8", tmp_path)
    c = C2_CASUALTY
    assert old.t_sf(c["t"], c["df"]) == pytest.approx(c["published_before_the_fix"], rel=1e-9)
    # and the current path does NOT reproduce it — the correction is real and is ~0.23 wide
    now = analyze_g9.t_sf_2sided(c["t"], c["df"])
    assert now == pytest.approx(0.9913576917769514, rel=1e-12)
    assert abs(now - c["published_before_the_fix"]) > 0.2


@pytest.mark.parametrize("artifact", G9_ARTIFACTS)
def test_every_published_clustered_p_reproduces_scipy_from_its_own_t_and_df(artifact):
    """Not just the casualty: EVERY term in both artifacts, checked against its own recorded t and
    the df its own `reference` string names. A p that no longer follows from its own t is either a
    stale artifact or a changed estimator, and either way must not ship silently."""
    from scipy import stats as st
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    d = json.load(open(path))
    checked = 0
    for mname, m in d["models"].items():
        if "error" in m:
            continue
        for lab, term in m["terms"].items():
            p = term.get("p_cr1_pooled_beta")
            if p is None:
                assert term["cr1_rank_deficient"] is True, (mname, lab)
                continue
            df = int(term["reference"].split("=")[1].rstrip(")"))
            assert p == pytest.approx(2 * st.t.sf(abs(term["t"]), df), rel=1e-9), (mname, lab)
            assert term["t"] == pytest.approx(term["beta_pooled"] / term["se_cr1"], rel=1e-9)
            checked += 1
    assert checked >= 10, f"only {checked} clustered p-values checked in {artifact}"


@pytest.mark.parametrize("artifact", G9_ARTIFACTS)
def test_the_c2_casualty_now_carries_the_corrected_value(artifact):
    """The continuation log's C-2 says the corrected value is 0.9914 and that it makes an already
    null term MORE null. Pin both halves so a regression cannot quietly restore 0.7656."""
    c = C2_CASUALTY
    if artifact != c["artifact"]:
        pytest.skip("the casualty is in the lastpos artifact only")
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    term = json.load(open(path))["models"][c["model"]]["terms"][c["term"]]
    assert term["t"] == pytest.approx(c["t"], rel=1e-9)
    assert term["reference"] == f"t(df={c['df']})"
    assert term["p_cr1_pooled_beta"] == pytest.approx(0.9913576917769514, rel=1e-9)
    assert term["p_cr1_pooled_beta"] > c["published_before_the_fix"]   # more null, not less


# --------------------------------------------------------------------------------------------- #
# C-10 — the canonical invocation must be COMMITTED, and must be the one that made the artifacts
# --------------------------------------------------------------------------------------------- #
def test_the_g9_artifact_discovery_finds_the_artifacts_we_know_about():
    """Anti-vacuity anchor for `g9_artifacts()`. A discovery function that quietly returns [] would
    turn the coverage guard below into a guard that passes because it checked nothing."""
    found = g9_artifacts()
    assert set(G9_ARTIFACTS_KNOWN) <= set(found), (G9_ARTIFACTS_KNOWN, found)


def test_the_g9_artifact_discovery_does_not_claim_other_scripts_artifacts():
    """...and the other direction: identity must not be so loose that g2/g8/g11 artifacts match."""
    found = set(g9_artifacts())
    for other in ("g2_analysis_cwpos.json", "g8_comprehension_by_nexamples.json",
                  "g11_role_full.json", "position_2x2.json"):
        if os.path.exists(os.path.join(OUTDIR, other)):
            assert other not in found, other


def test_canonical_runs_cover_every_committed_g9_artifact():
    """Keyed by artifact identity, so a new artifact with no recipe is caught rather than ignored.

    THE ORIGINAL VERSION OF THIS TEST DID NOT DO THAT. It iterated a hardcoded two-element list, so
    a third g9 artifact shipped without a recipe left it green -- the exact failure its own
    docstring claimed to prevent. The second half below is the case it should FAIL, executed.
    """
    present = g9_artifacts()
    assert present, "no g9 artifact on disk at all"
    for a in present:
        assert a in analyze_g9.CANONICAL_RUNS, f"{a} has no committed invocation"
        assert analyze_g9.CANONICAL_RUNS[a][-2:] == ["--out", f"outputs/boombness/{a}"], (
            f"{a}'s recipe does not write {a} — the key and the recipe disagree")
    # THE CASE THIS GUARD MUST FAIL, executed: a g9 artifact on disk that CANONICAL_RUNS has never
    # heard of. Tried once per identity route, because a discovery that only knows one of them is
    # half a guard. Synthetic minimal artifacts, so no published number is ever duplicated on disk.
    routes = {
        "g9_UNRECORDED_by_provenance.json":
            {"provenance": {"argv": ["src/boombness/analyze_g9.py", "--out", "x"]}},
        "g9_UNRECORDED_by_structure.json":
            {"plan_section": "9", "role_identifiability": {"identified": False}},
    }
    for novel, body in routes.items():
        dst = os.path.join(OUTDIR, novel)
        assert not os.path.exists(dst)
        assert novel not in analyze_g9.CANONICAL_RUNS
        with open(dst, "w") as fh:
            json.dump(body, fh)
        try:
            assert novel in g9_artifacts(), f"discovery did not see {novel}"
            with pytest.raises(AssertionError):
                for a in g9_artifacts():
                    assert a in analyze_g9.CANONICAL_RUNS, f"{a} has no committed invocation"
        finally:
            os.remove(dst)


@pytest.mark.parametrize("artifact", G9_ARTIFACTS)
def test_canonical_runs_match_the_committed_artifact_provenance(artifact):
    """The recipe and the artifact cannot drift: the artifact records the argv it was made with,
    and it must be the argv the committed recipe would replay."""
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    d = json.load(open(path))
    prov = d["provenance"]
    for k in ("argv", "git_commit", "git_dirty", "python"):
        assert k in prov, f"{artifact} provenance is missing {k}"
    assert prov["argv"][1:] == analyze_g9.CANONICAL_RUNS[artifact], (
        f"{artifact} was made with an argv the committed recipe does not reproduce")
    # the recipe's directory flags must also be the ones the artifact echoes as its own keys
    argv = prov["argv"]
    for flag, key in (("--judge", "judge"), ("--extract", "extract"),
                      ("--refusalness", "refusalness")):
        rel = argv[argv.index(flag) + 1]
        # The recipe must be RELATIVE to the repo root, or it is not a recipe anyone else can run.
        # Asserted explicitly because the original `d[key] == os.path.join(ROOT, rel)` could not
        # notice: os.path.join swallows its first argument when the second is absolute, so an
        # absolute path in CANONICAL_RUNS would have passed silently.
        assert not os.path.isabs(rel), f"{flag} in the recipe is absolute: {rel}"
        # and the artifact's recorded input is that same directory. Compared by the relative
        # identity, not by this checkout's absolute path, which the artifact bakes in and which
        # differs for anyone who clones the repo somewhere else.
        assert d[key].endswith(os.sep + rel) or d[key] == os.path.join(ROOT, rel), (
            key, d[key], rel)
    # (whether those directories still exist on disk is asserted by the regeneration test below,
    # which skips rather than fails when a run has been archived off the filesystem)


def test_print_canonical_answers_without_the_required_flags():
    """The recipe has to be discoverable from the script alone. If `--print-canonical` needed
    --judge/--extract/--refusalness, you could only get the invocation by already having it."""
    r = subprocess.run([sys.executable, os.path.join(SRC, "analyze_g9.py"), "--print-canonical"],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    for a in G9_ARTIFACTS:
        assert f"--out outputs/boombness/{a}" in r.stdout, a
    assert analyze_g9.CANONICAL_PYTHON in r.stdout


def test_print_canonical_is_resolved_by_argparse_not_by_exact_spelling(tmp_path):
    """ONE-OF-TWO-PATHS. The flag was matched with `"--print-canonical" in sys.argv[1:]` -- by its
    exact spelling. argparse accepts any unambiguous prefix, so `--print-can` set
    `args.print_canonical = True` on the parsed path where NOTHING read it: with the required flags
    supplied the script ran the entire analysis and wrote --out; without them it died with a
    "required arguments" error that never mentions the flag you asked for. Both halves below fail
    against that version."""
    exe = os.path.join(SRC, "analyze_g9.py")
    # (a) the abbreviation alone must print the recipe, not an argparse usage error
    r = subprocess.run([sys.executable, exe, "--print-can"], cwd=ROOT,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-2000:]
    assert r.stdout == subprocess.run([sys.executable, exe, "--print-canonical"], cwd=ROOT,
                                      capture_output=True, text=True).stdout
    # (b) the abbreviation ALONGSIDE the required flags must still short-circuit and must not
    #     touch --out. The input dirs are deliberately nonexistent: pre-fix this reached
    #     require_done and exited non-zero, post-fix it never gets there.
    out = tmp_path / "must_not_be_written.json"
    r = subprocess.run([sys.executable, exe, "--print-can",
                        "--judge", str(tmp_path / "nope"), "--extract", str(tmp_path / "nope"),
                        "--refusalness", str(tmp_path / "nope"), "--position", "last",
                        "--out", str(out)], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, (r.returncode, r.stderr[-2000:])
    assert "--judge" in r.stdout
    assert not out.exists(), "--print-canonical ran the analysis instead of short-circuiting"
    # (c) and the pre-pass must not INVENT a resolution the real parser rejects. `--p` is ambiguous
    #     between --print-canonical and --position; a separately-written pre-parser that only knows
    #     --print-canonical resolves it, so a typo for --position would become a silent exit-0
    #     no-op that writes nothing. It must stay an error. This is why `build_parser` is one
    #     definition with `required` relaxed, rather than a second hand-written parser.
    r = subprocess.run([sys.executable, exe, "--p"], cwd=ROOT, capture_output=True, text=True)
    assert r.returncode != 0, r.stdout[-500:]
    assert "ambiguous" in r.stderr, r.stderr[-500:]


def test_pre_fix_g9_had_no_provenance_and_no_committed_invocation(tmp_path):
    """C-10 as stated: before the fix the script recorded no argv and no commit, and no committed
    invocation of it existed anywhere in the repo. Both halves fail against the pre-fix code."""
    old = _pre_fix_module("analyze_g9", tmp_path)
    assert not hasattr(old, "CANONICAL_RUNS")
    assert not hasattr(old, "canonical_commands")
    src = _pre_fix_source("analyze_g9")
    assert '"provenance"' not in src and "git_commit" not in src
    # ...and at that revision NOTHING committed anywhere in the repo was an INVOCATION of it.
    # The script name is mentioned in three docs, but a mention is not a recipe: an invocation is
    # a line that also carries the flags that decide the numbers. That is the C-10 finding, and it
    # is asserted on the property that matters (does any committed line name the script AND pass
    # it inputs?) rather than on "does the string appear".
    hits = subprocess.run(["git", "grep", "-n", "analyze_g9.py", PRE_FIX_SHA["analyze_g9"]],
                          cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    assert hits, "sanity: the script existed at that revision"
    invocations = [h for h in hits if "--judge" in h or "--extract" in h or "--refusalness" in h]
    assert not invocations, invocations
    # the working tree now has one, in a committed source file, and it is executable
    assert analyze_g9.CANONICAL_RUNS and analyze_g9.canonical_commands().startswith("#")
    recipe = analyze_g9.canonical_commands()
    assert "--judge" in recipe and "--extract" in recipe and "--refusalness" in recipe


@pytest.mark.parametrize("artifact", G9_ARTIFACTS)
def test_the_committed_recipe_actually_regenerates_the_artifact(tmp_path, artifact):
    """The whole point of C-10: every number must be regenerable by a committed script from a
    committed artifact. Replays `CANONICAL_RUNS[artifact]` verbatim (only --out redirected) and
    diffs EVERY leaf field against the committed file. Provenance is excluded because argv and
    commit are properties of the replay, not of the result."""
    path = os.path.join(ROOT, "outputs", "boombness", artifact)
    if not os.path.exists(path):
        pytest.skip(f"{artifact} not present")
    argv = list(analyze_g9.CANONICAL_RUNS[artifact])
    for flag in ("--judge", "--extract", "--refusalness"):
        d = os.path.join(ROOT, argv[argv.index(flag) + 1])
        if not os.path.isdir(d):
            pytest.skip(f"input run {d} not present")
    argv[argv.index("--out") + 1] = str(tmp_path / artifact)
    r = subprocess.run([sys.executable, os.path.join(SRC, "analyze_g9.py"), *argv],
                       cwd=ROOT, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr[-3000:]
    got = json.load(open(tmp_path / artifact))
    want = json.load(open(path))
    got.pop("provenance"), want.pop("provenance")
    # `judge`/`extract`/`refusalness` are stored as os.path.abspath, i.e. they carry the absolute
    # path of whichever checkout produced the file. Comparing those verbatim would make this test
    # go red for anyone who clones the repo to a different directory, for a reason that has nothing
    # to do with the numbers. Compare them by the identity that is actually asserted -- the run
    # directory under outputs/ -- and fail loudly if that marker is missing rather than skipping.
    for side in (got, want):
        for k in ("judge", "extract", "refusalness"):
            marker = "outputs" + os.sep + "boombness" + os.sep
            assert marker in side[k], (k, side[k])
            side[k] = side[k].split(marker, 1)[1]

    def leaves(o, p=""):
        if isinstance(o, dict):
            for k, v in o.items():
                yield from leaves(v, f"{p}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                yield from leaves(v, f"{p}[{i}]")
        else:
            yield p, o
    a, b = dict(leaves(want)), dict(leaves(got))
    assert set(a) == set(b), sorted(set(a) ^ set(b))[:20]
    bad = {k: (a[k], b[k]) for k in a
           if not (a[k] == b[k] or (isinstance(a[k], float) and isinstance(b[k], float)
                                    and a[k] == pytest.approx(b[k], rel=1e-12)))}
    assert not bad, bad
    assert len(a) > 400, f"only {len(a)} leaf fields compared"
