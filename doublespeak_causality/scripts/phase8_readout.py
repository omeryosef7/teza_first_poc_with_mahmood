#!/usr/bin/env python3
"""Phase 8 (readout / concept emergence across layers): per-layer LINEAR readability of the
harmful concept in the residual stream, and whether it tracks the causal circuit (L9 MLP write,
L14–21 carry). CPU-only — reuses the extracted Llama reps + unified concept direction.

Per layer L, at the readout position (final prompt token), the linear concept readout is
   emergence[L] = (mean(DOUBLESPEAK resid_post)[L] − mean(NEUTRAL resid_post)[L]) · unit(concept_dir[L])
i.e. how far the Doublespeak residual has moved along the per-layer concept axis vs neutral.
DIRECT_CONCEPT (explicit concept present) is the reference upper bound. Descriptive: a linear
lens is a readout, not a cause — but its emergence layer is compared to the causal write/carry loci.

Usage: python scripts/phase8_readout.py --reps-dir <llama pair_reps> --cohort curated
"""
from __future__ import annotations
import argparse, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v * 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps-dir", required=True)
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--dirs", default=os.path.join(DC, "outputs", "unified_directions"))
    ap.add_argument("--pos", default="final_prompt")
    ap.add_argument("--out-dir", default=os.path.join(DC, "outputs", "phase8_readout"))
    args = ap.parse_args()

    m = np.load(os.path.join(args.reps_dir, "means.npz"))
    d = np.load(os.path.join(args.dirs, f"{args.cohort}.npz"))
    concept = d["concept"].astype(np.float64)          # [L, H]
    refusal = d["refusal"].astype(np.float64)
    L = concept.shape[0]

    def proj(cond, split):
        key = f"{cond}|{split}|resid_post|{args.pos}"
        neu = m[f"NEUTRAL_CODEWORD|{split}|resid_post|{args.pos}"].astype(np.float64)
        x = m[key].astype(np.float64)
        return np.array([float(np.dot(x[l] - neu[l], unit(concept[l]))) for l in range(L)])

    out = {"cohort": args.cohort, "pos": args.pos, "n_layers": L, "by_split": {}}
    splits = sorted({k.split("|")[1] for k in m.keys() if "|" in k and not k.startswith("__")})
    for split in splits:
        try:
            ds = proj("DOUBLESPEAK", split)
            direct = proj("DIRECT_CONCEPT", split)
        except KeyError:
            continue
        # emergence layer = first L where DS reaches 50% of its own max (cumulative onset)
        mx = ds.max()
        onset = int(np.argmax(ds >= 0.5 * mx)) if mx > 0 else None
        peak = int(np.argmax(ds))
        # correlation of the DS emergence curve with a mid-band causal template (peak L9 write +
        # L14-21 carry): report the raw curve and the layer of peak/onset; interpretation in report.
        out["by_split"][split] = {
            "ds_proj_concept": [round(float(x), 3) for x in ds],
            "direct_proj_concept": [round(float(x), 3) for x in direct],
            "onset_layer_50pct": onset, "peak_layer": peak,
            "ds_proj_at_L9": round(float(ds[9]), 3) if L > 9 else None,
            "ds_proj_at_L14": round(float(ds[14]), 3) if L > 14 else None,
            "ds_proj_at_L21": round(float(ds[21]), 3) if L > 21 else None,
            "frac_of_max_by_L9": round(float(ds[9] / mx), 3) if L > 9 and mx > 0 else None,
            "frac_of_max_by_L14": round(float(ds[14] / mx), 3) if L > 14 and mx > 0 else None,
        }
    os.makedirs(args.out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(args.out_dir, f"{args.cohort}.json"), "w"), indent=1)
    print(f"[readout {args.cohort}] pos={args.pos}")
    for split, s in out["by_split"].items():
        print(f"  [{split}] onset(50%)=L{s['onset_layer_50pct']} peak=L{s['peak_layer']} "
              f"proj@L9={s['ds_proj_at_L9']}(={s['frac_of_max_by_L9']}x max) "
              f"@L14={s['ds_proj_at_L14']}(={s['frac_of_max_by_L14']}x) @L21={s['ds_proj_at_L21']}")


if __name__ == "__main__":
    main()
