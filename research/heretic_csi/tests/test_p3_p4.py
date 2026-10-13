import os, sys, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import p3_svd_analysis as p3


def test_svd_factored_matches_dense():
    torch.manual_seed(0)
    A, B = torch.randn(3, 50, dtype=torch.float64), torch.randn(40, 3, dtype=torch.float64)
    U, S, V = p3.svd_factored(A, B)
    dense = (B @ A).double()
    assert torch.allclose(U @ torch.diag(S) @ V.t(), dense, atol=1e-8)
    assert torch.allclose(S, torch.linalg.svdvals(dense)[:3], atol=1e-8)


def test_head_mass_sums_to_one_and_localizes():
    A = torch.zeros(2, 4096); A[:, 256:384] = torch.randn(2, 128)   # head 2 only
    B = torch.randn(4096, 2)
    hm = p3.head_mass(A, B)
    assert abs(sum(hm) - 1) < 1e-9 and hm[2] > 0.999999


def test_eff_rank():
    assert abs(p3.eff_rank(torch.tensor([1.0, 0, 0])) - 1) < 1e-9
    assert abs(p3.eff_rank(torch.tensor([1.0, 1.0])) - 2) < 1e-9


def test_p4_head_restriction_embeds_zero_outside_heads():
    import p4_head_fit as p4, p2b_operator as po
    torch.manual_seed(0)
    n, din, dout = 40, 4096, 16
    s_in = torch.randn(n, din); t_in = s_in.clone()
    W = torch.randn(dout, din) * 0.01
    s_out = s_in @ W.t(); t_out = s_out + torch.randn(n, dout)
    m = po.PairedIO("L10.o_proj", s_in, s_out, t_in, t_out, torch.randn(10, din))
    fac = p4.fit_variant([m], po.FitCfg(rank=2, n_steps=2), heads=[2, 5])
    A, B = fac["L10.o_proj"]
    keep = p4.cols([2, 5])
    mask = torch.ones(din, dtype=torch.bool); mask[keep] = False
    assert A.shape == (2, din) and float(A[:, mask].abs().max()) == 0.0 and float(A[:, keep].abs().max()) > 0
    assert list(keep[:3]) == [256, 257, 258] and int(keep[128]) == 640


def test_p4_random_heads_disjoint_from_top8():
    import random, p4_head_fit as p4
    for j in range(60):
        hs = random.Random(4000 + 100 + j).sample(p4.NON_TOP8, 8)
        assert not set(hs) & set(p4.TOP8) and len(set(hs)) == 8
