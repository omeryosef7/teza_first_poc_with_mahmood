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


# =========================================================================== #
# C-6 -- the semantic readout could not spell the codeword
#
# `semantic_logodds` was log p(concept ids) - log p(codeword ids) at the final next-token
# position with no forcing prefix. `outputs/boombness/g1_stratified.json` records
# `"readout": "semantic_logodds"`, so this is the statistic G1's +68%-of-span headline is
# computed from -- see test_c6_g1_headline_is_computed_from_this_statistic below.
# =========================================================================== #
def _rev_before_or_head(marker):
    """Like `_rev_before`, but usable while the fix is still UNCOMMITTED.

    `_rev_before` asserts the marker exists in history. That is the right loud failure once a fix
    is committed, and the WRONG one while it is still in the working tree: there the pre-fix module
    simply IS HEAD, and asserting would turn "the fix is not committed yet" into a fixture error
    that hides whether the real assertions fail. Empty history therefore resolves to HEAD, and the
    demonstration that these tests fail against the defect is carried by the assertions themselves
    (`whole_answer_semantic` is absent, the default is "primary", the band name is unconditional),
    which fail exactly as loudly if the marker is ever renamed away.
    """
    shas = _git("log", "--format=%H", "-S", marker, "--", TARGET).split()
    return (shas[-1] + "^") if shas else "HEAD"


@pytest.fixture(scope="module")
def c6_module(tmp_path_factory):
    """The module as it stood BEFORE the C-6 whole-answer port."""
    d = tmp_path_factory.mktemp("prefix_c6")
    return _module_at(d, _rev_before_or_head("whole_answer_semantic"), "c6_aggressive_patching")


# --------------------------------------------------------------------------- #
# A tokenizer that reproduces Llama-3.1-8B's carrot/bomb asymmetry exactly, and a model that
# wants to answer " Carrot". No GPU, no weights, no prompt text.
#   " carrot" -> 1 token         "carrot" -> ['car','rot']
#   " Carrot" -> [' Car','rot']  "Carrot" -> ['Car','rot']
#   " bomb"/"bomb"/" Bomb"/"Bomb" -> 1 token each
# So `bomb` has FOUR single-token full-word variants and `carrot` exactly ONE, and the model's
# preferred spelling of the codeword (' Car'+'rot') is not representable as a single next token.
# --------------------------------------------------------------------------- #
V_STUB = 48
PIECES = {
    "CTX": [1, 2, 3], "Answer:": [5],
    " bomb": [10], "bomb": [11], " Bomb": [12], "Bomb": [13],
    " carrot": [20], "carrot": [21, 22], " Carrot": [23, 22], "Carrot": [24, 22],
}
DECODE = {1: "C", 2: "T", 3: "X", 5: "Answer:", 10: " bomb", 11: "bomb", 12: " Bomb",
          13: "Bomb", 20: " carrot", 21: "car", 22: "rot", 23: " Car", 24: "Car"}


class StubTok:
    pad_token_id = 0
    eos_token_id = 0

    def __call__(self, text, add_special_tokens=False):
        ids, i = [], 0
        while i < len(text):
            for piece in sorted(PIECES, key=len, reverse=True):
                if text.startswith(piece, i):
                    ids.extend(PIECES[piece])
                    i += len(piece)
                    break
            else:
                raise AssertionError(f"StubTok cannot tokenize {text[i:]!r}")
        return {"input_ids": ids}

    def decode(self, ids):
        return "".join(DECODE[int(i) if not isinstance(i, int) else i] for i in ids)


class _StubOut:
    def __init__(self, logits):
        self.logits = logits


class StubModel:
    """logits[b, t, :] = TABLE[input_ids[b, t]] -- a well-defined next-token law, nothing more."""
    device = "cpu"

    def __init__(self):
        tab = torch.zeros(V_STUB, V_STUB)
        tab[5, 23] = 8.0     # after "Answer:" the model wants ' Car' ...
        tab[5, 10] = 4.0     # ... then ' bomb'
        tab[5, 12] = 3.0     # ... then ' Bomb'
        tab[5, 20] = -2.0    # ' carrot' is the one spelling the old readout could see
        tab[23, 22] = 10.0   # ' Car' -> 'rot'
        tab[24, 22] = 10.0
        tab[21, 22] = 10.0
        self.table = tab

    def __call__(self, input_ids=None, attention_mask=None, use_cache=False):
        return _StubOut(self.table[input_ids.long()])


class StubLM:
    def __init__(self):
        self.tokenizer = StubTok()
        self.model = StubModel()


def _single_next_token_logodds(lm, context, c_ids, w_ids):
    """The PRE-FIX statistic, computed here exactly as `readout` computed it (and still does under
    --readout-ids primary): log-softmax at the final position, logsumexp over each id group."""
    ids = lm.tokenizer(context, add_special_tokens=False)["input_ids"]
    lp = torch.log_softmax(lm.model(input_ids=torch.tensor([ids])).logits[0, -1, :].float(), -1)
    c = float(lp[torch.tensor(list(c_ids))].logsumexp(0))
    w = float(lp[torch.tensor(list(w_ids))].logsumexp(0))
    mass = float(lp[torch.tensor(sorted(set(c_ids) | set(w_ids)))].logsumexp(0).exp())
    return c - w, mass


def test_c6_g1_headline_is_computed_from_this_statistic():
    """WHICH NUMBER THIS FIX IS ABOUT. g1_stratified.json names its readout, and the +68%-of-span
    headline with CI [+50,+95] over 24 families / 6 domains is one of its arms."""
    path = os.path.join(REPO, "outputs", "boombness", "g1_stratified.json")
    if not os.path.exists(path):
        pytest.skip("committed G1 artifact not present")
    with open(path) as fh:
        g1 = json.load(fh)["G1"]
    assert g1["readout"] == "semantic_logodds"
    arm = g1["pairs"]["harm_ctx"]["arms"]["transplant|demos_only|L18"]
    assert round(arm["frac_of_span"], 2) == 0.68
    assert [round(x, 2) for x in arm["frac_ci95"]] == [0.50, 0.95]
    assert (arm["n_families"], arm["n_domains"]) == (24, 6)


def test_c6_the_old_instrument_structurally_cannot_spell_the_codeword():
    """THE DEFECT, as a property of the tokenizer rather than of any run. Every single-next-token
    id set is asymmetric: 4 ids for the concept against 1 for the codeword, and the model's
    preferred spelling (' Car') is REJECTED by `readout_ids` by design because it is the generic
    English word `car`."""
    tok = StubTok()
    rc = sg.readout_ids(tok, "bomb")
    rw = sg.readout_ids(tok, "carrot")
    assert len(rc["full_word_ids"]) == 4 and len(rw["full_word_ids"]) == 1
    assert 23 in rw["rejected_first_ids"], "' Car' is rejected: `car` is the generic English word"
    c_ids, w_ids, _ = sg.readout_id_pair(tok, "bomb", "carrot", mode="full_word")
    assert (len(c_ids), len(w_ids)) == (4, 1), "4-ids-to-1 toward the concept"


def test_c6_whole_answer_variant_sets_are_symmetric_by_construction():
    """The fix's premise: both options get the same number of surface forms, built by one rule."""
    conc = sg.answer_variants("bomb", True)
    code = sg.answer_variants("carrot", True)
    assert conc == [" bomb", " Bomb"] and code == [" carrot", " Carrot"]
    assert len(conc) == len(code) == 2


def test_c6_the_two_instruments_disagree_in_SIGN_on_the_same_model(c6_module):
    """FAILS AGAINST THE PRE-C-6 MODULE, which has no `whole_answer_semantic` to call at all.

    One model, one context, two instruments. The single-next-token readout can only see
    ' carrot' (log-odds strongly POSITIVE: the concept wins) while the model in fact wants to
    answer ' Car'+'rot' (whole-answer log-odds NEGATIVE: the codeword wins). The published
    statistic is therefore not merely noisy on this model -- it has the wrong sign, which is the
    concrete meaning of 'the instrument cannot represent the model's preferred spelling'."""
    assert not hasattr(c6_module, "whole_answer_semantic"), \
        "pre-C-6 module unexpectedly has the whole-answer readout"
    lm = StubLM()
    ctx = "CTX" + "Answer:"
    c_ids, w_ids, _ = sg.readout_id_pair(lm.tokenizer, "bomb", "carrot", mode="primary")
    old_lo, old_mass = _single_next_token_logodds(lm, ctx, c_ids, w_ids)
    new = ap.whole_answer_semantic(lm, ctx, {"concept": sg.answer_variants("bomb", True),
                                             "codeword": sg.answer_variants("carrot", True)})
    assert old_lo > 0.0, "the old instrument says CONCEPT"
    assert new["semantic_logodds"] < 0.0, "the answer the model actually gives is the CODEWORD"
    # ... and the old instrument was reading a tail while the new one is a forced choice.
    assert old_mass < 0.05 < 0.9 < new["option_mass"]
    assert new["option_mass"] / old_mass > 50


def test_c6_option_mass_and_top1_are_recorded_by_both_instruments(c6_module):
    """FAILS AGAINST THE PRE-C-6 MODULE: `readout` there emits neither key, and the absence of
    `option_mass` is precisely what let a readout decided inside a 1e-5 tail ship for two months.
    `top1_id` is the token the model actually wants -- the field that would have shown ' Car'."""
    import inspect
    old_src = inspect.getsource(c6_module.readout)
    assert "option_mass" not in old_src and "top1_id" not in old_src
    lm = StubLM()
    new = ap.whole_answer_semantic(lm, "CTXAnswer:", {
        "concept": sg.answer_variants("bomb", True),
        "codeword": sg.answer_variants("carrot", True)})
    assert new["top1_id"] == 23, "the model wants ' Car', which no single-token readout can score"
    assert set(new) >= {"option_mass", "top1_id", "semantic_logodds",
                        "n_variants_concept", "n_variants_codeword"}
    assert new["n_variants_concept"] == new["n_variants_codeword"] == 2


def test_c6_default_readout_mode_is_whole_answer_and_was_primary_before(c6_module):
    """FAILS AGAINST THE PRE-C-6 MODULE by construction: its default is the broken instrument.
    Ported from score_behavior.py, which already runs
    `--readout-ids whole_answer --answer-prefix "Answer:"`."""
    import inspect
    new_src = inspect.getsource(ap.main)
    old_src = inspect.getsource(c6_module.main)
    assert '"--readout-ids", default="whole_answer"' in new_src
    assert '"--readout-ids", default="primary"' in old_src
    assert "whole_answer" not in old_src
    # the old instrument stays REACHABLE -- the point is the default, not the deletion.
    assert set(ap.SEMANTIC_READOUT_MODES) == {"primary", "full_word", "whole_answer"}
    assert ap.DEFAULT_ANSWER_PREFIX == "Answer:"


def test_c6_whole_answer_is_never_passed_to_readout_id_pair():
    """`whole_answer` is a SCORING mode, not an id-SELECTION mode. Threading it into the scorer and
    not into the id builder is the one-of-two-paths slip that killed job 764743; `readout_id_pair`
    raises on it deliberately, and main() must map it to `primary` the way score_behavior does."""
    import inspect
    with pytest.raises(ValueError):
        sg.readout_id_pair(StubTok(), "bomb", "carrot", mode="whole_answer")
    assert '"primary" if args.readout_ids == "whole_answer"' in inspect.getsource(ap.main)


def test_c6_readout_refuses_an_unknown_semantic_mode():
    """A typo in the mode must die, not silently fall through to the old instrument."""
    with pytest.raises(ValueError):
        ap.readout(None, [1], None, [1], [2], [], {}, 0, semantic_mode="whole-answer")
    with pytest.raises(ValueError):
        ap.readout(None, [1], None, [1], [2], [], {}, 0, semantic_mode="whole_answer",
                   templated=None, sem_variants=None)


def test_c6_rows_are_versioned_so_committed_artifacts_stay_readable(rows):
    """'Do not silently change the default in a way that makes old artifacts unreadable.' Every
    committed row predates the change and carries NO mode key; a reader that finds none is looking
    at v1 and must read it as `primary`. New rows say which instrument produced them."""
    assert ap.ROW_SCHEMA_VERSION == 2
    assert all("semantic_readout_mode" not in r for r in rows)
    assert all("row_schema_version" not in r for r in rows)
    assert all("semantic_logodds" in r for r in rows), "v1 rows still parse as before"


def test_c6_answer_prefix_must_not_shift_the_patch_positions(c6_module):
    """FAILS AGAINST THE PRE-C-6 MODULE (no such function).

    The patch positions index `tokenize(templated)`; the whole-answer readout forwards
    `tokenize(templated + answer_prefix)`. A tokenizer that merges across the join makes index k
    mean two different tokens in the two sequences -- the absolute-position-index bug class that
    has hit this repo twice. The guard is checked live per prompt."""
    assert not hasattr(c6_module, "answer_prefix_preserves_positions")
    tok = StubTok()
    ids = tok("CTX")["input_ids"]
    assert ap.answer_prefix_preserves_positions(tok, "CTX", "Answer:", ids) is True
    assert ap.answer_prefix_preserves_positions(tok, "CTX", "", ids) is True

    class MergingTok(StubTok):
        def __call__(self, text, add_special_tokens=False):
            if text == "CTXAnswer:":
                return {"input_ids": [1, 2, 99]}      # the join re-tokenized: index 2 moved
            return StubTok.__call__(self, text, add_special_tokens)

    assert ap.answer_prefix_preserves_positions(MergingTok(), "CTX", "Answer:", ids) is False


# --------------------------------------------------------------------------- #
# C-6 -- one sequence per forward, because the house patch hooks edit batch row 0 only
# --------------------------------------------------------------------------- #
class _Blk(torch.nn.Module):
    def forward(self, h):
        return h + 1.0


class _Inner(torch.nn.Module):
    def __init__(self, n):
        super().__init__()
        self.layers = torch.nn.ModuleList([_Blk() for _ in range(n)])


class _ToyLM(torch.nn.Module):
    """The minimum `ds_common._get_layers` accepts, so the REAL LayerPatch can be exercised."""

    def __init__(self, n=3):
        super().__init__()
        self.model = _Inner(n)

    def forward(self, x):
        for blk in self.model.layers:
            x = blk(x)
        return x


def test_c6_house_patch_hooks_edit_batch_row_zero_only():
    """THE HAZARD, measured against the real helper. `string_option_readout` batches its variants
    into one forward; `ds_common.LayerPatch` writes `hidden[0, p, :]`. So a batched call under a
    patch would score variant 0 patched and the rest UNPATCHED -- and the concept and the codeword
    live in different rows of that batch, making `semantic_logodds` a patched-vs-unpatched
    comparison. If this test ever fails, the helpers became batch-aware and
    WHOLE_ANSWER_MAX_BATCH may be raised."""
    m = _ToyLM()
    x = torch.zeros(2, 4, 8)
    assert torch.equal(m(x)[0], m(x)[1]), "unpatched, the two rows are identical"
    with ds_common.LayerPatch(m, 0, [1], vector=torch.ones(8), mode="add", alpha=5.0):
        out = m(x)
    assert not torch.equal(out[0, 1], out[1, 1]), "row 0 patched, row 1 not -- the hazard"
    assert torch.equal(out[1], m(x)[1]), "row 1 is exactly the unpatched result"


def test_c6_whole_answer_readout_forces_one_sequence_per_forward(monkeypatch):
    """FAILS AGAINST ANY VERSION THAT LETS signals BATCH: the readout must pass max_batch=1."""
    assert ap.WHOLE_ANSWER_MAX_BATCH == 1
    seen = {}

    def fake(lm, context, options, max_batch=16):
        seen["max_batch"] = max_batch
        return {"logp_concept": -1.0, "logp_codeword": -2.0, "p_concept": 0.3,
                "p_codeword": 0.1, "option_mass": 0.4, "top1_id": 7,
                "n_variants_concept": 2, "n_variants_codeword": 2}

    monkeypatch.setattr(sg, "string_option_readout", fake)
    ap.whole_answer_semantic(StubLM(), "CTXAnswer:", {"concept": [" bomb"], "codeword": [" carrot"]})
    assert seen["max_batch"] == 1


def test_c6_whole_answer_readout_delegates_to_signals_not_a_local_copy(monkeypatch):
    """Reuse, checked by identity: the numbers must come from `signals.string_option_readout`, the
    same helper score_behavior.py uses, so the two scripts cannot drift apart."""
    called = []
    monkeypatch.setattr(sg, "string_option_readout",
                        lambda *a, **k: (called.append(1) or {
                            "logp_concept": -1.0, "logp_codeword": -3.0, "p_concept": 0.3,
                            "p_codeword": 0.05, "option_mass": 0.35, "top1_id": 7,
                            "n_variants_concept": 2, "n_variants_codeword": 2}))
    out = ap.whole_answer_semantic(StubLM(), "CTXAnswer:",
                                   {"concept": [" bomb"], "codeword": [" carrot"]})
    assert called == [1]
    assert out["semantic_logodds"] == 2.0


# =========================================================================== #
# T10 (b) -- VERIFICATION: a readout layer inside a patched window is refused
# =========================================================================== #
def test_t10_no_window_containing_a_readout_layer_is_ever_reported_valid():
    """The refusal, as a property over the whole window x readout-layer grid rather than over the
    handful of windows a previous test happened to name. For EVERY window and EVERY readout layer
    R inside it, R is refused: it is never in `readout_layers_valid`, and the window as a whole is
    valid for R only when it lies strictly below R."""
    windows = ap.build_windows(32, [8, 9, 10, 14, 15, 16, 17, 18, 19, 20, 21, 12, 24])
    checked = 0
    for wname, wl in windows.items():
        f = ap.readout_window_flags(ds_common, wl, READOUT_LAYERS)
        for R in READOUT_LAYERS:
            if R in set(wl):
                assert R not in f["readout_layers_valid"], f"{wname} @ L{R} was not refused"
                assert R in f["readout_layers_inside_window"]
                checked += 1
            if R in f["readout_layers_valid"]:
                assert max(wl) < R, f"{wname} is not strictly upstream of L{R}"
    assert checked > 0, "the grid must actually contain overlapping cases"


def test_t10_the_refusal_rule_is_the_house_helper_not_a_local_copy():
    """`ds_common.patch_layer_sweep(R)` is the single source of truth (defects C1/C3). Its own
    contract -- a patch at L==R overwrites the readout with zero propagation, so the sweep stops
    at R-1 -- is what the refusal means, and the module derives its answer from it (see
    test_t10_flags_use_the_house_helper_not_a_local_reimplementation, which monkeypatches it)."""
    for R in (1, 8, 12, 18, 31):
        allowed = ds_common.patch_layer_sweep(R)
        assert R not in allowed and max(allowed) == R - 1


def test_t10_the_default_readout_layers_are_refused_by_the_default_windows():
    """The concrete claim in the defect table: the default readout layers sit inside the default
    windows, so the default configuration is the compromised one and must say so."""
    windows = ap.build_windows(32, [8, 12, 18, 24])
    inside = [w for w, wl in windows.items()
              if ap.readout_window_flags(ds_common, wl, READOUT_LAYERS)[
                  "readout_inside_patched_window"]]
    assert len(inside) == len(windows) - 1 and "L0-4" not in inside
    f_all = ap.readout_window_flags(ds_common, windows["all"], READOUT_LAYERS)
    assert f_all["readout_layers_valid"] == [], "no readout layer survives scope=all"
    assert f_all["n_readout_layers_inside_window"] == len(READOUT_LAYERS)


# =========================================================================== #
# T9b -- VERIFICATION: a single draw cannot be reported as a band, on EITHER path
# =========================================================================== #
def test_t9b_a_single_draw_cell_cannot_claim_the_band_identity(c6_module):
    """FAILS AGAINST THE PRE-FIX MODULE, which emitted `intervention="add_control_band"` for any
    number of surviving draws including one. The guard is on the row's IDENTITY, not on a field:
    retraction #7 and R-12 were both fake bands whose sd field looked fine and whose tell was arms
    agreeing to four decimals, so a downstream filter on `add_control_band` must be unable to
    select a single-draw cell at all."""
    import inspect
    old = inspect.getsource(c6_module.run_pair)
    assert '"intervention": "add_control_band"' in old, "pre-fix: the name was unconditional"
    assert "band_row_intervention" not in old
    assert ap.band_row_intervention(1) == ap.SINGLE_DRAW_ROW_INTERVENTION
    assert ap.band_row_intervention(0) == ap.SINGLE_DRAW_ROW_INTERVENTION
    assert ap.band_row_intervention(2) == ap.BAND_ROW_INTERVENTION
    assert ap.band_row_intervention(12) == ap.BAND_ROW_INTERVENTION
    assert ap.BAND_ROW_INTERVENTION != ap.SINGLE_DRAW_ROW_INTERVENTION
    # and the aggregate itself still refuses to invent an sd for one draw
    assert ap.between_draw_band([{"m": 1.0}])["between_draw_sd|m"] is None
    assert "band_row_intervention(k)" in inspect.getsource(ap.run_pair)


def test_t9b_run_level_flag_follows_the_draws_ACHIEVED_not_the_draws_REQUESTED(c6_module):
    """FAILS AGAINST THE PRE-FIX MODULE: there `control_draws_underpowered` was a pure function of
    `args.n_control_draws`, so a run that asked for 12 and achieved 1 reported 'not underpowered'.
    This is R-12's exact shape -- a quantity threaded into the path that was looked at and dropped
    on the path that produced the artifact."""
    import inspect
    old = inspect.getsource(c6_module.main)
    assert "control_underpowered = (n_control_draws < 10" in old
    assert "control_draws_underpowered(" not in old
    # requested is fine, achieved is not -> underpowered
    assert ap.control_draws_underpowered(12, [12, 12, 1], True) is True
    assert ap.control_draws_underpowered(12, [12, 12, 12], True) is False
    # requested is not fine -> underpowered whatever happened
    assert ap.control_draws_underpowered(3, [3, 3], True) is True
    # no stochastic control was requested at all -> the notion does not apply
    assert ap.control_draws_underpowered(1, [1], False) is False
    assert "control_draws_underpowered(" in inspect.getsource(ap.main)


def test_t9b_both_paths_must_receive_the_same_draw_count(c6_module):
    """THE R-12 GUARD, on both paths at once. `expand_add_directions` decides which draw NAMES get
    scored; `build_control_directions` decides which draw VECTORS exist. run_pair silently
    `continue`s on a name with no vector, so a parameter dropped on either path shrinks the band
    without a word -- to one draw in the limit. FAILS AGAINST THE PRE-FIX MODULE, which has no
    such check."""
    assert not hasattr(c6_module, "assert_control_draws_consistent")
    dsf = _d_surface()
    names = ap.expand_add_directions("d_surface,random,orthogonal", 12)
    ap.assert_control_draws_consistent(names, ap.build_control_directions(sg, dsf, 20260816, 12))
    # the defect: the count reached one path and not the other
    with pytest.raises(ValueError) as e:
        ap.assert_control_draws_consistent(names, ap.build_control_directions(sg, dsf, 20260816, 1))
    assert "random#1" in str(e.value) or "orthogonal#1" in str(e.value)
    # a fitted direction that is simply absent is NOT this defect and must not be reported as it
    ap.assert_control_draws_consistent(["d_surface", "d_context"], {})
    import inspect
    assert "assert_control_draws_consistent(add_dirs, dirs)" in inspect.getsource(ap.main)


def test_t9b_the_band_never_averages_an_id_column(c6_module):
    """C-6 put `top1_id` and `n_variants_*` on every row. They are numeric and neither is a
    quantity: the mean of twelve token ids is a token id no draw emitted. FAILS AGAINST THE
    PRE-FIX MODULE, whose `between_draw_band` averaged every numeric non-bool column."""
    import inspect
    assert "is_averageable_key" not in inspect.getsource(c6_module.between_draw_band)
    recs = [{"semantic_logodds": 1.0, "top1_id": 10, "n_variants_concept": 2,
             "nexttok|top1_id": 10, "option_mass": 0.4},
            {"semantic_logodds": 3.0, "top1_id": 4000, "n_variants_concept": 2,
             "nexttok|top1_id": 4000, "option_mass": 0.6}]
    band = ap.between_draw_band(recs)
    assert band["semantic_logodds"] == 2.0 and band["option_mass"] == 0.5
    for k in ("top1_id", "nexttok|top1_id", "n_variants_concept"):
        assert k not in band, f"{k} must not be averaged"
        assert f"between_draw_sd|{k}" not in band
    # the old code would have published 2005.0 as "the" top1 token id
    old_band = c6_module.between_draw_band(recs)
    assert old_band["top1_id"] == 2005.0



# =========================================================================== #
# ADVERSARIAL VERIFICATION, 2026-08-19 -- four defects found IN the C-6/T9b patch itself.
#
# HOW THE PRE-FIX FAILURE IS DEMONSTRATED. The C-6/T9b patch is not in git history (it was still
# in the working tree when it was reviewed), so `_rev_before_or_head` cannot export it and a
# `v_module` fixture would silently resolve to the PRE-C-6 module instead -- comparing against
# the wrong revision, which is the exact trap `_rev_before` was written to close. These tests
# therefore assert on the LIVE module only, and the demonstration is a file swap:
#
#   cp src/boombness/aggressive_patching.py /tmp/verified.py
#   cp <the C-6/T9b patch as reviewed>      src/boombness/aggressive_patching.py
#   pytest tests/test_patching_readout.py -k test_v      ->  5 failed, 0 passed
#   cp /tmp/verified.py                     src/boombness/aggressive_patching.py
#
# Once this lands in history, pin them with `_rev_before("def option_mass_gate")`.
# =========================================================================== #
def test_v1_tail_gate_cannot_pass_a_run_it_never_evaluated():
    """DEFECT 1 (dead guard). The ported tail gate iterated the option-mass buckets and could fail
    only on a bucket it SAW:

        for bucket, vals in sorted(option_mass.items()):
            if not vals: continue
            ...
        if tail_fail and not args.allow_tail_readout: return 4

    A run in which every family was skipped -- by `resolve:`, by `multi_subtoken_target:`, or by
    the very `answer_prefix_shifts_positions:` guard this patch ADDED -- reaches `tail_fail == []`,
    writes `option_mass_gate: "PASS"` into summary.json and exits 0.
    `extract_boombness.resolve_occurrences` documents jobs 764745-747, where exactly that shape
    killed 179/179 rows in three arms while SLURM reported COMPLETED 0:0. The sibling C-6 port
    (`surgical_knockout.option_mass_gate`) already carries the missing-bucket check; it was
    dropped on the way into this module -- the one-of-two-paths shape, across scripts."""
    gating = [ap.semantic_mass_bucket("semantic_one_word", iv) for iv in ap.GATED_INTERVENTIONS]
    assert gating == ["semantic/semantic_one_word/none",
                      "semantic/semantic_one_word/donor_ceiling"]
    # (a) nothing measured at all -> NOT a pass
    summary, fatal = ap.option_mass_gate({}, 0.05, gating)
    assert summary == {} and fatal, "a gate that never saw its own bucket has not passed"
    assert "never evaluated" in fatal[0]
    # (b) one gating bucket present and healthy, the other absent -> still not a pass
    summary, fatal = ap.option_mass_gate({gating[0]: [0.9, 0.9, 0.9]}, 0.05, gating)
    assert summary[gating[0]]["reportable"] is True
    assert any(gating[1] in f for f in fatal)
    # (c) both present and healthy -> pass
    summary, fatal = ap.option_mass_gate({g: [0.9, 0.8, 0.95] for g in gating}, 0.05, gating)
    assert fatal == [] and all(summary[g]["gates_the_run"] for g in gating)
    # (d) an INTERVENED bucket in the tail is a finding about the arm, never a gate failure ...
    m = {g: [0.9, 0.8, 0.95] for g in gating}
    tr = ap.semantic_mass_bucket("semantic_one_word", "transplant")
    m[tr] = [1e-6, 1e-6, 1e-6]
    summary, fatal = ap.option_mass_gate(m, 0.05, gating)
    assert fatal == [] and summary[tr]["reportable"] is False and summary[tr]["gates_the_run"] is False
    # ... while a GATING bucket in the tail is
    m[gating[0]] = [1e-6, 1e-6, 1e-6]
    summary, fatal = ap.option_mass_gate(m, 0.05, gating)
    assert len(fatal) == 1 and gating[0] in fatal[0]
    # (e) and the gate is a module-level function, so it is testable at all -- the patch's was
    # written inline in main() and had no test of any kind.
    import inspect
    assert "option_mass_gate(option_mass" in inspect.getsource(ap.main)


def test_v1b_the_gate_governs_buckets_by_identity_not_by_the_key_spelling():
    """DEFECT 1, second half. The patch decided which buckets it governed with

        gated = bucket.rsplit("/", 1)[-1] in ("none", "donor_ceiling")

    i.e. by an incidental property of the key's SPELLING -- the property all five of this
    project's dead guards matched on. The gating buckets are now identities built from the run's
    own `--query-kind` by the same function the emitter builds the key with, so a bucket from a
    different query kind cannot satisfy this run's gate and its absence is reported."""
    import inspect
    gating = [ap.semantic_mass_bucket("semantic_one_word", iv) for iv in ap.GATED_INTERVENTIONS]
    other = {ap.semantic_mass_bucket("comprehension_usage", "none"): [0.9] * 5,
             ap.semantic_mass_bucket("comprehension_usage", "donor_ceiling"): [0.9] * 5}
    summary, fatal = ap.option_mass_gate(other, 0.05, gating)
    assert fatal and "never evaluated" in fatal[0], \
        "a healthy `none` bucket from ANOTHER query kind must not satisfy this run's gate"
    src = inspect.getsource(ap.run_pair)
    assert "semantic_mass_bucket(" in src
    assert 'f"semantic/{recip' not in src, "the bucket key must not be spelled twice"
    assert 'rsplit("/", 1)[-1]' not in inspect.getsource(ap.main)


def test_v2_the_readout_pair_is_a_property_of_the_slice_not_of_row_zero():
    """DEFECT 2 (example[0] reused across examples -- the class that has hit this repo twice).
    `main()` built the readout ids AND the whole-answer variant STRINGS from
    `rows[0]["concept"], rows[0]["codeword"]` once for the entire run. The sibling C-6 port called
    this out by name on the same day (`surgical_knockout.readout_for`: 'READOUT IDS AND ANSWER
    VARIANTS ARE PER (concept, codeword), NOT PER rows[0] ... inert on today's bank only because
    all eligible rows share one pair, which is an incidental property of the bank, not a
    contract'). C-6 makes the consequence worse than it was, because the variants are now
    TEACHER-FORCED as the answer: a second pair in the bank would have every row of it scored on
    another family's words, at a perfectly healthy-looking option mass."""
    import inspect
    assert 'rows[0]["concept"]' not in inspect.getsource(ap.main)
    one = [{"concept": "bomb", "codeword": "carrot"}] * 3
    assert ap.assert_single_concept_codeword_pair(one) == ("bomb", "carrot")
    with pytest.raises(SystemExit) as e:
        ap.assert_single_concept_codeword_pair(one + [{"concept": "bomb", "codeword": "tulip"}])
    assert "distinct (concept, codeword) pairs" in str(e.value)
    # ... and it refuses nothing on the committed bank: the defect is latent, not live, which is
    # why the fix is a refusal rather than a re-run.
    bank = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")
    if not os.path.exists(bank):
        pytest.skip("bank not present")
    sel = []
    with open(bank) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") == "semantic_one_word" and r.get("bank_block") == "core2x2":
                sel.append({"concept": r["concept"], "codeword": r["codeword"]})
    assert len(sel) == 288
    assert ap.assert_single_concept_codeword_pair(sel)


def test_v3_whole_answer_refuses_a_query_whose_answer_is_not_the_pair():
    """DEFECT 3 (the C-6 port took only half of score_behavior's contract). `--query-kind` accepts
    every kind in `prompt_families.QUERY_KINDS`; `comprehension_usage` is
    `occurrence_analysis_safe=True`, so it survives the module's existing refusal, and it is a
    live 288-row slice of the bank. Its declared answer vocabulary is "literal"/"coded"
    (`scores: "comprehension"`), and score_behavior.py carries a SECOND variant set
    (`comp_variants`) and dispatches on the query kind. The port took only the semantic half, so
    that run would teacher-force " bomb"/" Carrot" as the answer to a literal-or-coded question
    and label the result `semantic_logodds`."""
    from prompt_families import QUERY_KINDS as QK
    import inspect
    # the mis-aimed combination really was reachable
    assert QK["comprehension_usage"]["occurrence_analysis_safe"] is True
    assert QK["comprehension_usage"]["scores"] == "comprehension"
    assert QK["semantic_one_word"]["scores"] == "semantic"

    ap.assert_query_kind_answers_with_the_pair("semantic_one_word", QK)
    for bad in ("comprehension_usage", "behavioral"):
        with pytest.raises(SystemExit) as e:
            ap.assert_query_kind_answers_with_the_pair(bad, QK)
        assert "answer space is not the (concept, codeword) pair" in str(e.value)
    # refused by the bank's OWN declared answer space, not by a hard-coded list of kind names
    body = inspect.getsource(ap.assert_query_kind_answers_with_the_pair).split('"""')[2]
    assert "comprehension_usage" not in body and "behavioral" not in body
    # and ONLY the new instrument is narrowed: `primary` still reproduces the pre-C-6 runs
    assert ('if args.readout_ids == "whole_answer":\n'
            "        assert_query_kind_answers_with_the_pair") in inspect.getsource(ap.main)


def test_v4_a_band_that_was_never_measured_is_not_a_powered_band():
    """DEFECT 4 -- the same never-evaluated-is-not-passed shape, one function over. With
    stochastic controls requested and ZERO band cells produced, `any([])` is False, so the
    patch's `control_draws_underpowered` reported the run NOT underpowered while its control band
    did not exist at all. T9b's whole point is that the flag must follow what happened."""
    assert ap.control_draws_underpowered(12, [], True) is True
    # the cases the C-6/T9b patch already got right must not regress
    assert ap.control_draws_underpowered(12, [12, 12, 1], True) is True
    assert ap.control_draws_underpowered(12, [12, 12, 12], True) is False
    assert ap.control_draws_underpowered(3, [3, 3], True) is True
    assert ap.control_draws_underpowered(1, [1], False) is False
    assert ap.control_draws_underpowered(12, [], False) is False
