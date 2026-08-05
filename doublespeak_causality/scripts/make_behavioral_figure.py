#!/usr/bin/env python3
"""Headline figure for the behavioral refusal-locus finding (paper). Reads the committed summary.json
files; no GPU. Panel A = the dissociation (concept levers leave harmful ASR flat, refusal levers move
it from ~0 to ~0.55); Panel B = refusal re-injection dose-response to zero. clearharm locked TEST split.

Usage: python scripts/make_behavioral_figure.py  (writes figures/behavioral_dissociation.png)
"""
import json, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
def load(pat):
    d = sorted(glob.glob(os.path.join(DC, "outputs", pat)))[-1]
    return json.load(open(os.path.join(d, "summary.json")))

# Okabe-Ito colorblind-safe
BLUE, ORANGE, GREY, INK = "#0072B2", "#D55E00", "#BBBBBB", "#222222"

rf = load("behav_refusal_clearharm_a1.0_*8038*")["by_split"]["test"]["ASR"]
carry = load("behav_carry_clearharm_*7831*")["by_split"]["test"]["ASR_carry_abl"]
write = load("behav_write_clearharm_L8*7908*")["by_split"]["test"]["ASR_write_abl"]
inj = load("behav_refinject_clearharm_L18_*710769*")["by_split"]["test"]["ASR"]

# Panel A: bars grouped concept-levers (inert, blue) vs refusal-levers (potent, orange)
labels = ["Direct\nharmful", "Doublespeak", "DS +\ncarry-ablate", "DS +\nwrite-ablate",
          "Direct +\nrefusal-ablate", "DS +\nrefusal-reinject"]
vals   = [rf["direct_base"], rf["ds_base"], carry, write, rf["direct_refabl"], inj["ds_refadd12"]]
cols   = [GREY, BLUE, BLUE, BLUE, ORANGE, ORANGE]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"width_ratios": [1.5, 1]})

bars = axA.bar(range(len(vals)), vals, color=cols, width=0.7, zorder=3)
for i, v in enumerate(vals):
    axA.text(i, v + 0.012, f"{v:.2f}", ha="center", va="bottom", fontsize=10, color=INK, zorder=4)
axA.set_xticks(range(len(labels))); axA.set_xticklabels(labels, fontsize=9)
axA.set_ylabel("Harmful ASR (StrongREJECT)", fontsize=11)
axA.set_ylim(0, 0.66)
axA.set_title("A · Concept levers leave ASR flat; refusal levers move it", fontsize=11.5, loc="left")
axA.axhline(rf["ds_base"], color=BLUE, ls=":", lw=1, alpha=0.6, zorder=1)
axA.spines[["top", "right"]].set_visible(False)
axA.grid(axis="y", color="#EEEEEE", zorder=0)
axA.legend(handles=[Patch(color=BLUE, label="concept lever → INERT"),
                    Patch(color=ORANGE, label="refusal lever → POTENT"),
                    Patch(color=GREY, label="unmodified baseline")],
           fontsize=8.5, frameon=False, loc="upper left")

# Panel B: refusal re-injection dose-response to zero
alphas = [0, 4, 8, 12]
dose = [inj["ds_base"], inj["ds_refadd4"], inj["ds_refadd8"], inj["ds_refadd12"]]
axB.plot(alphas, dose, "-o", color=ORANGE, lw=2.2, ms=7, zorder=3)
for a, v in zip(alphas, dose):
    axB.text(a, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9.5, color=INK)
axB.set_xlabel("refusal re-injection strength α (into Doublespeak)", fontsize=10)
axB.set_ylabel("Harmful ASR", fontsize=11)
axB.set_title("B · Restoring refusal kills the jailbreak (dose-dependent)", fontsize=11.5, loc="left")
axB.set_xticks(alphas); axB.set_ylim(-0.03, 0.45)
axB.spines[["top", "right"]].set_visible(False)
axB.grid(color="#EEEEEE", zorder=0)

fig.suptitle("Doublespeak is refusal suppression, not concept remapping  (Llama-3.1-8B, clearharm locked test)",
             fontsize=12.5, fontweight="bold", y=1.02)
fig.tight_layout()
outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "behavioral_dissociation.png")
fig.savefig(out, dpi=170, bbox_inches="tight")
print("wrote", out)
print("Panel A vals:", dict(zip([l.replace(chr(10), ' ') for l in labels], vals)))
print("Panel B dose:", dict(zip(alphas, dose)))
