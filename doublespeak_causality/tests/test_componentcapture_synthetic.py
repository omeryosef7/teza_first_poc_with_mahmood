"""
GPU-free synthetic tests for pair_common.ComponentCapture (plan §P0 / §0.9 — untested hook
primitives). No model, no GPU, deterministic; the toy block mimics the HF decoder-layer
interface (called with hidden_states positionally, returning a tuple, with `self_attn`
returning a tuple and `mlp` a plain tensor).

Asserts:
  (a) all four components {resid_pre, attn_out, mlp_out, resid_post} are captured with the
      right VALUES at the requested positions, per layer (closed-form toy arithmetic);
  (b) stacked() returns [n_layers, n_positions, hidden] float32 CPU, in `positions` order,
      and honours a component SUBSET;
  (c) validation: unknown component -> ValueError; a layer that never ran -> RuntimeError
      from stacked(); handles removed on __exit__;
  (d) DECODE-SHAPED INPUT (documents the known behaviour): with seq==1, any requested
      position outside [0, seq) makes _grab raise IndexError — ComponentCapture is
      PREFILL-ONLY and fails LOUDLY on a KV-cached decode step (unlike SubmodulePatch /
      DemoStateSwap, which silently skip out-of-range positions). Position 0 alone still
      works, so the failure is specific to out-of-range indices, not to seq==1 per se.

Run:  python -m pytest doublespeak_causality/tests/test_componentcapture_synthetic.py -q
"""
import os
import sys

import pytest
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import COMPONENTS, ComponentCapture  # noqa: E402


# --------------------------------------------------------------------------- #
# Toy model
# --------------------------------------------------------------------------- #
class ToyAttn(nn.Module):
    """attn_out = x + a_shift; returns a TUPLE like a real HF self_attn."""

    def __init__(self, a_shift: float):
        super().__init__()
        self.a_shift = a_shift

    def forward(self, x):
        return (x + self.a_shift, None)


class ToyMLP(nn.Module):
    """mlp_out = m_scale * x; returns a plain tensor like a real HF mlp."""

    def __init__(self, m_scale: float):
        super().__init__()
        self.m_scale = m_scale

    def forward(self, x):
        return x * self.m_scale


class ToyBlock(nn.Module):
    """resid_pre = x
       attn_out  = self_attn(x)[0]      = x + a
       mid       = x + attn_out
       mlp_out   = mlp(mid)             = m * mid
       resid_post= mid + mlp_out
    """

    def __init__(self, a_shift, m_scale):
        super().__init__()
        self.self_attn = ToyAttn(a_shift)
        self.mlp = ToyMLP(m_scale)

    def forward(self, x):
        a = self.self_attn(x)[0]
        mid = x + a
        m = self.mlp(mid)
        return (mid + m, None)


class ToyStack(nn.Module):
    def __init__(self, n_layers=3, a_shifts=None, m_scales=None):
        super().__init__()
        a_shifts = a_shifts or [i + 1.0 for i in range(n_layers)]
        m_scales = m_scales or [0.5 * (i + 1) for i in range(n_layers)]
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(
            ToyBlock(a, m) for a, m in zip(a_shifts, m_scales))

    def forward(self, x):
        for blk in self.model.layers:
            x, _ = blk(x)
        return x


class ToyLM:
    """ComponentCapture only touches lm.model (via ds_common._get_layers)."""

    def __init__(self, model):
        self.model = model


def _reference(stack, x):
    """Recompute every component per layer, independently of the hooks."""
    ref = {c: [] for c in COMPONENTS}
    h = x
    for blk in stack.model.layers:
        a = h + blk.self_attn.a_shift
        mid = h + a
        m = mid * blk.mlp.m_scale
        ref["resid_pre"].append(h.clone())
        ref["attn_out"].append(a.clone())
        ref["mlp_out"].append(m.clone())
        ref["resid_post"].append((mid + m).clone())
        h = mid + m
    return ref


# --------------------------------------------------------------------------- #
# (a) values
# --------------------------------------------------------------------------- #
def test_captures_all_four_components_with_correct_values():
    torch.manual_seed(0)
    stack = ToyStack(n_layers=3)
    lm = ToyLM(stack)
    x = torch.randn(1, 6, 8)
    positions = [1, 4]
    ref = _reference(stack, x)
    with ComponentCapture(lm, COMPONENTS, positions) as cap:
        stack(x)
    got = cap.stacked()
    for comp in COMPONENTS:
        assert got[comp].shape == (3, len(positions), 8), (comp, got[comp].shape)
        for li in range(3):
            want = ref[comp][li][0, positions, :]
            assert torch.allclose(got[comp][li], want, atol=1e-6), (comp, li)


def test_positions_are_returned_in_request_order_not_sorted():
    stack = ToyStack(n_layers=1, a_shifts=[0.0], m_scales=[0.0])
    lm = ToyLM(stack)
    x = torch.arange(4 * 3, dtype=torch.float32).reshape(1, 4, 3)
    with ComponentCapture(lm, ["resid_pre"], [3, 0]) as cap:
        stack(x)
    got = cap.stacked()["resid_pre"]
    assert torch.allclose(got[0, 0], x[0, 3]), "row 0 must be position 3 (request order)"
    assert torch.allclose(got[0, 1], x[0, 0]), "row 1 must be position 0"


def test_dtype_and_device_are_float32_cpu():
    stack = ToyStack(n_layers=2)
    lm = ToyLM(stack)
    x = torch.randn(1, 3, 8).to(torch.float64)
    with ComponentCapture(lm, ["resid_post"], [0]) as cap:
        stack(x)
    t = cap.stacked()["resid_post"]
    assert t.dtype == torch.float32 and t.device.type == "cpu", (t.dtype, t.device)


def test_component_subset_only_captures_requested():
    stack = ToyStack(n_layers=2)
    lm = ToyLM(stack)
    x = torch.randn(1, 3, 8)
    with ComponentCapture(lm, ["attn_out", "mlp_out"], [2]) as cap:
        stack(x)
    got = cap.stacked()
    assert set(got) == {"attn_out", "mlp_out"}


def test_batch_dim_is_dropped_row_zero_only():
    """_grab takes hidden[0] on a 3-D tensor: capture is batch-row 0 by construction."""
    stack = ToyStack(n_layers=1, a_shifts=[0.0], m_scales=[0.0])
    lm = ToyLM(stack)
    x = torch.stack([torch.zeros(3, 4), torch.full((3, 4), 9.0)]).unsqueeze(0).squeeze(0)
    assert x.shape == (2, 3, 4)
    with ComponentCapture(lm, ["resid_pre"], [0]) as cap:
        stack(x)
    assert torch.allclose(cap.stacked()["resid_pre"][0, 0], torch.zeros(4)), "row 0 only"


# --------------------------------------------------------------------------- #
# (c) validation / hygiene
# --------------------------------------------------------------------------- #
def test_unknown_component_raises():
    lm = ToyLM(ToyStack(n_layers=1))
    with pytest.raises(ValueError):
        ComponentCapture(lm, ["resid_pre", "bogus"], [0])


def test_stacked_raises_when_a_layer_never_ran():
    stack = ToyStack(n_layers=3)
    lm = ToyLM(stack)
    x = torch.randn(1, 3, 8)
    with ComponentCapture(lm, ["resid_post"], [0]) as cap:
        stack.model.layers[0](x)          # only layer 0 forwards
    with pytest.raises(RuntimeError) as e:
        cap.stacked()
    assert "no capture for layers" in str(e.value)


def test_handles_removed_on_exit():
    stack = ToyStack(n_layers=2)
    lm = ToyLM(stack)
    x = torch.randn(1, 3, 8)
    with ComponentCapture(lm, COMPONENTS, [0]) as cap:
        stack(x)
    assert cap._handles == [], "handles must be emptied on __exit__"
    cap._buf = {c: {} for c in cap.components}
    stack(x)                               # would refill the buffers if hooks lingered
    assert all(cap._buf[c] == {} for c in cap.components), "hooks must be gone"


# REGRESSION GUARD (defect found by this test, fixed 2026-08-05).
# ComponentCapture._grab built its index with torch.tensor([...]) and no dtype; for an
# empty position list that yields float32 and index_select() raises "Expected dtype int32
# or int64 for index". Reachable from capture_components() whenever every requested
# position resolves to None. Fix: dtype=torch.long (pair_common.py).
# This test was xfail(strict=True) until the fix landed.
def test_empty_positions_yields_zero_rows():
    stack = ToyStack(n_layers=2)
    lm = ToyLM(stack)
    with ComponentCapture(lm, ["resid_post"], []) as cap:
        stack(torch.randn(1, 3, 8))
    assert cap.stacked()["resid_post"].shape == (2, 0, 8)


# --------------------------------------------------------------------------- #
# (d) decode-shaped input — documents the PREFILL-ONLY behaviour
# --------------------------------------------------------------------------- #
def test_decode_step_out_of_range_position_raises_indexerror():
    """DOCUMENTED BEHAVIOUR: on a KV-cached decode step (seq==1) a prompt position is out
    of range and ComponentCapture raises IndexError rather than silently capturing fewer
    rows. Loud failure is the safe behaviour, but it means ComponentCapture CANNOT be used
    inside generate() with prompt positions — it is prefill-only."""
    stack = ToyStack(n_layers=1)
    lm = ToyLM(stack)
    x_decode = torch.randn(1, 1, 8)        # seq == 1
    with pytest.raises(IndexError) as e:
        with ComponentCapture(lm, ["resid_pre"], [5]) as cap:
            stack(x_decode)
    assert "position out of range" in str(e.value)
    assert "seq_len=1" in str(e.value), str(e.value)


def test_decode_step_position_zero_still_works():
    """The failure above is about OUT-OF-RANGE indices, not about seq==1 itself."""
    stack = ToyStack(n_layers=1, a_shifts=[0.0], m_scales=[0.0])
    lm = ToyLM(stack)
    x_decode = torch.full((1, 1, 4), 3.0)
    with ComponentCapture(lm, ["resid_pre"], [0]) as cap:
        stack(x_decode)
    assert torch.allclose(cap.stacked()["resid_pre"][0, 0], torch.full((4,), 3.0))


def test_partial_out_of_range_is_all_or_nothing():
    """A mix of valid and invalid positions raises too (no partial capture)."""
    stack = ToyStack(n_layers=1)
    lm = ToyLM(stack)
    with pytest.raises(IndexError):
        with ComponentCapture(lm, ["resid_pre"], [0, 9]) as cap:
            stack(torch.randn(1, 3, 8))


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
