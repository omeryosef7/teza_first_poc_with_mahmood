#!/usr/bin/env python3
"""Deployed-vs-fitted residual at the codeword row (review 2026-10-14 #9).

Each module's ΔW was fit on I/O captured from the UNEDITED knockout model, but all 26 edits are deployed
jointly, so a module's deployed input already carries the upstream edits (compounding). Using the
KO_CAPOP_r capture (KO + CAND at all rows, capture AFTER the edit) paired by context to the clean (BASE)
and unedited-KO captures, per module at the codeword row:

  GC_fitted   = 1 - sum||s_out + Δ(s_in) - t_out||^2 / sum||s_out - t_out||^2   (what the fit promised)
  GC_deployed = 1 - sum||dep_out         - t_out||^2 / sum||s_out - t_out||^2   (what the deployed model does)
  input_shift = sum||dep_in - s_in||^2 / sum||t_in - s_in||^2                   (upstream edits moved the input)
  input_toward_clean = 1 - sum||dep_in - t_in||^2 / sum||s_in - t_in||^2

Outputs a JSON with per-module rows and pooled values. CPU only.
"""
import argparse, json, os, sys

import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))


def by_ctx(path):
    d = torch.load(path, map_location="cpu")
    return {r["meta"]["ctx_sha16"]: r for r in d["records"]}, d["names"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--capop", required=True)
    ap.add_argument("--clean", required=True)
    ap.add_argument("--ko", required=True)
    ap.add_argument("--factors", required=True)
    ap.add_argument("--key", default="CAND")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dep, names = by_ctx(a.capop)
    cl, _ = by_ctx(a.clean)
    ko, _ = by_ctx(a.ko)
    fac = torch.load(a.factors, map_location="cpu")["operators"][a.key]["factors"]
    keys = [h for h in dep if h in cl and h in ko]
    if len(keys) != len(dep):
        raise SystemExit(f"{len(dep) - len(keys)} deployed records have no clean/KO partner")
    rows, tot = [], {"num_fit": 0.0, "num_dep": 0.0, "den": 0.0, "shift": 0.0, "gap_in": 0.0, "to_clean": 0.0}
    for n in names:
        A, B = (x.double() for x in fac[n])
        f = lambda r, i: r["acts"][n]["cw"][i].double()   # noqa: E731
        num_fit = num_dep = den = shift = gap_in = to_clean = 0.0
        for h in keys:
            s_in, s_out = f(ko[h], 0), f(ko[h], 1)
            t_in, t_out = f(cl[h], 0), f(cl[h], 1)
            d_in, d_out = f(dep[h], 0), f(dep[h], 1)
            pred = s_out + B @ (A @ s_in)
            num_fit += float(((pred - t_out) ** 2).sum()); num_dep += float(((d_out - t_out) ** 2).sum())
            den += float(((s_out - t_out) ** 2).sum())
            shift += float(((d_in - s_in) ** 2).sum()); gap_in += float(((t_in - s_in) ** 2).sum())
            to_clean += float(((d_in - t_in) ** 2).sum())
        rows.append({"module": n, "GC_fitted": 1 - num_fit / den, "GC_deployed": 1 - num_dep / den,
                     "input_shift": shift / max(gap_in, 1e-12), "input_toward_clean": 1 - to_clean / max(gap_in, 1e-12)})
        for k, v in zip(tot, (num_fit, num_dep, den, shift, gap_in, to_clean)):
            tot[k] += v
    pooled = {"GC_fitted": 1 - tot["num_fit"] / tot["den"], "GC_deployed": 1 - tot["num_dep"] / tot["den"],
              "input_shift": tot["shift"] / tot["gap_in"], "input_toward_clean": 1 - tot["to_clean"] / tot["gap_in"]}
    json.dump({"n_prompts": len(keys), "pooled": pooled, "modules": rows, "capop": a.capop, "factors": a.factors},
              open(a.out, "w"), indent=1)
    print(json.dumps({"n_prompts": len(keys), "pooled": pooled}))


if __name__ == "__main__":
    main()
