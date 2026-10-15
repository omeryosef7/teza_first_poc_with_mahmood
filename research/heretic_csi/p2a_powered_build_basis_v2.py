#!/usr/bin/env python3
"""Generic extended RANDOM control family builder for powered P2a re-tests (PR-HCSI-S199 onward).

Same generation code path as scripts/dcs_csi_axis.py (M = randn(R, hidden, float64, generator);
Q = qr(M.T)[0].T), NEW generator seed, indices continuing after the existing ctrl_random_r{R}_* keys.
Unlike v1 (p2a_powered_build_basis.py, S-084) this COPIES the source file's meta (codeword, selected_layer, site,
fit_prompt, fit_population, ...) so score_behavior's layer/codeword guards fire for the new file (fixes the S-107b
meta gap), then records the extension fields. The candidate key is copied byte-identically (sha16 asserted).
Never modifies the source basis file.
"""
from __future__ import annotations
import argparse, json, os, sys
import torch
sys.path.insert(0, os.path.dirname(__file__))
from learned_projector import save_basis, sha16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--cand-key", required=True)
    ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--n-new", type=int, default=144)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = torch.load(a.src, map_location="cpu", weights_only=False)
    cand = src["bases"][a.cand_key]
    assert cand.shape[0] == a.rank, (cand.shape, a.rank)
    pref = f"ctrl_random_r{a.rank}_"
    start = len([k for k in src["bases"] if k.startswith(pref)])
    assert all(f"{pref}{i}" in src["bases"] for i in range(start)), "existing keys not contiguous"
    g = torch.Generator().manual_seed(a.seed)
    bases = {a.cand_key: cand.clone()}
    for i in range(start, start + a.n_new):
        M = torch.randn(a.rank, cand.shape[1], generator=g, dtype=torch.float64)
        bases[f"{pref}{i}"] = torch.linalg.qr(M.T)[0].T.contiguous()
    meta = {k: v for k, v in src["meta"].items() if k not in ("bases", "bases_sha16_of")}
    meta.update({"schema_ext": "hcsi_p2a_powered_ext/2", "prereg": a.prereg, "source_pt": a.src,
                 "source_meta_seed": src["meta"].get("seed"), "new_generator_seed": a.seed,
                 "new_keys": f"{pref}{start}..{start + a.n_new - 1}",
                 "generation": "M=randn(R,hidden,float64,generator); Q=qr(M.T)[0].T (dcs_csi_axis.py code path)",
                 "cand_sha16_source": src["meta"]["bases"][a.cand_key]["sha16"]})
    save_basis(bases, meta, a.out)
    saved = torch.load(a.out, map_location="cpu", weights_only=False)
    assert sha16(saved["bases"][a.cand_key]) == meta["cand_sha16_source"], "candidate copy is not byte-identical"
    for k in ("codeword", "selected_layer", "site", "fit_prompt"):
        assert saved["meta"].get(k) == src["meta"].get(k), k
    print(json.dumps({"out": a.out, "n_keys": len(saved["bases"]), "new_keys": meta["new_keys"],
                      "cand_sha16": sha16(saved["bases"][a.cand_key]), "codeword": saved["meta"]["codeword"],
                      "selected_layer": saved["meta"]["selected_layer"]}))


if __name__ == "__main__":
    main()
