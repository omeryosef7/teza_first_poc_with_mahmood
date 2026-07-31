"""
GPU-free synthetic tests for pair_common.ZHeadPatch / ZHeadCapture (NEXT5 W4 tier-B). No model,
no harmful text. A toy stack whose self_attn.o_proj is an nn.Linear over [n_heads*head_dim]:

  (1) ZHeadPatch overwrites ONLY the target head's z at the target positions (other heads and
      positions untouched), and the o_proj output reflects the change,
  (2) self-patch (corrupt == clean z) == baseline exactly (locality),
  (3) ZHeadPatch is decode-step safe: a seq==1 forward with an out-of-range position is a no-op,
  (4) ZHeadCapture captures z with grad, and a per-head AtP estimate g_z.(z_corrupt - z_clean)
      EXACTLY equals a true z-patch delta on the LINEAR o_proj (the gate's correctness contract),
  (5) hooks removed on __exit__; bad head raises.

Run:  python doublespeak_causality/tests/test_zhead_synthetic.py
      pytest doublespeak_causality/tests/test_zhead_synthetic.py -q
"""
import os
import sys

import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import pair_common as pc              # noqa: E402


class ToyAttn(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.o_proj = nn.Linear(hidden, hidden, bias=False)


class ToyBlock(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.self_attn = ToyAttn(hidden)


class ToyCfg:
    def __init__(self, n_heads, hidden):
        self.num_attention_heads = n_heads
        self.hidden_size = hidden


class ToyModel(nn.Module):
    """model.model.layers[li].self_attn.o_proj — matches ds_common._get_layers + _attn_head_dims."""
    def __init__(self, n_layers=2, n_heads=4, head_dim=3):
        super().__init__()
        hidden = n_heads * head_dim
        self.config = ToyCfg(n_heads, hidden)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock(hidden) for _ in range(n_layers))

    def apply_o_proj(self, li, z):                 # z: [b, seq, hidden]
        return self.model.layers[li].self_attn.o_proj(z)


def test_patch_only_target_head_and_positions():
    torch.manual_seed(0)
    m = ToyModel(n_heads=4, head_dim=3)            # hidden 12
    z = torch.randn(1, 5, 12)
    corrupt = torch.tensor([9.0, 9.0, 9.0])        # head_dim 3
    with pc.ZHeadPatch(m, 0, head=2, positions=[1, 3], corrupt_vec=corrupt):
        out = m.apply_o_proj(0, z)
    # reconstruct what the patched z should be
    zr = z.view(1, 5, 4, 3).clone()
    zr[0, 1, 2, :] = corrupt
    zr[0, 3, 2, :] = corrupt
    expected = m.model.layers[0].self_attn.o_proj(zr.view(1, 5, 12))
    assert torch.allclose(out, expected, atol=1e-6)


def test_self_patch_equals_baseline():
    torch.manual_seed(1)
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 4, 12)
    base = m.apply_o_proj(0, z)
    zr = z.view(1, 4, 4, 3)
    same = zr[0, 2, 1, :].clone()                  # corrupt == clean at that head/pos
    with pc.ZHeadPatch(m, 0, head=1, positions=[2], corrupt_vec=same):
        out = m.apply_o_proj(0, z)
    assert torch.allclose(out, base, atol=1e-6), "self-patch must equal baseline (locality)"


def test_decode_step_out_of_range_is_noop():
    m = ToyModel(n_heads=4, head_dim=3)
    z = torch.randn(1, 1, 12)                       # seq==1 decode step
    base = m.apply_o_proj(0, z)
    with pc.ZHeadPatch(m, 0, head=0, positions=[7], corrupt_vec=torch.zeros(3)):
        out = m.apply_o_proj(0, z)
    assert torch.allclose(out, base, atol=1e-6), "out-of-range decode position must be a no-op"


def test_atp_equals_true_patch_linear():
    """On a LINEAR o_proj, first-order AtP is exact: g_z.(z_corrupt - z_clean) == true delta."""
    torch.manual_seed(2)
    m = ToyModel(n_layers=1, n_heads=4, head_dim=3)
    hidden = 12
    z_clean = torch.randn(1, 4, hidden)
    qpos, head = 3, 2
    corrupt_head = torch.tensor([2.0, -1.0, 0.5])

    def metric_from_out(out):
        return out[0, qpos, :].sum()               # linear readout

    # --- AtP: capture z, backward the metric, dot grad with delta on the head slice ---
    cap = pc.ZHeadCapture(m, [0])
    with torch.enable_grad():
        zc = z_clean.clone().requires_grad_(True)
        with cap:
            out = m.apply_o_proj(0, zc)
            M = metric_from_out(out)
        M.backward()
    # grad[0]: [seq, hidden] -> [seq, n_heads, head_dim]; take (qpos, head) slice
    g_z = cap.acts[0].grad[0].view(4, 4, 3)[qpos, head]     # [head_dim]
    z_clean_h = z_clean.view(1, 4, 4, 3)[0, qpos, head, :]
    delta = corrupt_head - z_clean_h
    atp = float(g_z.dot(delta))

    # --- true patch: replace head z at qpos, measure the metric delta ---
    with torch.no_grad():
        m_clean = float(metric_from_out(m.apply_o_proj(0, z_clean)))
        with pc.ZHeadPatch(m, 0, head=head, positions=[qpos], corrupt_vec=corrupt_head):
            m_patched = float(metric_from_out(m.apply_o_proj(0, z_clean)))
    true_delta = m_patched - m_clean
    assert abs(atp - true_delta) < 1e-4, f"AtP {atp} != true {true_delta} (must be exact for linear)"


def test_bad_head_raises():
    m = ToyModel(n_heads=4, head_dim=3)
    try:
        pc.ZHeadPatch(m, 0, head=9, positions=[0], corrupt_vec=torch.zeros(3))
    except IndexError:
        return
    raise AssertionError("out-of-range head must raise IndexError")


def test_capture_hooks_removed():
    m = ToyModel(n_layers=2, n_heads=4, head_dim=3)
    z = torch.randn(1, 3, 12)
    cap = pc.ZHeadCapture(m, [0, 1])
    with cap:
        m.apply_o_proj(0, z)
    # after exit, a fresh forward should not repopulate acts
    cap.acts.clear()
    m.apply_o_proj(0, z)
    assert cap.acts == {}, "hooks must be removed on __exit__"


TESTS = [test_patch_only_target_head_and_positions, test_self_patch_equals_baseline,
         test_decode_step_out_of_range_is_noop, test_atp_equals_true_patch_linear,
         test_bad_head_raises, test_capture_hooks_removed]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
