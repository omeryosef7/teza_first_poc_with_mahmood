"""Regenerate report §4b's corrected whole-answer comprehension figures from the run dirs.

WHY (2026-08-23). `outputs/boombness/section4b_whole_answer.json` carries `provenance.argv == ["-"]`:
it was HAND-AUTHORED. Its numbers are the ones the report now cites to supersede the readout R-6
withdrew -- including the headline "+0.2795, p 0.00099" that this session promoted into §4b's banner a
tick earlier. A figure with no script behind it is exactly the Q5 defect, and promoting it made the
exposure worse rather than better.

This script recomputes those numbers from the committed run dirs and refuses if they do not match.
Pairing is on `prompt_id`; the estimand is the paired arm-minus-baseline mean over `comprehension_usage`
rows, clustered on `domain`.
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

BASE = "outputs/boombness/score_behavior/wa_base_20260818_184457_3887695"
ARMS = {
    "project_out_d_surface": "outputs/boombness/score_behavior/wa_projout_20260818_185458_3888975",
    "Dctrl_double_random": "outputs/boombness/score_behavior/wa_Dctrl_20260818_185458_3888977",
}
PUBLISHED = "outputs/boombness/section4b_whole_answer.json"


def rows(run, kind="comprehension_usage"):
    # A run without DONE.json is an INCOMPLETE run; using one silently mixes a partial arm into a
    # comparison. wa_D_20260818_184457_3887694 in this same directory has no DONE.json.
    if not os.path.exists(os.path.join(run, "DONE.json")):
        raise SystemExit(f"[4b] REFUSING: {run} has no DONE.json -- incomplete run")
    out = {}
    with open(os.path.join(run, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != kind:
                continue
            out[r["prompt_id"]] = (r["comprehension_logodds"], r["domain"])
    return out


def cluster_stats(deltas_by_domain):
    means = [sum(v) / len(v) for v in deltas_by_domain.values()]
    k = len(means)
    m = sum(means) / k
    var = sum((x - m) ** 2 for x in means) / (k - 1)
    se = math.sqrt(var / k)
    t = m / se if se else float("inf")
    # two-sided t with k-1 df, via the incomplete beta (no scipy dependency)
    df = k - 1
    x = df / (df + t * t)
    p = _betainc(df / 2.0, 0.5, x)
    tcrit = _tcrit95(df)
    return m, (m - tcrit * se, m + tcrit * se), p, k


def _betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(0, 200):
        m2 = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m2 * (b - m2) * x) / ((a + 2 * m2 - 1) * (a + 2 * m2))
        else:
            num = -((a + m2) * (a + b + m2) * x) / ((a + 2 * m2) * (a + 2 * m2 + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = 1e-30 if abs(c) < 1e-30 else c
        f *= c * d
        if abs(1.0 - c * d) < 1e-12:
            break
    return front * (f - 1.0)


def _tcrit95(df):
    lo, hi = 0.0, 100.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if _betainc(df / 2.0, 0.5, df / (df + mid * mid)) > 0.05:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/boombness/section4b_recompute.json")
    ap.add_argument("--tol", type=float, default=5e-4)
    a = ap.parse_args()

    base = rows(BASE)
    published = json.load(open(PUBLISHED))
    result, mismatches = {}, []
    for name, run in ARMS.items():
        arm = rows(run)
        common = sorted(set(base) & set(arm))
        by_dom = defaultdict(list)
        for pid in common:
            by_dom[base[pid][1]].append(arm[pid][0] - base[pid][0])
        m, ci, p, k = cluster_stats(by_dom)
        result[name] = {"delta": m, "ci95_domain_clustered": list(ci), "p_vs_0": p,
                        "n": len(common), "n_clusters": k}
        pub = published["arms"][name]["comprehension"]
        for field, got, want in (("delta", m, pub["delta"]),
                                 ("p_vs_0", p, pub["p_vs_0"]),
                                 ("n", len(common), pub["n"])):
            if abs(got - want) > a.tol:
                mismatches.append(f"{name}.{field}: recomputed {got!r} vs published {want!r}")
        print(f"  {name:26s} delta {m:+.4f}  CI [{ci[0]:+.4f}, {ci[1]:+.4f}]  "
              f"p {p:.5f}  n {len(common)}  k {k}")

    json.dump({"plan_section": "2.6 / report 4b",
               "regenerates": PUBLISHED,
               "estimand": "paired arm-minus-baseline comprehension_logodds, clustered on domain",
               "arms": result,
               "provenance": {"argv": sys.argv}},
              open(a.out, "w"), indent=1)
    print(f"[4b] -> {a.out}")
    if mismatches:
        print("[4b] MISMATCH vs the hand-authored artifact:", file=sys.stderr)
        for m in mismatches:
            print("   " + m, file=sys.stderr)
        return 1
    print("[4b] recomputed figures match the published artifact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
