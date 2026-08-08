#!/usr/bin/env python
"""
Figure F5 -- demonstration-count dose response (§6).

source: outputs/dose_response_clearharm_20260808_124748_735299/summary.json
Three panels vs n_demo in {0,1,2,4,6,8,10,12}, train+test overlaid, bootstrap CI bands:
  A) decision-token refusal projection @L18  -> STEP DOWN at n_demo=1, then flat
  B) forced-choice p_concept                 -> flat (demo-invariant)
  C) StrongREJECT ASR                        -> weak/noisy, no monotone trend
All numbers read from the JSON at runtime (nothing hardcoded).
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "outputs/dose_response_clearharm_20260808_124748_735299/summary.json")
OUT = os.path.join(ROOT, "figures/fig5_dose_response.png")

C_TRAIN, C_TEST = "#2a78d6", "#1baf7a"
S = json.load(open(SRC))
ns = S["n_demos"]
anchor = S.get("readout_anchor", 18)

def series(split, key):
    """returns x, mean, lo, hi arrays for a mean_curves key over n_demos."""
    mc = S["by_split"][split]["mean_curves"][key]
    x, m, lo, hi = [], [], [], []
    for n in ns:
        v = mc.get(str(n))
        if v is None: continue
        x.append(n); m.append(v[0]); lo.append(v[1]); hi.append(v[2])
    return np.array(x), np.array(m), np.array(lo), np.array(hi)

panels = [
    ("refusal_anchor", f"decision-token refusal projection  (L{anchor})", "refusal axis projection"),
    ("p_concept", "forced-choice  p_concept", "p(concept)"),
    ("asr", "StrongREJECT ASR", "ASR"),
]
fig, axes = plt.subplots(1, 3, figsize=(15, 4.4))
for ax, (key, title, ylab) in zip(axes, panels):
    for split, col in (("train", C_TRAIN), ("test", C_TEST)):
        if split not in S["by_split"]: continue
        x, m, lo, hi = series(split, key)
        if len(x) == 0: continue
        n_items = S["by_split"][split]["n_items"]
        ax.plot(x, m, "-o", color=col, lw=2, ms=5, label=f"{split} (n={n_items})")
        ax.fill_between(x, lo, hi, color=col, alpha=0.15)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("n_demonstrations"); ax.set_ylabel(ylab)
    ax.axvline(1, color="#888", ls="--", lw=1, alpha=0.7)
    ax.grid(alpha=0.25); ax.set_xticks(ns)
axes[0].legend(fontsize=9, loc="best")
axes[0].annotate("step at n=1", xy=(1, series("train", "refusal_anchor")[1][1]),
                 xytext=(4, 3.6), fontsize=9, color="#444",
                 arrowprops=dict(arrowstyle="->", color="#888"))
fig.suptitle("§6 Demonstration-count dose response: refusal suppression is a STEP at n=1; "
             "concept readout flat; ASR weakly coupled  (v3 clearharm)", fontsize=12)
fig.tight_layout(rect=[0, 0, 1, 0.95])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=140, bbox_inches="tight")
print(f"[fig5] wrote {OUT}")
