"""
GPU-free synthetic test for 51_mlp_attribution's _MLPActGradCapture (N7-A). On a LINEAR toy whose
layer.mlp is an nn.Linear, first-order MLP-AtP is EXACT: g_mlp . (mlp_corrupt - mlp_clean) equals the
true metric delta from overwriting that layer's mlp output. Mirrors test_zhead_synthetic's AtP check.

Run:  python doublespeak_causality/tests/test_mlp_attribution.py
      pytest doublespeak_causality/tests/test_mlp_attribution.py -q
"""
import os, sys, importlib.util
import torch
import torch.nn as nn

HERE = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, HERE)

mlp = importlib.util.spec_from_file_location("mlp51", os.path.join(HERE, "51_mlp_attribution.py"))
mlp51 = importlib.util.module_from_spec(mlp); mlp.loader.exec_module(mlp51)

H = 4


class ToyMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.lin = nn.Linear(H, H, bias=False)
    def forward(self, x):
        return self.lin(x)                       # linear -> AtP exact


class ToyBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.mlp = ToyMLP()
    def forward(self, h):
        return h + self.mlp(h)


class ToyModel(nn.Module):
    def __init__(self, n_layers=2):
        super().__init__()
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(ToyBlock() for _ in range(n_layers))
        self.W_U = nn.Linear(H, 5, bias=False)
    def forward(self, x):
        h = x
        for layer in self.model.layers:
            h = layer(h)
        return h


def test_mlp_atp_equals_true_patch_linear():
    torch.manual_seed(0)
    m = ToyModel(n_layers=2)
    for p in m.parameters():
        p.data = torch.randn_like(p.data) * 0.5
    x = torch.randn(1, 3, H)
    qpos, L = 2, 0
    corrupt_mlp = torch.tensor([1.0, -0.5, 0.3, 0.2])

    def metric(out):
        return m.W_U(out[0, -1, :]).float()[0]   # a linear readout

    # AtP: capture layer-L mlp output + grad, dot with (corrupt - clean)
    cap = mlp51._MLPActGradCapture(m, [L])
    with torch.enable_grad():
        with cap:
            out = m(x); M = metric(out)
        M.backward()
    a = cap.acts[L]
    g = a.grad[0][qpos].float()
    clean_mlp = a.detach()[0][qpos].float()
    atp = float((g * (corrupt_mlp - clean_mlp)).sum())

    # true patch: overwrite layer-L mlp output at qpos with corrupt, measure metric delta
    m_clean = float(metric(m(x)).detach())
    h = None
    def hook(mod, inp, outp):
        o = outp.clone(); o[0, qpos, :] = corrupt_mlp; return o
    handle = m.model.layers[L].mlp.register_forward_hook(hook)
    m_patched = float(metric(m(x)).detach())
    handle.remove()
    true_delta = m_patched - m_clean

    assert abs(atp - true_delta) < 1e-4, f"MLP-AtP {atp} != true {true_delta} (must be exact for linear)"


def test_capture_hooks_mlp_and_removes():
    m = ToyModel(n_layers=2)
    x = torch.randn(1, 3, H)
    cap = mlp51._MLPActGradCapture(m, [0, 1])
    with cap:
        m(x)
    assert set(cap.acts.keys()) == {0, 1}, "should capture both target layers' mlp outputs"
    cap.acts.clear()
    m(x)
    assert cap.acts == {}, "hooks must be removed on __exit__"


TESTS = [test_mlp_atp_equals_true_patch_linear, test_capture_hooks_mlp_and_removes]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t(); print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1; print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS)-fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
