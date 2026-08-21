"""cluster_power.py — can this design detect ANYTHING at cluster level, and if so how big?

WHY. Across five layers the `d_naive`-vs-rung comparison returned cluster sign-flip p of
0.375 / 0.125 / 0.625 / 0.156 / 0.0625, with L8 and L13 sitting EXACTLY at their attainable floors
(2/2^k for k informative clusters). L13 was 6 up and 0 down -- the most one-sided outcome its cluster
structure permits -- and still could not reach 0.05. That is a property of the DESIGN, not of the
effect, and it should be quantified before anyone spends more GPU on this comparison.

The floor alone already says a lot: with k informative domains the smallest attainable two-sided p is
2/2^k, so k >= 6 is REQUIRED for any chance of p <= 0.05, and k >= 6 with every one of them pointing
the same way. Observed k was 4, 4, 4, 6, 5.

But the floor is necessary, not sufficient. This script simulates the actual test: inject a true
per-prompt effect delta, using the REAL domain sizes and the REAL baseline refusal structure, and
measure how often the cluster sign-flip test rejects. That converts "underpowered" from an adjective
into a minimum detectable effect.

NO GENERATION TEXT IS READ -- domain labels and numeric scores only.
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
from common import read_jsonl  # noqa: E402


def _rows(pat):
    m = {}
    for d in sorted(glob.glob(pat)):
        f = os.path.join(d, "results.jsonl")
        if os.path.exists(f):
            for r in read_jsonl(f):
                if r.get("strongreject_score") is not None:
                    m[r["prompt_id"]] = r
    return m


def cluster_p(nets, n, obs):
    import itertools
    inform = [v for v in nets if v != 0]
    if not inform:
        return 1.0
    if len(inform) <= 20:
        cnt = tot = 0
        for signs in itertools.product((1, -1), repeat=len(inform)):
            s = sum(sg * v for sg, v in zip(signs, inform)) / n
            tot += 1
            if abs(s) >= abs(obs) - 1e-12:
                cnt += 1
        return cnt / tot
    return 1.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", default="outputs/boombness/judge/abg_base_*")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--n-sim", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    base = _rows(args.baseline)
    ids = sorted(base)
    dom = {}
    for i in ids:
        dom.setdefault(base[i].get("domain"), []).append(i)
    sizes = {d: len(v) for d, v in dom.items()}
    # only prompts the baseline REFUSES can flip to compliance -- that is where every observed
    # flip came from, so the simulation must respect it or it will overstate power.
    refus = {d: sum(1 for i in v if base[i].get("strongreject_score", 0) < args.threshold)
             for d, v in dom.items()}
    n = len(ids)

    rng = random.Random(args.seed)
    curve = {}
    for delta in (0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12):
        rej = 0
        for _ in range(args.n_sim):
            nets = []
            for d, v in dom.items():
                # each refusable prompt flips with probability delta (one-sided true effect)
                k = sum(1 for _ in range(refus[d]) if rng.random() < delta)
                nets.append(k)
            obs = sum(nets) / n
            if cluster_p(nets, n, obs) <= 0.05:
                rej += 1
        curve[str(delta)] = rej / args.n_sim

    mde = None
    for d in sorted(curve, key=float):
        if curve[d] >= 0.80:
            mde = float(d)
            break

    doc = {"question": "at what true effect size can the cluster sign-flip test reach p<=0.05 here?",
           "n_prompts": n, "n_domains": len(dom),
           "domain_sizes": sizes, "refusable_per_domain": refus,
           "attainable_floor_by_informative_clusters": {str(k): 2.0 / (2 ** k)
                                                        for k in range(1, 9)},
           "power_curve_true_delta_to_power": curve,
           "minimum_detectable_effect_at_80pct_power": mde,
           "observed_effects_for_comparison": {"L6": 0.0081, "L8": 0.0141, "L10": -0.0040,
                                               "L12": 0.0222, "L13": 0.0121},
           "reading": ("k informative clusters give an attainable floor of 2/2^k, so k>=6 all pointing "
                       "one way is REQUIRED before p<=0.05 is even possible; observed k was 4,4,4,6,5. "
                       "The simulation adds the sufficient half."),
           "provenance": {"argv": sys.argv, "git_commit": subprocess.run(
               ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}}
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=2)

    print(f"  n={n} prompts, G={len(dom)} domains, refusable={sum(refus.values())}")
    print(f"  attainable floor: k=4 -> {2/16:.4f}   k=5 -> {2/32:.4f}   k=6 -> {2/64:.4f}")
    print(f"  {'true delta':>11s} {'power':>7s}")
    for d in sorted(curve, key=float):
        print(f"  {float(d):11.3f} {curve[d]:7.3f}")
    print(f"\n  minimum detectable effect @80% power: {mde}")
    print(f"  largest effect observed in this comparison: +0.0222 (L12)")
    print(f"\n[power] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
