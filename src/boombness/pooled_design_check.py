"""pooled_design_check.py — would pooling banks give a design that separates identity from dose?

WHY THIS SCRIPT EXISTS AT ALL. Its artifact (`pooled_design_feasibility.json`) was produced by an
ad-hoc computation and committed with **no producing script** — violating the bar quoted at the top of
`verify_report_numbers.py`: *every number in the final report must be regenerable by a committed script
from a committed artifact.* Six figures in a section that ended with a directive to future work rested
on something nobody could re-run. Audit #11 found it. This is that script.

WHAT IT COMPUTES, AND WHY THE ANSWER IS NO. C-13 showed that on a single bank, "remove `d_surface`" and
"remove a lot of cell-mean variance" are geometrically inseparable, and recommended a different design.
Pooling the cells of `carrot->bomb`, `carrot->knife` and `button->bomb` looks like it helps: the
spectrum flattens and directions orthogonal to `d_surface` carry 1.8x more dose.

Two controls kill that reading, and both are computed here:

  * pooling three IDENTICAL copies of one bank changes nothing, so pooling per se buys zero -- the
    entire gain comes from the three banks' `d_surface` directions being non-collinear; and
  * the direction carrying the new dose is ITSELF a surface contrast (cos ~0.66 with knife's own
    `d_surface`), and removing every bank's own `d_surface` from its own cells leaves essentially the
    same residual as the single bank (0.1614 vs 0.1598) -- pooling adds NO non-surface variance.

So a control built to reach the pooled `b` would most likely be another codeword's surface contrast:
precisely the confound C-13 flagged. The script prints that conclusion rather than leaving it to a
reader who might see only the encouraging first table.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
import sys

FITS = {
    "carrot_bomb": "outputs/boombness/extract_boombness/full_20260816_185942_1008673",
    "carrot_knife": "outputs/boombness/extract_boombness/knifefit_*",
    "button_bomb": "outputs/boombness/extract_boombness/buttonfit_*",
}


def cells_and_dir(fit_dir, layer):
    import torch
    d = sorted(glob.glob(fit_dir))[-1] if "*" in fit_dir else fit_dir
    pl = torch.load(os.path.join(d, "directions_fit_dev.pt"), map_location="cpu",
                    weights_only=False)
    cm = pl["cell_means"]
    rows = [cm[c][layer].float().reshape(-1) for c in sorted(cm)
            if isinstance(cm.get(c), dict) and cm[c].get(layer) is not None]
    v = pl["d_surface"][layer].float().reshape(-1)
    return torch.stack(rows), v / v.norm(), os.path.basename(d)


def geometry(M, u):
    import torch
    Mc = M - M.mean(dim=0, keepdim=True)
    tot = float((Mc ** 2).sum())
    a = float(((Mc @ u.reshape(-1, 1)) ** 2).sum()) / tot
    Mp = Mc - (Mc @ u.reshape(-1, 1)) @ u.reshape(1, -1)
    S = torch.linalg.svdvals(Mc)
    b = float(torch.linalg.svdvals(Mp)[0] ** 2) / tot
    return {"dose_d_surface": a, "max_orthogonal_dose": b,
            "top_eigenvalue_share": float(S[0] ** 2) / tot, "n_cells": int(M.shape[0])}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layer", type=int, default=8)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import torch
    L = args.layer

    per, mats = {}, {}
    for name, pat in FITS.items():
        M, u, base = cells_and_dir(pat, L)
        mats[name] = (M, u)
        per[name] = {**geometry(M, u), "fit": base}

    ref_u = mats["carrot_bomb"][1]
    pooled = torch.cat([mats[k][0] for k in mats], 0)
    pooled_geo = geometry(pooled, ref_u)

    # CONTROL 1 -- pooling three identical copies of one bank
    dup = torch.cat([mats["carrot_bomb"][0]] * 3, 0)
    dup_geo = geometry(dup, ref_u)

    # CONTROL 2 -- is the new orthogonal dose just another codeword's surface contrast?
    Mc = pooled - pooled.mean(dim=0, keepdim=True)
    Mp = Mc - (Mc @ ref_u.reshape(-1, 1)) @ ref_u.reshape(1, -1)
    _, _, Vh = torch.linalg.svd(Mp, full_matrices=False)
    w = Vh[0] / Vh[0].norm()
    cos_w = {k: abs(float(torch.dot(w, mats[k][1]))) for k in mats}

    # CONTROL 3 -- residual after removing EVERY bank's own d_surface from its own cells
    resid = []
    for k, (M, u) in mats.items():
        Mk = M - M.mean(dim=0, keepdim=True)
        resid.append(Mk - (Mk @ u.reshape(-1, 1)) @ u.reshape(1, -1))
    R = torch.cat(resid, 0)
    # TWO NORMALISATIONS, both reported. Dividing by the POOLED-centred total counts the between-bank
    # offsets in the denominator; dividing by the sum of each bank's OWN centred total does not. They
    # answer slightly different questions and audit #11 quoted the second (0.1614) while a first pass
    # here computed the first (0.1225). Neither changes the conclusion -- pooling adds no non-surface
    # variance either way -- but publishing one without naming the choice is the estimand error this
    # sprint has already made twice.
    pooled_resid_frac = float((R ** 2).sum()) / float((Mc ** 2).sum())
    own_tot = sum(float(((m - m.mean(dim=0, keepdim=True)) ** 2).sum()) for m, _ in mats.values())
    pooled_resid_frac_own = float((R ** 2).sum()) / own_tot
    M1 = mats["carrot_bomb"][0]
    M1c = M1 - M1.mean(dim=0, keepdim=True)
    u1 = mats["carrot_bomb"][1]
    single_resid_frac = 1.0 - float(((M1c @ u1.reshape(-1, 1)) ** 2).sum()) / float((M1c ** 2).sum())

    cross = {f"{a}|{b}": abs(float(torch.dot(mats[a][1], mats[b][1])))
             for i, a in enumerate(mats) for b in list(mats)[i + 1:]}

    doc = {"layer": L, "per_bank": per, "pooled": pooled_geo,
           "control_1_three_identical_copies": dup_geo,
           "control_2_new_orthogonal_direction_vs_each_banks_d_surface": cos_w,
           "control_3_residual_after_removing_each_banks_own_d_surface": {
               "pooled_over_pooled_centred_total": pooled_resid_frac,
               "pooled_over_sum_of_own_centred_totals": pooled_resid_frac_own,
               "single_bank": single_resid_frac,
               "note": "the two pooled normalisations differ only in whether between-bank offsets sit "
                       "in the denominator; the conclusion is the same under both"},
           "cross_bank_d_surface_cosines": cross,
           "VERDICT": ("Pooling does NOT deliver the design C-13 asked for. Control 1: three identical "
                       "copies leave the geometry unchanged, so pooling per se buys nothing -- the gain "
                       "is entirely that the banks' d_surface directions are non-collinear. Control 2: "
                       "the direction carrying the new orthogonal dose is itself a surface contrast. "
                       "Control 3: pooling adds essentially no non-surface variance. A control built to "
                       "reach the pooled b would most likely be another codeword's surface contrast, "
                       "which is the confound C-13 flagged."),
           "provenance": {"argv": sys.argv, "git_commit": subprocess.run(
               ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}}
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)

    print(f"  {'design':16s} {'cells':>6s} {'top-eig':>8s} {'dose(d_s)':>10s} {'max orth':>9s}")
    for k, v in per.items():
        print(f"  {k:16s} {v['n_cells']:6d} {v['top_eigenvalue_share']:8.4f} "
              f"{v['dose_d_surface']:10.4f} {v['max_orthogonal_dose']:9.4f}")
    print(f"  {'POOLED':16s} {pooled_geo['n_cells']:6d} {pooled_geo['top_eigenvalue_share']:8.4f} "
          f"{pooled_geo['dose_d_surface']:10.4f} {pooled_geo['max_orthogonal_dose']:9.4f}")
    print(f"  {'3 IDENTICAL':16s} {dup_geo['n_cells']:6d} {dup_geo['top_eigenvalue_share']:8.4f} "
          f"{dup_geo['dose_d_surface']:10.4f} {dup_geo['max_orthogonal_dose']:9.4f}  <- control 1")
    print(f"\n  control 2 — new orthogonal direction vs each bank's own d_surface: "
          + ", ".join(f"{k}={v:.2f}" for k, v in cos_w.items()))
    print(f"  control 3 — residual after removing each bank's own d_surface: pooled "
          f"{pooled_resid_frac:.4f} (÷ pooled-centred total) / {pooled_resid_frac_own:.4f} "
          f"(÷ sum of own totals) vs single {single_resid_frac:.4f}")
    print(f"\n  VERDICT: pooling does NOT deliver the design C-13 asked for.")
    print(f"\n[pooled-design] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
