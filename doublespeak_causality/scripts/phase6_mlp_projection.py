#!/usr/bin/env python3
"""Phase 6 (representational): per-layer MLP-output write onto concept / signature / refusal directions.

Uses the already-extracted reps (means.npz: per-condition mlp_out at codeword_last, [32,4096]) and the
per-layer directions (directions.npz d_Direct/d_DS at mlp_out; refusal_alllayers). No new GPU.

For each layer L, the MLP write update = mean(DOUBLESPEAK mlp_out)[L] - mean(NEUTRAL_CODEWORD mlp_out)[L].
Projected (cosine) onto:
  concept  = d_Direct at mlp_out (mean DIRECT - mean NEUTRAL, MLP-output space)
  signature= d_DS     at mlp_out (mean DOUBLESPEAK - mean NEUTRAL)   [NOT the concept axis]
  refusal  = refusal_direction[L] (last-token harmful/harmless)
This localizes WHERE the MLP writes in the concept direction (representational; causal MLP patching is
the follow-up). Descriptive until an exact MLP intervention moves a downstream metric.

Usage: python scripts/phase6_mlp_projection.py --reps-dir <pair_reps> --concept-dir <pair_directions> --cohort curated
"""
from __future__ import annotations
import argparse, glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v * 0


def cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    return float(np.dot(a, b) / (na * nb)) if na > 1e-9 and nb > 1e-9 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps-dir", required=True)
    ap.add_argument("--concept-dir", required=True)
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--out-dir", default=os.path.join(DC, "outputs", "phase6_mlp_projection"))
    args = ap.parse_args()

    m = np.load(os.path.join(args.reps_dir, "means.npz"))
    d = np.load(os.path.join(args.concept_dir, "directions.npz"))
    sp = args.split
    ds = m[f"DOUBLESPEAK|{sp}|mlp_out|codeword_last"].astype(np.float64)     # [L,H]
    neu = m[f"NEUTRAL_CODEWORD|{sp}|mlp_out|codeword_last"].astype(np.float64)
    update = ds - neu                                                        # DS MLP write vs neutral
    concept = d[f"d_Direct|{sp}|mlp_out|codeword_last"].astype(np.float64)   # [L,H]
    signature = d[f"d_DS|{sp}|mlp_out|codeword_last"].astype(np.float64)
    import torch
    refusal = None
    rfiles = sorted(glob.glob(os.path.join(args.refusal_dir, "refusal_direction_llama_L*.pt")))
    if rfiles:
        refusal = np.stack([torch.load(f, map_location="cpu").float().numpy()
                            for f in sorted(rfiles, key=lambda x: int(x.split("_L")[1].split(".pt")[0]))])

    L = update.shape[0]
    per = []
    for l in range(L):
        row = {"layer": l,
               "update_norm": round(float(np.linalg.norm(update[l])), 3),
               "cos_concept": round(cos(update[l], concept[l]), 4),
               "cos_signature": round(cos(update[l], signature[l]), 4),
               "proj_concept": round(float(np.dot(update[l], unit(concept[l]))), 3)}
        if refusal is not None and l < len(refusal):
            row["cos_refusal"] = round(cos(update[l], refusal[l]), 4)
        per.append(row)

    os.makedirs(args.out_dir, exist_ok=True)
    top = sorted(per, key=lambda r: -r["proj_concept"])[:6]
    band = lambda a, b: round(sum(r["proj_concept"] for r in per if a <= r["layer"] <= b), 2)
    summary = {"cohort": args.cohort, "split": sp, "n_layers": L,
               "top_concept_write_layers": [(r["layer"], r["proj_concept"], r["cos_concept"]) for r in top],
               "proj_concept_band": {"early_0_9": band(0, 9), "mid_10_19": band(10, 19), "late_20_31": band(20, 31)},
               "per_layer": per}
    json.dump(summary, open(os.path.join(args.out_dir, f"{args.cohort}.json"), "w"), indent=1)
    print(f"[mlp-proj {args.cohort}] top concept-write layers (layer, proj, cos):")
    for l, p, c in summary["top_concept_write_layers"]:
        print(f"    L{l}: proj={p} cos_concept={c}")
    print(f"  band proj_concept: {summary['proj_concept_band']}")


if __name__ == "__main__":
    main()
