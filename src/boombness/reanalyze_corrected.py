"""reanalyze_corrected.py — the tick-7 claims, redone the way the audit says they must be.

The 4-hourly audit confirmed 25 findings, several of which invalidate the tick-7 headline. This
script recomputes the same contrast under the corrections, so the retraction is quantitative
rather than a shrug:

  (1) QUERY KIND IS NOT A FREE CHOICE. Tick 7 restricted to `query_kind=behavioral` without
      saying so or why. The audit showed the mid-band "null" is specific to that subset: under
      the other two query kinds the same band is significantly NEGATIVE, and the late-layer
      headline collapses from +0.133 to +0.047 when all three are pooled. Every number here is
      reported PER QUERY KIND and pooled, never silently restricted.

  (2) THE "NULL" WAS A CANCELLATION. C-A in the mid band depends on n_examples and CHANGES SIGN
      (positive at 1-2 demos, significantly negative at 8-16). Pooling over the example mix
      averages that to ~0. So the layer profile is reported as a LAYER x N_EXAMPLES surface.

  (3) THE UNIT OF ANALYSIS IS THE DOMAIN, NOT THE FAMILY. The "30 families" are 6 domains x 5
      nested example counts, pooled over 2 splits to 60 - pseudo-replication. With a domain ICC
      around 0.5 the effective n is nearer 6 than 60. t values are therefore recomputed with a
      CLUSTER-ROBUST standard error clustered on domain, and the naive value is printed beside
      it so the inflation is visible.

  (4) A NULL NEEDS AN INTERVAL, NOT p>0.05. Every "no effect" layer gets a confidence interval
      and an explicit statement of the smallest effect the data could exclude.

  (5) MULTIPLICITY. 32 layers were tested. Holm-corrected significance is reported.

Nothing here re-runs the model; it reads an extract run's results.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


def paired_by_family(rows: List[Dict], col: str, hi_cell: str, lo_cell: str
                     ) -> List[Tuple[str, str, int, float]]:
    """[(domain, family_id, n_examples, hi-lo)] paired within family."""
    hi = {r["family_id"]: r for r in rows if r["cell"] == hi_cell and col in r}
    lo = {r["family_id"]: r for r in rows if r["cell"] == lo_cell and col in r}
    out = []
    for f, rh in hi.items():
        rl = lo.get(f)
        if rl is None:
            continue
        out.append((rh["domain"], f, rh["n_examples"], rh[col] - rl[col]))
    return out


def cluster_robust(diffs: List[Tuple[str, str, int, float]]) -> Dict[str, float]:
    """Mean, naive SE, and a domain-clustered SE (CR1) for a paired difference.

    Clustering on domain because the families are NOT independent: they are 6 domains crossed
    with nested example counts and two splits, so treating 60 rows as 60 independent draws
    understates the SE by roughly sqrt(1 + (m-1) * ICC).
    """
    vals = [d for _, _, _, d in diffs]
    n = len(vals)
    if n < 2:
        return {"n": n, "mean": float("nan"), "se_naive": float("nan"),
                "se_cluster": float("nan"), "t_naive": float("nan"),
                "t_cluster": float("nan"), "n_clusters": 0}
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / (n - 1)
    se_naive = math.sqrt(var / n)

    by_dom: Dict[str, List[float]] = collections.defaultdict(list)
    for dom, _, _, d in diffs:
        by_dom[dom].append(d)
    G = len(by_dom)
    # CR1 sandwich for the mean: sum of squared cluster sums / n^2, with the usual G/(G-1) bump.
    ss = sum((sum(v - mean for v in vs)) ** 2 for vs in by_dom.values())
    se_cluster = math.sqrt(ss / (n * n) * (G / max(G - 1, 1))) if G > 1 else float("nan")
    return {"n": n, "n_clusters": G, "mean": mean,
            "se_naive": se_naive, "se_cluster": se_cluster,
            "t_naive": mean / se_naive if se_naive > 0 else float("nan"),
            "t_cluster": mean / se_cluster if se_cluster and se_cluster > 0 else float("nan")}


def holm(pvals: Dict[int, float], alpha: float = 0.05) -> Dict[int, bool]:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, prev_reject = {}, True
    for i, (k, p) in enumerate(items):
        thr = alpha / (m - i)
        rej = prev_reject and (p <= thr)
        out[k] = rej
        prev_reject = rej
    return out


def two_sided_p(t: float, df: int) -> float:
    if not math.isfinite(t):
        return 1.0
    try:
        from scipy import stats
        return float(2 * stats.t.sf(abs(t), df))
    except Exception:
        return float(math.erfc(abs(t) / math.sqrt(2)))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", required=True)
    ap.add_argument("--metric", default="d_surface|cos")
    ap.add_argument("--layers", default="0,4,8,12,16,18,20,24,28,31")
    ap.add_argument("--hi", default="C")
    ap.add_argument("--lo", default="A")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.run:
        require_done(args.run, allow_partial=args.allow_partial)

    rows = read_jsonl(os.path.join(args.run, "results.jsonl"))
    fin = [r for r in rows if r.get("is_final_occurrence") and r["bank_block"] == "core2x2"
           and r["n_examples"] > 0]
    layers = [int(x) for x in args.layers.split(",")]
    metric, stat = args.metric.split("|")

    def col(L):
        return f"{metric}|L{L}|{stat}"

    qks = sorted({r["query_kind"] for r in fin})
    print(f"[reanalyze] {len(fin)} rows, query kinds {qks}")
    print(f"[reanalyze] contrast {args.hi} - {args.lo}, metric {args.metric}\n")

    report: Dict[str, object] = {"run": os.path.abspath(args.run), "metric": args.metric,
                                 "contrast": f"{args.hi}-{args.lo}", "query_kinds": qks}

    # ---- (1) per query kind and pooled ---------------------------------------- #
    print("=== C-A BY QUERY KIND (the tick-7 table used ONLY 'behavioral') ===")
    hdr = f"{'L':>3} " + " ".join(f"{q[:14]:>16s}" for q in qks) + f" {'POOLED':>16s}"
    print(hdr)
    per_qk: Dict[str, Dict[int, Dict]] = {q: {} for q in qks}
    pooled: Dict[int, Dict] = {}
    for L in layers:
        cells = []
        for q in qks:
            sub = [r for r in fin if r["query_kind"] == q]
            st = cluster_robust(paired_by_family(sub, col(L), args.hi, args.lo))
            per_qk[q][L] = st
            cells.append(f"{st['mean']:+.4f}(t{st['t_cluster']:+.1f})")
        st = cluster_robust(paired_by_family(fin, col(L), args.hi, args.lo))
        pooled[L] = st
        cells.append(f"{st['mean']:+.4f}(t{st['t_cluster']:+.1f})")
        print(f"{L:>3} " + " ".join(f"{c:>16s}" for c in cells))
    report["by_query_kind"] = {q: {str(L): v for L, v in d.items()} for q, d in per_qk.items()}
    report["pooled"] = {str(L): v for L, v in pooled.items()}

    # ---- (2) the layer x n_examples surface ----------------------------------- #
    print("\n=== C-A BY LAYER x N_EXAMPLES (pooled over query kinds) ===")
    print("    the tick-7 'null carry band' was this surface averaged over the example mix")
    ns = sorted({r["n_examples"] for r in fin})
    print(f"{'L':>3} " + " ".join(f"{'n=' + str(n):>15s}" for n in ns))
    surface: Dict[int, Dict[int, Dict]] = {}
    for L in layers:
        surface[L] = {}
        cells = []
        for n in ns:
            sub = [r for r in fin if r["n_examples"] == n]
            st = cluster_robust(paired_by_family(sub, col(L), args.hi, args.lo))
            surface[L][n] = st
            cells.append(f"{st['mean']:+.4f}(t{st['t_cluster']:+.1f})")
        print(f"{L:>3} " + " ".join(f"{c:>15s}" for c in cells))
    report["layer_x_n_examples"] = {str(L): {str(n): v for n, v in d.items()}
                                    for L, d in surface.items()}

    # ---- (3)(4)(5) inference on the pooled profile ---------------------------- #
    print("\n=== INFERENCE ON THE POOLED PROFILE (naive vs domain-clustered, Holm over layers) ===")
    pv = {}
    for L in layers:
        st = pooled[L]
        pv[L] = two_sided_p(st["t_cluster"], max(st["n_clusters"] - 1, 1))
    rej = holm(pv)
    # AUDIT 11: this script computed its p from t(G-1) and then built the printed CI and the MDE
    # with a hardcoded 1.96 -- the NORMAL multiplier. With G=6 the correct value is t(5)=2.5706, so
    # every clustered interval and every "what the null can exclude" bound was 31% too narrow, and
    # the CI contradicted the p-value beside it. Same defect class as the analyze_g8 fix.
    from analyze_g8 import t_crit
    _G = pooled[layers[0]].get("n_clusters", 6) if layers else 6
    TCRIT = t_crit(max(_G - 1, 1))
    print(f"[reanalyze] clustered CI multiplier = t({max(_G-1,1)}) = {TCRIT:.4f} "
          f"(was a hardcoded 1.96 -> intervals were {100*(TCRIT/1.96-1):.0f}% too narrow)")
    print(f"{'L':>3} {'mean':>9} {'se_naive':>9} {'se_clust':>9} {'t_naive':>8} "
          f"{'t_clust':>8} {'p_clust':>9} {'Holm':>6} {'95% CI (clustered)':>24}")
    for L in layers:
        st = pooled[L]
        lo = st["mean"] - TCRIT * st["se_cluster"]
        hi = st["mean"] + TCRIT * st["se_cluster"]
        print(f"{L:>3} {st['mean']:>+9.4f} {st['se_naive']:>9.4f} {st['se_cluster']:>9.4f} "
              f"{st['t_naive']:>+8.1f} {st['t_cluster']:>+8.1f} {pv[L]:>9.4f} "
              f"{'YES' if rej[L] else 'no':>6} {f'[{lo:+.4f}, {hi:+.4f}]':>24}")
    report["holm_rejected"] = {str(L): bool(rej[L]) for L in layers}
    report["p_clustered"] = {str(L): pv[L] for L in layers}

    # ---- what a "null" layer can actually exclude ----------------------------- #
    print("\n=== WHAT THE 'NULL' LAYERS CAN EXCLUDE (plan: a null needs an interval) ===")
    ref_L = max(layers, key=lambda L: abs(pooled[L]["mean"]))
    ref = abs(pooled[ref_L]["mean"])
    for L in layers:
        st = pooled[L]
        if rej[L]:
            continue
        mde = TCRIT * st["se_cluster"]
        print(f"  L{L:<3} not significant. |CI| bound = {mde:.4f} = "
              f"{100 * mde / ref:.0f}% of the largest observed effect (L{ref_L}, {ref:.4f}). "
              f"{'Cannot exclude an effect of that size.' if mde > 0.5 * ref else 'Excludes effects above that bound.'}")
    out = args.out or os.path.join(args.run, "analysis", "reanalysis_corrected.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[reanalyze] -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
