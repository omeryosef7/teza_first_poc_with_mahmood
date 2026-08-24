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


def test_manifest_arity_is_checked_and_matches_the_documented_format():
    """The gens dirs make the stratification possible and `model` makes the 2-model analysis possible;
    a short manifest must refuse rather than mis-parse.

    UPDATED 2026-08-24 (C-17 F5): the format gained a leading `model` field, 6 -> 7. The check no
    longer hardcodes a number -- it reads the arity the code enforces and asserts the DOCUMENTED
    format in the module docstring has exactly that many colon-separated fields, so the two can never
    drift apart again.
    """
    import re
    s = open(SRC).read()
    m = re.search(r"len\(parts\) != (\d+)", s)
    assert m, "the manifest arity check is gone"
    n = int(m.group(1))
    i = s.index(m.group(0))
    assert "REFUSING" in s[i:i + 400], "a wrong-arity manifest no longer refuses"
    doc = re.search(r"Manifest lines:\s*(.+)", s)          # whole line: "<A judge>" contains a space
    assert doc, "the manifest format is no longer documented in the docstring"
    n_doc = doc.group(1).strip().count(":") + 1
    assert n_doc == n, f"docstring documents {n_doc} fields but the code enforces {n}"


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


def test_cells_are_keyed_by_MODEL_too():
    """A silent overwrite found 2026-08-24 by cross-checking the tool against a hand computation.

    `cells[(bank, dom)] = ...` had no `model` in the key, so with two models per bank the second
    SILENTLY OVERWROTE the first: a 10-population run computed a Llama-only analysis and reported it
    under a 10-population label. Tool said mean -0.0573; the correct value is -0.0764.
    """
    s = open(SRC).read()
    assert "cells[(model, bank, dom)]" in s, \
        "cells lost `model` from its key; two models per bank will silently overwrite"
    assert 'cellmeta[f"{model}|{bank}|{dom}"]' in s, "cellmeta key must match the cells key"
    assert "cells[(bank, dom)]" not in s, "the un-keyed assignment is back"


def test_aggregations_unpack_the_three_part_key():
    """If the key gains a field, every consumer must unpack it -- otherwise ValueError at best,
    wrong grouping at worst."""
    s = open(SRC).read()
    for pat in ("for (mo, b, d), v in cells.items()", "lambda k: (k[1], k[2])"):
        assert pat in s, f"an aggregation still assumes the 2-part key: {pat!r} missing"


# =========================================================================== #
# C-18 CLOSURE (2026-08-25). Commit 059e819f fixed four defects in this tool and pinned NONE of
# them: the only two tests that mentioned the model-keying bug were string-greps over the source,
# which by construction cannot catch a VALUE regression -- the grep passes whether the number is
# right or wrong. What follows drives the real code.
#
# Fixtures are built from SCALAR FIELDS ONLY (prompt_id, strongreject_score, domain, stop_reason);
# no prompt or completion text is written anywhere in this file.
# =========================================================================== #
def _write_judge(d, ids, score, domains):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for i, pid in enumerate(ids):
            f.write(json.dumps({"prompt_id": pid, "strongreject_score": score,
                                "domain": domains[i % len(domains)]}) + "\n")
    return d


def _write_gens(d, ids, stops):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "gens.jsonl"), "w") as f:
        for i, pid in enumerate(ids):
            f.write(json.dumps({"prompt_id": pid, "stop_reason": stops[i % len(stops)]}) + "\n")
    return d


def _mark_done(d, n):
    with open(os.path.join(d, "DONE.json"), "w") as f:
        json.dump({"schema": "DONE/1", "status": "ok", "rows_written": n,
                   "run_id": os.path.basename(d)}, f)
    return d


def _build_manifest(root, mark_done=True):
    """4 bank NAMES over 2 pool hashes and 2 models -> n_banks 4, n_independent_pools 2."""
    rows = [("Qwen3", "main", "poolAAAAAAAAAAAA"), ("Qwen3", "ticket_bomb", "poolAAAAAAAAAAAA"),
            ("Llama", "button_knife", "poolBBBBBBBBBBBB"), ("Llama", "window_knife", "poolBBBBBBBBBBBB")]
    doms = ["d1", "d2"]
    lines = []
    for model, bank, pool in rows:
        ids = [f"{model}_{bank}_{i}" for i in range(6)]
        dirs = []
        for arm, score in (("A", 0.9), ("C", 0.1)):
            j = _write_judge(os.path.join(root, f"judge_{model}_{bank}_{arm}"), ids, score, doms)
            g = _write_gens(os.path.join(root, f"gens_{model}_{bank}_{arm}"), ids, ["eos", "eos", "length"])
            if mark_done:
                _mark_done(j, len(ids))
                _mark_done(g, len(ids))
            dirs += [j, g]
        # manifest order is model:bank:pool:Ajudge:Cjudge:Agens:Cgens
        ja, ga, jc, gc = dirs[0], dirs[1], dirs[2], dirs[3]
        lines.append(":".join([model, bank, pool, ja, jc, ga, gc]))
    mf = os.path.join(root, "manifest.txt")
    with open(mf, "w") as f:
        f.write("\n".join(lines) + "\n")
    return mf


def _run_tool(manifest, out_root, extra_argv=()):
    """Run the REAL main() with outputs redirected into tmp. Returns the run dir."""
    import glob
    import common
    import crossbank_knockout_test as xb
    old_root, old_argv = common.OUT_ROOT, sys.argv
    common.OUT_ROOT = str(out_root)
    sys.argv = ["crossbank_knockout_test.py", "--manifest", str(manifest), "--tag", "pytest"] \
        + list(extra_argv)
    try:
        assert xb.main() == 0
    finally:
        common.OUT_ROOT, sys.argv = old_root, old_argv
    runs = glob.glob(os.path.join(str(out_root), "crossbank_knockout_test", "*"))
    assert len(runs) == 1, runs
    return runs[0]


@pytest.fixture(scope="module")
def xb_run(tmp_path_factory):
    root = str(tmp_path_factory.mktemp("xb_inputs"))
    mf = _build_manifest(root)
    run = _run_tool(mf, str(tmp_path_factory.mktemp("xb_out")))
    with open(os.path.join(run, "summary.json")) as f:
        summ = json.load(f)
    with open(os.path.join(run, "crossbank_test.json")) as f:
        art = json.load(f)
    with open(os.path.join(run, "metadata.json")) as f:
        meta = json.load(f)
    return {"run": run, "summary": summ, "artifact": art, "metadata": meta}


# --------------------------------------------------------------- C-18 fix 1
def test_n_independent_pools_counts_POOLS_not_banks(xb_run):
    """The manifest tuple is (model, bank, pool, ...) and the count read field 2, the BANK, so every
    artifact this tool ever wrote reported n_independent_pools == n_banks -- the one number the C-11
    independence argument turns on."""
    s = xb_run["summary"]
    assert s["n_banks"] == 4, s
    assert s["n_independent_pools"] == 2, (
        "4 bank names over 2 pool hashes must report 2 independent pools; "
        f"got {s['n_independent_pools']} -- the count is reading the bank field again")


def test_distinct_pools_helper_reads_field_three():
    """Same defect at the unit the tool actually calls (not a copy of the expression)."""
    from crossbank_knockout_test import distinct_pools
    entries = [("Q", "main", "pA", "1", "2", "3", "4"), ("Q", "ticket", "pA", "1", "2", "3", "4"),
               ("L", "knife", "pB", "1", "2", "3", "4"), ("L", "window", "pB", "1", "2", "3", "4")]
    assert distinct_pools(entries) == ["pA", "pB"]


# --------------------------------------------------------------- C-18 fix 2
def test_asr_rows_are_keyed_by_model_AND_bank_with_distinct_values():
    """Keyed on bank alone the second model SILENTLY OVERWROTE the first, so a 10-population run
    emitted 5 asr rows under a 10-population label.

    The two rows carry deliberately DIFFERENT values: a same-value fixture would pass under the bug.
    """
    from crossbank_knockout_test import asr_rows
    banks = [{"model": "Q", "bank": "main", "baseline_asr": 0.90, "knockout_asr": 0.10},
             {"model": "L", "bank": "main", "baseline_asr": 0.20, "knockout_asr": 0.15}]
    r = asr_rows(banks)
    assert len(r) == 2, f"one bank name over two models collapsed to {len(r)} row(s): {r}"
    assert r["asr_Q_main"] == [0.90, 0.10]
    assert r["asr_L_main"] == [0.20, 0.15]


def test_the_written_summary_carries_one_asr_row_per_population(xb_run):
    s = xb_run["summary"]
    rows = {k: v for k, v in s.items() if k.startswith("asr_")}
    assert len(rows) == 4, f"4 populations must write 4 asr rows, got {sorted(rows)}"
    assert set(rows) == {"asr_Qwen3_main", "asr_Qwen3_ticket_bomb",
                         "asr_Llama_button_knife", "asr_Llama_window_knife"}


# --------------------------------------------------------------- C-18 fix 3
def test_t_table_has_df_17_and_is_monotone():
    """df=17 is the k=18 the headline used; the sparse table had no entry and fell back to a formula
    that was anticonservative by 4.3% of the reported margin."""
    from crossbank_knockout_test import _T, t_crit_95
    assert 17 in _T, "df=17 is missing again -- that is exactly the k the headline used"
    ts = [t_crit_95(k - 1) for k in range(2, 201)]
    assert all(a >= b - 1e-12 for a, b in zip(ts, ts[1:])), \
        "the critical value must never RISE with df; the interpolation is running backwards"


def test_t_table_is_never_below_the_true_t():
    """An interval built on a t below the true one is anticonservative, which is the entire defect
    C-14 and REVIEW-8 finding 5 were about."""
    try:
        from scipy.stats import t as _t
    except Exception:                                    # pragma: no cover
        pytest.skip("scipy not available")
    from crossbank_knockout_test import t_crit_95
    for df in range(1, 41):
        assert t_crit_95(df) >= _t.ppf(0.975, df) - 1e-9, \
            f"df={df}: table {t_crit_95(df)} < true {_t.ppf(0.975, df)} -- ANTICONSERVATIVE"


def test_a_single_cluster_does_not_CRASH_the_tool():
    """df = k-1 = 0 is in neither the table nor its interpolation range: `lo` fell back to 1 and `hi`
    came out 1, so the interpolation divided by zero and took the whole run down."""
    from crossbank_knockout_test import cluster_bootstrap
    r = cluster_bootstrap([-0.25], n_boot=100)
    assert r["degenerate"] is True
    assert r["n_clusters"] == 1 and r["t_df"] == 0
    assert r["t_ci95_lo"] == float("-inf") and r["t_ci95_hi"] == float("inf")
    assert r["t_excludes_zero"] is False, \
        "one cluster can never exclude zero; a degenerate record must not claim significance"
    assert cluster_bootstrap([], n_boot=10)["degenerate"] is True


# --------------------------------------------------------------- C-18 fix 4
def test_the_C18_verdict_is_IN_THE_JSON_at_every_threshold(xb_run):
    """A warning that is only printed dies with the terminal scrollback. The retraction has to be in
    the artifact a reader opens."""
    blocks = xb_run["artifact"]["by_threshold"]
    assert set(blocks) == {"0.25", "0.5", "0.75"}, sorted(blocks)
    for thr, blk in blocks.items():
        v = blk["levels"]["pool_x_domain"]["VERDICT"]
        assert "C-18" in v, f"threshold {thr}: pool_x_domain carries no C-18 verdict ({v!r})"
        assert "NOT a defensible headline" in v, f"threshold {thr}: the retraction is gone ({v!r})"


# --------------------------------------------------------------- gap 5
def test_an_input_without_DONE_is_REFUSED_by_default(tmp_path):
    """require_done existed since 2026-08-17 and this tool -- which turns those runs into the
    headline p -- checked none of the four directories each manifest row names."""
    root = str(tmp_path / "in")
    os.makedirs(root)
    mf = _build_manifest(root, mark_done=False)
    with pytest.raises(SystemExit) as e:
        _run_tool(mf, str(tmp_path / "out1"))
    assert "DONE" in str(e.value), str(e.value)[:200]


def test_the_same_input_is_accepted_with_allow_partial_inputs(tmp_path):
    root = str(tmp_path / "in")
    os.makedirs(root)
    mf = _build_manifest(root, mark_done=False)
    run = _run_tool(mf, str(tmp_path / "out2"), extra_argv=["--allow-partial-inputs"])
    assert os.path.exists(os.path.join(run, "summary.json"))


def test_input_row_counts_travel_into_the_artifact_as_provenance(xb_run):
    """A headline over a truncated input must be detectable from the artifact alone."""
    prov = xb_run["metadata"]["input_provenance"]
    assert len(prov) == 16, f"4 rows x 4 dirs = 16 inputs, got {len(prov)}"
    assert all(v["rows_written"] == 6 for v in prov.values()), prov
    assert xb_run["metadata"]["allow_partial_inputs"] is False


# --------------------------------------------------------------- gap 6
def test_summary_marks_the_retracted_statistic_and_names_a_defensible_headline(xb_run):
    """`headline_p_pool_x_domain` is the key a reader greps, and C-18 retracted the statistic it
    names. The key stays (backward compatibility) but the retraction now travels with it."""
    s = xb_run["summary"]
    assert "headline_p_pool_x_domain" in s, "an existing artifact key was removed"
    assert s["p_pool_x_domain_RETRACTED_C18"] == s["headline_p_pool_x_domain"], \
        "the retraction marker must carry the SAME value, or it marks nothing"
    assert s["headline_estimand"] == "domain_only (defensible marginal, C-17/C-18)"
    assert s["headline_p"] == \
        xb_run["artifact"]["by_threshold"]["0.5"]["levels"]["domain_only"]["p"], \
        "headline_p must be the domain_only marginal at threshold 0.5"
