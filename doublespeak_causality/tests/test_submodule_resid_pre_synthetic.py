"""
GPU-free synthetic tests for SubmodulePatch component="resid_pre" (Phase-3 4-location
coverage). Verifies the forward_pre_hook edits the block INPUT at the intended position,
propagates downstream, is an exact no-op at alpha=0 (add), and that resid_pre@L equals
resid_post@(L-1) numerically. No model, no GPU, deterministic.

Run:  python -m pytest doublespeak_causality/tests/test_submodule_resid_pre_synthetic.py -q
"""
import os
import sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import SubmodulePatch  # noqa: E402


class ToyBlock(nn.Module):
    """Returns (hidden, aux) like a real decoder layer; fixed additive shift so
    downstream layers depend on upstream values."""
    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (x + self.shift, None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=4, hidden=8):
        super().__init__()
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock(i + 1) for i in range(n_layers))

    def forward(self, x):
        aux = None
        for blk in self.model.layers:
            x, aux = blk(x)
        return x


def _base():
    stack = ToyStack(n_layers=4, hidden=8)
    x = torch.zeros(1, 3, 8)  # [batch, seq, hidden]
    return stack, x


def test_resid_pre_replaces_block_input_and_propagates():
    stack, x = _base()
    v = torch.full((8,), 100.0)
    # patch input to layer 2 at position 1
    with SubmodulePatch(stack, 2, "resid_pre", positions=[1], vector=v, mode="replace"):
        out = stack(x)
    # layers 2 and 3 add shift 3 and 4 => +7 on top of the injected 100
    assert torch.allclose(out[0, 1], torch.full((8,), 107.0)), out[0, 1]
    # position 0 untouched by the patch: full stack shifts 1+2+3+4 = 10
    assert torch.allclose(out[0, 0], torch.full((8,), 10.0)), out[0, 0]


def test_resid_pre_alpha_zero_add_is_identity():
    stack, x = _base()
    baseline = stack(x)
    v = torch.randn(8)
    with SubmodulePatch(stack, 2, "resid_pre", positions=[0, 1, 2], vector=v,
                        mode="add", alpha=0.0):
        out = stack(x)
    assert torch.allclose(out, baseline, atol=1e-6)


def test_resid_pre_at_L_equals_resid_post_at_L_minus_1():
    """resid_pre@L and resid_post@(L-1) are the same tensor point -> identical result."""
    stack, x = _base()
    v = torch.full((8,), 42.0)
    with SubmodulePatch(stack, 2, "resid_pre", positions=[1], vector=v, mode="replace"):
        pre = stack(x)
    with SubmodulePatch(stack, 1, "resid_post", positions=[1], vector=v, mode="replace"):
        post = stack(x)
    assert torch.allclose(pre, post), (pre[0, 1], post[0, 1])


def test_resid_pre_hook_removed_after_context():
    stack, x = _base()
    baseline = stack(x)
    with SubmodulePatch(stack, 0, "resid_pre", positions=[0], vector=torch.full((8,), 5.0),
                        mode="replace"):
        pass
    after = stack(x)
    assert torch.allclose(after, baseline, atol=1e-6)
