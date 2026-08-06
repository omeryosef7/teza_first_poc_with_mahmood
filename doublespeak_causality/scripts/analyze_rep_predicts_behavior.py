#!/usr/bin/env python3
"""Item-level rep->behavior: does a Doublespeak prompt's refusal-axis projection predict whether it
jailbreaks? Joins REFPROJ (per-item DS refusal projection) with BEHAV-REFUSAL (per-item ds_base outcome)
by item id. Mann-Whitney U + point-biserial + AUC at decoder L21 (hs22). No GPU. Writes a box/strip figure.

Usage: python scripts/analyze_rep_predicts_behavior.py [--layer 22]
"""
import argparse, json, glob, os
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
ORANGE, BLUE, INK = "#D55E00", "#0072B2", "#222222"

def join(tag):
    rp = sorted(glob.glob(os.path.join(DC, "outputs", f"refproj_{tag}_*")))[-1]
    rf = sorted(glob.glob(os.path.join(DC, "outputs", f"behav_refusal_{tag}_a1.0_*")))[-1]
    proj = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(rp, "raw.jsonl")))}
    out  = {x["id"]: x for x in (json.loads(l) for l in open(os.path.join(rf, "raw.jsonl")))}
    ids = [i for i in proj if i in out]
    return proj, out, ids

# P7 (reports/P7_REFUSAL_DIRECTION_VALIDATION.md §4c) generation-validated every per-layer refusal
# direction. INDEXING: refproj keys are hidden_states rows 1..32, and hidden_states[k+1] is post-block-k,
# so hs h <-> DECODER LAYER h-1 (hs22 = decoder L21, the historical readout). P7 reports decoder layers.
P7_VALID_BOTH_DECODER = [13, 14, 15, 16, 17, 18, 19, 20, 24, 28, 29]
P7_VALID_BOTH_HS = [L + 1 for L in P7_VALID_BOTH_DECODER]


def stats_at(pr, mal):
    """AUC / Mann-Whitney p / point-biserial r for one layer. AUC is P(malicious proj < non-malicious)."""
    U, p = stats.mannwhitneyu(pr[mal], pr[~mal], alternative="less")
    r, _ = stats.pointbiserialr(mal.astype(float), pr)
    return 1 - U / (mal.sum() * (~mal).sum()), float(p), float(r)


def holm(ps):
    """Holm-Bonferroni adjusted p-values, order preserved. 32 layers is a family; report it as one."""
    idx = sorted(range(len(ps)), key=lambda i: ps[i])
    out, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(idx):
        run = max(run, (len(ps) - k) * ps[i])
        out[i] = min(1.0, run)
    return out


def sweep(args):
    """RP-03: the per-layer AUC sweep. Previously quoted in REP_PREDICTS_BEHAVIOR.md but emitted by NO
    code path, hence UNVERIFIED in CLAIM_AUDIT_TABLE. Recomputed here from the committed refproj rows."""
    report = {"index_convention": "keys are hidden_states rows 1..32; hs h == decoder layer h-1",
              "p7_valid_both_families_decoder": P7_VALID_BOTH_DECODER, "cohorts": {}}
    for tag in ["clearharm", "curated"]:
        proj, out, ids = join(tag)
        mal = np.array([out[i]["ds_base_label"] == "MALICIOUS" for i in ids])
        hs_rows = sorted(proj[ids[0]]["doublespeak"], key=int)
        rows, ps = [], []
        for h in hs_rows:
            pr = np.array([proj[i]["doublespeak"][h] for i in ids])
            auc, pv, r = stats_at(pr, mal)
            rows.append(dict(hs=int(h), decoder_layer=int(h) - 1, auc=round(auc, 4),
                             mw_p=pv, r=round(r, 4),
                             p7_valid_both=(int(h) - 1) in P7_VALID_BOTH_DECODER))
            ps.append(pv)
        for row, q in zip(rows, holm(ps)):
            row["mw_p_holm"] = q
        # 5-fold CV AUC at the headline layer. NOTE this is NOT model validation -- the "classifier" is a
        # single raw feature with no fitted parameters, so CV here only measures how stable the AUC is
        # across subsamples. It is computed because REP_PREDICTS_BEHAVIOR.md quotes such a number that
        # no committed code path produced (claim RP-03); folds are deterministic (seed 0), stratified by
        # label so a fold cannot end up single-class (which would make AUC undefined).
        for hl_dec in (args.cv_layer,):
            h = str(hl_dec + 1)
            pr = np.array([proj[i]["doublespeak"][h] for i in ids])
            rng = np.random.default_rng(0)
            folds = [[] for _ in range(5)]
            for cls in (True, False):                      # stratify
                idx = np.where(mal == cls)[0]; rng.shuffle(idx)
                for k, j in enumerate(idx):
                    folds[k % 5].append(j)
            aucs = []
            for f in folds:
                f = np.array(f); m = mal[f]
                if m.all() or (~m).any() == False or m.sum() == 0:
                    continue
                aucs.append(stats_at(pr[f], m)[0])
            cv_auc = dict(layer_decoder=hl_dec, n_folds=len(aucs),
                          mean=round(float(np.mean(aucs)), 4), sd=round(float(np.std(aucs, ddof=1)), 4),
                          folds=[round(float(a), 4) for a in aucs])
        cv = [x for x in rows if x["p7_valid_both"]]
        best = max(rows, key=lambda x: x["auc"])
        best_cv = max(cv, key=lambda x: x["auc"]) if cv else None
        report["cohorts"][tag] = {
            "n": len(ids), "n_malicious": int(mal.sum()), "layers": rows,
            "auc_range_all": [round(min(x["auc"] for x in rows), 4), round(max(x["auc"] for x in rows), 4)],
            "best_layer_any": best,
            "best_layer_p7_valid": best_cv,
            "n_holm_sig": sum(1 for x in rows if x["mw_p_holm"] < 0.05),
            "n_holm_sig_p7_valid": sum(1 for x in cv if x["mw_p_holm"] < 0.05),
            "cv_auc_at_headline_layer": cv_auc,
        }
    dst = os.path.join(DC, "outputs", "rep_predicts_behavior_sweep.json")
    json.dump(report, open(dst, "w"), indent=1)
    print("wrote", dst)
    for tag, c in report["cohorts"].items():
        print(f"\n== {tag}  n={c['n']} malicious={c['n_malicious']}")
        print(f"   AUC over all 32 hs rows: {c['auc_range_all'][0]:.3f} .. {c['auc_range_all'][1]:.3f}")
        print(f"   Holm-significant: {c['n_holm_sig']}/32 all, {c['n_holm_sig_p7_valid']}/{len(P7_VALID_BOTH_DECODER)} among P7-cross-validated layers")
        b = c["best_layer_any"]; print(f"   best any     : decoder L{b['decoder_layer']} AUC={b['auc']:.3f} holm={b['mw_p_holm']:.2e}")
        b = c["best_layer_p7_valid"]
        if b: print(f"   best P7-valid: decoder L{b['decoder_layer']} AUC={b['auc']:.3f} holm={b['mw_p_holm']:.2e}")
        v = c["cv_auc_at_headline_layer"]
        print(f"   5-fold CV AUC @L{v['layer_decoder']}: {v['mean']:.3f} +/- {v['sd']:.3f}  folds={v['folds']}")
    return report


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--layer", default="22")
    ap.add_argument("--cv-layer", type=int, default=21,
                    help="decoder layer for the 5-fold CV AUC (default 21, the historical readout)")
    ap.add_argument("--sweep", action="store_true",
                    help="RP-03: recompute AUC at EVERY layer, Holm-corrected over the 32-layer family, "
                         "and flag which layers P7 validated in both direction families")
    args = ap.parse_args()
    if args.sweep:
        sweep(args); return
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.4))
    res = {}
    for ax, tag in zip(axes, ["clearharm", "curated"]):
        proj, out, ids = join(tag)
        mal = np.array([out[i]["ds_base_label"] == "MALICIOUS" for i in ids])
        pr  = np.array([proj[i]["doublespeak"][args.layer] for i in ids])
        U, p = stats.mannwhitneyu(pr[mal], pr[~mal], alternative="less")
        r, rp = stats.pointbiserialr(mal.astype(float), pr)
        auc = 1 - U / (mal.sum() * (~mal).sum())          # P(malicious proj < non-malicious proj)
        res[tag] = dict(n=len(ids), mal=int(mal.sum()), auc=round(auc, 3), mw_p=float(p), r=round(r, 3))
        # strip + box
        for j, (grp, col, lab) in enumerate([(~mal, BLUE, "refused/benign"), (mal, ORANGE, "jailbreak")]):
            y = pr[grp]; xj = np.random.default_rng(0).normal(j, 0.06, len(y))
            ax.scatter(xj, y, color=col, s=22, alpha=0.7, zorder=3)
            ax.hlines(np.median(y), j - 0.2, j + 0.2, color=INK, lw=2, zorder=4)
        ax.set_xticks([0, 1]); ax.set_xticklabels(["refused/\nbenign", "jailbreak"], fontsize=9)
        ax.set_title(f"{tag}  (AUC={auc:.2f}, p={p:.1e})", fontsize=10.5, loc="left")
        ax.set_ylabel(f"DS refusal-axis projection (L21)" if tag == "clearharm" else "", fontsize=10)
        ax.axhline(0, color="#CCCCCC", lw=0.8); ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#EEEEEE")
    fig.suptitle("A Doublespeak prompt's refusal suppression predicts its jailbreak (clearharm; uniform on curated)",
                 fontsize=11.5, fontweight="bold", y=1.02)
    fig.tight_layout()
    outdir = os.path.join(DC, "figures"); os.makedirs(outdir, exist_ok=True)
    out_png = os.path.join(outdir, "rep_predicts_behavior.png")
    fig.savefig(out_png, dpi=170, bbox_inches="tight")
    print("wrote", out_png); print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main()
