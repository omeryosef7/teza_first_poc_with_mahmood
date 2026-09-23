"""--knockout-cells: PR-CSI-014's per-cell knockout, and the six ways it could lie.

WHY. `--knockout-heads 2` ties head 2 across the WHOLE --intervene band: on band 6-14 it knocks the
head out at layers 6,7,...,14 simultaneously. Every PR-CSI-012 census arm was that shape, which is
why D34 says WHICH heads carry load and cannot say AT WHAT DEPTH. A cell selector addresses one
(layer, head) pair.

The implementation choice under test: a cell selector becomes ONE HOOK PER LAYER, each built for a
single-layer band with that layer's own head list. `pair_common.py` is untouched -- both knockout
classes already take (layer_idxs, heads) and `make_intervention` already returns a LIST.

The silent failures this guards against:
  1. the flag is accepted but never reaches the hook -> an arm named "L10h2" knocks head 2 out at all
     nine layers and trivially reproduces the 9-cell effect;
  2. the per-layer hooks are handed DIFFERENT stats dicts -> the realised dose is counted once
     instead of summed, and the identity check reads 1/9 of the arm it thinks it is reading;
  3. a cell names a layer OUTSIDE the band -> no hook is installed for it, the arm edits less than
     its name says, and a no-op knockout scores as a perfectly healthy null;
  4. the composed recursion drops knock_cells on one leg (it has dropped a threaded argument on that
     exact line twice before);
  5. --knockout-heads and --knockout-cells are both accepted -> the arm records two selectors and
     cannot be identified from its own artifact (S-227's collision, with the layer axis added);
  6. the default changes -> every Phase 2-4 and PR-CSI-010/011/012/013 arm is silently re-scoped.

Run:  python -m pytest tests/test_knockout_cells.py -q
"""
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness", "score_behavior.py")


class _FakeKO:
    def __init__(self, layer_idxs, heads, stats, mode=None):
        self.layers, self.heads, self.stats, self.mode = list(layer_idxs), heads, stats, mode


class _PC:
    """Records every hook built, with the layer list, head list and the stats OBJECT IDENTITY."""

    def __init__(self):
        self.made = []

    def AllQueryAttentionKnockout(self, model, layers, blocked_keys=None, heads=None, stats=None):
        k = _FakeKO(layers, heads, stats)
        self.made.append(k)
        return k

    def ScopedAttentionKnockout(self, model, layers, blocked_keys=None, mode=None, query_span=None,
                                demo_span=None, heads=None, stats=None, surface_span=None):
        k = _FakeKO(layers, heads, stats, mode=mode)
        self.made.append(k)
        return k


class _LM:
    num_layers = 32
    model = types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=16,
                                                               num_attention_heads=32))


DEMO = [11, 12, 13, 14, 15]
BAND = [6, 7, 8, 9, 10, 11, 12, 13, 14]


def _spec(layers=None):
    return {"direction": "demo_all", "mode": "attn_knockout",
            "layers": list(BAND if layers is None else layers), "alpha": 1.0}


def test_one_cell_builds_exactly_one_hook_on_exactly_that_layer():
    """FAILURE 1. The whole point: L10h2 must edit head 2 at layer 10 and nowhere else."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={10: [2]})
    assert len(pc.made) == 1, (
        f"expected ONE hook for one cell, got {len(pc.made)} -- a cell arm that installs a hook per "
        f"band layer is the 9-cell arm wearing the 1-cell arm's name")
    assert pc.made[0].layers == [10], f"hook built for layers {pc.made[0].layers}, not [10]"
    assert pc.made[0].heads == [2], f"hook got heads {pc.made[0].heads}, not [2]"


def test_cells_on_several_layers_group_by_layer():
    """Two cells on two layers -> two hooks, each carrying only its own layer's heads."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={7: [23], 14: [19]})
    got = sorted((h.layers, h.heads) for h in pc.made)
    assert got == [([7], [23]), ([14], [19])], f"grouped wrong: {got}"


def test_two_cells_on_one_layer_share_a_hook():
    """L10h2 + L10h19 is ONE hook with two heads, not two hooks on the same layer."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={10: [2, 19]})
    assert len(pc.made) == 1, f"expected one hook for one layer, got {len(pc.made)}"
    assert pc.made[0].heads == [2, 19]


def test_every_cell_hook_shares_ONE_stats_dict():
    """FAILURE 2. The counters accumulate via setdefault+=, so they must all point at ONE dict.

    Hand the hooks separate dicts and the realised dose is counted per layer instead of summed --
    the identity check would then read a fraction of the arm it thinks it is reading."""
    import score_behavior as sb
    pc = _PC()
    shared = {}
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats=shared,
                         knock_cells={7: [23], 10: [2], 14: [19]})
    assert len(pc.made) == 3
    for h in pc.made:
        assert h.stats is shared, (
            "a cell hook was handed a DIFFERENT stats dict; the realised dose would not sum across "
            "layers and the dose identity would be wrong by a factor of len(cells)")


def test_cell_outside_the_band_REFUSES():
    """FAILURE 3. The refusal must happen where `band` is authoritative, i.e. in make_intervention."""
    import score_behavior as sb
    pc = _PC()
    with pytest.raises(SystemExit) as e:
        sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                             demo_keys=DEMO, seq_len=64, knock_stats={},
                             knock_cells={31: [2]})       # layer 31 is not in band 6-14
    assert "outside the --intervene band" in str(e.value), str(e.value)
    assert pc.made == [], "a hook was built despite the refusal"


def test_band_layer_with_no_named_cell_gets_no_hook():
    """The complement of failure 3: naming one cell must not install hooks on the other 8 layers."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={10: [2]})
    assert [h.layers for h in pc.made] == [[10]]


def test_scoped_path_also_carries_cells():
    """PR-CSI-013/014 run target_surface_row_only, NOT the legacy scope. Both paths must work."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_scope="target_surface_row_only",
                         protected=frozenset({40, 41}), surface_span=frozenset({41}),
                         knock_cells={10: [2]})
    assert len(pc.made) == 1 and pc.made[0].layers == [10] and pc.made[0].heads == [2]
    assert pc.made[0].mode == "target_surface_row_only", (
        "the scope was dropped on the cell path -- a scoped arm demoted to the all-query knockout "
        "is a LARGER intervention under the scoped arm's name")


def test_composed_arms_forward_cells_too():
    """FAILURE 4. This exact line has dropped a threaded argument twice."""
    import torch  # noqa: F401
    import score_behavior as sb
    pc = _PC()
    pc.AllPositionProjectOut = lambda *a, **k: object()
    spec = {"composed": [_spec([10]), _spec([14])]}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={10: [2], 14: [2]})
    assert [(h.layers, h.heads) for h in pc.made] == [([10], [2]), ([14], [2])], \
        "the composed recursion dropped knock_cells on one leg"


def test_default_is_unchanged_when_no_cells_are_given():
    """FAILURE 6. Every existing arm -- Phases 2-4, PR-CSI-010/011/012/013 -- must be untouched."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={})
    assert len(pc.made) == 1, "one wide hook over the whole band, as every existing arm built"
    assert pc.made[0].layers == BAND
    assert pc.made[0].heads is None, "heads=None means ALL heads; the default changed"


def test_head_selector_still_works_beside_the_cell_selector():
    """--knockout-heads must be entirely unaffected by the new branch."""
    import score_behavior as sb
    pc = _PC()
    sb.make_intervention(None, pc, _LM(), _spec(), None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={}, knock_heads=[2])
    assert len(pc.made) == 1 and pc.made[0].layers == BAND and pc.made[0].heads == [2]


# ---- source-level guards: these live in main()'s argument handling, which needs a real model ----

def test_both_selectors_together_REFUSE():
    """FAILURE 5. Two selectors for one axis is two definitions of the arm."""
    src = open(SRC).read()
    assert "args.knockout_cells.strip() and args.knockout_heads.strip()" in src, \
        "the mutual-exclusion guard is gone; an arm could record two selectors"
    i = src.index("args.knockout_cells.strip() and args.knockout_heads.strip()")
    assert "REFUSING" in src[i:i + 400]


def test_cells_without_intervene_refuses():
    src = open(SRC).read()
    assert "args.knockout_cells.strip() and not args.intervene" in src
    i = src.index("args.knockout_cells.strip() and not args.intervene")
    assert "REFUSING" in src[i:i + 300]


def test_malformed_cell_refuses():
    """LAYER:HEAD is the whole grammar; anything else must die at argument time."""
    src = open(SRC).read()
    assert "is not LAYER:HEAD" in src, "the syntax check is gone"
    assert "non-integer" in src, "a non-integer layer/head would reach int() unguarded"


def test_cell_ranges_come_from_the_model_not_a_constant():
    src = open(SRC).read()
    i = src.index("from --knockout-cells")
    assert "num_attention_heads" in src[max(0, i - 2000):i], \
        "the head range is not taken from the model's own head count"
    assert "lm.num_layers" in src[max(0, i - 2000):i], \
        "the layer range is not taken from the model's own depth"


def test_duplicate_cells_refuse():
    src = open(SRC).read()
    assert "duplicate cell" in src


def test_empty_selector_refuses_rather_than_running_a_null():
    src = open(SRC).read()
    assert "parsed to ZERO cells" in src, \
        "an empty --knockout-cells would fall through to a no-op knockout scoring as a clean null"


def test_the_selection_is_echoed():
    """A cell-restricted run that does not say which cells is unauditable."""
    src = open(SRC).read()
    assert "knockout restricted to" in src and "CELL(S) of" in src


def test_composed_cell_outside_the_UNION_refuses():
    """The composed counterpart of failure 3, and the reason the check is on the UNION.

    Per-leg the cell belongs to no band, so a relaxed implementation would let every leg skip it and
    the arm would edit nothing under a name claiming an edit."""
    import torch  # noqa: F401
    import score_behavior as sb
    pc = _PC()
    pc.AllPositionProjectOut = lambda *a, **k: object()
    spec = {"composed": [_spec([10]), _spec([14])]}
    with pytest.raises(SystemExit) as e:
        sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                             demo_keys=DEMO, seq_len=64, knock_stats={},
                             knock_cells={31: [2]})       # in NO leg's band
    assert "UNION of the composed legs' bands" in str(e.value), str(e.value)
    assert pc.made == [], "a hook was built despite the refusal"


def test_composed_leg_carrying_no_cell_takes_the_ordinary_path():
    """A leg may legitimately carry none of the arm's cells; it must not hit the 'NO hook' refusal."""
    import torch  # noqa: F401
    import score_behavior as sb
    pc = _PC()
    pc.AllPositionProjectOut = lambda *a, **k: object()
    spec = {"composed": [_spec([10]), _spec([14])]}
    sb.make_intervention(None, pc, _LM(), spec, None, control_seed=1,
                         demo_keys=DEMO, seq_len=64, knock_stats={},
                         knock_cells={10: [2]})           # leg 2 (band [14]) gets nothing
    got = [(h.layers, h.heads) for h in pc.made]
    assert got == [([10], [2]), ([14], None)], (
        f"got {got}; the cell leg must be L10h2 and the cell-free leg must fall back to the "
        f"ordinary all-heads hook rather than refusing")
