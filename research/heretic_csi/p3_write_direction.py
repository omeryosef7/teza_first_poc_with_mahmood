#!/usr/bin/env python3
"""P3 follow-up (DESCRIPTIVE): what is the WRITE direction of the learned operators?

Observation that motivated this (P3 pass 1): the top left singular vector U1 of CAND is ~identical (|cos| >= 0.98)
to that of every fitted control (DER, even role-swapped SHUF) at every module, while the full-ΔW Frobenius cosine is
only ~0.6 (DER) / ~0.35 (SHUF). Hypothesis: U1 is a domain-GENERAL output direction (e.g. the mean KO->clean output
gap, or the dominant output direction of the module) and any specificity lives in the READ side A.

Per codeword and module (codeword row, TRAIN captures):
  g      = mean_i (t_out_i - s_out_i)            mean clean-minus-KO output gap
  mu_t   = mean_i t_out_i                         mean clean output
  pc1    = top principal direction of the per-prompt gap (t_out - s_out) after removing its mean
  frac_mean_gap = ||g||^2 * n / sum_i ||t_out_i - s_out_i||^2   (share of gap energy that is a common shift)
and for every available factors_<cw>_r<R>.pt CAND: |cos(U1, g)|, |cos(U1, mu_t)|, |cos(U1, pc1)|.
Cross-codeword: |cos(g_basket, g_button)| per module (is the gap itself codeword-general?).
"""
import glob, json, os, sys
import torch
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_fit as pf                      # noqa: E402
from p3_svd_analysis import svd_factored  # noqa: E402
CAP = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/cap")
FAC = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/fac")


def unit(v):
    return v / v.norm().clamp_min(1e-30)


def main():
    out = {"per_codeword": {}, "cross_codeword_gap_cos": {}}
    G = {}
    for cw in ("basket", "button"):
        pairs, names = pf.load_pairs(f"{CAP}/cap_{cw}_BASE.pt", f"{CAP}/cap_{cw}_KO.pt", cw)
        mods = pf.build(pairs, names, list(range(len(pairs))), "cw")
        st = {}
        for m in mods:
            d = (m.t_out - m.s_out).double()
            g = d.mean(0)
            frac = float(g.pow(2).sum() * d.shape[0] / d.pow(2).sum())
            dc = d - g
            _, _, Vh = torch.linalg.svd(dc, full_matrices=False)
            st[m.name] = {"g": unit(g), "mu_t": unit(m.t_out.double().mean(0)), "pc1": Vh[0], "frac_mean_gap": frac}
        G[cw] = st
        res = {"modules": {n: {"frac_mean_gap": v["frac_mean_gap"]} for n, v in st.items()}, "operators": {}}
        for fp in sorted(glob.glob(f"{FAC}/factors_{cw}_r*.pt")):
            r = int(fp.rsplit("_r", 1)[1][:-3])
            ops = torch.load(fp, map_location="cpu")["operators"]
            for key in ("CAND", "DER0", "SHUF0"):
                if key not in ops:
                    continue
                row = {}
                for n, (A, B) in ops[key]["factors"].items():
                    U = svd_factored(A, B)[0][:, 0]
                    row[n] = {k: abs(float(U @ st[n][k])) for k in ("g", "mu_t", "pc1")}
                res["operators"][f"r{r}:{key}"] = row
                mg = sum(x["g"] for x in row.values()) / len(row)
                print(f"[wd] {cw} r{r} {key}: mean |cos(U1, mean gap)| = {mg:.3f}", flush=True)
        out["per_codeword"][cw] = res
        del pairs, mods
    for n in G["basket"]:
        out["cross_codeword_gap_cos"][n] = abs(float(G["basket"][n]["g"] @ G["button"][n]["g"]))
    p = os.path.join(REPO, "reports/heretic_csi/P3_write_direction.json")
    json.dump(out, open(p, "w"), indent=1)
    print("P3_WD_DONE", p, flush=True)


if __name__ == "__main__":
    main()
