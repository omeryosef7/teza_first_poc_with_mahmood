"""GPU-free test for the D3 scope-matched single-position project-out hook (pair_common).

Asserts the hook:
  * removes the direction's component ONLY at the decision position (last, pos=-1),
    leaving all other positions bit-identical;
  * is a no-op on a KV-cached decode step (seq==1);
  * handles the tuple / bare-tensor output forms of a decoder layer.

Run: python -m pytest doublespeak_causality/tests/test_singleposition_projectout_synthetic.py -q
"""
import os
import sys

import numpy as np
import pytest
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

import pair_common as pc  # noqa: E402


def test_projects_out_only_at_decision_position():
    torch.manual_seed(0)
    d_model, seq = 32, 7
    direction = torch.randn(d_model)
    hook = pc.make_single_position_project_out_hook(direction, alpha=1.0, pos=-1)
    h = torch.randn(1, seq, d_model)
    out = hook(None, None, (h.clone(),))
    hp = out[0]
    u = direction / direction.norm()
    # decision position: projection onto u must be ~0 after the hook
    assert torch.allclose(hp[0, -1, :] @ u, torch.tensor(0.0), atol=1e-5)
    # all other positions unchanged
    assert torch.allclose(hp[0, :-1, :], h[0, :-1, :], atol=1e-6)
    # and the decision position IS changed (component was nonzero before)
    assert not torch.allclose(hp[0, -1, :], h[0, -1, :], atol=1e-4)


def test_noop_on_cached_decode_step():
    direction = torch.randn(16)
    hook = pc.make_single_position_project_out_hook(direction, alpha=1.0, pos=-1)
    h = torch.randn(1, 1, 16)          # seq==1 → cached decode
    out = hook(None, None, (h.clone(),))
    assert torch.allclose(out[0], h, atol=1e-7)


def test_bare_tensor_output_form():
    direction = torch.randn(16)
    hook = pc.make_single_position_project_out_hook(direction, alpha=1.0, pos=-1)
    h = torch.randn(1, 5, 16)
    out = hook(None, None, h.clone())   # bare tensor, not a tuple
    assert torch.is_tensor(out)
    u = direction / direction.norm()
    assert torch.allclose(out[0, -1, :] @ u, torch.tensor(0.0), atol=1e-5)


def test_alpha_scales_removal():
    direction = torch.randn(24)
    h = torch.randn(1, 4, 24)
    u = direction / direction.norm()
    before = float(h[0, -1, :] @ u)
    hook = pc.make_single_position_project_out_hook(direction, alpha=0.5, pos=-1)
    out = hook(None, None, (h.clone(),))
    after = float(out[0][0, -1, :] @ u)
    # alpha=0.5 removes half the projection
    assert after == pytest.approx(0.5 * before, abs=1e-4)
