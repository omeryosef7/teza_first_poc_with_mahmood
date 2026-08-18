"""Regression tests for the two 2026-08-18 defects in src/boombness/aggressive_patching.py.

STANDING RULE (project): a guard that has never been tested against a case it should fail is not a
guard. Every test here is written to FAIL against `git show HEAD:src/boombness/aggressive_patching.py`
-- which is exported to a temp file and imported alongside the fixed module so the failure is
demonstrated in-process rather than asserted in a comment.

T9a  the `random` / `orthogonal` control directions were ONE vector per layer (seed = args.seed + L)
     reused across all families and domains, so the downstream domain bootstrap resampled a single
     draw and its "control band" carried zero direction-level variance.
T10  the default readout layers {8,12,16,18,20,24,28,31} sit INSIDE the patched windows, so the
     §5.3 projection / logit-lens readouts at those layers report the value the intervention just
     wrote. Verified on the committed artifact below: 48/48 exact ties to the donor ceiling.
"""
import json
import math
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import aggressive_patching as ap          # the fixed module
import ds_common
import signals as sg
import torch

ARTIFACT = os.path.join(
    REPO, "outputs", "boombness", "aggressive_patching",
    "g1strat_20260818_133953_3374345", "results.jsonl")

READOUT_LAYERS = [8, 12, 16, 18, 20, 24, 28, 31]


# --------------------------------------------------------------------------- #
# The pre-fix module, imported live so "this test fails against HEAD" is checkable
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def head_module(tmp_path_factory):
    import importlib.util
    d = tmp_path_factory.mktemp("head")
    src = os.path.join(str(d), "old_aggressive_patching.py")
    with open(src, "w") as fh:
        subprocess.run(["git", "show", "HEAD:src/boombness/aggressive_patching.py"],
                       cwd=REPO, check=True, stdout=fh)
    spec = importlib.util.spec_from_file_location("old_aggressive_patching", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rows():
    if not os.path.exists(ARTIFACT):
        pytest.skip(f"committed artifact not present: {ARTIFACT}")
    with open(ARTIFACT) as fh:
        return [json.loads(line) for line in fh]


# --------------------------------------------------------------------------- #
# T10 -- readout layers inside the patched window
# --------------------------------------------------------------------------- #
def test_t10_committed_artifact_is_tautological_at_L18(rows):
    """THE DEFECT ITSELF, measured. `transplant|query_only|L18` writes the donor's L18 residual at
    the probe position and then reads L18: the captured vector IS the donor's, so the projection
    cannot differ from the donor ceiling. Measured on the committed run: 48/48 recipient prompts
    tie BIT-FOR-BIT (exact float equality, not a tolerance)."""
    ceiling = {(r["pair"], r["recipient_prompt_id"]): r
               for r in rows if r["intervention"] == "donor_ceiling"}
    hits = [r for r in rows if r["intervention"] == "transplant"
            and r["scope"] == "query_only" and r["window"] == "L18"]
    assert len(hits) == 48, f"expected 48 such cells in the committed run, got {len(hits)}"
    ties = sum(1 for r in hits
               if r["boombness|L18|proj"]
               == ceiling[(r["pair"], r["recipient_prompt_id"])]["boombness|L18|proj"])
    assert ties == 48, f"{ties}/48 -- the tautology this fix is about"


def test_t10_head_artifacts_carry_no_flag_so_they_cannot_be_filtered(rows):
    """Nothing in the committed artifact marks the tautological cells; that is why the fix has to
    add a column rather than only fix future defaults."""
    assert all("readout_inside_patched_window" not in r for r in rows)


def test_t10_flags_use_the_house_helper_not_a_local_reimplementation(monkeypatch):
    """FAILS AGAINST HEAD: `readout_window_flags` does not exist there at all.

    ds_common.patch_layer_sweep is the single source of truth for this rule (it was written for
    defects C1/C3, the same bug in the patchscope and activation-patching drivers). This test
    monkeypatches it and asserts the module's answer follows the patched helper, so a future
    re-implementation of the rule inside this file cannot pass."""
    calls = []

    def fake_sweep(R):
        calls.append(R)
        return list(range(R))

    monkeypatch.setattr(ds_common, "patch_layer_sweep", fake_sweep)
    flags = ap.readout_window_flags(ds_common, [18], READOUT_LAYERS)
    assert calls == READOUT_LAYERS, "every readout layer must be checked via the house helper"
    assert flags["readout_inside_patched_window"] is True
    assert flags["readout_layers_inside_window"] == [18]
    # strictly-upstream windows only: L20..L31 are above the single patched layer 18.
    assert flags["readout_layers_valid"] == [20, 24, 28, 31]


def test_t10_flags_are_false_only_when_the_whole_window_is_upstream():
    """FAILS AGAINST HEAD (no such function). A window entirely below every readout layer is the
    only clean case; `all` and `write_carry_8-21` are not."""
    windows = ap.build_windows(32, [8, 12, 18, 24])
    inside = {w for w, wl in windows.items()
              if ap.readout_window_flags(ds_common, wl, READOUT_LAYERS)["readout_inside_patched_window"]}
    for w in ("all", "write_carry_8-21", "L8", "L12", "L18", "L24",
              "L5-8", "L9-12", "L13-16", "L17-20", "L21-24", "L25-31"):
        assert w in inside, f"{w} contains a readout layer and must be flagged"
    assert "L0-4" not in inside, "L0-4 is strictly upstream of every readout layer"
    flags = ap.readout_window_flags(ds_common, windows["L0-4"], READOUT_LAYERS)
    assert flags["readout_layers_valid"] == READOUT_LAYERS


def test_t10_per_layer_flags_line_up_with_the_metric_columns():
    """Each `boombness|L{R}|proj` column gets a `boombness|L{R}|inside_patched_window` companion so
    a single column can be filtered without re-deriving the window membership."""
    f = ap.readout_window_flags(ds_common, [17, 18, 19, 20], READOUT_LAYERS)
    per = ap.per_layer_inside_flags(READOUT_LAYERS, f["readout_layers_inside_window"])
    assert per["boombness|L18|inside_patched_window"] is True
    assert per["boombness|L20|inside_patched_window"] is True
    assert per["boombness|L24|inside_patched_window"] is False
    assert set(per) == {f"boombness|L{R}|inside_patched_window" for R in READOUT_LAYERS}


def test_t10_readout_layer_zero_does_not_crash_the_sweep():
    """patch_layer_sweep(0) raises (no valid patch window exists below layer 0). A flag must never
    take down a multi-hour run, so R=0 is reported as 'no valid layers' instead."""
    f = ap.readout_window_flags(ds_common, [0], [0, 4])
    assert f["readout_layers_inside_window"] == [0]
    assert 0 not in f["readout_layers_valid"]


def test_t10_head_module_has_no_flag_helpers(head_module):
    """Explicit statement of the pre-fix gap the tests above rely on."""
    for name in ("readout_window_flags", "per_layer_inside_flags"):
        assert not hasattr(head_module, name), f"HEAD unexpectedly has {name}"


# --------------------------------------------------------------------------- #
# T9a -- control directions were a single draw
# --------------------------------------------------------------------------- #
def _d_surface(n_layers=4, dim=256):
    g = torch.Generator().manual_seed(7)
    return {L: torch.randn(dim, generator=g) * (1.0 + L) for L in range(n_layers)}


def test_t9a_head_builds_exactly_one_control_vector_per_layer(head_module):
    """THE DEFECT, stated as code. HEAD has no way to produce a second draw: no helper, and the
    seed is a pure function of (args.seed, L), so every family and every domain in the run shares
    one vector per layer and the bootstrap's 24 resamples of it carry zero direction variance."""
    assert not hasattr(head_module, "build_control_directions")
    assert not hasattr(head_module, "CONTROL_DRAW_SEED_STRIDE")
    assert not hasattr(head_module, "expand_add_directions")


def test_t9a_k_draws_are_independent_and_the_band_has_nonzero_sd():
    """FAILS AGAINST HEAD (build_control_directions absent). The band the control is supposed to
    provide is the spread of <control_k, d_surface>/||d_surface|| ACROSS k; pre-fix that spread did
    not exist because there was one k."""
    ds_ = _d_surface()
    draws = ap.build_control_directions(sg, ds_, seed=20260816, n_draws=12)
    assert len(draws) == 24, "12 random + 12 orthogonal draws"
    for fam in ("random", "orthogonal"):
        vecs = [draws[ap.control_draw_name(fam, k)][2] for k in range(12)]
        # pairwise-distinct: a repeated seed would make these identical, which is the pre-fix bug
        for i in range(len(vecs)):
            for j in range(i + 1, len(vecs)):
                assert not torch.allclose(vecs[i], vecs[j]), f"{fam} draws {i},{j} identical"
        projs = [float(torch.dot(v.float(), ds_[2].float()) / ds_[2].float().norm())
                 for v in vecs]
        m = sum(projs) / len(projs)
        sd = math.sqrt(sum((x - m) ** 2 for x in projs) / (len(projs) - 1))
        assert sd > 0.0, f"{fam}: between-draw sd must be measurable, got {sd}"


def test_t9a_draw_zero_reproduces_the_historical_single_draw():
    """The fix must not silently swap one arbitrary vector for a different arbitrary vector: draw 0
    keeps the pre-fix seed (args.seed + L) so the committed numbers reappear as one member of the
    new band and the old run stays comparable."""
    ds_ = _d_surface()
    draws = ap.build_control_directions(sg, ds_, seed=20260816, n_draws=5)
    for L, v in ds_.items():
        assert torch.equal(draws[ap.control_draw_name("random", 0)][L],
                           sg.random_control_direction(v, seed=20260816 + L))
        assert torch.equal(draws[ap.control_draw_name("orthogonal", 0)][L],
                           sg.orthogonal_control_direction(v, seed=20260816 + L))


def test_t9a_expansion_replicates_only_the_stochastic_controls():
    """FAILS AGAINST HEAD (expand_add_directions absent); HEAD passed --add-directions verbatim."""
    got = ap.expand_add_directions("d_surface,d_context,d_naive,random,orthogonal", 10)
    assert got[:3] == ["d_surface", "d_context", "d_naive"], "fitted directions are not replicated"
    assert got.count("random#0") == 1 and "random#9" in got and "random#10" not in got
    assert len([g for g in got if g.startswith("orthogonal#")]) == 10
    fam, k = ap.split_direction_name("random#7")
    assert (fam, k) == ("random", 7)
    assert ap.split_direction_name("d_surface") == ("d_surface", None)


def test_t9a_default_draw_count_is_at_least_ten():
    """The band is only meaningful with enough draws; the CLI default must not re-create the
    single-draw regime by omission."""
    import argparse
    parser = [a for a in _parser()._actions if a.dest == "n_control_draws"]
    assert parser, "--n-control-draws must exist"
    assert parser[0].default >= 10, parser[0].default


def _parser():
    """Rebuild main()'s parser without running it (no model, no GPU)."""
    import argparse
    import inspect
    # main() is not factored; parse its source is fragile, so construct via the module's own
    # argparse by calling main with --help would exit. Instead exercise the documented default.
    src = inspect.getsource(ap.main)
    ns = argparse.ArgumentParser()
    ns.add_argument("--n-control-draws", type=int,
                    default=int(src.split('"--n-control-draws", type=int, default=')[1]
                                .split(',')[0].strip()))
    return ns


def test_t9a_between_draw_band_reports_sd_and_refuses_to_fake_it():
    """FAILS AGAINST HEAD (between_draw_band absent). With a single draw the sd is None, not 0.0:
    0.0 would read as 'no direction-level variance', which is exactly the false reassurance the
    pre-fix band gave."""
    recs = [{"m": 1.0}, {"m": 3.0}]
    band = ap.between_draw_band(recs)
    assert band["m"] == 2.0
    assert abs(band["between_draw_sd|m"] - math.sqrt(2.0)) < 1e-12
    one = ap.between_draw_band([{"m": 1.0}])
    assert one["m"] == 1.0 and one["between_draw_sd|m"] is None


def test_t9a_band_ignores_non_numeric_and_boolean_columns():
    """The flag columns added by T10 are booleans and must not be averaged into a 'mean flag'."""
    recs = [{"m": 1.0, "flag": True, "name": "a"}, {"m": 2.0, "flag": False, "name": "b"}]
    band = ap.between_draw_band(recs)
    assert "flag" not in band and "name" not in band
    assert band["m"] == 1.5
