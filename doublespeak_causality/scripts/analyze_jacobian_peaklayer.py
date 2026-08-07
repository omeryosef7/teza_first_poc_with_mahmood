#!/usr/bin/env python
"""P6 formal peak-layer inferential test (sibling of analyze_jacobian_predicts_behavior.py).

Instead of eyeballing argmax of point estimates, this:
  (a) bootstraps over ITEMS the argmax layer of mean ||J|| (grad_norm) -> modal peak + CI,
  (b) tests a pre-specified MID (L12-17) vs LATE (~L28-30) band contrast on ||J|| with a
      paired-over-items bootstrap CI and a sign test.
Run for BOTH targets (concept, refusal). Reads only scalar Jacobian norms from a
jacobian_* run dir (doublespeak condition, final_prompt position by default). No GPU.

Usage:
  python scripts/analyze_jacobian_peaklayer.py \
    --jac outputs/jacobian_clearharm_20260807_132150_732004 \
    --condition doublespeak --position final_prompt --out outputs/p6_peaklayer_clearharm.json
"""
import argparse, json, os
import numpy as np

MID_BAND = list(range(12, 18))     # L12..L17 inclusive
LATE_BAND = list(range(28, 31))    # L28..L30 inclusive


def _binom_two_sided(k, n, p=0.5):
    """Exact two-sided binomial sign-test p-value (no scipy dependency)."""
    from math import comb
    if n == 0:
        return float("nan")
    probs = [comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(n + 1)]
    pk = probs[k]
    return float(min(1.0, sum(pr for pr in probs if pr <= pk + 1e-12)))


def load_matrix(jac_dir, target, condition, position):
    """Return (item_keys, M) where M is [n_items x n_layers] grad_norm."""
    rows = {}
    n_layers = None
    for line in open(os.path.join(jac_dir, "raw.jsonl")):
        r = json.loads(line)
        if r["condition"] != condition or r["target"] != target:
            continue
        per_layer = r["by_pos"][position]
        gn = [pl["grad_norm"] for pl in per_layer]
        if n_layers is None:
            n_layers = len(gn)
        rows[r["item_key"]] = gn
    keys = sorted(rows)
    M = np.array([rows[k] for k in keys], float)
    return keys, M


def analyze_target(M, n_boot=5000, seed=0):
    n_items, n_layers = M.shape
    layers = np.arange(n_layers)
    rng = np.random.default_rng(seed)

    # point-estimate peak (argmax of mean curve over all items)
    mean_curve = M.mean(axis=0)
    point_peak = int(layers[np.argmax(mean_curve)])

    # (a) bootstrap the argmax layer over item resamples
    peaks = []
    for _ in range(n_boot):
        s = rng.integers(0, n_items, n_items)
        peaks.append(int(layers[np.argmax(M[s].mean(axis=0))]))
    peaks = np.array(peaks)
    vals, cnts = np.unique(peaks, return_counts=True)
    modal_peak = int(vals[np.argmax(cnts)])
    modal_frac = float(cnts.max() / n_boot)
    peak_lo, peak_hi = (int(x) for x in np.percentile(peaks, [2.5, 97.5]))
    # fraction of bootstrap peaks landing inside the MID band
    frac_in_mid = float(np.isin(peaks, MID_BAND).mean())

    # (b) mid vs late contrast, per-item band means
    mid = M[:, MID_BAND].mean(axis=1)
    late = M[:, LATE_BAND].mean(axis=1)
    d = mid - late
    point_diff = float(d.mean())
    # paired bootstrap CI on mean(mid-late)
    bdiffs = []
    for _ in range(n_boot):
        s = rng.integers(0, n_items, n_items)
        bdiffs.append(float(d[s].mean()))
    ci_lo, ci_hi = (float(x) for x in np.percentile(bdiffs, [2.5, 97.5]))
    # sign test: how many items have mid > late
    n_pos = int((d > 0).sum())
    n_neg = int((d < 0).sum())
    n_eff = n_pos + n_neg
    sign_p = _binom_two_sided(n_pos, n_eff)

    return {
        "n_items": int(n_items),
        "n_layers": int(n_layers),
        "point_peak_layer": point_peak,
        "boot_peak": {
            "modal_peak_layer": modal_peak,
            "modal_fraction": round(modal_frac, 4),
            "ci95_layer": [peak_lo, peak_hi],
            "frac_peaks_in_mid_band_L12_17": round(frac_in_mid, 4),
        },
        "mid_vs_late": {
            "mid_band": [MID_BAND[0], MID_BAND[-1]],
            "late_band": [LATE_BAND[0], LATE_BAND[-1]],
            "mean_mid": round(float(mid.mean()), 4),
            "mean_late": round(float(late.mean()), 4),
            "point_diff_mid_minus_late": round(point_diff, 4),
            "ci95_paired_bootstrap": [round(ci_lo, 4), round(ci_hi, 4)],
            "sign_test": {"n_mid_gt_late": n_pos, "n_late_gt_mid": n_neg,
                          "n_eff": n_eff, "two_sided_p": round(sign_p, 6)},
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jac", required=True)
    ap.add_argument("--condition", default="doublespeak")
    ap.add_argument("--position", default="final_prompt")
    ap.add_argument("--nboot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    res = {"jac_dir": a.jac, "condition": a.condition, "position": a.position,
           "seed": a.seed, "nboot": a.nboot, "targets": {}}
    for target in ["concept", "refusal"]:
        keys, M = load_matrix(a.jac, target, a.condition, a.position)
        res["targets"][target] = analyze_target(M, n_boot=a.nboot, seed=a.seed)
    print(json.dumps(res, indent=2))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=2)
        print("wrote", a.out)


if __name__ == "__main__":
    main()
