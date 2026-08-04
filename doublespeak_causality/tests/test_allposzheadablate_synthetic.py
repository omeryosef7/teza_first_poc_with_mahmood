"""GPU-free synthetic test for pair_common.AllPositionZHeadAblate. No model/GPU. Verifies the
all-position head ablation zeros exactly the requested heads at EVERY position, leaves others
untouched, handles the mode, and cleans up hooks."""
import os, sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pair_common import AllPositionZHeadAblate  # noqa: E402


class ToyAttn(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.o_proj = nn.Identity()          # o_proj INPUT == the head-concat z we edit


class ToyBlock(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.self_attn = ToyAttn(hidden)


class ToyCfg:
    def __init__(self, n_heads, hidden):
        self.num_attention_heads = n_heads
        self.hidden_size = hidden
        self.head_dim = hidden // n_heads
        self.num_key_value_heads = n_heads


class ToyModel(nn.Module):
    def __init__(self, n_layers=2, n_heads=4, head_dim=3):
        super().__init__()
        hidden = n_heads * head_dim
        self.config = ToyCfg(n_heads, hidden)
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock(hidden) for _ in range(n_layers))

    def run(self, z):
        # apply each layer's o_proj (Identity) with hooks active
        out = []
        for blk in self.model.layers:
            out.append(blk.self_attn.o_proj(z))
        return out


def test_zero_ablates_requested_heads_all_positions():
    m = ToyModel(n_layers=2, n_heads=4, head_dim=3)
    z = torch.arange(1 * 5 * 12, dtype=torch.float32).reshape(1, 5, 12)  # [b,seq,n_heads*head_dim]
    with AllPositionZHeadAblate(m, {0: [1, 3]}, mode="zero"):
        out0 = m.model.layers[0].self_attn.o_proj(z)
    zr = out0.view(1, 5, 4, 3)
    assert torch.all(zr[:, :, 1, :] == 0), "head 1 must be zero at ALL positions"
    assert torch.all(zr[:, :, 3, :] == 0), "head 3 must be zero at ALL positions"
    assert torch.all(zr[:, :, 0, :] == z.view(1, 5, 4, 3)[:, :, 0, :]), "head 0 untouched"
    assert torch.all(zr[:, :, 2, :] == z.view(1, 5, 4, 3)[:, :, 2, :]), "head 2 untouched"


def test_mean_mode_sets_head_to_its_position_mean():
    m = ToyModel(n_layers=1, n_heads=2, head_dim=2)
    z = torch.tensor([[[1., 2., 10., 20.], [3., 4., 30., 40.]]])  # [1,2,4]; head0=[:2], head1=[2:]
    with AllPositionZHeadAblate(m, {0: [0]}, mode="mean"):
        out = m.model.layers[0].self_attn.o_proj(z)
    zr = out.view(1, 2, 2, 2)
    # head0 mean over positions: ([1,2]+[3,4])/2 = [2,3], broadcast to both positions
    assert torch.allclose(zr[0, 0, 0], torch.tensor([2., 3.])) and torch.allclose(zr[0, 1, 0], torch.tensor([2., 3.]))
    assert torch.allclose(zr[0, :, 1], torch.tensor([[10., 20.], [30., 40.]])), "head1 untouched"


def test_decode_step_single_position():
    m = ToyModel(n_layers=1, n_heads=2, head_dim=2)
    z = torch.ones(1, 1, 4)              # seq==1 (a KV-cached decode step)
    with AllPositionZHeadAblate(m, {0: [0]}, mode="zero"):
        out = m.model.layers[0].self_attn.o_proj(z)
    zr = out.view(1, 1, 2, 2)
    assert torch.all(zr[0, 0, 0] == 0) and torch.all(zr[0, 0, 1] == 1), "decode-step ablation works"


def test_hooks_removed():
    m = ToyModel(n_layers=2, n_heads=2, head_dim=2)
    with AllPositionZHeadAblate(m, {0: [0], 1: [1]}, mode="zero") as a:
        pass
    assert a._handles == []
    z = torch.ones(1, 2, 4)
    assert torch.all(m.model.layers[0].self_attn.o_proj(z) == 1), "hook removed"


TESTS = [test_zero_ablates_requested_heads_all_positions, test_mean_mode_sets_head_to_its_position_mean,
         test_decode_step_single_position, test_hooks_removed]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
