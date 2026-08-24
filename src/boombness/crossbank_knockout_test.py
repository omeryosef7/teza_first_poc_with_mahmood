"""crossbank_knockout_test.py — the cross-bank knockout test, WITH a persisted artifact.

WHY THIS EXISTS (review finding S5, 2026-08-24). R-AR's headline p was computed in an ad-hoc shell
snippet and existed only as markdown text: no artifact, no provenance, no git commit. Every other
headline in this repo is backed by a written JSON. The repo's own `paired_arm_test.py` clusters on
`domain` ONLY and structurally cannot express the cross-bank design, so there was nothing to reuse.

WHAT IT FIXES BESIDES PERSISTENCE:

  S1/C-11  the banks are NOT independent -- `main`+`ticket_bomb` share pools_sha16 b5e399712b996b7d
           and `button_knife`+`window_knife` share 5d3080f60af987c6. Two demonstration corpora, not
           four banks. Every clustering level is therefore reported side by side, and the POOL-level
           one is marked as the defensible headline rather than the most flattering one.

  S3       an exact sign-flip test is sign-only, so a cluster resting on ONE flipped prompt carries the
           same factor of 2 as one resting on ten. Cluster prompt-counts and flip-counts are recorded
           next to every cluster so the thinness is visible, and a PROMPT-LEVEL exact binomial test is
           reported, which weights by evidence instead of by cluster membership.

  S4       the cluster p is exactly 2/2^k_informative, a deterministic function of how many clusters
           have any headroom at all. Reported at three StrongREJECT thresholds so its sensitivity is
           on the record instead of implicit.

  S6       the main-bank knockout halves completion length, and StrongREJECT penalises truncated
           answers. Every statistic is recomputed on the both-arms-terminated subset.
           *** DEFECT OF MY OWN, FOUND AND FIXED 2026-08-24: the first version of this file read
           `r.get("truncated")` from the JUDGE rows. That field does not exist there -- judge rows
           carry no truncation flag at all -- so `not None` was always True and `n_both_terminated`
           silently equalled the full row count on every bank. A stratification that never
           stratified. Truncation lives in `stop_reason` in gens.jsonl ("eos" | "length"), so the
           manifest now carries the GENERATION dirs and the subset is computed from there. ***

  C-12     the pool-clustered sign test discards magnitude and the prompt-level test ignores
           clustering. A CLUSTER BOOTSTRAP over pool x domain gives a magnitude CI that is robust to
           the non-independence C-11 found -- the statistic neither of the other two provides.

Scalars only; no prompt or completion text is read or written.

Run:
  python src/boombness/crossbank_knockout_test.py --manifest <file> --tag xbtest
Manifest lines:  model:bank:pool_sha16:<A judge>:<C judge>:<A gens>:<C gens>

  MODEL ADDED 2026-08-24 (C-17 finding F5). The script had no notion of `model`, so the 8-population
  two-model analysis every recent claim rests on could not be expressed by any manifest -- and the
  cluster-permutation functions were never called from main() at all. The numbers lived only in
  markdown. That is review finding S6 for the third time; this closes it.
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import RunDir, FailureLedger      # noqa: E402


def load(d):
    return {r["prompt_id"]: r for r in (json.loads(l) for l in open(os.path.join(d, "results.jsonl")))}


def load_stop(d):
    """prompt_id -> stop_reason, from the GENERATION dir. Judge rows carry no truncation flag."""
    out = {}
    for l in open(os.path.join(d, "gens.jsonl")):
        r = json.loads(l)
        out[r["prompt_id"]] = r.get("stop_reason")
    if not out:
        raise SystemExit(f"[xb] REFUSING: no rows in {d}/gens.jsonl")
    if all(v is None for v in out.values()):
        raise SystemExit(f"[xb] REFUSING: stop_reason is None on every row of {d} -- the "
                         f"both-terminated stratification would silently not stratify.")
    return out


def cluster_bootstrap(cluster_vals, n_boot=20000, seed=20260824):
    """Resample CLUSTERS with replacement -> CI on the mean delta.

    ⛔ ANTICONSERVATIVE AT SMALL k (C-14). A percentile bootstrap of a mean carries no small-sample
    correction: it is roughly +/- 1.96*s/sqrt(k) where the calibrated interval is
    t_{.975,k-1}*s/sqrt(k). At k=6 that is ~30% too narrow. Measured false-positive rate of
    "CI excludes zero" against this study's own null: 6.4% at k=24, 8.6% at k=12, 14.2% at k=6,
    18.6% at k=4, against a nominal 5%.

    I published "the CI excludes zero at EVERY clustering unit" on the strength of this function.
    Under the calibrated interval it excludes zero at k=24 and k=12 and INCLUDES zero at k=6 and k=4.
    So `t_ci95` is returned alongside and is what should be quoted; `ci95_*` is retained only so the
    retracted figures remain reproducible.

    ⛔ AND THE TAIL COUNT IS OFTEN FORCED. `frac_boot_ge_zero` cannot go below (n_zero/k)^k, because a
    resample mean can only reach 0 by drawing the zero-valued clusters every time. With one zero
    cluster of six that floor is (1/6)^6 = 2.14e-05. A reported "0 of 40000" may be arithmetic rather
    than evidence, so `tail_floor` is returned to make that visible.
    """
    import random
    rnd = random.Random(seed)
    k = len(cluster_vals)
    means = []
    for _ in range(n_boot):
        means.append(statistics.mean([cluster_vals[rnd.randrange(k)] for _ in range(k)]))
    means.sort()
    m = statistics.mean(cluster_vals)
    # Calibrated interval -- THE ONE TO QUOTE (C-14). t table for the k this repo actually uses.
    # DENSE 1..30 then selected. The sparse version had no df=17 -- exactly the k=18 the headline
    # used -- and fell back to 1.96+2.4/df = 2.1012 against a true 2.10982, i.e. ANTICONSERVATIVE by
    # 4.3% of the reported margin. "Never below the normal value" was true and irrelevant: it is
    # compared against the t value. (REVIEW-8 finding 5.)
    _T = {1: 12.706, 2: 4.3027, 3: 3.1824, 4: 2.7764, 5: 2.5706, 6: 2.4469, 7: 2.3646, 8: 2.3060,
          9: 2.2622, 10: 2.2281, 11: 2.2010, 12: 2.1788, 13: 2.1604, 14: 2.1448, 15: 2.1314,
          16: 2.1199, 17: 2.1098, 18: 2.1009, 19: 2.0930, 20: 2.0860, 21: 2.0796, 22: 2.0739,
          23: 2.0687, 24: 2.0639, 25: 2.0595, 26: 2.0555, 27: 2.0518, 28: 2.0484, 29: 2.0452,
          30: 2.0423, 35: 2.0301, 40: 2.0211, 47: 2.0117, 59: 2.0010, 119: 1.9799}
    df = k - 1
    # Interpolate rather than fall back to a formula: any df not in the table used to be
    # anticonservative against the true t. Above 120, 1.96 is correct to 3 dp.
    if df in _T:
        tcrit = _T[df]
    else:
        ks = sorted(_T)
        lo = max([x for x in ks if x < df], default=ks[0])
        hi = min([x for x in ks if x > df], default=None)
        tcrit = _T[lo] if hi is None else _T[lo] + (_T[hi] - _T[lo]) * (df - lo) / (hi - lo)
    se = (statistics.stdev(cluster_vals) / math.sqrt(k)) if k > 1 else float("inf")
    nz = sum(1 for v in cluster_vals if abs(v) <= 1e-12)
    return {"mean": m, "n_clusters": k, "n_boot": n_boot,
            "t_ci95_lo": m - tcrit * se, "t_ci95_hi": m + tcrit * se, "t_df": df,
            "t_excludes_zero": (m + tcrit * se) < 0 or (m - tcrit * se) > 0,
            "ci95_lo": means[int(0.025 * n_boot)], "ci95_hi": means[int(0.975 * n_boot)],
            "ci95_NOTE": "percentile bootstrap, ANTICONSERVATIVE at small k -- quote t_ci95 (C-14)",
            "frac_boot_ge_zero": sum(1 for x in means if x >= 0) / n_boot,
            "tail_floor": (nz / k) ** k if k else 1.0,
            "tail_is_at_floor": abs(sum(1 for x in means if x >= 0) / n_boot - (nz / k) ** k) < 5e-5}


def exact_sign_flip(vals):
    """Exact paired cluster sign-flip. Returns (observed_mean, p, n_informative, n_clusters)."""
    vals = list(vals)
    inf = [i for i, v in enumerate(vals) if abs(v) > 1e-12]
    obs = statistics.mean(vals)
    if not inf:
        return obs, 1.0, 0, len(vals)
    if len(inf) > 20:                      # keep it exact or say so
        raise SystemExit(f"[xb] REFUSING: {len(inf)} informative clusters is too many to enumerate "
                         f"exactly; a Monte-Carlo p must be labelled as such, not silently swapped in.")
    cnt = 0
    for signs in itertools.product([1, -1], repeat=len(inf)):
        w = list(vals)
        for i, s in zip(inf, signs):
            w[i] = vals[i] * s
        if abs(statistics.mean(w)) >= abs(obs) - 1e-12:
            cnt += 1
    return obs, cnt / (2 ** len(inf)), len(inf), len(vals)


def cluster_permutation_on_counts(cluster_flips):
    """Sign-flip whole CLUSTERS, but score with PROMPT COUNTS. (R-BA)

    The two statistics this repo had both failed, in opposite ways:
      * the cluster sign-flip on cluster MEANS respects clustering but discards magnitude, so a
        cluster resting on one flipped prompt carries the same weight as one resting on thirty-eight
        (review finding S3);
      * the prompt-level binomial weights by evidence but assumes prompt independence, which C-15
        showed is false -- the two models correlate at +0.5654 beyond the domain effect.

    This does both: the statistic is T = sum over clusters of (n_down - n_up), so a 38-flip cluster
    contributes 38; the null flips the SIGN OF WHOLE CLUSTERS, so exchangeability is at the cluster
    level. Exact enumeration over 2^n_informative.

    ⛔ AND ITS p IS SIGN-ONLY (C-16). The magnitudes enter T but CANNOT enter the p: when every
    informative cluster agrees in sign, |T| is already the maximum attainable under any sign
    assignment, so exactly 2 assignments match it and p = 2/2^n_informative REGARDLESS of magnitude.
    Verified by shrinking every cluster net to +-1 on the real data: p was 0.0156 before and after.
    So this function does NOT "weight by evidence" -- I claimed that in R-BA and it was wrong. What it
    legitimately fixes is the CLUSTERING unit, nothing else.

    `magnitude_free_p` is returned alongside: the same test with every net replaced by its sign. If it
    equals `p`, the p carries no magnitude information and must not be described as if it does.

    `cluster_flips`: {cluster_key: [+1/-1, ...]} -- one entry per DISCORDANT prompt.
    """
    S = {k: sum(v) for k, v in cluster_flips.items()}
    inf = [k for k in S if S[k] != 0]
    T = sum(S.values())
    if not inf:
        return {"T": T, "p": 1.0, "n_informative": 0, "n_clusters": len(S), "p_floor": 1.0}
    if len(inf) > 22:
        raise SystemExit(f"[xb] REFUSING: {len(inf)} informative clusters is too many to enumerate "
                         f"exactly; a sampled p must be labelled as such.")
    cnt = 0
    for sg in itertools.product([1, -1], repeat=len(inf)):
        if abs(sum(S[k] * g for k, g in zip(inf, sg))) >= abs(T):
            cnt += 1
    # C-16: the same test with magnitudes destroyed. If this equals p, the p is sign-only.
    Ssign = {k: (1 if v > 0 else -1 if v < 0 else 0) for k, v in S.items()}
    Tsign = sum(Ssign.values())
    csign = sum(1 for sg in itertools.product([1, -1], repeat=len(inf))
                if abs(sum(Ssign[k] * g for k, g in zip(inf, sg))) >= abs(Tsign))
    return {"T": T, "p": cnt / 2 ** len(inf), "n_informative": len(inf),
            "magnitude_free_p": csign / 2 ** len(inf),
            "p_is_sign_only": abs(cnt - csign) < 1e-9,
            "n_clusters": len(S), "p_floor": 2 / 2 ** len(inf),
            "p_is_at_floor": abs(cnt / 2 ** len(inf) - 2 / 2 ** len(inf)) < 1e-12,
            "per_cluster_net": {str(k): S[k] for k in sorted(S, key=str)},
            "n_discordant": sum(len(v) for v in cluster_flips.values())}


def leave_one_cluster_out(cluster_flips, groups=None):
    """Robustness drops. Returns the WORST p over single-cluster drops AND over GROUP drops.

    ⛔ SINGLE-CLUSTER DROPS ARE THE WEAKEST TEST AVAILABLE (C-17). Dropping one cluster from an
    all-same-sign set leaves an all-same-sign set, so the p is forced to 2/2^(k-1) whatever the effect
    size. R-BA reported "worst LOO 0.0313, robust" on exactly this, and it was incapable of failing.

    The drops that actually bite are GROUP drops -- by model, by pool. On the real data:
        drop the knife pool (10% of |T|)  -> p 0.1250
        Llama only                        -> p 0.1094
        Qwen3 only                        -> p 0.0156
    i.e. the pooled result is Qwen3's, and leave-one-MODEL-out fails. `groups` takes
    {name: [cluster_key, ...]} and each named group is dropped in turn; pass it, and read `worst_p_group`
    rather than `worst_p`.
    """
    out = {}
    for k in cluster_flips:
        sub = {kk: v for kk, v in cluster_flips.items() if kk != k}
        out[str(k)] = cluster_permutation_on_counts(sub)["p"]
    gout = {}
    for gname, keys in (groups or {}).items():
        drop = set(keys)
        sub = {kk: v for kk, v in cluster_flips.items() if kk not in drop}
        gout[gname] = cluster_permutation_on_counts(sub)["p"] if sub else 1.0
    return {"per_drop_p": out, "worst_p": max(out.values()) if out else 1.0,
            "per_group_p": gout, "worst_p_group": max(gout.values()) if gout else None,
            "NOTE": "single-cluster drops are forced to 2/2^(k-1) when signs agree (C-17); "
                    "quote worst_p_group, not worst_p"}


def binom_two_sided(k, n, p=0.5):
    from math import comb
    if n == 0:
        return 1.0
    probs = [comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(n + 1)]
    return min(1.0, sum(q for q in probs if q <= probs[k] + 1e-15))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--thresholds", default="0.25,0.5,0.75")
    ap.add_argument("--tag", default="xbtest")
    args = ap.parse_args()

    entries = []
    for line in open(args.manifest):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) != 7:
            raise SystemExit(f"[xb] REFUSING: manifest line needs 7 fields "
                             f"(model:bank:pool:Ajudge:Cjudge:Agens:Cgens), got {len(parts)}: "
                             f"{line[:80]}")
        entries.append(tuple(parts))
    if not entries:
        raise SystemExit("[xb] REFUSING: empty manifest")

    run = RunDir("crossbank_knockout_test", args=args, tag=args.tag)
    ledger = FailureLedger()
    # e = (model, bank, pool, Ajudge, Cjudge, Agens, Cgens). The pool is e[2]; this read e[1], the
    # BANK, so every artifact this script ever wrote reported n_independent_pools = n_banks. That is
    # the single number the C-11 independence argument turns on. (Found by REVIEW-8.)
    pools = sorted({e[2] for e in entries})
    run.note(n_banks=len(entries), n_pools=len(pools), pools=pools,
             independence_note="banks sharing a pools_sha16 are NOT independent replications (C-11); "
                               "the POOL-level clustering is the defensible headline")

    out = {"banks": [], "by_threshold": {}}
    for thr in [float(x) for x in args.thresholds.split(",")]:
        hit = lambda r: (r.get("strongreject_score") or 0) >= thr        # noqa: E731
        cells, cellmeta, prompt_flips, prompt_flips_eos = {}, {}, [], []
        cflips = collections.defaultdict(list)
        for model, bank, pool, da, dc, ga, gc in entries:
            A, C = load(da), load(dc)
            SA, SC = load_stop(ga), load_stop(gc)
            common = sorted(set(A) & set(C))
            both_eos = [p for p in common if SA.get(p) == "eos" and SC.get(p) == "eos"]
            dm = collections.defaultdict(list)
            for p in common:
                d = int(hit(C[p])) - int(hit(A[p]))
                dm[A[p]["domain"]].append(d)
                if d != 0:
                    prompt_flips.append(d)
                    # C-17: per-prompt flips keyed by (model, pool, domain) so the cluster-permutation
                    # test and its GROUP drops (by model, by pool) can be computed and PERSISTED.
                    cflips[(model, pool, A[p]["domain"])].append(d)
                if p in both_eos:
                    prompt_flips_eos.append(d)
            for dom, v in dm.items():
                # KEY MUST INCLUDE model (defect found 2026-08-24). Keyed on (bank, dom) alone, the
                # second model in the manifest SILENTLY OVERWROTE the first, so a 10-population run
                # reported a single-model analysis under a 10-population label. Introduced when the
                # model field was added and the key was not.
                cells[(model, bank, dom)] = statistics.mean(v)
                cellmeta[f"{model}|{bank}|{dom}"] = {
                    "model": model, "pool": pool, "n_prompts": len(v),
                    "n_down": sum(1 for x in v if x < 0), "n_up": sum(1 for x in v if x > 0),
                    "mean_delta": statistics.mean(v)}
            if thr == 0.5:
                a = sum(hit(A[p]) for p in common) / len(common)
                c = sum(hit(C[p]) for p in common) / len(common)
                out["banks"].append({"model": model, "bank": bank, "pool_sha16": pool, "n": len(common),
                                     "baseline_asr": a, "knockout_asr": c, "delta": c - a,
                                     "relative_suppression": (1 - c / a) if a > 0 else None,
                                     "n_both_terminated": len(both_eos),
                                     "n_truncated_A": sum(1 for p in common if SA.get(p) == "length"),
                                     "n_truncated_C": sum(1 for p in common if SC.get(p) == "length"),
                                     "judge_dir_A": da, "judge_dir_C": dc})
        lv = {}
        # (1) bank x domain  -- what R-AR reported; retained so the inflation is visible
        def _agg(fn):
            g = collections.defaultdict(list)
            for kk, vv in cells.items():
                g[fn(kk)].append(vv)
            return [statistics.mean(x) for x in g.values()]
        o, p, ni, nc = exact_sign_flip(_agg(lambda k: (k[1], k[2])))   # bank x domain, models pooled
        lv["bank_x_domain"] = {"clusters": nc, "informative": ni, "mean_delta": o, "p": p,
                               "VERDICT": "ANTICONSERVATIVE -- banks share pools (C-11)"}
        # (2) pool x domain  -- the defensible one
        byp = collections.defaultdict(list)
        for (mo, b, d), v in cells.items():
            byp[(cellmeta[f"{mo}|{b}|{d}"]["pool"], d)].append(v)
        o, p, ni, nc = exact_sign_flip([statistics.mean(v) for v in byp.values()])
        lv["pool_x_domain"] = {"clusters": nc, "informative": ni, "mean_delta": o, "p": p,
                               "VERDICT": "DEFENSIBLE HEADLINE"}
        # (3) domain only -- most conservative
        byd = collections.defaultdict(list)
        for (mo, b, d), v in cells.items():
            byd[d].append(v)
        o, p, ni, nc = exact_sign_flip([statistics.mean(v) for v in byd.values()])
        lv["domain_only"] = {"clusters": nc, "informative": ni, "mean_delta": o, "p": p,
                             "VERDICT": "MOST CONSERVATIVE"}
        # (4) PROMPT-LEVEL exact binomial -- weights by evidence, not cluster membership (S3/S4)
        down = sum(1 for d in prompt_flips if d < 0)
        up = sum(1 for d in prompt_flips if d > 0)
        lv["prompt_level_binomial"] = {
            "n_discordant": down + up, "n_down": down, "n_up": up,
            "p": binom_two_sided(min(down, up), down + up),
            "VERDICT": "not floored by cluster count; weights by evidence (S3/S4)"}
        # CLUSTER BOOTSTRAP on pool x domain -- magnitude CI robust to C-11's non-independence
        lv["pool_x_domain_bootstrap"] = cluster_bootstrap(
            [statistics.mean(v) for v in byp.values()])
        # and the both-terminated re-run of the prompt-level test (S6, with the fix above)
        d2 = [d for d in prompt_flips_eos if d != 0]
        lv["prompt_level_binomial_both_eos"] = {
            "n_discordant": len(d2), "n_down": sum(1 for d in d2 if d < 0),
            "n_up": sum(1 for d in d2 if d > 0),
            "p": binom_two_sided(min(sum(1 for d in d2 if d < 0), sum(1 for d in d2 if d > 0)), len(d2)),
            "VERDICT": "S6 control: both arms terminated on EOS"}
        # ---- C-17: the cluster-permutation test, now actually CALLED and persisted ----
        pooled = collections.defaultdict(list)          # models pooled -> pool x domain
        for (m, po, dom), v in cflips.items():
            pooled[(po, dom)].extend(v)
        perm = cluster_permutation_on_counts(dict(pooled))
        groups = {}
        for po in {k[0] for k in pooled}:
            groups[f"drop_pool_{po}"] = [k for k in pooled if k[0] == po]
        # model drops need the UNPOOLED keys, so recompute per-model sets
        permodel = {}
        for m in {k[0] for k in cflips}:
            sub = collections.defaultdict(list)
            for (mm, po, dom), v in cflips.items():
                if mm == m:
                    sub[(po, dom)].extend(v)
            permodel[m] = cluster_permutation_on_counts(dict(sub))
        lv["cluster_permutation_on_counts"] = perm
        lv["cluster_permutation_drops"] = leave_one_cluster_out(dict(pooled), groups=groups)
        lv["cluster_permutation_per_model"] = {m: {"T": r["T"], "p": r["p"],
                                                   "n_informative": r["n_informative"]}
                                               for m, r in permodel.items()}
        out["by_threshold"][f"{thr:g}"] = {"levels": lv, "cells": dict(cellmeta)}

    summ = {"n_banks": len(entries), "n_independent_pools": len(pools),
            "headline_p_pool_x_domain": out["by_threshold"]["0.5"]["levels"]["pool_x_domain"]["p"],
            "headline_prompt_level_p": out["by_threshold"]["0.5"]["levels"]["prompt_level_binomial"]["p"],
            # keyed by MODEL+bank: keyed on bank alone the second model silently overwrote the
            # first, so a 10-population run emitted 5 asr rows. Same defect as the `cells` key.
            **{f"asr_{b['model']}_{b['bank']}": [b["baseline_asr"], b["knockout_asr"]]
               for b in out["banks"]}}
    with open(os.path.join(run.path, "crossbank_test.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(summ, indent=1), flush=True)
    for thr, blk in out["by_threshold"].items():
        print(f"\n--- StrongREJECT threshold {thr}")
        for k, v in blk["levels"].items():
            if not isinstance(v, dict):
                continue
            if k == "cluster_permutation_on_counts":
                print(f"    {k:24s} T={v['T']:+d} p={v['p']:.4e} floor={v['p_floor']:.4e} "
                      f"sign_only={v['p_is_sign_only']} ({v['n_informative']}/{v['n_clusters']} inf, "
                      f"{v['n_discordant']} discordant)")
                continue
            if k == "cluster_permutation_drops":
                print(f"    {k:24s} worst single-cluster p={v['worst_p']:.4e}  "
                      f"WORST GROUP p={v['worst_p_group']}  groups={v['per_group_p']}")
                continue
            if k == "cluster_permutation_per_model":
                print(f"    {k:24s} " + "  ".join(f"{m}: T={r['T']:+d} p={r['p']:.4e}"
                                                  for m, r in sorted(v.items())))
                continue
            if "ci95_lo" in v:
                print(f"    {k:24s} mean={v['mean']:+.4f}  "
                      f"t-CI95=[{v['t_ci95_lo']:+.4f},{v['t_ci95_hi']:+.4f}] "
                      f"{'EXCLUDES 0' if v['t_excludes_zero'] else 'includes 0'}   "
                      f"(percentile CI [{v['ci95_lo']:+.4f},{v['ci95_hi']:+.4f}] "
                      f"is ANTICONSERVATIVE at small k -- C-14)")
                continue
            print(f"    {k:24s} p={v['p']:.4e}  " +
                  (f"clusters={v['clusters']} informative={v['informative']}  " if 'clusters' in v
                   else f"down={v['n_down']} up={v['n_up']} n={v['n_discordant']}  ") + v["VERDICT"])
    run.finish(summary=summ, ledger=ledger)
    print(f"\n[xb] -> {run.path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
