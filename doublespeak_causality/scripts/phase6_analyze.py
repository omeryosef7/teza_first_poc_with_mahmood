#!/usr/bin/env python3
"""Reusable per-split + Holm-corrected analysis of a phase6_mlp_causal.py output dir.

Reads raw.jsonl, reports dev(train)/heldout(test) SEPARATELY (plan mandate), and applies
Holm correction across the 32-layer family (paired sign-flip permutation p-values) so tiny
per-layer CIs that don't survive multiple comparisons are not over-claimed.

Necessity specific effect per (split, window) = random_control - C3 (necessity cell; legacy alias C3_mlpout accepted) (paired).
Sufficiency specific = S3_install - S_random (paired).

Usage: python scripts/phase6_analyze.py <output_dir> [<output_dir> ...]
"""
from __future__ import annotations
import json, os, sys
import numpy as np
from scipy import stats

RNG = np.random.default_rng(0)


def perm_p(vals):
    """Two-sided WILCOXON signed-rank p (H0: median diff = 0). Chosen over (a) the sign-flip
    permutation — RNG-order-dependent + resolution-limited to 1/nperm — and (b) the paired
    t-test — which is over-conservative here because the necessity diffs are strongly RIGHT-
    SKEWED (a few strong-concept examples dominate the mean while the sign is consistent).
    Wilcoxon is robust to that skew, deterministic, and resolves below any Holm threshold used
    here. Effect size + CI still via bootci."""
    a = np.array(vals, dtype=float)
    if a.size < 6 or np.allclose(a, 0):
        return 1.0
    try:
        return float(stats.wilcoxon(a).pvalue)
    except ValueError:
        return 1.0


def bootci(vals, nboot=2000):
    a = np.array(vals, dtype=float)
    if a.size == 0:
        return None
    boot = [RNG.choice(a, a.size, replace=True).mean() for _ in range(nboot)]
    return [round(float(a.mean()), 4), round(float(np.percentile(boot, 2.5)), 4),
            round(float(np.percentile(boot, 97.5)), 4)]


def holm(pvals: dict, alpha=0.05):
    order = sorted(pvals, key=lambda k: pvals[k])
    m = len(order)
    rej, ok = {}, True
    for i, k in enumerate(order):
        if ok and pvals[k] <= alpha / (m - i):
            rej[k] = True
        else:
            ok = False
            rej[k] = False
    return rej


def analyze_dir(d):
    rows = [json.loads(l) for l in open(os.path.join(d, "raw.jsonl"))]
    meta = json.load(open(os.path.join(d, "summary.json"))) if os.path.exists(os.path.join(d, "summary.json")) else {}
    cohort = meta.get("cohort", "?")
    positions = meta.get("positions", "?")
    out = {"dir": os.path.basename(d), "cohort": cohort, "positions": positions, "by_split": {}}
    for sp in sorted({r["split"] for r in rows}):
        sr = [r for r in rows if r["split"] == sp]
        valid = {r["sid"] for r in sr if r["cell"] == "C1"
                 and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
        wins = sorted({r["window"] for r in sr},
                      key=lambda w: int(w[1:]) if w.startswith("L") else 99)
        pv, mean, cis, suf = {}, {}, {}, {}
        # cell alias: dirs generated before commit e3802f4 store the necessity cell as
        # "C3_mlpout"; later renamed "C3". Accept both so the reproduce path works on old + new dirs.
        _ALIAS = {"C3": ("C3", "C3_mlpout")}
        npos = next((r.get("n_pos_swapped") for r in sr if r["cell"] in _ALIAS["C3"]), None)
        for w in wins:
            cm = lambda c: {r["sid"]: r["p_concept"] for r in sr
                            if r["cell"] in _ALIAS.get(c, (c,)) and r["window"] == w}
            c3, rc, s3, sr_ = cm("C3"), cm("random_control"), cm("S3_install"), cm("S_random")
            nec = [s for s in valid if s in c3 and s in rc]
            sfx = [s for s in valid if s in s3 and s in sr_]
            diffs = [rc[s] - c3[s] for s in nec]
            pv[w] = perm_p(diffs)
            mean[w] = round(float(np.mean(diffs)), 4) if diffs else 0.0
            cis[w] = bootci(diffs)
            suf[w] = bootci([s3[s] - sr_[s] for s in sfx])
        rej = holm(pv)
        holm_pos = [(w, mean[w], round(pv[w], 5), cis[w]) for w in wins if rej.get(w) and mean[w] > 0]
        holm_neg = [(w, mean[w]) for w in wins if rej.get(w) and mean[w] < 0]
        out["by_split"][sp] = {
            "n_valid": len(valid), "n_pos_patched": npos,
            "holm_positive_necessity": holm_pos, "holm_negative": holm_neg,
            "per_window_mean": mean, "per_window_suf": suf,
        }
    return out


def main():
    for d in sys.argv[1:]:
        r = analyze_dir(d)
        print(f"\n### {r['cohort']} / positions={r['positions']}  ({r['dir']})")
        for sp, s in r["by_split"].items():
            print(f"  [{sp}] n_valid={s['n_valid']} n_pos={s['n_pos_patched']}")
            print(f"     Holm+ necessity: {s['holm_positive_necessity']}")
            if s["holm_negative"]:
                print(f"     Holm- (noise): {s['holm_negative']}")


if __name__ == "__main__":
    main()
