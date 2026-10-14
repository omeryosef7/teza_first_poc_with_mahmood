#!/usr/bin/env python
"""Independent recomputation of the P2b VALIDATION primary / secondary verdicts (review #6).

Written from the preregistration text (PREREG_P2B + amendments 1-7 + PREREG_P2B_VALIDATION), NOT from
p2b_analyze.py. Extends the reviewer's own verify_p2b_train.py (review #5) to the VALIDATION population.
Reads ONLY VAL run dirs hcsi_p2b_<cw>_val_<ARM>_<YYYYMMDD>_<HHMMSS>_<pid> (strict regex: *valovl* / *valaovl*
overlap dirs never match) plus, for leakage/provenance checks only, TRAIN-K4 KO/CAND dirs and the TRAIN capture
run dirs (domains + factor sha).

Definitions:
  y        = sigmoid(logp_concept - logp_codeword) per row; key = (domain, family_id minus domain and query_kind)  [VAL has dev|slotN AND heldout|slotN]
  key set  = keys with BASE option_mass >= 0.05, intersected with keys present in every arm of the family
  stat(A)  = mean over domains of [mean over that domain's keys of (y_A - y_KO)]
  rank p   = (1 + #controls with stat >= cand stat) / (N + 1)   (ties count against the candidate)
  Holm     = m=2 over ranks {1,4} per codeword, separately for primary and secondary
  recovery = mean_d(A-KO) / mean_d(KO_FULL-KO); CI95 = percentile domain bootstrap
  PASS     = Holm p < 0.05 AND recovery CI-lo > 0 AND gates/VOID screens clean
Usage: python verify_p2b_val.py --out <json> [--boot 10000]
"""
import argparse, glob, json, math, os, re
from collections import Counter
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SB = os.path.join(ROOT, "outputs", "boombness", "score_behavior")
FLOOR = 0.05
NROWS = 230


def find_dir(cw, arm, prefix=None, nrows=NROWS):
    prefix = prefix or f"hcsi_p2b_{cw}_val"
    pat = re.compile(r"^" + re.escape(f"{prefix}_{arm}") + r"_\d{8}_\d{6}_\d+$")
    cands = [d for d in os.listdir(SB) if pat.match(d)]
    good = []
    for d in cands:
        dj = os.path.join(SB, d, "DONE.json")
        if not os.path.exists(dj):
            continue
        done = json.load(open(dj))
        if done.get("status") != "ok" or done.get("rows_written") != nrows:
            continue
        good.append(d)
    if len(good) != 1:
        raise RuntimeError(f"{cw} {arm}: {len(good)} complete dirs among {cands}")
    return good[0], [c for c in cands if c not in good]


_cache = {}


def load(cw, arm, prefix=None, nrows=NROWS):
    k = (cw, arm, prefix)
    if k in _cache:
        return _cache[k]
    d, skipped = find_dir(cw, arm, prefix, nrows)
    rows = {}
    for line in open(os.path.join(SB, d, "results.jsonl")):
        r = json.loads(line)
        slot = "|".join(r["family_id"].split("|")[1:-1])  # split+slot+cell fields; dev|slot0 != heldout|slot0
        key = (r["domain"], slot)
        assert key not in rows, (d, key)
        lc, lw = r["logp_concept"], r["logp_codeword"]
        rows[key] = dict(y=1.0 / (1.0 + math.exp(-(lc - lw))), om=r["option_mass"], lc=lc, lw=lw, pid=r["prompt_id"])
    a = json.load(open(os.path.join(SB, d, "config.json")))["args"]
    rm = json.load(open(os.path.join(SB, d, "RUNMETA.json")))
    opj = os.path.join(SB, d, "p2b_operator.json")
    op = json.load(open(opj)) if os.path.exists(opj) else {}
    meta = dict(dir=d, job=str(rm.get("slurm_job_id")), host=rm.get("hostname"), gpu=rm.get("gpu"), skipped=skipped,
                exclude=a.get("exclude_prompt_ids"), bank=a.get("bank"), attn=a.get("attn_impl"), dtype=a.get("dtype"),
                hook_calls=op.get("hook_calls"), factors_sha16=op.get("factors_sha16"), opspec=op.get("opspec"),
                op=op)
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


def stat(cw, arm, keys, drop=None, ref="KO"):
    return float(dom_diffs(cw, arm, keys, ref=ref, drop=drop)[1].mean())


def row_stat(cw, arm, keys):
    A, R = load(cw, arm)[0], load(cw, "KO")[0]
    return float(np.mean([A[k]["y"] - R[k]["y"] for k in keys]))


def rank_p(c, ctrl):
    n_ge = sum(1 for x in ctrl if x >= c)
    return 1 + n_ge, (1 + n_ge) / (len(ctrl) + 1)


def holm2(p1, p4):
    ps = sorted([(p1, 1), (p4, 4)])
    a1 = min(1.0, 2 * ps[0][0])
    a2 = min(1.0, max(a1, ps[1][0]))
    return {ps[0][1]: a1, ps[1][1]: a2}


def boot_ratio(num, den, B, seed):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(num), size=(B, len(num)))
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
    best_other = max(v for a, v in cs.items() if v < c) if any(v < c for v in cs.values()) else None
    return dict(cand=cand, n_keys=len(keys), n_domains=len(doms), stat=round(c, 5), rank=rk, of=len(ctrl) + 1,
                p=p, recovery=round(rec, 4), ci95=[round(x, 4) for x in ci],
                top3_controls=[(a, round(v, 5)) for a, v in top],
                margin_to_best_control=round(c - top[0][1], 5),
                margin_to_next_below=None if best_other is None else round(c - best_other, 5),
                n_controls_beating=sum(1 for v in cs.values() if v >= c),
                keys=keys, ctrl=ctrl)


def sub_rank(cw, cand, ctrl, keys, drop=None):
    c = stat(cw, cand, keys, drop)
    return rank_p(c, [stat(cw, a, keys, drop) for a in ctrl])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()
    B = a.boot
    out = {"schema": "verify_p2b_val/1", "boot": B, "floor": FLOOR, "codewords": {}}
    split = json.load(open(os.path.join(ROOT, "data/boombness_prompts/dcs_ts116_domain_split.json")))
    import ast
    assign = split["assign"] if isinstance(split["assign"], dict) else ast.literal_eval(split["assign"])
    for cw in ["basket", "button"]:
        O = {}
        # ---- population / leakage
        base = load(cw, "BASE")[0]
        vdoms = sorted({k[0] for k in base})
        pop = dict(n_rows=len(base), n_domains=len(vdoms),
                   rows_per_domain=sorted(Counter(k[0] for k in base).values())[::max(1, len(vdoms) - 1)],
                   all_domains_validation_in_frozen_split=all(assign.get(d) == "validation" for d in vdoms))
        tr = load(cw, "KO", prefix=f"hcsi_p2b_{cw}_k4", nrows=268)[0]
        capd = glob.glob(os.path.join(SB, f"hcsi_p2b_cap_{cw}_KO_2026*"))
        capdoms, capids = set(), set()
        for d in capd:
            for line in open(os.path.join(d, "results.jsonl")):
                rr = json.loads(line); capdoms.add(rr["domain"]); capids.add(rr["prompt_id"])
        pop["val_domains_in_TRAIN_K4"] = len(set(vdoms) & {k[0] for k in tr})
        pop["val_domains_in_fit_captures"] = len(set(vdoms) & capdoms)
        pop["val_prompt_ids_in_fit_captures"] = len({v["pid"] for v in base.values()} & capids)
        pop["n_capture_dirs"] = len(capd)
        O["population"] = pop
        # ---- gates
        g = {}
        kall = keyset(cw, ["KO", "KO_FULL", "KO_IDENT"])
        g["n_keys_base_floor"] = len(kall)
        g["KO_minus_BASE"] = round(-stat(cw, "BASE", kall), 5)
        g["FULL_minus_KO"] = round(stat(cw, "KO_FULL", kall), 5)
        ko, idn = load(cw, "KO")[0], load(cw, "KO_IDENT")[0]
        g["ident_max_abs_dy"] = max(abs(ko[k]["y"] - idn[k]["y"]) for k in ko)
        g["ident_hook_calls"] = load(cw, "KO_IDENT")[1]["hook_calls"]
        med = {}
        for x in ["BASE", "KO", "KO_FULL", "KO_IDENT", "KO_CAND_r1", "KO_CAND_r4", "KO_CWONLY_r1", "KO_CWONLY_r4",
                  "BASE_CAND_r1", "BASE_CAND_r4", "KO_MEANBIAS", "KO_CWMEANBIAS", "KO_NEUT_r1", "KO_NEUT_r4"]:
            med[x] = float(np.median([v["om"] for v in load(cw, x)[0].values()]))
        g["median_om"] = med
        g["collapse_void_required_arms"] = [x for x in ["BASE", "KO", "KO_FULL", "KO_IDENT", "KO_CAND_r1", "KO_CAND_r4",
                                                         "KO_CWONLY_r1", "KO_CWONLY_r4"] if med[x] < 0.05]
        for r in (1, 4):
            c, cp = load(cw, f"KO_CAND_r{r}")[0], load(cw, f"KO_CAPOP_r{r}")[0]
            g[f"CAPOP_r{r}_max_abs_dy_vs_CAND"] = max(abs(c[k]["y"] - cp[k]["y"]) for k in c)
            g[f"CAND_r{r}_hook_calls"] = load(cw, f"KO_CAND_r{r}")[1]["hook_calls"]
            g[f"CWONLY_r{r}_hook_calls"] = load(cw, f"KO_CWONLY_r{r}")[1]["hook_calls"]
            g[f"preservation_BASE_CAND_r{r}_minus_BASE"] = round(stat(cw, f"BASE_CAND_r{r}", kall, ref="BASE"), 5)
        O["gates"] = g
        # ---- primary / secondary
        for kind in ["primary", "secondary"]:
            res = {r: cell(cw, r, kind, B) for r in (1, 4)}
            h = holm2(res[1]["p"], res[4]["p"])
            for r in (1, 4):
                res[r]["holm"] = h[r]
                res[r]["verdict"] = "PASS" if (h[r] < 0.05 and res[r]["ci95"][0] > 0) else "NOT PASS"
            O[kind] = res
        # ---- control norm matching (from operator json module_fro)
        nm = {}
        for r in (1, 4):
            cf = load(cw, f"KO_CAND_r{r}")[1]["op"].get("module_fro", {})
            if isinstance(cf, str):
                import ast as _a; cf = _a.literal_eval(cf)
            worst = 0.0
            for x in fam(cw, r, "primary"):
                mf = load(cw, x)[1]["op"].get("module_fro", {})
                if isinstance(mf, str):
                    import ast as _a; mf = _a.literal_eval(mf)
                for m, v in cf.items():
                    worst = max(worst, abs(mf.get(m, 0.0) - v) / max(v, 1e-12))
            nm[f"r{r}_max_rel_module_fro_dev_primary_controls"] = worst
        O["norm_match"] = nm
        # ---- extras
        for r in (1, 4):
            P = O["primary"][r]
            keys, cand = P["keys"], P["cand"]
            ex = {}
            pf = fam(cw, r, "primary")
            ex["rank_RAND_only"] = sub_rank(cw, cand, pf[:61], keys)
            ex["rank_SHUF_only"] = sub_rank(cw, cand, pf[61:66], keys)
            ex["rank_DER_only"] = sub_rank(cw, cand, pf[66:], keys)
            kr = keyset(cw, ["KO", "KO_FULL", cand] + fam(cw, r, "DERRAW") + fam(cw, r, "SHUFRAW"))
            ex["rank_DERRAW"] = sub_rank(cw, cand, fam(cw, r, "DERRAW"), kr)
            ex["rank_SHUFRAW"] = sub_rank(cw, cand, fam(cw, r, "SHUFRAW"), kr)
            ex["rank_vs_primary_with_DER_replaced_by_DERRAW"] = sub_rank(
                cw, cand, pf[:66] + fam(cw, r, "DERRAW"), keyset(cw, ["KO", "KO_FULL", cand] + pf[:66] + fam(cw, r, "DERRAW")))
            ex["DER_stats"] = sorted(round(stat(cw, x, keys), 5) for x in pf[66:])
            ex["DERRAW_stats"] = sorted(round(stat(cw, x, kr), 5) for x in fam(cw, r, "DERRAW"))
            ex["cand_stat_on_DERRAW_keys"] = round(stat(cw, cand, kr), 5)
            ex["SHUF_stats"] = sorted(round(stat(cw, x, keys), 5) for x in pf[61:66])
            ex["RAND_max"] = round(max(stat(cw, x, keys) for x in pf[:61]), 5)
            _, dc = dom_diffs(cw, cand, keys)
            derm = np.array([dom_diffs(cw, x, keys)[1] for x in pf[66:]])
            der = derm.mean(0)
            ex["CAND_minus_meanDER"] = boot_mean(dc - der, B, 7)
            ex["CAND_minus_bestDER_paired"] = boot_mean(dc - derm[int(np.argmax(derm.mean(1)))], B, 8)
            ex["n_domains_CAND_gt_meanDER"] = int((dc > der).sum())
            ex["meanDER_recovery"] = round(float(der.mean() / dom_diffs(cw, "KO_FULL", keys)[1].mean()), 4)
            # position + NEUT (amendment 7)
            arms_pos = [cand, f"KO_CWONLY_r{r}", f"KO_ATLAST_r{r}", f"KO_NEUT_r{r}", f"KO_NEUT_CWONLY_r{r}",
                        f"KO_NEUT_ATLAST_r{r}"]
            kp = keyset(cw, ["KO", "KO_FULL"] + arms_pos)
            _, dfull = dom_diffs(cw, "KO_FULL", kp)
            _, dgap = dom_diffs(cw, "BASE", kp)
            pos = {"n_keys": len(kp)}
            dd = {}
            for x in arms_pos:
                _, dx = dom_diffs(cw, x, kp)
                dd[x] = dx
                pos[x] = dict(stat=boot_mean(dx, B, 99), rec=boot_ratio(dx, dfull, B, 99),
                              frac_BASE_KO_gap=boot_ratio(dx, dgap, B, 98),
                              hook_calls=load(cw, x)[1]["hook_calls"])
            pos["NEUT_minus_CAND"] = boot_mean(dd[f"KO_NEUT_r{r}"] - dd[cand], B, 11)
            pos["CWONLY_minus_CAND"] = boot_mean(dd[f"KO_CWONLY_r{r}"] - dd[cand], B, 13)
            pos["NEUT_rank_vs_primary_family"] = sub_rank(cw, f"KO_NEUT_r{r}", pf, keys)
            pos["NEUT_rank_vs_DER"] = sub_rank(cw, f"KO_NEUT_r{r}", pf[66:], keys)
            pos["NEUT_sum_module_fro_over_CAND"] = None
            try:
                import ast as _a
                f1 = load(cw, f"KO_NEUT_r{r}")[1]["op"].get("module_fro"); f2 = load(cw, cand)[1]["op"].get("module_fro")
                f1 = _a.literal_eval(f1) if isinstance(f1, str) else f1
                f2 = _a.literal_eval(f2) if isinstance(f2, str) else f2
                pos["NEUT_sum_module_fro_over_CAND"] = round(sum(f1.values()) / sum(f2.values()), 4)
            except Exception as e:
                pos["NEUT_sum_module_fro_over_CAND"] = f"n/a {e}"
            ex["position"] = pos
            ex["row_level_rank"] = rank_p(row_stat(cw, cand, keys), [row_stat(cw, x, keys) for x in pf])
            # decomposition (row-level mean dlogp vs KO)
            A, K = load(cw, cand)[0], load(cw, "KO")[0]
            ex["decomp_dlogp_concept"] = round(float(np.mean([A[k]["lc"] - K[k]["lc"] for k in keys])), 4)
            ex["decomp_dlogp_codeword"] = round(float(np.mean([A[k]["lw"] - K[k]["lw"] for k in keys])), 4)
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
        # ---- LODO
        lodo = {}
        for kind in ["primary", "secondary"]:
            K = {r: O[kind][r]["keys"] for r in (1, 4)}
            doms = sorted({k[0] for k in K[4]} | {k[0] for k in K[1]})
            res = []
            for dd_ in doms:
                rk = {r: sub_rank(cw, O[kind][r]["cand"], O[kind][r]["ctrl"], K[r], drop=dd_) for r in (1, 4)}
                h = holm2(rk[1][1], rk[4][1])
                res.append((dd_, rk[1][0], rk[4][0], h[1], h[4]))
            lodo[kind] = dict(
                n=len(res),
                r4_rank_counts=dict(Counter(x[2] for x in res)), r1_rank_counts=dict(Counter(x[1] for x in res)),
                n_r4_holm_lt_05=sum(1 for x in res if x[4] < 0.05),
                n_r1_holm_lt_05=sum(1 for x in res if x[3] < 0.05),
                max_holm_r4=max(x[4] for x in res), max_holm_r1=max(x[3] for x in res),
                domains_breaking_r4=[(x[0], x[2], round(x[4], 4)) for x in res if x[4] >= 0.05],
                domains_breaking_r1=[(x[0], x[1], round(x[3], 4)) for x in res if x[3] >= 0.05])
        O["lodo"] = lodo
        # ---- add-on descriptive
        add = {}
        for x in ["KO_CWMEANBIAS", "KO_MEANBIAS"]:
            kk = keyset(cw, ["KO", "KO_FULL", x])
            _, dx = dom_diffs(cw, x, kk)
            _, df = dom_diffs(cw, "KO_FULL", kk)
            add[x] = dict(stat=round(float(dx.mean()), 5), rec=boot_ratio(dx, df, B, 31),
                          median_om=float(np.median([v["om"] for v in load(cw, x)[0].values()])))
        add["KO_MEANBIAS_NM_present"] = [d for d in os.listdir(SB) if d.startswith(f"hcsi_p2b_{cw}_val_KO_MEANBIAS_NM")]
        O["addon_descriptive"] = add
        # ---- provenance / config gate / factor identity with TRAIN
        prov, viol, hosts = {}, [], Counter()
        exp_ex = f"runargs/dcs_cont/exclude_{cw}_bomb_sow_validation.txt"
        allarms = sorted({x for (c2, x, p), _ in _cache.items() if c2 == cw and p is None})
        for x in allarms:
            m = load(cw, x)[1]
            prov[x] = m["job"]; hosts[(m["job"], m["host"], m["gpu"])] += 1
            if m["exclude"] != exp_ex or not m["bank"].endswith(f"ts116m_{cw}_bomb.jsonl") or m["attn"] != "eager" \
                    or m["dtype"] != "bfloat16" or m["gpu"] != "NVIDIA RTX A5000":
                viol.append((x, m["exclude"], m["bank"], m["attn"], m["dtype"], m["gpu"]))
        O["config_violations"] = viol
        O["provenance_job_host_gpu_counts"] = {"|".join(map(str, k)): v for k, v in hosts.items()}
        fs = {}
        for r in (1, 4):
            v = load(cw, f"KO_CAND_r{r}")[1]
            t = load(cw, f"KO_CAND_r{r}", prefix=f"hcsi_p2b_{cw}_k4", nrows=268)[1]
            fsets = Counter(load(cw, x)[1]["factors_sha16"] for x in [f"KO_CAND_r{r}", f"KO_CWONLY_r{r}"]
                            + fam(cw, r, "primary")[61:] + fam(cw, r, "secondary")[61:])
            fs[f"r{r}"] = dict(val=v["factors_sha16"], train=t["factors_sha16"], equal=v["factors_sha16"] == t["factors_sha16"],
                               fitted_arms_factor_sha_counts=dict(fsets))
        O["factor_identity"] = fs
        O["skipped_partial_dirs"] = sorted({s for (c2, _, _), (_, m) in _cache.items() if c2 == cw for s in m["skipped"]})
        for kind in ["primary", "secondary"]:
            for r in (1, 4):
                O[kind][r].pop("keys"); O[kind][r].pop("ctrl")
        out["codewords"][cw] = O
    # ---- outcome mapping (amendment 5)
    spec = {cw: {r: out["codewords"][cw]["primary"][r]["verdict"] == "PASS" for r in (1, 4)} for cw in out["codewords"]}
    b, u = spec["basket"], spec["button"]
    if b[1] and not u[1] and u[4]: oc = "A"
    elif b[1] and u[1]: oc = "B"
    elif not b[1] and not u[1] and b[4] and u[4]: oc = "C"
    elif (b[1] or b[4]) and not (u[1] or u[4]): oc = "D"
    elif not any(list(b.values()) + list(u.values())): oc = "E"
    else: oc = "other"
    out["outcome"] = dict(specific=spec, mapping=oc)
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    for cw, O in out["codewords"].items():
        for kind in ["primary", "secondary"]:
            for r in (1, 4):
                c = O[kind][r]
                print(cw, kind, r, c["n_keys"], c["n_domains"], c["stat"], f"{c['rank']}/{c['of']}",
                      round(c["holm"], 4), c["recovery"], c["ci95"], c["verdict"], "margin", c["margin_to_best_control"],
                      c["top3_controls"][0])
    print("OUTCOME", out["outcome"])


if __name__ == "__main__":
    main()
