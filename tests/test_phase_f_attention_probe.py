"""Torch-free unit tests for scripts/phase_f_attention_probe.py (Phase-F1.3 core).

All fixtures are HAND-BUILT synthetic numpy attention arrays + integer token
ranges — no text, no model, no torch. Every expected value is hand-computed in
the test so the numeric core is pinned exactly.
"""

import importlib.util
import os
import sys

import numpy as np
import pytest

SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts",
    "phase_f_attention_probe.py",
)
_spec = importlib.util.spec_from_file_location("pfap", SCRIPT)
pfap = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pfap)


def _tiny_attn():
    """attn shape [1, 1, 4, 6] with KNOWN rows.

    row3 (the chosen query row) = [0.0, 0.0, 0.4, 0.2, 0.2, 0.0], sum = 0.8.
    """
    attn = np.zeros((1, 1, 4, 6), dtype=np.float64)
    attn[0, 0, 0] = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    attn[0, 0, 1] = [0.0, 1.0, 0.0, 0.0, 0.0, 0.0]
    attn[0, 0, 2] = [0.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    attn[0, 0, 3] = [0.0, 0.0, 0.4, 0.2, 0.2, 0.0]
    return attn


def test_single_span_normalized_and_unnormalized():
    attn = _tiny_attn()
    # span covers k in [2, 4) -> indices 2,3 -> 0.4 + 0.2 = 0.6 from row 3.
    ranges = {"comp": [(2, 4)]}

    raw = pfap.attention_mass_to_spans(attn, [3], ranges, normalize=False)
    assert raw[(0, 0)]["comp"] == pytest.approx(0.6)

    norm = pfap.attention_mass_to_spans(attn, [3], ranges, normalize=True)
    # normalized by row-3 total attention = 0.8 -> 0.6 / 0.8 = 0.75.
    assert norm[(0, 0)]["comp"] == pytest.approx(0.75)


def test_mean_over_multiple_query_rows():
    attn = _tiny_attn()
    ranges = {"comp": [(2, 4)]}
    # mean of row2 [0,0,1,0,0,0] and row3 [0,0,0.4,0.2,0.2,0]
    #   = [0,0,0.7,0.1,0.1,0], total = 0.9, span[2,4) = 0.7 + 0.1 = 0.8.
    out = pfap.attention_mass_to_spans(attn, [2, 3], ranges, normalize=True)
    assert out[(0, 0)]["comp"] == pytest.approx(0.8 / 0.9)
    raw = pfap.attention_mass_to_spans(attn, [2, 3], ranges, normalize=False)
    assert raw[(0, 0)]["comp"] == pytest.approx(0.8)


def test_multi_instance_span_union():
    attn = _tiny_attn()
    # two disjoint ranges -> union indices 0 and 4 -> 0.0 + 0.2 = 0.2 from row 3.
    ranges = {"comp": [(0, 1), (4, 5)]}
    raw = pfap.attention_mass_to_spans(attn, [3], ranges, normalize=False)
    assert raw[(0, 0)]["comp"] == pytest.approx(0.2)


def test_overlapping_ranges_not_double_counted():
    attn = _tiny_attn()
    # overlapping ranges union indices 2,3,4 (index 3 counted once):
    #   0.4 + 0.2 + 0.2 = 0.8 from row 3.
    ranges = {"comp": [(2, 4), (3, 5)]}
    raw = pfap.attention_mass_to_spans(attn, [3], ranges, normalize=False)
    assert raw[(0, 0)]["comp"] == pytest.approx(0.8)


def test_empty_query_positions_returns_zero():
    attn = _tiny_attn()
    ranges = {"comp": [(2, 4)]}
    out = pfap.attention_mass_to_spans(attn, [], ranges, normalize=True)
    assert out[(0, 0)]["comp"] == 0.0
    # out-of-range query indices are ignored -> also zero.
    out2 = pfap.attention_mass_to_spans(attn, [99], ranges, normalize=True)
    assert out2[(0, 0)]["comp"] == 0.0


def test_out_of_range_span_returns_zero_no_crash():
    attn = _tiny_attn()
    ranges = {"comp": [(10, 12)]}  # entirely outside [0, 6)
    out = pfap.attention_mass_to_spans(attn, [3], ranges, normalize=False)
    assert out[(0, 0)]["comp"] == 0.0
    # a range straddling the boundary is clipped to [0, n_k).
    ranges2 = {"comp": [(4, 100)]}  # -> indices 4,5 -> 0.2 + 0.0 = 0.2
    out2 = pfap.attention_mass_to_spans(attn, [3], ranges2, normalize=False)
    assert out2[(0, 0)]["comp"] == pytest.approx(0.2)


def _contrast_records():
    return [
        {"is_success": True,
         "masses": {(0, 0): {"A": 0.8, "B": 0.1}, (0, 1): {"A": 0.2, "B": 0.5}}},
        {"is_success": True,
         "masses": {(0, 0): {"A": 0.6, "B": 0.3}, (0, 1): {"A": 0.4, "B": 0.5}}},
        {"is_success": False,
         "masses": {(0, 0): {"A": 0.2, "B": 0.4}, (0, 1): {"A": 0.3, "B": 0.1}}},
        {"is_success": False,
         "masses": {(0, 0): {"A": 0.4, "B": 0.2}, (0, 1): {"A": 0.5, "B": 0.3}}},
    ]


def test_success_failure_contrast_values():
    contrast = pfap.success_failure_contrast(_contrast_records())

    a00 = contrast[(0, 0)]["A"]
    assert a00["succ_mean"] == pytest.approx(0.7)   # mean(0.8, 0.6)
    assert a00["fail_mean"] == pytest.approx(0.3)   # mean(0.2, 0.4)
    assert a00["delta"] == pytest.approx(0.4)
    assert a00["n_succ"] == 2 and a00["n_fail"] == 2

    a01 = contrast[(0, 1)]["A"]
    assert a01["succ_mean"] == pytest.approx(0.3)   # mean(0.2, 0.4)
    assert a01["fail_mean"] == pytest.approx(0.4)   # mean(0.3, 0.5)
    assert a01["delta"] == pytest.approx(-0.1)

    b01 = contrast[(0, 1)]["B"]
    assert b01["succ_mean"] == pytest.approx(0.5)
    assert b01["fail_mean"] == pytest.approx(0.2)
    assert b01["delta"] == pytest.approx(0.3)


def test_contrast_missing_outcome_defaults_zero():
    # A (layer, head) seen only in a success record -> fail_mean 0.0, n_fail 0.
    records = [
        {"is_success": True, "masses": {(5, 5): {"A": 0.9}}},
        {"is_success": False, "masses": {(0, 0): {"A": 0.1}}},
    ]
    contrast = pfap.success_failure_contrast(records)
    s = contrast[(5, 5)]["A"]
    assert s["succ_mean"] == pytest.approx(0.9)
    assert s["fail_mean"] == 0.0
    assert s["n_succ"] == 1 and s["n_fail"] == 0
    assert s["delta"] == pytest.approx(0.9)


def test_top_k_heads_by_abs_delta():
    contrast = pfap.success_failure_contrast(_contrast_records())
    # A: |delta| (0,0)=0.4 > (0,1)=0.1  ->  top-1 = (0,0).
    assert pfap.top_k_heads_by_abs_delta(contrast, "A", 1) == [(0, 0)]
    assert pfap.top_k_heads_by_abs_delta(contrast, "A", 2) == [(0, 0), (0, 1)]
    # B: (0,1) delta=+0.3, (0,0) delta=-0.1  ->  top-1 = (0,1).
    assert pfap.top_k_heads_by_abs_delta(contrast, "B", 1) == [(0, 1)]
    # k <= 0 -> empty; k beyond available -> all.
    assert pfap.top_k_heads_by_abs_delta(contrast, "A", 0) == []
    assert len(pfap.top_k_heads_by_abs_delta(contrast, "A", 99)) == 2
    # unknown component -> empty.
    assert pfap.top_k_heads_by_abs_delta(contrast, "ZZZ", 3) == []


def test_module_import_is_torch_free():
    import scripts.phase_f_attention_probe  # noqa: F401
    assert "torch" not in sys.modules
