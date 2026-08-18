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

Every test here is written so it FAILS against the code that predates the fix it guards. The failure
is behavioural or numeric wherever that is possible — an exit code, a p of exactly 0.0000, a sd of
0.0 — and only falls back to a missing key where the pre-fix code had no such concept at all.

THREE PRE-FIX BASELINES, because the fixes landed in three passes. Pin them with `git show`, never
with HEAD, or committing a fix turns its own test red:

  a8251ffa^   pre-T9b / pre-T6b: one permutation per layer, `best_layer_by_auroc` selected on test,
              no nested selection, no stopping rule in code.        -> 32 of 35 fail
  a8251ffa    T9b + T6b landed, but `check_leakage` returns leak=False at K=1 (se is NaN) and the
              permutation p is the raw fraction that prints 0.0000. -> 22 of 35 fail
  f95d1eea    the K=1 and p_perm holes closed, but the K=1 null still publishes `min`/`max`/
              `quantiles` (a band from one point), `check_leakage` still passes vacuously over ZERO
              layers, and `role_probes` still guards its triad with a chained `a != b != c`.
                                                                    -> 19 of 35 fail
  the 2026-08-19 fix AS FIRST SUBMITTED (no SHA; snapshot the working tree before the adversarial
              pass): closes the band-from-one-draw and zero-LAYER holes, but still exits 0 on a run
              with zero REGIMES, still drops uncached `--layers` silently, and its brand-new
              `check_triad_varies_only_markup` certifies an EMPTY / truncated condition set as a
              valid triad.                                          -> 7 of 35 fail

Run:
  <interp> -m pytest tests/test_probes_selection.py -q
  git show <sha>:src/boombness/probes.py > /tmp/old/probes.py
  PROBES_MODULE=/tmp/old/probes.py <interp> -m pytest tests/test_probes_selection.py -q   # must fail
  ROLE_PROBES_MODULE=/tmp/old/role_probes.py <interp> -m pytest ... -k role                # ditto

The pre-fix module must be dropped in a directory of its OWN with nothing else in it: `probes.py`
puts its own directory first on sys.path, so a stale sibling `common.py` next to it would shadow the
real one and the run would die on an import rather than on the assertion under test.
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
    # The BEHAVIOURAL assertion goes first on purpose: against the pre-fix module this must fail as
    # `assert 0 != 0` — a run that exited clean — and not as a KeyError on a field that was simply
    # not there yet. An exit code is the thing the guard is for.
    assert _run_main(str(tmp_path), ["--null-draws", "1"]) != 0, (
        "--null-draws 1 exits 0, certifying a stopping rule that could not be evaluated")
    lk = probes.check_leakage(nd, tol=0.05)
    assert lk["rule_enforceable"] is False, "a null with no spread is reported as a passing check"
    assert lk["undecidable_layers"] == [8]


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
        # Numeric first: pre-fix the raw fraction `(draws >= real).mean()` printed and stored
        # exactly 0.0 at the layers no permutation beat, which is what this line catches.
        assert v["p_perm_ge_real"] > 0.0, (
            f"L{L} reports an empirical p of exactly {v['p_perm_ge_real']} from "
            f"{v['null_n_draws']} permutations; zero is not a value K draws can license")
        assert v["p_perm_ge_real"] >= v["p_perm_resolution"] > 0, (
            f"L{L} reports p_perm={v['p_perm_ge_real']} below its own resolution floor")
        assert v["p_perm_resolution"] == pytest.approx(1.0 / (v["null_n_draws"] + 1))


# ------------------------------------------------------- T9 verification pass 2026-08-19
# The 2026-08-18 tests above prove the null has K draws and that K=1 cannot pass the stopping rule.
# They do NOT prove that a K=1 null refuses to REPORT a band, and that is the half of T9 the defect
# is actually named after ("a single control draw presented as a band"). Suppressing sd/se is one of
# two paths; `min`, `max` and the empirical `quantiles` were the other, and they were still computed
# unconditionally — `np.quantile` of a one-element array returns that element, so K=1 published
# q0.05 == q0.5 == q0.95 == min == max == the single draw, and `main` republished all of it.

def test_single_draw_null_reports_no_band_and_no_sd():
    """K=1 must withhold EVERY band-shaped key, not only the numeric ones.

    Pre-fix this fails on `quantiles`: the module returned q0.05/q0.5/q0.95 all equal to the one
    draw, i.e. a band manufactured from a point — verbatim defect T9."""
    table, reps, layers, li = synthetic()
    nd = probes.shuffled_null_distribution(REGIME, table, reps, layers[:3], li, 3, 11,
                                           n_components=8, n_draws=1)
    assert nd["per_layer"], "sanity: K=1 still has to produce a point per layer"
    # THE DEFECT ITSELF GOES FIRST, before any key this fix invented. Against the pre-fix module
    # the ordering below fails as "empirical quantiles {...} reported from ONE draw"; asserting
    # `is_band` first made it fail as `KeyError: 'is_band'`, which is a report about vocabulary
    # rather than about the number that was published.
    for L, v in nd["per_layer"].items():
        assert v["n_draws"] == 1
        assert v["quantiles"] == {}, (
            f"L{L}: empirical quantiles {v['quantiles']} reported from ONE draw — a point "
            "presented as a band (defect T9)")
        for k in ("sd", "se", "min", "max"):
            assert math.isnan(v[k]), f"L{L}: {k}={v[k]!r} computed from a single draw"
        assert v["is_band"] is False, f"L{L}: 1 draw is flagged as a band"
        assert "band_suppressed_reason" in v
    assert nd["is_band"] is False, "a 1-draw null reports itself as a band"
    assert sorted(nd["layers_without_band"]) == sorted(nd["per_layer"]), (
        "layers whose band was withheld are not listed")


def test_two_draw_null_still_reports_its_band():
    """The suppression must key on K, not disable the band everywhere (the guard has to pass the
    case it should pass, or it is just a switch that is always off)."""
    table, reps, layers, li = synthetic()
    nd = probes.shuffled_null_distribution(REGIME, table, reps, layers[:3], li, 3, 11,
                                           n_components=8, n_draws=4)
    assert nd["is_band"] is True and nd["layers_without_band"] == []
    for v in nd["per_layer"].values():
        assert v["is_band"] is True
        assert set(v["quantiles"]) >= {"q0.05", "q0.5", "q0.95"}
        assert not math.isnan(v["sd"]) and not math.isnan(v["min"])


def test_single_draw_band_is_not_published_into_the_artifact(tmp_path):
    """The composed path, end to end. `shuffled_null_distribution` is one path; `main`'s
    `paired_vs_shuffled` table is the one a reader actually quotes, and it re-emitted
    `null_quantiles` / `null_min` / `null_max` and derived `above_null_q95` from the fake q95.

    Driven with --allow-leak so the run reaches exit 0 and the artifact can be inspected; the point
    under test is the CONTENT of the artifact, not the exit code (which has its own test)."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "1", "--allow-leak"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    assert s["leak_check"]["rule_enforceable"] is False, (
        "a K=1 run still records an enforceable stopping rule")
    paired = s["results"][REGIME]["paired_vs_shuffled"]
    assert paired, "no paired table was written"
    for L, v in paired.items():
        assert v["null_n_draws"] == 1
        # Same ordering rule as the unit test above: the published band first, the flag last.
        assert v["null_quantiles"] == {}, (
            f"L{L}: null_quantiles {v['null_quantiles']} published from ONE draw (defect T9)")
        assert math.isnan(v["null_sd"]) and math.isnan(v["null_min"]) and math.isnan(v["null_max"])
        assert v["above_null_q95"] is None, (
            f"L{L}: above_null_q95={v['above_null_q95']!r} — a verdict against a 95th percentile "
            "that one draw cannot define")
        assert v["null_is_band"] is False, f"L{L}: the artifact calls a 1-draw null a band"
    nulldist = s["results"][REGIME + "_null_distribution"]
    assert nulldist["is_band"] is False


# ------------------------------------------------- the vacuous-pass hole in the SAME guard
def test_stopping_rule_cannot_pass_over_zero_layers():
    """`rule_enforceable = not undecidable_layers` is True for an EMPTY null, because an empty null
    has no undecidable layers. So a check that ran over nothing certified itself clean — the same
    dead-guard shape as the K=1 hole, one level up."""
    lk = probes.check_leakage({"regime": "r", "n_draws": 20, "per_layer": {}}, tol=0.05)
    assert lk["n_layers_checked"] == 0
    assert lk["no_layers_evaluated"] is True
    assert lk["leak"] is False
    assert lk["rule_enforceable"] is False, (
        "a stopping rule evaluated over ZERO layers reports itself as enforceable and passing")
    assert lk["unenforceable_reason"]


def test_main_exits_nonzero_when_a_regime_evaluates_no_layers(tmp_path):
    """End to end. The fake bank holds only cells A and C, so `d6_surface_matched_concept` (B vs E)
    has an EMPTY pool: every layer is skipped in both the real and the null arm, the regime computes
    nothing, and pre-fix it collected a clean stopping-rule verdict and exit 0."""
    import glob
    import json
    rc = _run_main(str(tmp_path), ["--null-draws", "6",
                                   "--regimes", "d6_surface_matched_concept"])
    assert rc != 0, ("a regime that evaluated ZERO layers exited 0 with a clean stopping-rule "
                     "verdict")
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    assert s["leak_check"]["rule_enforceable"] is False
    assert s["leak_check"]["regimes_with_no_layers"] == ["d6_surface_matched_concept"]
    assert s["leak_check"]["by_regime"]["d6_surface_matched_concept"]["n_layers_checked"] == 0


def test_a_populated_regime_is_still_enforceable(tmp_path):
    """Companion to the test above: the zero-layer guard must not fire on a regime that did work."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "4"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    lk = s["leak_check"]["by_regime"][REGIME]
    assert lk["n_layers_checked"] == 3 and lk["no_layers_evaluated"] is False
    assert lk["rule_enforceable"] is True
    assert s["leak_check"]["regimes_with_no_layers"] == []


# ------------------------------------------------------------------- T6, still the default
def test_nested_selection_is_unconditional_not_an_opt_in(tmp_path):
    """T6's fix is only a fix if nobody has to ask for it. There must be no CLI switch that turns
    nested selection on or off, and `main` must compute it for every regime it runs with no flag
    beyond the ones this test does not pass.

    Fails against the pre-T6b module (`a8251ffa^`), which has no `nested_layer_selection` at all and
    reports the selected-on-test argmax as the headline."""
    import glob
    import json
    ap = _argparser()
    dests = {a.dest for a in ap._actions}
    assert not {d for d in dests if "nested" in d and d != "inner_folds"}, (
        f"nested layer selection is gated behind a flag ({dests}); it must be the default path")
    assert hasattr(probes, "nested_layer_selection")
    assert _run_main(str(tmp_path), ["--null-draws", "3"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    for rg, res in s["results"].items():
        if rg.endswith("_null_distribution") or "shuffled" in rg:
            continue
        assert "nested_layer_selection" in res, (
            f"{rg} was analysed without nested layer selection; the headline is still an argmax "
            "over test-set AUROCs (defect T6)")
    assert "nested_layer_selection" in s["headline_note"]


def test_selection_is_stable_is_recorded_in_both_artifacts(tmp_path):
    """T6 asks for `selection_is_stable` in the artifact. summary.json carried it; results.jsonl —
    the per-regime row a reader scans — carried only `nested_selected_layers`, so the flag and the
    number it qualifies did not travel together."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "4"]) == 0
    rundir = os.path.dirname(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                                    "summary.json"))[0])
    s = json.load(open(os.path.join(rundir, "summary.json")))
    nested = s["results"][REGIME]["nested_layer_selection"]
    assert isinstance(nested["selection_is_stable"], bool)
    assert nested["selected_layers"] and nested["n_layers_considered"] == 3
    # results.jsonl here is a SYNTHETIC fixture written by this test: prompt ids and cell letters
    # only, no prompt text and no generations.
    rows = [json.loads(l) for l in open(os.path.join(rundir, "results.jsonl")) if l.strip()]
    assert len(rows) == 1
    assert "nested_selection_is_stable" in rows[0], (
        "the run row reports auroc_nested_selection without the flag that says whether the layer "
        "choice was stable across folds (defect T6)")
    assert rows[0]["nested_selection_is_stable"] == nested["selection_is_stable"]
    assert rows[0]["nested_n_layers_considered"] == nested["n_layers_considered"]


# ----------------------------------------------------- remaining unexecuted paths in main()
def test_allow_leak_is_the_only_way_past_a_fired_stopping_rule(tmp_path):
    """The escape hatch itself had never been executed. Both abort branches must honour it, and
    neither may honour anything else."""
    rc = _run_main(str(tmp_path), ["--null-draws", "6", "--leak-tol", "-1", "--leak-z", "-1",
                                   "--allow-leak"])
    assert rc == 0, f"--allow-leak did not suppress the leak abort (rc={rc})"


def test_missing_done_json_fails_before_anything_is_computed(tmp_path):
    """`require_done` is the first guard in main() and had no test on this path."""
    import json
    run, bank_path = _fake_run(str(tmp_path))
    os.remove(os.path.join(run, "DONE.json"))
    saved_argv = sys.argv
    try:
        sys.argv = ["probes.py", "--run", run, "--bank", bank_path, "--layers", "0,4,8",
                    "--regimes", REGIME, "--pca", "8", "--tag", "nodone"]
        with pytest.raises(BaseException) as ei:
            probes.main()
        assert not isinstance(ei.value, AssertionError)
    finally:
        sys.argv = saved_argv


def test_missing_rep_cache_fails_loudly(tmp_path):
    run, bank_path = _fake_run(str(tmp_path))
    os.remove(os.path.join(run, "cache", "final_occurrence_reps.pt"))
    saved_argv = sys.argv
    try:
        sys.argv = ["probes.py", "--run", run, "--bank", bank_path, "--regimes", REGIME,
                    "--pca", "8", "--tag", "nocache"]
        with pytest.raises(SystemExit) as ei:
            probes.main()
        assert "final_occurrence_reps" in str(ei.value)
    finally:
        sys.argv = saved_argv


# ------------------------------------------------------- role_probes.py (same ownership)
# `role_probes` has no test file of its own and its selftest had never been executed against a case
# it should fail. Its ONE distinctness guard was a chained comparison,
# `conds["untagged"] != conds["tagged"] != conds["user_tagged"]`, which Python evaluates as
# `(a != b) and (b != c)` and which therefore never tested the (untagged, user_tagged) pair — the
# pair the triad exists to contrast. Same shape as the five dead guards this sprint has shipped.

_ROLE_PROBES = []


def _role_probes():
    """Loaded once (importing it drags in common/sklearn), and overridable the same way
    PROBES_MODULE overrides probes.py, so these guards can be pointed at pre-fix code:

      ROLE_PROBES_MODULE=<old role_probes.py> <interp> -m pytest tests/test_probes_selection.py
    """
    if not _ROLE_PROBES:
        path = os.environ.get("ROLE_PROBES_MODULE", os.path.join(SRC, "role_probes.py"))
        spec = importlib.util.spec_from_file_location("role_probes_under_test", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ROLE_PROBES.append(mod)
    return _ROLE_PROBES[0]


def _collapsing_conditions(rp):
    """Conditions built with an IDENTITY renderer, which makes `user_tagged == untagged`.

    That is exactly the case the triad must reject and the chained comparison accepts:
      untagged   = "aaa\\n\\nbbb"
      tagged     = "aaabbb"            (join with no separator) -> differs from untagged
      user_tagged= "aaa\\n\\nbbb"        -> IDENTICAL to untagged
    `(untagged != tagged) and (tagged != user_tagged)` is True, so the pre-fix assertion passes.
    """
    segs = [("user", "aaa"), ("assistant", "bbb")]
    saved = rp.render_single
    try:
        rp.render_single = lambda prefix, role, content, tool_name=None: content
        return rp.build_role_conditions("llama3", segs), [c for _, c in segs]
    finally:
        rp.render_single = saved


def test_role_triad_distinctness_is_checked_over_all_pairs():
    """The pre-fix guard is reproduced verbatim next to the new one, and must disagree with it."""
    rp = _role_probes()
    conds, contents = _collapsing_conditions(rp)
    assert conds["untagged"] == conds["user_tagged"], "sanity: the collision was not constructed"
    chained = conds["untagged"] != conds["tagged"] != conds["user_tagged"]   # pre-fix expression
    assert chained is True, "sanity: the pre-fix chained comparison must accept this case"
    assert hasattr(rp, "check_triad_varies_only_markup"), (
        "the triad's distinctness condition exists only as an assertion inside main()")
    v = rp.check_triad_varies_only_markup(conds, contents)
    assert v["ok"] is False, (
        "two role conditions are byte-identical and the triad still reports itself valid — the "
        "chained `a != b != c` never tested the (untagged, user_tagged) pair")
    assert ("untagged", "user_tagged") in [tuple(p) for p in v["colliding_pairs"]]


def test_role_triad_accepts_the_real_renderer():
    """The companion case the guard must PASS, so it is a check and not a switch stuck at fail."""
    rp = _role_probes()
    segs = [("user", "The report describes an object near the bridge."),
            ("assistant", "It is logged in the inventory.")]
    conds = rp.build_role_conditions("llama3", segs)
    v = rp.check_triad_varies_only_markup(conds, [c for _, c in segs])
    assert v["ok"] is True and v["colliding_pairs"] == []
    assert v["n_conditions"] == 5 and all(v["content_complete"].values())


def test_role_triad_rejects_a_condition_that_lost_content():
    """The other half of 'varies ONLY the markup': a renderer that truncates must be caught."""
    rp = _role_probes()
    conds = {"untagged": "aaa\n\nbbb", "tagged": "<u>aaa</u><a>bbb</a>", "user_tagged": "<u>aaa</u>"}
    v = rp.check_triad_varies_only_markup(conds, ["aaa", "bbb"])
    assert v["ok"] is False
    assert v["missing_content"] == {"user_tagged": ["bbb"]}


def test_role_selftest_returns_nonzero_when_the_triad_is_invalid(monkeypatch):
    """main() must FAIL the run, not print and return 0."""
    rp = _role_probes()
    monkeypatch.setattr(rp, "render_single",
                        lambda prefix, role, content, tool_name=None: content)
    monkeypatch.setattr(sys, "argv", ["role_probes.py", "--selftest"])
    assert rp.main() == 1, "an invalid triad exits 0 from --selftest"


def test_role_selftest_returns_zero_on_the_real_renderer(monkeypatch):
    rp = _role_probes()
    monkeypatch.setattr(sys, "argv", ["role_probes.py", "--selftest"])
    assert rp.main() == 0


# =========================================================================================
# ADVERSARIAL VERIFICATION PASS, 2026-08-19 (second pass, on the fix above)
# -----------------------------------------------------------------------------------------
# The 2026-08-19 fix closed two vacuous-pass holes: a band computed from one draw, and a stopping
# rule that passed over zero LAYERS. Verifying it turned up three more of the same shape, two of
# them inside the fix itself:
#
#   (v)   the zero-layer fix landed on the per-regime path and was dropped on the no-regime path;
#   (vi)  `--layers` still dropped uncached layers silently, which makes the new `n_layers_checked`
#         field — the field that exists to prove the check ran on something — unreadable;
#   (vii) `check_triad_varies_only_markup`, written on 2026-08-19 to replace a chained comparison,
#         itself returned `ok: True` for an EMPTY condition mapping and for one that had lost
#         `user_tagged` — a REGRESSION, because the chained assertion it replaced at least raised
#         KeyError on the latter.
#
# Each test below is pinned against the fix AS SUBMITTED, not only against HEAD:
#   cp src/boombness/probes.py       $SP/patch_asubmitted/probes.py     (before this pass)
#   cp src/boombness/role_probes.py  $SP/patch_role/role_probes.py
#   PROBES_MODULE=$SP/patch_asubmitted/probes.py ROLE_PROBES_MODULE=$SP/patch_role/role_probes.py \
#       <interp> -m pytest tests/test_probes_selection.py -q      # these five must FAIL

def test_check_leakage_requires_the_null_to_declare_a_band():
    """`decidable = has_band and se > 0` was added as "two independent facts", but no test ever
    exercised the `has_band` half on its own, so nothing proved it could change an outcome.

    It can: a per-layer record that declares `is_band: False` while carrying a finite, positive
    `se` is decided by the pre-fix expression (`se > 0` alone) and flagged as a leak. A guard whose
    only untested clause is the one the fix is named after is how this project shipped five dead
    guards."""
    nd = {"regime": "r", "n_draws": 1, "per_layer": {
        8: {"mean": 0.63, "sd": 0.10, "se": 0.02, "min": 0.5, "max": 0.7, "n_draws": 1,
            "is_band": False, "quantiles": {}, "draws": [0.63]}}}
    lk = probes.check_leakage(nd, tol=0.05)
    assert lk["rule_enforceable"] is False, (
        "a null that declares itself NOT a band still bought a decidable verdict with its se")
    assert lk["undecidable_layers"] == [8]
    assert lk["per_layer"][0]["decidable"] is False
    # ... and the companion: a record that DOES declare a band is still decided normally, so the
    # clause is a check and not a switch stuck at "undecidable".
    nd2 = {"regime": "r", "n_draws": 20, "per_layer": {
        8: {"mean": 0.63, "sd": 0.10, "se": 0.02, "min": 0.5, "max": 0.7, "n_draws": 20,
            "is_band": True, "quantiles": {"q0.95": 0.7}, "draws": []}}}
    lk2 = probes.check_leakage(nd2, tol=0.05)
    assert lk2["rule_enforceable"] is True and lk2["leak"] is True


def test_main_exits_nonzero_when_no_regime_is_evaluated(tmp_path):
    """(v) The zero-LAYER guard is per regime; `undecidable` is accumulated inside the regime loop.

    With zero regimes the loop never runs, `undecidable` is empty, the banner never fires and the
    run returns 0 — while the summary.json that same run writes records
    `leak_check.rule_enforceable: False`. An exit code that contradicts the artifact next to it is
    the vacuous pass one level above the one the 2026-08-19 fix closed."""
    import glob
    import json
    rc = _run_main(str(tmp_path), ["--null-draws", "4", "--regimes", ""])
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    assert s["leak_check"]["rule_enforceable"] is False, "sanity: nothing was evaluated"
    assert rc != 0, (
        f"a run that evaluated ZERO regimes returned {rc} while its own summary.json records "
        "rule_enforceable=False — the exit code contradicts the artifact")
    assert s["leak_check"]["no_regimes_evaluated"] is True
    assert s["leak_check"]["n_regimes_evaluated"] == 0


def test_a_run_with_regimes_is_unaffected_by_the_no_regime_guard(tmp_path):
    """Companion: the (v) guard must not fire on a run that did work."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "4"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    assert s["leak_check"]["no_regimes_evaluated"] is False
    assert s["leak_check"]["n_regimes_evaluated"] == 1


def test_requested_layers_absent_from_the_cache_are_not_dropped_silently(tmp_path):
    """(vi) `want = [L for L in want if L in layer_index]` shrank the analysis with no message, no
    FailureLedger entry and no summary field — and then the run reported `n_layers_checked: 3`,
    which is exactly what a complete three-layer run reports. The field added to prove the stopping
    rule had something to run on cannot distinguish 3-of-3 from 3-of-5."""
    with pytest.raises(SystemExit) as ei:
        _run_main(str(tmp_path), ["--null-draws", "4", "--layers", "0,4,8,99,777"])
    msg = str(ei.value)
    assert "99" in msg and "777" in msg, f"the dropped layers are not named in the failure: {msg}"


def test_a_valid_layer_subset_is_still_accepted(tmp_path):
    """Companion to (vi): asking for a subset the cache HAS must remain a normal run, and the
    request must be recorded next to what was analysed."""
    import glob
    import json
    assert _run_main(str(tmp_path), ["--null-draws", "4", "--layers", "0,8"]) == 0
    s = json.load(open(glob.glob(os.path.join(str(tmp_path), "out", "probes", "*",
                                              "summary.json"))[0]))
    assert s["layers"] == [0, 8] and s["layers_requested"] == [0, 8]
    assert s["leak_check"]["by_regime"][REGIME]["n_layers_checked"] == 2


def test_role_triad_check_is_not_vacuous_on_an_empty_condition_set():
    """(vii) `ok = all(content_complete.values()) and not colliding_pairs` — BOTH of which are
    vacuously true over an empty mapping. The function written on 2026-08-19 to replace a dead
    guard certified an empty triad as valid, which is the same shape as `check_leakage` passing
    over zero layers in the very same patch."""
    rp = _role_probes()
    v = rp.check_triad_varies_only_markup({}, ["aaa"])
    assert v["ok"] is False, (
        "an EMPTY set of role conditions reports itself as a valid triad — every pairwise test "
        "passes vacuously when there are no pairs")
    assert sorted(v["missing_conditions"]) == ["tagged", "untagged", "user_tagged"]


def test_role_triad_check_requires_the_named_conditions_not_just_distinct_ones():
    """(vii), the reachable half AND a regression check.

    `conds` without `user_tagged` is content-complete and collision-free, so the new check passed
    it. The chained `conds["untagged"] != conds["tagged"] != conds["user_tagged"]` it replaced
    raised KeyError there — so the rewrite turned a loud failure into a silent pass on the one
    condition the Userness contrast is actually about."""
    rp = _role_probes()
    conds = {"untagged": "aaa\n\nbbb", "tagged": "<u>aaa</u><a>bbb</a>"}
    v = rp.check_triad_varies_only_markup(conds, ["aaa", "bbb"])
    assert v["colliding_pairs"] == [] and all(v["content_complete"].values()), (
        "sanity: this mapping passes every test the pre-fix version applied")
    # Substantive assertion before the bookkeeping key, so the pre-fix failure names the verdict.
    assert v["ok"] is False, (
        "a condition set that lost `user_tagged` is reported as a valid triad; the chained "
        "comparison this replaced at least raised KeyError on it")
    assert v["missing_conditions"] == ["user_tagged"]


def test_role_triad_check_still_accepts_the_full_five_condition_set():
    """Companion to (vii): requiring the three named conditions must not reject the extra arms."""
    rp = _role_probes()
    segs = [("user", "The report describes an object near the bridge."),
            ("assistant", "It is logged in the inventory.")]
    conds = rp.build_role_conditions("llama3", segs)
    v = rp.check_triad_varies_only_markup(conds, [c for _, c in segs])
    assert v["ok"] is True and v["missing_conditions"] == []
    assert set(v["required_conditions"]) <= set(conds)
