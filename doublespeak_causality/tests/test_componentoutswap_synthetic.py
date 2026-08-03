"""
GPU-free synthetic tests for pair_common.ComponentOutSwap (Phase 6 causal MLP write).
No model, no GPU, deterministic. The mlp/attn-OUTPUT analogue of DemoStateSwap; mirrors
tests/test_demostateswap_synthetic.py.

Asserts:
  (a) SELF-SWAP (source == receiver's own captured mlp output) == baseline EXACTLY;
  (b) swapping target positions changes ONLY those positions (and downstream), never earlier;
  (c) per-position rows are written distinctly (not one shared vector, unlike SubmodulePatch);
  (d) handles removed after __exit__.

Run:  python doublespeak_causality/tests/test_componentoutswap_synthetic.py
"""
import os
import sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import ComponentOutSwap  # noqa: E402


class ToyMLP(nn.Module):
    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return x + self.shift          # plain tensor output, like a real MLP


class ToyBlock(nn.Module):
    """resid_post = resid_pre + mlp(resid_pre); mlp is a hookable submodule."""
    def __init__(self, shift: float):
        super().__init__()
        self.mlp = ToyMLP(shift)

    def forward(self, x):
        return (x + self.mlp(x), None)


class ToyAttn(nn.Module):
    """Returns a TUPLE (attn_out, weights) like a real HF self_attn — exercises the
    tuple-output branch of ComponentOutSwap that mlp (plain tensor) does not."""
    def __init__(self, shift: float):
        super().__init__()
        self.shift = shift

    def forward(self, x):
        return (x + self.shift, None)


class ToyAttnBlock(nn.Module):
    """resid_post = resid_pre + self_attn(resid_pre)[0]; self_attn returns a TUPLE."""
    def __init__(self, shift: float):
        super().__init__()
        self.self_attn = ToyAttn(shift)

    def forward(self, x):
        return (x + self.self_attn(x)[0], None)


class ToyAttnStack(nn.Module):
    def __init__(self, n_layers=3, shifts=None):
        super().__init__()
        shifts = shifts or [i + 1 for i in range(n_layers)]
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyAttnBlock(s) for s in shifts)

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


class ToyStack(nn.Module):
    def __init__(self, n_layers=4, shifts=None):
        super().__init__()
        shifts = shifts or [i + 1 for i in range(n_layers)]
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock(s) for s in shifts)

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


def _capture_mlp_out(stack, x, positions, layers):
    store, handles = {}, []
    for li in layers:
        def mk(li):
            def f(mod, inp, out):
                h = out[0] if isinstance(out, tuple) else out
                store[li] = h[0, positions, :].clone()
            return f
        handles.append(stack.model.layers[li].mlp.register_forward_hook(mk(li)))
    stack(x)
    for h in handles:
        h.remove()
    return store


def test_self_swap_equals_baseline_exactly():
    torch.manual_seed(0)
    stack = ToyStack(n_layers=4)
    x = torch.randn(1, 5, 8)
    positions, layers = [1, 3], [0, 1, 2, 3]
    base = stack(x).clone()
    src = _capture_mlp_out(stack, x, positions, layers)
    with ComponentOutSwap(stack, positions, src, component="mlp_out"):
        out = stack(x)
    assert torch.equal(out, base), "self-swap must reproduce the baseline EXACTLY"


def test_swap_changes_only_target_positions():
    stack = ToyStack(n_layers=4)
    x = torch.zeros(1, 6, 8)
    positions, layers = [2], [1]
    base = stack(x).clone()
    src = {1: torch.full((1, 8), 100.0)}
    with ComponentOutSwap(stack, positions, src, component="mlp_out"):
        out = stack(x)
    assert (out - base).abs().sum(-1)[0][2] > 0, "target position 2 must change"
    for p in (0, 1, 3, 4, 5):
        assert torch.allclose(out[0, p], base[0, p]), f"pos {p} must be unchanged"
    assert out.shape == base.shape


def test_per_position_rows_written_distinctly():
    stack = ToyStack(n_layers=1, shifts=[0.0])   # resid_post = x + mlp_out, mlp shift 0
    x = torch.zeros(1, 3, 4)
    # distinct rows per position: pos0 -> 10, pos2 -> 20
    src = {0: torch.stack([torch.full((4,), 10.0), torch.full((4,), 20.0)])}
    with ComponentOutSwap(stack, [0, 2], src, component="mlp_out"):
        out = stack(x)
    assert torch.allclose(out[0, 0], torch.full((4,), 10.0)), out[0, 0]
    assert torch.allclose(out[0, 2], torch.full((4,), 20.0)), out[0, 2]
    assert torch.allclose(out[0, 1], torch.zeros(4)), "untouched pos1"


def test_hook_removed_after_context():
    stack = ToyStack(n_layers=2)
    x = torch.zeros(1, 2, 8)
    with ComponentOutSwap(stack, [0], {0: torch.full((1, 8), 99.0)}, component="mlp_out") as s:
        pass
    assert s._handles == [], "handles must be emptied on __exit__"
    assert torch.allclose(stack(x), stack(x)), "hook must be removed"


def _capture_attn_out(stack, x, positions, layers):
    store, handles = {}, []
    for li in layers:
        def mk(li):
            def f(mod, inp, out):
                h = out[0] if isinstance(out, tuple) else out
                store[li] = h[0, positions, :].clone()
            return f
        handles.append(stack.model.layers[li].self_attn.register_forward_hook(mk(li)))
    stack(x)
    for h in handles:
        h.remove()
    return store


def test_attn_out_tuple_self_swap_exact():
    """component='attn_out' hooks a TUPLE-returning submodule; self-swap must still be exact."""
    torch.manual_seed(1)
    stack = ToyAttnStack(n_layers=3)
    x = torch.randn(1, 5, 8)
    positions, layers = [1, 4], [0, 1, 2]
    base = stack(x).clone()
    src = _capture_attn_out(stack, x, positions, layers)
    with ComponentOutSwap(stack, positions, src, component="attn_out"):
        out = stack(x)
    assert torch.equal(out, base), "attn_out (tuple) self-swap must reproduce baseline EXACTLY"


def test_attn_out_tuple_per_position_and_locality():
    stack = ToyAttnStack(n_layers=1, shifts=[0.0])
    x = torch.zeros(1, 3, 4)
    src = {0: torch.stack([torch.full((4,), 7.0), torch.full((4,), 9.0)])}
    with ComponentOutSwap(stack, [0, 2], src, component="attn_out"):
        out = stack(x)
    assert torch.allclose(out[0, 0], torch.full((4,), 7.0)), out[0, 0]
    assert torch.allclose(out[0, 2], torch.full((4,), 9.0)), out[0, 2]
    assert torch.allclose(out[0, 1], torch.zeros(4)), "untouched pos1"


TESTS = [test_self_swap_equals_baseline_exactly,
         test_swap_changes_only_target_positions,
         test_per_position_rows_written_distinctly,
         test_hook_removed_after_context,
         test_attn_out_tuple_self_swap_exact,
         test_attn_out_tuple_per_position_and_locality]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
