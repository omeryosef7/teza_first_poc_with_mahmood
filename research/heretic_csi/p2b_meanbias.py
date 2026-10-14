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


if __name__ == "__main__":
    main()
