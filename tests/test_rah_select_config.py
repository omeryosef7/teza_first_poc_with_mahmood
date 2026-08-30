"""`RAH-PR-009` required the Stage-A selection to be a pure, unit-tested, deterministic function
with a written tie-break, so a reviewer can re-run it over the committed grid and assert equality
with the frozen configuration. These tests pin the rule and prove each tie-break can decide.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "scripts"))
import rah_select_config as sc  # noqa: E402

LLAMA = "meta-llama/Llama-3.1-8B-Instruct"
QWEN = "Qwen/Qwen3-14B"


def _run(model, bank, concept, n_layers, cells):
    """cells: list of (form, R, uplift, ok, n_layers_above_band_passing)."""
    grid = []
    for form, R, up, ok, sup in cells:
        lo = sc.BAND_LO[model]
        per = [{"L": lo + 1 + i, "p_concept_mean": 0.9} for i in range(sup)]
        per += [{"L": lo + 1 + sup + i, "p_concept_mean": 0.01} for i in range(3)]
        grid.append({"form": form, "R": R, "uplift_over_unpatched": up,
                     "positive_control_ok": ok, "pos_ctrl_max": up, "p_codeword_at_best": 0.001,
                     "per_layer": per})
    return {"file": bank, "model": model, "bank": bank, "concept": concept,
            "codeword": "cw", "n_layers": n_layers, "grid": grid}


def test_depth_fraction_collides_across_models():
    """4/32 and 5/40 must land on the same axis or the two models cannot be compared at all."""
    assert sc.depth_fraction(4, 32) == sc.depth_fraction(5, 40) == 0.125


def test_max_min_uplift_wins_not_max_max():
    """The registered rule maximises the MINIMUM. A cell with a huge peak but a weak worst case
    must LOSE to a steadier one -- that is the whole point of the rule."""
    runs = [
        _run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.99, True, 5),
                                      ("id07_raw", 4, 0.80, True, 5)]),
        _run(QWEN, "a", "bomb", 40, [("fc_probe_last", 5, 0.10, True, 5),
                                     ("id07_raw", 5, 0.79, True, 5)]),
    ]
    win, _ = sc.select(runs)
    assert win["form"] == "id07_raw", "max-min must prefer the steadier cell"
    assert win["min_uplift_over_runs"] == pytest.approx(0.79)


def test_a_cell_failing_the_gate_on_ONE_run_is_ineligible():
    runs = [
        _run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.99, True, 5),
                                      ("id07_raw", 4, 0.50, True, 5)]),
        _run(QWEN, "a", "bomb", 40, [("fc_probe_last", 5, 0.99, False, 5),
                                     ("id07_raw", 5, 0.50, True, 5)]),
    ]
    win, _ = sc.select(runs)
    assert win["form"] == "id07_raw", "a cell must pass on EVERY run to be eligible"


def test_tiebreak_1_lower_depth_fraction():
    runs = [_run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.80, True, 5),
                                          ("fc_probe_last", 8, 0.80, True, 5)])]
    win, _ = sc.select(runs)
    assert win["depth_fraction"] == 0.125


def test_tiebreak_2_broader_support_above_the_band():
    runs = [_run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.80, True, 3),
                                          ("id07_raw", 4, 0.80, True, 9)])]
    win, _ = sc.select(runs)
    assert win["form"] == "id07_raw" and win["min_support_above_band"] == 9


def test_support_counts_ONLY_layers_above_the_band():
    """RAH-DR-001 F2: donor layers at or below `lo` are bit-identical between arms, so counting
    them as support would reward a vacuous cell."""
    lo = sc.BAND_LO[LLAMA]
    rec = {"per_layer": [{"L": lo - 1, "p_concept_mean": 0.99},
                         {"L": lo, "p_concept_mean": 0.99},
                         {"L": lo + 1, "p_concept_mean": 0.99},
                         {"L": lo + 2, "p_concept_mean": 0.01}]}
    assert sc.support_above_band(rec, lo) == 1


def test_selection_is_deterministic():
    runs = [_run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.80, True, 5)]),
            _run(QWEN, "a", "bomb", 40, [("fc_probe_last", 5, 0.85, True, 5)])]
    a, _ = sc.select(runs)
    b, _ = sc.select(runs)
    assert a == b


def test_refuses_when_no_cell_passes_everywhere():
    runs = [_run(LLAMA, "a", "bomb", 32, [("fc_probe_last", 4, 0.80, False, 5)])]
    win, table = sc.select(runs)
    assert win is None and table
