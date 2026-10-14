#!/usr/bin/env python3
"""PR-HCSI-S084 (+ AMENDMENT 1) analysis of the powered button r4 VALIDATION re-test.

Steps (all frozen before any r4ext arm was run):
 1. OVERLAP VOID check: OVL_{BASE,KO,CAND_r4,RAND_r4_0} from job 1 must reproduce job 1022698's
    {BASE,KO,KO_CAND_r4,KO_RAND_r4_0} per prompt_id (identical id sets; |dlogp|,|dy| <= 1e-6).
 2. GPU-type check: every job log reports NVIDIA RTX A5000 only.
 3. Frozen analyzer scripts/dcs_csi_subspace_analyze.py over run dirs of jobs 1022698 + 1027577 + 1032110
    (KO_CAND_r4 vs 190 RAND + 10 SHUF = 200 controls, split validation, expect-n 230, floor 0.05).
 4. Amended PASS rule: Holm over {r1 0.2456, r16 0.1754, r4 p_ext} < 0.05 AND candidate > every KO_SHUF_r4_j
    AND candidate-minus-KO CI-lo > 0 AND gates AND no VOID. Row-set deviation from 203 reported.
"""
import glob, json, math, os, re, subprocess, sys
ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
PY = "/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python"
ORIG, J1, J2 = "1022698", "1027577", "1032110"
OUTJ = f"{ROOT}/reports/heretic_csi/P2A_BUTTON_R4_POWERED.json"
ANA = f"{ROOT}/reports/heretic_csi/hcsi_p2a_button_r4ext_validation_analyzer.json"
LOOKS = {"r1": 0.2456, "r16": 0.1754}


def dirs_for(job):
    out = {}
    for d in glob.glob(f"{ROOT}/outputs/boombness/score_behavior/hcsi_p2a_button_*"):
        try:
            m = json.load(open(d + "/RUNMETA.json"))
        except Exception:
            continue
        if str(m.get("slurm_job_id")) == job and os.path.exists(d + "/DONE.json"):
            arm = json.load(open(d + "/config.json"))["args"]["arm"]
            if arm in out:
                raise SystemExit(f"duplicate arm {arm} in job {job}")
            out[arm] = d
    return out


def rows(d):
    return {r["prompt_id"]: r for r in map(json.loads, open(d + "/results.jsonl"))}


def y(r):
    return 1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"])))


def overlap():
    o, n = dirs_for(ORIG), dirs_for(J1)
    pairs = {"OVL_BASE": "BASE", "OVL_KO": "KO", "OVL_CAND_r4": "KO_CAND_r4", "OVL_RAND_r4_0": "KO_RAND_r4_0"}
    res, void = {}, []
    for a_new, a_old in pairs.items():
        if a_new not in n:
            void.append(f"{a_new} missing"); continue
        rn, ro = rows(n[a_new]), rows(o[a_old])
        same_ids = set(rn) == set(ro)
        md = max((max(abs(rn[p]["logp_concept"] - ro[p]["logp_concept"]), abs(rn[p]["logp_codeword"] - ro[p]["logp_codeword"]),
                      abs(y(rn[p]) - y(ro[p]))) for p in set(rn) & set(ro)), default=float("nan"))
        res[a_new] = {"vs": a_old, "n_new": len(rn), "n_old": len(ro), "identical_id_sets": same_ids, "max_abs_diff": md}
        if not same_ids or not (md <= 1e-6):
            void.append(f"{a_new}: ids_equal={same_ids} max|diff|={md:.3g}")
    return res, void


def gpu_ok():
    out = {}
    for j in (ORIG, J1, J2):
        names = set(re.findall(r"^(NVIDIA [^,]+),", open(f"{ROOT}/outputs/heretic_csi/logs/sweep_{j}.out").read(), re.M))
        out[j] = sorted(names)
    return out, all(v == ["NVIDIA RTX A5000"] for v in out.values())


def holm(ps):
    order = sorted(ps, key=ps.get); out = {}; run = 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * ps[k])); out[k] = run
    return out


def decide(cand, controls, looks, ci_lo, gates_ok, void, n_keys_common, arms_lost):
    """Pure PR-HCSI-S084 + A1 decision on UNROUNDED statistics (review #4 item 9).
    cand: float; controls: {arm: float} (all 200); looks: {'r1': p, 'r16': p};
    arms_lost: {arm: n_keys_dropped_by_intersection}."""
    better = sum(1 for v in controls.values() if v >= cand)          # ties count against the candidate
    p_ext = (1 + better) / (len(controls) + 1)
    hp = holm(dict(looks, r4=p_ext))
    shuf = {k: v for k, v in controls.items() if k.startswith("KO_SHUF_r4_")}
    beats_all_shuf = bool(shuf) and all(cand > v for v in shuf.values())
    short = sorted(a for a, n in arms_lost.items() if n)
    passed = (not void) and hp["r4"] < 0.05 and beats_all_shuf and ci_lo > 0 and gates_ok
    return {"rank": 1 + better, "n_controls": len(controls), "p_ext": p_ext, "holm": hp,
            "beats_every_shuf": beats_all_shuf, "max_shuf": max(shuf.values()) if shuf else None,
            "row_set": {"n_keys_common": n_keys_common, "deviation_from_203": n_keys_common - 203,
                        "arms_with_dropped_keys": short},
            "VERDICT": ("VOID: " + "; ".join(void)) if void else ("PASS" if passed else "DOES NOT PASS")}


def unrounded_stats(arms, jobs):
    """Recompute the analyzer's statistic mean_d(dmean[arm] - dmean[KO]) WITHOUT rounding, using the
    frozen analyzer's own key/value helpers (same run-dir resolution, BASE-referenced floor 0.05,
    (domain, slot) key intersection across ALL arms)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("dcs_ana", f"{ROOT}/scripts/dcs_csi_subspace_analyze.py")
    A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)
    sel = {"require_rescue_layer": None, "require_slurm_jobs": list(jobs)}
    assign = A.lpm.load_split()
    rd = lambda arm: A.rederive.strict_run_dir(f"hcsi_p2a_button_{arm}", 230, row_file="results.jsonl", allow_short=20, **sel)
    keep = A.reference_key_set(rd("BASE"), 0.05)
    kv = {arm: A.arm_key_values(rd(arm), assign, "validation")[0] for arm in arms}
    common = set.intersection(*[set(v) for v in kv.values()]) & keep
    lost = {arm: len(kv[arm]) - len(set(kv[arm]) & common) for arm in arms}
    lost_vs_ref = {arm: len(set(kv["BASE"]) & keep) - len(set(kv[arm]) & keep) for arm in arms}
    dm = {}
    for arm in arms:
        by = {}
        for k in common:
            by.setdefault(k[0], []).append(kv[arm][k])
        dm[arm] = {d: sum(v) / len(v) for d, v in by.items()}
    doms = sorted({k[0] for k in common})
    stat = {arm: sum(dm[arm][d] - dm["KO"][d] for d in doms) / len(doms) for arm in arms}
    return stat, len(common), lost_vs_ref


def main():
    ov, ov_void = overlap()
    gpus, gpu_pass = gpu_ok()
    n1, n2 = dirs_for(J1), dirs_for(J2)
    new_rand = sorted([a for a in list(n1) + list(n2) if a.startswith("KO_RAND_r4_")], key=lambda a: int(a.rsplit("_", 1)[1]))
    arms = (["BASE", "KO", "KO_SELF", "KO_FULL", "KO_CAND_r4"] + [f"KO_RAND_r4_{i}" for i in range(190)]
            + [f"KO_SHUF_r4_{j}" for j in range(10)])
    cmd = [PY, f"{ROOT}/scripts/dcs_csi_subspace_analyze.py", "--codeword", "button", "--tag-prefix", "hcsi_p2a_button",
           "--expect-n", "230", "--arms", ",".join(arms), "--candidate-arm", "KO_CAND_r4", "--comparator-arm", "KO_RAND_r4_0",
           "--control-prefixes", "KO_SHUF,KO_RAND", "--split", "validation", "--direction", "sufficiency",
           "--option-mass-floor", "0.05", "--expect-n-controls", "200", "--allow-short", "20",
           "--require-slurm-job", f"{ORIG},{J1},{J2}", "--out", ANA]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    open(f"{ROOT}/outputs/heretic_csi/logs/analyze_button_r4ext_val.log", "w").write(r.stdout + "\n" + r.stderr)
    if r.returncode != 0:
        raise SystemExit("frozen analyzer failed:\n" + r.stderr[-3000:])
    d = json.load(open(ANA))
    vb, ctr = d["verdict_basis"], d["control_recovery_distribution"]
    ctrl_arms = [a for a in arms if a.startswith(("KO_RAND_r4_", "KO_SHUF_r4_"))]
    stat, n_common, lost = unrounded_stats(arms, (ORIG, J1, J2))
    assert n_common == d["n_keys_common"], (n_common, d["n_keys_common"])
    # my unrounded values must round to the analyzer's published 5-dp points
    mism = {a: (stat[a], ctr["controls"][a]) for a in ctrl_arms if abs(round(stat[a], 5) - ctr["controls"][a]) > 1.01e-5}
    assert abs(round(stat["KO_CAND_r4"], 5) - ctr["candidate"]) <= 1.01e-5 and not mism, mism
    cmk = d["contrasts"]["candidate_minus_ko"]
    gates_ok = (not d.get("VOID")) and bool(d.get("gates")) and all(bool(v) for v in d["gates"].values())
    void = list(ov_void) + ([] if gpu_pass else [f"non-a5000 GPU: {gpus}"]) + (list(d.get("VOID") or []))
    dec = decide(stat["KO_CAND_r4"], {a: stat[a] for a in ctrl_arms}, LOOKS, cmk["ci95"][0], gates_ok, void, n_common, lost)
    frozen_rounded_rank = vb.get("candidate_rank")
    res = {"prereg": ["configs/heretic_csi/prereg_S084_button_r4_powered.json", "configs/heretic_csi/prereg_S084_button_r4_powered_AMENDMENT_1.json"],
           "jobs": {"orig": ORIG, "ext1": J1, "ext2": J2}, "n_new_rand_arms": len(new_rand), "gpus": gpus, "overlap": ov,
           "decision_unrounded": dec, "frozen_analyzer_rounded_rank": frozen_rounded_rank,
           "rank_agreement_unrounded_vs_rounded": dec["rank"] == frozen_rounded_rank,
           "candidate_stat_unrounded": stat["KO_CAND_r4"], "candidate_minus_KO": cmk,
           "recovery_fraction": d.get("recovery_fraction_candidate_of_full"),
           "control_stats_unrounded": {a: stat[a] for a in ctrl_arms},
           "best_control": max(ctrl_arms, key=stat.get), "gates": d.get("gates"), "VOID": void,
           "VERDICT": dec["VERDICT"]}
    json.dump(res, open(OUTJ, "w"), indent=1, default=str)
    print(json.dumps({k: res[k] for k in ["VERDICT", "decision_unrounded", "frozen_analyzer_rounded_rank",
                                          "rank_agreement_unrounded_vs_rounded", "candidate_stat_unrounded",
                                          "best_control", "candidate_minus_KO", "overlap", "gpus"]}, indent=1, default=str))


if __name__ == "__main__":
    main()
