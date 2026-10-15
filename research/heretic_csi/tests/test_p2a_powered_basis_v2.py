"""PR-HCSI-S199 basis checks (basket r1 ext): rank 1, unit-norm, candidate byte-identical, keys continue at 46,
distinct from each other and from the frozen 46, source meta copied (codeword/selected_layer/site/fit_prompt)."""
import os, sys, torch, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
EXT = os.path.join(ROOT, "configs/heretic_csi/hcsi_ranksweep_basket_r1ext.pt")
SRC = os.path.join(ROOT, "configs/heretic_csi/hcsi_ranksweep_basket.pt")


@pytest.mark.skipif(not os.path.exists(EXT), reason="basket r1ext basis not built")
def test_basket_r1ext():
    from learned_projector import sha16
    e = torch.load(EXT, map_location="cpu", weights_only=False)
    s = torch.load(SRC, map_location="cpu", weights_only=False)
    assert sha16(e["bases"]["cand_rank1"]) == s["meta"]["bases"]["cand_rank1"]["sha16"]
    for k in ("codeword", "selected_layer", "site", "fit_prompt"):
        assert e["meta"][k] == s["meta"][k]
    new = sorted((k for k in e["bases"] if k.startswith("ctrl_random_r1_")), key=lambda k: int(k.rsplit("_", 1)[1]))
    assert len(new) == 144 and int(new[0].rsplit("_", 1)[1]) == 46 and int(new[-1].rsplit("_", 1)[1]) == 189
    V = torch.cat([e["bases"][k].double() for k in new] + [s["bases"][f"ctrl_random_r1_{i}"].double() for i in range(46)])
    assert V.shape == (190, 4096)
    assert torch.allclose(V.norm(dim=1), torch.ones(190, dtype=torch.float64), atol=1e-6)
    G = (V @ V.T).abs() - torch.eye(190, dtype=torch.float64)
    assert G.max().item() < 0.2            # random unit vectors in 4096-D: |cos| ~ 0.016
    assert len({e["meta"]["bases"][k]["sha16"] for k in new}) == 144
    assert not ({e["meta"]["bases"][k]["sha16"] for k in new} & {s["meta"]["bases"][f"ctrl_random_r1_{i}"]["sha16"] for i in range(46)})
