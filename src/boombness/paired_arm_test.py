"""paired_arm_test.py — is arm A different from arm B, on the same prompts?

WHY SEPARATE FROM `effect_decomposition.py`. That script compares an arm to the BASELINE. The dose
ladder needs a different question: two INTERVENTIONS matched on dose and on cosine-with-`d_surface`,
compared to each other. Going through the baseline twice and differencing would double the variance
and throw away the pairing, which is the whole point -- both arms see the identical 495 prompts.

Domain-clustered (G=16 on AdvBench), because prompts within a domain are not independent; the sprint
has already had one result retracted for pseudo-replication.

⛔ THE PERCENTILE CLUSTER BOOTSTRAP HERE IS ANTI-CONSERVATIVE, AND WAS QUOTED AS IF IT WERE NOT
(R-27, audit #7). It resamples the 16 domains correctly, but almost all of them contribute a net of
ZERO: at L8 only **4** domains carried a nonzero net. With 4 informative clusters the smallest p any
cluster-level test can return is 2/2^4 = **0.125**, yet the percentile bootstrap reported 0.021. So
`p_bootstrap` was reporting significance for data that cannot be significant at the level it claims to
cluster on. It is retained for continuity, but `p_cluster_signflip` and `n_informative_clusters` are
now computed alongside it and are the numbers to quote.

The sign-flip randomization is the right test here: under the null that the two arms are exchangeable,
each CLUSTER's net contribution is equally likely to carry either sign, so flipping cluster signs
generates the exact null distribution at the level the data are actually correlated.

ALSO REPORTS THE DISCORDANT COUNT, because that is what the inference actually rests on. A delta of
+0.0141 over 495 prompts sounds sturdier than "8 up, 1 down among 9 prompts that differ at all". Both
are the same fact; only the second makes the fragility visible. The exact sign test on the discordant
pairs is printed next to the bootstrap for that reason.
"""
from __future__ import annotations

import argparse
import glob
import json
import math
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


def _sign_test(up, down):
    n = up + down
    if n == 0:
        return 1.0
    k = min(up, down)
    c = sum(math.comb(n, i) for i in range(0, k + 1))
    return min(1.0, 2 * c / (2 ** n))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-a", required=True)
    ap.add_argument("--arm-b", required=True)
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=20260821)
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    A, B = _rows(args.arm_a), _rows(args.arm_b)
    if not A or not B:
        print(f"[paired] missing run: A={len(A)} rows, B={len(B)} rows", file=sys.stderr)
        return 2
    ids = sorted(set(A) & set(B))
    suc = lambda r: 1 if r["strongreject_score"] >= args.threshold else 0
    diff = {i: suc(A[i]) - suc(B[i]) for i in ids}
    up = sum(1 for v in diff.values() if v > 0)
    down = sum(1 for v in diff.values() if v < 0)

    dom = {}
    for i in ids:
        dom.setdefault(A[i].get("domain"), []).append(diff[i])
    doms = sorted(dom)
    rng = random.Random(args.seed)
    bs = []
    for _ in range(args.n_boot):
        s = [v for _ in doms for v in dom[rng.choice(doms)]]
        bs.append(sum(s) / len(s))
    bs.sort()
    lo, hi = bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs))]
    p_boot = 2 * min(sum(1 for b in bs if b <= 0), sum(1 for b in bs if b >= 0)) / len(bs)

    # ---- cluster-level sign-flip randomization (the honest test; see the docstring)
    nets = {d: sum(v) for d, v in dom.items()}
    inform = [d for d, v in nets.items() if v != 0]
    n_inf = len(inform)
    obs = sum(nets.values()) / len(ids)
    if n_inf <= 20:                                    # exact enumeration
        import itertools
        cnt = tot = 0
        base_nets = [nets[d] for d in inform]
        for signs in itertools.product((1, -1), repeat=n_inf):
            s = sum(sg * v for sg, v in zip(signs, base_nets)) / len(ids)
            tot += 1
            if abs(s) >= abs(obs) - 1e-12:
                cnt += 1
        p_flip = cnt / tot
        exact = True
    else:
        rr = random.Random(args.seed)
        cnt = 0
        for _ in range(args.n_boot):
            s = sum((1 if rr.random() < 0.5 else -1) * nets[d] for d in inform) / len(ids)
            if abs(s) >= abs(obs) - 1e-12:
                cnt += 1
        p_flip = cnt / args.n_boot
        exact = False
    min_attainable = 2.0 / (2 ** n_inf) if n_inf else 1.0

    doc = {"arm_a": {"label": args.label_a, "glob": args.arm_a},
           "arm_b": {"label": args.label_b, "glob": args.arm_b},
           "n": len(ids), "n_clusters": len(doms),
           "delta_a_minus_b": sum(diff.values()) / len(ids),
           "net": sum(diff.values()), "n_discordant": up + down,
           "up": up, "down": down,
           "ci95_domain_clustered": [lo, hi],
           "p_bootstrap": p_boot,
           "p_bootstrap_WARNING": "anti-conservative with few informative clusters; see "
                                  "p_cluster_signflip (R-27)",
           "n_informative_clusters": n_inf,
           "informative_cluster_nets": {d: nets[d] for d in inform},
           "p_cluster_signflip": p_flip,
           "p_cluster_signflip_exact": exact,
           "min_attainable_cluster_p": min_attainable,
           "significant_at_cluster_level": bool(p_flip <= 0.05),
           "p_exact_sign_test_on_discordant": _sign_test(up, down),
           "note": "the inference rests on the %d discordant prompts, not on %d; the sign test is "
                   "the assumption-free companion to the bootstrap" % (up + down, len(ids)),
           "provenance": {"argv": sys.argv, "git_commit": subprocess.run(
               ["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()}}
    with open(args.out, "w") as f:
        json.dump(doc, f, indent=2)

    print(f"  {args.label_a} - {args.label_b}: delta={doc['delta_a_minus_b']:+.4f} "
          f"net={doc['net']:+d}  n={doc['n']} G={doc['n_clusters']}")
    print(f"    discordant={doc['n_discordant']} (up={up}, down={down})")
    print(f"    CI95 (domain-clustered) = [{lo:+.4f}, {hi:+.4f}]   bootstrap p={p_boot:.4f} "
          f"(anti-conservative)")
    print(f"    informative clusters={n_inf}/{len(doms)}  min attainable cluster p="
          f"{min_attainable:.4f}")
    print(f"    CLUSTER sign-flip p={p_flip:.4f}{'' if exact else ' (MC)'}   "
          f"significant at cluster level: {p_flip <= 0.05}")
    print(f"    exact sign test on discordant pairs: p={doc['p_exact_sign_test_on_discordant']:.4f}")
    print(f"\n[paired] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
