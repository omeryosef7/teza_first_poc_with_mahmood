#!/usr/bin/env python3
"""GENERIC frozen read for powered P2a VALIDATION re-tests (PR-HCSI-S199 onward). Generalizes the S-084 pair
p2a_powered_analyze.py + p2a_powered_binding.py (same rule, same steps) to any codeword/rank, and adds the
pre-declared PAIRED-floor sensitivity.

Steps: (1) overlap VOID check — OVL_{BASE,KO,CAND_r{R},RAND_r{R}_0} in the first ext job must reproduce the
original job's {BASE,KO,KO_CAND_r{R},KO_RAND_r{R}_0} bit-exactly (|dlogp|,|dy| <= 1e-6, identical id sets);
(2) every job's GPU type == the original job's; (3) frozen analyzer scripts/dcs_csi_subspace_analyze.py over
orig + ext jobs (candidate vs n_old_rand + n_new RAND + nshuf SHUF; BASE-referenced floor 0.05 = PRIMARY);
(4) unrounded recomputation with the analyzer's own helpers (asserted to round to the analyzer's 5-dp values);
(5) decide() on unrounded AND on the analyzer's rounded values; BINDING: PASS only if both PASS, disagreement =>
"DOES NOT PASS (rounding-sensitive)", VOID propagates; (6) SENSITIVITY (descriptive, never the verdict): same
decision under the strict PAIRED floor (keep keys where BASE, KO and KO_FULL all have option mass >= 0.05).
PASS = Holm({looks..., r{R}: p_ext})[r{R}] < 0.05 AND candidate > every SHUF AND candidate-KO CI-lo > 0
AND gates AND no VOID; ties count against the candidate. Shared row set reported vs --expected-rows.
"""
import argparse, glob, importlib.util, json, math, os, re, subprocess
ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
PY = "/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python"


def holm(ps):
    order = sorted(ps, key=ps.get); out = {}; run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[k])); out[k] = run
    return out


def decide(cand, controls, looks, look_key, shuf_prefix, ci_lo, gates_ok, void, n_keys_common, expected_rows, arms_lost,
           n_domains=None, min_rows=None, min_domains=None):
    """min_rows/min_domains: PR-HCSI-S199 AMENDMENT 1 row-set floor. If the common-key row set (or the number of
    domains with >=1 common key) is below the floor the verdict is UNDERPOWERED, never PASS/DOES NOT PASS.
    None => no floor (used only by the S-084 reproduction test)."""
    better = sum(1 for v in controls.values() if v >= cand)
    p_ext = (1 + better) / (len(controls) + 1)
    hp = holm(dict(looks, **{look_key: p_ext}))
    shuf = {k: v for k, v in controls.items() if k.startswith(shuf_prefix)}
    beats = bool(shuf) and all(cand > v for v in shuf.values())
    passed = (not void) and hp[look_key] < 0.05 and beats and ci_lo > 0 and gates_ok
    under = []
    if min_rows is not None and n_keys_common < min_rows:
        under.append(f"common rows {n_keys_common} < {min_rows}")
    if min_domains is not None and n_domains is not None and n_domains < min_domains:
        under.append(f"domains {n_domains} < {min_domains}")
    return {"rank": 1 + better, "n_controls": len(controls), "p_ext": p_ext, "holm": hp, "beats_every_shuf": beats,
            "max_shuf": max(shuf.values()) if shuf else None,
            "row_set": {"n_keys_common": n_keys_common, "expected": expected_rows, "deviation": n_keys_common - expected_rows,
                        "arms_with_dropped_keys": sorted(a for a, n in arms_lost.items() if n)},
            "n_domains": n_domains, "underpowered_reasons": under,
            "VERDICT": ("VOID: " + "; ".join(void)) if void else
                       ("UNDERPOWERED (row set): " + "; ".join(under) if under else ("PASS" if passed else "DOES NOT PASS"))}


def combine(u, r):
    u, r = u["VERDICT"], r["VERDICT"]
    if u.startswith("VOID") or r.startswith("VOID"):
        return u if u.startswith("VOID") else r
    if u.startswith("UNDERPOWERED") or r.startswith("UNDERPOWERED"):
        return u if u.startswith("UNDERPOWERED") else r
    return u if u == r else "DOES NOT PASS (rounding-sensitive)"


def _ana():
    spec = importlib.util.spec_from_file_location("dcs_ana", f"{ROOT}/scripts/dcs_csi_subspace_analyze.py")
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A); return A


def dirs_for(cw, job):
    out = {}
    for d in glob.glob(f"{ROOT}/outputs/boombness/score_behavior/hcsi_p2a_{cw}_*"):
        try:
            m = json.load(open(d + "/RUNMETA.json"))
        except Exception:
            continue
        if str(m.get("slurm_job_id")) == str(job) and os.path.exists(d + "/DONE.json"):
            arm = json.load(open(d + "/config.json"))["args"]["arm"]
            if arm in out:
                raise SystemExit(f"duplicate arm {arm} in job {job}")
            out[arm] = d
    return out


def _rows(d):
    return {r["prompt_id"]: r for r in map(json.loads, open(d + "/results.jsonl"))}


def _y(r):
    return 1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"])))


def overlap(cw, R, orig, ext1):
    o, n = dirs_for(cw, orig), dirs_for(cw, ext1)
    pairs = {"OVL_BASE": "BASE", "OVL_KO": "KO", f"OVL_CAND_r{R}": f"KO_CAND_r{R}", f"OVL_RAND_r{R}_0": f"KO_RAND_r{R}_0"}
    res, void = {}, []
    for an, ao in pairs.items():
        if an not in n or ao not in o:
            void.append(f"{an}/{ao} missing"); continue
        rn, ro = _rows(n[an]), _rows(o[ao])
        same = set(rn) == set(ro)
        md = max((max(abs(rn[p]["logp_concept"] - ro[p]["logp_concept"]), abs(rn[p]["logp_codeword"] - ro[p]["logp_codeword"]),
                      abs(_y(rn[p]) - _y(ro[p]))) for p in set(rn) & set(ro)), default=float("nan"))
        res[an] = {"vs": ao, "n_new": len(rn), "n_old": len(ro), "identical_id_sets": same, "max_abs_diff": md}
        if not same or not (md <= 1e-6):
            void.append(f"{an}: ids_equal={same} max|diff|={md:.3g}")
    return res, void


def gpus(jobs):
    out = {j: sorted(set(re.findall(r"^(NVIDIA [^,]+),", open(f"{ROOT}/outputs/heretic_csi/logs/sweep_{j}.out").read(), re.M)))
           for j in jobs}
    ref = out[jobs[0]]
    return out, (len(ref) == 1 and all(v == ref for v in out.values()))


def stats(A, cw, arms, jobs, floor_mode):
    sel = {"require_rescue_layer": None, "require_slurm_jobs": [str(j) for j in jobs]}
    assign = A.lpm.load_split()
    rd = lambda arm: A.rederive.strict_run_dir(f"hcsi_p2a_{cw}_{arm}", 230, row_file="results.jsonl", allow_short=20, **sel)
    keep = A.reference_key_set(rd("BASE"), 0.05)
    if floor_mode == "paired":
        keep &= A.reference_key_set(rd("KO"), 0.05) & A.reference_key_set(rd("KO_FULL"), 0.05)
    kv = {arm: A.arm_key_values(rd(arm), assign, "validation")[0] for arm in arms}
    common = set.intersection(*[set(v) for v in kv.values()]) & keep
    lost = {arm: len(set(kv["BASE"]) & keep) - len(set(kv[arm]) & keep) for arm in arms}
    doms = sorted({k[0] for k in common}); dm = {}
    for arm in arms:
        by = {}
        for k in common:
            by.setdefault(k[0], []).append(kv[arm][k])
        dm[arm] = {d: sum(v) / len(v) for d, v in by.items()}
    st = {arm: sum(dm[arm][d] - dm["KO"][d] for d in doms) / len(doms) for arm in arms}
    diffs = [dm[f"KO_CAND_r{arms_rank(arms)}"][d] - dm["KO"][d] for d in doms]
    return st, len(common), lost, doms, diffs


def arms_rank(arms):
    return int(next(a for a in arms if a.startswith("KO_CAND_r")).split("_r")[1])


def boot_ci(diffs, n_boot=20000, seed=20260915):
    import random
    rng = random.Random(seed); n = len(diffs); dr = []
    for _ in range(n_boot):
        dr.append(sum(diffs[rng.randrange(n)] for _ in range(n)) / n)
    dr.sort()
    return [dr[int(0.025 * n_boot)], dr[min(n_boot - 1, int(0.975 * n_boot))]]


def companions(A, cw, R, jobs, st, cand, orig_ctrls):
    """DESCRIPTIVE companions (S-199 AMENDMENT 1; never change the verdict).
    (ii) candidate vs the ORIGINAL 56 controls on the SAME shrunken common row set (st = stats over the
         common keys of all arms): separates row-set loss from null-size gain.
    (iii) per-control paired comparison, each control on ITS OWN rows: for control c, keys = BASE-floor keys
         present in {candidate, KO, c}; delta_c = mean over domains of (dmean[cand]-dmean[c]) on those keys."""
    better = sum(1 for k in orig_ctrls if st[k] >= st[cand])
    comp_ii = {"n_controls": len(orig_ctrls), "rank": 1 + better, "p": (1 + better) / (len(orig_ctrls) + 1),
               "candidate_stat": st[cand]}
    sel = {"require_rescue_layer": None, "require_slurm_jobs": [str(j) for j in jobs]}
    assign = A.lpm.load_split()
    rd = lambda arm: A.rederive.strict_run_dir(f"hcsi_p2a_{cw}_{arm}", 230, row_file="results.jsonl", allow_short=20, **sel)
    keep = A.reference_key_set(rd("BASE"), 0.05)
    names = [cand, "KO"] + [a for a in st if a.startswith(("KO_RAND_r", "KO_SHUF_r"))]
    kv = {a: A.arm_key_values(rd(a), assign, "validation")[0] for a in names}
    deltas, rows = {}, {}
    for c in names[2:]:
        keys = set(kv[cand]) & set(kv["KO"]) & set(kv[c]) & keep
        by = {}
        for k in keys:
            by.setdefault(k[0], []).append(kv[cand][k] - kv[c][k])
        deltas[c] = sum(sum(v) / len(v) for v in by.values()) / len(by)
        rows[c] = len(keys)
    vals = sorted(deltas.values())
    comp_iii = {"n_controls": len(deltas), "n_candidate_gt_control": sum(1 for v in vals if v > 0),
                "min_delta": vals[0], "median_delta": vals[len(vals) // 2], "max_delta": vals[-1],
                "worst_controls": sorted(deltas, key=deltas.get)[:5], "rows_per_control_min_max": [min(rows.values()), max(rows.values())]}
    return comp_ii, comp_iii


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True); ap.add_argument("--rank", type=int, required=True)
    ap.add_argument("--orig-job", required=True); ap.add_argument("--ext-jobs", required=True, help="comma list; first has OVL arms")
    ap.add_argument("--looks", required=True, help="other VAL looks, e.g. r4=0.0175,r16=0.1754")
    ap.add_argument("--n-old-rand", type=int, default=46); ap.add_argument("--n-new", type=int, default=144)
    ap.add_argument("--nshuf", type=int, default=10); ap.add_argument("--expected-rows", type=int, required=True)
    ap.add_argument("--min-rows", type=int, default=100, help="AMENDMENT 1 row-set floor (common keys)")
    ap.add_argument("--min-domains", type=int, default=21, help="AMENDMENT 1 domain floor (domains with >=1 common key)")
    ap.add_argument("--tag", required=True, help="output stem, e.g. P2A_BASKET_R1_POWERED")
    a = ap.parse_args()
    cw, R = a.codeword, a.rank
    ext = [x for x in a.ext_jobs.split(",") if x]; jobs = [a.orig_job] + ext
    looks = {k: float(v) for k, v in (x.split("=") for x in a.looks.split(","))}
    ov, ov_void = overlap(cw, R, a.orig_job, ext[0])
    gp, gp_ok = gpus(jobs)
    cand = f"KO_CAND_r{R}"
    ctrl_arms = [f"KO_RAND_r{R}_{i}" for i in range(a.n_old_rand + a.n_new)] + [f"KO_SHUF_r{R}_{j}" for j in range(a.nshuf)]
    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", cand] + ctrl_arms
    ana_out = f"{ROOT}/reports/heretic_csi/{a.tag}_analyzer.json"
    cmd = [PY, f"{ROOT}/scripts/dcs_csi_subspace_analyze.py", "--codeword", cw, "--tag-prefix", f"hcsi_p2a_{cw}",
           "--expect-n", "230", "--arms", ",".join(arms), "--candidate-arm", cand, "--comparator-arm", f"KO_RAND_r{R}_0",
           "--control-prefixes", "KO_SHUF,KO_RAND", "--split", "validation", "--direction", "sufficiency",
           "--option-mass-floor", "0.05", "--expect-n-controls", str(len(ctrl_arms)), "--allow-short", "20",
           "--require-slurm-job", ",".join(jobs), "--out", ana_out]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    open(f"{ROOT}/outputs/heretic_csi/logs/{a.tag}_analyzer.log", "w").write(r.stdout + "\n" + r.stderr)
    if r.returncode != 0:
        raise SystemExit("frozen analyzer failed:\n" + r.stderr[-3000:])
    d = json.load(open(ana_out)); ctr = d["control_recovery_distribution"]
    A = _ana()
    st, n_common, lost, doms, _ = stats(A, cw, arms, jobs, "base")
    assert n_common == d["n_keys_common"], (n_common, d["n_keys_common"])
    mism = {k: (st[k], ctr["controls"][k]) for k in ctrl_arms if abs(round(st[k], 5) - ctr["controls"][k]) > 1.01e-5}
    assert abs(round(st[cand], 5) - ctr["candidate"]) <= 1.01e-5 and not mism, mism
    cmk = d["contrasts"]["candidate_minus_ko"]
    gates_ok = (not d.get("VOID")) and bool(d.get("gates")) and all(bool(v) for v in d["gates"].values())
    void = list(ov_void) + ([] if gp_ok else [f"GPU types differ / not unique: {gp}"]) + list(d.get("VOID") or [])
    lk, sp = f"r{R}", f"KO_SHUF_r{R}_"
    dec_u = decide(st[cand], {k: st[k] for k in ctrl_arms}, looks, lk, sp, cmk["ci95"][0], gates_ok, void, n_common, a.expected_rows, lost,
                    len(doms), a.min_rows, a.min_domains)
    dec_r = decide(ctr["candidate"], dict(ctr["controls"]), looks, lk, sp, cmk["ci95"][0], gates_ok, void, n_common, a.expected_rows, lost,
                    len(doms), a.min_rows, a.min_domains)
    assert dec_r["rank"] == d["verdict_basis"]["candidate_rank"], (dec_r["rank"], d["verdict_basis"]["candidate_rank"])
    final = combine(dec_u, dec_r)
    # SENSITIVITY (descriptive): strict paired floor
    st_p, n_p, lost_p, doms_p, diffs_p = stats(A, cw, arms, jobs, "paired")
    ci_p = boot_ci(diffs_p)
    dec_p = decide(st_p[cand], {k: st_p[k] for k in ctrl_arms}, looks, lk, sp, ci_p[0], gates_ok, void, n_p, a.expected_rows, lost_p,
                    len(doms_p), a.min_rows, a.min_domains)
    orig_ctrls = [f"KO_RAND_r{R}_{i}" for i in range(a.n_old_rand)] + [f"KO_SHUF_r{R}_{j}" for j in range(a.nshuf)]
    comp_ii, comp_iii = companions(A, cw, R, jobs, st, cand, orig_ctrls)
    res = {"codeword": cw, "rank": R, "jobs": jobs, "companions_DESCRIPTIVE": {"ii_candidate_vs_original_56_on_shrunken_rows": comp_ii,
                                                                           "iii_per_control_paired_own_rows": comp_iii}, "gpus": gp, "overlap": ov, "looks_family": dict(looks, **{lk: "p_ext"}),
           "PRIMARY_base_ref_floor": {"unrounded": dec_u, "rounded_frozen_analyzer": dec_r, "FINAL_VERDICT": final,
                                      "candidate_stat_unrounded": st[cand], "candidate_minus_KO": cmk,
                                      "recovery_fraction": d.get("recovery_fraction_candidate_of_full"),
                                      "best_control": max(ctrl_arms, key=st.get), "best_control_stat": max(st[k] for k in ctrl_arms),
                                      "gates": d.get("gates")},
           "SENSITIVITY_paired_floor": {"decision": dec_p, "candidate_stat": st_p[cand], "candidate_minus_KO_ci95": ci_p,
                                        "n_domains": len(doms_p), "note": "descriptive only; never the verdict"},
           "control_stats_unrounded": {k: st[k] for k in ctrl_arms}, "VOID": void, "FINAL_VERDICT": final}
    out = f"{ROOT}/reports/heretic_csi/{a.tag}.json"
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(json.dumps({"FINAL_VERDICT": final, "unrounded": {k: dec_u[k] for k in ("rank", "p_ext", "holm", "beats_every_shuf", "max_shuf", "row_set", "VERDICT")},
                      "rounded": {k: dec_r[k] for k in ("rank", "VERDICT")}, "candidate_stat": st[cand], "cand_minus_KO": cmk["point"],
                      "ci95": cmk["ci95"], "companion_ii": comp_ii, "companion_iii": comp_iii, "paired_floor": {k: dec_p[k] for k in ("rank", "p_ext", "holm", "beats_every_shuf", "VERDICT")},
                      "paired_ci95": ci_p, "overlap": ov, "gpus": gp}, indent=1, default=str))


if __name__ == "__main__":
    main()
