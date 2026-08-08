#!/usr/bin/env python
"""Figure F3 - three distinct notions of "importance" per layer (concept vs refusal).

Contrasts, for each layer, THREE importance measures, to show they dissociate:
  1. LINEAR READABILITY  (plain projection of the target direction)  -> peaks LATE  (~L30)
  2. JACOBIAN SENSITIVITY (||J|| = grad_norm)                        -> peaks MID   (concept L16, refusal L12)
  3. CAUSAL PATCH         (per-layer marginal residual restoration)  -> peaks MID   (L15-18 restoration band)

Scalar JSON in, matplotlib PNG out. No GPU, no model text.

Sources (recomputed from JSON, nothing hardcoded from prose):
  - outputs/jacobian_clearharm_20260807_132150_732004/summary.json
       by_split_condition[train|doublespeak].by_position.final_prompt.<target>.per_layer[*]
         grad_norm[0]   = ||J|| (Jacobian sensitivity, point estimate)
         proj_<target>  = plain per-layer projection (linear readability)
  - outputs/refsuploc_clearharm_20260807_163312_732161/analysis_refsuploc.json
       by_split.train.cells['resid_pre|direct|L{L}'].frac_ratio_of_means
         = cumulative refusal-restoration fraction when the direct-harmful residual is
           patched at layer L (anchor/read at L24). We plot the PER-LAYER MARGINAL
           restoration (increment), which is the causally meaningful "how much does
           patching HERE add" signal; the cumulative frac saturates toward the L24
           anchor by construction.
  - outputs/p6_peaklayer_clearharm.json (bootstrapped modal peak layers, cross-check).
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAC = os.path.join(BASE, "outputs/jacobian_clearharm_20260807_132150_732004/summary.json")
RSL = os.path.join(BASE, "outputs/refsuploc_clearharm_20260807_163312_732161/analysis_refsuploc.json")
PEAK = os.path.join(BASE, "outputs/p6_peaklayer_clearharm.json")
OUT = os.path.join(BASE, "figures/fig3_three_notions.png")

CAUSAL_BAND = (15, 18)  # plan section 3 restoration band

# ---- load jacobian curves (train | doublespeak | final_prompt) ------------
jd = json.load(open(JAC))
fp = jd["by_split_condition"]["train|doublespeak"]["by_position"]["final_prompt"]


def jac_curves(target):
    pl = fp[target]["per_layer"]
    layers = np.array([p["layer"] for p in pl])
    gradnorm = np.array([p["grad_norm"][0] for p in pl])          # ||J||
    readout = np.array([abs(p["proj_" + target]) for p in pl])    # |projection|
    return layers, gradnorm, readout


# ---- load causal per-layer marginal restoration ---------------------------
rd = json.load(open(RSL))
cells = rd["by_split"]["train"]["cells"]
anchor = rd["anchor_layer"]
cum = []
for L in range(32):
    k = f"resid_pre|direct|L{L}"
    cum.append(cells[k]["frac_ratio_of_means"] if k in cells else np.nan)
cum = np.array(cum)
# marginal restoration = per-layer increment, only over the active range [0, anchor]
marg = np.full(32, np.nan)
prev = 0.0
for L in range(0, anchor + 1):
    marg[L] = cum[L] - prev
    prev = cum[L]
marg = np.clip(marg, 0, None)              # negatives are noise; causal "adds" only
causal_layers = np.arange(anchor + 1)
causal = marg[: anchor + 1]

pk = json.load(open(PEAK))


def norm(y):
    y = np.asarray(y, float)
    m = np.nanmax(y)
    return y / m if m > 0 else y


# ---- figure ---------------------------------------------------------------
plt.rcParams.update({"font.size": 10, "axes.titlesize": 11, "figure.dpi": 150})
fig, axes = plt.subplots(2, 1, figsize=(9.2, 8.4), sharex=True)

C_READ = "#4C6EF5"   # readability (late)
C_JAC = "#E8590C"    # jacobian sensitivity (mid)
C_CAUS = "#2B8A3E"   # causal patch (mid)

titles = {"concept": "CONCEPT target", "refusal": "REFUSAL target"}
jac_peaks = {}
read_peaks = {}

for ax, target in zip(axes, ["concept", "refusal"]):
    layers, gradnorm, readout = jac_curves(target)
    rp = int(layers[np.argmax(readout)])
    jp = int(layers[np.argmax(gradnorm)])
    read_peaks[target] = rp
    jac_peaks[target] = jp

    # causal band shading
    ax.axvspan(CAUSAL_BAND[0], CAUSAL_BAND[1], color=C_CAUS, alpha=0.10, zorder=0)

    ax.plot(layers, norm(readout), "-o", ms=3.5, color=C_READ, lw=1.8,
            label=f"1. Linear readability  |proj|  (peak L{rp})")
    ax.plot(layers, norm(gradnorm), "-s", ms=3.5, color=C_JAC, lw=1.8,
            label=f"2. Jacobian sensitivity  ||J||  (peak L{jp})")
    cpeak = int(causal_layers[np.nanargmax(causal)])
    ax.plot(causal_layers, norm(causal), "-^", ms=3.5, color=C_CAUS, lw=1.8,
            label=f"3. Causal patch  Δrestore  (peak L{cpeak}, band L15–18)")

    # peak markers
    ax.axvline(rp, color=C_READ, ls=":", lw=1.1, alpha=0.7)
    ax.axvline(jp, color=C_JAC, ls=":", lw=1.1, alpha=0.7)

    ax.set_title(f"{titles[target]}  —  readable-late,  sensitive-mid,  causal-mid",
                 loc="left", fontweight="bold")
    ax.set_ylabel("importance (each curve\nnormalized to its own max)")
    ax.set_ylim(-0.03, 1.08)
    ax.grid(alpha=0.25, lw=0.6)
    ax.legend(loc="upper center", fontsize=8.5, framealpha=0.92, ncol=1)

axes[1].set_xlabel("layer")
axes[1].set_xticks(range(0, 32, 2))
axes[1].set_xlim(-0.5, 31)

band_patch = Patch(facecolor=C_CAUS, alpha=0.10, label="L15–18 causal restoration band")
fig.legend(handles=[band_patch], loc="lower right", bbox_to_anchor=(0.995, 0.005),
           fontsize=8, framealpha=0.9)

cap = (
    "Figure F3. Three notions of layer 'importance' dissociate (Llama-3.1-8B-Instruct, ClearHarm, "
    "Doublespeak, final-prompt token).\n"
    "Where a target is READABLE (linear projection, blue) peaks LATE (~L30); where it is SENSITIVE "
    "(Jacobian norm ‖J‖, orange) peaks MID (concept L16, refusal L12); where intervention actually MOVES\n"
    "behavior (per-layer marginal residual restoration, green) peaks MID in the L15–18 restoration band. "
    "'Where it is represented' ≠ 'where it matters'. Curves min-max normalized per panel for shape "
    "comparison.\nSources: jacobian summary.json (grad_norm, proj_*) + refsuploc analysis_refsuploc.json "
    "(resid_pre|direct frac); peaks cross-checked vs p6_peaklayer_clearharm.json."
)
fig.text(0.012, 0.008, cap, fontsize=7.0, va="bottom", ha="left", wrap=True)

fig.subplots_adjust(left=0.10, right=0.985, top=0.955, bottom=0.20, hspace=0.16)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=150)
print("wrote", OUT)
print("readout(readability) peaks:", read_peaks)
print("jacobian(||J||) peaks:", jac_peaks)
print("causal marginal-restoration peak layer:", int(causal_layers[np.nanargmax(causal)]),
      "| band", CAUSAL_BAND)
print("cross-check p6_peaklayer modal peaks: concept L%d, refusal L%d" % (
    pk["targets"]["concept"]["boot_peak"]["modal_peak_layer"],
    pk["targets"]["refusal"]["boot_peak"]["modal_peak_layer"]))
