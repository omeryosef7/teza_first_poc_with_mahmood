"""dcs_cell_geometry.py -- DCS phase, P2/P3: concept-specific 2x2 representation geometry.

WHY THIS EXISTS. The P0 audit (DCS-001) found that this repository has NO helper that reports
pairwise distance/cosine between the four cell means across layers. Every existing direction
(`d_surface`, `d_context`, `d_inter`, `d_naive`) is a fixed linear combination of those means,
so the repo could report combinations of the geometry but never the geometry itself. The single
most intuitive claim this phase might want to make --

    "under harmful demonstrations the representation of the codeword moves toward the explicit
     bomb representation"

-- is a statement about distances between cell means, and it has never been measured here.

WHAT IT COMPUTES, per (bank, split, layer):
  * the four preregistered contrast VECTORS (DCS plan Sec 1.4 cand1-cand4) plus the three existing
    directions recomputed from the SAME cell means, so every number sits on one common population;
  * their norms -- the DOSE. The shipped `.pt` stores UNIT vectors and puts magnitude in `gap`
    (signals.py:334-336), so a reader comparing stored vectors is comparing directions with the
    dose silently divided out. Here raw norms are first-class.
  * the full 4x4 cell geometry: pairwise Euclidean distance and cosine among A/B/C/E;
  * the movement statistic the phase turns on:
        toward_B = 1 - d(C,B) / d(A,B)
    i.e. what fraction of the A->B gap the codeword covers when only the demonstrations change.
    Reported beside its own components so it can never be quoted without them.

READS ONLY `directions_fit_{split}.pt`. No GPU, no model, no bank. Deliberately stdlib+torch only
so it does not import anything from the producer (standing rule 8: a verifier must not read the
producer's own derived field -- this RE-DERIVES every direction from `cell_means` and CHECKS the
recomputation against the shipped unit vectors).

SIGN CONVENTION (plan Sec 1.4): positive = more bomb-like. cand1 = C - A is already in that
orientation by construction; nothing is flipped at reporting time.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import torch

CELLS = ("A", "B", "C", "E")

#: plan Sec 1.4. Coefficients over (A, B, C, E). Kept as an explicit table rather than four
#: expressions so that adding a candidate is data, not code -- and so the algebraic dependencies
#: declared in the plan (d_context = (cand1+cand2)/2, d_surface = (cand4+cand3)/2) are checkable.
CONTRASTS = {
    "cand1_C_minus_A": {"C": 1.0, "A": -1.0},
    "cand2_B_minus_E": {"B": 1.0, "E": -1.0},
    "cand3_E_minus_A": {"E": 1.0, "A": -1.0},
    "cand4_B_minus_C": {"B": 1.0, "C": -1.0},
    # existing, recomputed from the same means (signals.py:326-336)
    "d_surface": {"B": 0.5, "C": -0.5, "E": 0.5, "A": -0.5},
    "d_context": {"C": 0.5, "A": -0.5, "B": 0.5, "E": -0.5},
    "d_inter": {"B": 1.0, "C": -1.0, "E": -1.0, "A": 1.0},   # (B-C)-(E-A), NO 1/2
    "d_naive": {"B": 1.0, "A": -1.0},
}


def combine(means: dict, coeffs: dict) -> torch.Tensor:
    out = None
    for cell, c in coeffs.items():
        v = means[cell].to(torch.float64) * c
        out = v if out is None else out + v
    return out


def cos(a: torch.Tensor, b: torch.Tensor) -> float:
    na, nb = a.norm().item(), b.norm().item()
    if na == 0 or nb == 0:
        return float("nan")
    return float((a @ b).item() / (na * nb))


def analyse_payload(path: str) -> dict:
    pl = torch.load(path, map_location="cpu", weights_only=False)
    cm = pl.get("cell_means")
    if not cm:
        return {"path": path, "error": "no cell_means in payload"}
    layers = sorted(cm["A"].keys())
    out = {
        "path": path,
        "layers": layers,
        "n_per_cell": pl.get("n_per_cell"),
        "n_families": len(pl.get("families", []) or []),
        "layer_convention": pl.get("layer_convention"),
        "per_layer": {},
        "recompute_check": {},
    }
    for L in layers:
        means = {c: cm[c][L].to(torch.float64) for c in CELLS}
        rec = {}
        vecs = {}
        for name, co in CONTRASTS.items():
            v = combine(means, co)
            vecs[name] = v
            rec[name] = {"norm": float(v.norm().item())}
        # geometry among the four cells
        geom = {}
        for i, x in enumerate(CELLS):
            for y in CELLS[i + 1:]:
                d = (means[x] - means[y]).norm().item()
                geom[f"dist_{x}{y}"] = float(d)
                geom[f"cos_{x}{y}"] = cos(means[x], means[y])
        dAB = geom["dist_AB"]
        dCB = geom["dist_BC"]
        geom["toward_B_frac"] = float("nan") if dAB == 0 else float(1.0 - dCB / dAB)
        # cosines between the candidate directions, on this same population
        names = list(CONTRASTS)
        cosmat = {}
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                cosmat[f"{a}|{b}"] = cos(vecs[a], vecs[b])
        # does C-A point toward the explicit-concept axis? (cand1 vs cand3, and vs d_surface)
        out["per_layer"][str(L)] = {
            "norms": {k: v["norm"] for k, v in rec.items()},
            "geometry": geom,
            "cos_between_contrasts": cosmat,
        }
        # verify our recomputation reproduces the shipped (unit) directions
        chk = {}
        for name in ("d_surface", "d_context", "d_inter", "d_naive"):
            shipped = pl.get(name)
            if shipped is None or L not in shipped:
                continue
            chk[name] = {
                "cos_with_shipped_unit": cos(vecs[name], shipped[L].to(torch.float64)),
                "our_norm": float(vecs[name].norm().item()),
                "shipped_gap": float(pl["gap"][name][L]) if "gap" in pl and name in pl["gap"] and L in pl["gap"][name] else None,
            }
        if chk:
            out["recompute_check"][str(L)] = chk
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True,
                    help="extract_boombness run directories (each holding directions_fit_*.pt)")
    ap.add_argument("--out", required=True, help="output JSON path")
    args = ap.parse_args()

    result = {"runs": {}}
    for run in args.runs:
        md = os.path.join(run, "metadata.json")
        meta = json.load(open(md)) if os.path.exists(md) else {}
        entry = {
            "bank_path": meta.get("bank_path"),
            "bank_file_sha16": meta.get("bank_file_sha16"),
            "bank_rows_sha16": meta.get("bank_rows_sha16"),
            "model": meta.get("model"),
            "seed": meta.get("seed"),
            "git_sha": meta.get("git_sha"),
            "git_dirty": meta.get("git_dirty"),
            "argv": meta.get("argv"),
            "splits": {},
        }
        for p in sorted(glob.glob(os.path.join(run, "directions_fit_*.pt"))):
            split = os.path.basename(p).replace("directions_fit_", "").replace(".pt", "")
            entry["splits"][split] = analyse_payload(p)
        result["runs"][os.path.basename(run)] = entry

    with open(args.out, "w") as f:
        json.dump(result, f, indent=1)
    print(f"[dcs-geom] wrote {args.out}  ({len(result['runs'])} runs)")

    # --- console summary: the one sentence this phase exists to test ---
    print(f"\n  {'run':34s} {'split':8s} {'L':>3s} {'d(A,B)':>9s} {'d(C,B)':>9s} {'toward_B':>9s} {'|C-A|':>9s}")
    for rn, e in result["runs"].items():
        for split, s in e["splits"].items():
            if "error" in s:
                print(f"  {rn:34s} {split:8s}  ERROR {s['error']}")
                continue
            for L in s["layers"]:
                g = s["per_layer"][str(L)]["geometry"]
                n = s["per_layer"][str(L)]["norms"]
                print(f"  {rn[:34]:34s} {split:8s} {L:3d} {g['dist_AB']:9.3f} {g['dist_BC']:9.3f} "
                      f"{g['toward_B_frac']:9.4f} {n['cand1_C_minus_A']:9.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
