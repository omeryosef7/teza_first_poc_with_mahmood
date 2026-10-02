#!/usr/bin/env python3
"""Unit tests for learned_projector.py (CPU, no GPU)."""
import os, sys, tempfile
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
if PKG not in sys.path:
    sys.path.insert(0, PKG)
import learned_projector as lp   # noqa: E402


def test_random_orthonormal_is_rank_r_and_orthonormal():
    for r in (1, 2, 4, 8, 16, 32):
        B = lp.random_orthonormal_basis(r, 4096, seed=r)
        assert B.shape == (r, 4096)
        gram = B @ B.t()
        assert torch.allclose(gram, torch.eye(r), atol=1e-4), f"rows not orthonormal at r={r}"
        assert int(torch.linalg.matrix_rank(B.double(), tol=1e-6)) == r


def test_pls1_deflation_gives_rank_r():
    g = torch.Generator().manual_seed(0)
    X = torch.randn(80, 64, generator=g)
    # label correlated with a 3-D subspace of X
    y = X[:, :3] @ torch.tensor([1.0, -0.5, 0.3]) + 0.01 * torch.randn(80, generator=g)
    W = lp.pls1(X, y, 4)
    assert W.shape[0] <= 4 and W.shape[1] == 64
    assert int(torch.linalg.matrix_rank(W.double(), tol=1e-6)) == W.shape[0], "PLS components degenerate (no deflation)"


def test_control_family_distinct_and_seeded():
    fam = lp.random_orthonormal_family(4, 4096, n=5, base_seed=1000, key="basket")
    assert len(fam) == 5 and all(k.startswith("basket__rand") for k in fam)
    # distinct draws (not byte-identical — the CSI retraction-#7 failure mode)
    mats = list(fam.values())
    for i in range(len(mats)):
        for j in range(i + 1, len(mats)):
            assert not torch.allclose(mats[i], mats[j]), "two control draws identical (seed didn't reach draw)"
    # reproducible given same seed
    fam2 = lp.random_orthonormal_family(4, 4096, n=5, base_seed=1000, key="basket")
    assert torch.allclose(fam["basket__rand0"], fam2["basket__rand0"])


def test_save_load_roundtrip_matches_format():
    B = lp.random_orthonormal_basis(5, 128, seed=7)
    meta = {"schema": "dcs_csi_axis/1", "codeword": "basket", "site": "rel-6",
            "method": "random_orthonormal_control", "control_seed": 7}
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "basis.pt")
        out_meta = lp.save_basis({"basket": B}, meta, p)
        assert out_meta["bases"]["basket"]["rank"] == 5
        assert out_meta["bases_sha16_of"] == "saved_float32_tensor_bytes"
        m2, bases = lp.load_basis(p)
        assert "basket" in bases and bases["basket"].shape == (5, 128)
        assert bases["basket"].dtype == torch.float32
        assert lp.sha16(bases["basket"]) == m2["bases"]["basket"]["sha16"], "sha16 drifted from bytes on disk"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn(); print("PASS", fn.__name__)
    print(f"\nALL {len(fns)} PASSED")
