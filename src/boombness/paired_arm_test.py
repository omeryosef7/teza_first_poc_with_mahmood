"""paired_arm_test.py — is arm A different from arm B, on the same prompts?

WHY SEPARATE FROM `effect_decomposition.py`. That script compares an arm to the BASELINE. The dose
ladder needs a different question: two INTERVENTIONS matched on dose and on cosine-with-`d_surface`,
compared to each other. Going through the baseline twice and differencing would double the variance
and throw away the pairing, which is the whole point -- both arms see the identical 495 prompts.

Domain-clustered (G=16 on AdvBench), because prompts within a domain are not independent; the sprint
has already had one result retracted for pseudo-replication.

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

    doc = {"arm_a": {"label": args.label_a, "glob": args.arm_a},
           "arm_b": {"label": args.label_b, "glob": args.arm_b},
           "n": len(ids), "n_clusters": len(doms),
           "delta_a_minus_b": sum(diff.values()) / len(ids),
           "net": sum(diff.values()), "n_discordant": up + down,
           "up": up, "down": down,
           "ci95_domain_clustered": [lo, hi], "p_bootstrap": p_boot,
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
    print(f"    CI95 (domain-clustered) = [{lo:+.4f}, {hi:+.4f}]   bootstrap p={p_boot:.4f}")
    print(f"    exact sign test on discordant pairs: p={doc['p_exact_sign_test_on_discordant']:.4f}")
    print(f"\n[paired] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
