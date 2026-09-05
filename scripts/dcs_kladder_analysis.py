#!/usr/bin/env python3
"""DCS-PR-032 — the surgical row ladder, K = 3..7 (with the inherited rungs recomputed identically).

FROZEN BEFORE ITS DATA. Implements §11 of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`.

THE QUESTION. `R-021`/`R-022` bracket the transition between K=2 (null, -0.012) and K=8 (large,
-6.616) and never ran rungs 3-7. Is it a STEP or a RAMP, and where?

⛔ WHAT THIS CANNOT SEPARATE. `query_last_k_rows` cuts `_q[-K:]`, so destination-row count and
cut-cell count rise together BY CONSTRUCTION. This ladder separates STEP from RAMP; it does NOT
separate rows from cells. Inherited verbatim from `R-022` and not weakened here.

Every rung is read against ITS OWN dose-matched control, which is why the control family being inert
across a 32x dose range (+5.16..+5.38) matters: the contrast is within-rung.
"""
from __future__ import annotations
import argparse, collections, glob, json, os
import numpy as np
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
from clustered_stats import cluster_sign_test  # noqa: E402

NEW_RUNGS = (3, 4, 5, 6, 7)
INHERITED = (1, 2, 8, 16, 32)
ALPHA = 0.05
EXPECT_N = 380
HALF_K8_RULE = 0.5            # §11.5: |delta_K| >= 0.5 * |delta_K8|
STEP_LOW, STEP_HIGH = 0.20, 0.50   # §11.5 declared shapes
RAMP_MAX_SINGLE = 0.40


def load_arm(run_dir):
    if not os.path.exists(os.path.join(run_dir, "DONE.json")):
        return None          # C-047/§17.3: never read an in-progress run
    p = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def find_arm(root, tag):
    hits = sorted(glob.glob(os.path.join(root, f"{tag}_*")))
    return hits[-1] if hits else None


def contract(rows, name):
    """Checks read BEFORE any delta. A failing rung is VOID, not reinterpreted (§11.7)."""
    out = dict(arm=name, n_rows=len(rows))
    out["n_domains"] = len({r["domain"] for r in rows})
    out["keys_masked_median"] = float(np.median([r.get("hook_n_keys_masked", 0) for r in rows]))
    out["query_rows_edited_median"] = float(np.median(
        [r.get("hook_n_query_rows_edited", 0) for r in rows]))
    out["liveness_violations"] = int(sum(int(r.get("hook_liveness_violations", 0) or 0)
                                         for r in rows))
    out["decode_edits_max"] = int(max([r.get("hook_n_decode_edits", 0) or 0 for r in rows] or [0]))
    om = [r["option_mass"] for r in rows if "option_mass" in r]
    out["option_mass_median"] = float(np.median(om)) if om else None
    ks = {r.get("knockout_last_k") for r in rows}
    out["knockout_last_k"] = sorted(x for x in ks if x is not None)
    out["ok_n"] = (len(rows) == EXPECT_N)
    out["ok_liveness"] = (out["liveness_violations"] == 0)
    return out


def per_domain_delta(demo, ctrl):
    """Paired at the DOMAIN level (the declared independence unit), demo minus its own control."""
    def by_dom(rows):
        d = collections.defaultdict(list)
        for r in rows:
            if "semantic_logodds" in r:
                d[r["domain"]].append(float(r["semantic_logodds"]))
        return {k: float(np.mean(v)) for k, v in d.items()}
    a, b = by_dom(demo), by_dom(ctrl)
    doms = sorted(set(a) & set(b))
    return {d: a[d] - b[d] for d in doms}, by_dom(demo), by_dom(ctrl)


def holm(pvals):
    """Holm-Bonferroni over the family; returns adjusted p in the input order."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, adj, prev = len(pvals), [0.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        v = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, v)
        adj[i] = prev
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_kladder.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-032", alpha=ALPHA, expect_n=EXPECT_N,
               note="query_last_k_rows cuts _q[-K:]; rows and cut cells rise together by "
                    "construction. STEP vs RAMP only; NOT rows vs cells.",
               rungs={}, contracts={}, void=[])

    for K in sorted(set(NEW_RUNGS) | set(INHERITED)):
        dd, cd = find_arm(a.root, f"dcsk{K}_C_demo"), find_arm(a.root, f"dcsk{K}_C_ctrl")
        if not dd or not cd:
            continue
        demo, ctrl = load_arm(dd), load_arm(cd)
        if demo is None or ctrl is None:
            continue
        cD, cC = contract(demo, f"k{K}_demo"), contract(ctrl, f"k{K}_ctrl")
        res["contracts"][f"K{K}"] = dict(demo=cD, ctrl=cC)
        bad = []
        if not cD["ok_n"] or not cC["ok_n"]:
            bad.append(f"n != {EXPECT_N} (demo {cD['n_rows']}, ctrl {cC['n_rows']})")
        if not cD["ok_liveness"] or not cC["ok_liveness"]:
            bad.append("liveness violations")
        if cD["keys_masked_median"] != cC["keys_masked_median"]:
            bad.append(f"DOSE MISMATCH keys_masked {cD['keys_masked_median']} vs "
                       f"{cC['keys_masked_median']}")
        if bad:
            res["void"].append(dict(K=K, reasons=bad))
            continue
        delta, dmean, cmean = per_domain_delta(demo, ctrl)
        vals = [delta[d] for d in sorted(delta)]
        st = cluster_sign_test(vals, alpha=ALPHA)
        res["rungs"][f"K{K}"] = dict(
            K=K, is_new=(K in NEW_RUNGS), n_domains=len(vals),
            mean_delta=float(np.mean(vals)), median_delta=float(np.median(vals)),
            n_negative=int(sum(1 for v in vals if v < 0)),
            demo_mean=float(np.mean(list(dmean.values()))),
            ctrl_mean=float(np.mean(list(cmean.values()))),
            option_mass_demo=cD["option_mass_median"], option_mass_ctrl=cC["option_mass_median"],
            keys_masked=cD["keys_masked_median"],
            query_rows_edited=cD["query_rows_edited_median"],
            sign_test=dict(st), sign_summary=st.summary(), per_domain=delta)

    # ---- Holm over the FIVE NEW rungs only (§11.4); inherited rungs are context, not family
    new = [k for k in res["rungs"] if res["rungs"][k]["is_new"]]
    if new:
        ps = [res["rungs"][k]["sign_test"]["p"] for k in new]
        for k, adj in zip(new, holm(ps)):
            res["rungs"][k]["holm_p"] = adj
            res["rungs"][k]["significant"] = bool(adj <= ALPHA)

    # ---- §11.5 threshold rule, applied exactly as written
    k8 = res["rungs"].get("K8", {}).get("mean_delta")
    res["k8_reference"] = k8
    if k8 is not None:
        thr = HALF_K8_RULE * abs(k8)
        res["threshold_magnitude"] = thr
        kstar = None
        for K in sorted(set(NEW_RUNGS) | {8}):
            e = res["rungs"].get(f"K{K}")
            if not e:
                continue
            sig = e.get("significant", e["sign_test"]["p"] <= ALPHA)
            if sig and abs(e["mean_delta"]) >= thr:
                kstar = K
                break
        res["K_star"] = kstar
        # declared shapes
        prof = [(K, res["rungs"][f"K{K}"]["mean_delta"]) for K in (1, 2, 3, 4, 5, 6, 7, 8)
                if f"K{K}" in res["rungs"]]
        res["profile"] = prof
        if len(prof) >= 3 and k8:
            fr = [abs(v) / abs(k8) for _, v in prof]
            rises = [fr[i + 1] - fr[i] for i in range(len(fr) - 1)]
            jumped = any(fr[i] < STEP_LOW and fr[i + 1] > STEP_HIGH for i in range(len(fr) - 1))
            monotone = all(r >= -0.05 for r in rises)
            if jumped:
                res["shape"] = "STEP"
            elif monotone and max(rises) <= RAMP_MAX_SINGLE:
                res["shape"] = "RAMP"
            else:
                res["shape"] = "NEITHER — reported as such, no mechanism claimed"

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(f"[write] {a.out}\n")
    print(f"{'K':>4} {'new':>4} {'mean_delta':>11} {'%ofK8':>7} {'neg/dom':>9} {'p':>10} "
          f"{'holm':>8} {'opt_mass':>9}")
    for K in sorted(set(NEW_RUNGS) | set(INHERITED)):
        e = res["rungs"].get(f"K{K}")
        if not e:
            continue
        pct = (100 * abs(e["mean_delta"]) / abs(k8)) if k8 else float("nan")
        hp = e.get("holm_p")
        print(f"{K:>4} {str(e['is_new']):>4} {e['mean_delta']:>+11.4f} {pct:>6.1f}% "
              f"{e['n_negative']:>4}/{e['n_domains']:<4} {e['sign_test']['p']:>10.3e} "
              f"{('%.4f'%hp) if hp is not None else '-':>8} "
              f"{e['option_mass_demo'] if e['option_mass_demo'] is not None else float('nan'):>9.3f}")
    if res["void"]:
        print(f"\n⛔ VOID rungs: {res['void']}")
    print(f"\nK* = {res.get('K_star')}   shape = {res.get('shape')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
