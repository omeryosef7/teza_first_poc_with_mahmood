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

  (5) MULTIPLICITY. Holm-corrected significance is reported, over an EXPLICIT family.

      AUDIT T6c: this docstring used to say flatly "32 layers were tested", while `pv` was built
      only over the ~10 layers that happen to be on the command line (`--layers`, default
      0,4,8,12,16,18,20,24,28,31). Code and prose therefore disagreed about m, and the JSON recorded
      neither m nor the rule that produced it, so a reader could not tell which family the
      `holm_rejected` flags belonged to. The consequence is not cosmetic: at m=10 the smallest two
      p-values clear their thresholds, and the report cites "holm_rejected True only at L4 and L31"
      TWICE as its multiplicity backstop for the mid-band claims.

      WHAT THE HONEST FAMILY IS. Not the command line. The extract writes every direction/statistic
      at ALL 32 layers (results.jsonl carries d_surface|L0..L31|cos), the whole profile was looked
      at, and the displayed subset is visibly data-dependent: 0,4,8,...,28 is a stride-4 grid, but
      L18 was added off-grid and L31 kept, i.e. layers were promoted into the table after the
      profile had been seen. A family that is chosen after looking is not a family. So the default
      rule here is `--holm-family available`: the family is every layer for which the requested
      metric column exists in results.jsonl, all of them are actually tested, and Holm runs over
      that full p-vector. `--holm-family displayed` reproduces the old, smaller family for
      comparison; both are always printed side by side and both are written to the JSON along with
      `holm_m` and `holm_family_rule`, so the sensitivity of any conclusion to this choice is on the
      record instead of buried in a default argument.

      Note that "m=32" is NOT the same as "rank the 10 displayed p-values but divide by 32". The
      audit note used the latter (L4 at rank 2 -> alpha/31 = 0.001613 < p = 0.001631, so L4 drops).
      The former is the defensible correction, and it is more powerful, because the 22 layers that
      were never displayed contribute their own p-values to the step-down. Both are reported.

Nothing here re-runs the model; it reads an extract run's results.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import re
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


def holm_table(pvals: Dict[int, float], alpha: float = 0.05, m: Optional[int] = None
               ) -> Dict[int, Dict[str, object]]:
    """Holm step-down, returning the threshold and rank that produced each decision.

    `m` is the FAMILY SIZE and defaults to the number of p-values supplied. It is exposed because
    the family is a claim about which hypotheses were tested, not a property of the dict that
    happens to be in hand (audit T6c: the family here is every layer present in results.jsonl, not
    the subset that reached the printed table). Passing m > len(pvals) reproduces the conservative
    "corrected as if the untested members had been tested and had missed" reading; it is supported
    so the two readings can be printed together, but it is not the default and it is not the
    defensible correction -- if the other hypotheses are testable, test them.
    """
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    if m is None:
        m = len(items)
    if m < len(items):
        raise ValueError(f"Holm family size m={m} is smaller than the {len(items)} p-values given")
    out: Dict[int, Dict[str, object]] = {}
    prev_reject = True
    for i, (k, p) in enumerate(items):
        thr = alpha / (m - i)
        rej = bool(prev_reject and (p <= thr))
        out[k] = {"p": p, "rank": i + 1, "thr": thr, "rejected": rej, "m": m}
        prev_reject = rej
    return out


def holm(pvals: Dict[int, float], alpha: float = 0.05, m: Optional[int] = None) -> Dict[int, bool]:
    return {k: bool(v["rejected"]) for k, v in holm_table(pvals, alpha, m).items()}


def available_layers(rows: Sequence[Dict], metric: str, stat: str) -> List[int]:
    """Every layer index for which `metric|L*|stat` exists in the rows.

    This is the honest Holm family (audit T6c): the extract wrote all of these, so all of them are
    testable, and any one of them could have been the layer the table ended up quoting. Scans a few
    rows rather than one, because a column is only guaranteed present on rows where it was computed.
    """
    pat = re.compile(rf"^{re.escape(metric)}\|L(\d+)\|{re.escape(stat)}$")
    found = set()
    for r in rows[:200]:
        for k in r:
            mm = pat.match(k)
            if mm:
                found.add(int(mm.group(1)))
    return sorted(found)


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
    ap.add_argument("--holm-family", default="available", choices=["available", "displayed"],
                    help="which set of layers the Holm correction is taken over. 'available' (the "
                         "default) = every layer with a column for --metric in results.jsonl, all "
                         "of them actually tested; 'displayed' = only the --layers subset, which is "
                         "the pre-audit behaviour and is only honest if that subset was fixed in "
                         "advance. Both are always printed and both go in the JSON.")
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
    pooled_all: Dict[int, Dict] = dict(pooled)

    def p_for(L: int) -> float:
        st = pooled_all.get(L)
        if st is None:
            st = cluster_robust(paired_by_family(fin, col(L), args.hi, args.lo))
            pooled_all[L] = st
        return two_sided_p(st["t_cluster"], max(st["n_clusters"] - 1, 1))
    # AUDIT T6c: the family is every layer the extract actually wrote for this metric, not the
    # --layers subset that reached the table. See the module docstring for why the displayed subset
    # cannot be treated as pre-registered (L18 is off the stride-4 grid).
    avail_layers = available_layers(fin, metric, stat)
    pv = {L: p_for(L) for L in layers}                       # displayed family
    pv_all = {L: p_for(L) for L in avail_layers}             # available family
    m_disp, m_avail = len(pv), len(pv_all)
    tab_disp = holm_table(pv, m=m_disp)
    tab_avail = holm_table(pv_all, m=m_avail)
    # The reading the audit note used: rank only the displayed p-values, but divide by the full m.
    tab_disp_m_avail = holm_table(pv, m=m_avail)
    chosen = args.holm_family
    rej = {L: bool((tab_disp if chosen == "displayed" else tab_avail)[L]["rejected"]) for L in layers}
    print(f"[reanalyze] Holm family rule = '{chosen}': m = "
          f"{m_disp if chosen == 'displayed' else m_avail} "
          f"(displayed layers m={m_disp}; layers available for {args.metric} in results.jsonl "
          f"m={m_avail})")
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
    # ---- (5) Holm sensitivity: the same p-vector under both families ---------- #
    print(f"\n=== HOLM SENSITIVITY: does the decision depend on the family? "
          f"(m={m_disp} displayed vs m={m_avail} available) ===")
    print(f"{'L':>3} {'p_clust':>10} | {'thr@m=' + str(m_disp):>12} {'rej':>4} | "
          f"{'thr@m=' + str(m_avail):>12} {'rej':>4} | {'thr@m=' + str(m_avail) + ' (disp-rank)':>22} {'rej':>4}")
    for L in layers:
        a, b, c = tab_disp[L], tab_avail[L], tab_disp_m_avail[L]
        print(f"{L:>3} {pv[L]:>10.6f} | {a['thr']:>12.6f} {'YES' if a['rejected'] else 'no':>4} | "
              f"{b['thr']:>12.6f} {'YES' if b['rejected'] else 'no':>4} | "
              f"{c['thr']:>22.6f} {'YES' if c['rejected'] else 'no':>4}")
    surv_d = [L for L in layers if tab_disp[L]["rejected"]]
    surv_a = [L for L in avail_layers if tab_avail[L]["rejected"]]
    surv_c = [L for L in layers if tab_disp_m_avail[L]["rejected"]]
    print(f"  rejected @ m={m_disp} (displayed family): {surv_d}")
    print(f"  rejected @ m={m_avail} (available family, all tested): {surv_a}")
    print(f"  rejected @ m={m_avail} with only the displayed p-values ranked: {surv_c}")

    report["holm_rejected"] = {str(L): bool(rej[L]) for L in layers}
    report["p_clustered"] = {str(L): pv[L] for L in layers}
    report["holm_family_rule"] = chosen
    report["holm_m"] = m_avail if chosen == "available" else m_disp
    report["holm_family_layers"] = (avail_layers if chosen == "available" else list(layers))
    report["holm_family_rule_doc"] = (
        "'available' = every layer with a %s|L*|%s column in results.jsonl, each one actually "
        "tested and entered into the step-down; 'displayed' = only the --layers subset. The "
        "displayed subset is not pre-registered (L18 is off the stride-4 grid), so 'available' is "
        "the default." % (metric, stat))
    report["p_clustered_all_layers"] = {str(L): pv_all[L] for L in avail_layers}
    report["holm_detail"] = {
        "displayed_family": {str(L): tab_disp[L] for L in layers},
        "available_family": {str(L): tab_avail[L] for L in avail_layers},
        "displayed_pvalues_scaled_to_available_m": {str(L): tab_disp_m_avail[L] for L in layers},
    }
    report["holm_rejected_by_family"] = {
        f"m={m_disp}_displayed": [int(L) for L in surv_d],
        f"m={m_avail}_available": [int(L) for L in surv_a],
        f"m={m_avail}_displayed_pvalues_only": [int(L) for L in surv_c],
    }
    report["pooled_all_layers"] = {str(L): pooled_all[L] for L in avail_layers}

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
