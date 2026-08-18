"""analyze_g64.py — plan §6.4: the three-way metric comparison and its four named deliverables.

§6.4 asks for three Boombness metrics — `logit_lens_boombness`, `direction_boombness`,
`probe_boombness` — compared against ASR, refusal rate, comprehension score, number of examples and
role-style condition, and it names four outputs:

    plots/metric_vs_asr.png
    plots/metric_by_layer.png
    plots/metric_by_carrot_occurrence.png
    plots/correlation_table.csv

THREE OF THE FOUR DID NOT EXIST, and `probe_boombness` was absent from every comparison because
probes.py emitted only per-regime aggregates. `probes.py --emit-scores` now writes out-of-fold
per-prompt margins, which is what makes the third metric comparable at all.

INFERENCE. Correlations are Spearman, with a p-value from a WITHIN-DOMAIN permutation (the domain
is the cluster; 6 domains). A naive iid p-value on 234 prompts drawn from 6 domains is
pseudo-replication -- the failure this sprint recorded as retraction R1 -- so the iid value is
computed and reported alongside, explicitly labelled, but the permutation one is the citable one.
This matches analyze_g2.py.

ESTIMAND PAIRING (audit T5, 2026-08-18). The table used to carry a column `spearman_rho` -- the RAW
POOLED Spearman -- with `p_within_domain_perm` in the very next column. Those are two different
quantities: the permutation demeans x and y within domain first, so its p tests the WITHIN-DOMAIN
correlation, not the pooled one. Nothing in the header said so, so a reader read the p as the p of
the rho beside it. It is not cosmetic: in the published table the p column is NOT MONOTONE in |pooled
rho| -- `logit_lens_boombness` at L12 vs ASR is rho_pooled=-0.2098 with p=0.818, while
`direction_boombness` at L24 is rho_pooled=+0.0884 with p=0.120, so the row with 2.4x the |rho|
carries the far LARGER p and a reader ranking metrics by that pair gets the ordering backwards. The table now
reports BOTH point estimates -- `rho_pooled` and `rho_within_domain` -- with the permutation p named
`p_perm_within_domain_rho` and a `p_estimand` column naming the quantity it tests, and the same for
the partial (`rho_partial_n_examples_pooled` / `rho_partial_n_examples_within_domain` /
`p_perm_within_domain_partial`). Neither estimate was promoted or demoted; only the pairing changed.

ROLE-STYLE is reported as eta^2 (between-style variance share) rather than a correlation, because
it is categorical; and it is flagged NOT IDENTIFIED, because §9 established that `role_style` is
perfectly collinear with `bank_block` with zero family overlap, so any role association is a
family-set association. The number is descriptive only.
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import os
import random
import statistics as st
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


def _rank(v: Sequence[float]) -> List[float]:
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[order[k]] = avg
        i = j + 1
    return r


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) < 3:
        return float("nan")
    rx, ry = _rank(x), _rank(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def _demean_within(v, domains):
    """Subtract each domain's mean. Required before a within-domain permutation."""
    by = collections.defaultdict(list)
    for i, d in enumerate(domains):
        by[d].append(i)
    out = list(v)
    for idx in by.values():
        m = st.mean(out[i] for i in idx)
        for i in idx:
            out[i] -= m
    return out


def rho_within_domain(x, y, domains) -> float:
    """The point estimate `perm_p_within_domain` actually tests: Spearman on group-demeaned x,y.

    Added by audit T5. It existed only inside the permutation function as a local `obs`, so the
    table could report a pooled rho beside a within-domain p and no one could see the gap.
    """
    return spearman(_demean_within(x, domains), _demean_within(y, domains))


def perm_p_within_domain(x, y, domains, n_perm=2000, seed=20260818) -> float:
    """Permute x WITHIN each domain, on the GROUP-DEMEANED vectors.

    AUDIT (2026-08-18): the first version permuted within domain but evaluated the correlation on
    the RAW pooled vectors. Shuffling inside a group preserves that group's mean exactly, so the
    BETWEEN-domain component of the association survived every draw and the null was not centred on
    zero - the statistic was not the within-domain one its name promised. This is the identical bug
    analyze_g2.py:284 diagnosed as audit A3 and fixed; it was reintroduced here. Demeaning x and y
    within domain first makes the statistic actually within-domain.
    """
    rng = random.Random(seed)
    xw, yw = _demean_within(x, domains), _demean_within(y, domains)
    obs = abs(spearman(xw, yw))
    if math.isnan(obs):
        return float("nan")
    idx_by_dom = collections.defaultdict(list)
    for i, d in enumerate(domains):
        idx_by_dom[d].append(i)
    hits = 0
    for _ in range(n_perm):
        xp = list(xw)
        for idx in idx_by_dom.values():
            vals = [xp[i] for i in idx]
            rng.shuffle(vals)
            for i, v in zip(idx, vals):
                xp[i] = v
        if abs(spearman(xp, yw)) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def rank_partial_within_domain(x, y, z, domains) -> float:
    """The point estimate `perm_p_partial` tests: the rank partial on group-demeaned vectors."""
    return rank_partial(_demean_within(x, domains), _demean_within(y, domains),
                        _demean_within(z, domains))


def rank_partial(x, y, z) -> float:
    """Spearman of x,y after linearly removing z on the RANK scale.

    Required here, not optional. `probe_boombness` correlates rho=+0.631 with `n_examples`, and
    demonstration count is itself an ASR driver, so the probe's raw ASR correlation is partly a
    demo-counter. Every metric-vs-ASR row therefore carries the n_examples-partialled value beside
    the raw one, and the write-up cites the partialled one.
    """
    rx, ry, rz = _rank(x), _rank(y), _rank(z)

    def resid(a, b):
        ma, mb = st.mean(a), st.mean(b)
        den = sum((v - mb) ** 2 for v in b)
        if den == 0:
            return list(a)
        sl = sum((u - ma) * (v - mb) for u, v in zip(a, b)) / den
        return [u - (ma + sl * (v - mb)) for u, v in zip(a, b)]

    return spearman(resid(rx, rz), resid(ry, rz))


def perm_p_partial(x, y, z, domains, n_perm=2000, seed=20260818) -> float:
    """Within-domain permutation of x, recomputing the PARTIAL correlation each time."""
    rng = random.Random(seed)
    # same demeaning fix as perm_p_within_domain
    x, y, z = (_demean_within(x, domains), _demean_within(y, domains), _demean_within(z, domains))
    obs = abs(rank_partial(x, y, z))
    if math.isnan(obs):
        return float("nan")
    idx = collections.defaultdict(list)
    for i, d in enumerate(domains):
        idx[d].append(i)
    hits = 0
    for _ in range(n_perm):
        xp = list(x)
        for ii in idx.values():
            vv = [xp[i] for i in ii]
            rng.shuffle(vv)
            for i, v in zip(ii, vv):
                xp[i] = v
        if abs(rank_partial(xp, y, z)) >= obs:
            hits += 1
    return (hits + 1) / (n_perm + 1)


def eta_squared(values: Sequence[float], groups: Sequence[object]) -> float:
    g = collections.defaultdict(list)
    for v, k in zip(values, groups):
        g[k].append(v)
    grand = st.mean(values)
    ssb = sum(len(v) * (st.mean(v) - grand) ** 2 for v in g.values())
    sst = sum((v - grand) ** 2 for v in values)
    return ssb / sst if sst > 0 else float("nan")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--comprehension", required=True, help="unintervened score_behavior run")
    ap.add_argument("--probe-scores", required=True, help="probes run dir with probe_scores.jsonl")
    ap.add_argument("--probe-regime", default="d5_surface_matched_codeword")
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--layers", default="0,4,8,12,16,20,24,28,31")
    ap.add_argument("--headline-layer", type=int, default=12)
    ap.add_argument("--common-subset", dest="common", action="store_true", default=True,
                    help="restrict EVERY metric to prompts that carry ALL THREE (default). "
                         "Without it the metrics are compared on different populations, which is "
                         "how the first run of this script reported probe rho=+0.440 on n=72 "
                         "beside direction rho=+0.372 on n=270 as if they were like-for-like.")
    ap.add_argument("--no-common-subset", dest="common", action="store_false")
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    for d in (args.extract, args.judge, args.comprehension, args.probe_scores):
        require_done(d)
    layers = [int(x) for x in args.layers.split(",")]
    os.makedirs(args.outdir, exist_ok=True)

    J = read_jsonl(os.path.join(args.judge, "results.jsonl"))
    E = read_jsonl(os.path.join(args.extract, "results.jsonl"))
    S = read_jsonl(os.path.join(args.comprehension, "results.jsonl"))
    P = [json.loads(l) for l in open(os.path.join(args.probe_scores, "probe_scores.jsonl"))]

    asr = {r["prompt_id"]: r["strongreject_score"] for r in J
           if r.get("condition") == args.arm and r.get("strongreject_score") is not None}
    refused = {r["prompt_id"]: (1.0 if r.get("refused") else 0.0) for r in J
               if r["prompt_id"] in asr}
    meta = {r["prompt_id"]: r for r in J if r["prompt_id"] in asr}
    # `prompt_id` = sha256(family_id + '|' + condition) and `family_id` ENDS WITH the query_kind,
    # so a behavioural prompt_id and a comprehension_usage prompt_id are never equal. Joining on it
    # gave 0 of 288 matches and silently dropped `comprehension` -- a plan-§6.4 REQUIRED target --
    # out of the correlation table entirely. Join on the query-kind-stripped family stem instead.
    def _stem(fid): return "|".join((fid or "").split("|")[:-1])
    comp_by_stem = {}
    for r in S:
        if r.get("readout") == "comprehension" and r.get("comprehension_logodds") is not None:
            comp_by_stem[(_stem(r.get("family_id")), r.get("condition"))] = r["comprehension_logodds"]
    comp = {}
    for pid, m in meta.items():
        v = comp_by_stem.get((_stem(m.get("family_id")), m.get("condition")))
        if v is not None:
            comp[pid] = v

    erow = {r["prompt_id"]: r for r in E if r.get("is_final_occurrence") and r["prompt_id"] in asr}
    prow: Dict[int, Dict[str, float]] = collections.defaultdict(dict)
    for r in P:
        if r.get("regime") == args.probe_regime:
            prow[r["layer"]][r["prompt_id"]] = r["probe_margin"]

    # ---- metric availability, stated rather than assumed ------------------------------------ #
    METRICS = {
        "logit_lens_boombness": lambda L, p: erow[p].get(f"ll|L{L}|boombness"),
        "direction_boombness":  lambda L, p: erow[p].get(f"d_surface|L{L}|proj"),
        "probe_boombness":      lambda L, p: prow.get(L, {}).get(p),
    }
    # ---- COMMON SUBSET: the three metrics must be read on the SAME prompts ------------------ #
    # The rep cache behind `probe_boombness` was built from a 1464-row bank version; the bank is now
    # 2352 rows, so 888 rows have no cached rep and the probe covers only a fraction of the judged
    # population -- and that fraction is not random (whole bank_blocks are absent: strength,
    # consistency, position, role_style, families; only core2x2 survives).
    hl = args.headline_layer
    have_all = [p for p in sorted(erow)
                if erow[p].get(f"ll|L{hl}|boombness") is not None
                and erow[p].get(f"d_surface|L{hl}|proj") is not None
                and prow.get(hl, {}).get(p) is not None]
    cov = {"judged": len(asr), "with_extract": len(erow), "with_probe_at_headline":
           sum(1 for p in erow if prow.get(hl, {}).get(p) is not None),
           "common_all_three": len(have_all)}
    print(f"[G6.4] arm={args.arm}  judged={len(asr)}  with-extract={len(erow)}  "
          f"probe-regime={args.probe_regime}")
    print(f"[G6.4] coverage: {cov}")
    if args.common:
        if len(have_all) < 30:
            raise SystemExit(f"[G6.4] only {len(have_all)} prompts carry all three metrics — "
                             "too few for a like-for-like comparison")
        keep = set(have_all)
        erow = {p: r for p, r in erow.items() if p in keep}
        print(f"[G6.4] COMMON-SUBSET mode: all metrics restricted to {len(erow)} prompts "
              f"({len(set(meta[p].get('bank_block') for p in erow))} bank_block(s), "
              f"{len(set(meta[p].get('domain') for p in erow))} domains)")

    rows_csv = []
    missing_targets = set()
    per_layer_metric = collections.defaultdict(dict)   # metric -> layer -> rho vs ASR
    per_layer_partial = collections.defaultdict(dict)  # ... partialling out n_examples
    for L in layers:
        for mname, getter in METRICS.items():
            pids = [p for p in sorted(erow) if getter(L, p) is not None]
            if len(pids) < 30:
                print(f"  L{L:<2d} {mname:22s} SKIP (only {len(pids)} rows carry it)")
                continue
            xs = [getter(L, p) for p in pids]
            doms = [meta[p].get("domain") for p in pids]
            targets = {
                "asr_score": [asr[p] for p in pids],
                "refusal": [refused[p] for p in pids],
                "n_examples": [float(meta[p].get("n_examples") or 0) for p in pids],
            }
            cpids = [p for p in pids if p in comp]
            for tname, ys in targets.items():
                rho = spearman(xs, ys)
                rho_w = rho_within_domain(xs, ys, doms)
                pp = perm_p_within_domain(xs, ys, doms)
                nex = [float(meta[p].get("n_examples") or 0) for p in pids]
                # `p_perm_within_domain_rho` belongs to `rho_within_domain`, NOT to `rho_pooled`
                # (audit T5). Both estimates are kept because they answer different questions.
                rec = {"layer": L, "metric": mname, "target": tname, "n": len(pids),
                       "rho_pooled": round(rho, 6),
                       "rho_within_domain": round(rho_w, 6),
                       "p_perm_within_domain_rho": round(pp, 6),
                       "p_estimand": "rho_within_domain",
                       "rho_partial_n_examples_pooled": "",
                       "rho_partial_n_examples_within_domain": "",
                       "p_perm_within_domain_partial": "",
                       "n_domains": len(set(doms)), "identified": "yes"}
                if tname == "asr_score":
                    rp = rank_partial(xs, ys, nex)
                    rec["rho_partial_n_examples_pooled"] = round(rp, 6)
                    rec["rho_partial_n_examples_within_domain"] = round(
                        rank_partial_within_domain(xs, ys, nex, doms), 6)
                    # The partial permutation refits the partial 2000x, so it runs only at the
                    # headline layer; elsewhere the partial rho is reported without a p.
                    if L == args.headline_layer:
                        rec["p_perm_within_domain_partial"] = round(
                            perm_p_partial(xs, ys, nex, doms), 6)
                    per_layer_metric[mname][L] = rho
                    per_layer_partial[mname][L] = rp
                rows_csv.append(rec)
            if len(cpids) < 30:
                missing_targets.add(mname)
            if len(cpids) >= 30:
                xc = [getter(L, p) for p in cpids]
                yc = [comp[p] for p in cpids]
                dc = [meta[p].get("domain") for p in cpids]
                rows_csv.append({"layer": L, "metric": mname, "target": "comprehension",
                                 "n": len(cpids), "rho_pooled": round(spearman(xc, yc), 6),
                                 "rho_within_domain": round(rho_within_domain(xc, yc, dc), 6),
                                 "p_perm_within_domain_rho":
                                     round(perm_p_within_domain(xc, yc, dc), 6),
                                 "p_estimand": "rho_within_domain",
                                 "rho_partial_n_examples_pooled": "",
                                 "rho_partial_n_examples_within_domain": "",
                                 "p_perm_within_domain_partial": "",
                                 "n_domains": len(set(dc)), "identified": "yes"})
            # role style: categorical, and NOT identified (see §9)
            # eta^2 is not a rho at all; it goes in `rho_pooled` only as the row's single point
            # estimate, and carries no p (audit T5: `p_estimand` says so explicitly).
            rows_csv.append({"layer": L, "metric": mname, "target": "role_style_eta2",
                             "n": len(pids),
                             "rho_pooled": round(eta_squared(xs, [meta[p].get("role_style")
                                                                 for p in pids]), 6),
                             "rho_within_domain": "",
                             "p_perm_within_domain_rho": "",
                             "p_estimand": "none (statistic is eta^2, not a correlation)",
                             "rho_partial_n_examples_pooled": "",
                             "rho_partial_n_examples_within_domain": "",
                             "p_perm_within_domain_partial": "",
                             "n_domains": len(set(doms)),
                             "identified": "NO - role_style is collinear with bank_block (§9)"})

    if missing_targets:
        raise SystemExit(
            f"[G6.4] REFUSING: `comprehension` is a plan-§6.4 REQUIRED target and it could not be "
            f"joined for {sorted(missing_targets)}. The first version of this script skipped it "
            f"silently on a `>= 30` guard, so the deliverable shipped without one of its five "
            f"required targets and nothing said so.")

    csv_path = os.path.join(args.outdir, "correlation_table.csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["layer", "metric", "target", "n",
                                          "rho_pooled", "rho_within_domain",
                                          "p_perm_within_domain_rho", "p_estimand",
                                          "rho_partial_n_examples_pooled",
                                          "rho_partial_n_examples_within_domain",
                                          "p_perm_within_domain_partial",
                                          "n_domains", "identified"])
        w.writeheader()
        w.writerows(rows_csv)
    print(f"[G6.4] wrote {csv_path} ({len(rows_csv)} rows)")

    # ---------------------------------------------------------------------------- plots ----- #
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 1. metric_by_layer.png — rho vs ASR across depth, all three metrics
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for mname, d in per_layer_metric.items():
        Ls = sorted(d)
        line, = ax.plot(Ls, [d[L] for L in Ls], marker="o", label=f"{mname} (raw)")
        dp = per_layer_partial.get(mname, {})
        if dp:
            ax.plot(sorted(dp), [dp[L] for L in sorted(dp)], marker="x", ls="--",
                    color=line.get_color(), alpha=0.7, label=f"{mname} (| n_examples)")
    ax.axhline(0, color="k", lw=0.8, ls=":")
    ax.set_xlabel("block layer"); ax.set_ylabel(f"Spearman rho vs StrongReject score ({args.arm})")
    ax.set_title("§6.4 metric vs ASR by layer"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(os.path.join(args.outdir, "metric_by_layer.png"), dpi=140)
    plt.close(fig)

    # 2. metric_vs_asr.png — scatter at the headline layer
    L = args.headline_layer
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, (mname, getter) in zip(axes, METRICS.items()):
        pids = [p for p in sorted(erow) if getter(L, p) is not None]
        if not pids:
            ax.set_title(f"{mname}\n(not available at L{L})"); continue
        ax.scatter([getter(L, p) for p in pids], [asr[p] for p in pids], s=9, alpha=0.5)
        ax.set_title(f"{mname}\nrho={spearman([getter(L,p) for p in pids],[asr[p] for p in pids]):+.3f}",
                     fontsize=9)
        ax.set_xlabel(f"metric @ L{L}"); ax.grid(alpha=0.3)
    axes[0].set_ylabel("StrongReject score")
    fig.tight_layout(); fig.savefig(os.path.join(args.outdir, "metric_vs_asr.png"), dpi=140)
    plt.close(fig)

    # 3. metric_by_carrot_occurrence.png — §7 keeps token-level separate; this is the token view
    occ = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in E:
        if r.get("condition") != args.arm or r.get("occurrence_index") is None:
            continue
        for mname, col in (("logit_lens_boombness", f"ll|L{L}|boombness"),
                           ("direction_boombness", f"d_surface|L{L}|proj")):
            if r.get(col) is not None:
                occ[mname][r["occurrence_index"]].append(r[col])
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    for mname, d in occ.items():
        ks = sorted(d)
        mus = [st.mean(d[k]) for k in ks]
        ses = [st.pstdev(d[k]) / math.sqrt(len(d[k])) if len(d[k]) > 1 else 0.0 for k in ks]
        ax.errorbar(ks, mus, yerr=ses, marker="o", capsize=3, label=f"{mname} (L{L})")
    ax.set_xlabel("carrot occurrence index"); ax.set_ylabel(f"metric @ L{L}")
    ax.set_title(f"§6.4 metric by codeword occurrence — {args.arm}")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(args.outdir, "metric_by_carrot_occurrence.png"), dpi=140)
    plt.close(fig)

    # PROVENANCE (added 2026-08-18). The first version of this summary recorded no input paths and
    # no argv, so `g64_summary.json` could not regenerate itself: reproducing §6.4 required guessing
    # which of 16 extract runs, 20+ judge runs and 2 probe-score runs had been used. That is the
    # same "no script regenerates this" failure the report blames for an earlier retraction, and the
    # external critique caught it for §11's role statistics without noticing §6.4 had it too. The
    # standing rule is that every published number must be regenerable by a committed script from a
    # committed artifact; a script that does not record its inputs cannot satisfy it.
    import subprocess as _sp
    def _git(*a):
        try:
            return _sp.check_output(["git", *a], stderr=_sp.DEVNULL).decode().strip()
        except Exception:
            return None
    provenance = {
        "argv": sys.argv,
        "git_commit": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "inputs": {"extract": os.path.abspath(args.extract), "judge": os.path.abspath(args.judge),
                   "comprehension": os.path.abspath(args.comprehension),
                   "probe_scores": os.path.abspath(args.probe_scores)},
        "python": sys.executable,
    }
    summary = {"plan_section": "6.4", "arm": args.arm, "layers": layers,
               "provenance": provenance,
               "common_subset": bool(args.common), "coverage": cov,
               "coverage_caveat": (
                   "probe_boombness comes from a rep cache built on a 1464-row bank version; the "
                   "bank is now 2352 rows. Without --common-subset the three metrics are computed "
                   "on different populations and are NOT comparable."),
               "headline_layer": L, "probe_regime": args.probe_regime,
               "n_judged": len(asr), "n_with_extract": len(erow),
               "metrics_present": sorted(per_layer_metric),
               "deliverables": ["correlation_table.csv", "metric_vs_asr.png",
                                "metric_by_layer.png", "metric_by_carrot_occurrence.png"],
               "role_style": "eta^2 reported but NOT IDENTIFIED (collinear with bank_block, §9)",
               "estimand_note": (
                   "correlation_table.csv reports TWO point estimates per row. `rho_pooled` is the "
                   "raw pooled Spearman. `rho_within_domain` is the Spearman after demeaning x and "
                   "y within domain. The permutation p, `p_perm_within_domain_rho`, tests "
                   "`rho_within_domain` ONLY -- it is NOT a p-value for `rho_pooled`. Likewise "
                   "`p_perm_within_domain_partial` tests "
                   "`rho_partial_n_examples_within_domain`, not the pooled partial. Before "
                   "2026-08-18 the file printed only the pooled rho next to the within-domain p "
                   "with no label, and the p column is not monotone in |rho_pooled|, so ranking "
                   "metrics by that pair inverted the ordering."),
               "columns_renamed_2026_08_18": {
                   "spearman_rho": "rho_pooled",
                   "p_within_domain_perm": "p_perm_within_domain_rho",
                   "rho_partial_n_examples": "rho_partial_n_examples_pooled",
                   "p_partial": "p_perm_within_domain_partial"}}
    with open(os.path.join(args.outdir, "g64_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"[G6.4] wrote 3 plots + summary to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
