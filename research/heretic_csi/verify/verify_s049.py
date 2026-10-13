#!/usr/bin/env python3
"""F3 INDEPENDENT VERIFIER for HERETIC-CSI S-049 (+ S-050 K4 r4/r8).

Written from scratch (does NOT import/reuse dcs_csi_subspace_analyze.py or analyze_sweep.py).
Reads raw score_behavior run dirs (located via the '[score] ... -> <dir>' lines of each sweep log),
recomputes y_install = logistic(logp_concept - logp_codeword) per row, aggregates per DOMAIN,
recovery = sum_d(cand-KO) / sum_d(FULL-KO) over domains (equal domain weight), domain-cluster
bootstrap CI, and rank of the candidate among its rank-matched controls, p = rank/(n+1).
"""
from __future__ import annotations
import functools, argparse, collections, hashlib, json, math, os, re, sys
import numpy as np

ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
JOBS = {  # job -> (codeword, rank, intended split)
    966084: ("basket", 1, "train"), 965928: ("basket", 16, "train"),
    966157: ("button", 1, "train"), 966158: ("button", 16, "train"),
    968532: ("basket", 1, "validation"), 968533: ("basket", 16, "validation"),
    968534: ("button", 1, "validation"), 968535: ("button", 16, "validation"),
    969085: ("basket", 4, "train_k4"), 969086: ("basket", 8, "train_k4"),
    969087: ("button", 4, "train_k4"), 969088: ("button", 8, "train_k4"),
}
B = 2000


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


QUAR = {}


@functools.lru_cache(maxsize=None)
def _run_dirs(job):
    return run_dirs_(job)


def run_dirs(job):
    return dict(_run_dirs(job))


def run_dirs_(job):
    out = {}
    QUAR[job] = []
    for ln in open(f"{ROOT}/outputs/heretic_csi/logs/sweep_{job}.out"):
        m = re.match(r"\[score\] \{'semantic': \d+\} -> (\S+)", ln.strip())
        if m:
            d = m.group(1)
            if not os.path.isdir(d):
                QUAR[job].append(os.path.basename(d))
                continue
            arm = json.load(open(os.path.join(d, "config.json")))["args"]["arm"]
            if arm in out:
                raise SystemExit(f"duplicate arm {arm} in job {job}")
            out[arm] = d
    return out


import functools


@functools.lru_cache(maxsize=None)
def load(d):
    rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl"))]
    done = json.load(open(os.path.join(d, "DONE.json")))
    cfg = json.load(open(os.path.join(d, "config.json")))
    return rows, done, cfg


def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))


def per_domain(rows, keep_ids):
    acc = collections.defaultdict(list)
    for r in rows:
        if r["prompt_id"] in keep_ids:
            acc[r["domain"]].append(sigmoid(r["logp_concept"] - r["logp_codeword"]))
    return {d: float(np.mean(v)) for d, v in acc.items()}


def analyse(job, floor_mode="base_ko_full", mutate=None, seed=0):
    cw, rank, split = JOBS[job]
    dirs = run_dirs(job)
    data = {a: load(d) for a, d in dirs.items()}
    assign = json.load(open(f"{ROOT}/data/boombness_prompts/dcs_ts116_domain_split.json"))["assign"]
    want = "train" if split.startswith("train") else "validation"
    info = {"job": job, "codeword": cw, "rank": rank, "split": split, "n_arms": len(dirs)}
    # population checks
    base_rows = data["BASE"][0]
    doms = sorted({r["domain"] for r in base_rows})
    info["n_rows_BASE"] = len(base_rows)
    info["n_domains"] = len(doms)
    info["domain_split_counts"] = dict(collections.Counter(assign[d] for d in doms))
    info["TEST_present"] = any(assign[d] == "test" for d in doms)
    info["all_in_intended_split"] = all(assign[d] == want for d in doms)
    info["codeword_ok"] = all(r["target_surface"] == cw for r in base_rows)
    # option-mass floor: drop prompt if option_mass < 0.05 in BASE, KO or KO_FULL (paired, arm-independent)
    def om_ok(arm):
        return {r["prompt_id"] for r in data[arm][0] if r["option_mass"] >= 0.05}
    all_ids = {r["prompt_id"] for r in base_rows}
    if floor_mode == "base_ko_full":
        keep = all_ids & om_ok("BASE") & om_ok("KO") & om_ok("KO_FULL")
    elif floor_mode == "base":
        keep = all_ids & om_ok("BASE")
    else:
        keep = all_ids
    info["n_rows_after_floor"] = len(keep)
    info["n_rows_dropped_floor"] = len(all_ids) - len(keep)
    # per-arm per-domain means
    pd = {a: per_domain(rows, keep) for a, (rows, _, _) in data.items()}
    info["arm_row_counts"] = {a: len(rows) for a, (rows, _, _) in data.items()}
    info["arms_short"] = {a: len(all_ids) - len({r['prompt_id'] for r in rows}) for a, (rows, _, _) in data.items()
                         if len({r['prompt_id'] for r in rows}) < len(all_ids)}
    D = sorted(pd["KO"])
    cand = f"KO_CAND_r{rank}"
    ctrls = sorted(a for a in dirs if a.startswith(f"KO_RAND_r{rank}_") or a.startswith(f"KO_SHUF_r{rank}_"))
    foreign = [a for a in dirs if a.startswith(("KO_RAND", "KO_SHUF", "KO_CAND")) and a not in ctrls and a != cand]
    info["n_controls"] = len(ctrls)
    info["foreign_rank_arms"] = foreign
    ymean = {a: float(np.mean([pd[a][d] for d in D if d in pd[a]])) for a in pd}
    info["y_install_mean_by_arm_liveness"] = {a: ymean[a] for a in ["BASE", "KO", "KO_SELF", "KO_FULL", cand]}
    info["KO_minus_BASE"] = ymean["KO"] - ymean["BASE"]
    info["KO_SELF_minus_KO"] = ymean["KO_SELF"] - ymean["KO"]
    info["KO_FULL_minus_KO"] = ymean["KO_FULL"] - ymean["KO"]

    def stat(arm, domains):
        num = sum(pd[arm][d] - pd["KO"][d] for d in domains if d in pd[arm])
        den = sum(pd["KO_FULL"][d] - pd["KO"][d] for d in domains if d in pd[arm])
        return num / den

    def effect(arm, domains):  # mean over domains of arm-KO (rank statistic; same denominator for all)
        v = [pd[arm][d] - pd["KO"][d] for d in domains if d in pd[arm]]
        return float(np.mean(v))
    candidate = cand
    pool = [cand] + ctrls
    rng = np.random.default_rng(seed)
    if mutate == "swap_candidate":  # treat a random control as the candidate
        candidate = ctrls[rng.integers(len(ctrls))]
    eff = {a: effect(a, D) for a in pool}
    if mutate == "shuffle_domain_labels":  # permute candidate's per-domain values across domains -> recovery unaffected in mean;
        # stronger null: sign-flip candidate's (cand-KO_FULL midpoint) per domain is not meaningful; instead permute arm identity per domain
        perm_eff = {}
        for a in pool:
            perm_eff[a] = []
        for d in D:
            vals = [pd[a][d] for a in pool if d in pd[a]]
            arms_d = [a for a in pool if d in pd[a]]
            rng.shuffle(vals)
            for a, v in zip(arms_d, vals):
                perm_eff[a].append(v - pd["KO"][d])
        eff = {a: float(np.mean(v)) for a, v in perm_eff.items()}
    others = [eff[a] for a in pool if a != candidate]
    rnk = 1 + sum(1 for v in others if v > eff[candidate])
    ties = sum(1 for v in others if v == eff[candidate])
    info["candidate_arm_used"] = candidate
    info["candidate_effect_mean_dKO"] = eff[candidate]
    info["control_effect_quantiles"] = [float(np.quantile(others, q)) for q in (0.05, 0.5, 0.95, 1.0)]
    info["test_rank"] = rnk
    info["ties"] = ties
    info["n_pool"] = len(pool)
    info["p_rank"] = rnk / (len(others) + 1)
    info["p_floor"] = 1 / (len(others) + 1)
    if mutate is None:
        rec = stat(cand, D)
        boots = []
        Da = np.array(D)
        for _ in range(B):
            s = list(rng.choice(Da, size=len(Da), replace=True))
            try:
                boots.append(stat(cand, s))
            except ZeroDivisionError:
                pass
        info["recovery_fraction"] = rec
        info["recovery_CI95_domain_bootstrap"] = [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]
        info["n_domains_used"] = len([d for d in D if d in pd[cand]])
        # rank-matching / norm-matching / seeds / hashes
        cfgs = {a: data[a][2]["args"] for a in pool}
        keys = {a: cfgs[a]["rescue_basis_key"] for a in pool}
        info["candidate_basis_key"] = keys[cand]
        info["control_norm_match_keys"] = sorted({cfgs[a]["rescue_norm_match_key"] for a in ctrls})
        info["basis_paths"] = sorted({cfgs[a]["rescue_basis"] for a in pool})
        info["live_ranks"] = dict(collections.Counter(
            data[a][0][0]["rescue_liveness"]["rank"] for a in pool))
        # written-norm match: control written_norm_mean vs candidate's per prompt
        cn = {r["prompt_id"]: r["rescue_liveness"]["written_norm_mean"] for r in data[cand][0]}
        rel = []
        for a in ctrls:
            for r in data[a][0]:
                if r["prompt_id"] in cn and cn[r["prompt_id"]] > 0:
                    rel.append(abs(r["rescue_liveness"]["written_norm_mean"] - cn[r["prompt_id"]]) / cn[r["prompt_id"]])
        info["control_vs_cand_written_norm_relerr_max"] = float(max(rel)) if rel else None
        info["control_vs_cand_written_norm_relerr_median"] = float(np.median(rel)) if rel else None
        info["seeds"] = sorted({cfgs[a]["seed"] for a in pool})
        info["distinct_basis_keys"] = len(set(keys.values())) == len(pool)
        info["results_sha16"] = {a: sha16(os.path.join(dirs[a], "results.jsonl")) for a in ["BASE", "KO", "KO_FULL", cand]}
        info["all_DONE_ok"] = all(data[a][1]["status"] == "ok" and data[a][1]["n_rows_failed"] == 0 for a in data)
        info["excl_files"] = sorted({c[2]["args"]["exclude_prompt_ids"] for c in data.values()})
        info["bank_sha16"] = sorted({c[2]["args"]["bank"] for c in data.values()})
    return info


def check_pt(cw):
    import torch
    pt = torch.load(f"{ROOT}/configs/heretic_csi/hcsi_ranksweep_{cw}.pt", map_location="cpu", weights_only=False)
    out = {}
    for r in (1, 4, 8, 16):
        ck = "cand_rank1" if r == 1 else f"cand_pls{r}"
        rr = {}
        for k, t in pt["bases"].items():
            if k == ck or k.startswith(f"ctrl_random_r{r}_") or k.startswith(f"ctrl_shuffled_pls{r}_"):
                rr[k] = int(torch.linalg.matrix_rank(t.float()).item())
        out[r] = {"candidate_key": ck, "candidate_rank": rr.get(ck), "n_controls_in_pt": len(rr) - (1 if ck in rr else 0),
                  "control_ranks": dict(collections.Counter(v for k, v in rr.items() if k != ck))}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=f"{ROOT}/reports/heretic_csi/VERIFY_S049_independent.json")
    ap.add_argument("--jobs", default=",".join(map(str, JOBS)))
    a = ap.parse_args()
    res = {"schema": "hcsi_verify_s049/1", "cells": [], "mutations": [], "pt_rank_check": {}}
    for cw in ("basket", "button"):
        try:
            res["pt_rank_check"][cw] = check_pt(cw)
        except Exception as e:
            res["pt_rank_check"][cw] = f"ERR {e}"
    for j in map(int, a.jobs.split(",")):
        info = analyse(j)
        info_nf = analyse(j, floor_mode="none")
        info["sensitivity_no_floor"] = {k: info_nf[k] for k in ("test_rank", "p_rank", "candidate_effect_mean_dKO", "n_rows_after_floor")}
        info["sensitivity_no_floor"]["recovery_fraction"] = info_nf["recovery_fraction"]
        info_b = analyse(j, floor_mode="base")
        info["sensitivity_floor_BASE_ref"] = {k: info_b[k] for k in ("test_rank", "p_rank", "candidate_effect_mean_dKO", "n_rows_after_floor", "recovery_fraction", "recovery_CI95_domain_bootstrap")}
        res["cells"].append(info)
        muts = {"job": j}
        swaps = [analyse(j, mutate="swap_candidate", seed=s)["p_rank"] for s in range(20)]
        shuf = [analyse(j, mutate="shuffle_domain_labels", seed=s)["p_rank"] for s in range(20)]
        muts["swap_candidate_p_median"] = float(np.median(swaps))
        muts["swap_candidate_p_min"] = float(min(swaps))
        muts["shuffle_arm_identity_within_domain_p_median"] = float(np.median(shuf))
        muts["shuffle_p_min"] = float(min(shuf))
        res["mutations"].append(muts)
        print(json.dumps({k: info[k] for k in ("job", "codeword", "rank", "split", "n_rows_BASE", "n_domains", "n_rows_after_floor",
                                                "test_rank", "n_pool", "p_rank", "recovery_fraction", "recovery_CI95_domain_bootstrap")}), muts, flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("wrote", a.out)
