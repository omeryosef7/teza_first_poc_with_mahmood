#!/usr/bin/env python3
"""Second paper figure — the depth-resolved refusal mechanism. Panel A: refusal-axis projection vs
depth for Direct/Doublespeak/neutral (Doublespeak sits at/below the benign level at every depth;
suppression onsets at the L8-11 write band and grows) — the representational signature. Panel B: the
calibrated depth-localization (restoring refusal rescues at mid-late layers, not early) — the refusal
DECISION is read mid-late. Reads committed summary.json; no GPU.

Usage: python scripts/make_refusal_depth_figure.py  -> figures/refusal_depth_mechanism.png
"""
import json, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
def load(pat):
    d = sorted(glob.glob(os.path.join(DC, "outputs", pat)))[-1]
    return json.load(open(os.path.join(d, "summary.json")))

BLUE, ORANGE, GREEN, GREY, INK = "#0072B2", "#D55E00", "#009E73", "#BBBBBB", "#222222"

# Panel A — refusal projection vs decoder layer (hs row = L+1); skip final layer (unembedding-proximity spike)
pl = load("refproj_clearharm_*7113*")["by_split"]["test"]["per_layer"]
hs_rows = [h for h in range(10, 32)]                       # decoder L9..L30 (readable band)
xs = [h - 1 for h in hs_rows]
direct = [pl[str(h)]["mean"]["direct"] for h in hs_rows]
ds     = [pl[str(h)]["mean"]["doublespeak"] for h in hs_rows]
neu    = [pl[str(h)]["mean"]["neutral"] for h in hs_rows]

# Panel B — calibrated rescue ΔASR by inject layer
bl = load("refinject_cal_clearharm_*7116*")["by_split"]["train"]["by_layer_vs_ds_base"]
Ls = [9, 16, 22, 28]
d_asr = [bl[str(L)]["delta_ASR"] for L in Ls]
pvals = [bl[str(L)]["mcnemar_p"] for L in Ls]
rand  = [bl[str(L)]["rand_delta_ASR"] for L in Ls]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.5, 4.6))

axA.plot(xs, direct, "-o", color=BLUE, lw=2, ms=4, label="Direct harmful (refuses)")
axA.plot(xs, ds, "-o", color=ORANGE, lw=2, ms=4, label="Doublespeak (jailbreak)")
axA.plot(xs, neu, "--", color=GREEN, lw=1.8, label="neutral / benign")
axA.axvspan(8, 11, color=GREY, alpha=0.25, zorder=0)
axA.text(9.5, max(direct) * 0.30, "L8–11\nwrite band", ha="center", va="center", fontsize=8, color=INK)
axA.set_xlabel("decoder layer", fontsize=11)
axA.set_ylabel("refusal-axis projection (decision token)", fontsize=10.5)
axA.set_title("A · Doublespeak suppresses refusal to the benign level, all depths", fontsize=11, loc="left")
axA.legend(fontsize=8.5, frameon=False, loc="upper left")
axA.spines[["top", "right"]].set_visible(False); axA.grid(color="#EEEEEE")

cols = [ORANGE if p < 0.05 else GREY for p in pvals]
axB.bar(range(len(Ls)), d_asr, color=cols, width=0.6, zorder=3, label="restore refusal")
axB.scatter(range(len(Ls)), rand, color=INK, marker="x", s=45, zorder=4, label="random dir (control)")
for i, (dv, p) in enumerate(zip(d_asr, pvals)):
    star = "*" if p < 0.05 else "ns"
    axB.text(i, dv - 0.018, f"{dv:+.2f}\n{star}", ha="center", va="top", fontsize=9, color=INK)
axB.axhline(0, color=INK, lw=0.8)
axB.set_xticks(range(len(Ls))); axB.set_xticklabels([f"L{L}" for L in Ls], fontsize=10)
axB.set_ylabel("ΔASR from restoring refusal at layer", fontsize=10.5)
axB.set_ylim(-0.33, 0.08)
axB.set_title("B · Rescue works MID-LATE, not early (calibrated)", fontsize=11, loc="left")
axB.legend(fontsize=8.5, frameon=False, loc="lower left")
axB.spines[["top", "right"]].set_visible(False); axB.grid(axis="y", color="#EEEEEE")

fig.suptitle("Doublespeak suppresses refusal from the write band, but the refusal DECISION is read mid-late",
             fontsize=12, fontweight="bold", y=1.02)
fig.tight_layout()
outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "refusal_depth_mechanism.png")
fig.savefig(out, dpi=170, bbox_inches="tight")
print("wrote", out)
print("Panel B ΔASR:", dict(zip(Ls, zip(d_asr, pvals))))
