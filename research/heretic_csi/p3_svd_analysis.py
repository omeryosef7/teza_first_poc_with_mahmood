#!/usr/bin/env python3
"""P3 (DESCRIPTIVE): SVD / geometry of the learned P2b weight operators ΔW = B@A.

For every factors_<cw>_r<R>.pt present (F2's p2b_fit output) and operator key in --keys (default CAND,
plus DER0 as a fitted-control comparison), per module (L<l>.o_proj / L<l>.down_proj, layers 6-18):
  * exact SVD of ΔW via QR of the factors (no dense ΔW): ΔW = U S V^T, rank <= r
  * numerical rank, entropy-effective rank exp(H(s^2/sum s^2)), cumulative Frobenius fraction,
    ||ΔW||_F, ||W_base||_F (from the pinned safetensors snapshot), ||ΔW||/||W||
  * o_proj only: HEAD MASS of ΔW = ||ΔW[:, 128h:128h+128]||_F^2 / ||ΔW||_F^2 per query head h (o_proj's
    input is the concatenation of the 32 query-head outputs, head h = columns 128h..128h+127; verified in
    transformers' LlamaAttention: attn_output.transpose(1,2).reshape(..., -1) -> o_proj).
    Mass on the inherited 8-head set [19,17,23,6,13,2,24,28] vs the distribution over random 8-head sets.
  * alignment (DESCRIPTIVE geometry, not a causal claim) of the module's left singular subspace U_k
    (k = min(r, 4) residual-WRITE directions) with reference directions, as the squared projection
    ||P_{U_k} d||^2 of the unit direction d, against the exact random-subspace null E = k/4096
    (Beta(k/2,(4096-k)/2); 99th percentile reported):
      - d_surface (bombspec_<cw>_bomb fit, block-L output at codeword_last; layers 6-14 only)
      - refusal direction (doublespeak_causality/outputs/refusal_alllayers, block-L output, last pos)
      - P2a probe axis cand_rank1 and the cand_pls4 subspace (L18 residual, rel-6 site) -- compared only
        against L18 modules' writes and flagged as a cross-position comparison
  * cross-codeword overlap of the CAND write subspaces (basket vs button, same rank/module): mean cos^2
    of principal angles vs the random null k/4096.
Outputs JSON + markdown table. Re-runnable as more ranks land. CPU only.
"""
import argparse, glob, json, math, os, random, sys
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
FAC = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac")
SNAP = "/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2"
TOP8 = [19, 17, 23, 6, 13, 2, 24, 28]
HEAD_DIM, N_HEADS, D = 128, 32, 4096


def svd_factored(A, B):
    """ΔW = B@A with A [r,in], B [out,r]. Returns U [out,r'], S [r'], V [in,r']."""
    A, B = A.double(), B.double()
    Qb, Rb = torch.linalg.qr(B)
    Qa, Ra = torch.linalg.qr(A.t())
    Uc, S, Vch = torch.linalg.svd(Rb @ Ra.t())
    return Qb @ Uc, S, Qa @ Vch.t()


def eff_rank(S):
    p = (S ** 2) / (S ** 2).sum().clamp_min(1e-300)
    p = p[p > 0]
    return float(torch.exp(-(p * p.log()).sum()))


def base_norms(names):
    from safetensors import safe_open
    idx = json.load(open(os.path.join(SNAP, "model.safetensors.index.json")))["weight_map"]
    out = {}
    for n in names:
        l, c = n.split(".")
        key = f"model.layers.{int(l[1:])}." + ("self_attn.o_proj.weight" if c == "o_proj" else "mlp.down_proj.weight")
        with safe_open(os.path.join(SNAP, idx[key]), framework="pt") as f:
            out[n] = float(f.get_tensor(key).double().norm())
    return out


def refs():
    R = {"d_surface": {}, "refusal": {}, "pls": {}}
    for cw in ("basket", "button"):
        g = glob.glob(os.path.join(REPO, f"outputs/boombness/extract_boombness/bombspec_{cw}_bomb_2026090*/directions_fit_dev.pt"))
        if g:
            p = torch.load(g[0], map_location="cpu", weights_only=False)
            R["d_surface"][cw] = {int(L): v.double() / v.double().norm() for L, v in p["d_surface"].items()}
            R.setdefault("d_surface_src", {})[cw] = os.path.relpath(g[0], REPO)
        b = torch.load(os.path.join(REPO, f"configs/heretic_csi/hcsi_ranksweep_{cw}.pt"), map_location="cpu")
        r1 = b["bases"]["cand_rank1"].double().reshape(-1, D)[0]
        q, _ = torch.linalg.qr(b["bases"]["cand_pls4"].double().t())
        R["pls"][cw] = {"rank1": r1 / r1.norm(), "pls4": q}
    for L in range(6, 19):
        f = os.path.join(REPO, f"doublespeak_causality/outputs/refusal_alllayers/refusal_direction_llama_L{L}.pt")
        if os.path.exists(f):
            v = torch.load(f, map_location="cpu", weights_only=False).double()
            R["refusal"][L] = v / v.norm()
    return R


def proj2(U, d):
    return float(((U.t() @ d) ** 2).sum())


def beta_q99(k, n=D, draws=20000, seed=0):
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(draws, n, generator=g, dtype=torch.float64)
    x = x / x.norm(dim=1, keepdim=True)
    v = (x[:, :k] ** 2).sum(1)
    return float(v.quantile(0.99))


def head_mass(A, B):
    """fraction of ||B@A||_F^2 in each query head's 128-column block (o_proj input)."""
    A, B = A.double(), B.double()
    G = B.t() @ B
    tot = float(torch.trace(A @ A.t() @ G))
    m = []
    for h in range(N_HEADS):
        Ac = A[:, h * HEAD_DIM:(h + 1) * HEAD_DIM]
        m.append(float(torch.trace(Ac @ Ac.t() @ G)) / max(tot, 1e-300))
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", default="CAND,DER0")
    ap.add_argument("--out", default=os.path.join(REPO, "reports/heretic_csi/P3_svd_descriptive.json"))
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(FAC, "factors_*_r*.pt")))
    R = refs()
    rng = random.Random(20261014)
    rand8 = [sorted(rng.sample(range(N_HEADS), 8)) for _ in range(2000)]
    res = {"files": [], "null_q99": {}, "ref_sources": {
        "d_surface": R.get("d_surface_src"), "refusal": "doublespeak_causality/outputs/refusal_alllayers (block-L out, last pos)",
        "pls": "configs/heretic_csi/hcsi_ranksweep_<cw>.pt cand_rank1 / cand_pls4 (L18 residual, rel-6)"},
        "top8": TOP8, "cells": [], "cross_codeword": []}
    WN = None
    U_store = {}
    for fp in files:
        base = os.path.basename(fp)[len("factors_"):-3]
        cw, r = base.rsplit("_r", 1); r = int(r)
        blob = torch.load(fp, map_location="cpu")
        res["files"].append({"file": os.path.relpath(fp, REPO), "codeword": cw, "rank": r,
                             "keys": list(blob["operators"])})
        for key in a.keys.split(","):
            if key not in blob["operators"]:
                continue
            fac = blob["operators"][key]["factors"]
            if WN is None:
                WN = base_norms(list(fac))
            tot2 = 0.0
            mods = []
            for n, (A, B) in fac.items():
                U, S, V = svd_factored(A, B)
                k = min(r, 4)
                L, comp = int(n.split(".")[0][1:]), n.split(".")[1]
                q99 = res["null_q99"].setdefault(str(k), beta_q99(k))
                al = {}
                ds = R["d_surface"].get(cw, {}).get(L)
                if ds is not None:
                    al["d_surface_own"] = proj2(U[:, :k], ds)
                other = "button" if cw == "basket" else "basket"
                ds2 = R["d_surface"].get(other, {}).get(L)
                if ds2 is not None:
                    al["d_surface_other"] = proj2(U[:, :k], ds2)
                if L in R["refusal"]:
                    al["refusal"] = proj2(U[:, :k], R["refusal"][L])
                if L == 18:
                    al["pls_rank1_own_L18"] = proj2(U[:, :k], R["pls"][cw]["rank1"])
                    Q = R["pls"][cw]["pls4"]
                    al["pls4_own_L18_mean_cos2"] = float(torch.linalg.svdvals(U[:, :k].t() @ Q).pow(2).mean())
                fro = float(S.norm())
                tot2 += fro ** 2
                m = {"module": n, "layer": L, "comp": comp, "fro": fro, "W_fro": WN[n], "rel": fro / WN[n],
                     "sv": [float(x) for x in S], "num_rank": int((S > 1e-6 * S.max()).sum()),
                     "eff_rank": eff_rank(S),
                     "cum_frac": [float(x) for x in (S ** 2).cumsum(0) / (S ** 2).sum()],
                     "align_k": k, "align_null_mean": k / D, "align_null_q99": q99, "align": al}
                if comp == "o_proj":
                    hm = head_mass(A, B)
                    t8 = sum(hm[h] for h in TOP8)
                    rn = sorted(sum(hm[h] for h in s) for s in rand8)
                    m["head_mass"] = hm
                    m["top8_mass"] = t8
                    m["top8_mass_pctile_vs_random8"] = sum(x < t8 for x in rn) / len(rn)
                    m["head2_mass"] = hm[2]
                mods.append(m)
                if key == "CAND":
                    U_store[(cw, r, n)] = U[:, :k]
            for m in mods:
                m["frac_of_total_norm2"] = m["fro"] ** 2 / tot2
            by_comp = {c: sum(m["fro"] ** 2 for m in mods if m["comp"] == c) / tot2 for c in ("o_proj", "down_proj")}
            by_layer = {L: sum(m["fro"] ** 2 for m in mods if m["layer"] == L) / tot2 for L in sorted({m["layer"] for m in mods})}
            res["cells"].append({"codeword": cw, "rank": r, "key": key, "total_fro": math.sqrt(tot2),
                                 "norm2_by_comp": by_comp, "norm2_by_layer": by_layer, "modules": mods})
            print(f"[p3] {cw} r{r} {key}: total ||ΔW||={math.sqrt(tot2):.2f} comp={ {k: round(v,3) for k,v in by_comp.items()} }", flush=True)
    for (cw, r, n), U in U_store.items():
        if cw != "basket" or ("button", r, n) not in U_store:
            continue
        U2 = U_store[("button", r, n)]
        c2 = torch.linalg.svdvals(U.t() @ U2).pow(2)
        res["cross_codeword"].append({"rank": r, "module": n, "k": U.shape[1], "mean_cos2": float(c2.mean()),
                                      "max_cos2": float(c2.max()), "null_mean": U.shape[1] / D})
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("P3_DONE", a.out, flush=True)


if __name__ == "__main__":
    main()
