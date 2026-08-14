"""build_intervention_directions.py -- Phase 4 direction + dose artifacts (plan §8.1-8.2).

From a full Bombness extraction, build the per-layer intervention directions the causal
harness needs, and calibrate the natural dose. Pure numpy (+ torch to save). No GPU.

Per layer L (over the concept write+carry band), at the query codeword:
  v_bomb[L]        : unit diff-of-means direction (doublespeak - benign) -- "more BOMB-like"
  gap[L]           : natural dose unit = |mean_db - mean_benign| projection (§8.2). To
                     ABLATE Bombness in a DS prompt, subtract up to 1.0*gap along v_bomb;
                     to ADD, add alpha*gap.
  v_bomb_perp_ref  : v_bomb with the refusal_L18 component removed (orthogonalized, §8.1)
  cos_vs_refusal   : geometry check (should be small)
  v_random[L]      : a norm-matched random direction (seeded), the specificity control

Saved as a .pt: {layers:[...], v_bomb:{L:tensor}, gap:{L:float}, v_bomb_perp_ref:{L:tensor},
v_random:{L:tensor}, cos_vs_refusal:{L:float}, meta:{...}}. The harness loads this and
applies stacked LayerPatch(project_out / add) at the codeword position over the band.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))
from src.probes import contextual_identity_probe as cip  # noqa: E402
from src.probes.smoke_fit import load_run, POSITIONS      # noqa: E402

WRITE_CARRY_BAND = list(range(8, 22))  # concept write L8-11 + carry L14-21 (plan §1.1)


def orthogonalize(v, ref):
    """Remove the ref component from v; return the (renormalized) perpendicular part."""
    ref_u = ref / np.linalg.norm(ref)
    v_perp = v - (v @ ref_u) * ref_u
    n = np.linalg.norm(v_perp)
    return v_perp / n if n > 0 else v_perp


def build(acts, items, refusal_vec, band=WRITE_CARRY_BAND, seed=20260814):
    cw = POSITIONS.index("codeword_last")
    lab = np.array([it.get("label") in (0, 1) for it in items])
    idx = np.where(lab)[0]
    y = np.array([items[i]["label"] for i in idx])
    if len(np.unique(y)) < 2:
        raise ValueError("need both classes")
    rng = np.random.default_rng(seed)
    out = {"layers": list(band), "v_bomb": {}, "gap": {}, "v_bomb_perp_ref": {},
           "v_random": {}, "cos_vs_refusal": {}, "gap_over_sd": {}}
    ref = np.asarray(refusal_vec, float).ravel()
    for L in band:
        X = acts[idx, L, cw, :].astype(np.float64)
        vraw = X[y == 1].mean(0) - X[y == 0].mean(0)     # db - benign
        gap = float(np.linalg.norm(vraw))                # natural dose unit
        v = vraw / gap
        proj = X @ v
        out["v_bomb"][L] = v.astype(np.float32)
        out["gap"][L] = gap
        out["gap_over_sd"][L] = float(gap / proj.std())
        out["cos_vs_refusal"][L] = round(cip.cosine(v, ref), 4)
        out["v_bomb_perp_ref"][L] = orthogonalize(v, ref).astype(np.float32)
        r = rng.standard_normal(v.shape[0]); r /= np.linalg.norm(r)
        out["v_random"][L] = r.astype(np.float32)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--refusal", default="outputs/stage_gcg_full/refusal_direction_llama_L18.pt")
    ap.add_argument("--out", required=True, help="output .pt path")
    ap.add_argument("--band", default=None, help="comma layers, default write+carry 8..21")
    args = ap.parse_args()
    import torch
    acts, items = load_run(args.run)
    rd = torch.load(args.refusal, map_location="cpu")
    rvec = np.asarray(rd["direction"] if isinstance(rd, dict) and "direction" in rd else rd, float).ravel()
    band = [int(x) for x in args.band.split(",")] if args.band else WRITE_CARRY_BAND
    d = build(acts, items, rvec, band=band)
    payload = {
        "layers": d["layers"],
        "v_bomb": {L: torch.tensor(v) for L, v in d["v_bomb"].items()},
        "v_bomb_perp_ref": {L: torch.tensor(v) for L, v in d["v_bomb_perp_ref"].items()},
        "v_random": {L: torch.tensor(v) for L, v in d["v_random"].items()},
        "gap": d["gap"], "gap_over_sd": d["gap_over_sd"], "cos_vs_refusal": d["cos_vs_refusal"],
        "meta": {"run": args.run, "refusal": args.refusal, "position": "codeword_last",
                 "component": "resid_post==hidden_states[L+1]", "seed": 20260814},
    }
    torch.save(payload, args.out)
    print(f"saved {args.out}: {len(d['layers'])} layers")
    print("gap per layer:", {L: round(g, 2) for L, g in d["gap"].items()})
    print("cos_vs_refusal:", d["cos_vs_refusal"])


if __name__ == "__main__":
    main()
