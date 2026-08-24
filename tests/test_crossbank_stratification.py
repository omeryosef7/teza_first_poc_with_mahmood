"""The truncation stratification must actually stratify (my own defect, 2026-08-24).

WHAT HAPPENED. `crossbank_knockout_test.py` was written to fix review finding S5 (the headline p had no
persisted artifact). Its S6 control was supposed to re-run every statistic on rows where BOTH arms
terminated normally. It read `r.get("truncated")` from the JUDGE rows.

Judge rows have no truncation field at all -- their keys are strongreject_score, refused, n_chars,
domain, prompt_id, ... and nothing about stopping. So `not None` was always True, `both_eos` always
equalled `common`, and `n_both_terminated` was reported as the full row count on all four banks. A
stratification that never stratified, shipped inside the fix for a review finding.

Truncation lives in `stop_reason` in gens.jsonl ("eos" | "length"). On the main bank that is
eos 71 / length 25 for the baseline and eos 89 / length 7 for the knockout -- so the field is far from
constant, and the bug hid a real 25-row exclusion.

Run:  python -m pytest tests/test_crossbank_stratification.py -q
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness", "crossbank_knockout_test.py")


def test_stratification_reads_stop_reason_not_a_judge_field():
    """THE REGRESSION TEST. Point it back at the judge rows and this goes red."""
    s = open(SRC).read()
    assert 'stop_reason' in s, "the stratification no longer reads stop_reason"
    assert 'SA.get(p) == "eos" and SC.get(p) == "eos"' in s, \
        "both_eos is not computed from stop_reason on BOTH arms"
    # Check the CODE, not the prose: the module docstring quotes `r.get("truncated")` on purpose to
    # explain the defect, and an over-broad match would flag that explanation as the bug returning.
    import ast
    tree = ast.parse(s)
    body = ast.get_docstring(ast.parse(s)) or ""
    code_only = s.replace(body, "")
    assert '.get("truncated")' not in code_only, \
        "the judge-row `truncated` field is back in CODE; it does not exist and always reads None"


def test_a_constant_stop_reason_column_REFUSES():
    """If stop_reason were ever absent, the run must die rather than silently not stratify."""
    s = open(SRC).read()
    assert "REFUSING" in s and "would silently not stratify" in s, \
        "the all-None guard on stop_reason is gone"


def test_judge_rows_really_do_lack_a_truncation_field():
    """Pins the fact the bug depended on, so nobody 'fixes' it back."""
    import glob
    d = sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", "judge", "phj_p4q3A_*")))
    if not d:
        pytest.skip("judge artifact not present")
    row = json.loads(open(os.path.join(d[-1], "results.jsonl")).readline())
    assert "truncated" not in row
    assert "stop_reason" not in row, \
        "judge rows now carry stop_reason; the loader could be simplified, but check it first"


def test_gens_rows_carry_stop_reason_and_it_VARIES():
    """A stratifier is only meaningful if the column it splits on is not constant."""
    import collections
    import glob
    d = sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", "score_behavior", "p4q3A_*")))
    if not d:
        pytest.skip("generation artifact not present")
    c = collections.Counter(json.loads(l)["stop_reason"]
                            for l in open(os.path.join(d[-1], "gens.jsonl")))
    assert set(c) <= {"eos", "length"}, c
    assert len(c) > 1, f"stop_reason is constant ({c}); the S6 control would be vacuous"
    assert c["length"] >= 5, f"only {c['length']} truncated rows; the control has nothing to remove"


def test_manifest_requires_the_generation_dirs():
    """The gens dirs are what make the stratification possible; a 4-field manifest must refuse."""
    s = open(SRC).read()
    assert "len(parts) != 6" in s, "the manifest arity check is gone"
    i = s.index("len(parts) != 6")
    assert "REFUSING" in s[i:i + 300]


def test_bootstrap_resamples_CLUSTERS_not_prompts():
    """C-11: prompts are not the independent unit; pool x domain clusters are."""
    from crossbank_knockout_test import cluster_bootstrap
    out = cluster_bootstrap([-0.2, -0.1, -0.3, -0.15], n_boot=2000)
    assert out["n_clusters"] == 4, "the bootstrap is not resampling the clusters it was given"
    assert out["ci95_lo"] <= out["mean"] <= out["ci95_hi"]
    assert out["frac_boot_ge_zero"] == 0.0, "an all-negative cluster set must never bootstrap above 0"


def test_bootstrap_ci_widens_with_fewer_clusters():
    """Sanity: 4 clusters must give a wider CI than 16 of the same values."""
    from crossbank_knockout_test import cluster_bootstrap
    few = cluster_bootstrap([-0.2, -0.1, -0.3, -0.15], n_boot=4000)
    many = cluster_bootstrap([-0.2, -0.1, -0.3, -0.15] * 4, n_boot=4000)
    assert (few["ci95_hi"] - few["ci95_lo"]) > (many["ci95_hi"] - many["ci95_lo"])


# --------------------------------------------------------------------------- C-14
def test_bootstrap_reports_a_CALIBRATED_interval_too():
    """C-14 S1. A percentile bootstrap of a mean is ~30% too narrow at k=6.

    I published "the CI excludes zero at EVERY clustering unit" on the strength of the percentile
    interval. Under a t-interval it excludes zero at k=24 and k=12 and INCLUDES zero at k=6 and k=4.
    """
    from crossbank_knockout_test import cluster_bootstrap
    v = [-0.1094, -0.3906, 0.0, -0.0781, -0.0625, -0.0312]      # the real domain-6 cell means
    r = cluster_bootstrap(v, n_boot=20000)
    assert "t_ci95_lo" in r and "t_ci95_hi" in r, "the calibrated interval is gone"
    assert r["t_ci95_hi"] > 0 > r["ci95_hi"], (
        "on the real domain-6 data the percentile CI must exclude zero while the t-CI includes it; "
        "if this stops holding the anticonservatism this test exists for has vanished")
    assert r["t_excludes_zero"] is False


def test_the_t_interval_is_wider_than_the_percentile_one_at_small_k():
    from crossbank_knockout_test import cluster_bootstrap
    v = [-0.20, -0.10, -0.30, -0.15, -0.05, -0.25]
    r = cluster_bootstrap(v, n_boot=20000)
    assert (r["t_ci95_hi"] - r["t_ci95_lo"]) > (r["ci95_hi"] - r["ci95_lo"]), \
        "the calibrated interval is not wider than the percentile one; the correction is inert"


def test_tail_floor_is_reported_and_detected():
    """C-14 S2. If every cluster value is <= 0 the tail cannot go below (n_zero/k)^k.

    My reported "0 and 1 of 40000" were exactly that floor and would read the same at an effect of
    -0.001, so the artifact must be visible in the output.
    """
    from crossbank_knockout_test import cluster_bootstrap
    v = [-0.1094, -0.3906, 0.0, -0.0781, -0.0625, -0.0312]
    r = cluster_bootstrap(v, n_boot=40000)
    assert abs(r["tail_floor"] - (1 / 6) ** 6) < 1e-12, "the tail floor is miscomputed"
    assert r["tail_is_at_floor"] is True, "the at-floor condition is not detected on the real data"


def test_a_tiny_effect_hits_the_same_floor_which_is_the_whole_point():
    """The floor is reached by SIGN, not by magnitude -- so it is not evidence of effect size."""
    from crossbank_knockout_test import cluster_bootstrap
    tiny = [-0.001, -0.001, 0.0, -0.001, -0.001, -0.001]
    big = [-0.30, -0.40, 0.0, -0.25, -0.35, -0.20]
    a = cluster_bootstrap(tiny, n_boot=40000)
    b = cluster_bootstrap(big, n_boot=40000)
    assert a["tail_is_at_floor"] and b["tail_is_at_floor"]
    assert abs(a["frac_boot_ge_zero"] - b["frac_boot_ge_zero"]) < 1e-4, (
        "a 300x difference in effect size must produce the SAME tail count; that identity is exactly "
        "why the tail count is not evidence")


# --------------------------------------------------------------------------- C-16
def test_permutation_p_is_flagged_as_sign_only():
    """C-16. I claimed cluster_permutation_on_counts 'weights by evidence'. It does not.

    When every informative cluster agrees in sign, |T| is already the maximum attainable under any
    sign assignment, so exactly 2 assignments match and p = 2/2^k REGARDLESS of the magnitudes. On the
    real data, shrinking every cluster net from (+36,+14,+12,+8,+4,+2,+2) to +-1 left p at 0.0156.
    """
    from crossbank_knockout_test import cluster_permutation_on_counts
    real = {'a': [-1] * 14 + [1] * 2, 'b': [-1] * 3 + [1] * 3, 'c': [-1] * 37 + [1],
            'd': [-1] * 9 + [1], 'e': [-1] * 3 + [1] * 3, 'f': [-1] * 15 + [1],
            'g': [-1] * 8 + [1] * 6, 'h': [-1] * 4, 'i': [-1] * 3 + [1]}
    r = cluster_permutation_on_counts(real)
    assert "magnitude_free_p" in r, "the magnitude-free comparison is gone"
    assert r["p_is_sign_only"] is True, (
        "on this data the p MUST be flagged sign-only; if it is not, either the flag broke or the "
        "saturation condition changed and R-BA's retraction needs revisiting")
    assert abs(r["p"] - r["magnitude_free_p"]) < 1e-12


def test_the_flag_goes_FALSE_when_magnitudes_actually_matter():
    """The flag must discriminate, or it is decoration. Mixed signs -> |T| is not maximal -> the
    magnitudes change which assignments beat it."""
    from crossbank_knockout_test import cluster_permutation_on_counts
    mixed = {'a': [-1] * 30, 'b': [1] * 2, 'c': [-1] * 3, 'd': [1] * 1}
    r = cluster_permutation_on_counts(mixed)
    assert r["p_is_sign_only"] is False, \
        "with mixed signs and unequal magnitudes the p must depend on magnitude; the flag is inert"


def test_leave_one_out_is_floor_determined_and_says_so():
    """C-16: every LOO p came back at 2/2^6. That shows sign agreement survives, not effect size."""
    from crossbank_knockout_test import cluster_permutation_on_counts, leave_one_cluster_out
    real = {'a': [-1] * 14 + [1] * 2, 'b': [-1] * 3 + [1] * 3, 'c': [-1] * 37 + [1],
            'd': [-1] * 9 + [1], 'e': [-1] * 3 + [1] * 3, 'f': [-1] * 15 + [1],
            'g': [-1] * 8 + [1] * 6, 'h': [-1] * 4, 'i': [-1] * 3 + [1]}
    loo = leave_one_cluster_out(real)
    assert abs(loo["worst_p"] - 2 / 2 ** 6) < 1e-12, (
        f"worst LOO p is {loo['worst_p']}, expected the 6-informative floor 2/2^6; if it is no longer "
        "at the floor the LOO analysis has become informative and C-16's caveat can be relaxed")


def test_group_drops_exist_and_are_the_ones_to_quote():
    """C-17. Single-cluster drops are forced to 2/2^(k-1) when signs agree, so they cannot fail.

    R-BA reported "worst LOO 0.0313, robust" on exactly that. The drops that bite are by MODEL and by
    POOL: on the real data the knife pool is 10% of |T| and dropping it takes p from 0.0156 to 0.1250,
    and Llama alone gives 0.1094 against Qwen3's 0.0156.
    """
    from crossbank_knockout_test import leave_one_cluster_out
    cl = {('b', 'a'): [-1] * 14 + [1] * 2, ('b', 'b'): [-1] * 3 + [1] * 3, ('b', 'c'): [-1] * 37 + [1],
          ('b', 'd'): [-1] * 9 + [1], ('b', 'e'): [-1] * 3 + [1] * 3, ('b', 'f'): [-1] * 15 + [1],
          ('k', 'c'): [-1] * 8 + [1] * 6, ('k', 'd'): [-1] * 4, ('k', 'e'): [-1] * 3 + [1]}
    groups = {'knife': [k for k in cl if k[0] == 'k'], 'bomb': [k for k in cl if k[0] == 'b']}
    r = leave_one_cluster_out(cl, groups=groups)
    assert "per_group_p" in r and "worst_p_group" in r, "group drops are gone"
    assert r["worst_p_group"] > r["worst_p"], (
        "the group drop must be STRICTLY harder than the single-cluster drop on this data; if it is "
        "not, the weak test is being presented as robustness again")
    assert r["per_group_p"]["knife"] > 0.05, \
        "dropping the knife pool must lose significance; that is C-17's finding F3"


def test_single_cluster_drop_is_documented_as_weak():
    from crossbank_knockout_test import leave_one_cluster_out
    import inspect
    src = inspect.getsource(leave_one_cluster_out)
    assert "WEAKEST TEST" in src or "incapable of failing" in src, \
        "the docstring no longer warns that single-cluster drops cannot fail"
