#!/usr/bin/env python3
"""CORRECTED refusal depth-localization figure, built ONLY from generation-VALIDATED refusal
directions (P7, plan §1.1/§38-item-2).

Every plotted number is recomputed from raw.jsonl (never from report prose):
  Panel A  -- per-layer refusal-axis validation metric (ablate & induce specificity vs norm-matched
              random controls), both direction families, all 32 layers.
              Source: outputs/refval_clearharm_20260806_054117_722611/raw.jsonl (job 722611, full sweep).
  Panel B  -- calibrated rescue delta_ASR (adding the refusal axis back reduces attack success),
              at the injectable layers {9,16,22,28}, both cohorts.
              Source: outputs/refinject_cal_{clearharm,curated}/raw.jsonl (train split).

Validated-in-BOTH-families set = {13,14,15,16,17,18,19,20,24,28,29}. L0-L12 have NO validated refusal
axis and are greyed/hatched; one-family-only layers (21,22,23,27,30) are drawn faded, never as evidence.

Usage: python scripts/make_depth_validated_figure.py  -> figures/fig_depth_validated.png
"""
import json, os
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
OUT = os.path.join(DC, "outputs")

BLUE, ORANGE, GREEN, GREY, INK = "#0072B2", "#D55E00", "#009E73", "#BBBBBB", "#222222"
VALID_BOTH = {13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 29}

# ----------------------------------------------------------------------------- Panel A data (from raw)
SWEEP = os.path.join(OUT, "refval_clearharm_20260806_054117_722611", "raw.jsonl")
raw = [json.loads(l) for l in open(SWEEP)]
bh = sum(r["refused"] for r in raw if r["arm"] == "base_harmful") / \
     sum(1 for r in raw if r["arm"] == "base_harmful")          # base harmful refusal (=0.95)
bb = sum(r["refused"] for r in raw if r["arm"] == "base_benign") / \
     sum(1 for r in raw if r["arm"] == "base_benign")           # base benign refusal (=0.00)
agg = defaultdict(list)
for r in raw:
    if r["family"] is None:
        continue
    agg[(r["family"], r["layer"], r["arm"])].append(r["refused"])
mean = {k: sum(v) / len(v) for k, v in agg.items()}
LAYERS = sorted({l for (_, l, _) in agg})
FAMS = ["existing", "clearharm"]


def spec(fam, layer):
    abl = mean[(fam, layer, "ablate")]; ablr = mean[(fam, layer, "ablate_rand")]
    ind = mean[(fam, layer, "induce")]; indr = mean[(fam, layer, "induce_rand")]
    return (bh - abl) - (bh - ablr), (ind - bb) - (indr - bb)   # ablate_spec, induce_spec


A = {fam: {L: spec(fam, L) for L in LAYERS} for fam in FAMS}

# ----------------------------------------------------------------------------- Panel B data (from raw)
INJ = {"clearharm": os.path.join(OUT, "refinject_cal_clearharm_20260804_194105_711685", "raw.jsonl"),
       "curated":   os.path.join(OUT, "refinject_cal_curated_20260804_213213_711769", "raw.jsonl")}
INJ_L = [9, 16, 22, 28]
B = {}
for cohort, path in INJ.items():
    rows = [r for r in (json.loads(l) for l in open(path)) if r["split"] == "train"]
    n = len(rows)
    base = sum(r["ds_base_label"] == "MALICIOUS" for r in rows) / n
    B[cohort] = {"n": n}
    for L in INJ_L:
        cal = sum(r[f"ds_cal_L{L}_label"] == "MALICIOUS" for r in rows) / n
        rnd = sum(r[f"ds_calrand_L{L}_label"] == "MALICIOUS" for r in rows) / n
        B[cohort][L] = {"delta_ASR": cal - base, "rand_delta_ASR": rnd - base}
# McNemar p-values are read from the committed summaries (paired-test statistic, not a raw mean)
for cohort in INJ:
    sdir = os.path.dirname(INJ[cohort])
    s = json.load(open(os.path.join(sdir, "summary.json")))["by_split"]["train"]["by_layer_vs_ds_base"]
    for L in INJ_L:
        B[cohort][L]["p"] = s[str(L)]["mcnemar_p"]

# ============================================================================= FIGURE
fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.5, 5.2), gridspec_kw={"width_ratios": [1.55, 1]})

# ---- Panel A ---------------------------------------------------------------------------------------
# grey/hatch the region with no validated refusal axis
axA.axvspan(-0.5, 12.5, facecolor=GREY, alpha=0.22, hatch="///", edgecolor="#999999", zorder=0, lw=0)
axA.text(6, axA.get_ylim()[1], "", )  # noop keep autoscale
# faint green shading on validated-in-both layers
for L in VALID_BOTH:
    axA.axvspan(L - 0.5, L + 0.5, facecolor=GREEN, alpha=0.10, zorder=0, lw=0)

styles = {"existing": (BLUE, "existing (carrot/bomb fit)"),
          "clearharm": (ORANGE, "clearharm (native refit)")}
for fam in FAMS:
    c, lab = styles[fam]
    xs = LAYERS
    abl = [A[fam][L][0] for L in xs]
    ind = [A[fam][L][1] for L in xs]
    axA.plot(xs, abl, "-o", color=c, lw=1.8, ms=4, label=f"{lab} - ablate spec.")
    axA.plot(xs, ind, "--^", color=c, lw=1.3, ms=3.5, alpha=0.7, label=f"{lab} - induce spec.")

axA.axhline(0, color=INK, lw=0.8)
axA.set_xlim(-0.7, 31.7)
ylo, yhi = axA.get_ylim()
axA.text(6, yhi * 0.90, "no validated\nrefusal axis\n(L0-L12)", ha="center", va="top",
         fontsize=9, color="#555555", fontweight="bold")
# anchor layer markers (staggered heights so labels don't collide)
for L, note, frac in [(16, "L16", 0.02), (18, "L18 (strongest,\nboth families)", 0.13),
                      (22, "L22 (clearharm\nfamily only)", 0.02)]:
    axA.axvline(L, color=INK, lw=0.7, ls=":", alpha=0.6, zorder=1)
    axA.text(L, ylo + (yhi - ylo) * frac, note, ha="center", va="bottom", fontsize=7.5,
             color=INK, rotation=0)
axA.set_xlabel("decoder layer of fitted refusal direction", fontsize=11)
axA.set_ylabel("refusal-axis specificity  (gain over norm-matched random dir)", fontsize=10)
axA.set_title("A - A validated refusal axis appears at L13, absent L0-L12  (both fits agree)",
              fontsize=10.5, loc="left")
axA.set_xticks(range(0, 32, 2))
axA.legend(fontsize=7.8, frameon=False, loc="upper right", ncol=1)
axA.spines[["top", "right"]].set_visible(False); axA.grid(axis="y", color="#EEEEEE")

# ---- Panel B ---------------------------------------------------------------------------------------
# bar layout: two cohorts side by side per layer
cohorts = ["clearharm", "curated"]
coh_col = {"clearharm": ORANGE, "curated": BLUE}
w = 0.36
xpos = list(range(len(INJ_L)))
for ci, cohort in enumerate(cohorts):
    offs = (ci - 0.5) * w
    for xi, L in enumerate(INJ_L):
        d = B[cohort][L]["delta_ASR"]; p = B[cohort][L]["p"]
        invalid = (L not in VALID_BOTH)                 # L9 invalid; L22 one-family
        one_fam = (L == 22)
        col = coh_col[cohort]
        hatch = None; alpha = 1.0; ec = col
        if L == 9:
            col = GREY; ec = "#888888"; hatch = "///"; alpha = 0.9   # no validated axis
        elif one_fam:
            alpha = 0.45                                             # one-family only, not evidence
        axB.bar(xi + offs, d, width=w, color=col, edgecolor=ec, hatch=hatch, alpha=alpha, zorder=3)
        # random control
        axB.scatter(xi + offs, B[cohort][L]["rand_delta_ASR"], color=INK, marker="x", s=28, zorder=5)
        # significance star
        if p < 0.05 and L in VALID_BOTH:
            axB.text(xi + offs, d - 0.012, "*", ha="center", va="top", fontsize=13, color=INK)

axB.axhline(0, color=INK, lw=0.8)
axB.set_xticks(xpos)
xlabels = []
for L in INJ_L:
    if L == 9:
        xlabels.append("L9\n(no valid axis)")
    elif L == 22:
        xlabels.append("L22\n(1 family)")
    else:
        xlabels.append(f"L{L}\n(validated)")
axB.set_xticklabels(xlabels, fontsize=8.5)
axB.set_ylabel("calibrated rescue  ΔASR  (more negative = refusal restored)", fontsize=9.5)
axB.set_title("B - Restoring the axis rescues at validated mid-late layers (train)", fontsize=10.5, loc="left")
axB.spines[["top", "right"]].set_visible(False); axB.grid(axis="y", color="#EEEEEE")

legB = [Patch(facecolor=ORANGE, label="clearharm cohort"),
        Patch(facecolor=BLUE, label="curated cohort"),
        Patch(facecolor=GREY, hatch="///", edgecolor="#888888", label="no validated axis (L9)"),
        Line2D([0], [0], marker="x", color=INK, ls="none", label="random dir (control)"),
        Line2D([0], [0], marker="$*$", color=INK, ls="none", label="McNemar p<0.05")]
axB.legend(handles=legB, fontsize=7.6, frameon=False, loc="lower left")

fig.suptitle("Refusal is read MID-LATE: the refusal axis is validated only from L13 on; "
             "the depth story is built ONLY from validated directions",
             fontsize=12, fontweight="bold", y=1.005)
fig.tight_layout()
outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "fig_depth_validated.png")
fig.savefig(out, dpi=150, bbox_inches="tight")
print("wrote", out)

# --------------------------------------------------------------- print the plotted values for audit
print(f"\nbase_harmful refusal = {bh:.3f}   base_benign refusal = {bb:.3f}")
print("\nPANEL A  per-layer specificity (ablate / induce), by family  [validated-in-both marked *]")
print("  L | existing abl/ind |  clearharm abl/ind | both?")
for L in LAYERS:
    e = A["existing"][L]; c = A["clearharm"][L]
    mark = "*" if L in VALID_BOTH else " "
    print(f" {L:2}{mark}| {e[0]:+.3f} / {e[1]:+.3f}  |  {c[0]:+.3f} / {c[1]:+.3f}")
print("\nPANEL B  calibrated rescue delta_ASR (train), by cohort")
for cohort in cohorts:
    print(f"  {cohort} (n={B[cohort]['n']}):")
    for L in INJ_L:
        b = B[cohort][L]
        print(f"    L{L:2}: dASR={b['delta_ASR']:+.4f}  rand={b['rand_delta_ASR']:+.4f}  p={b['p']:.4f}")
