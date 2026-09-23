"""R26. The CELL knockout against the REAL hook class, not a fake one.

WHY. `tests/test_knockout_cells.py` proves score_behavior BUILDS the right hooks -- it substitutes a fake
`pc` and inspects what was constructed. That is the right test for the wiring and it says NOTHING about
whether `pc.ScopedAttentionKnockout` actually WORKS when handed a single-layer band, nor whether N such
hooks sharing one `stats` dict accumulate their counters the way S-291 reasoned. Those two properties are
what the per-cell dose prediction of `DOSE_UNIT / band_width` rests on, and until this file they had never
been executed at all: the cell path has only ever run against a fake.

It reuses the ToyModel harness from doublespeak_causality/tests/test_allquery_attnknockout.py, so this is
the real class, a real 4-D additive mask and a real forward pass, at zero GPU cost.

Run:  python -m pytest tests/test_knockout_cells_integration.py -q
"""
import os
import sys

import pytest

torch = pytest.importorskip("torch")

DC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doublespeak_causality")
sys.path.insert(0, DC)
sys.path.insert(0, os.path.join(DC, "tests"))

from pair_common import ScopedAttentionKnockout, AllQueryAttentionKnockout   # noqa: E402
from test_allquery_attnknockout import ToyModel, _prefill_mask, _run         # noqa: E402

SEQ = 12
DEMO = [2, 3, 4]              # the "demonstration" key positions
QUERY = frozenset({9, 10, 11})
SURF = frozenset({10})        # the target-surface row, inside the query span


def _mk(model, layers, heads, stats):
    return ScopedAttentionKnockout(model, layers, blocked_keys=DEMO,
                                   mode="target_surface_row_only",
                                   query_span=QUERY, demo_span=DEMO,
                                   heads=heads, stats=stats, surface_span=SURF)


def test_a_single_layer_band_actually_edits_the_mask():
    """The cell path hands the real class a ONE-LAYER band. That had never been executed."""
    m = ToyModel(n_layers=9, n_heads=4)
    st = {}
    with _mk(m, [4], [2], st):
        _run(m, _prefill_mask(SEQ), SEQ)
    assert st["n_prefill_edits"] > 0, (
        "a one-layer cell hook made NO prefill edit -- a knockout that edits nothing scores as a "
        "perfectly clean null, which is the failure every refusal in this path exists to prevent")
    assert st["n_forward"] > 0


def test_N_cell_hooks_sharing_one_stats_dict_ACCUMULATE():
    """THE PROPERTY THE 224 PREDICTION RESTS ON.

    S-291 reasoned that the classes seed counters with setdefault and increment in _pre, so N per-layer
    hooks handed the SAME dict sum their edits. That was read off the source and never run."""
    one = {}
    m1 = ToyModel(n_layers=9, n_heads=4)
    with _mk(m1, [4], [2], one):
        _run(m1, _prefill_mask(SEQ), SEQ)
    three = {}
    m3 = ToyModel(n_layers=9, n_heads=4)
    h_a, h_b, h_c = _mk(m3, [4], [2], three), _mk(m3, [5], [2], three), _mk(m3, [6], [2], three)
    with h_a, h_b, h_c:
        _run(m3, _prefill_mask(SEQ), SEQ)
    assert three["n_prefill_edits"] == 3 * one["n_prefill_edits"], (
        f"three cell hooks recorded {three['n_prefill_edits']} prefill edits, not 3x the single-hook "
        f"{one['n_prefill_edits']}. The per-cell dose arithmetic DOSE_UNIT/band_width assumes exactly "
        f"this additivity, so if it fails the 224 prediction is wrong for a reason that has nothing to "
        f"do with the model")


def test_the_per_cell_dose_arithmetic_holds_on_the_toy():
    """One cell of a B-layer band records 1/B of what the whole band records, HEADS HELD FIXED.

    This is the toy-scale statement of `per_cell_dose = DOSE_UNIT / band_width`. It cannot predict the
    real 2016/9 = 224 (different model, different rows), but it does test that the RATIO is 1/B rather
    than something else -- which is the part of the claim that is about the hook and not about Llama."""
    BAND = [3, 4, 5, 6]
    whole = {}
    mw = ToyModel(n_layers=9, n_heads=4)
    with _mk(mw, BAND, [2], whole):
        _run(mw, _prefill_mask(SEQ), SEQ)
    cell = {}
    mc = ToyModel(n_layers=9, n_heads=4)
    with _mk(mc, [BAND[0]], [2], cell):
        _run(mc, _prefill_mask(SEQ), SEQ)
    assert whole["n_prefill_edits"] == len(BAND) * cell["n_prefill_edits"], (
        f"a {len(BAND)}-layer band recorded {whole['n_prefill_edits']} and one of its cells "
        f"{cell['n_prefill_edits']}; the ratio is not {len(BAND)}, so DOSE_UNIT/band_width is the "
        f"wrong arithmetic")


def test_one_cell_vs_the_ALL_HEADS_arm_reproduces_S246s_ASYMMETRY():
    """⚠ MY FIRST EXPECTATION HERE WAS WRONG, AND THE TOY CORRECTED IT AGAINST A FACT ALREADY IN THE LOG.

    I asserted the ratio would be n_heads * band_width = 16. Measured: 12 vs 3, i.e. band_width = 4.
    The edits do NOT scale with heads on the all-heads arm, because of the asymmetry S-246 had already
    measured on the real model: "a K-head arm records K x 2016 prefill edits; the ALL-32 arm records
    2016 (NEVER EXPANDS)". `_pre` expands the head axis only when `heads is not None`; with heads=None
    the mask keeps head-dim 1 and the edits are counted once.

    ✅ SO THE TOY INDEPENDENTLY REPRODUCES S-246 -- and that is the useful result, because it is the
    same asymmetry that makes the dose blind between HD_KO and a singleton on the real family."""
    BAND = [3, 4, 5, 6]
    ko = {}
    mk_ = ToyModel(n_layers=9, n_heads=4)
    with _mk(mk_, BAND, None, ko):            # heads=None => ALL heads, the denominator arm's shape
        _run(mk_, _prefill_mask(SEQ), SEQ)
    cell = {}
    mc = ToyModel(n_layers=9, n_heads=4)
    with _mk(mc, [BAND[0]], [2], cell):
        _run(mc, _prefill_mask(SEQ), SEQ)
    assert 0 < cell["n_prefill_edits"] < ko["n_prefill_edits"]
    assert ko["n_prefill_edits"] == len(BAND) * cell["n_prefill_edits"], (
        f"all-heads/whole-band recorded {ko['n_prefill_edits']}, one cell {cell['n_prefill_edits']}; "
        f"expected a factor of band({len(BAND)}) alone, because heads=None NEVER EXPANDS the head axis "
        f"(S-246). If this ever becomes n_heads*band, the all-heads arm started expanding and "
        f"DOSE_UNIT's meaning changed.")
    # And the cell/singleton relationship the 224 prediction actually rests on: same heads, 1/B layers.
    single = {}
    ms = ToyModel(n_layers=9, n_heads=4)
    with _mk(ms, BAND, [2], single):
        _run(ms, _prefill_mask(SEQ), SEQ)
    assert single["n_prefill_edits"] == len(BAND) * cell["n_prefill_edits"], (
        "a 1-head/whole-band arm is not band_width x a 1-head/1-layer arm, so per_cell_dose = "
        "DOSE_UNIT/band_width is the wrong arithmetic")


def test_cell_hooks_do_not_leak_onto_layers_they_were_not_given():
    """A cell arm must edit ONE layer. If the hook registered on the whole module list, the arm would be
    the 9-cell arm wearing the 1-cell arm's name -- and the dose would silently be 9x."""
    m = ToyModel(n_layers=9, n_heads=4)
    h = _mk(m, [4], [2], {})
    assert len(h.layers) == 1, f"hook holds {len(h.layers)} layers, not 1"
    assert h.layers[0] is m.model.layers[4], "the hook attached to the wrong layer object"


def test_the_liveness_tables_are_consistent_across_cell_hooks():
    """N hooks write `liveness_required`/`mode` into one dict with `=`. They must agree, or the last
    constructor silently decides what the arm's liveness contract was."""
    st = {}
    m = ToyModel(n_layers=9, n_heads=4)
    a, b = _mk(m, [4], [2], st), _mk(m, [5], [2], st)
    assert st["mode"] == "target_surface_row_only"
    assert st["liveness_required"] == list(a.stats["liveness_required"]) == list(b.stats["liveness_required"])
    assert st["n_blocked_keys"] == len(set(DEMO))


def test_heads_None_still_means_all_heads_on_a_single_layer():
    """The KO arm on a cell family is head-level; a single-layer hook with heads=None must not crash."""
    st = {}
    m = ToyModel(n_layers=9, n_heads=4)
    with _mk(m, [4], None, st):
        _run(m, _prefill_mask(SEQ), SEQ)
    assert st["n_prefill_edits"] > 0
