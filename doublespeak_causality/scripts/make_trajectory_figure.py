#!/usr/bin/env python3
"""Figure: the refusal outcome is decided at the DECISION POINT, not re-engaged mid-generation. Refusal-axis
projection (L30) across generated tokens for Direct / Doublespeak-that-complies / Doublespeak-that-refuses
(clearharm test). The refused and complied DS trajectories are separated from step 0 — the model that will
refuse already carries the refusal signal at the first generated token. Reads committed summary.json; no GPU.
"""
import json, glob, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
GREY, ORANGE, BLUE, INK = "#888888", "#D55E00", "#0072B2", "#222222"
d = sorted(glob.glob(os.path.join(DC, "outputs", "refusal_traj_clearharm_*711956*")))[-1]
s = json.load(open(os.path.join(d, "summary.json")))["by_split"]["test"]
bl = s["by_layer"]["30"]
def clip(v): return [x for x in v if x is not None]

fig, ax = plt.subplots(figsize=(7.2, 4.6))
for key, col, lab in [("direct", GREY, "Direct harmful (refuses)"),
                      ("ds_refused", BLUE, "Doublespeak → refuses"),
                      ("ds_complied", ORANGE, "Doublespeak → jailbreak")]:
    y = clip(bl[key]); ax.plot(range(len(y)), y, "-", color=col, lw=2.2, label=lab)
ax.axvline(0, color=INK, ls=":", lw=1)
ax.annotate("decision point (token 0):\noutcome already separated", xy=(0, 9.1), xytext=(8, 11),
            fontsize=9, color=INK, arrowprops=dict(arrowstyle="->", color=INK))
ax.axhline(0, color="#CCCCCC", lw=0.8)
ax.set_xlabel("generated token index", fontsize=11)
ax.set_ylabel("refusal-axis projection (L30)", fontsize=11)
ax.set_title("Refusal is decided at the decision point, not re-engaged mid-generation\n"
             "(clearharm test; curated has 0% DS refusals — its non-jailbreaks are concept-dilution, not refusal)",
             fontsize=10.5, loc="left")
ax.legend(fontsize=9.5, frameon=False, loc="upper right")
ax.spines[["top", "right"]].set_visible(False); ax.grid(color="#EEEEEE")
fig.tight_layout()
outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "refusal_trajectory.png")
fig.savefig(out, dpi=170, bbox_inches="tight")
print("wrote", out)
print("step0 L30:", {k: round(clip(bl[k])[0], 2) for k in ["direct", "ds_refused", "ds_complied"]})
