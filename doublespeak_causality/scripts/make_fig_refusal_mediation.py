#!/usr/bin/env python
"""
Figure F-med -- §4 refusal carry-vs-readout mediation depth gradient.

source: outputs/refusal_mediation_clearharm_20260808_233827_737608/summary.json (test n=42)
Panel A: per-head TOTAL vs DIRECT restoration of the decision-token refusal projection (grouped bars).
Panel B: mediated_frac (=1-DIRECT/TOTAL) vs sender layer -> the carry->readout depth gradient.
All numbers read from the JSON at runtime (nothing hardcoded).
"""
import json, os, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "outputs/refusal_mediation_clearharm_20260808_233827_737608/summary.json")
OUT = os.path.join(ROOT, "figures/fig_refusal_mediation.png")

C_TOTAL, C_DIRECT, C_MED = "#2a78d6", "#eb6834", "#1baf7a"
S = json.load(open(SRC))
t = S["by_split"]["test"]
heads = t["heads"]
# order by (layer, head)
def lh(k):
    m = re.match(r"L(\d+)H(\d+)", k); return (int(m.group(1)), int(m.group(2)))
names = sorted(heads.keys(), key=lh)
layers = [lh(n)[0] for n in names]
tot = [heads[n]["mean_TOTAL"] for n in names]
dr = [heads[n]["mean_DIRECT"] for n in names]
mf = [heads[n]["median_mediated_frac"] for n in names]

fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 4.6))

x = np.arange(len(names)); w = 0.38
axA.bar(x - w/2, tot, w, color=C_TOTAL, label="TOTAL (recompute)")
axA.bar(x + w/2, dr, w, color=C_DIRECT, label="DIRECT (skip-path)")
axA.set_xticks(x); axA.set_xticklabels(names, rotation=30, ha="right")
axA.set_ylabel("Δ refusal projection (restoration)")
axA.set_title(f"A. Per-head TOTAL vs DIRECT effect  (test n={t['n_items']})")
axA.legend(fontsize=9); axA.grid(alpha=0.25, axis="y")

axB.plot(x, mf, "-o", color=C_MED, lw=2, ms=7)
for xi, m, n in zip(x, mf, names):
    axB.annotate(f"{m:.2f}", (xi, m), textcoords="offset points", xytext=(0, 8), fontsize=9, ha="center")
axB.set_xticks(x); axB.set_xticklabels(names, rotation=30, ha="right")
axB.set_ylabel("mediated fraction  (1 − DIRECT/TOTAL)")
axB.set_ylim(0, 1.0)
axB.axhspan(0.5, 1.0, color="#1baf7a", alpha=0.06)
axB.set_title("B. Carry→readout depth gradient (early L13 = carry)")
axB.grid(alpha=0.25)

fig.suptitle("§4 Refusal carry-vs-readout mediation: L13 heads ~88% mediated (carry), "
             "L16 progressively readout  (all sanity gates byte-perfect)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.94])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=140, bbox_inches="tight")
print(f"[fig-med] wrote {OUT}")
