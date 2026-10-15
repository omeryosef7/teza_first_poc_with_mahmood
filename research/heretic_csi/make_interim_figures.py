"""Interim figures for the HERETIC-CSI deliverables (F9). CPU only; reads committed report JSONs only.
Outputs: reports/heretic_csi/fig_p2a_val_specificity.png, fig_p2b_preservation_vs_rank.png."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
R = os.path.join(REPO, "reports/heretic_csi")

def load(n):
    return json.load(open(os.path.join(R, n)))

# --- Fig 1: P2a VALIDATION activation-space rescue: candidate vs rank-matched control distribution ---
cells = {
    "basket": {1: "hcsi_p2a_basket_r1.json", 4: "hcsi_p2a_basket_r4_validation.json", 16: "hcsi_p2a_basket_r16.json"},
    "button": {1: "hcsi_p2a_button_r1.json", 4: "hcsi_p2a_button_r4ext_validation_analyzer.json", 16: "hcsi_p2a_button_r16.json"},
}
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=False)
for ax, (cw, m) in zip(axes, cells.items()):
    for i, (r, f) in enumerate(sorted(m.items())):
        d = load(f)
        assert d.get("split") == "validation", (f, d.get("split"))
        c = d["control_recovery_distribution"]
        ctr = np.array(list(c["controls"].values()), float)
        vb = d["verdict_basis"]
        ax.scatter(np.full(len(ctr), i) + np.random.default_rng(0).uniform(-0.15, 0.15, len(ctr)), ctr,
                   s=8, color="0.6", label="rank-matched controls" if i == 0 else None)
        ax.scatter([i], [c["candidate"]], s=60, color="C3", marker="D",
                   label="candidate" if i == 0 else None)
        ax.annotate(f"{vb['candidate_rank']}/{vb['n_controls']+1}", (i, c["candidate"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=8)
    ax.set_xticks(range(3)); ax.set_xticklabels(["r1", "r4", "r16"])
    ax.axhline(0, lw=0.5, color="k")
    ax.set_title(f"{cw} — P2a VALIDATION (L18 rel-6, under KO)")
    ax.set_ylabel("candidate − KO (domain-level stat)")
    ax.legend(fontsize=7, loc="upper left")
fig.text(0.5, -0.02, "button r4 uses the S-084 powered family (200 controls); others 56. Labels = candidate rank / (n+1). "
         "Sources: hcsi_p2a_*.json (S-049, S-072/073, S-125/126).", ha="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(R, "fig_p2a_val_specificity.png"), dpi=150, bbox_inches="tight")

# --- Fig 2: P2b preservation vs rank (TRAIN-K4, descriptive) ---
rows = load("P2B_RANK_CURVE_TRAIN.json")["rows"]
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
for cw, col in (("basket", "C0"), ("button", "C1")):
    rr = sorted([x for x in rows if x["codeword"] == cw], key=lambda x: x["rank"])
    ks = [x["rank"] for x in rr]
    axes[0].plot(ks, [x["fit_preserve_damage"] for x in rr], "o-", color=col, label=cw)
    axes[1].plot(ks, [x["BASE_CAND_minus_BASE_y"] for x in rr], "o-", color=col, label=cw)
for ax, t in zip(axes, ["fit-side preserve damage (TRAIN captures)", "BASE_CAND − BASE (clean-prompt y change)"]):
    ax.set_xscale("log", base=2); ax.set_xlabel("operator rank"); ax.set_title(t, fontsize=9); ax.legend(fontsize=8)
    ax.axhline(0, lw=0.5, color="k")
fig.text(0.5, -0.03, "P2b weight operator, TRAIN-K4, in-sample, DESCRIPTIVE. Source: P2B_RANK_CURVE_TRAIN.json (S-188).",
         ha="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(R, "fig_p2b_preservation_vs_rank.png"), dpi=150, bbox_inches="tight")
print("OK")
