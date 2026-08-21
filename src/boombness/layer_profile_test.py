"""layer_profile_test.py — is the layer profile a BAND, or the maximum of an unordered family?

WHY. Over the 10 AdvBench layer arms, Holm rejects nothing: L12 has p_cl = 0.00562 against a
threshold of 0.00500. So "L12 is significant" is not quotable. But per-layer correction answers
"is this ONE layer special", which is not the claim. The claim is that the effect occupies a
**contiguous band with a hard edge** — L8/L10/L12 each individually p<0.02, L6 marginal, L13/L14
decaying, and everything from L16 outward flat.

A lone significant layer flanked by nulls is a selection artifact. A monotone rise-and-fall across
ordered layers is different evidence — but only if the ORDER matters. That is what this tests, and
the report previously asserted the band descriptively while naming this test as missing.

THE NULL IS LAYER-LABEL EXCHANGEABILITY. Take the observed per-layer effects as a multiset and
reassign them to depths at random. Under that null the same effect sizes exist but their arrangement
carries no information, so any concentration into a contiguous run is chance. The statistic is a
SCAN: the largest contiguous window of layers by sum of effects, size-weighted so a wide mediocre
window competes fairly with a narrow strong one.

WHAT THIS DOES NOT DO. It conditions on the observed multiset of effects, so it cannot tell you the
effects are real — only that their ARRANGEMENT is not random. If every layer effect were noise, this
test could still fire on a lucky contiguous run. It is evidence about SHAPE, reported alongside the
per-layer inference and not instead of it.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import population_block  # noqa: E402


def scan_statistic(effects, min_w: int = 2):
    """Largest size-weighted contiguous window: max over i<=j of sum(effects[i..j]) / sqrt(len)."""
    n = len(effects)
    best, span = float("-inf"), None
    for i in range(n):
        run = 0.0
        for j in range(i, n):
            run += effects[j]
            w = j - i + 1
            if w < min_w:
                continue
            v = run / (w ** 0.5)
            if v > best:
                best, span = v, (i, j)
    return best, span


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True, help="advbench_layer_profile.json")
    ap.add_argument("--key", default="paired_vs_baseline")
    ap.add_argument("--effect-field", default="delta_cluster_mean")
    ap.add_argument("--n-perm", type=int, default=100000)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--bank", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = json.load(open(sorted(glob.glob(args.profile))[-1]))
    pv = d[args.key]
    layers = []
    for k, v in pv.items():
        if not isinstance(v, dict) or v.get(args.effect_field) is None:
            continue
        if not k.startswith("L"):          # cN entries are the matched controls
            continue
        layers.append((int(k[1:]), k, float(v[args.effect_field])))
    layers.sort()
    depths = [x[0] for x in layers]
    eff = [x[2] for x in layers]

    obs, span = scan_statistic(eff)
    rng = random.Random(args.seed)
    perm = list(eff)
    hits = 0
    for _ in range(args.n_perm):
        rng.shuffle(perm)
        if scan_statistic(perm)[0] >= obs:
            hits += 1
    p = (hits + 1) / (args.n_perm + 1)

    out = {
        "test": "scan statistic over contiguous layer windows; null = layer-label exchangeability",
        "population": population_block(args.bank),
        "profile": os.path.abspath(sorted(glob.glob(args.profile))[-1]),
        "effect_field": args.effect_field,
        "layers": depths, "effects": eff,
        "observed_statistic": obs,
        "observed_window": {"layers": [depths[span[0]], depths[span[1]]],
                            "n_layers": span[1] - span[0] + 1,
                            "members": [layers[i][1] for i in range(span[0], span[1] + 1)]},
        "n_perm": args.n_perm, "p_perm": p,
        "conditions_on": "the observed multiset of per-layer effects; this tests ARRANGEMENT, not "
                         "whether the effects are real. Report beside the per-layer inference.",
        "provenance": {"argv": sys.argv,
                       "git_commit": subprocess.run(["git", "rev-parse", "HEAD"],
                                                    capture_output=True, text=True).stdout.strip()},
    }
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print("layers :", depths)
    print("effects:", [round(e, 4) for e in eff])
    print(f"observed window = L{out['observed_window']['layers'][0]}-L{out['observed_window']['layers'][1]} "
          f"({out['observed_window']['n_layers']} layers), statistic = {obs:.5f}")
    print(f"permutation p (label exchangeability, {args.n_perm} draws) = {p:.5f}")
    print(f"[profile] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
