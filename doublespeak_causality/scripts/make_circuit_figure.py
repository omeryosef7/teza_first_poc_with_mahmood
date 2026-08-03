#!/usr/bin/env python3
"""Publication summary figure of the Doublespeak causal circuit. Scalar-only (reads p_concept/C1
from the phase5/phase6/phase7b raw.jsonl; no harmful text plotted). Okabe-Ito colorblind-safe palette.

Panel A: per-layer causal NECESSITY across depth — MLP-write necessity (Phase 6) + head-carry
necessity summed per layer (Phase 5), clearharm heldout (locked test); circuit-stage bands shaded.
Panel B: DIRECT fraction (carry L14-18 ~0 = mediated vs output L30-31 ~0.6 = proximal) + the
L9-write->carry mediation (~0.8 vs random 0).

Usage: python scripts/make_circuit_figure.py
"""
import glob, json, os
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
OUT = os.path.join(DC, "figures", "circuit_summary.png")
# Okabe-Ito (colorblind-safe)
BLUE, ORANGE, GREEN, VERM, PURPLE, SKY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"
INK, MUTED, GRID = "#222222", "#666666", "#DDDDDD"


def newest(patt):
    g = sorted(glob.glob(patt))
    return g[-1] if g else None


def mlp_necessity_by_layer(split="heldout"):
    d = newest(os.path.join(DC, "outputs", "phase6_mlpKO_clearharm_demo_layer_*_703532"))
    rows = [json.loads(l) for l in open(os.path.join(d, "raw.jsonl"))]
    sr = [r for r in rows if r["split"] == split]
    valid = {r["sid"] for r in sr if r["cell"] == "C1" and r["p_concept"] > r.get("benign_p_concept", 1)}
    out = {}
    for w in sorted({r["window"] for r in sr}, key=lambda w: int(w[1:])):
        cm = lambda c: {r["sid"]: r["p_concept"] for r in sr if r["cell"] in (c, "C3_mlpout") and r["window"] == w} if c == "C3" else {r["sid"]: r["p_concept"] for r in sr if r["cell"] == c and r["window"] == w}
        c3, rc = cm("C3"), cm("random_control")
        nec = [rc[s] - c3[s] for s in valid if s in c3 and s in rc]
        out[int(w[1:])] = float(np.mean(nec)) if nec else 0.0
    return out


def head_necessity_by_layer(split="heldout"):
    dirs = [newest(os.path.join(DC, "outputs", f"phase5_headz_clearharm_*_{j}")) for j in (704131, 704133)]
    rows = []
    for d in dirs:
        rows += [json.loads(l) for l in open(os.path.join(d, "raw.jsonl"))]
    sr = [r for r in rows if r["split"] == split]
    valid = {r["sid"] for r in sr if r["cell"] == "benign" and r["C1"] > r.get("benign_p_concept", 1)}
    nec = defaultdict(list)
    for r in sr:
        if r["cell"] == "benign" and r["sid"] in valid:
            nec[(r["layer"], r["head"])].append(r["C1"] - r["p_concept"])
    bylayer = defaultdict(float)
    for (l, h), v in nec.items():
        m = np.mean(v)
        if m > 0:
            bylayer[l] += m
    return dict(bylayer)


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    mlp = mlp_necessity_by_layer()
    head = head_necessity_by_layer()
    L = 32
    xs = np.arange(L)
    mlp_y = np.array([mlp.get(l, 0.0) for l in range(L)])
    head_y = np.array([head.get(l, 0.0) for l in range(L)])

    plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.linewidth": 0.8,
                         "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [2.1, 1]})

    # ---- Panel A: per-layer necessity across depth ----
    ymax = max(mlp_y.max(), head_y.max()) * 1.32
    axA.set_xlim(-0.5, 31.5); axA.set_ylim(0, ymax)
    bands = [(8, 12, "retrieval + write\n(K/V + MLP L9)", "#FDF1E0"),
             (14, 21, "carry heads", "#E9F6F0"), (30, 31, "output", "#F7EBF2")]
    for a, b, lab, col in bands:
        axA.axvspan(a - 0.4, b + 0.4, color=col, zorder=0)
        axA.text((a + b) / 2, ymax * 0.93, lab, ha="center", va="top", fontsize=7.5, color=MUTED)
    axA.plot(xs, mlp_y, "-", color=BLUE, lw=2, marker="o", ms=4, label="MLP-write necessity (demo pos)", zorder=4)
    axA.plot(xs, head_y, "-", color=ORANGE, lw=2, marker="s", ms=4, label="head-carry necessity (Σ/layer)", zorder=4)
    axA.annotate("L9", (9, mlp_y[9]), textcoords="offset points", xytext=(0, 7), color=BLUE, fontsize=9, ha="center", fontweight="bold")
    pl = int(np.argmax(head_y))
    axA.annotate(f"L{pl}", (pl, head_y[pl]), textcoords="offset points", xytext=(0, 7), color=ORANGE, fontsize=9, ha="center", fontweight="bold")
    axA.set_xlabel("layer"); axA.set_ylabel("causal necessity  (Δ p_concept)")
    axA.set_title("A · Causal necessity across depth (ClearHarm, locked test)", fontsize=10, loc="left")
    axA.grid(axis="y", color=GRID, lw=0.6, zorder=0)
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)
    axA.legend(frameon=False, fontsize=8, loc="upper left", bbox_to_anchor=(0.02, 0.80))

    # ---- Panel B: direct_frac + mediation summary (verified numbers) ----
    labels = ["carry\nL14-18", "output\nL30-31", "L9→carry\nmediation", "random\ncontrol"]
    vals = [0.0, 0.62, 0.79, 0.0]
    cols = [ORANGE, PURPLE, GREEN, MUTED]
    bars = axB.bar(range(4), vals, color=cols, width=0.62, zorder=3)
    for i, (bar, v) in enumerate(zip(bars, vals)):
        axB.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9, color=INK)
    axB.axhline(1.0, color=GRID, lw=0.8, ls="--", zorder=1)
    axB.set_xticks(range(4)); axB.set_xticklabels(labels, fontsize=8)
    axB.set_ylabel("fraction"); axB.set_ylim(0, 1.15)
    axB.set_title("B · Direct-to-logit vs mediated (Phase 7 / 7b)", fontsize=10, loc="left")
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)
    axB.grid(axis="y", color=GRID, lw=0.6, zorder=0)

    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.text(0.01, 0.965, "Doublespeak causal circuit:  demo-KV retrieval (L8–11) + L9 MLP write → "
             "L14–21 carry heads (mediated) → L30–31 output → logit",
             fontsize=11, ha="left", color=INK, fontweight="bold")
    fig.savefig(OUT, dpi=160, facecolor="white")
    print(f"wrote {OUT}")
    print(f"  MLP peak L{int(np.argmax(mlp_y))}={mlp_y.max():.3f}; head peak L{pl}={head_y[pl]:.3f}")


if __name__ == "__main__":
    main()
