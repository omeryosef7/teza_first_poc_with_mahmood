#!/usr/bin/env python3
"""P3 v2 alignment nulls (adversarial review #2, MEDIUM-8). Replaces the isotropic Beta(k/2,(D-k)/2) null of
p3_svd_analysis.py (kept unchanged) with:
  ANISO  : reference-direction null drawn from the module's own output covariance at the codeword row:
           d_null = Xc^T z / ||Xc^T z||, Xc = centred clean module outputs (670 TRAIN prompts), z ~ N(0, I).
           Statistic s = ||P_{U_k} d||^2 for the real reference d vs 2000 null draws -> empirical p (upper tail,
           (1+#null>=s)/(N+1)) and q99.
  PLS4   : the L18 statistic mean_cos2(U_k, Q4) (mean squared cosine of principal angles with the 4-dim PLS subspace)
           compared to a DIMENSION-MATCHED null: random 4-dim subspaces (a) isotropic, (b) anisotropic (4 orthonormalised
           draws of d_null) -> q99 and empirical p.
Reference directions as in P3 v1: d_surface (own/other codeword, L6-14), refusal (L6-18), PLS rank-1 and PLS-4 (L18).
Writes reports/heretic_csi/P3_alignment_aniso.json (NEW file; v1 JSON untouched). CPU only.
"""
import glob, json, os, sys
import torch
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_fit as pf                                  # noqa: E402
from p3_svd_analysis import svd_factored, refs, proj2  # noqa: E402
CAP = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/cap")
FAC = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac")
NDRAW, D = 2000, 4096


def emp_p(s, null):
    return (1 + int((null >= s).sum())) / (len(null) + 1)


def main():
    R = refs()
    g = torch.Generator().manual_seed(20261014)
    out = {"ndraw": NDRAW, "cells": []}
    for cw in ("basket", "button"):
        files = sorted(glob.glob(f"{FAC}/factors_{cw}_r*.pt"))
        if not files:
            print(f"[aniso] {cw}: no factor files yet", flush=True); continue
        pairs, names = pf.load_pairs(f"{CAP}/cap_{cw}_BASE.pt", f"{CAP}/cap_{cw}_KO.pt", cw)
        mods = {m.name: m for m in pf.build(pairs, names, list(range(len(pairs))), "cw")}
        Xc = {n: (m.t_out.double() - m.t_out.double().mean(0)) for n, m in mods.items()}
        del pairs, mods
        for fp in files:
            r = int(fp.rsplit("_r", 1)[1][:-3])
            ops = torch.load(fp, map_location="cpu")["operators"]
            for key in ("CAND",):
                rows = {}
                for n, (A, B) in ops[key]["factors"].items():
                    L, comp = int(n.split(".")[0][1:]), n.split(".")[1]
                    k = min(r, 4)
                    U = svd_factored(A, B)[0][:, :k]
                    Z = torch.randn(Xc[n].shape[0], NDRAW, generator=g, dtype=torch.float64)
                    Dn = Xc[n].t() @ Z
                    Dn = Dn / Dn.norm(dim=0, keepdim=True)
                    null = ((U.t() @ Dn) ** 2).sum(0)
                    iso = torch.randn(D, NDRAW, generator=g, dtype=torch.float64)
                    iso = iso / iso.norm(dim=0, keepdim=True)
                    null_iso = ((U.t() @ iso) ** 2).sum(0)
                    row = {"k": k, "aniso_null_q99": float(null.quantile(0.99)), "aniso_null_mean": float(null.mean()),
                           "iso_null_q99": float(null_iso.quantile(0.99)), "align": {}}
                    refd = {}
                    other = "button" if cw == "basket" else "basket"
                    if L in R["d_surface"].get(cw, {}): refd["d_surface_own"] = R["d_surface"][cw][L]
                    if L in R["d_surface"].get(other, {}): refd["d_surface_other"] = R["d_surface"][other][L]
                    if L in R["refusal"]: refd["refusal"] = R["refusal"][L]
                    if L == 18: refd["pls_rank1_own_L18"] = R["pls"][cw]["rank1"]
                    for name, d in refd.items():
                        s = proj2(U, d)
                        row["align"][name] = {"s": s, "p_aniso": emp_p(s, null), "p_iso": emp_p(s, null_iso),
                                              "ratio_to_aniso_mean": s / float(null.mean())}
                    if L == 18:
                        Q = R["pls"][cw]["pls4"]
                        s = float(torch.linalg.svdvals(U.t() @ Q).pow(2).mean())
                        ni, na = [], []
                        for _ in range(500):
                            qi, _ = torch.linalg.qr(torch.randn(D, 4, generator=g, dtype=torch.float64))
                            ni.append(float(torch.linalg.svdvals(U.t() @ qi).pow(2).mean()))
                            za = Xc[n].t() @ torch.randn(Xc[n].shape[0], 4, generator=g, dtype=torch.float64)
                            qa, _ = torch.linalg.qr(za)
                            na.append(float(torch.linalg.svdvals(U.t() @ qa).pow(2).mean()))
                        ni, na = torch.tensor(ni), torch.tensor(na)
                        row["align"]["pls4_own_L18_mean_cos2"] = {"s": s, "null_dim": 4, "iso4_q99": float(ni.quantile(0.99)),
                                                                  "aniso4_q99": float(na.quantile(0.99)),
                                                                  "p_iso4": emp_p(s, ni), "p_aniso4": emp_p(s, na)}
                    rows[n] = row
                out["cells"].append({"codeword": cw, "rank": r, "key": key, "modules": rows})
                nsig = sum(1 for m in rows.values() for v in m["align"].values() if v.get("p_aniso", v.get("p_aniso4", 1)) <= 0.01)
                ntot = sum(len(m["align"]) for m in rows.values())
                print(f"[aniso] {cw} r{r} {key}: {nsig}/{ntot} alignment stats with anisotropic p<=0.01", flush=True)
        del Xc
    p = os.path.join(REPO, "reports/heretic_csi/P3_alignment_aniso.json")
    json.dump(out, open(p, "w"), indent=1)
    print("P3_ANISO_DONE", p, flush=True)


if __name__ == "__main__":
    main()
