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
