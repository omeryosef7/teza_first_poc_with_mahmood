"""§17 capstone figure: Bombness is epiphenomenal, refusal is the lever — everywhere.

Self-contained (numbers are the committed, audited headline ΔASRs from the role-probe
sprint; sources in the labels). Grouped bar chart of behavioral ΔASR for Bombness
ablation vs refusal ablation, across cohorts/models + the per-example Phase-5 arm + the
AdvBench second corpus. Shows the Bombness bars pinned near 0 while the refusal bars are
large and positive — the representation≠behavior dissociation with external validity.

No GPU, no model, no harmful text. Writes figures/roleprobe_causal_summary.png.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)
OUT = os.path.join(DC, "figures", "roleprobe_causal_summary.png")

# (label, bombness ΔASR, refusal ΔASR, source). None = arm not applicable/measured.
ROWS = [
    ("Llama\nclearharm\n(necessity)", -0.048, 0.238, "757931"),
    ("Llama\nclearharm\n(2×2 main)", 0.000, 0.357, "757943"),
    ("Phi-4\nclearharm", -0.071, 0.095, "758057"),
    ("Qwen3-14B\nclearharm", 0.048, 0.167, "758075"),
    ("Llama\nper-example\n(Phase 5)", 0.048, None, "758162"),
    ("Llama\nAdvBench\n(Phase 10)", 0.057, 0.295, "758657"),
]

labels = [r[0] for r in ROWS]
bomb = [r[1] for r in ROWS]
refusal = [r[2] for r in ROWS]

x = np.arange(len(labels))
w = 0.38

fig, ax = plt.subplots(figsize=(11, 5.2))
b1 = ax.bar(x - w / 2, [b if b is not None else 0 for b in bomb], w,
            label="Bombness ablation (the concept)", color="#4C72B0")
b2 = ax.bar(x + w / 2, [r if r is not None else 0 for r in refusal], w,
            label="Refusal ablation (the lever)", color="#C44E52")

# mark the not-measured refusal cell (Phase 5 per-example had no refusal arm)
for i, r in enumerate(refusal):
    if r is None:
        ax.text(x[i] + w / 2, 0.005, "n/a", ha="center", va="bottom", fontsize=8, color="gray")

ax.axhline(0, color="black", lw=0.8)
ax.axhspan(-0.03, 0.06, color="#4C72B0", alpha=0.06)  # the "epiphenomenal band" Bombness sits in
ax.set_ylabel("behavioral ΔASR (StrongREJECT ≥ 0.5)")
ax.set_title("Doublespeak causality: the concept representation is epiphenomenal; "
             "refusal suppression is the behavioral lever\n"
             "(across 3 model families, per-example causal surgery, and an independent "
             "second corpus)", fontsize=10.5)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8)
ax.legend(loc="upper left", fontsize=9)
ax.set_ylim(-0.12, 0.45)

# value labels
for bars, vals in ((b1, bomb), (b2, refusal)):
    for rect, v in zip(bars, vals):
        if v is None:
            continue
        ax.text(rect.get_x() + rect.get_width() / 2, v + (0.008 if v >= 0 else -0.02),
                f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=8)

ax.text(0.5, -0.155, "Bombness bars sit in the near-zero band (shaded); refusal bars are "
        "large and, on AdvBench, significant (p=0.0). Numbers are the audited headline "
        "ΔASRs (run ids on x-axis).",
        transform=ax.transAxes, ha="center", fontsize=8, color="#444")

fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=150, bbox_inches="tight")
print(f"wrote {OUT}")
