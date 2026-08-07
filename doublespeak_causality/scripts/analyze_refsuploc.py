#!/usr/bin/env python3
"""§3 analysis — refusal-suppression localization coarse band, done RIGHTLY.

Reads a refsuploc_* run dir's raw.jsonl and, per split, per (component, donor, layer) cell at the
anchor readout row, computes:
  - restoration_i = proj_patched - proj_ds_base           (per item; the effect)
  - gap_i         = proj_direct  - proj_ds_base           (per item; the recoverable range)
  - restore mean + paired bootstrap CI (stats.paired_bootstrap_ci against 0)
  - frac = mean(restoration)/mean(gap)   [RATIO-OF-MEANS — robust; NOT the harness's mean-of-ratios]
  - Wilcoxon signed-rank p (one-sided 'greater' for a restoration claim) — NOT sign-flip permutation (§0.6)
  - specificity: direct-minus-rand and direct-minus-neutral paired-diff bootstrap CI at the same cell

Multiple comparisons: Holm over the DIRECT-donor per-component 32-layer family (and the pooled
4x32 grid), per §0.6. A cell is a Gate-A HIT iff: direct restoration Wilcoxon-Holm significant AND the
direct-minus-rand paired CI excludes 0 (specificity) AND ratio-of-means frac >= --frac-thr.

Discovery = train(+dev); test reported SEPARATELY as frozen confirmation (never pooled as primary).

Usage: python scripts/analyze_refsuploc.py <run_dir> [<run_dir> ...] [--anchor 18] [--frac-thr 0.5]
"""
from __future__ import annotations
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import stats as st
try:
    from scipy.stats import wilcoxon
except Exception:
    wilcoxon = None


def wilcox_p(diffs, alternative="greater"):
    """One-sided Wilcoxon signed-rank p that restoration>0. Returns None if degenerate."""
    d = np.asarray([x for x in diffs if x is not None], float)
    d = d[np.abs(d) > 0]
    if wilcoxon is None or len(d) < 6:
        return None
    try:
        return float(wilcoxon(d, alternative=alternative, zero_method="wilcox").pvalue)
    except Exception:
        return None


def analyze_dir(run_dir, anchor, frac_thr, comps, donors, seed=0):
    raw = os.path.join(run_dir, "raw.jsonl")
    allr = [json.loads(x) for x in open(raw)]
    ar = str(anchor + 1)  # hidden-states row = layer+1
    splits = sorted({r["split"] for r in allr})
    cohort = allr[0].get("cohort", os.path.basename(run_dir))
    layers = sorted({int(k.split("|L")[1]) for r in allr for k in r["patched"]})
    out = {"run_dir": run_dir, "cohort": cohort, "anchor_layer": anchor, "anchor_row": anchor + 1,
           "frac_thr": frac_thr, "by_split": {}}

    for split in splits:
        sr = [r for r in allr if r["split"] == split]
        gap = np.array([r["base"]["direct"][ar] - r["base"]["ds_base"][ar] for r in sr], float)
        ds_base = np.array([r["base"]["ds_base"][ar] for r in sr], float)
        direct = np.array([r["base"]["direct"][ar] for r in sr], float)

        def restore_arr(C, donor, Lp):
            key = f"{C}|{donor}|L{Lp}"
            return np.array([r["patched"][key][ar] - r["base"]["ds_base"][ar] for r in sr if key in r["patched"]], float)

        cells = {}
        selfswap_max = 0.0
        # collect direct-donor p-values per component for Holm
        direct_pvals = {C: {} for C in comps}
        for C in comps:
            for Lp in layers:
                for donor in donors:
                    rest = restore_arr(C, donor, Lp)
                    if len(rest) == 0:
                        continue
                    ci = st.paired_bootstrap_ci(rest, np.zeros_like(rest), n_boot=2000, seed=seed)
                    frac = float(rest.mean() / gap.mean()) if abs(gap.mean()) > 1e-9 else None
                    entry = {"n": len(rest), "restore_mean": round(float(rest.mean()), 4),
                             "restore_ci": [round(ci["lo"], 4), round(ci["hi"], 4)],
                             "frac_ratio_of_means": round(frac, 4) if frac is not None else None}
                    if donor in ("direct", "neutral"):
                        entry["wilcoxon_p_greater"] = wilcox_p(rest, "greater")
                    if donor == "direct":
                        direct_pvals[C][Lp] = entry.get("wilcoxon_p_greater")
                    if donor == "self":
                        selfswap_max = max(selfswap_max, float(np.abs(rest).max()) if len(rest) else 0.0)
                    cells[f"{C}|{donor}|L{Lp}"] = entry
            # specificity: direct - rand and direct - neutral paired diffs at each layer
            for Lp in layers:
                dk = f"{C}|direct|L{Lp}"
                if dk not in cells:
                    continue
                dr = restore_arr(C, "direct", Lp)
                for alt in ("rand", "neutral"):
                    ak = f"{C}|{alt}|L{Lp}"
                    if ak not in cells:
                        continue
                    ra = restore_arr(C, alt, Lp)
                    m = min(len(dr), len(ra))
                    if m < 2:
                        continue
                    dci = st.paired_bootstrap_ci(dr[:m], ra[:m], n_boot=2000, seed=seed)
                    cells[dk][f"minus_{alt}_ci"] = [round(dci["lo"], 4), round(dci["hi"], 4)]
                    cells[dk][f"minus_{alt}_excludes0"] = bool((dci["lo"] > 0 or dci["hi"] < 0) and dci["ci_reliable"])
                    # specificity requires the DONOR restore MORE than the control (lo>0), not merely differ
                    cells[dk][f"minus_{alt}_donor_higher"] = bool(dci["lo"] > 0 and dci["ci_reliable"])

        # Holm over the direct-donor per-component family + pooled grid
        holm = {}
        pooled_keys, pooled_p = [], []
        for C in comps:
            ks = [Lp for Lp in layers if direct_pvals[C].get(Lp) is not None]
            ps = [direct_pvals[C][Lp] for Lp in ks]
            if ps:
                adj = st.holm_bonferroni(ps)
                for Lp, a in zip(ks, adj):
                    cells[f"{C}|direct|L{Lp}"]["holm_p_percomp"] = round(float(a), 5)
            for Lp in ks:
                pooled_keys.append(f"{C}|direct|L{Lp}"); pooled_p.append(direct_pvals[C][Lp])
        if pooled_p:
            adj = st.holm_bonferroni(pooled_p)
            for k, a in zip(pooled_keys, adj):
                cells[k]["holm_p_pooled"] = round(float(a), 5)

        # Gate-A hits
        hits = []
        for C in comps:
            for Lp in layers:
                dk = f"{C}|direct|L{Lp}"
                e = cells.get(dk, {})
                sig = (e.get("holm_p_percomp") is not None and e["holm_p_percomp"] < 0.05)
                spec = e.get("minus_rand_donor_higher", False)  # direct must restore MORE than norm-random
                fr = e.get("frac_ratio_of_means")
                if sig and spec and fr is not None and fr >= frac_thr:
                    hits.append({"cell": f"{C}|L{Lp}", "frac": fr, "restore_ci": e["restore_ci"],
                                 "holm_p": e["holm_p_percomp"], "minus_rand_ci": e.get("minus_rand_ci")})
        hits.sort(key=lambda h: -h["frac"])

        out["by_split"][split] = {
            "n": len(sr), "gap_mean": round(float(gap.mean()), 4),
            "ds_base_mean": round(float(ds_base.mean()), 4), "direct_mean": round(float(direct.mean()), 4),
            "selfswap_max_abs_restore": round(selfswap_max, 6),
            "gate_a_hits": hits, "cells": cells}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dirs", nargs="+")
    ap.add_argument("--anchor", type=int, default=18)
    ap.add_argument("--frac-thr", type=float, default=0.5)
    ap.add_argument("--components", default="resid_pre,attn_out,mlp_out,resid_post")
    ap.add_argument("--donors", default="direct,neutral,rand,self")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    comps = args.components.split(","); donors = args.donors.split(",")
    for rd in args.run_dirs:
        res = analyze_dir(rd, args.anchor, args.frac_thr, comps, donors, args.seed)
        outp = os.path.join(rd, "analysis_refsuploc.json")
        json.dump(res, open(outp, "w"), indent=1)
        print(f"\n=== {res['cohort']}  anchor L{args.anchor}  -> {outp} ===")
        for sp, s in res["by_split"].items():
            print(f"[{sp}] n={s['n']} gap={s['gap_mean']:+.3f} (ds_base={s['ds_base_mean']:.2f} direct={s['direct_mean']:.2f}) "
                  f"self-swap max|restore|={s['selfswap_max_abs_restore']:.2e}")
            if s["gate_a_hits"]:
                print(f"   GATE-A HITS (Holm-sig · specific vs rand · frac>={args.frac_thr}):")
                for h in s["gate_a_hits"][:10]:
                    print(f"     {h['cell']:>16}  frac={h['frac']}  restore_ci={h['restore_ci']}  "
                          f"holm_p={h['holm_p']}  d-rand_ci={h['minus_rand_ci']}")
            else:
                print("   GATE-A HITS: none at this threshold")


if __name__ == "__main__":
    main()
