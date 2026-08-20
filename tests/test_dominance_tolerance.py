"""The reconstruction guard in dominance.py was loosened for bfloat16 — prove it still discriminates.

CONTEXT. `dominance_at` checks that its value-flow decomposition reproduces the attention module's
actual output, to catch a wrong GQA head map or wrong o_proj slicing. The tolerance was a hardcoded
relative 1e-3, calibrated when every caller loaded float32. Commit bf56ca6b switched
`surgical_knockout` to bfloat16 to fix a Qwen3 OOM, and that constant was not revisited: the module
then accumulates in bfloat16 (eps ~= 3.9e-3) while the decomposition recomputes in float32, so the
two cannot agree to 1e-3. Every prompt of every E6 arm died with `dominance:AssertionError:L8`.

Loosening a guard is only legitimate if the guard still fails the case it exists for. These tests
reproduce the decomposition algebra exactly (dominance.py:161-181) and show that a WRONG head map
produces an error orders of magnitude above even the bfloat16 tolerance.
"""
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "boombness"))

BF16_TOL = 3e-2   # what dominance.py now uses for non-float32 weights
NQ, NKV, HD, T, DM = 8, 2, 4, 11, 32


def _pieces(seed=0):
    g = torch.Generator().manual_seed(seed)
    A = torch.softmax(torch.randn(NQ, T, generator=g), dim=-1)
    v = torch.randn(T, NKV, HD, generator=g)
    Wo = torch.randn(DM, NQ * HD, generator=g) / (NQ * HD) ** 0.5
    return A, v, Wo


def _reconstruct(A, v, Wo, head_map):
    vh = v[:, head_map, :]
    Wo_h = Wo.view(Wo.shape[0], NQ, HD).permute(1, 0, 2)
    Yv = torch.einsum("hdk,thk->htd", Wo_h, vh)
    Y = A.unsqueeze(-1) * Yv
    return Y.sum(dim=(0, 1))


def _rel_err(got, want):
    return float((got - want).norm()) / (float(want.norm()) or 1.0)


def test_correct_head_map_reconstructs_essentially_exactly():
    A, v, Wo = _pieces()
    correct = torch.arange(NQ) // (NQ // NKV)
    truth = _reconstruct(A, v, Wo, correct)
    assert _rel_err(_reconstruct(A, v, Wo, correct), truth) < 1e-6


def test_a_wrong_gqa_head_map_is_still_caught_at_the_bfloat16_tolerance():
    """The failure the guard exists for. It must exceed the LOOSENED tolerance by a wide margin."""
    A, v, Wo = _pieces()
    correct = torch.arange(NQ) // (NQ // NKV)
    truth = _reconstruct(A, v, Wo, correct)
    wrong = correct.flip(0)                      # heads read the wrong kv group
    err = _rel_err(_reconstruct(A, v, Wo, wrong), truth)
    assert err > 10 * BF16_TOL, f"wrong head map only produced rel err {err:.3e}"


def test_bfloat16_rounding_alone_stays_inside_the_tolerance():
    """The case the old 1e-3 constant wrongly rejected: same map, bfloat16 inputs."""
    A, v, Wo = _pieces()
    correct = torch.arange(NQ) // (NQ // NKV)
    truth = _reconstruct(A, v, Wo, correct)
    bf = _reconstruct(A.bfloat16().float(), v.bfloat16().float(), Wo.bfloat16().float(), correct)
    err = _rel_err(bf, truth)
    assert err < BF16_TOL, f"bfloat16 rounding gave {err:.3e}, above tol"
    assert err > 1e-3, (
        f"bfloat16 rounding gave {err:.3e}, which the OLD 1e-3 tolerance would have accepted — "
        "this test would then not demonstrate the reported failure")
