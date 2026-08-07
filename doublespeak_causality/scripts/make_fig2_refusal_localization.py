#!/usr/bin/env python
"""
Figure F2 -- refusal-suppression localization with behavior-confirmed nodes.

Panel A (representational, Gate A):
  source: outputs/refsuploc_clearharm_20260807_163312_732161/analysis_refsuploc.json
  heatmap of direct-donor restoration frac (frac_ratio_of_means) over
  component x layer (train split); Gate-A hits overlaid; L0-12 greyed; L15-18 band.

Panel B (behavioral, Gate B):
  source: outputs/refdecpatch_clearharm_20260807_194210_732388/summary.json
  grouped bars of delta-ASR vs ds_base for the band arms {direct L15/16/17,
  rand L17, self L17}, per split (train/dev/test), McNemar p stars.

All plotted numbers are read from the JSON at runtime (nothing hardcoded).
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.colors import LinearSegmentedColormap

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A_JSON = os.path.join(ROOT, "outputs/refsuploc_clearharm_20260807_163312_732161/analysis_refsuploc.json")
B_JSON = os.path.join(ROOT, "outputs/refdecpatch_clearharm_20260807_194210_732388/summary.json")
OUT = os.path.join(ROOT, "figures/fig2_refusal_localization.png")

# ---- palette (dataviz default) ----
C_TRAIN, C_DEV, C_TEST = "#2a78d6", "#eb6834", "#1baf7a"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#f4f7fb", "#c7dbf0", "#7fb0e0", "#3987e5", "#173a6b"])

# ============================ Panel A data ============================
A = json.load(open(A_JSON))
anchor_layer = A["anchor_layer"]
frac_thr = A["frac_thr"]
tr = A["by_split"]["train"]
cells = tr["cells"]
COMPS = ["resid_pre", "attn_out", "mlp_out", "resid_post"]  # forward order within a layer
LAYERS = list(range(32))

fracA = np.full((len(COMPS), len(LAYERS)), np.nan)
holmA = np.full((len(COMPS), len(LAYERS)), np.nan)
for i, comp in enumerate(COMPS):
    for j, L in enumerate(LAYERS):
        c = cells.get(f"{comp}|direct|L{L}")
        if c is not None:
            fracA[i, j] = c["frac_ratio_of_means"]
            holmA[i, j] = c["holm_p_pooled"]

# Gate-A hit set (cell strings like "resid_pre|L24")
gate_a = set(h["cell"] for h in tr["gate_a_hits"])

# ============================ Panel B data ============================
B = json.load(open(B_JSON))
ARMS = ["ds_dpatch_direct_L15", "ds_dpatch_direct_L16", "ds_dpatch_direct_L17",
        "ds_dpatch_rand_L17", "ds_dpatch_self_L17"]
ARM_LBL = ["direct\nL15", "direct\nL16", "direct\nL17", "rand\nL17", "self\nL17"]
SPLITS = [("train", C_TRAIN), ("dev", C_DEV), ("test", C_TEST)]

# ============================ Figure ============================
fig = plt.figure(figsize=(15, 6.2), dpi=150)
gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.22,
                      left=0.055, right=0.985, top=0.80, bottom=0.13)

# ---------- Panel A ----------
axA = fig.add_subplot(gs[0, 0])
im = axA.imshow(fracA, aspect="auto", cmap=SEQ, vmin=0.0, vmax=1.0,
                origin="upper", interpolation="nearest")
axA.set_xticks(LAYERS)
axA.set_xticklabels([str(L) for L in LAYERS], fontsize=6.5)
axA.set_yticks(range(len(COMPS)))
axA.set_yticklabels(COMPS, fontsize=9)
axA.set_xlabel("layer", fontsize=9)
axA.set_title("A  Representational restoration (Gate A): direct-donor refusal-projection frac",
              fontsize=10.5, loc="left", pad=8)

# grey out L0-12 (no validated refusal axis)
axA.add_patch(Rectangle((-0.5, -0.5), 13, len(COMPS), facecolor="0.82",
                        edgecolor="none", alpha=0.55, zorder=3))
axA.text(6, -0.72, "L0-12: no validated refusal axis", fontsize=7.5,
         color="0.35", ha="center", va="bottom")

# annotate residual band L15-18
axA.add_patch(Rectangle((14.5, -0.5), 4, len(COMPS), fill=False,
                        edgecolor="#173a6b", lw=2.0, zorder=6))
axA.text(16.5, -0.72, "residual band L15-18", fontsize=8, color="#173a6b",
         ha="center", va="bottom", fontweight="bold")

# overlay Gate-A hits (frac>=thr, Holm-sig, > rand) as stars
for i, comp in enumerate(COMPS):
    for j, L in enumerate(LAYERS):
        if f"{comp}|L{L}" in gate_a:
            axA.scatter(j, i, marker="*", s=70, c="white",
                        edgecolors="black", linewidths=0.5, zorder=7)

# annotate numeric frac in the band -- only on attn_out/mlp_out rows
# (residual rows carry the * star; skip numbers there to avoid overlap)
for j in [15, 16, 17, 18]:
    for i, comp in enumerate(COMPS):
        if comp in ("attn_out", "mlp_out"):
            v = fracA[i, j]
            if not np.isnan(v):
                axA.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6.2,
                         color="0.15", zorder=8)

cbar = fig.colorbar(im, ax=axA, fraction=0.045, pad=0.015)
cbar.set_label("restoration frac\n(1 = anchor L%d)" % anchor_layer, fontsize=8)
cbar.ax.tick_params(labelsize=7)
axA.text(0.99, 0.03, "* = Gate-A hit (frac >= %.1f, Holm-sig, > rand control)" % frac_thr,
         transform=axA.transAxes, fontsize=7.5, color="0.2", ha="right", va="bottom",
         bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="0.7", alpha=0.85))

# ---------- Panel B ----------
axB = fig.add_subplot(gs[0, 1])
x = np.arange(len(ARMS))
w = 0.26
for k, (sp, col) in enumerate(SPLITS):
    vs = B["by_split"][sp]["vs_ds_base"]
    deltas = [vs[a]["delta_ASR"] for a in ARMS]
    ps = [vs[a]["mcnemar_p"] for a in ARMS]
    xk = x + (k - 1) * w
    bars = axB.bar(xk, deltas, w, color=col, label=f"{sp} (n={B['by_split'][sp]['n']})",
                   edgecolor="white", linewidth=0.6, zorder=3)
    for xi, d, p in zip(xk, deltas, ps):
        if p < 0.05:
            yoff = -0.012 if d < 0 else 0.006
            va = "top" if d < 0 else "bottom"
            axB.text(xi, d + yoff, "*", ha="center", va=va, fontsize=11,
                     color=col, fontweight="bold", zorder=4)

axB.axhline(0, color="0.2", lw=0.9, zorder=2)
axB.set_xticks(x)
axB.set_xticklabels(ARM_LBL, fontsize=8)
axB.set_ylabel(r"$\Delta$ASR  vs  ds_base", fontsize=9)
axB.set_title("B  Behavioral confirmation (Gate B): decode-patch %s"
              % B["component"], fontsize=10.5, loc="left", pad=8)
axB.legend(fontsize=7.5, loc="upper left", framealpha=0.9)
axB.text(1.02, -0.16, "negative = ASR reduced (refusal restored)   * McNemar p<0.05",
         transform=axB.transAxes, fontsize=7.5, color="0.25", ha="right", va="top")
axB.grid(axis="y", color="0.85", lw=0.6, zorder=0)
axB.set_axisbelow(True)

# ---------- global title / caption ----------
fig.suptitle("Refusal suppression is carried in the residual stream at L15-18: "
             "restoring it reinstates the refusal representation (A) and lowers ASR (B)",
             fontsize=12, y=0.975, x=0.055, ha="left", fontweight="bold")
fig.text(0.055, 0.915,
         "ClearHarm cohort, Qwen3-14B. A: residual (resid_pre/resid_post) restores the "
         "Doublespeak-suppressed refusal projection while attn_out/mlp_out barely do "
         "(residual carry, not sub-block write). B: patching resid_post at L15-17 "
         "significantly lowers attack success; rand raises it, self is inert.",
         fontsize=8.5, color="0.30", ha="left", va="top")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print("wrote", OUT)

# ---- console table of key values ----
print("\n== Panel A: direct-donor frac (train) ==")
for L in [16, 18]:
    for comp in COMPS:
        c = cells[f"{comp}|direct|L{L}"]
        print(f"  L{L:>2} {comp:<10} frac={c['frac_ratio_of_means']:+.4f}  holm_p={c['holm_p_pooled']:.2g}")
print("\n== Panel B: delta-ASR vs ds_base ==")
for sp, _ in SPLITS:
    vs = B["by_split"][sp]["vs_ds_base"]
    for a in ["ds_dpatch_direct_L15", "ds_dpatch_direct_L16", "ds_dpatch_direct_L17"]:
        print(f"  {sp:<5} {a:<24} dASR={vs[a]['delta_ASR']:+.4f}  p={vs[a]['mcnemar_p']:.4g}")
