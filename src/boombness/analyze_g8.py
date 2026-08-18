"""analyze_g8.py — plan §8: does comprehension of the codeword mapping scale with demonstration count?

Open as "not aggregated" since the mid-session sanity check. Two questions, one of which is a control:

  (a) BASELINE CURVE. `comprehension_logodds` = log p(coded) - log p(literal) at the answer position,
      as a function of n_examples in {0,1,2,4,8,16}, per condition. The design is balanced 12 per
      (n_examples x condition) cell over 6 domains, so the curve is not confounded by cell counts.

  (b) THE n_examples=0 LEVEL IS NOT USABLE AS A FLOOR, and this script proves that rather than
      assuming it. The intent was: with zero demonstrations the mapping is never taught, so that level
      measures prior lexical association. But the bank contains exactly ONE distinct zero-demo prompt
      per condition, replicated 12x -- `prompt_sha16` has a single unique value while `domain` varies.
      So the level has n_effective = 1, its between-domain SD is exactly 0 (there is nothing to vary),
      and a cluster CI computed there is [m, m] -- a degenerate point reported as an interval.
      Worse, both branches sit at ~1e-6 absolute probability, so the log-odds is a ratio of two
      near-zero probabilities. Every cell therefore carries `n_effective`, degenerate levels are
      EXCLUDED from the trend fit (they would otherwise contribute 12 of 72 points from one prompt),
      and their CI is reported as null rather than as a zero-width interval.

  (c) INTERACTION WITH THE INTERVENTIONS. §2.6 established that the -0.25 arm degrades comprehension.
      If that damage shrinks as demonstrations accumulate, the intervention is competing with
      in-context evidence rather than destroying the representation. Deltas are PAIRED by prompt_id
      against the unintervened baseline, so prompt difficulty cancels.

Inference is domain-clustered throughout (G=6), matching G2/G9. With 6 clusters this uses a
t reference on G-1 = 5 df, NOT a normal reference: a normal reference is anticonservative at this
cluster count.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics as st
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402

COL = "comprehension_logodds"


def t_sf(t: float, df: int) -> float:
    """Two-sided survival for Student-t via the regularized incomplete beta (no scipy in this env)."""
    x = df / (df + t * t)
    return _betainc(df / 2.0, 0.5, x)


def _betainc(a: float, b: float, x: float) -> float:
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    f, c, d = 1.0, 1.0, 0.0
    for i in range(200):
        m = i // 2
        if i == 0: num = 1.0
        elif i % 2 == 0: num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else: num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = 1e-30 if abs(d) < 1e-30 else 1.0 / d
        c = 1.0 + num / (1e-30 if abs(c) < 1e-30 else c)
        f *= c * d
        if abs(1 - c * d) < 1e-10: break
    return front * (f - 1)


def t_crit(df: int, alpha: float = 0.05) -> float:
    """Two-sided t critical value, obtained by inverting `t_sf` by bisection.

    The first version hardcoded `2.571 if G==6 else 2.776 if G==5 else 2.0`. The 2.0 fallback is the
    NORMAL value and is wrong for every other df -- at df=3 the truth is 3.182 and at df=2 it is
    4.303, so a 3- or 4-cluster CI would have come out less than half its correct width. No number in
    this sprint is affected (G=6 throughout), but it is the same defect audit 10 found in
    analyze_g9.py: a normal-shaped reference standing in for a small-df t. Computed now, not tabled.
    """
    lo, hi = 0.0, 200.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_sf(mid, df) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def cluster_mean_ci(vals_by_cluster: Dict[str, List[float]], alpha=0.05, n_effective=None):
    """Cluster-level mean +/- t(G-1) SE. The unit of inference is the DOMAIN, not the prompt.

    A zero between-cluster SD is NOT a tight interval -- it means every cluster saw the same prompt.
    That case returns ci=None and degenerate=True instead of the zero-width interval [m, m], which
    the first version of this script printed and which reads as an extraordinarily precise estimate.
    """
    means = [st.mean(v) for v in vals_by_cluster.values() if v]
    G = len(means)
    base = {"n_clusters": G, "n_effective": n_effective}
    if G < 2:
        return {**base, "mean": means[0] if means else float("nan"), "se": None,
                "ci": None, "p_vs_0": None, "degenerate": True,
                "degenerate_reason": f"{G} cluster(s) with data"}
    m = st.mean(means)
    sd = st.stdev(means)
    if sd == 0 or (n_effective is not None and n_effective < 2):
        return {**base, "mean": m, "se": 0.0 if sd == 0 else None, "ci": None, "p_vs_0": None,
                "degenerate": True,
                "degenerate_reason": ("between-cluster SD is exactly 0"
                                      if sd == 0 else f"n_effective={n_effective} distinct prompts")}
    se = sd / math.sqrt(G)
    tcrit = t_crit(G - 1)
    t = m / se
    return {**base, "mean": m, "se": se, "ci": [m - tcrit * se, m + tcrit * se],
            "p_vs_0": t_sf(abs(t), G - 1), "degenerate": False}


def n_eff(rows) -> int:
    """Distinct prompts, not row count. A level replicated across a metadata field is still n=1."""
    return len({r.get("prompt_sha16") for r in rows if r.get("prompt_sha16") is not None}) or len(rows)


def by_cluster(rows, key, cluster="domain"):
    d = collections.defaultdict(list)
    for r in rows:
        if r.get(key) is not None:
            d[r.get(cluster)].append(r[key])
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, help="unintervened score_behavior run")
    ap.add_argument("--arms", nargs="*", default=[], help="intervened runs, as label=path")
    ap.add_argument("--cluster-by", default="domain")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    require_done(args.baseline)
    base = [r for r in read_jsonl(os.path.join(args.baseline, "results.jsonl"))
            if r.get("readout") == "comprehension"]
    if not base:
        raise SystemExit("[G8] baseline run has no comprehension rows")
    bcfg = json.load(open(os.path.join(args.baseline, "config.json")))
    if (bcfg.get("args", bcfg) or {}).get("intervene"):
        raise SystemExit("[G8] --baseline run carries an --intervene spec; it is not a baseline")

    levels = sorted({r["n_examples"] for r in base})
    conds = sorted({r["condition"] for r in base})

    # ---- balance check: an unbalanced cell grid makes the curve uninterpretable ---------- #
    grid = collections.Counter((r["n_examples"], r["condition"]) for r in base)
    counts = sorted({grid.get((n, c), 0) for n in levels for c in conds})
    balanced = len(counts) == 1
    print(f"[G8] baseline {len(base)} comprehension rows; levels={levels}; "
          f"{len(conds)} conditions; cell counts {counts} -> "
          f"{'BALANCED' if balanced else 'UNBALANCED (curve is confounded by cell size)'}")

    report = {"plan_section": "8", "baseline": os.path.abspath(args.baseline),
              "levels": levels, "conditions": conds, "balanced_cell_grid": balanced,
              "cell_counts": counts, "cluster_by": args.cluster_by, "curve": {}, "arms": {}}

    # ---- (a)+(b) the baseline curve, per condition ------------------------------------- #
    print(f"\n[G8] baseline {COL} by n_examples (mean over {args.cluster_by} clusters, "
          f"+/- t(5) SE):")
    hdr = f"{'condition':22s} " + " ".join(f"{'n='+str(n):>16s}" for n in levels)
    print(hdr)
    for c in conds:
        cells = {}
        line = f"{c[:22]:22s} "
        for n in levels:
            rows = [r for r in base if r["condition"] == c and r["n_examples"] == n]
            ne = n_eff(rows)
            cells[str(n)] = cluster_mean_ci(by_cluster(rows, COL, args.cluster_by), n_effective=ne)
            line += f"{cells[str(n)]['mean']:>14.3f}" + ("!!" if cells[str(n)]["degenerate"] else "  ")
        report["curve"][c] = cells
        print(line)

    # ---- which levels are degenerate? computed, not assumed ----------------------------- #
    degen = sorted({n for n in levels
                    if any(report["curve"][c][str(n)]["degenerate"] for c in conds)})
    report["degenerate_levels"] = degen
    report["effective_n_by_level"] = {
        str(n): {c: report["curve"][c][str(n)]["n_effective"] for c in conds} for n in levels}
    if degen:
        print(f"\n[G8] !! DEGENERATE LEVELS n_examples={degen} — excluded from the trend fit.")
        for n in degen:
            ne = {c: report["curve"][c][str(n)]["n_effective"] for c in conds}
            print(f"     n={n}: distinct prompts per condition = {ne} (rows per cell = "
                  f"{counts[0] if balanced else '?'}). The level is one prompt replicated across a "
                  f"metadata field, so its between-cluster SD is 0 and it has no usable interval. "
                  f"It cannot serve as the 'mapping never taught' floor the plan wanted.")

    # slope across levels, computed on log2(1+n) at the CLUSTER level
    fit_levels = [n for n in levels if n not in degen]
    print(f"\n[G8] trend on log2(1+n_examples), cluster-level slopes "
          f"(fitted on n_examples={fit_levels}):")
    report["trend_fitted_on_levels"] = fit_levels
    for c in conds:
        per_dom = collections.defaultdict(list)
        for r in base:
            if r["condition"] == c and r.get(COL) is not None and r["n_examples"] in fit_levels:
                per_dom[r[args.cluster_by]].append((math.log2(1 + r["n_examples"]), r[COL]))
        slopes = []
        for dom, pts in per_dom.items():
            mx = st.mean(p[0] for p in pts); my = st.mean(p[1] for p in pts)
            den = sum((p[0] - mx) ** 2 for p in pts)
            if den > 0:
                slopes.append(sum((p[0] - mx) * (p[1] - my) for p in pts) / den)
        s = cluster_mean_ci({str(i): [v] for i, v in enumerate(slopes)})
        report["curve"][c]["slope_log2"] = s
        ci = (f"CI [{s['ci'][0]:+.4f}, {s['ci'][1]:+.4f}]  p={s['p_vs_0']:.4f}"
              if s["ci"] else f"DEGENERATE ({s['degenerate_reason']})")
        print(f"  {c:24s} slope={s['mean']:+.4f} per doubling  {ci}")

    # ---- (c) intervention damage vs demonstration count, PAIRED by prompt_id ------------ #
    bkey = {(r["prompt_id"], r["condition"]): r for r in base if r.get(COL) is not None}
    for spec in args.arms:
        if "=" not in spec:
            raise SystemExit(f"--arms takes label=path, got {spec!r}")
        label, path = spec.split("=", 1)
        require_done(path)
        arows = [r for r in read_jsonl(os.path.join(path, "results.jsonl"))
                 if r.get("readout") == "comprehension" and r.get(COL) is not None]
        per_level = {}
        n_paired_total = 0
        for n in levels:
            deltas = collections.defaultdict(list)
            for r in arows:
                if r["n_examples"] != n:
                    continue
                b = bkey.get((r["prompt_id"], r["condition"]))
                if b is None:
                    continue
                deltas[r[args.cluster_by]].append(r[COL] - b[COL])
                n_paired_total += 1
            per_level[str(n)] = cluster_mean_ci(
                deltas, n_effective=n_eff([r for r in arows if r["n_examples"] == n]))
        report["arms"][label] = {"run": os.path.abspath(path), "n_paired": n_paired_total,
                                 "delta_by_n_examples": per_level}
        print(f"\n[G8] arm {label}: paired delta vs baseline ({n_paired_total} pairs)")
        for n in levels:
            v = per_level[str(n)]
            if v["ci"] is None:
                print(f"  n={n:<3d} delta={v['mean']:+.4f}  [no interval: {v['degenerate_reason']}]")
            else:
                print(f"  n={n:<3d} delta={v['mean']:+.4f}  "
                      f"CI [{v['ci'][0]:+.4f}, {v['ci'][1]:+.4f}]  p={v['p_vs_0']:.4f}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[G8] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
