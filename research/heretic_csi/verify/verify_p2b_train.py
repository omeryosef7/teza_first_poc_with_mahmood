#!/usr/bin/env python
"""Independent recomputation of the P2b TRAIN-K4 primary / secondary verdicts (review #5).

Written from the preregistration text (PREREG_P2B + amendments 1-6), NOT from p2b_analyze.py.
Reads ONLY TRAIN-K4 run dirs: outputs/boombness/score_behavior/hcsi_p2b_<cw>_k4_<ARM>_<YYYYMMDD>_<HHMMSS>_<pid>.
Overlap dirs (k4ovl / k4aovl / k4nmovl / k4ovln501) do not match the strict prefix and are never read, except
k4nmovl_KO, which is read ONLY to check it equals the main KO (host equivalence for the descriptive NM arm).
No VALIDATION (hcsi_p2b_*_val_*) dir is touched.

Definitions used (from the prereg text):
  y        = sigmoid(logp_concept - logp_codeword) per row; key = (domain, slotN from family_id)
  key set  = keys with BASE option_mass >= 0.05, intersected with keys present in every arm of the family
  stat(A)  = mean over domains of [mean over that domain's keys of (y_A - y_KO)]
  rank p   = (1 + #controls with stat >= cand stat) / (N + 1)   (ties count against the candidate)
  Holm     = m=2 over ranks {1,4} per codeword, separately for primary and secondary
  recovery = mean_d(A-KO) / mean_d(KO_FULL-KO); CI95 = percentile domain bootstrap (B draws)
  PASS     = Holm p < 0.05 AND recovery CI-lo > 0 (gates checked separately below)
Usage: python verify_p2b_train.py --out <json> [--boot 10000]
"""
import argparse, glob, json, math, os, re, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SB = os.path.join(ROOT, "outputs", "boombness", "score_behavior")
FLOOR = 0.05


def find_dir(cw, arm, prefix=None):
    prefix = prefix or f"hcsi_p2b_{cw}_k4"
    pat = re.compile(r"^" + re.escape(f"{prefix}_{arm}") + r"_\d{8}_\d{6}_\d+$")
    cands = [d for d in os.listdir(SB) if pat.match(d)]
    good = []
    for d in cands:
        p = os.path.join(SB, d)
        dj = os.path.join(p, "DONE.json")
        if not os.path.exists(dj):
            continue
        done = json.load(open(dj))
        if done.get("status") != "ok" or done.get("rows_written") != 268:
            continue
        good.append(d)
    if len(good) != 1:
        raise RuntimeError(f"{cw} {arm}: {len(good)} complete dirs among {cands}")
    return good[0], [c for c in cands if c not in good]


_cache = {}


def load(cw, arm, prefix=None):
    k = (cw, arm, prefix)
    if k in _cache:
        return _cache[k]
    d, skipped = find_dir(cw, arm, prefix)
    rows = {}
    for line in open(os.path.join(SB, d, "results.jsonl")):
        r = json.loads(line)
        slot = r["family_id"].split("|")[2]
        key = (r["domain"], slot)
        assert key not in rows, (d, key)
        lc, lw = r["logp_concept"], r["logp_codeword"]
        y = 1.0 / (1.0 + math.exp(-(lc - lw)))
        rows[key] = dict(y=y, om=r["option_mass"], lc=lc, lw=lw)
    cfg = json.load(open(os.path.join(SB, d, "config.json")))
    a = cfg["args"]
    meta = dict(dir=d, job=d.rsplit("_", 1)[1], skipped=skipped, exclude=a.get("exclude_prompt_ids"),
                bank=a.get("bank"), model=a.get("model"))
    _cache[k] = (rows, meta)
    return _cache[k]


def keyset(cw, arms, extra_floor_arms=()):
    base, _ = load(cw, "BASE")
    ks = {k for k, v in base.items() if v["om"] >= FLOOR}
    for a in arms:
        ks &= set(load(cw, a)[0].keys())
    for a in extra_floor_arms:
        r = load(cw, a)[0]
        ks &= {k for k, v in r.items() if v["om"] >= FLOOR}
    return sorted(ks)


def dom_diffs(cw, arm, keys, ref="KO", drop=None):
    A, R = load(cw, arm)[0], load(cw, ref)[0]
    by = {}
    for k in keys:
        if drop is not None and k[0] == drop:
            continue
        by.setdefault(k[0], []).append(A[k]["y"] - R[k]["y"])
    doms = sorted(by)
    return doms, np.array([np.mean(by[d]) for d in doms])


def stat(cw, arm, keys, drop=None):
    return float(dom_diffs(cw, arm, keys, drop=drop)[1].mean())


def row_stat(cw, arm, keys):
    A, R = load(cw, arm)[0], load(cw, "KO")[0]
    return float(np.mean([A[k]["y"] - R[k]["y"] for k in keys]))


def rank_p(c, ctrl):
    n_ge = sum(1 for x in ctrl if x >= c)
    return 1 + n_ge, (1 + n_ge) / (len(ctrl) + 1)


def holm2(p1, p4):
    ps = sorted([(p1, 1), (p4, 4)])
    adj = {}
    a1 = min(1.0, 2 * ps[0][0])
    a2 = min(1.0, max(a1, ps[1][0]))
    adj[ps[0][1]] = a1
    adj[ps[1][1]] = a2
    return adj


def boot_ratio(num, den, B, seed):
    rng = np.random.default_rng(seed)
    n = len(num)
    idx = rng.integers(0, n, size=(B, n))
    r = num[idx].mean(1) / den[idx].mean(1)
    return float(num.mean() / den.mean()), [float(np.percentile(r, 2.5)), float(np.percentile(r, 97.5))]


def boot_mean(x, B, seed):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(1)
    return float(x.mean()), [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def fam(cw, r, kind):
    if kind == "primary":
        return ([f"KO_RAND_r{r}_{i}" for i in range(61)] + [f"KO_SHUF_r{r}_{i}" for i in range(5)]
                + [f"KO_DER_r{r}_{i}" for i in range(15)])
    if kind == "secondary":
        return [f"KO_CWRAND_r{r}_{i}" for i in range(61)] + [f"KO_CWDER_r{r}_{i}" for i in range(15)]
    if kind == "DERRAW":
        return [f"KO_DERRAW_r{r}_{i}" for i in range(15)]
    if kind == "SHUFRAW":
        return [f"KO_SHUFRAW_r{r}_{i}" for i in range(5)]
    raise KeyError(kind)


def cell(cw, r, kind, B, strict=None):
    cand = f"KO_CAND_r{r}" if kind == "primary" else f"KO_CWONLY_r{r}"
    ctrl = fam(cw, r, kind)
    arms = ["KO", "KO_FULL", cand] + ctrl
    extra = ()
    if strict == "cand_ko":
        extra = ("KO", cand)
    elif strict == "all":
        extra = tuple(arms)
    keys = keyset(cw, arms, extra)
    c = stat(cw, cand, keys)
    cs = {a: stat(cw, a, keys) for a in ctrl}
    rk, p = rank_p(c, list(cs.values()))
    doms, num = dom_diffs(cw, cand, keys)
    _, den = dom_diffs(cw, "KO_FULL", keys)
    rec, ci = boot_ratio(num, den, B, 12345 + r)
    top = sorted(cs.items(), key=lambda kv: -kv[1])[:3]
    return dict(cand=cand, n_keys=len(keys), n_domains=len(doms), stat=round(c, 5), rank=rk, of=len(ctrl) + 1,
                p=p, recovery=round(rec, 4), ci95=[round(x, 4) for x in ci],
                top3_controls=[(a, round(v, 5)) for a, v in top], keys=keys, ctrl=ctrl)


def sub_rank(cw, cand, ctrl, keys, drop=None):
    c = stat(cw, cand, keys, drop)
    return rank_p(c, [stat(cw, a, keys, drop) for a in ctrl])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()
    B = a.boot
    out = {"schema": "verify_p2b_train/1", "boot": B, "floor": FLOOR, "codewords": {}}
    for cw in ["basket", "button"]:
        O = {}
        # ---- gates
        g = {}
        kall = keyset(cw, ["KO", "KO_FULL", "KO_IDENT"])
        g["n_keys_base_floor"] = len(kall)
        g["KO_minus_BASE"] = round(-stat(cw, "BASE", kall), 5)
        g["FULL_minus_KO"] = round(stat(cw, "KO_FULL", kall), 5)
        ko, idn = load(cw, "KO")[0], load(cw, "KO_IDENT")[0]
        g["ident_max_abs_dy"] = max(abs(ko[k]["y"] - idn[k]["y"]) for k in ko)
        g["median_om"] = {x: float(np.median([v["om"] for v in load(cw, x)[0].values()]))
                          for x in ["BASE", "KO", "KO_FULL", "KO_IDENT"]}
        O["gates"] = g
        # ---- primary / secondary
        for kind in ["primary", "secondary"]:
            res = {r: cell(cw, r, kind, B) for r in (1, 4)}
            h = holm2(res[1]["p"], res[4]["p"])
            for r in (1, 4):
                res[r]["holm"] = h[r]
                res[r]["verdict"] = "PASS" if (h[r] < 0.05 and res[r]["ci95"][0] > 0) else "NOT PASS"
            O[kind] = res
        # ---- per-cell extras
        for r in (1, 4):
            P = O["primary"][r]
            keys, cand = P["keys"], P["cand"]
            ex = {}
            ex["rank_RAND_only"] = sub_rank(cw, cand, fam(cw, r, "primary")[:61], keys)
            ex["rank_SHUF_only"] = sub_rank(cw, cand, fam(cw, r, "primary")[61:66], keys)
            ex["rank_DER_only"] = sub_rank(cw, cand, fam(cw, r, "primary")[66:], keys)
            kr = keyset(cw, ["KO", cand] + fam(cw, r, "DERRAW") + fam(cw, r, "SHUFRAW"))
            ex["rank_DERRAW"] = sub_rank(cw, cand, fam(cw, r, "DERRAW"), kr)
            ex["rank_SHUFRAW"] = sub_rank(cw, cand, fam(cw, r, "SHUFRAW"), kr)
            ex["DER_stats"] = sorted(round(stat(cw, x, keys), 5) for x in fam(cw, r, "primary")[66:])
            ex["DERRAW_stats"] = sorted(round(stat(cw, x, kr), 5) for x in fam(cw, r, "DERRAW"))
            ex["SHUF_stats"] = sorted(round(stat(cw, x, keys), 5) for x in fam(cw, r, "primary")[61:66])
            ex["RAND_max"] = round(max(stat(cw, x, keys) for x in fam(cw, r, "primary")[:61]), 5)
            # CAND minus mean DER (paired by domain)
            _, dc = dom_diffs(cw, cand, keys)
            der = np.mean([dom_diffs(cw, x, keys)[1] for x in fam(cw, r, "primary")[66:]], axis=0)
            ex["CAND_minus_meanDER"] = boot_mean(dc - der, B, 7)
            ex["meanDER_recovery"] = round(float(der.mean() / dom_diffs(cw, "KO_FULL", keys)[1].mean()), 4)
            # position + NEUT
            kp = keyset(cw, ["KO", "KO_FULL", cand, f"KO_CWONLY_r{r}", f"KO_ATLAST_r{r}", f"KO_NEUT_r{r}"])
            _, dfull = dom_diffs(cw, "KO_FULL", kp)
            pos = {}
            for x in [cand, f"KO_CWONLY_r{r}", f"KO_ATLAST_r{r}", f"KO_NEUT_r{r}"]:
                _, dx = dom_diffs(cw, x, kp)
                pos[x] = dict(stat=round(float(dx.mean()), 5), rec=boot_ratio(dx, dfull, B, 99))
            _, dn = dom_diffs(cw, f"KO_NEUT_r{r}", kp)
            _, dcd = dom_diffs(cw, cand, kp)
            _, dcw = dom_diffs(cw, f"KO_CWONLY_r{r}", kp)
            pos["NEUT_minus_CAND"] = boot_mean(dn - dcd, B, 11)
            pos["NEUT_minus_CWONLY"] = boot_mean(dn - dcw, B, 12)
            pos["CWONLY_minus_CAND"] = boot_mean(dcw - dcd, B, 13)
            # NEUT rank inside the primary family (descriptive; NEUT is NOT norm matched)
            pos["NEUT_rank_vs_primary_family"] = sub_rank(cw, f"KO_NEUT_r{r}", fam(cw, r, "primary"), keys)
            pos["NEUT_rank_vs_DER"] = sub_rank(cw, f"KO_NEUT_r{r}", fam(cw, r, "primary")[66:], keys)
            opn = {}
            for x in [cand, f"KO_NEUT_r{r}"]:
                oj = json.load(open(os.path.join(SB, load(cw, x)[1]["dir"], "p2b_operator.json")))
                mf = oj.get("module_fro", {})
                opn[x] = dict(opspec=oj.get("opspec"), where=oj.get("where", "all"), hook_calls=oj.get("hook_calls"),
                              sum_module_fro=round(sum(mf.values()), 3),
                              l2_module_fro=round(math.sqrt(sum(v * v for v in mf.values())), 3),
                              n_zero_modules=sum(1 for v in mf.values() if v == 0),
                              mean_last_pos_delta_norm=oj.get("mean_last_pos_delta_norm"))
            pos["operators"] = opn
            ex["position"] = pos
            # overshoot anatomy
            base, kod, full, cd = (load(cw, x)[0] for x in ["BASE", "KO", "KO_FULL", cand])
            _, dbase = dom_diffs(cw, "BASE", keys)
            _, dfl = dom_diffs(cw, "KO_FULL", keys)
            ex["overshoot"] = dict(
                CAND_over_BASEgap=boot_ratio(dc, dbase, B, 21),
                FULL_over_BASEgap=round(float(dfl.mean() / dbase.mean()), 4),
                n_domains=len(dc), n_dom_FULL_le0=int((dfl <= 0).sum()), n_dom_FULL_lt_0p02=int((dfl < 0.02).sum()),
                n_dom_CAND_gt_FULL=int((dc > dfl).sum()),
                n_dom_CAND_gt_BASEgap=int((dc > dbase).sum()),
                median_dom_FULL=round(float(np.median(dfl)), 4),
                rec_excl_small_den=(lambda m: round(float(dc[m].mean() / dfl[m].mean()), 4))(dfl >= 0.05),
                n_dom_den_ge_0p05=int((dfl >= 0.05).sum()),
                CAND_y_minus_BASE_y_rowmean=round(float(np.mean([cd[k]["y"] - base[k]["y"] for k in keys])), 4),
                trimmed_ratio_10pct=round(float(np.mean(np.sort(dc)[len(dc)//10: -len(dc)//10]) /
                                                np.mean(np.sort(dfl)[len(dfl)//10: -len(dfl)//10])), 4))
            # row-level statistic sensitivity
            ctrl = fam(cw, r, "primary")
            ex["row_level_rank"] = rank_p(row_stat(cw, cand, keys), [row_stat(cw, x, keys) for x in ctrl])
            O.setdefault("extras", {})[r] = ex
        # ---- strict-floor sensitivity
        st = {}
        for kind in ["primary", "secondary"]:
            for mode in ["cand_ko", "all"]:
                rr = {r: cell(cw, r, kind, 2000, strict=mode) for r in (1, 4)}
                h = holm2(rr[1]["p"], rr[4]["p"])
                st[f"{kind}_{mode}"] = {r: dict(n_keys=rr[r]["n_keys"], n_domains=rr[r]["n_domains"],
                                                rank=rr[r]["rank"], p=rr[r]["p"], holm=h[r], rec=rr[r]["recovery"],
                                                ci=rr[r]["ci95"]) for r in (1, 4)}
        O["strict_floor"] = st
        # ---- LODO on Holm (both families)
        lodo = {}
        for kind in ["primary", "secondary"]:
            K = {r: O[kind][r]["keys"] for r in (1, 4)}
            doms = sorted({k[0] for k in K[4]})
            res = []
            for dd in doms:
                p = {r: sub_rank(cw, O[kind][r]["cand"], O[kind][r]["ctrl"], K[r], drop=dd)[1] for r in (1, 4)}
                h = holm2(p[1], p[4])
                res.append((dd, p[1], p[4], h[1], h[4]))
            lodo[kind] = dict(
                n=len(res),
                n_r4_holm_lt_05=sum(1 for x in res if x[4] < 0.05),
                n_r1_holm_lt_05=sum(1 for x in res if x[3] < 0.05),
                max_holm_r4=max(x[4] for x in res), max_holm_r1=max(x[3] for x in res),
                domains_breaking_r4=[x[0] for x in res if x[4] >= 0.05][:20],
                domains_breaking_r1=[x[0] for x in res if x[3] >= 0.05][:20])
        O["lodo"] = lodo
        # ---- add-on descriptive: CWMEANBIAS and (basket only, if present) MEANBIAS_NM
        add = {}
        for x in ["KO_CWMEANBIAS", "KO_MEANBIAS_NM_r1", "KO_MEANBIAS_NM_r4"]:
            try:
                load(cw, x)
            except RuntimeError as e:
                add[x] = f"absent: {e}"
                continue
            kk = keyset(cw, ["KO", "KO_FULL", x])
            _, dx = dom_diffs(cw, x, kk)
            _, df = dom_diffs(cw, "KO_FULL", kk)
            add[x] = dict(stat=round(float(dx.mean()), 5), rec=boot_ratio(dx, df, B, 31),
                          median_om=float(np.median([v["om"] for v in load(cw, x)[0].values()])),
                          job=load(cw, x)[1]["job"])
            for r in (1, 4):
                if x.endswith(f"_r{r}") or x == "KO_CWMEANBIAS":
                    k2 = keyset(cw, ["KO", x, f"KO_CAND_r{r}", f"KO_NEUT_r{r}"])
                    _, a1 = dom_diffs(cw, f"KO_CAND_r{r}", k2)
                    _, a2 = dom_diffs(cw, x, k2)
                    _, a3 = dom_diffs(cw, f"KO_NEUT_r{r}", k2)
                    add[x][f"CAND_r{r}_minus"] = boot_mean(a1 - a2, B, 41)
                    add[x][f"NEUT_r{r}_minus"] = boot_mean(a3 - a2, B, 42)
        # nm-overlap KO equality (host check for the NM arm)
        try:
            kov, _ = load(cw, "KO", prefix=f"hcsi_p2b_{cw}_k4nmovl")
            add["nmovl_KO_max_abs_dy"] = max(abs(kov[k]["y"] - ko[k]["y"]) for k in ko)
        except Exception as e:
            add["nmovl_KO_max_abs_dy"] = f"n/a: {e}"
        O["addon_descriptive"] = add
        # ---- provenance
        prov = {}
        for r in (1, 4):
            for kind in ["primary", "secondary"]:
                for x in ["KO", "BASE", "KO_FULL", O[kind][r]["cand"]] + O[kind][r]["ctrl"]:
                    m = load(cw, x)[1]
                    prov[x] = m["job"]
                    assert m["exclude"] == f"runargs/heretic_csi/exclude_{cw}_K4.txt", (x, m["exclude"])
                    assert m["bank"].endswith(f"ts116m_{cw}_bomb.jsonl"), (x, m["bank"])
        from collections import Counter
        O["provenance_job_counts"] = dict(Counter(prov.values()))
        O["skipped_partial_dirs"] = sorted({s for (c2, _, _), (_, m) in _cache.items() if c2 == cw for s in m["skipped"]})
        for kind in ["primary", "secondary"]:
            for r in (1, 4):
                O[kind][r].pop("keys"); O[kind][r].pop("ctrl")
        out["codewords"][cw] = O
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    for cw, O in out["codewords"].items():
        for kind in ["primary", "secondary"]:
            for r in (1, 4):
                c = O[kind][r]
                print(cw, kind, r, c["n_keys"], c["n_domains"], c["stat"], f"{c['rank']}/{c['of']}",
                      round(c["holm"], 4), c["recovery"], c["ci95"], c["verdict"])


if __name__ == "__main__":
    main()
