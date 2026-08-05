#!/usr/bin/env python3
"""Item-level rep->behavior: does a Doublespeak prompt's refusal-axis projection predict whether it
jailbreaks? Joins REFPROJ (per-item DS refusal projection) with BEHAV-REFUSAL (per-item ds_base outcome)
by item id. Mann-Whitney U + point-biserial + AUC at decoder L21 (hs22). No GPU. Writes a box/strip figure.

Usage: python scripts/analyze_rep_predicts_behavior.py [--layer 22]
"""
import argparse, json, glob, os
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
ORANGE, BLUE, INK = "#D55E00", "#0072B2", "#222222"

def join(tag):
    rp = sorted(glob.glob(os.path.join(DC, "outputs", f"refproj_{tag}_*")))[-1]
    rf = sorted(glob.glob(os.path.join(DC, "outputs", f"behav_refusal_{tag}_a1.0_*")))[-1]
    proj = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(rp, "raw.jsonl")))}
    out  = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(rf, "raw.jsonl")))}
    ids = [i for i in proj if i in out]
    return proj, out, ids

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--layer", default="22"); args = ap.parse_args()
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4))
    res = {}
    for ax, tag in zip(axes, ["clearharm", "curated"]):
        proj, out, ids = join(tag)
        mal = np.array([out[i]["ds_base_label"] == "MALICIOUS" for i in ids])
        pr  = np.array([proj[i]["doublespeak"][args.layer] for i in ids])
        U, p = stats.mannwhitneyu(pr[mal], pr[~mal], alternative="less")
        r, rp = stats.pointbiserialr(mal.astype(float), pr)
        auc = 1 - U / (mal.sum() * (~mal).sum())          # P(malicious proj < non-malicious proj)
        res[tag] = dict(n=len(ids), mal=int(mal.sum()), auc=round(auc, 3), mw_p=float(p), r=round(r, 3))
        # strip + box
        for j, (grp, col, lab) in enumerate([(~mal, BLUE, "refused/benign"), (mal, ORANGE, "jailbreak")]):
            y = pr[grp]; xj = np.random.default_rng(0).normal(j, 0.06, len(y))
            ax.scatter(xj, y, color=col, s=22, alpha=0.7, zorder=3)
            ax.hlines(np.median(y), j - 0.2, j + 0.2, color=INK, lw=2, zorder=4)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["refused/\nbenign", "jailbreak"], fontsize=9)
        ax.set_title(f"{tag}  (AUC={auc:.2f}, p={p:.1e})", fontsize=10.5, loc="left")
        ax.set_ylabel(f"DS refusal-axis projection (L21)" if tag == "clearharm" else "", fontsize=10)
        ax.axhline(0, color="#CCCCCC", lw=0.8); ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#EEEEEE")
    fig.suptitle("A Doublespeak prompt's refusal suppression predicts its jailbreak (clearharm; uniform on curated)",
                 fontsize=11.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
    out_png = os.path.join(outdir, "rep_predicts_behavior.png")
    fig.savefig(out_png, dpi=170, bbox_inches="tight")
    print("wrote", out_png); print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
