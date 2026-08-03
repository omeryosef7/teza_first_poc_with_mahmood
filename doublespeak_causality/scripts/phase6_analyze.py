#!/usr/bin/env python3
"""Reusable per-split + Holm-corrected analysis of a phase6_mlp_causal.py output dir.

Reads raw.jsonl, reports dev(train)/heldout(test) SEPARATELY (plan mandate), and applies
Holm correction across the 32-layer family (paired sign-flip permutation p-values) so tiny
per-layer CIs that don't survive multiple comparisons are not over-claimed.

Necessity specific effect per (split, window) = random_control - C3_mlpout (paired).
Sufficiency specific = S3_install - S_random (paired).

Usage: python scripts/phase6_analyze.py <output_dir> [<output_dir> ...]
"""
from __future__ import annotations
import json, os, sys
import numpy as np

RNG = np.random.default_rng(0)


def perm_p(vals, nperm=20000):
    a = np.array(vals, dtype=float)
    if a.size == 0:
        return 1.0
    obs = abs(a.mean())
    signs = RNG.integers(0, 2, size=(nperm, a.size)) * 2 - 1
    null = np.abs((signs * a).mean(axis=1))
    return float((null >= obs).mean())


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
        npos = next((r.get("n_pos_swapped") for r in sr if r["cell"] == "C3_mlpout"), None)
        for w in wins:
            cm = lambda c: {r["sid"]: r["p_concept"] for r in sr if r["cell"] == c and r["window"] == w}
            c3, rc, s3, sr_ = cm("C3_mlpout"), cm("random_control"), cm("S3_install"), cm("S_random")
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
