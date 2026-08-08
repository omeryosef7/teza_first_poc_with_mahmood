#!/usr/bin/env python
"""
Figure F7 -- causal defense: ASR reduction vs benign utility.

Headline: the mechanism-derived refusal-restoration defense IS effective at
reducing attack ASR, but it is fundamentally NON-SELECTIVE -- it over-refuses
benign prompts at every dose, and intent-gating on the refusal axis cannot
separate attacks from benign requests.

Panel A (dose-response tradeoff at L18, train split):
  source: outputs/defense_util_clearharm_20260808_025303_732750/summary.json
    by_split.train.by_layer["L18_d{0.25,0.5,0.75,1.0}"].{delta_ASR, benign_over_refusal}
  plus fixed-dose L16/L18/L20 points:
  source: outputs/defense_util_clearharm_20260808_010203_732688/summary.json
    by_split.train.by_layer["16"/"18"/"20"].{delta_ASR, benign_over_refusal}
  x = benign over-refusal, y = attack |ASR reduction|. Both rise together at a
  ~constant ratio -> no selectivity.

Panel B (gating separability, train split):
  source: outputs/defense_gated_clearharm_20260808_053211_732795/summary.json
    proj_stats.{proj_ds_mean, proj_benign_mean, proj_direct_mean}, threshold,
    ds_fire_rate, benign_fire_rate.
  Gate on the refusal axis fires on benign >= attacks -> cannot separate.

All plotted numbers are read from the JSON at runtime (nothing hardcoded).
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXED_JSON = os.path.join(ROOT, "outputs/defense_util_clearharm_20260808_010203_732688/summary.json")
DOSE_JSON  = os.path.join(ROOT, "outputs/defense_util_clearharm_20260808_025303_732750/summary.json")
GATED_JSON = os.path.join(ROOT, "outputs/defense_gated_clearharm_20260808_053211_732795/summary.json")
OUT = os.path.join(ROOT, "figures/fig7_defense_tradeoff.png")

# ---- palette ----
C_ATTACK = "#2a78d6"   # dose-response points
C_FIXED  = "#eb6834"   # fixed-dose layer points
C_DS     = "#d1495b"   # attack / ds
C_BENIGN = "#2a78d6"   # benign
C_DIRECT = "#5a5a5a"   # direct request / threshold
C_REF    = "#999999"

# ============================ Panel A data ============================
dose = json.load(open(DOSE_JSON))
tr = dose["by_split"]["train"]["by_layer"]
scales = dose["dose_scales"]
dose_x, dose_y, dose_lab = [], [], []
for s in scales:
    key = "L18_d%s" % ("1.0" if s == 1.0 else str(s))
    d = tr[key]
    dose_x.append(d["benign_over_refusal"])
    dose_y.append(abs(d["delta_ASR"]))
    dose_lab.append("d=%.2f" % s)

fixed = json.load(open(FIXED_JSON))
ftr = fixed["by_split"]["train"]["by_layer"]
fx_x, fx_y, fx_lab = [], [], []
for L in ["16", "18", "20"]:
    d = ftr[L]
    fx_x.append(d["benign_over_refusal"])
    fx_y.append(abs(d["delta_ASR"]))
    fx_lab.append("L%s (full)" % L)

# ============================ Panel B data ============================
gated = json.load(open(GATED_JSON))
gtr = gated["by_split"]["train"]
T = gated["threshold"]
ps = gtr["proj_stats"]
proj_benign = ps["proj_benign_mean"]
proj_ds = ps["proj_ds_mean"]
proj_direct = ps["proj_direct_mean"]
ds_fire = gtr["ds_fire_rate"]
benign_fire = gtr["benign_fire_rate"]

# ============================ Figure ============================
fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 5.6))

# ---- Panel A: dose-response tradeoff ----
lim = max(max(dose_x), max(dose_y), max(fx_x), max(fx_y)) * 1.15
axA.plot([0, lim], [0, lim], ls="--", color=C_REF, lw=1.2, zorder=1,
         label="selectivity ref (y=x)")

# dose sweep line + points
axA.plot(dose_x, dose_y, "-", color=C_ATTACK, lw=1.6, zorder=2)
axA.scatter(dose_x, dose_y, s=90, color=C_ATTACK, zorder=3,
            label="L18 dose sweep")
for x, y, lab in zip(dose_x, dose_y, dose_lab):
    axA.annotate(lab, (x, y), textcoords="offset points", xytext=(9, -12),
                 fontsize=8.5, color=C_ATTACK)

# fixed-dose layer points
axA.scatter(fx_x, fx_y, s=110, marker="D", color=C_FIXED, zorder=3,
            edgecolor="white", linewidth=0.8, label="fixed dose (L16/18/20)")
for x, y, lab in zip(fx_x, fx_y, fx_lab):
    axA.annotate(lab, (x, y), textcoords="offset points", xytext=(7, 5),
                 fontsize=8.5, color=C_FIXED)

# ratio annotation: mean(|dASR|/over_refusal) across dose points
ratios = [y / x for x, y in zip(dose_x, dose_y) if x > 0]
axA.text(0.03, 0.97,
         "dose points track a ~const ratio\n|ASR reduction| / over-refusal $\\approx$ %.2f\n(defense buys ASR drop at a fixed benign cost)" % np.mean(ratios),
         transform=axA.transAxes, va="top", ha="left", fontsize=9,
         bbox=dict(boxstyle="round,pad=0.4", fc="#f4f7fb", ec="#c7dbf0"))

axA.set_xlim(0, lim)
axA.set_ylim(0, lim)
axA.set_xlabel("benign over-refusal (added false refusals)", fontsize=10.5)
axA.set_ylabel("attack ASR reduction  |$\\Delta$ASR|", fontsize=10.5)
axA.set_title("(A) Dose-response tradeoff at L18 (train)\nboth rise together -- non-selective",
              fontsize=11, fontweight="bold")
axA.legend(loc="lower right", fontsize=8.5, framealpha=0.9)
axA.grid(True, alpha=0.25)

# ---- Panel B: gating separability ----
labels = ["benign", "attack (ds)", "direct request"]
vals = [proj_benign, proj_ds, proj_direct]
cols = [C_BENIGN, C_DS, C_DIRECT]
xpos = np.arange(len(labels))
bars = axB.bar(xpos, vals, color=cols, width=0.6, zorder=2)
for b, v in zip(bars, vals):
    axB.text(b.get_x() + b.get_width() / 2, v + 0.08, "%.2f" % v,
             ha="center", va="bottom", fontsize=9.5)

# threshold line
axB.axhline(T, ls="--", color=C_DIRECT, lw=1.4, zorder=3)
axB.text(1.0, T - 0.12, "gate threshold T = %.2f" % T,
         ha="center", va="top", fontsize=9, color=C_DIRECT)

axB.set_xticks(xpos)
axB.set_xticklabels(labels, fontsize=10)
axB.set_ylabel("mean projection on refusal axis", fontsize=10.5)
axB.set_ylim(0, max(vals) * 1.22)
axB.set_title("(B) Gating separability (train)\ngate fires on benign $\\geq$ attacks",
              fontsize=11, fontweight="bold")
axB.grid(True, axis="y", alpha=0.25)

# fire-rate annotation
axB.text(0.03, 0.97,
         "fire rate  (proj > T-based gate):\n  benign  = %.1f%%\n  attack (ds) = %.1f%%\n$\\Rightarrow$ gate cannot separate intent"
         % (benign_fire * 100, ds_fire * 100),
         transform=axB.transAxes, va="top", ha="left", fontsize=9,
         bbox=dict(boxstyle="round,pad=0.4", fc="#fdecec", ec="#f2c3c3"))

# ---- headline caption ----
fig.suptitle("F7  Causal defense: restoring refusal defends but is non-selective",
             fontsize=13, fontweight="bold", y=0.99)
fig.text(0.5, 0.005,
         "Restoring the refusal direction reduces attack ASR but over-refuses benign at every dose (A) and under intent-gating (B) "
         "-> no selective mechanism-derived defense.  (ClearHarm, train split, L18)",
         ha="center", va="bottom", fontsize=9.5, style="italic")

fig.tight_layout(rect=[0, 0.035, 1, 0.955])
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print("wrote", OUT)
print("Panel A dose points (over_refusal, |dASR|):",
      list(zip([round(x, 4) for x in dose_x], [round(y, 4) for y in dose_y])))
print("Panel A fixed points (over_refusal, |dASR|):",
      list(zip([round(x, 4) for x in fx_x], [round(y, 4) for y in fx_y])))
print("Panel B proj means benign/ds/direct:", proj_benign, proj_ds, proj_direct, "T=", T)
print("Panel B fire rates ds/benign:", ds_fire, benign_fire)
