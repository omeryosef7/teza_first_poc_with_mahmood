"""
GPU-free synthetic tests for LayerPatch (plan §23: "a synthetic test demonstrating
that replacing an activation actually changes the downstream tensor at the intended
layer and nowhere else"). No model, no GPU, fully deterministic.

Run:  python -m pytest doublespeak_causality/tests/test_layerpatch_synthetic.py -q
"""
import os
import sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ds_common import LayerPatch  # noqa: E402


class ToyBlock(nn.Module):
    """A block that returns a tuple (hidden, aux) like a real decoder layer,
    applying a fixed additive shift so downstream layers depend on upstream."""
    def __init__(self, hidden: int, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (x + self.shift, None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=4, hidden=8):
        super().__init__()
        # LayerPatch discovers layers via model.model.layers
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock(hidden, i + 1) for i in range(n_layers))

    def forward(self, x):
        aux = None
        for blk in self.model.layers:
            x, aux = blk(x)
        return x


def _run(stack, x):
    return stack(x)


def test_replace_only_changes_target_position_and_downstream():
    torch.manual_seed(0)
    stack = ToyStack(n_layers=4, hidden=8)
    x = torch.zeros(1, 5, 8)  # [batch, seq, hidden]

    base = _run(stack, x).clone()

    vec = torch.full((8,), 100.0)
    with LayerPatch(stack, layer_idx=1, positions=[2], vector=vec, mode="replace"):
        patched = _run(stack, x)

    # Position 2 must differ; all other positions identical (locality in seq).
    diff = (patched - base).abs().sum(dim=-1)[0]  # [seq]
    assert diff[2] > 0, "target position 2 should change"
    for p in (0, 1, 3, 4):
        assert torch.allclose(patched[0, p], base[0, p]), f"pos {p} must be unchanged"


def test_replace_value_propagates_with_downstream_shifts():
    stack = ToyStack(n_layers=4, hidden=8)  # shifts 1,2,3,4
    x = torch.zeros(1, 3, 8)
    vec = torch.full((8,), 100.0)
    # Patch AFTER layer_idx=1 (which added shift 1 then 2 => running 3 at its output).
    # Remaining layers add 3 and 4 => +7. So patched pos = 100 + 7 = 107.
    with LayerPatch(stack, layer_idx=1, positions=[0], vector=vec, mode="replace"):
        out = _run(stack, x)
    assert torch.allclose(out[0, 0], torch.full((8,), 107.0)), out[0, 0][:3]


def test_add_mode_scales_by_alpha():
    stack = ToyStack(n_layers=2, hidden=4)  # shifts 1,2
    x = torch.zeros(1, 2, 4)
    base = _run(stack, x).clone()   # every entry = 3
    vec = torch.ones(4)
    with LayerPatch(stack, layer_idx=0, positions=[1], vector=vec, mode="add", alpha=5.0):
        out = _run(stack, x)
    # layer0 output +5 at pos1, then layer1 adds 2 => base(3)+5 = 8 at pos1.
    assert torch.allclose(out[0, 1], torch.full((4,), 8.0))
    assert torch.allclose(out[0, 0], base[0, 0])  # pos0 untouched


def test_alpha_zero_add_is_identity():
    stack = ToyStack(n_layers=3, hidden=6)
    x = torch.randn(1, 4, 6)
    base = _run(stack, x).clone()
    vec = torch.randn(6)
    with LayerPatch(stack, layer_idx=1, positions=[0, 2], vector=vec, mode="add", alpha=0.0):
        out = _run(stack, x)
    assert torch.allclose(out, base, atol=1e-6), "alpha=0 add must reproduce baseline"


def test_project_out_removes_component():
    stack = ToyStack(n_layers=1, hidden=4)  # single layer, shift 1 => output all ones
    x = torch.zeros(1, 1, 4)
    d = torch.tensor([1.0, 0.0, 0.0, 0.0])
    with LayerPatch(stack, layer_idx=0, positions=[0], vector=d, mode="project_out", alpha=1.0):
        out = _run(stack, x)
    # output was [1,1,1,1]; remove full component along e0 => [0,1,1,1].
    assert torch.allclose(out[0, 0], torch.tensor([0.0, 1.0, 1.0, 1.0]))


def test_hook_removed_after_context():
    stack = ToyStack(n_layers=2, hidden=4)
    x = torch.zeros(1, 2, 4)
    vec = torch.full((4,), 50.0)
    with LayerPatch(stack, layer_idx=0, positions=[0], vector=vec, mode="replace"):
        pass
    after = _run(stack, x)
    base = _run(stack, x)
    assert torch.allclose(after, base), "hook must be removed on __exit__"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("ALL SYNTHETIC LAYERPATCH TESTS PASSED")
