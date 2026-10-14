#!/usr/bin/env python3
"""Input-INDEPENDENT mean-gap comparator (PREREG AMENDMENT 3, review #2 #5).

For each operator module (o_proj/down_proj, layers 6-18 -- the same modules as CAND), the TRAIN-mean
codeword-row module-output gap  g[name] = mean_i (t_out_i - s_out_i)  (clean minus knockout), computed on
the SAME paired TRAIN captures the operators were fit on (pairing + checks via p2b_fit.load_pairs).
Deployed by p2b_runner OPSPEC bias:<file>:<all|cw> as a constant added to the module output. It is the
steering-vector version of "write the mean KO->clean shift": a CAND that does not beat it certifies only
that adding the mean shift undoes part of the knockout, not an input-conditional operator.
"""
import argparse, json, os, sys
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_fit as pf   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", required=True)
    ap.add_argument("--ko", required=True)
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--nm-factors", default=None,
                    help="AMENDMENT 6: also write norm-matched copies, one per factors file (comma list, e.g. r1,r4)")
    ap.add_argument("--nm-out", default=None, help="comma list of output paths matching --nm-factors")
    a = ap.parse_args()
    pairs, names = pf.load_pairs(a.clean, a.ko, a.codeword)
    bias, norms = {}, {}
    for n in names:
        g = torch.stack([p["clean"]["acts"][n]["cw"][1].double() - p["ko"]["acts"][n]["cw"][1].double() for p in pairs]).mean(0)
        bias[n] = g.float()
        norms[n] = float(g.norm())
    meta = {"codeword": a.codeword, "n_pairs": len(pairs), "n_domains": len({p["domain"] for p in pairs}),
            "definition": "mean over TRAIN pairs of (clean - KO) module output at the codeword row",
            "clean_capture": a.clean, "ko_capture": a.ko, "per_module_norm": norms,
            "total_norm": sum(norms.values())}
    torch.save({"bias": bias, "meta": meta}, a.out)
    print(json.dumps({k: v for k, v in meta.items() if k != "per_module_norm"}))
    if a.nm_factors:
        # MEANBIAS_NM (AMENDMENT 6, DESCRIPTIVE ONLY): the same gap direction per module, rescaled so its injected norm
        # equals CAND's MEAN per-position delta norm ||x A^T B^T||, averaged over EVERY clean TRAIN-captured input row
        # (codeword row, last row and the 6 random preserve rows per prompt). Fit/apply-side quantity from the TRAIN
        # captures + frozen factors; no endpoint is read.
        for fpath, opath in zip(a.nm_factors.split(","), a.nm_out.split(",")):
            fac = torch.load(fpath, map_location="cpu")["operators"]["CAND"]["factors"]
            tgt, vecs = {}, {}
            for n in names:
                A, B = (x.double() for x in fac[n])
                X = torch.stack([xin.double() for p in pairs for (xin, _) in p["clean"]["acts"][n].values()])
                tgt[n] = float(((X @ A.t()) @ B.t()).norm(dim=1).mean())
                vecs[n] = (bias[n].double() * (tgt[n] / max(float(bias[n].norm()), 1e-12))).float()
            m2 = {**meta, "norm_matched_to": fpath, "nm_reference": "mean_rows ||x A^T B^T|| over all clean TRAIN-captured rows",
                  "n_rows_per_module": int(X.shape[0]), "per_module_target_norm": tgt, "total_norm": sum(tgt.values()),
                  "descriptive_only": "can NEVER unlock input-conditional wording (amendment 6)"}
            torch.save({"bias": vecs, "meta": m2}, opath)
            print(json.dumps({"nm": opath, "rows": int(X.shape[0]), "total_norm": m2["total_norm"]}))


if __name__ == "__main__":
    main()
