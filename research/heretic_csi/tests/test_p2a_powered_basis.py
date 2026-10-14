"""PR-HCSI-S084 basis checks: rank 4, orthonormal, distinct from each other AND from the frozen 46, candidate
byte-identical, keys continue at 46 (no tag collision)."""
import os, sys, torch, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXT = os.path.join(ROOT, "configs/heretic_csi/hcsi_ranksweep_button_r4ext.pt")
SRC = os.path.join(ROOT, "configs/heretic_csi/hcsi_ranksweep_button.pt")


@pytest.mark.skipif(not os.path.exists(EXT), reason="extended basis not built")
def test_ext_basis():
    from learned_projector import sha16
    e = torch.load(EXT, map_location="cpu", weights_only=False)
    s = torch.load(SRC, map_location="cpu", weights_only=False)
    assert sha16(e["bases"]["cand_pls4"]) == s["meta"]["bases"]["cand_pls4"]["sha16"]
    new = sorted((k for k in e["bases"] if k.startswith("ctrl_random_r4_")), key=lambda k: int(k.rsplit("_", 1)[1]))
    assert len(new) >= 144 and int(new[0].rsplit("_", 1)[1]) == 46
    old = [s["bases"][f"ctrl_random_r4_{i}"] for i in range(46)]
    allb = [e["bases"][k].double() for k in new] + [b.double() for b in old]
    for k in new:
        B = e["bases"][k].double()
        assert B.shape == (4, 4096)
        assert torch.linalg.matrix_rank(B).item() == 4
        assert torch.allclose(B @ B.T, torch.eye(4, dtype=torch.float64), atol=1e-5)
        assert e["meta"]["bases"][k]["sha16"] == sha16(e["bases"][k])
    # distinctness: projector overlap between any two bases far from identical (random 4-dim in 4096 ~ 4/4096)
    P = torch.stack([b.T @ b for b in allb[:60]])  # pairwise check on a subset keeps it cheap
    for i in range(len(P)):
        for j in range(i + 1, len(P)):
            assert (P[i] * P[j]).sum().item() < 0.5
    # every new key distinct from every old key (hash level)
    oldh = {s["meta"]["bases"][f"ctrl_random_r4_{i}"]["sha16"] for i in range(46)}
    assert not oldh & {e["meta"]["bases"][k]["sha16"] for k in new}
    assert len({e["meta"]["bases"][k]["sha16"] for k in new}) == len(new)
