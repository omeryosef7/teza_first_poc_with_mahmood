#!/usr/bin/env python3
"""Phase-2.2: unify the three SEPARATE per-layer direction families into one artifact + report.

Keeps concept_direction[L], refusal_direction[L], doublespeak_signature[L] as DISTINCT objects
(the plan forbids merging concept+refusal). Emits, per cohort:
  outputs/unified_directions/<cohort>.npz   concept[32,H], signature[32,H], refusal[32,H]
  outputs/unified_directions/<cohort>.json   per-layer norms + cross-direction cosines + refusal sep

Inputs:
  --concept-dir  pair_directions_* dir (has directions.npz with d_Direct|<split>|<comp>|<pos>, d_DS|...)
  --refusal-dir  refusal_alllayers dir (refusal_direction_llama_L{0..31}.pt + .json separation)
  --split dev|heldout   which cross-fit split's concept/signature to use (default dev = train-derived)
  --component resid_post  --position codeword_last

cos(concept, refusal) and cos(signature, refusal) answer: is the concept mechanism a SEPARATE axis
from refusal (plan §2)? Low cosines => separable levers.

Usage:
  python scripts/build_unified_directions.py \
    --concept-dir outputs/pair_directions_<clearharm> --refusal-dir outputs/refusal_alllayers \
    --cohort clearharm
"""
from __future__ import annotations
import argparse, glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)


def _cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return float("nan")
    return float(np.dot(a, b) / (na * nb))


def load_refusal(refusal_dir):
    import torch
    vecs, seps = {}, {}
    for pt in sorted(glob.glob(os.path.join(refusal_dir, "refusal_direction_llama_L*.pt"))):
        L = int(os.path.basename(pt).split("_L")[1].split(".pt")[0])
        vecs[L] = torch.load(pt, map_location="cpu").float().numpy()
        j = pt.replace(".pt", ".json")
        if os.path.exists(j):
            seps[L] = json.load(open(j)).get("separation")
    n = max(vecs) + 1
    R = np.stack([vecs[L] for L in range(n)], axis=0)
    sep = [seps.get(L) for L in range(n)]
    return R, sep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concept-dir", required=True)
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_alllayers"))
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--split", default="dev")
    ap.add_argument("--component", default="resid_post")
    ap.add_argument("--position", default="codeword_last")
    ap.add_argument("--out-dir", default=os.path.join(DC, "outputs", "unified_directions"))
    args = ap.parse_args()

    npz = np.load(os.path.join(args.concept_dir, "directions.npz"))
    ck = f"d_Direct|{args.split}|{args.component}|{args.position}"
    sk = f"d_DS|{args.split}|{args.component}|{args.position}"
    concept = np.asarray(npz[ck], dtype=np.float64)      # [L, H]
    signature = np.asarray(npz[sk], dtype=np.float64)
    refusal, refusal_sep = load_refusal(args.refusal_dir)  # [L, H], [L]
    L = min(concept.shape[0], refusal.shape[0])
    concept, signature, refusal = concept[:L], signature[:L], refusal[:L]

    per_layer = []
    for l in range(L):
        per_layer.append({
            "layer": l,
            "norm_concept": round(float(np.linalg.norm(concept[l])), 4),
            "norm_signature": round(float(np.linalg.norm(signature[l])), 4),
            "norm_refusal": round(float(np.linalg.norm(refusal[l])), 4),
            "refusal_separation": (round(refusal_sep[l], 4) if refusal_sep[l] is not None else None),
            "cos_concept_refusal": round(_cos(concept[l], refusal[l]), 4),
            "cos_signature_refusal": round(_cos(signature[l], refusal[l]), 4),
            "cos_concept_signature": round(_cos(concept[l], signature[l]), 4),
        })

    os.makedirs(args.out_dir, exist_ok=True)
    np.savez_compressed(os.path.join(args.out_dir, f"{args.cohort}.npz"),
                        concept=concept.astype(np.float32),
                        signature=signature.astype(np.float32),
                        refusal=refusal.astype(np.float32))
    report = {
        "cohort": args.cohort, "split": args.split,
        "component": args.component, "position": args.position,
        "concept_dir": os.path.abspath(args.concept_dir),
        "refusal_dir": os.path.abspath(args.refusal_dir),
        "n_layers": L,
        "note": "concept/refusal/signature kept SEPARATE (never merged). cos_* answer plan §2 separability.",
        "per_layer": per_layer,
        "summary": {
            "mean_cos_concept_refusal": round(float(np.nanmean([p["cos_concept_refusal"] for p in per_layer])), 4),
            "max_abs_cos_concept_refusal": round(float(np.nanmax([abs(p["cos_concept_refusal"]) for p in per_layer])), 4),
            "mean_cos_signature_refusal": round(float(np.nanmean([p["cos_signature_refusal"] for p in per_layer])), 4),
            "mean_cos_concept_signature": round(float(np.nanmean([p["cos_concept_signature"] for p in per_layer])), 4),
            "refusal_peak_layer": int(np.nanargmax([p["refusal_separation"] or 0 for p in per_layer])),
        },
    }
    with open(os.path.join(args.out_dir, f"{args.cohort}.json"), "w") as f:
        json.dump(report, f, indent=1)

    s = report["summary"]
    print(f"[unify {args.cohort}] L={L} @ {args.component}/{args.position} split={args.split}")
    print(f"  mean cos(concept,refusal)={s['mean_cos_concept_refusal']} "
          f"(max|.|={s['max_abs_cos_concept_refusal']}) -> "
          f"{'SEPARABLE' if s['max_abs_cos_concept_refusal'] < 0.5 else 'OVERLAP: check'}")
    print(f"  mean cos(signature,refusal)={s['mean_cos_signature_refusal']}  "
          f"mean cos(concept,signature)={s['mean_cos_concept_signature']}  "
          f"refusal peak L={s['refusal_peak_layer']}")


if __name__ == "__main__":
    main()
