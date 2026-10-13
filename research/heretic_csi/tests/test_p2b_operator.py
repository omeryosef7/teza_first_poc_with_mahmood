"""Unit + synthetic tests for P2b (CPU, no model). Run: python -m pytest research/heretic_csi/tests/test_p2b_operator.py -q"""
import os, sys
import torch
import torch.nn as nn

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p2b_operator as po   # noqa: E402
import p2b_fit as pf        # noqa: E402

D, F = 16, 24


class Layer(nn.Module):
    def __init__(self):
        super().__init__()
        self.self_attn = nn.Module(); self.self_attn.o_proj = nn.Linear(D, D, bias=False)
        self.mlp = nn.Module(); self.mlp.down_proj = nn.Linear(F, D, bias=False)


class Toy(nn.Module):
    def __init__(self, n=3):
        super().__init__()
        self.model = nn.Module(); self.model.layers = nn.ModuleList([Layer() for _ in range(n)])


def _hooks(m):
    return sum(len(x._forward_hooks) for x in m.modules())


def test_operator_hooks_exact_and_removed():
    torch.manual_seed(0)
    m = Toy(); lin = m.model.layers[1].self_attn.o_proj
    x = torch.randn(1, 5, D)
    base = lin(x)
    A, B = torch.randn(2, D), torch.randn(D, 2)
    with po.OperatorHooks(m, {"L1.o_proj": (A, B)}) as hk:
        y = lin(x)
    assert torch.allclose(y, base + (x @ A.t()) @ B.t(), atol=1e-5)
    assert hk.n_calls == 1 and _hooks(m) == 0
    assert torch.equal(lin(x), base)                      # restored exactly


def test_identity_is_inert():
    m = Toy(); lin = m.model.layers[0].mlp.down_proj
    x = torch.randn(1, 4, F); base = lin(x)
    fac = po.identity_factors({"L0.down_proj": (D, F)}, 3)
    with po.OperatorHooks(m, fac):
        assert torch.equal(lin(x), base)


def test_capture_first_forward_only_and_position():
    m = Toy(); lin = m.model.layers[2].self_attn.o_proj
    cap = po.CaptureHooks(m, ["L2.o_proj"])
    x1, x2 = torch.randn(1, 6, D), torch.randn(1, 7, D)
    with cap:
        cap.arm({"cw": 2, "last": 5}, {"k": 1})
        lin(x1); lin(x2)                                  # second forward must NOT be recorded
    assert len(cap.records) == 1 and _hooks(m) == 0
    xin, yout = cap.records[0]["acts"]["L2.o_proj"]["cw"]
    assert torch.allclose(xin.float(), x1[0, 2].bfloat16().float())
    assert torch.allclose(yout.float(), lin(x1)[0, 2].detach().bfloat16().float())


def _synthetic(n=200, seed=0, true_rank=2):
    g = torch.Generator().manual_seed(seed)
    W = torch.randn(D, F, generator=g) / F ** 0.5
    U, V = torch.randn(D, true_rank, generator=g), torch.randn(true_rank, F, generator=g)
    s_in = torch.randn(n, F, generator=g); t_in = s_in.clone()
    # KO loses a rank-2 component that the clean forward writes: target = W s + U V s
    s_out, t_out = s_in @ W.t(), s_in @ W.t() + (s_in @ V.t()) @ U.t() * 0.3
    p_in = torch.randn(n, F, generator=g) * 0.0           # preserve set irrelevant here
    return [po.PairedIO("L0.down_proj", s_in, s_out, t_in, t_out, p_in)]


def test_fit_closes_gap_and_rank_matters():
    mods = _synthetic()
    gcs = {}
    for r in (1, 2, 4):
        fac = po.fit_factored(mods, po.FitCfg(rank=r, objective="mse", n_steps=10))
        gcs[r] = po.gap_closure(mods, fac)["gap_closure"]
        A, B = fac["L0.down_proj"]
        assert po.numerical_rank(A, B) <= r
    assert gcs[2] > 0.95 and gcs[1] < gcs[2]              # true operator is rank 2


def test_objectives_all_run_and_reduce_gap():
    mods = _synthetic()
    m = mods[0]
    for obj in po.OBJECTIVES:
        fac = po.fit_factored(mods, po.FitCfg(rank=2, objective=obj, n_steps=5))
        if obj == "knn":   # UNPAIRED: closes the distance to the nearest target, not to the paired one
            A, B = fac[m.name]
            new_s = m.s_out + (m.s_in @ A.t()) @ B.t()
            assert po.mean_distance_to_knn(new_s, m.t_out, 1) < 0.9 * po.mean_distance_to_knn(m.s_out, m.t_out, 1)
        else:
            assert po.gap_closure(mods, fac)["gap_closure"] > 0.3, obj


def test_random_norm_matched():
    shapes = {"L0.o_proj": (D, D), "L0.down_proj": (D, F)}
    target = {"L0.o_proj": 2.5, "L0.down_proj": 0.7}
    fac = po.random_norm_matched(shapes, 3, target, seed=1)
    for n, (A, B) in fac.items():
        assert abs(po.fro_norm(A, B) - target[n]) < 1e-4
        assert po.numerical_rank(A, B) == 3
    fac2 = po.random_norm_matched(shapes, 3, target, seed=2)
    assert not torch.allclose(fac["L0.o_proj"][1], fac2["L0.o_proj"][1])


def test_rescale_and_fro():
    A, B = torch.randn(3, F), torch.randn(D, 3)
    assert abs(po.fro_norm(A, B) - float((B @ A).norm())) < 1e-4
    (A2, B2), = po.rescale_to({"x": (A, B)}, {"x": 5.0}).values()
    assert abs(po.fro_norm(A2, B2) - 5.0) < 1e-4


def test_degenerate_fits_are_zero():
    mods = _synthetic()
    for which in ("SRC2SRC", "TGT2TGT"):
        fac = po.fit_factored(pf.degenerate(mods, which), po.FitCfg(rank=2, objective="mse", n_steps=3))
        A, B = fac["L0.down_proj"]
        assert po.fro_norm(A, B) == 0.0


def _fake_pairs(n_dom=6, per=4):
    pairs = []
    for d in range(n_dom):
        for k in range(per):
            acts = lambda s: {"L0.o_proj": {"cw": (torch.randn(D) + s, torch.randn(D)),    # noqa: E731
                                            "last": (torch.randn(D), torch.randn(D))}}
            pairs.append({"domain": f"d{d}", "ko": {"acts": acts(0)}, "clean": {"acts": acts(1)}})
    return pairs


def test_shuffle_is_domain_derangement_and_folds_partition():
    pairs = _fake_pairs()
    idx = list(range(len(pairs)))
    perm, swap = pf.shuffle_plan(pairs, idx, 3)
    assert sorted(perm) == idx and all(pairs[i]["domain"] != pairs[j]["domain"] for i, j in zip(idx, perm))
    assert 0 < sum(swap) < len(swap)
    mods = pf.build(pairs, ["L0.o_proj"], idx, "cw", shuffle_seed=3)
    assert mods[0].s_in.shape == (24, D) and mods[0].p_in.shape == (48, D)
    folds = pf.domain_folds(pairs, k=3)
    assert sorted(i for f in folds for i in f) == idx
    for f in folds:   # no domain split across folds
        ds = {pairs[i]["domain"] for i in f}
        assert all(pairs[i]["domain"] not in ds for g in folds if g is not f for i in g)


def test_preserve_set_includes_extra_rows():
    pairs = _fake_pairs(n_dom=3, per=2)
    for p in pairs:   # clean capture carries 2 extra preserve rows; KO capture does not
        p["clean"]["acts"]["L0.o_proj"]["x0"] = (torch.randn(D), torch.randn(D))
        p["clean"]["acts"]["L0.o_proj"]["x1"] = (torch.randn(D), torch.randn(D))
    m = pf.build(pairs, ["L0.o_proj"], list(range(len(pairs))), "cw")[0]
    assert m.p_in.shape == (len(pairs) * 4, D) and m.s_in.shape == (len(pairs), D)
