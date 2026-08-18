"""Guards for the two selection/control defects in `src/boombness/probes.py`.

Both defects were reported by the 2026-08-18 external critique and both are the kind that leave a
publishable-looking number behind:

  T6b  `best_layer_by_auroc` was the argmax of the per-layer TEST AUROC over ~10 layers with no
       validation split, and that layer's test AUROC was the reported result. The maximum of ten
       noisy estimates is biased upward, and nothing in the artifact told a reader by how much or
       even over how many layers the max had been taken.
  T9b  the shuffled-label control drew ONE permutation per layer (`RandomState(seed + L)`, re-seeded
       identically in every fold) and printed it in a column next to the real AUROC as if it were a
       null band. A point has no draw-to-draw variance, so every comparison against it understated
       the null's spread — the same mistake retraction #7 had already documented for the G4 steering
       band (between-draw sd 0.0301).

Every test here is written so it FAILS against `git show HEAD:src/boombness/probes.py`. The failure
is numeric wherever a numeric failure is possible: the null-distribution tests fall back to calling
the old `run_regime` K times, which is exactly what "one draw" means, and observe sd == 0.

Run:
  <interp> -m pytest tests/test_probes_selection.py -q
  PROBES_MODULE=/tmp/old_probes.py <interp> -m pytest tests/test_probes_selection.py -q   # must fail
"""
from __future__ import annotations

import importlib.util
import math
import os
import sys

import numpy as np
import pytest

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "boombness")
sys.path.insert(0, SRC)


def _load():
    path = os.environ.get("PROBES_MODULE", os.path.join(SRC, "probes.py"))
    spec = importlib.util.spec_from_file_location("probes_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probes = _load()

N_LAYERS = 10
DIM = 20
DOMAINS = [f"dom{i}" for i in range(6)]
REGIME = "d5_surface_matched_codeword"


def synthetic(seed: int = 7):
    """Pure-noise features: labels are independent of the representations at EVERY layer.

    That is the setting in which the two defects are visible and quantifiable — the honest AUROC is
    0.5 at every layer, so any headline above chance is selection, and any shuffled control above
    chance is a permutation that got lucky rather than a leak.
    """
    rng = np.random.RandomState(seed)
    table, reps = [], {}
    for d in DOMAINS:
        for j in range(12):
            pid = f"{d}_{j}"
            cell = "C" if j % 2 == 0 else "A"
            table.append({"prompt_id": pid, "cell": cell, "condition": "cond", "domain": d,
                          "split": "dev", "family_id": f"{d}_fam{j // 4}", "n_examples": 4,
                          "bank_block": "core2x2", "query_kind": "q",
                          "y": 1 if cell in probes.CONCEPT_CELLS else 0})
            reps[pid] = rng.randn(N_LAYERS, DIM).astype(np.float32)
    layers = list(range(N_LAYERS))
    return table, reps, layers, {L: L for L in layers}


def _null_aurocs(table, reps, layers, layer_index, k=24, seed=11):
    """Per-layer list of shuffled AUROCs over k draws — via the new API when it exists, else by
    calling the old single-draw `run_regime` k times, which is precisely what the old code could
    offer as a 'null'."""
    if hasattr(probes, "shuffled_null_distribution"):
        nd = probes.shuffled_null_distribution(REGIME, table, reps, layers, layer_index, 3, seed,
                                               n_components=8, n_draws=k)
        return {L: v["draws"] for L, v in nd["per_layer"].items()}, nd
    out = {L: [] for L in layers}
    for _ in range(k):
        r = probes.run_regime(REGIME, table, reps, layers, layer_index, 3, seed,
                              shuffle_labels=True, n_components=8)
        for L, v in r["per_layer"].items():
            out[L].append(v["auroc"])
    return out, None


# --------------------------------------------------------------------------- T9b
def test_null_control_has_between_draw_variance():
    """A null must be a distribution. The old control redrew the SAME permutation every time, so
    its between-draw sd is exactly 0.0 and any band built from it is fictitious."""
    table, reps, layers, li = synthetic()
    draws, nd = _null_aurocs(table, reps, layers, li, k=24)
    sds = [float(np.std(np.asarray(v), ddof=1)) for v in draws.values() if len(v) > 1]
    assert sds, "no layer produced repeated null draws at all"
    assert max(sds) > 0.01, (
        f"between-draw sd of the shuffled null is {max(sds):.6f} — the control is a single point "
        "redrawn identically, not a distribution (defect T9b)")
    assert nd is not None, "module exposes no shuffled_null_distribution(); the null is not a distribution"
    assert nd["n_draws"] == 24
    for L, v in nd["per_layer"].items():
        assert v["n_draws"] == 24
        assert set(v["quantiles"]) >= {"q0.05", "q0.5", "q0.95"}, "empirical quantiles not reported"
        assert v["sd"] == v["sd"] and v["se"] == v["se"]


def test_null_draws_is_a_cli_argument():
    ap = _argparser()
    opts = {a.dest for a in ap._actions}
    assert "null_draws" in opts, "K (number of null shuffles) is not a CLI argument"
    default_k = [a.default for a in ap._actions if a.dest == "null_draws"][0]
    assert default_k >= 20, f"default null draws is {default_k}, the task requires K >= 20"


def test_shuffle_streams_differ_across_folds_and_draws():
    """Pre-fix the permutation RNG was seeded `seed + L` INSIDE the fold loop, so every fold of a
    layer replayed one stream and there was no draw axis at all."""
    n = 40
    def rng(draw, layer, fold):
        if hasattr(probes, "shuffle_rng"):
            return probes.shuffle_rng(123, draw, layer, fold)
        return np.random.RandomState(123 + layer)          # the pre-fix expression, verbatim
    a = rng(0, 8, 0).permutation(n)
    b = rng(0, 8, 1).permutation(n)
    c = rng(1, 8, 0).permutation(n)
    assert not np.array_equal(a, b), "same permutation reused across folds (defect T9b)"
    assert not np.array_equal(a, c), "the null has no independent draw axis (defect T9b)"


# --------------------------------------------------------------------------- stopping rule
def test_stopping_rule_is_enforced_in_code():
    """The module's docstring states 'shuffled AUROC meaningfully above 0.5 means the split is
    leaking'. Pre-fix nothing checked it: a run with a 0.67 shuffled control still wrote DONE.json."""
    assert hasattr(probes, "check_leakage"), "no code enforces the module's own stopping rule"
    leaky = {"regime": "r", "n_draws": 24, "per_layer": {
        8: {"mean": 0.67, "sd": 0.05, "se": 0.05 / math.sqrt(24), "min": 0.5, "max": 0.8,
            "n_draws": 24, "quantiles": {}, "draws": []}}}
    clean = {"regime": "r", "n_draws": 24, "per_layer": {
        8: {"mean": 0.508, "sd": 0.05, "se": 0.05 / math.sqrt(24), "min": 0.4, "max": 0.6,
            "n_draws": 24, "quantiles": {}, "draws": []}}}
    assert probes.check_leakage(leaky, tol=0.05)["leak"] is True
    assert probes.check_leakage(leaky, tol=0.05)["layers_flagged"] == [8]
    # A null mean 0.008 above chance is not a leak however small its standard error gets.
    assert probes.check_leakage(clean, tol=0.05)["leak"] is False


def test_leak_exits_nonzero_by_default():
    ap = _argparser()
    opts = {a.dest for a in ap._actions}
    assert "allow_leak" in opts and "leak_tol" in opts, (
        "no CLI surface for the stopping rule; a violation cannot fail the run loudly")


# --------------------------------------------------------------------------- T6b
def test_best_layer_key_is_labelled_selected_on_test():
    table, reps, layers, li = synthetic()
    out = probes.run_regime(REGIME, table, reps, layers, li, 3, 11, n_components=8)
    assert "best_layer_by_auroc" not in out, (
        "a bare `best_layer_by_auroc` is still emitted; it is an argmax over test-set AUROCs and "
        "must be labelled SELECTED-ON-TEST (defect T6b)")
    assert "best_layer_by_auroc_SELECTED_ON_TEST" in out
    assert out["n_layers_considered"] == N_LAYERS, (
        "the number of layers the max was taken over is not recorded, so a reader cannot discount it")
    assert "selection_warning" in out


def test_nested_selection_is_unbiased_where_test_selection_is_not():
    """On pure noise the honest AUROC is 0.5 at every layer. The max over 10 test-set AUROCs sits
    well above that; selecting the layer on inner training folds must not."""
    table, reps, layers, li = synthetic()
    assert hasattr(probes, "nested_layer_selection"), (
        "no validation-fold layer selection exists; the reported layer is chosen on the test set")
    out = probes.run_regime(REGIME, table, reps, layers, li, 3, 11, n_components=8)
    aurocs = [v["auroc"] for v in out["per_layer"].values() if not math.isnan(v["auroc"])]
    max_on_test = max(aurocs)
    nested = probes.nested_layer_selection(REGIME, table, reps, layers, li, 3, 11,
                                           n_components=8, inner_folds=2)
    assert nested["n_layers_considered"] == N_LAYERS
    assert len(nested["selected_layers"]) >= 2 and "selection_is_stable" in nested
    a = nested["auroc_nested"]
    assert not math.isnan(a)
    assert abs(a - 0.5) <= abs(max_on_test - 0.5) + 1e-9, (
        f"nested AUROC {a:.4f} is further from chance than the selected-on-test max "
        f"{max_on_test:.4f} on pure noise")
    assert max_on_test > 0.5, "sanity: the test-set max should exceed chance on noise"


def _argparser():
    import argparse
    holder = {}
    real_parse = argparse.ArgumentParser.parse_args

    def capture(self, *a, **k):
        holder["ap"] = self
        raise SystemExit(0)

    argparse.ArgumentParser.parse_args = capture
    try:
        sys.argv = ["probes.py", "--run", "x"]
        try:
            probes.main()
        except SystemExit:
            pass
    finally:
        argparse.ArgumentParser.parse_args = real_parse
    if "ap" not in holder:
        pytest.fail("could not capture the argument parser")
    return holder["ap"]


# --------------------------------------------------------------------- verification pass 2026-08-18
# The four tests below were added when the fix above was VERIFIED rather than written. They exist
# because the original guard had never been executed: `test_leak_exits_nonzero_by_default` only
# asserted that two CLI flags exist, so `main()` — the only place `shuffled_null_distribution`,
# `check_leakage`, the paired table, the printout and the non-zero exit are actually wired together
# — had never run once. Two real defects were sitting in that unexecuted path (K=1 silently passing
# the stopping rule; a permutation p that printed 0.0000 from 20 draws), and neither could have been
# caught by a test of the pieces.

def _fake_run(tmpdir):
    """A complete, minimal `extract_boombness` run dir + bank so `main()` can be driven end to end.

    Pure-noise reps again: the honest AUROC is 0.5 everywhere, so a clean run must NOT flag a leak
    and the stopping rule can be forced to fire only by moving its threshold.
    """
    import json
    import torch
    rng = np.random.RandomState(3)
    run = os.path.join(tmpdir, "fakerun")
    os.makedirs(os.path.join(run, "cache"), exist_ok=True)
    layers = [0, 4, 8]
    bank, reps = [], {}
    for d in range(6):
        for j in range(12):
            pid = f"d{d}_{j}"
            bank.append({"prompt_id": pid, "cell": "C" if j % 2 == 0 else "A", "condition": "cond",
                         "domain": f"dom{d}", "split": "dev", "family_id": f"d{d}_f{j // 4}",
                         "n_examples": 4, "bank_block": "core2x2", "query_kind": "q"})
            reps[pid] = torch.tensor(rng.randn(len(layers), 24), dtype=torch.float32)
    torch.save({"layers": layers, "reps": reps}, os.path.join(run, "cache", "final_occurrence_reps.pt"))
    with open(os.path.join(run, "DONE.json"), "w") as f:
        json.dump({"ok": True}, f)
    bank_path = os.path.join(tmpdir, "bank.jsonl")
    with open(bank_path, "w") as f:
        for r in bank:
            f.write(json.dumps(r) + "\n")
    return run, bank_path


def _run_main(tmpdir, extra):
    import functools
    import common
    run, bank_path = _fake_run(tmpdir)
    saved_rundir, saved_argv = probes.RunDir, sys.argv
    probes.RunDir = functools.partial(common.RunDir, out_root=os.path.join(tmpdir, "out"))
    try:
        sys.argv = ["probes.py", "--run", run, "--bank", bank_path, "--layers", "0,4,8",
                    "--folds", "3", "--regimes", REGIME, "--pca", "8",
                    "--tag", f"t{len(extra)}{abs(hash(tuple(extra))) % 10000}"] + extra
        return probes.main()
    finally:
        probes.RunDir, sys.argv = saved_rundir, saved_argv


def test_main_runs_end_to_end_and_exits_clean_on_a_clean_null(tmp_path):
    """The whole wiring, once: null distribution -> paired table -> printout -> summary -> exit 0.

    On pure noise the null mean sits at chance, so a correct run must exit 0 AND must record a
    stopping-rule verdict that was actually evaluated (`rule_enforceable` True)."""
    assert _run_main(str(tmp_path), ["--null-draws", "6"]) == 0
    import glob
    import json
    summ = glob.glob(os.path.join(str(tmp_path), "out", "probes", "*", "summary.json"))
    assert len(summ) == 1, "main() did not write exactly one summary.json"
    s = json.load(open(summ[0]))
    assert s["leak_check"]["rule_enforceable"] is True
    assert s["leak_check"]["regimes_flagged"] == []
    assert s["null_draws"] == 6
    nested = s["results"][REGIME]["nested_layer_selection"]
    assert not math.isnan(nested["auroc_nested"])
    assert REGIME + "_null_distribution" in s["results"]
    assert REGIME + "_shuffled" not in s["results"], "the bare single-draw key is still emitted"


def test_main_exits_nonzero_when_the_stopping_rule_actually_fires(tmp_path):
    """Executes the abort path, not just its CLI flags. The thresholds are moved rather than the
    data, because a leak that big cannot be manufactured out of noise; what is under test is that a
    fired rule reaches a non-zero exit code after the artifacts are on disk."""
    rc = _run_main(str(tmp_path), ["--null-draws", "6", "--leak-tol", "-1", "--leak-z", "-1"])
    assert rc == 2, f"stopping rule fired but main() returned {rc}"


def test_single_draw_null_cannot_silently_pass_the_stopping_rule(tmp_path):
    """K=1 has no between-draw spread, so `se` is NaN and the rule is UNDECIDABLE.

    The first version of this fix let that case return `leak = False` and exit 0 — a clean verdict
    on a check that never ran, inside the very commit that existed to stop exactly that. """
    nd = {"regime": "r", "n_draws": 1, "per_layer": {
        8: {"mean": 0.63, "sd": float("nan"), "se": float("nan"), "min": 0.63, "max": 0.63,
            "n_draws": 1, "quantiles": {}, "draws": [0.63]}}}
    lk = probes.check_leakage(nd, tol=0.05)
    assert lk["rule_enforceable"] is False, "a null with no spread is reported as a passing check"
    assert lk["undecidable_layers"] == [8]
    assert _run_main(str(tmp_path), ["--null-draws", "1"]) != 0, (
        "--null-draws 1 exits 0, certifying a stopping rule that could not be evaluated")


def test_permutation_p_cannot_be_reported_as_zero(tmp_path):
    """An empirical p from K permutations has a floor of 1/(K+1); 0.0000 is not a value K=20 can
    license. Checked on the artifact main() writes, so the smoothing is verified where it is
    published rather than where it is computed."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "6"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*", "summary.json"))[0]))
    paired = s["results"][REGIME]["paired_vs_shuffled"]
    assert paired, "no paired real-vs-null table was written"
    for L, v in paired.items():
        assert v["p_perm_ge_real"] >= v["p_perm_resolution"] > 0, (
            f"L{L} reports p_perm={v['p_perm_ge_real']} below its own resolution floor")
        assert v["p_perm_resolution"] == pytest.approx(1.0 / (v["null_n_draws"] + 1))
