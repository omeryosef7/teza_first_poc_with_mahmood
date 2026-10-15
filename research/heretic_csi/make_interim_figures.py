"""Interim figures for the HERETIC-CSI deliverables (F9).  CPU only.

v2 (review #9 fixes): writes NEW files only (v1 PNGs are left untouched):
  reports/heretic_csi/fig_p2a_val_specificity_v2.png   — per-cell status annotation; descriptive/fragile cells hollow;
                                                          shuffled-label controls coloured separately
  reports/heretic_csi/fig_p2b_preservation_vs_rank_v2.png — both panels as a FRACTION OF THE BASE−KO GAP, labelled
                                                          axes, ±5% reference band, explicit rank ticks, "no CI" note
  reports/heretic_csi/P6_GATE_TABLE_interim.md          — G3/G1/G2 per codeword from the P6 manifests (snapshot)
Inputs: committed report JSONs (hcsi_p2a_*_r{1,16}.json committed in S-198; others committed earlier) and, for the P6
table only, the per-codeword manifests outputs/heretic_csi/p6/stage0_<cw>.json (NOT in git; snapshot, interim)."""
import glob, json, os, datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
R = os.path.join(REPO, "reports/heretic_csi")

def load(n):
    return json.load(open(os.path.join(R, n)))

# ---------------- Fig 1 v2: P2a VALIDATION, candidate vs rank-matched controls, with per-cell status ----------------
cells = {
    "basket": [(1, "hcsi_p2a_basket_r1.json", "PASS 1/57 (robust to floor, S-200);\nuncorrected over 3 VAL looks\n(Holm 0.0525) ⇒ SUGGESTIVE", "pass"),
               (4, "hcsi_p2a_basket_r4_validation.json", "descriptive, FRAGILE —\nnot a pass", "desc"),
               (16, "hcsi_p2a_basket_r16.json", "fail 10/57", "fail")],
    "button": [(1, "hcsi_p2a_button_r1.json", "fail 14/57", "fail"),
               (4, "hcsi_p2a_button_r4ext_validation_analyzer.json", "CONFIRMED 1/201\n(200 ctrl, Holm 0.0149)", "conf"),
               (16, "hcsi_p2a_button_r16.json", "fail 10/57", "fail")],
}
style = {"conf": dict(color="C3", facecolors="C3"), "pass": dict(color="C1", facecolors="C1"),
         "desc": dict(color="0.4", facecolors="none"), "fail": dict(color="k", facecolors="none")}
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
rng = np.random.default_rng(0)
for ax, (cw, lst) in zip(axes, cells.items()):
    for i, (r, f, lab, st) in enumerate(lst):
        d = load(f)
        assert d.get("split") == "validation", (f, d.get("split"))
        c = d["control_recovery_distribution"]
        names = list(c["controls"].keys())
        vals = np.array([c["controls"][k] for k in names], float)
        shuf = np.array([k.startswith("KO_SHUF") for k in names])
        jit = rng.uniform(-0.15, 0.15, len(vals))
        ax.scatter(i + jit[~shuf], vals[~shuf], s=7, color="0.65", label="random rank-matched controls" if i == 0 else None)
        ax.scatter(i + jit[shuf], vals[shuf], s=14, color="C0", marker="^", label="shuffled-label controls" if i == 0 else None)
        ax.scatter([i], [c["candidate"]], s=70, marker="D", edgecolors=style[st]["color"],
                   facecolors=style[st]["facecolors"], linewidths=1.5, zorder=5,
                   label="candidate" if i == 0 else None)
        ax.annotate(lab, (i, c["candidate"]), textcoords="offset points", xytext=(9, 2), fontsize=7)
    ax.set_xticks(range(3)); ax.set_xticklabels(["r1", "r4", "r16"])
    ax.axhline(0, lw=0.5, color="k")
    ax.set_title(f"{cw} — P2a VALIDATION (PLS, L18 rel-6, under KO)", fontsize=10)
    ax.set_ylabel("candidate − KO  (domain-level Δ y_install)")
    ax.legend(fontsize=7, loc="upper left")
fig.text(0.5, -0.06,
         "Filled red = CONFIRMED (S-126); filled orange = preregistered pass, SUGGESTIVE (S-049/S-198/S-200); hollow = fail or descriptive. "
         "button r4 uses the S-084 powered family (190 random + 10 shuffled); other cells 46 + 10.\n"
         "Basket VAL cells use 133–145 common rows vs button 193–203 (declared option-mass attrition). "
         "Sources: hcsi_p2a_*.json (S-049, S-073, S-125/126).", ha="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(R, "fig_p2a_val_specificity_v2.png"), dpi=150, bbox_inches="tight")

# ---------------- Fig 2 v2: P2b preservation vs rank, as fraction of the BASE−KO gap ----------------
rows = load("P2B_RANK_CURVE_TRAIN.json")["rows"]
fig, axes = plt.subplots(1, 2, figsize=(11, 3.9))
ticks = [1, 2, 4, 8, 16, 32, 50]
for cw, col in (("basket", "C0"), ("button", "C1")):
    rr = sorted([x for x in rows if x["codeword"] == cw], key=lambda x: x["rank"])
    ks = [x["rank"] for x in rr]
    gap = [abs(x["manip_KO_minus_BASE"]) for x in rr]
    axes[0].plot(ks, [x["fit_preserve_damage"] for x in rr], "o-", color=col, label=cw)
    axes[1].plot(ks, [x["BASE_CAND_minus_BASE_y"] / g for x, g in zip(rr, gap)], "o-", color=col, label=cw)
axes[0].set_ylabel("fit-side preserve damage\n(fraction of the BASE−KO gap)")
axes[0].set_title("fit side (TRAIN captures, in-sample)", fontsize=9)
axes[1].set_ylabel("(BASE_CAND − BASE) / |KO − BASE|\n(clean-prompt Δy as fraction of the gap)")
axes[1].set_title("deployed on clean prompts (TRAIN-K4)", fontsize=9)
for ax in axes:
    ax.set_xscale("log", base=2); ax.set_xticks(ticks); ax.set_xticklabels([str(t) for t in ticks])
    ax.set_xlabel("operator rank"); ax.axhline(0, lw=0.5, color="k")
    ax.legend(fontsize=7)
axes[1].axhspan(-0.05, 0.05, color="0.9", zorder=0, label="±5% of gap"); axes[1].legend(fontsize=7)
axes[0].text(0.02, 0.92, "all values < 0.4% of the gap", transform=axes[0].transAxes, fontsize=7)
fig.text(0.5, -0.07,
         "P2b weight operator, TRAIN-K4, in-sample, DESCRIPTIVE (S-188). Point estimates only — no CI is available for these "
         "quantities. KL and refusal were not measured as preservation endpoints.\nSource: P2B_RANK_CURVE_TRAIN.json.",
         ha="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(R, "fig_p2b_preservation_vs_rank_v2.png"), dpi=150, bbox_inches="tight")

# ---------------- P6 gate table (snapshot of manifests) ----------------
lines = ["# P6 gate table — INTERIM snapshot (" + datetime.datetime.now().isoformat(timespec="minutes") + ")", "",
         "Source: `outputs/heretic_csi/p6/stage0_<cw>.json` manifests (not in git; snapshot). Decision rules: PREREG_P6 +",
         "amendments 1–6. G3 median is the frozen point rule (CI descriptive). Codewords without a manifest have no Stage-0",
         "result yet.", "",
         "| codeword | G3 median | G3 | G1 C−A [95% CI] | G1 | G2 | readout job | partition |", "|---|---|---|---|---|---|---|---|"]
for man in sorted(glob.glob(os.path.join(REPO, "outputs/heretic_csi/p6/stage0_*.json"))):
    if man.endswith(".lock"):
        continue
    m = json.load(open(man))
    g3 = m.get("g3") or {}
    g1 = m.get("g1") or {}
    med = g3.get("g3_median_option_mass", g3.get("g3_median"))
    ci = g1.get("ci95")
    lines.append("| {} | {} | {} | {} | {} | {} | {} | {} |".format(
        m.get("codeword"), "" if med is None else f"{med:.4f}", m.get("g3_status", m.get("status")),
        "" if not g1 else f"{g1.get('install_strength_C_minus_A')} [{ci[0]}, {ci[1]}]" if ci else "",
        m.get("g1_status", ""), m.get("g2_status", ""), m.get("readout_slurm_job", ""),
        (m.get("partitions") or {}).get("readout", "")))
open(os.path.join(R, "P6_GATE_TABLE_interim.md"), "w").write("\n".join(lines) + "\n")
print("OK")
