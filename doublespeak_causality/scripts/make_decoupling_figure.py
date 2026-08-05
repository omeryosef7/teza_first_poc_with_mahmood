#!/usr/bin/env python3
"""Third paper figure — the causal DECOUPLING (level 6, the mechanistic why). Ablating the L8-11
concept WRITE reduces the concept readout (positive control fires, Panel A) but leaves Doublespeak's
refusal-axis suppression UNMOVED (Panel B) — the demos' two effects run on separate pathways, which is
why the concept circuit is behaviorally epiphenomenal. Reads committed summary.json; no GPU.

Usage: python scripts/make_decoupling_figure.py  -> figures/causal_decoupling.png
"""
import json, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
def load(pat):
    d = sorted(glob.glob(os.path.join(DC, "outputs", pat)))[-1]
    return json.load(open(os.path.join(d, "summary.json")))

BLUE, LTBLUE, ORANGE, GREY, INK = "#0072B2", "#7FBFE0", "#D55E00", "#BBBBBB", "#222222"
cohorts = ["clearharm", "curated"]
S = {c: load(f"write_refusal_intx_{c}_*7118*")["by_split"]["test"] for c in cohorts}

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.6))
x = np.arange(len(cohorts)); w = 0.38

# Panel A — concept readout DROPS under write-ablation (control fired)
pc_ds  = [S[c]["pconcept_control"]["ds"] for c in cohorts]
pc_wab = [S[c]["pconcept_control"]["writeabl"] for c in cohorts]
axA.bar(x - w/2, pc_ds, w, color=BLUE, label="Doublespeak", zorder=3)
axA.bar(x + w/2, pc_wab, w, color=LTBLUE, label="+ concept-write ablated", zorder=3)
for i in range(len(cohorts)):
    axA.text(x[i]-w/2, pc_ds[i]+.012, f"{pc_ds[i]:.2f}", ha="center", fontsize=9, color=INK)
    axA.text(x[i]+w/2, pc_wab[i]+.012, f"{pc_wab[i]:.2f}", ha="center", fontsize=9, color=INK)
    axA.annotate("", xy=(x[i]+w/2, pc_wab[i]), xytext=(x[i]-w/2, pc_ds[i]),
                 arrowprops=dict(arrowstyle="->", color=INK, lw=1.1))
axA.set_xticks(x); axA.set_xticklabels(cohorts, fontsize=10)
axA.set_ylabel("concept readout  p(concept)", fontsize=10.5); axA.set_ylim(0, 1.0)
axA.set_title("A · Write-ablation DROPS the concept (control fires)", fontsize=11, loc="left")
axA.legend(fontsize=8.5, frameon=False, loc="lower left")
axA.spines[["top", "right"]].set_visible(False); axA.grid(axis="y", color="#EEEEEE")

# Panel B — refusal projection (hs31) UNCHANGED by write-ablation
di = [S[c]["per_layer"]["31"]["mean"]["direct"] for c in cohorts]
ds = [S[c]["per_layer"]["31"]["mean"]["ds_base"] for c in cohorts]
wa = [S[c]["per_layer"]["31"]["mean"]["ds_writeabl"] for c in cohorts]
ww = 0.26
axB.bar(x - ww, di, ww, color=GREY, label="Direct (refuses)", zorder=3)
axB.bar(x, ds, ww, color=ORANGE, label="Doublespeak", zorder=3)
axB.bar(x + ww, wa, ww, color=ORANGE, hatch="////", edgecolor="white", label="DS + concept-write ablated", zorder=3)
for i in range(len(cohorts)):
    for xoff, v in [(-ww, di[i]), (0, ds[i]), (ww, wa[i])]:
        axB.text(x[i]+xoff, v + (0.4 if v>=0 else -1.2), f"{v:.1f}", ha="center", fontsize=8.5, color=INK)
axB.axhline(0, color=INK, lw=0.8)
axB.set_xticks(x); axB.set_xticklabels(cohorts, fontsize=10)
axB.set_ylabel("refusal-axis projection (L30)", fontsize=10.5)
axB.set_title("B · ...but the refusal signal is UNMOVED (DS ≈ DS-ablated ≪ Direct)", fontsize=10.5, loc="left")
axB.legend(fontsize=8, frameon=False, loc="upper right")
axB.spines[["top", "right"]].set_visible(False); axB.grid(axis="y", color="#EEEEEE")

fig.suptitle("Concept-remap and refusal-suppression are causally INDEPENDENT pathways",
             fontsize=12.5, fontweight="bold", y=1.02)
fig.tight_layout()
outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "causal_decoupling.png")
fig.savefig(out, dpi=170, bbox_inches="tight")
print("wrote", out)
