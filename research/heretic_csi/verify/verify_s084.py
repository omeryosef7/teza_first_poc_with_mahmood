#!/usr/bin/env python3
"""F3 independent verification of PR-HCSI-S084 (+AMENDMENT 1): button cand_pls4 rank-4 VALIDATION vs 200 controls.
Own code; does NOT use scripts/dcs_csi_subspace_analyze.py or research/heretic_csi/p2a_powered_*.
Dir selection: every score_behavior dir whose tag starts hcsi_p2a_button_ and whose RUNMETA slurm_job_id is in JOBS;
exactly one dir per arm required. Statistic: mean over domains of [mean_y(arm,d) - mean_y(KO,d)] on the prompt_id set
common to ALL pool+liveness arms after the BASE-referenced 0.05 option-mass floor (UNROUNDED)."""
import glob, json, math, os, re, collections, hashlib
import numpy as np, torch
ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = f"{ROOT}/outputs/boombness/score_behavior"
JOBS = {"1022698", "1027577", "1032110"}
OUT = f"{ROOT}/reports/heretic_csi/VERIFY_S084_powered.json"
R1, R16 = 0.2456, 0.1754
LIVE = ["BASE", "KO", "KO_SELF", "KO_FULL"]
CAND = "KO_CAND_r4"
CTRL = [f"KO_RAND_r4_{i}" for i in range(190)] + [f"KO_SHUF_r4_{j}" for j in range(10)]
sig = lambda x: 1 / (1 + math.exp(-x))


def select():
    by = collections.defaultdict(list); other_jobs = collections.Counter()
    for d in glob.glob(f"{SB}/hcsi_p2a_button_*"):
        try:
            rm = json.load(open(f"{d}/RUNMETA.json"))
        except Exception:
            continue
        j = str(rm.get("slurm_job_id"))
        arm = json.load(open(f"{d}/config.json"))["args"]["arm"]
        if j in JOBS:
            by[arm].append((d, j, rm.get("gpu"), rm.get("hostname")))
        else:
            other_jobs[j] += 1
    return by, other_jobs


def logged(job):
    s = set()
    for ln in open(f"{ROOT}/outputs/heretic_csi/logs/sweep_{job}.out"):
        m = re.match(r"\[score\] \{'semantic': \d+\} -> (\S+)", ln.strip())
        if m:
            s.add(os.path.basename(m.group(1)))
    return s


def rows(d):
    return {r["prompt_id"]: r for r in map(json.loads, open(f"{d}/results.jsonl"))}


def main():
    res = {"schema": "hcsi_verify_s084/1"}
    by, other = select()
    sel = {}
    problems = []
    for arm in LIVE + [CAND] + CTRL:
        L = by.get(arm, [])
        if len(L) != 1:
            problems.append(f"{arm}: {len(L)} dirs")
            continue
        sel[arm] = L[0]
    ovl = {a: by[a][0] for a in by if a.startswith("OVL_")}
    extra = sorted(a for a in by if a not in sel and not a.startswith("OVL_"))
    lg = set().union(*(logged(j) for j in JOBS))
    res["selection"] = {"n_pool_arms_selected": len(sel), "problems": problems, "ovl_arms_found(excluded)": sorted(ovl),
                        "unexpected_arms_from_jobs": extra,
                        "jobs_used": dict(collections.Counter(v[1] for v in sel.values())),
                        "gpus": dict(collections.Counter(v[2] for v in sel.values())),
                        "hosts": dict(collections.Counter(v[3] for v in sel.values())),
                        "all_selected_dirs_log_referenced": all(os.path.basename(v[0]) in lg for v in sel.values()),
                        "n_log_referenced_dirs_total": len(lg),
                        "same-tag dirs from other jobs (ignored)": dict(other)}
    assert not problems, problems
    R = {a: rows(v[0]) for a, v in sel.items()}
    res["done_ok"] = all(json.load(open(f"{v[0]}/DONE.json"))["status"] == "ok" for v in sel.values())
    res["arm_row_counts"] = dict(collections.Counter(len(r) for r in R.values()))
    # population / split
    S = json.load(open(f"{ROOT}/data/boombness_prompts/dcs_ts116_domain_split.json"))["assign"]
    doms = {r["domain"] for r in R["BASE"].values()}
    res["population"] = {"n_rows_BASE": len(R["BASE"]), "n_domains": len(doms), "split_counts": dict(collections.Counter(S[d] for d in doms)),
                         "TEST_present": any(S[d] == "test" for d in doms)}

    def keyset(floor_mode):
        ids = set(R["BASE"])
        for a in R:
            ids &= set(R[a])
        base_ok = {p for p in ids if R["BASE"][p]["option_mass"] >= 0.05}
        if floor_mode == "base":
            return base_ok
        if floor_mode == "strict":
            return {p for p in base_ok if R["KO"][p]["option_mass"] >= 0.05 and R["KO_FULL"][p]["option_mass"] >= 0.05}
        return ids

    def dmeans(ids):
        out = {}
        for a, rr in R.items():
            acc = collections.defaultdict(list)
            for p in ids:
                r = rr[p]; acc[r["domain"]].append(sig(r["logp_concept"] - r["logp_codeword"]))
            out[a] = {d: float(np.mean(v)) for d, v in acc.items()}
        return out

    def evaluate(ids, domains=None, cand=CAND, pm=None):
        pm = pm or dmeans(ids)
        D = sorted(domains if domains is not None else pm["KO"])
        st = {a: float(np.mean([pm[a][d] - pm["KO"][d] for d in D])) for a in [CAND] + CTRL}
        ctl = [a for a in [CAND] + CTRL if a != cand]
        ge = sum(st[a] >= st[cand] for a in ctl)
        return st, 1 + ge, (1 + ge) / (len(ctl) + 1), pm, D

    out = {}
    for fm in ("base", "strict", "none"):
        ids = keyset(fm)
        st, rank, p, pm, D = evaluate(ids)
        st5 = {a: round(v, 5) for a, v in st.items()}
        rank5 = 1 + sum(st5[a] >= st5[CAND] for a in CTRL)
        holm = min(1.0, 3 * p) if p <= min(R1, R16) else None
        shuf_max = max(st[f"KO_SHUF_r4_{j}"] for j in range(10))
        rand_max = max(st[f"KO_RAND_r4_{i}"] for i in range(190))
        diff = [pm[CAND][d] - pm["KO"][d] for d in D]
        rng = np.random.default_rng(0)
        bo = [float(np.mean(rng.choice(diff, len(diff)))) for _ in range(20000)]
        num = sum(pm[CAND][d] - pm["KO"][d] for d in D); den = sum(pm["KO_FULL"][d] - pm["KO"][d] for d in D)
        lodo = []
        for d in D:
            _, rk, _, _, _ = evaluate(ids, [x for x in D if x != d], pm=pm)
            lodo.append(rk)
        out[fm] = {"n_common_rows": len(ids), "n_domains": len(D), "cand_stat": st[CAND], "rank_unrounded_ties_against": rank,
                   "rank_5dp": rank5, "p": p, "holm_adj_p_r4": holm, "PASS_holm": holm is not None and holm < 0.05,
                   "shuf_max": shuf_max, "beats_every_shuf": st[CAND] > shuf_max, "rand_max": rand_max,
                   "margin_vs_best_control": st[CAND] - max(shuf_max, rand_max),
                   "control_mean": float(np.mean([st[a] for a in CTRL])), "control_sd": float(np.std([st[a] for a in CTRL], ddof=1)),
                   "cand_minus_KO_CI95": [float(np.percentile(bo, 2.5)), float(np.percentile(bo, 97.5))],
                   "n_dom_positive": int(sum(x > 0 for x in diff)), "recovery": num / den,
                   "liveness": {"KO-BASE": float(np.mean([pm["KO"][d] - pm["BASE"][d] for d in D])),
                                "FULL-KO": float(np.mean([pm["KO_FULL"][d] - pm["KO"][d] for d in D])),
                                "SELF-KO": float(np.mean([pm["KO_SELF"][d] - pm["KO"][d] for d in D]))},
                   "lodo_ranks": dict(collections.Counter(lodo))}
        if fm == "base":
            mut_swap = []
            for s in range(30):
                c = CTRL[np.random.default_rng(s).integers(len(CTRL))]
                mut_swap.append(evaluate(ids, cand=c, pm=pm)[2])
            mut_shuf = []
            for s in range(30):
                g = np.random.default_rng(1000 + s); pm2 = {a: dict(pm[a]) for a in pm}
                pool = [CAND] + CTRL
                for d in D:
                    vals = [pm[a][d] for a in pool]; g.shuffle(vals)
                    for a, v in zip(pool, vals):
                        pm2[a][d] = v
                mut_shuf.append(evaluate(ids, pm=pm2)[2])
            out[fm]["mutation_swap_candidate_p_median"] = float(np.median(mut_swap))
            out[fm]["mutation_within_domain_shuffle_p_median"] = float(np.median(mut_shuf))
            out[fm]["mutation_within_domain_shuffle_frac_p_le_0.0149"] = float(np.mean(np.array(mut_shuf) <= 0.0149))
    res["results"] = out
    # rank / norm matching
    old = torch.load(f"{ROOT}/configs/heretic_csi/hcsi_ranksweep_button.pt", map_location="cpu", weights_only=False)["bases"]
    new = torch.load(f"{ROOT}/configs/heretic_csi/hcsi_ranksweep_button_r4ext.pt", map_location="cpu", weights_only=False)["bases"]
    res["r4ext_sha256"] = hashlib.sha256(open(f"{ROOT}/configs/heretic_csi/hcsi_ranksweep_button_r4ext.pt", "rb").read()).hexdigest()
    res["cand_pls4_byte_identical_in_r4ext"] = bool(torch.equal(old["cand_pls4"], new["cand_pls4"]))
    cfg = {a: json.load(open(f"{sel[a][0]}/config.json"))["args"] for a in [CAND] + CTRL}
    ranks = collections.Counter(); keyinfo = collections.Counter(); seen = {}
    for a in CTRL:
        c = cfg[a]; src = old if c["rescue_basis"].endswith("hcsi_ranksweep_button.pt") else new
        B = src[c["rescue_basis_key"]]
        ranks[int(torch.linalg.matrix_rank(B.double()).item())] += 1
        orth = float((B.double() @ B.double().T - torch.eye(B.shape[0], dtype=torch.float64)).abs().max())
        keyinfo[(os.path.basename(c["rescue_basis"]), c["rescue_norm_match_key"], orth < 1e-5)] += 1
        h = hashlib.sha256(B.numpy().tobytes()).hexdigest()
        seen.setdefault(h, []).append(a)
    res["controls_rank_counter"] = dict(ranks)
    res["controls_basis_file_normkey_orthonormal"] = {str(k): v for k, v in keyinfo.items()}
    res["controls_distinct_bases"] = len(seen) == len(CTRL)
    res["controls_duplicate_of_candidate"] = hashlib.sha256(old["cand_pls4"].numpy().tobytes()).hexdigest() in seen
    res["cand_basis"] = (os.path.basename(cfg[CAND]["rescue_basis"]), cfg[CAND]["rescue_basis_key"], cfg[CAND]["rescue_norm_match_key"])
    cn = {p: r["rescue_liveness"]["written_norm_mean"] for p, r in R[CAND].items()}
    rel = [abs(r["rescue_liveness"]["written_norm_mean"] - cn[p]) / cn[p] for a in CTRL for p, r in R[a].items() if cn.get(p)]
    res["norm_match_relerr_max"] = float(max(rel))
    res["live_rank_rows"] = dict(collections.Counter(r["rescue_liveness"]["rank"] for a in [CAND] + CTRL for r in R[a].values()))
    # overlap bit-exactness
    ov = {}
    for o, ref in (("OVL_BASE", "BASE"), ("OVL_KO", "KO"), ("OVL_CAND_r4", CAND), ("OVL_RAND_r4_0", "KO_RAND_r4_0")):
        if o not in ovl:
            ov[o] = "MISSING"; continue
        A = rows(ovl[o][0]); Bm = R[ref]
        mx = max(max(abs(A[p]["logp_concept"] - Bm[p]["logp_concept"]), abs(A[p]["logp_codeword"] - Bm[p]["logp_codeword"])) for p in Bm if p in A)
        ov[o] = {"same_ids": set(A) == set(Bm), "max_abs_logp_diff": mx, "job": ovl[o][1], "ref_job": sel[ref][1]}
    res["overlap"] = ov
    json.dump(res, open(OUT, "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
