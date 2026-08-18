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
# The pre-fix module, imported live so "this test fails against the old code" is checkable
# --------------------------------------------------------------------------- #
TARGET = "src/boombness/aggressive_patching.py"


def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def _rev_before(marker):
    """Parent of the OLDEST commit that introduced `marker` into the target file.

    REVIEW FIX (2026-08-18): this fixture used to export `HEAD:<target>` and call the result "the
    pre-fix module". That was true only for the few minutes between writing the fix and committing
    it. The T9a/T10 fix is now IN HEAD, so every "FAILS AGAINST HEAD" test here was asserting a
    property of the FIXED file, and two of them (`test_t10_head_module_has_no_flag_helpers`,
    `test_t9a_head_builds_exactly_one_control_vector_per_layer`) failed the moment the fix landed
    -- i.e. the regression suite's own claim that it fails against the defect became unverifiable
    at exactly the point it started to matter. Pin the revision by CONTENT instead: find the first
    commit that added the marker string to this file and take its parent. That stays correct as
    history grows, and it fails loudly (rather than silently comparing the file to itself) if the
    marker is ever renamed.
    """
    shas = _git("log", "--format=%H", "-S", marker, "--", TARGET).split()
    assert shas, f"no commit in the history of {TARGET} introduces {marker!r}"
    return shas[-1] + "^"


def _module_at(dest_dir, rev, modname):
    import importlib.util
    src = os.path.join(str(dest_dir), modname + ".py")
    with open(src, "w") as fh:
        subprocess.run(["git", "show", f"{rev}:{TARGET}"], cwd=REPO, check=True, stdout=fh)
    spec = importlib.util.spec_from_file_location(modname, src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def head_module(tmp_path_factory):
    """The module as it stood BEFORE the T9a/T10 fix (parent of the commit that added the flag)."""
    d = tmp_path_factory.mktemp("prefix_t10")
    return _module_at(d, _rev_before("readout_window_flags"), "old_aggressive_patching")


@pytest.fixture(scope="module")
def t10a_module(tmp_path_factory):
    """The module as it stood after the layer-only T10 fix but before the T10b position fix.

    This is the version T10b is a regression test against: it has `readout_window_flags`, but the
    function is a pure layer predicate with no notion of which POSITIONS were patched.
    """
    d = tmp_path_factory.mktemp("prefix_t10b")
    rev = _rev_before("readout_tautological")
    mod = _module_at(d, rev, "t10a_aggressive_patching")
    if hasattr(mod, "readout_window_flags"):
        return mod
    pytest.skip("T10b's baseline revision predates the T10 fix entirely")


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
    # T10b added a `|tautological` companion to each column; positions were not supplied here, so
    # it is None (unknown) rather than False.
    assert set(per) == ({f"boombness|L{R}|inside_patched_window" for R in READOUT_LAYERS}
                        | {f"boombness|L{R}|tautological" for R in READOUT_LAYERS})
    assert all(per[f"boombness|L{R}|tautological"] is None for R in READOUT_LAYERS)


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


# --------------------------------------------------------------------------- #
# T10b -- the layer-only flag over-flagged, because a patch also has a POSITION extent
# --------------------------------------------------------------------------- #
def test_t10b_demo_only_scopes_are_not_tautological_in_the_committed_run(rows):
    """THE T10b DEFECT, measured on the artifact. `readout_inside_patched_window` is True for all
    five scopes at an in-window readout layer, but only the scopes that actually patch `probe_pos`
    (the last/query occurrence) reproduce the donor ceiling. Counting in-window
    `boombness|L*|proj` transplant cells on the committed run: query_only 1200/1200 and all
    1200/1200 tie the ceiling bit-for-bit; demos_only / first_demo / last_demo tie it 0/1200 each.
    A layer-only flag therefore condemns 3600 of 6000 cells that are ordinary evidence."""
    import collections
    meta = os.path.join(os.path.dirname(ARTIFACT), "metadata.json")
    with open(meta) as fh:
        m = json.load(fh)
    windows, readout = m["windows"], m["readout_layers"]
    key = lambda r: (r["pair"], r["family_id"], r["recipient_prompt_id"])   # noqa: E731
    ceiling = {key(r): r for r in rows if r["intervention"] == "donor_ceiling"}
    tally = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        if r["intervention"] != "transplant":
            continue
        wl = set(windows[r["window"]])
        for R in readout:
            if R not in wl:
                continue
            k = f"boombness|L{R}|proj"
            t = tally[r["scope"]]
            t[0] += 1
            t[1] += (r[k] == ceiling[key(r)][k])
    assert {s: tuple(v) for s, v in tally.items()} == {
        "query_only": (1200, 1200),
        "all": (1200, 1200),
        "demos_only": (1200, 0),
        "first_demo": (1200, 0),
        "last_demo": (1200, 0),
    }


def test_t10b_flags_distinguish_layer_overlap_from_an_overwritten_readout():
    """FAILS AGAINST THE T10a MODULE (no `readout_tautological` key at all). Same window, same
    readout layers, two different position sets: only the one containing the probe is a tautology."""
    hit = ap.readout_window_flags(ds_common, [18], READOUT_LAYERS,
                                  patched_positions=[11, 12], probe_pos=12)
    miss = ap.readout_window_flags(ds_common, [18], READOUT_LAYERS,
                                   patched_positions=[3, 4], probe_pos=12)
    for f in (hit, miss):
        assert f["readout_inside_patched_window"] is True, "the LAYER predicate is unchanged"
    assert hit["readout_probe_pos_patched"] is True and hit["readout_tautological"] is True
    assert hit["readout_layers_tautological"] == [18]
    assert miss["readout_probe_pos_patched"] is False and miss["readout_tautological"] is False
    assert miss["readout_layers_tautological"] == []


def test_t10b_unknown_positions_report_none_not_false():
    """'Not asked' must never render as 'clean'. A caller that has not been updated gets None."""
    f = ap.readout_window_flags(ds_common, [18], READOUT_LAYERS)
    assert f["readout_tautological"] is None and f["readout_probe_pos_patched"] is None
    per = ap.per_layer_inside_flags(READOUT_LAYERS, f["readout_layers_inside_window"],
                                    f["readout_layers_tautological"])
    assert per["boombness|L18|inside_patched_window"] is True
    assert per["boombness|L18|tautological"] is None


def test_t10b_per_layer_tautology_flags_track_the_position_test():
    f = ap.readout_window_flags(ds_common, [16, 18], READOUT_LAYERS,
                                patched_positions=[7], probe_pos=7)
    per = ap.per_layer_inside_flags(READOUT_LAYERS, f["readout_layers_inside_window"],
                                    f["readout_layers_tautological"])
    assert per["boombness|L16|tautological"] is True
    assert per["boombness|L18|tautological"] is True
    assert per["boombness|L20|tautological"] is False
    assert set(per) == ({f"boombness|L{R}|inside_patched_window" for R in READOUT_LAYERS}
                        | {f"boombness|L{R}|tautological" for R in READOUT_LAYERS})


def test_t10b_prior_module_had_no_position_notion(t10a_module):
    """Explicit statement of the gap: the layer-only version cannot even be ASKED the question."""
    import inspect
    sig = inspect.signature(t10a_module.readout_window_flags)
    assert "patched_positions" not in sig.parameters
    flags = t10a_module.readout_window_flags(ds_common, [18], READOUT_LAYERS)
    assert "readout_tautological" not in flags
    assert flags["readout_inside_patched_window"] is True     # ... for EVERY scope, which is the bug


def test_t10b_scope_positions_decide_the_flag_via_select_positions():
    """The position set the flag is computed from must be the one the patch actually uses."""
    last = [4, 9, 14, 21]          # occurrences; the query occurrence is the last
    probe = last[-1]
    for scope, taut in (("query_only", True), ("all", True), ("demos_only", False),
                        ("first_demo", False), ("last_demo", False)):
        pos = ap.select_positions(last, scope)
        f = ap.readout_window_flags(ds_common, [18], READOUT_LAYERS,
                                    patched_positions=pos, probe_pos=probe)
        assert f["readout_tautological"] is taut, scope
